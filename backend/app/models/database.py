import asyncio
from functools import lru_cache

from supabase import create_client, Client

from ..core.config import get_settings


@lru_cache()
def _get_client() -> Client:
    s = get_settings()
    return create_client(s.SUPABASE_URL, s.SUPABASE_SERVICE_ROLE_KEY)


async def buscar_produtos_similares(
    cliente_id: str,
    vetor_query: list[float],
    limite: int = 3,
) -> list[dict]:
    client = _get_client()
    result = await asyncio.to_thread(
        lambda: client.rpc(
            "buscar_produtos_similares",
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
    preco: str = "",
    metadata: dict = None,
) -> dict:
    if metadata is None:
        metadata = {}
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
                "preco": preco,
                "metadata": metadata,
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
        .select("id, texto_base, url_imagem, preco")
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
        .select("id, texto_base, url_imagem, preco")
        .eq("cliente_id", cliente_id)
        .eq("id", produto_id)
        .limit(1)
        .execute()
    )
    data = result.data or []
    return data[0] if data else None


async def atualizar_produto(cliente_id: str, produto_id: str, texto_base: str, preco: str, vetor: list[float] | None = None) -> dict | None:
    client = _get_client()
    update_data = {
        "texto_base": texto_base,
        "preco": preco,
    }
    if vetor:
        update_data["vetor_embedding"] = vetor

    result = await asyncio.to_thread(
        lambda: client.table("embeddings_marca")
        .update(update_data)
        .eq("cliente_id", cliente_id)
        .eq("id", produto_id)
        .execute()
    )
    data = result.data or []
    return data[0] if data else None


async def deletar_produto(cliente_id: str, produto_id: str) -> bool:
    client = _get_client()
    result = await asyncio.to_thread(
        lambda: client.table("embeddings_marca")
        .delete()
        .eq("cliente_id", cliente_id)
        .eq("id", produto_id)
        .execute()
    )
    return len(result.data or []) > 0


async def buscar_regra_marca(cliente_id: str) -> dict | None:
    """Tom de voz / regras da marca mais recentes do usuário."""
    client = _get_client()
    result = await asyncio.to_thread(
        lambda: client.table("embeddings_marca")
        .select("id, texto_base, url_imagem, metadata")
        .eq("cliente_id", cliente_id)
        .eq("tipo", "regra_marca")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    data = result.data or []
    return data[0] if data else None


async def atualizar_regra_marca(cliente_id: str, marca_id: str, texto_base: str, metadata: dict, vetor: list[float] | None = None) -> dict | None:
    client = _get_client()
    update_data = {
        "texto_base": texto_base,
        "metadata": metadata,
    }
    if vetor:
        update_data["vetor_embedding"] = vetor

    result = await asyncio.to_thread(
        lambda: client.table("embeddings_marca")
        .update(update_data)
        .eq("id", marca_id)
        .eq("cliente_id", cliente_id)
        .execute()
    )
    data = result.data or []
    return data[0] if data else None


async def atualizar_logo_marca(cliente_id: str, url_logo: str) -> dict | None:
    """Atualiza a URL do logo da marca mais recente do cliente."""
    marca = await buscar_regra_marca(cliente_id)
    if not marca:
        return None
    client = _get_client()
    result = await asyncio.to_thread(
        lambda: client.table("embeddings_marca")
        .update({"url_imagem": url_logo})
        .eq("id", marca["id"])
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
            file_options={"content-type": content_type, "upsert": "true"},
        )
    )
    url: str = client.storage.from_(bucket).get_public_url(caminho)
    return url
