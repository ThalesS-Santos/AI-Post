from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from google.genai.errors import ClientError

from ..models.database import (
    buscar_regra_marca,
    listar_produtos,
    salvar_embedding,
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
)
from ..services.llm_service import gerar_embedding_documento
from ..services.rag_service import (
    orquestrar_geracao,
    regenerar_imagem,
    regenerar_legenda,
)
from ..services.storage_service import upload_produto


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
async def gerar_posts(payload: GeneratePostRequest):
    try:
        posts = await orquestrar_geracao(
            cliente_id=str(payload.cliente_id),
            foco=payload.foco_semana,
            quantidade=payload.quantidade,
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
async def listar_produtos_endpoint(cliente_id: str):
    """Fotos salvas na conta do usuário (para não precisar reenviar)."""
    produtos = await listar_produtos(cliente_id)
    return ListaProdutosResponse(status="success", produtos=produtos)


@router.get("/status/{cliente_id}")
async def status_setup(cliente_id: str):
    """Diz se o usuário já cadastrou a marca e as fotos (controla o onboarding)."""
    marca = await buscar_regra_marca(cliente_id)
    produtos = await listar_produtos(cliente_id)
    return {
        "status": "success",
        "tem_marca": marca is not None,
        "tem_fotos": len(produtos) > 0,
        "total_fotos": len(produtos),
    }


@router.post("/regenerar-legenda", response_model=PostContent)
async def regenerar_legenda_endpoint(payload: RegenerarLegendaRequest):
    try:
        return await regenerar_legenda(
            cliente_id=str(payload.cliente_id),
            foco=payload.foco_semana,
            produto_id=str(payload.produto_id),
        )
    except ClientError as exc:
        raise _erro_gemini(exc)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/regenerar-imagem", response_model=RegenerarImagemResponse)
async def regenerar_imagem_endpoint(payload: RegenerarImagemRequest):
    try:
        img = await regenerar_imagem(
            cliente_id=str(payload.cliente_id),
            foco=payload.foco_semana,
            produto_id=str(payload.produto_id),
            legenda=payload.legenda,
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
):
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
async def setup_marca(payload: BrandSetupRequest):
    texto = (
        f"Marca: {payload.nome_marca}. "
        f"Tom de Voz: {payload.tom_voz}. "
        f"Nicho: {payload.nicho}. "
        f"{payload.descricao or ''}"
    ).strip()

    try:
        vetor = await gerar_embedding_documento(texto)
        registro = await salvar_embedding(
            cliente_id=str(payload.cliente_id),
            tipo="regra_marca",
            texto_base=texto,
            url_imagem="",
            vetor=vetor,
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
