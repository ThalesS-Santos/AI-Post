import asyncio
from google.genai.errors import ClientError

from ..models.database import (
    buscar_regra_marca,
    listar_produtos,
    buscar_produto_por_id,
)
from ..schemas.post_schema import PostContent, ConteudoMidia
from .image_service import gerar_imagem_ia
from .llm_service import gerar_post, planejar_cronograma
from .storage_service import baixar_imagem, para_base64


async def _gerar_imagem_para_conteudo(
    midia: ConteudoMidia,
    dia_numero: int,
    foco: str,
    estilos_imagem: list[str] = None,
    logo_url: str = "",
    todos_produtos: list[dict] = None,
    index: int = 0,
    tom_voz: str = ""
) -> PostContent:
    """Gera a imagem e mapeia para o formato PostContent do frontend."""
    # 1) Mapeia do ConteudoMidia estruturado para o PostContent
    tipo_display = midia.tipo.replace("_", " ").title()
    t_interno = f"Dia {dia_numero} - {tipo_display}"
    if midia.numero_imagens_carrossel:
        t_interno += f" ({midia.numero_imagens_carrossel} imagens)"

    legenda_completa = midia.legenda
    if midia.elementos_storie:
        legenda_completa += f"\n\n[Dica de Interação: {midia.elementos_storie}]"

    post = PostContent(
        titulo_interno=t_interno,
        legenda_instagram=legenda_completa,
        sugestao_de_edicao_visual=midia.descricao_visual,
        hashtags=midia.hashtags or [],
        local_do_preco=midia.local_do_preco
    )

    # 2) Encontra imagem correspondente do produto no catálogo local
    matching_prod = None
    img_b64 = None

    if midia.nome_produto_referenciado:
        for prod in (todos_produtos or []):
            if midia.nome_produto_referenciado.lower().strip() in prod.get("texto_base", "").lower():
                matching_prod = prod
                break

    if matching_prod:
        try:
            raw = await baixar_imagem(matching_prod["url_imagem"])
            img_b64 = para_base64(raw)
            post.produto_id = str(matching_prod["id"])
            post.produto_url = matching_prod["url_imagem"]
            post.imagem_disponivel = True
        except Exception as e:
            print(f"[RAGService] Erro ao baixar imagem do produto referenciado ({matching_prod['texto_base']}): {e}")

    # Fallback: Se não casou nome de produto ou falhou download, mas há produtos no catálogo
    if not img_b64 and todos_produtos:
        fallback_prod = todos_produtos[index % len(todos_produtos)]
        try:
            raw = await baixar_imagem(fallback_prod["url_imagem"])
            img_b64 = para_base64(raw)
            post.produto_id = str(fallback_prod["id"])
            post.produto_url = fallback_prod["url_imagem"]
            post.imagem_disponivel = True
        except Exception as e:
            print(f"[RAGService] Erro ao baixar imagem de fallback: {e}")

    # 3) Renderiza a(s) imagem(ns) final(is) de marketing por IA usando gemini-3.1-flash-image
    if img_b64:
        aspect_ratio = "9:16" if midia.tipo == "storie" else "1:1"
        
        # Post Único ou Storie
        img_marketing = await gerar_imagem_ia(
            legenda=post.legenda_instagram, 
            produto_b64=img_b64, 
            tema=foco,
            descricao_produto=post.titulo_interno,
            estilos_imagem=estilos_imagem,
            logo_url=logo_url,
            preco=matching_prod.get("preco", "") if matching_prod else "",
            local_do_preco=post.local_do_preco,
            aspect_ratio=aspect_ratio,
            tom_voz=tom_voz
        )
        if img_marketing:
            post.imagem_gerada_base64 = img_marketing
            post.imagem_disponivel = True
            post.imagens_carrossel_base64 = [img_marketing]

    return post


async def orquestrar_geracao(
    cliente_id: str,
    foco: str,
    quantidade: int,
    estilos_imagem: list[str] = None,
) -> list[PostContent]:
    marca = await buscar_regra_marca(cliente_id)
    if not marca:
        raise ValueError("Configure sua marca primeiro (nome, tom de voz e nicho).")
        
    store_name = marca.get("metadata", {}).get("file_search_store_name")
    if not store_name:
        raise ValueError("File Search Store da marca não encontrada. Atualize suas configurações de marca.")
        
    logo_url = marca.get("url_imagem", "")
    tom_voz = marca.get("metadata", {}).get("tom_voz", "")
    nome_marca = marca.get("metadata", {}).get("nome_marca", "")
    todos_produtos = await listar_produtos(cliente_id)
 
    # 1. Faz o planejamento estruturado geral em uma única chamada
    cronograma_plan = await planejar_cronograma(
        objetivo=foco,
        quantidade_dias=quantidade,
        file_search_store_name=store_name,
        nome_marca=nome_marca
    )
    
    # 2. Desmembra as postagens planejadas e cria tarefas para gerar as mídias em paralelo
    tarefas = []
    idx = 0
    for dia in cronograma_plan.cronograma:
        for midia in dia.conteudos:
            tarefas.append(
                _gerar_imagem_para_conteudo(
                    midia=midia,
                    dia_numero=dia.dia_numero,
                    foco=foco,
                    estilos_imagem=estilos_imagem,
                    logo_url=logo_url,
                    todos_produtos=todos_produtos,
                    index=idx,
                    tom_voz=tom_voz
                )
            )
            idx += 1
        
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


async def regenerar_legenda(cliente_id: str, foco: str, produto_id: str, estilos_imagem: list[str] = None) -> PostContent:
    """Refaz a legenda consultando o RAG Store da marca."""
    marca = await buscar_regra_marca(cliente_id)
    store_name = marca.get("metadata", {}).get("file_search_store_name") if marca else None
    if not store_name:
        raise ValueError("File Search Store da marca não encontrada.")
    nome_marca = marca.get("metadata", {}).get("nome_marca", "") if marca else ""
    post, _ = await gerar_post(objetivo=foco, file_search_store_name=store_name, nome_marca=nome_marca)
    return post


async def regenerar_imagem(
    cliente_id: str,
    foco: str,
    produto_id: str,
    legenda: str,
    estilos_imagem: list[str] = None,
) -> str | None:
    """Refaz a imagem a partir de uma foto de produto do catálogo."""
    produto = await buscar_produto_por_id(cliente_id, produto_id)
    if not produto:
        raise ValueError("Foto não encontrada.")
    raw = await baixar_imagem(produto["url_imagem"])
    b64 = para_base64(raw)
    
    marca = await buscar_regra_marca(cliente_id)
    logo_url = marca.get("url_imagem", "") if marca else ""
    tom_voz = marca.get("metadata", {}).get("tom_voz", "") if marca else ""
    
    return await gerar_imagem_ia(
        legenda=legenda, 
        produto_b64=b64, 
        tema=foco,
        descricao_produto=produto.get("texto_base", ""),
        estilos_imagem=estilos_imagem,
        logo_url=logo_url,
        preco=produto.get("preco", ""),
        local_do_preco="nenhum",
        tom_voz=tom_voz
    )
