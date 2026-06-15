import asyncio
import base64
import io

from google import genai
from google.genai import types
from google.genai.errors import ClientError

from PIL import Image, ImageDraw, ImageFont
import httpx

from ..core.config import get_settings

_IMAGE_MODEL = "imagen-4.0-generate-001"

_indisponivel = False


def _client() -> genai.Client:
    return genai.Client(api_key=get_settings().GEMINI_API_KEY)


def imagem_indisponivel() -> bool:
    return _indisponivel


async def _baixar_imagem(url: str) -> bytes | None:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10)
            resp.raise_for_status()
            return resp.content
    except Exception:
        return None


def _aplicar_logo_e_preco(img_bytes: bytes, logo_bytes: bytes | None, preco: str, local_do_preco: str) -> bytes:
    try:
        base_img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        width, height = base_img.size

        # Aplicar logo
        if logo_bytes:
            logo_img = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
            # Redimensionar logo para ocupar no máximo 15% da largura da imagem base
            logo_w = int(width * 0.15)
            aspect_ratio = logo_img.height / logo_img.width
            logo_h = int(logo_w * aspect_ratio)
            logo_img = logo_img.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
            
            # Posicionar no canto inferior direito com margem
            margin = int(width * 0.03)
            pos_x = width - logo_w - margin
            pos_y = height - logo_h - margin
            base_img.alpha_composite(logo_img, (pos_x, pos_y))

        # Aplicar preço se necessário
        if preco and local_do_preco == "imagem":
            draw = ImageDraw.Draw(base_img)
            try:
                # Tenta usar Arial, senão usa fonte padrão
                font_size = int(width * 0.08)
                font = ImageFont.truetype("arial.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()
            
            texto = f" {preco} "
            # Posição: Canto superior esquerdo com margem
            margin = int(width * 0.03)
            
            # Calculando bounding box do texto para o fundo vermelho
            bbox = draw.textbbox((0, 0), texto, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            
            rect_x0 = margin
            rect_y0 = margin
            rect_x1 = margin + text_w
            rect_y1 = margin + text_h + int(text_h * 0.2)
            
            # Fundo vermelho para destaque
            draw.rectangle([rect_x0, rect_y0, rect_x1, rect_y1], fill=(220, 20, 60, 255), outline=(255, 255, 255, 255), width=2)
            draw.text((margin, margin), texto, font=font, fill=(255, 255, 255, 255))

        out_img = base_img.convert("RGB")
        out_bytes = io.BytesIO()
        out_img.save(out_bytes, format="JPEG", quality=90)
        return out_bytes.getvalue()
    except Exception as e:
        print(f"Erro ao aplicar marca d'água/preço: {e}")
        return img_bytes


async def gerar_imagem_ia(
    legenda: str, 
    produto_b64: str, 
    tema: str, 
    descricao_produto: str = "",
    estilos_imagem: list[str] = None,
    logo_url: str = "",
    preco: str = "",
    local_do_preco: str = "nenhum",
) -> str | None:
    global _indisponivel
    if _indisponivel:
        return None

    client = _client()

    if estilos_imagem is None:
        estilos_imagem = []

    estilos_str = " e ".join(estilos_imagem) if estilos_imagem else "Realista de alta definição"

    prompt = (
        f"Crie uma imagem de marketing de altíssimo impacto visual, projetada para reter a atenção e parar a rolagem no Instagram. "
        f"Produto em destaque: {descricao_produto or 'Produto principal'}. "
        f"Estilo Artístico OBRIGATÓRIO: {estilos_str}. A imagem DEVE refletir perfeitamente esse(s) estilo(s) visual(is). "
        f"Contexto da publicação: {legenda}. "
        f"Tema da campanha: {tema}. "
        "Não inclua textos, letras, símbolos ou palavras escritas na imagem. Foco 100% na arte visual."
    )

    try:
        response = await asyncio.to_thread(
            lambda: client.models.generate_images(
                model=_IMAGE_MODEL,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="1:1"
                ),
            )
        )
        if response.generated_images:
            gen_img = response.generated_images[0]
            if gen_img.image and gen_img.image.image_bytes:
                img_bytes = gen_img.image.image_bytes
                
                logo_bytes = None
                if logo_url:
                    logo_bytes = await _baixar_imagem(logo_url)
                
                if logo_bytes or (preco and local_do_preco == "imagem"):
                    img_bytes = await asyncio.to_thread(_aplicar_logo_e_preco, img_bytes, logo_bytes, preco, local_do_preco)

                return base64.b64encode(img_bytes).decode("utf-8")
    except ClientError as exc:
        msg = str(exc)
        print(f"[ImageService] ClientError: {msg}")
        if exc.code == 404 or "limit: 0" in msg or "free_tier" in msg.lower():
            _indisponivel = True
        return None
    except Exception as exc:
        print(f"[ImageService] Exception: {exc}")
        return None

    return None
