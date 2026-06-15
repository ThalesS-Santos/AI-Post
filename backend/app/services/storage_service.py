import base64
import io
import uuid

import httpx
from PIL import Image

from ..models.database import fazer_upload_storage

MAX_DIMENSION = 1024
JPEG_QUALITY = 85


def _comprimir(raw: bytes) -> bytes:
    with Image.open(io.BytesIO(raw)) as img:
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        return buf.getvalue()


def para_base64(raw: bytes) -> str:
    return base64.b64encode(_comprimir(raw)).decode("utf-8")


async def upload_produto(raw: bytes, cliente_id: str, nome_arquivo: str) -> str:
    comprimido = _comprimir(raw)
    caminho = f"{cliente_id}/produtos/{uuid.uuid4()}_{nome_arquivo}"
    url = await fazer_upload_storage("catalogo-produtos", caminho, comprimido)
    return url


async def upload_logo(raw: bytes, cliente_id: str, nome_arquivo: str) -> str:
    # Para logo, mantemos o formato original (PNG com transparência) sem comprimir em JPEG.
    caminho = f"{cliente_id}/logos/{uuid.uuid4()}_{nome_arquivo}"
    # Detecta se é PNG ou JPEG
    content_type = "image/png" if nome_arquivo.lower().endswith(".png") else "image/jpeg"
    url = await fazer_upload_storage("catalogo-produtos", caminho, raw, content_type=content_type)
    return url


async def baixar_imagem(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.content
