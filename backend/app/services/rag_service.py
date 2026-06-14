from ..models.database import buscar_contexto_rag
from ..schemas.post_schema import PostContent
from .llm_service import gerar_embedding, gerar_post
from .storage_service import baixar_imagem, para_base64


async def _recuperar_contexto(cliente_id: str, foco: str) -> list[dict]:
    vetor = await gerar_embedding(foco)
    return await buscar_contexto_rag(cliente_id=cliente_id, vetor_query=vetor, limite=5)


async def orquestrar_geracao(
    cliente_id: str,
    foco: str,
    quantidade: int,
) -> list[PostContent]:
    contextos = await _recuperar_contexto(cliente_id, foco)

    if not contextos:
        raise ValueError(
            "Nenhum contexto de marca encontrado. Configure sua marca primeiro."
        )

    regra = next(
        (c for c in contextos if c.get("tipo") == "regra_marca"),
        contextos[0],
    )
    produtos = [c for c in contextos if c.get("tipo") == "produto"]

    if not produtos:
        raise ValueError(
            "Nenhum produto cadastrado. Adicione produtos ao catálogo antes de gerar posts."
        )

    tom_voz = regra.get("texto_base", "")
    posts: list[PostContent] = []

    for i in range(quantidade):
        produto = produtos[i % len(produtos)]
        raw = await baixar_imagem(produto["url_imagem"])
        b64 = para_base64(raw)
        post = await gerar_post(tom_voz=tom_voz, objetivo=foco, imagem_base64=b64)
        posts.append(post)

    return posts
