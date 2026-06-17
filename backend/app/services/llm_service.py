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

_SYSTEM_INSTRUCTION = """Você atua como o Motor de Criação Cérebro. \
Sua função primária é agir como um Diretor de Arte e Copywriter Sênior de Elite para a marca informada. \
Você deve consultar o File Search fornecido para obter as regras de marca (tom de voz, nicho) e as informações do produto relevante para o post.

REGRAS ABSOLUTAS DE PRIORIDADE MÁXIMA:
1. O TOM DE VOZ DA MARCA DEVE SER SEGUIDO COM RIGOR ABSOLUTO E CEGAMENTE! Analise profundamente o 'Tom de Voz' e a personalidade da marca no File Search. A legenda gerada DEVE soar exatamente como se a própria marca a estivesse escrevendo e falando. Adapte gírias, formalidade, vocabulário e estilo de escrita de maneira impecável.
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


async def _generate_content_with_retry(
    client: genai.Client,
    model: str,
    contents: str,
    config: types.GenerateContentConfig,
    timeout: int,
    retries: int = 3,
    delay: float = 2.0
):
    for attempt in range(retries):
        try:
            return await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                ),
                timeout=timeout,
            )
        except Exception as exc:
            if attempt < retries - 1:
                print(f"[LLM Retry] Falha na tentativa {attempt + 1} de {retries} com o modelo {model} ({exc}). Aguardando {delay}s antes de tentar novamente...")
                await asyncio.sleep(delay)
            else:
                raise exc


async def gerar_post(objetivo: str, file_search_store_name: str, nome_marca: str = "") -> tuple[PostContent, str | None]:
    """Gera um post utilizando a ferramenta File Search (RAG Nativo) do Gemini."""
    client = _client()

    prompt = (
        f"Nome da Marca: {nome_marca}\n"
        f"Consulte o seu File Search para obter o contexto da marca (tom de voz, nicho) e do produto cadastrado. "
        f"O nome da marca deve ser OBRIGATORIAMENTE '{nome_marca}' em todas as legendas e referências geradas. NUNCA utilize o nome 'OurCore' ou qualquer outra marca.\n"
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

    config = types.GenerateContentConfig(
        system_instruction=_SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=_POST_SCHEMA,
        temperature=0.85,
        max_output_tokens=2048,
        tools=tools
    )

    try:
        # Tenta com o gemini-3.5-flash: 5 tentativas com delay de 3.0s
        response = await _generate_content_with_retry(
            client=client,
            model="gemini-3.5-flash",
            contents=prompt,
            config=config,
            timeout=180,
            retries=5,
            delay=3.0
        )
    except Exception as exc:
        print(f"[LLM Fallback] Todas as 5 tentativas com gemini-3.5-flash falharam ({exc}). Fazendo fallback para gemini-3.1-flash-lite...")
        # Adaptamos o prompt para forçar formato JSON no gemini-3.1-flash-lite, pois não usaremos response_schema no fallback
        prompt_lite = (
            f"{prompt}\n\n"
            "ATENÇÃO FORMATO DE RESPOSTA:\n"
            "Você DEVE retornar APENAS um objeto JSON válido de acordo com o seguinte formato, sem formatação markdown (como ```json) e sem introduções. "
            "A legenda contida no JSON deve seguir com RIGOR MÁXIMO ABSOLUTO o tom de voz da marca contido no File Search:\n"
            "{\n"
            "  \"titulo_interno\": \"string\",\n"
            "  \"legenda_instagram\": \"string\",\n"
            "  \"sugestao_de_edicao_visual\": \"string\",\n"
            "  \"hashtags\": [\"string\"],\n"
            "  \"local_do_preco\": \"imagem\" ou \"legenda\" ou \"nenhum\"\n"
            "}"
        )
        
        config_lite = types.GenerateContentConfig(
            system_instruction=_SYSTEM_INSTRUCTION,
            temperature=0.85,
            max_output_tokens=2048,
            tools=tools
        )
        
        response = await _generate_content_with_retry(
            client=client,
            model="gemini-3.1-flash-lite",
            contents=prompt_lite,
            config=config_lite,
            timeout=180,
            retries=3,
            delay=2.0
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

    # Limpeza de possíveis formatações markdown do JSON retornado (necessário especialmente para chamadas sem response_schema)
    text = response.text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
        text = text.strip()

    try:
        data = json.loads(text)
        post_content = PostContent(**data)
    except Exception as parse_exc:
        print(f"[LLMService] Erro ao parsear ou validar JSON no gerar_post. Texto bruto gerado:\n{text}")
        raise parse_exc
    return post_content, img_b64

# --- Novo Fluxo Estruturado de Planejamento ---
from ..schemas.post_schema import PlanejamentoSocialMedia

_SYSTEM_INSTRUCTION_PLANNING = """Você atua como o Diretor de Criação e Social Media de Elite.
Sua tarefa é planejar um cronograma de conteúdo completo para as redes sociais da marca, consultando o File Search fornecido para obter as regras de marca (tom de voz, nicho) e as especificações de produtos do catálogo.

