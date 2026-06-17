from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status, Depends
from google.genai.errors import ClientError
import base64
import uuid

from ..core.security import verify_token
from ..models.database import (
    buscar_regra_marca,
    listar_produtos,
    salvar_embedding,
    atualizar_logo_marca,
    atualizar_produto,
    deletar_produto,
    atualizar_regra_marca,
    garantir_rag_store,
    salvar_post_supabase,
    listar_posts_supabase,
    deletar_post_supabase,
    fazer_upload_storage,
)
from ..schemas.post_schema import (
    BrandSetupRequest,
    GeneratePostRequest,
    GeneratePostResponse,
    ListaProdutosResponse,
    PostContent,
    RegenerarImagemRequest,
    RegenerarImagemResponse,
    RegenerarLegendaRequest,
    UpdateProdutoRequest,
    UpdateBrandRequest,
    BrandSetupResponse,
    SalvarPostRequest,
    ListarPostsResponse,
    PostSalvoResponse,
)
from ..services.llm_service import gerar_embedding_documento
from ..services.rag_service import (
    orquestrar_geracao,
    regenerar_imagem,
    regenerar_legenda,
)
from ..services.storage_service import upload_produto, upload_logo


def _erro_gemini(exc: ClientError) -> HTTPException:
    if exc.code == 429:
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Cota da API do Gemini excedida. Aguarde ~1 minuto e tente novamente.",
        )
    if exc.code == 403:
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "A chave da API do Gemini foi bloqueada ou expirou. "
                "Gere uma nova chave gratuita em https://aistudio.google.com/apikey "
                "e atualize GEMINI_API_KEY no arquivo backend/.env."
            ),
        )
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Erro na API do Gemini: {exc.message}",
    )


router = APIRouter(prefix="/api/v1")


@router.post("/gerar-posts", response_model=GeneratePostResponse)
async def gerar_posts(payload: GeneratePostRequest, token: dict = Depends(verify_token)):
    cliente_id = token["sub"]
    try:
        posts = await orquestrar_geracao(
            cliente_id=str(cliente_id),
            foco=payload.foco_semana,
            quantidade=payload.quantidade,
            estilos_imagem=payload.estilos_imagem,
        )
        return GeneratePostResponse(
            status="success",
            posts=posts,
            gerados=len(posts),
            solicitados=payload.quantidade,
        )
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="O Gemini demorou demais para responder ao gerar posts.",
        )
    except ClientError as exc:
        raise _erro_gemini(exc)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/produtos/{cliente_id}", response_model=ListaProdutosResponse)
async def listar_produtos_endpoint(cliente_id: str, token: dict = Depends(verify_token)):
    """Fotos salvas na conta do usuário (para não precisar reenviar)."""
    if token["sub"] != cliente_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não autorizado.")
    produtos = await listar_produtos(cliente_id)
    return ListaProdutosResponse(status="success", produtos=produtos)


