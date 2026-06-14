from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID


class GeneratePostRequest(BaseModel):
    cliente_id: UUID
    foco_semana: str = Field(..., min_length=3, max_length=500)
    quantidade: int = Field(default=7, ge=1, le=30)


class PostContent(BaseModel):
    # --- vem do JSON do Gemini ---
    titulo_interno: str
    legenda_instagram: str
    sugestao_de_edicao_visual: str
    hashtags: List[str]
    # --- preenchido pelo orquestrador (não vem do Gemini) ---
    produto_id: Optional[str] = None
    produto_url: Optional[str] = None
    imagem_gerada_base64: Optional[str] = None
    imagem_disponivel: bool = False


class GeneratePostResponse(BaseModel):
    status: str
    posts: List[PostContent]
    gerados: int = 0
    solicitados: int = 0


class RegenerarLegendaRequest(BaseModel):
    cliente_id: UUID
    foco_semana: str = Field(..., min_length=3, max_length=500)
    produto_id: UUID


class RegenerarImagemRequest(BaseModel):
    cliente_id: UUID
    foco_semana: str = Field(..., min_length=3, max_length=500)
    produto_id: UUID
    legenda: str = Field(..., min_length=1, max_length=3000)


class RegenerarImagemResponse(BaseModel):
    status: str
    imagem_gerada_base64: Optional[str] = None
    imagem_disponivel: bool = False


class ProdutoSalvo(BaseModel):
    id: str
    texto_base: str
    url_imagem: str


class ListaProdutosResponse(BaseModel):
    status: str
    produtos: List[ProdutoSalvo]


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    code: int


class BrandSetupRequest(BaseModel):
    cliente_id: UUID
    nome_marca: str = Field(..., min_length=2, max_length=100)
    tom_voz: str = Field(..., min_length=5, max_length=500)
    nicho: str = Field(..., min_length=2, max_length=100)
    descricao: Optional[str] = Field(None, max_length=1000)