REGRAS ABSOLUTAS DE PRIORIDADE MÁXIMA:
1. O TOM DE VOZ DA MARCA DEVE SER SEGUIDO COM RIGOR ABSOLUTO EM TODAS AS LEGENDAS! Analise profundamente o 'Tom de Voz' e a personalidade da marca no File Search. Cada legenda, texto de post ou storie DEVE refletir perfeitamente esse tom de voz.
2. Gere um cronograma de planejamento para exatamente a quantidade de dias solicitada.
3. Para cada dia do planejamento, você deve gerar no MÍNIMO 1 conteúdo (pode ser post_unico ou storie) e no MÁXIMO 2 conteúdos (ex: 1 post e 1 storie no mesmo dia).
4. Para cada postagem, se ela fizer referência a um produto específico do catálogo indexado no File Search, indique no campo 'nome_produto_referenciado' o nome exato do produto como especificado nas tags do File Search (ex: 'Tênis Nike Branco'). Se for um conteúdo genérico ou conceitual, deixe como null.
5. Se o produto tiver preço cadastrado no File Search, decida de forma inteligente o local do preço ('imagem', 'legenda', ou 'nenhum').
6. A chave que indica o número do dia dentro de cada item da lista 'cronograma' deve ser EXATAMENTE e LITERALMENTE 'dia_numero'. NUNCA use nomes de chaves dinâmicos como 'dia_numero_1', 'dia_numero_2', etc.
7. Você não deve conversar. Retorne APENAS um objeto JSON válido seguindo estritamente o schema requerido."""

async def planejar_cronograma(objetivo: str, quantidade_dias: int, file_search_store_name: str, nome_marca: str = "") -> PlanejamentoSocialMedia:
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

    if quantidade_dias == 1:
        diretriz_objetivo = f"Objetivo do Post (Foco da campanha): {objetivo or 'institucional geral / branding'}\n"
    else:
        if objetivo and objetivo.strip():
            diretriz_objetivo = f"O usuário informou o seguinte nicho/foco geral: '{objetivo}'. No entanto, como este planejamento é para múltiplos dias ({quantidade_dias} dias), você está 100% LIVRE e incentivado a criar e propor outros temas relevantes, variados e interessantes que se alinhem com o nicho e com o catálogo de produtos no File Search. Não fique limitado a falar apenas sobre '{objetivo}' em todos os dias; varie as campanhas de marketing para que o cronograma fique dinâmico e rico.\n"
        else:
            diretriz_objetivo = f"Como o usuário não definiu um foco ou tema de campanha específico para este planejamento de múltiplos dias ({quantidade_dias} dias), você tem 100% de LIBERDADE para selecionar livremente temas criativos, diversificados e relevantes que se alinhem com a personalidade da marca e com os produtos indexados no seu catálogo (File Search). Planeje uma jornada engajadora e diversificada de postagens.\n"

    prompt = (
        f"Nome da Marca: {nome_marca}\n"
        f"Consulte o seu File Search para obter o contexto da marca (tom de voz, nicho) e do produto cadastrado. "
        f"O nome da marca é '{nome_marca}' e todas as legendas do planejamento devem usar OBRIGATORIAMENTE este nome de marca quando referenciada. NUNCA mencione 'OurCore' ou qualquer outra marca nas legendas e roteiros.\n"
        f"Gere um cronograma de postagens de redes sociais de alta performance.\n"
        f"Diretriz do Período: {estrategia_periodo}\n"
        f"Quantidade de dias planejados: {quantidade_dias} dia(s)\n"
        f"{diretriz_objetivo}"
        f"Retorne o planejamento estruturado seguindo o schema JSON requerido."
    )

    tools = [
        types.Tool(
            file_search=types.FileSearch(
                file_search_store_names=[file_search_store_name]
            )
        )
    ]

    config = types.GenerateContentConfig(
        system_instruction=_SYSTEM_INSTRUCTION_PLANNING,
        response_mime_type="application/json",
        response_schema=PlanejamentoSocialMedia,
        temperature=0.85,
        max_output_tokens=4096,
        tools=tools
    )

    try:
        # Tenta com o gemini-3.5-flash: 5 tentativas com delay de 3.0s
        response = await _generate_content_with_retry(
            client=client,
            model="gemini-3.5-flash",
            contents=prompt,
            config=config,
            timeout=240,
            retries=5,
            delay=3.0
        )
    except Exception as exc:
        print(f"[LLM Fallback] Todas as 5 tentativas com gemini-3.5-flash falharam ({exc}). Fazendo fallback para gemini-3.1-flash-lite...")
        # Para o cronograma de planejamento, definimos a instrução do schema em formato legível de texto
        schema_instrucao = (
            "{\n"
            "  \"empresa_nome\": \"string (Nome da empresa analisada)\",\n"
            "  \"tom_de_voz_aplicado\": \"string (Breve justificativa de como o tom de voz foi adaptado nas legendas)\",\n"
            "  \"cronograma\": [\n"
            "    {\n"
            "      \"dia_numero\": 1,\n"
            "      \"conteudos\": [\n"
            "        {\n"
            "          \"tipo\": \"post_unico\" ou \"storie\",\n"
            "          \"numero_imagens_carrossel\": null,\n"
            "          \"descricao_visual\": \"Descrição detalhada da imagem ou arte\",\n"
            "          \"elementos_storie\": \"Enquetes ou interações se o tipo for storie, ou null\",\n"
            "          \"legenda\": \"Texto final da legenda do post ou roteiro falado do storie (CAMPO OBRIGATÓRIO, NUNCA DEVE SER NULO OU OMITIDO. DEVE SEGUIR RIGOROSAMENTE E EM DETALHES O TOM DE VOZ DA MARCA)\",\n"
            "          \"nome_produto_referenciado\": \"Nome do produto no catálogo ou null\",\n"
            "          \"local_do_preco\": \"imagem\" ou \"legenda\" ou \"nenhum\",\n"
            "          \"hashtags\": [\"#tag1\", \"#tag2\"]\n"
            "        }\n"
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}"
        )
        prompt_lite = (
            f"{prompt}\n\n"
            "ATENÇÃO FORMATO DE RESPOSTA:\n"
            "Você DEVE retornar APENAS um objeto JSON válido de acordo com a seguinte estrutura, sem formatação markdown (como ```json) e sem qualquer outro texto explicativo:\n"
            f"{schema_instrucao}"
        )
        
        config_lite = types.GenerateContentConfig(
            system_instruction=_SYSTEM_INSTRUCTION_PLANNING,
            temperature=0.85,
            max_output_tokens=4096,
            tools=tools
        )
        
        response = await _generate_content_with_retry(
            client=client,
            model="gemini-3.1-flash-lite",
            contents=prompt_lite,
            config=config_lite,
            timeout=240,
            retries=3,
            delay=2.0
        )

    if response.prompt_feedback and response.prompt_feedback.block_reason:
        raise ValueError(
            f"Conteúdo bloqueado pelos filtros de segurança: {response.prompt_feedback.block_reason}"
        )

    # Limpeza de possíveis formatações markdown do JSON retornado (necessário especialmente para chamadas sem response_schema)
    text = response.text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
        text = text.strip()

    try:
        data = json.loads(text)
        # Normalização de chaves alucinadas do dia (ex: dia_numero_5 em vez de dia_numero)
        if isinstance(data, dict) and "cronograma" in data and isinstance(data["cronograma"], list):
            for item in data["cronograma"]:
                if isinstance(item, dict):
                    chaves_para_corrigir = [k for k in item.keys() if k.startswith("dia_numero") and k != "dia_numero"]
                    for k in chaves_para_corrigir:
                        item["dia_numero"] = item.pop(k)
        planejamento = PlanejamentoSocialMedia(**data)
    except Exception as parse_exc:
        print(f"[LLMService] Erro ao parsear ou validar JSON no planejar_cronograma. Texto bruto gerado:\n{text}")
        raise parse_exc
    return planejamento