@router.put("/produtos/{cliente_id}/{produto_id}")
async def editar_produto_endpoint(
    cliente_id: str,
    produto_id: str,
    payload: UpdateProdutoRequest,
    token: dict = Depends(verify_token)
):
    if token["sub"] != cliente_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não autorizado.")
    try:
        vetor = await gerar_embedding_documento(payload.texto_base)
        await atualizar_produto(cliente_id, produto_id, payload.texto_base, payload.preco, vetor)
        return {"status": "success"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/produtos/{cliente_id}/{produto_id}")
async def deletar_produto_endpoint(
    cliente_id: str,
    produto_id: str,
    token: dict = Depends(verify_token)
):
    if token["sub"] != cliente_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não autorizado.")
    try:
        success = await deletar_produto(cliente_id, produto_id)
        if not success:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/status/{cliente_id}")
async def status_setup(cliente_id: str, token: dict = Depends(verify_token)):
    """Diz se o usuário já cadastrou a marca e as fotos (controla o onboarding)."""
    if token["sub"] != cliente_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não autorizado.")
    
    # Garante a criação da File Search Store do RAG nativo assim que o usuário faz login
    await garantir_rag_store(cliente_id)
    
    marca = await buscar_regra_marca(cliente_id)
    produtos = await listar_produtos(cliente_id)
    
    # Considera marca cadastrada se o texto descritivo estiver preenchido (não vazio)
    tem_marca = marca is not None and marca.get("texto_base", "").strip() != ""
    
    return {
        "status": "success",
        "tem_marca": tem_marca,
        "tem_fotos": len(produtos) > 0,
        "total_fotos": len(produtos),
    }


@router.post("/regenerar-legenda", response_model=PostContent)
async def regenerar_legenda_endpoint(payload: RegenerarLegendaRequest, token: dict = Depends(verify_token)):
    cliente_id = str(payload.cliente_id)
    if token["sub"] != cliente_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não autorizado.")
    try:
        return await regenerar_legenda(
            cliente_id=cliente_id,
            foco=payload.foco_semana,
            produto_id=str(payload.produto_id),
            estilos_imagem=payload.estilos_imagem,
        )
    except ClientError as exc:
        raise _erro_gemini(exc)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/regenerar-imagem", response_model=RegenerarImagemResponse)
async def regenerar_imagem_endpoint(payload: RegenerarImagemRequest, token: dict = Depends(verify_token)):
    cliente_id = str(payload.cliente_id)
    if token["sub"] != cliente_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não autorizado.")
    try:
        img = await regenerar_imagem(
            cliente_id=cliente_id,
            foco=payload.foco_semana,
            produto_id=str(payload.produto_id),
            legenda=payload.legenda,
            estilos_imagem=payload.estilos_imagem,
        )
        return RegenerarImagemResponse(
            status="success",
            imagem_gerada_base64=img,
            imagem_disponivel=img is not None,
        )
    except ClientError as exc:
        raise _erro_gemini(exc)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/upload-produto")
async def upload_produto_endpoint(
    arquivo: UploadFile = File(...),
    cliente_id: str = Form(...),
    texto_base: str = Form(...),
    preco: str = Form(""),
    token: dict = Depends(verify_token),
):
    if token["sub"] != cliente_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não autorizado.")
    try:
        conteudo = await arquivo.read()
        url = await upload_produto(
            raw=conteudo,
            cliente_id=cliente_id,
            nome_arquivo=arquivo.filename or "produto.jpg",
        )
        vetor = await gerar_embedding_documento(texto_base)
        registro = await salvar_embedding(
            cliente_id=cliente_id,
            tipo="produto",
            texto_base=texto_base,
            url_imagem=url,
            vetor=vetor,
            preco=preco,
        )
        return {"status": "success", "id": registro["id"], "url": url}
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="O Gemini demorou demais para processar o produto.",
        )
    except ClientError as exc:
        raise _erro_gemini(exc)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Não foi possível salvar o produto: {exc}",
        )


@router.post("/setup-marca")
async def setup_marca(payload: BrandSetupRequest, token: dict = Depends(verify_token)):
    cliente_id = str(payload.cliente_id)
    if token["sub"] != cliente_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não autorizado.")
    texto = (
        f"Marca: {payload.nome_marca}. "
        f"Tom de Voz: {payload.tom_voz}. "
        f"Nicho: {payload.nicho}. "
        f"{payload.descricao or ''}"
    ).strip()

    metadata = {
        "nome_marca": payload.nome_marca,
        "tom_voz": payload.tom_voz,
        "nicho": payload.nicho,
        "descricao": payload.descricao or "",
    }

    try:
        vetor = await gerar_embedding_documento(texto)
        registro = await salvar_embedding(
            cliente_id=cliente_id,
            tipo="regra_marca",
            texto_base=texto,
            url_imagem="",
            vetor=vetor,
            metadata=metadata,
        )
        return {"status": "success", "id": registro["id"]}
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="O Gemini demorou demais para gerar a marca. Tente novamente.",
        )
    except ClientError as exc:
        raise _erro_gemini(exc)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Não foi possível salvar a marca: {exc}",
        )


@router.get("/setup-marca/{cliente_id}", response_model=BrandSetupResponse)
async def get_marca_endpoint(cliente_id: str, token: dict = Depends(verify_token)):
    if token["sub"] != cliente_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não autorizado.")
    
    marca = await buscar_regra_marca(cliente_id)
    if not marca:
        raise HTTPException(status_code=404, detail="Marca não encontrada")
    
    meta = marca.get("metadata") or {}
    return BrandSetupResponse(
        id=marca["id"],
        nome_marca=meta.get("nome_marca", ""),
        tom_voz=meta.get("tom_voz", ""),
        nicho=meta.get("nicho", ""),
        descricao=meta.get("descricao", ""),
        url_logo=marca.get("url_imagem", "")
    )


