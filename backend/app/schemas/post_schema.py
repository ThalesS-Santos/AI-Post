from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID


class GeneratePostRequest(BaseModel):
    cliente_id: UUID
    foco_semana: str = Field(..., min_length=3, max_length=500)
    quantidade: int = Field(default=7, ge=1, le=30)


class PostContent(BaseModel):
    titulo_interno: str
    legenda_instagram: str
    sugestao_de_edicao_visual: str
    hashtags: List[str]


class GeneratePostResponse(BaseModel):
    status: str
    posts: List[PostContent]


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
