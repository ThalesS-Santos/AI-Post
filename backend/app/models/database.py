import asyncio
from functools import lru_cache

from supabase import create_client, Client

from ..core.config import get_settings


@lru_cache()
def _get_client() -> Client:
    s = get_settings()
    return create_client(s.SUPABASE_URL, s.SUPABASE_SERVICE_ROLE_KEY)


async def buscar_contexto_rag(
    cliente_id: str,
    vetor_query: list[float],
    limite: int = 3,
) -> list[dict]:
    client = _get_client()
    result = await asyncio.to_thread(
        lambda: client.rpc(
            "buscar_contexto_similar",
            {
                "cliente_uuid": cliente_id,
                "query_embedding": vetor_query,
                "match_count": limite,
            },
        ).execute()
    )
    return result.data or []


async def salvar_embedding(
    cliente_id: str,
    tipo: str,
    texto_base: str,
    url_imagem: str,
    vetor: list[float],
) -> dict:
    client = _get_client()
    result = await asyncio.to_thread(
        lambda: client.table("embeddings_marca")
        .insert(
            {
                "cliente_id": cliente_id,
                "tipo": tipo,
                "texto_base": texto_base,
                "url_imagem": url_imagem,
                "vetor_embedding": vetor,
            }
        )
        .execute()
    )
    return result.data[0]


async def listar_produtos(cliente_id: str) -> list[dict]:
    """Todas as fotos de produto salvas na conta do usuário."""
    client = _get_client()
    result = await asyncio.to_thread(
        lambda: client.table("embeddings_marca")
        .select("id, texto_base, url_imagem")
        .eq("cliente_id", cliente_id)
        .eq("tipo", "produto")
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


async def buscar_produto_por_id(cliente_id: str, produto_id: str) -> dict | None:
    client = _get_client()
    result = await asyncio.to_thread(
        lambda: client.table("embeddings_marca")
        .select("id, texto_base, url_imagem")
        .eq("cliente_id", cliente_id)
        .eq("id", produto_id)
        .limit(1)
        .execute()
    )
    data = result.data or []
    return data[0] if data else None


async def buscar_regra_marca(cliente_id: str) -> dict | None:
    """Tom de voz / regras da marca mais recentes do usuário."""
    client = _get_client()
    result = await asyncio.to_thread(
        lambda: client.table("embeddings_marca")
        .select("texto_base")
        .eq("cliente_id", cliente_id)
        .eq("tipo", "regra_marca")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    data = result.data or []
    return data[0] if data else None


async def fazer_upload_storage(
    bucket: str,
    caminho: str,
    dados: bytes,
    content_type: str = "image/jpeg",
) -> str:
    client = _get_client()
    await asyncio.to_thread(
        lambda: client.storage.from_(bucket).upload(
            path=caminho,
            file=dados,
            file_options={"content-type": content_type},
        )
    )
    url: str = client.storage.from_(bucket).get_public_url(caminho)
    return url
