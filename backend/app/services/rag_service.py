from google.genai.errors import ClientError

from ..models.database import (
    buscar_contexto_rag,
    buscar_produto_por_id,
    buscar_regra_marca,
    listar_produtos,
)
from ..schemas.post_schema import PostContent
from .image_service import gerar_imagem_ia
from .llm_service import gerar_embedding, gerar_post
from .storage_service import baixar_imagem, para_base64


async def _recuperar_contexto(cliente_id: str, foco: str) -> list[dict]:
    vetor = await gerar_embedding(foco)
    return await buscar_contexto_rag(cliente_id=cliente_id, vetor_query=vetor, limite=5)


async def _resolver_tom_voz(cliente_id: str, contextos: list[dict]) -> str:
    regra = next((c for c in contextos if c.get("tipo") == "regra_marca"), None)
    if regra and regra.get("texto_base"):
        return regra["texto_base"]
    rm = await buscar_regra_marca(cliente_id)
    return rm["texto_base"] if rm else ""


async def _montar_post(
    produto: dict,
    tom_voz: str,
    foco: str,
    com_imagem: bool = True,
) -> PostContent:
    """Gera 1 post completo: PRIMEIRO a legenda, DEPOIS a imagem a partir dela."""
    raw = await baixar_imagem(produto["url_imagem"])
    b64 = para_base64(raw)

    # 1) Legenda (texto) — base de tudo
    post = await gerar_post(tom_voz=tom_voz, objetivo=foco, imagem_base64=b64)
    post.produto_id = str(produto["id"])
    post.produto_url = produto["url_imagem"]

    # 2) Imagem IA, usando a legenda recém-criada como prompt principal
    if com_imagem:
        img = await gerar_imagem_ia(post.legenda_instagram, b64, foco)
        if img:
            post.imagem_gerada_base64 = img
            post.imagem_disponivel = True

    return post


async def orquestrar_geracao(
    cliente_id: str,
    foco: str,
    quantidade: int,
) -> list[PostContent]:
    contextos = await _recuperar_contexto(cliente_id, foco)
    produtos = [c for c in contextos if c.get("tipo") == "produto"]

    # A busca RAG traz no máx. 5; para 7/30 posts pegamos todo o catálogo.
    if quantidade > len(produtos):
        todos = await listar_produtos(cliente_id)
        if todos:
            produtos = todos

    if not produtos:
        raise ValueError(
            "Você ainda não tem fotos salvas. Adicione fotos do seu produto antes de gerar posts."
        )

    tom_voz = await _resolver_tom_voz(cliente_id, contextos)
    if not tom_voz:
        raise ValueError("Configure sua marca primeiro (nome, tom de voz e nicho).")

    posts: list[PostContent] = []
    for i in range(quantidade):
        produto = produtos[i % len(produtos)]
        try:
            posts.append(await _montar_post(produto, tom_voz, foco))
        except ClientError as exc:
            # Cota por minuto atingida no meio do lote: devolve o que já temos.
            if exc.code == 429 and posts:
                break
            raise

    return posts


# ---------- Refazer individual ----------

async def _contexto_regen(cliente_id: str, produto_id: str) -> tuple[dict, str, str]:
    produto = await buscar_produto_por_id(cliente_id, produto_id)
    if not produto:
        raise ValueError("Foto não encontrada na sua conta.")
    tom_voz = await _resolver_tom_voz(cliente_id, [])
    raw = await baixar_imagem(produto["url_imagem"])
    b64 = para_base64(raw)
    return produto, tom_voz, b64


async def regenerar_legenda(cliente_id: str, foco: str, produto_id: str) -> PostContent:
    """Refaz APENAS a legenda de um post (mantém a mesma foto-base)."""
    produto, tom_voz, b64 = await _contexto_regen(cliente_id, produto_id)
    post = await gerar_post(tom_voz=tom_voz, objetivo=foco, imagem_base64=b64)
    post.produto_id = str(produto["id"])
    post.produto_url = produto["url_imagem"]
    return post


async def regenerar_imagem(
    cliente_id: str,
    foco: str,
    produto_id: str,
    legenda: str,
) -> str | None:
    """Refaz APENAS a imagem, usando a legenda existente como prompt."""
    _produto, _tom, b64 = await _contexto_regen(cliente_id, produto_id)
    return await gerar_imagem_ia(legenda, b64, foco)
