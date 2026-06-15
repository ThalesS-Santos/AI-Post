import base64
import asyncio
import json

from google import genai
from google.genai import types

from ..core.config import get_settings
from ..schemas.post_schema import PostContent

_POST_SCHEMA = {
    "type": "object",
    "properties": {
        "titulo_interno":            {"type": "string"},
        "legenda_instagram":         {"type": "string"},
        "sugestao_de_edicao_visual": {"type": "string"},
        "hashtags":                  {"type": "array", "items": {"type": "string"}},
        "local_do_preco":            {"type": "string", "enum": ["imagem", "legenda", "nenhum"]},
    },
    "required": ["titulo_interno", "legenda_instagram", "sugestao_de_edicao_visual", "hashtags", "local_do_preco"],
}

_SYSTEM_INSTRUCTION = """Você atua como o Motor de Criação Cérebro da plataforma OurCore/N1. \
Sua função primária é agir como um Diretor de Arte e Copywriter Sênior. \
Você receberá uma imagem de referência do produto real do cliente, um bloco de contexto \
contendo o tom de voz e nicho da marca, e possivelmente o preço do produto.

REGRAS ABSOLUTAS:
1. Analise os detalhes visuais da imagem fornecida. Se houver granulado de chocolate, mencione. Se o fundo for rústico, adapte o humor.
2. Obedeça cegamente ao 'Tom de Voz' fornecido no Contexto do Cliente.
3. Se um Preço for fornecido, você deve decidir a melhor estratégia para exibi-lo:
   - "imagem": Se for uma promoção agressiva, destaque de vendas ou oferta especial que chama atenção.
   - "legenda": Se o preço for apenas informativo, mantendo a imagem limpa e focada no estilo e sofisticação.
   - "nenhum": Se o preço não foi fornecido.
4. Você não deve conversar. Retorne APENAS um objeto JSON válido, sem markdown, sem introduções.
5. Siga estritamente o schema fornecido."""


def _client() -> genai.Client:
    return genai.Client(api_key=get_settings().GEMINI_API_KEY)


async def gerar_embedding(texto: str, task_type: str = "RETRIEVAL_QUERY") -> list[float]:
    client = _client()
    result = await asyncio.wait_for(
        client.aio.models.embed_content(
            model="gemini-embedding-001",
            contents=texto,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=768,
            ),
        ),
        timeout=30,
    )
    return list(result.embeddings[0].values)


async def gerar_embedding_documento(texto: str) -> list[float]:
    return await gerar_embedding(texto, task_type="RETRIEVAL_DOCUMENT")


async def gerar_post(tom_voz: str, objetivo: str, imagem_base64: str, preco: str = "") -> PostContent:
    client = _client()

    prompt = (
        f"Contexto do Cliente (Recuperado via RAG): {tom_voz}\n"
        f"Objetivo do Post: {objetivo}\n"
        f"Preço do Produto (se houver): {preco}\n"
        "Imagem do Produto: [imagem anexada]"
    )

    image_part = types.Part.from_bytes(
        data=base64.b64decode(imagem_base64),
        mime_type="image/jpeg",
    )

    response = await asyncio.wait_for(
        client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, image_part],
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=_POST_SCHEMA,
                temperature=0.85,
                max_output_tokens=2048,
                # gemini-2.5 e um modelo "thinking"; sem isto os tokens de
                # raciocinio consomem o budget e o JSON volta truncado.
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        ),
        timeout=90,
    )

    if response.prompt_feedback and response.prompt_feedback.block_reason:
        raise ValueError(
            f"Conteúdo bloqueado pelos filtros de segurança: {response.prompt_feedback.block_reason}"
        )

    data = json.loads(response.text)
    return PostContent(**data)