@router.put("/setup-marca/{cliente_id}")
async def editar_marca_endpoint(
    cliente_id: str,
    payload: UpdateBrandRequest,
    token: dict = Depends(verify_token)
):
    if token["sub"] != cliente_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não autorizado.")
    
    marca = await buscar_regra_marca(cliente_id)
    if not marca:
        raise HTTPException(status_code=404, detail="Marca não encontrada")

    texto = (
        f"Marca: {payload.nome_marca}. "
        f"Tom de Voz: {payload.tom_voz}. "
        f"Nicho: {payload.nicho}. "
        f"{payload.descricao or ''}"
    ).strip()

    metadata = {
        "nome_marca": payload.nome_marca,
        "tom_voz": payload.tom_voz,
        "nicho": payload.nicho,
        "descricao": payload.descricao or "",
    }

    try:
        vetor = await gerar_embedding_documento(texto)
        await atualizar_regra_marca(cliente_id, marca["id"], texto, metadata, vetor)
        return {"status": "success"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/upload-logo")
async def upload_logo_endpoint(
    arquivo: UploadFile = File(...),
    cliente_id: str = Form(...),
    token: dict = Depends(verify_token),
):
    if token["sub"] != cliente_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não autorizado.")
    try:
        conteudo = await arquivo.read()
        url = await upload_logo(
            raw=conteudo,
            cliente_id=cliente_id,
            nome_arquivo=f"logo_{arquivo.filename or 'logo.png'}",
        )
        registro = await atualizar_logo_marca(cliente_id, url)
        if not registro:
             raise HTTPException(status_code=404, detail="Regra de marca não encontrada. Faça o setup primeiro.")
        return {"status": "success", "url_logo": url}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Não foi possível salvar a logo: {exc}",
        )


@router.post("/posts/salvar")
async def salvar_post(payload: SalvarPostRequest, token: dict = Depends(verify_token)):
    if token["sub"] != str(payload.cliente_id):
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não autorizado.")
    
    try:
        imagem_url = None
        if payload.imagem_gerada_base64:
            img_bytes = base64.b64decode(payload.imagem_gerada_base64)
            nome_arquivo = f"gerado_{uuid.uuid4()}.jpg"
            imagem_url = await fazer_upload_storage("posts-gerados", f"{payload.cliente_id}/posts/{nome_arquivo}", img_bytes)
        elif payload.produto_url:
            imagem_url = payload.produto_url
            
        carrossel_urls = []
        if payload.imagens_carrossel_base64:
            for i, img_b64 in enumerate(payload.imagens_carrossel_base64):
                c_bytes = base64.b64decode(img_b64)
                nome_c = f"gerado_{uuid.uuid4()}_slide_{i+1}.jpg"
                c_url = await fazer_upload_storage("posts-gerados", f"{payload.cliente_id}/posts/{nome_c}", c_bytes)
                carrossel_urls.append(c_url)
                
        registro = await salvar_post_supabase(
            cliente_id=str(payload.cliente_id),
            titulo_interno=payload.titulo_interno,
            legenda_instagram=payload.legenda_instagram,
            sugestao_de_edicao_visual=payload.sugestao_de_edicao_visual,
            hashtags=payload.hashtags,
            local_do_preco=payload.local_do_preco,
            produto_id=payload.produto_id,
            produto_url=payload.produto_url,
            imagem_url=imagem_url,
            imagens_carrossel_urls=carrossel_urls,
            imagem_disponivel=payload.imagem_disponivel
        )
        return {"status": "success", "id": registro["id"]}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Não foi possível salvar o post: {exc}"
        )


@router.get("/posts/{cliente_id}", response_model=ListarPostsResponse)
async def listar_posts_endpoint(cliente_id: str, token: dict = Depends(verify_token)):
    if token["sub"] != cliente_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não autorizado.")
    try:
        registros = await listar_posts_supabase(cliente_id)
        posts = [
            PostSalvoResponse(
                id=r["id"],
                cliente_id=r["cliente_id"],
                titulo_interno=r["titulo_interno"],
                legenda_instagram=r["legenda_instagram"],
                sugestao_de_edicao_visual=r["sugestao_de_edicao_visual"],
                hashtags=r["hashtags"],
                local_do_preco=r["local_do_preco"],
                produto_id=r.get("produto_id"),
                produto_url=r.get("produto_url"),
                imagem_url=r.get("imagem_url"),
                imagens_carrossel_urls=r.get("imagens_carrossel_urls") or [],
                imagem_disponivel=r["imagem_disponivel"],
                created_at=r["created_at"]
            )
            for r in registros
        ]
        return ListarPostsResponse(status="success", posts=posts)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/posts/{post_id}")
async def deletar_post_endpoint(post_id: str, token: dict = Depends(verify_token)):
    try:
        sucesso = await deletar_post_supabase(post_id)
        if not sucesso:
            raise HTTPException(status_code=404, detail="Post não encontrado")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
