from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID


class GeneratePostRequest(BaseModel):
    cliente_id: UUID
    foco_semana: str = Field(..., min_length=3, max_length=500)
    quantidade: int = Field(default=7, ge=1, le=30)
    estilos_imagem: List[str] = Field(default_factory=list, max_items=2)


class PostContent(BaseModel):
    # --- vem do JSON do Gemini ---
    titulo_interno: str
    legenda_instagram: str
    sugestao_de_edicao_visual: str
    hashtags: List[str]
    local_do_preco: str = "nenhum"
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
    estilos_imagem: List[str] = Field(default_factory=list, max_items=2)


class RegenerarImagemRequest(BaseModel):
    cliente_id: UUID
    foco_semana: str = Field(..., min_length=3, max_length=500)
    produto_id: UUID
    legenda: str = Field(..., min_length=1, max_length=3000)
    estilos_imagem: List[str] = Field(default_factory=list, max_items=2)


class RegenerarImagemResponse(BaseModel):
    status: str
    imagem_gerada_base64: Optional[str] = None
    imagem_disponivel: bool = False


class ProdutoSalvo(BaseModel):
    id: str
    texto_base: str
    url_imagem: str
    preco: Optional[str] = ""


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

class UpdateProdutoRequest(BaseModel):
    texto_base: str = Field(..., min_length=2, max_length=1000)
    preco: str = Field(default="")

class UpdateBrandRequest(BrandSetupRequest):
    pass

class BrandSetupResponse(BaseModel):
    id: str
    nome_marca: str
    tom_voz: str
    nicho: str
    descricao: str
    url_logo: str
