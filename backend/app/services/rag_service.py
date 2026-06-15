import asyncio
from google.genai.errors import ClientError

from ..models.database import (
    buscar_produtos_similares,
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
    return await buscar_produtos_similares(cliente_id=cliente_id, vetor_query=vetor, limite=5)


async def _resolver_tom_voz(cliente_id: str, contextos: list[dict]) -> tuple[str, str]:
    """Retorna (tom_voz, url_logo_marca)"""
    regra = next((c for c in contextos if c.get("tipo") == "regra_marca"), None)
    if regra and regra.get("texto_base"):
        return regra["texto_base"], regra.get("url_imagem", "")
    rm = await buscar_regra_marca(cliente_id)
    return (rm["texto_base"], rm.get("url_imagem", "")) if rm else ("", "")


async def _montar_post(
    produto: dict,
    tom_voz: str,
    foco: str,
    com_imagem: bool = True,
    estilos_imagem: list[str] = None,
    logo_url: str = "",
) -> PostContent:
    """Gera 1 post completo: PRIMEIRO a legenda, DEPOIS a imagem a partir dela."""
    raw = await baixar_imagem(produto["url_imagem"])
    b64 = para_base64(raw)
    preco_produto = produto.get("preco", "")

    # 1) Legenda (texto) — base de tudo
    post = await gerar_post(tom_voz=tom_voz, objetivo=foco, imagem_base64=b64, preco=preco_produto)
    post.produto_id = str(produto["id"])
    post.produto_url = produto["url_imagem"]

    # 2) Imagem IA, usando a legenda recém-criada como prompt principal e descrição textual do produto
    if com_imagem:
        img = await gerar_imagem_ia(
            legenda=post.legenda_instagram, 
            produto_b64=b64, 
            tema=foco,
            descricao_produto=produto.get("texto_base", ""),
            estilos_imagem=estilos_imagem,
            logo_url=logo_url,
            preco=preco_produto,
            local_do_preco=post.local_do_preco
        )
        if img:
            post.imagem_gerada_base64 = img
            post.imagem_disponivel = True

    return post


async def orquestrar_geracao(
    cliente_id: str,
    foco: str,
    quantidade: int,
    estilos_imagem: list[str] = None,
) -> list[PostContent]:
    produtos = await _recuperar_contexto(cliente_id, foco)

    # Se a quantidade solicitada for maior que o retornado pelo RAG,
    # preservamos a ordem de relevância dos produtos RAG e completamos com os demais produtos do catálogo.
    if quantidade > len(produtos):
        todos = await listar_produtos(cliente_id)
        if todos:
            ids_existentes = {p["id"] for p in produtos}
            adicionais = [p for p in todos if p["id"] not in ids_existentes]
            produtos.extend(adicionais)

    if not produtos:
        raise ValueError(
            "Você ainda não tem fotos salvas. Adicione fotos do seu produto antes de gerar posts."
        )

    tom_voz, logo_url = await _resolver_tom_voz(cliente_id, [])
    if not tom_voz:
        raise ValueError("Configure sua marca primeiro (nome, tom de voz e nicho).")

    # Gerar concorrentemente com asyncio.gather para evitar timeouts em lotes
    tarefas = []
    for i in range(quantidade):
        produto = produtos[i % len(produtos)]
        tarefas.append(_montar_post(produto, tom_voz, foco, estilos_imagem=estilos_imagem, logo_url=logo_url))
    
    resultados = await asyncio.gather(*tarefas, return_exceptions=True)
    
    posts: list[PostContent] = []
    primeiro_erro = None
    
    for r in resultados:
        if isinstance(r, Exception):
            if primeiro_erro is None:
                primeiro_erro = r
        else:
            posts.append(r)
            
    if not posts and primeiro_erro:
        raise primeiro_erro

    return posts


# ---------- Refazer individual ----------

async def _contexto_regen(cliente_id: str, produto_id: str) -> tuple[dict, str, str, str]:
    produto = await buscar_produto_por_id(cliente_id, produto_id)
    if not produto:
        raise ValueError("Foto não encontrada na sua conta.")
    tom_voz, logo_url = await _resolver_tom_voz(cliente_id, [])
    raw = await baixar_imagem(produto["url_imagem"])
    b64 = para_base64(raw)
    return produto, tom_voz, logo_url, b64


async def regenerar_legenda(cliente_id: str, foco: str, produto_id: str, estilos_imagem: list[str] = None) -> PostContent:
    """Refaz APENAS a legenda de um post (mantém a mesma foto-base)."""
    produto, tom_voz, logo_url, b64 = await _contexto_regen(cliente_id, produto_id)
    preco_produto = produto.get("preco", "")
    post = await gerar_post(tom_voz=tom_voz, objetivo=foco, imagem_base64=b64, preco=preco_produto)
    post.produto_id = str(produto["id"])
    post.produto_url = produto["url_imagem"]
    return post


async def regenerar_imagem(
    cliente_id: str,
    foco: str,
    produto_id: str,
    legenda: str,
    estilos_imagem: list[str] = None,
) -> str | None:
    """Refaz APENAS a imagem, usando a legenda existente como prompt."""
    produto, _tom, logo_url, b64 = await _contexto_regen(cliente_id, produto_id)
    preco_produto = produto.get("preco", "")
    return await gerar_imagem_ia(
        legenda=legenda, 
        produto_b64=b64, 
        tema=foco,
        descricao_produto=produto.get("texto_base", ""),
        estilos_imagem=estilos_imagem,
        logo_url=logo_url,
        preco=preco_produto,
        # Default para legenda regenerada não mudamos, apenas se quiser refazer
        local_do_preco="nenhum" # Para imagem solta
    )
