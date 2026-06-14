import asyncio
import base64

from google import genai
from google.genai import types
from google.genai.errors import ClientError

from ..core.config import get_settings

# "nano banana" — geração/edição de imagem multimodal do Gemini.
_IMAGE_MODEL = "gemini-2.5-flash-image"

# Uma vez detectado que o modelo de imagem não está disponível no plano
# (free tier com cota 0, ou modelo inexistente para a chave), paramos de
# tentar no resto do processo para não desperdiçar segundos por post.
_indisponivel = False


def _client() -> genai.Client:
    return genai.Client(api_key=get_settings().GEMINI_API_KEY)


def imagem_indisponivel() -> bool:
    return _indisponivel


async def gerar_imagem_ia(legenda: str, produto_b64: str, tema: str) -> str | None:
    """
    Gera uma imagem com IA usando a LEGENDA como prompt principal,
    a foto real do produto como referência visual e o tema da campanha.

    Retorna a imagem em base64 (PNG) ou None se a geração de imagem não
    estiver disponível no plano atual — nesse caso o app usa a foto original.
    """
    global _indisponivel
    if _indisponivel:
        return None

    client = _client()

    prompt = (
        "Crie uma imagem de marketing para Instagram, fotorrealista, bonita e "
        "pronta para publicação, baseada NESTE texto do post:\n"
        f'"{legenda}"\n\n'
        f"Tema da campanha: {tema}.\n"
        "Use a foto de referência anexada para manter fidelidade ao produto real "
        "(mesmas cores, formato e características). Iluminação profissional, "
        "composição limpa e atraente, alta qualidade. Não escreva texto na imagem."
    )

    image_part = types.Part.from_bytes(
        data=base64.b64decode(produto_b64),
        mime_type="image/jpeg",
    )

    try:
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=_IMAGE_MODEL,
                contents=[prompt, image_part],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            ),
            timeout=60,
        )
    except ClientError as exc:
        msg = str(exc)
        # 404 = modelo não existe p/ a chave; "limit: 0"/free_tier = sem cota.
        if exc.code == 404 or "limit: 0" in msg or "free_tier" in msg.lower():
            _indisponivel = True
        return None
    except (TimeoutError, Exception):
        return None

    try:
        for part in response.candidates[0].content.parts:
            inline = getattr(part, "inline_data", None)
            if inline and inline.data:
                return base64.b64encode(inline.data).decode("utf-8")
    except (AttributeError, IndexError):
        return None

    return None
