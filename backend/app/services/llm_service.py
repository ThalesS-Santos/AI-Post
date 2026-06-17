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
Você deve consultar o File Search fornecido para obter as regras de marca (tom de voz, nicho) e as informações do produto relevante para o post.

REGRAS ABSOLUTAS:
1. Obedeça cegamente ao 'Tom de Voz' recuperado através do File Search.
2. Analise os detalhes visuais do produto associado.
3. Se um preço for encontrado no File Search, decida a melhor estratégia para exibi-lo:
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


async def gerar_post(objetivo: str, file_search_store_name: str) -> tuple[PostContent, str | None]:
    """Gera um post utilizando a ferramenta File Search (RAG Nativo) do Gemini."""
    client = _client()

    prompt = (
        f"Consulte o seu File Search para obter o contexto da marca (tom de voz, nicho) e do produto cadastrado.\n"
        f"Objetivo do Post (Tema da campanha): {objetivo}\n"
        f"Gere o post correspondente no formato JSON requerido."
    )

    tools = [
        types.Tool(
            file_search=types.FileSearch(
                file_search_store_names=[file_search_store_name]
            )
        )
    ]

    response = await asyncio.wait_for(
        client.aio.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=_POST_SCHEMA,
                temperature=0.85,
                max_output_tokens=2048,
                tools=tools
            ),
        ),
        timeout=90,
    )

    if response.prompt_feedback and response.prompt_feedback.block_reason:
        raise ValueError(
            f"Conteúdo bloqueado pelos filtros de segurança: {response.prompt_feedback.block_reason}"
        )

    # Procura citação de imagem (media_id) nos metadados de grounding
    media_id = None
    if response.candidates and response.candidates[0].grounding_metadata:
        gm = response.candidates[0].grounding_metadata
        if gm.grounding_chunks:
            for chunk in gm.grounding_chunks:
                if chunk.retrieved_context and chunk.retrieved_context.media_id:
                    media_id = chunk.retrieved_context.media_id
                    break

    img_b64 = None
    if media_id:
        try:
            # Faz o download do blob do produto referenciado na citação
            img_bytes = await asyncio.to_thread(
                client.file_search_stores.download_media,
                media_id=media_id
            )
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        except Exception as e:
            print(f"[LLMService] Erro ao baixar mídia RAG {media_id}: {e}")

    data = json.loads(response.text)
    return PostContent(**data), img_b64

# --- Novo Fluxo Estruturado de Planejamento ---
from ..schemas.post_schema import PlanejamentoSocialMedia

_SYSTEM_INSTRUCTION_PLANNING = """Você atua como o Diretor de Criação e Social Media de Elite da plataforma OurCore/N1.
Sua tarefa é planejar um cronograma de conteúdo completo para as redes sociais da empresa, consultando o File Search fornecido para obter as regras de marca (tom de voz, nicho) e as especificações de produtos do catálogo.

REGRAS ABSOLUTAS:
1. Obedeça cegamente ao 'Tom de Voz' recuperado através do File Search.
2. Gere um cronograma de planejamento para exatamente a quantidade de dias solicitada.
3. Para cada dia do planejamento, você deve gerar no MÍNIMO 1 conteúdo (pode ser post_unico, carrossel ou storie) e no MÁXIMO 2 conteúdos (ex: 1 post e 1 storie no mesmo dia).
4. Para cada postagem, se ela fizer referência a um produto específico do catálogo indexado no File Search, indique no campo 'nome_produto_referenciado' o nome exato do produto como especificado nas tags do File Search (ex: 'Tênis Nike Branco'). Se for um conteúdo genérico ou conceitual, deixe como null.
5. Se o produto tiver preço cadastrado no File Search, decida de forma inteligente o local do preço ('imagem', 'legenda', ou 'nenhum').
6. Você não deve conversar. Retorne APENAS um objeto JSON válido seguindo estritamente o schema requerido."""

async def planejar_cronograma(objetivo: str, quantidade_dias: int, file_search_store_name: str) -> PlanejamentoSocialMedia:
    client = _client()

    if quantidade_dias == 1:
        estrategia_periodo = "ESTRATÉGIA DIÁRIA: Foco em uma única ação imediata e de alto impacto, otimizada para o tema."
    elif quantidade_dias <= 7:
        estrategia_periodo = "ESTRATÉGIA SEMANAL: Crie um fluxo de engajamento balanceado, variando entre post_unico, stories com enquetes e carrosséis explicativos."
    else:
        estrategia_periodo = (
            "ESTRATÉGIA MENSAL (30 dias): Planeje uma jornada completa de 4 semanas. "
            "Intercale campanhas de vendas com conteúdo de valor do nicho. Evite que o feed fique repetitivo."
        )

    prompt = (
        f"Consulte o seu File Search para obter o contexto da marca (tom de voz, nicho) e do produto cadastrado.\n"
        f"Gere um cronograma de postagens de redes sociais de alta performance.\n"
        f"Diretriz do Período: {estrategia_periodo}\n"
        f"Quantidade de dias planejados: {quantidade_dias} dia(s)\n"
        f"Objetivo do Cronograma (Foco da campanha): {objetivo}\n"
        f"Retorne o planejamento estruturado seguindo o schema JSON requerido."
    )

    tools = [
        types.Tool(
            file_search=types.FileSearch(
                file_search_store_names=[file_search_store_name]
            )
        )
    ]

    response = await asyncio.wait_for(
        client.aio.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_INSTRUCTION_PLANNING,
                response_mime_type="application/json",
                response_schema=PlanejamentoSocialMedia,
                temperature=0.85,
                max_output_tokens=4096,
                tools=tools
            ),
        ),
        timeout=120,
    )

    if response.prompt_feedback and response.prompt_feedback.block_reason:
        raise ValueError(
            f"Conteúdo bloqueado pelos filtros de segurança: {response.prompt_feedback.block_reason}"
        )

    data = json.loads(response.text)
    return PlanejamentoSocialMedia(**data)
