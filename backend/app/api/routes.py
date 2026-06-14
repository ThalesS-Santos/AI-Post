from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from google.genai.errors import ClientError

from ..models.database import salvar_embedding
from ..schemas.post_schema import (
    BrandSetupRequest,
    GeneratePostRequest,
    GeneratePostResponse,
)
from ..services.llm_service import gerar_embedding_documento
from ..services.rag_service import orquestrar_geracao
from ..services.storage_service import upload_produto

router = APIRouter(prefix="/api/v1")


@router.post("/gerar-posts", response_model=GeneratePostResponse)
async def gerar_posts(payload: GeneratePostRequest):
    try:
        posts = await orquestrar_geracao(
            cliente_id=str(payload.cliente_id),
            foco=payload.foco_semana,
            quantidade=payload.quantidade,
        )
        return GeneratePostResponse(status="success", posts=posts)
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="O Gemini demorou demais para responder ao gerar posts.",
        )
    except ClientError as exc:
        if exc.code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Cota da API do Gemini excedida. Aguarde ~1 minuto e tente novamente.",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro na API do Gemini: {exc.message}",
        )
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
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Não foi possível salvar a marca: {exc}",
        )
