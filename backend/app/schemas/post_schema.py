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
    imagens_carrossel_base64: List[str] = Field(default_factory=list)


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

# --- Novos Schemas Estruturados para Planejamento ---
from typing import Literal

class ConteudoMidia(BaseModel):
    tipo: Literal["post_unico", "carrossel", "storie"] = Field(
        description="O formato do conteúdo na rede social."
    )
    numero_imagens_carrossel: Optional[int] = Field(
        default=None, 
        description="Se o tipo for 'carrossel', defina o número de imagens (ex: 4). Caso contrário, deixe nulo."
    )
    descricao_visual: str = Field(
        description="Descrição detalhada do que deve aparecer na imagem/arte ou no frame do Storie."
    )
    elementos_storie: Optional[str] = Field(
        default=None,
        description="Se for Storie, indique elementos interativos (ex: 'Enquete: Você prefere A ou B?', 'Caixinha de perguntas', 'Link')."
    )
    legenda: str = Field(
        description="Texto final da legenda do post ou roteiro falado/escrito do storie. Deve seguir RIGOROSAMENTE o tom de voz da empresa informado no prompt."
    )
    nome_produto_referenciado: Optional[str] = Field(
        default=None,
        description="Nome exato do produto que foi referenciado neste post (baseado no catálogo do File Search), ou null se for um post genérico institucional/conteúdo."
    )
    local_do_preco: Literal["imagem", "legenda", "nenhum"] = Field(
        default="nenhum",
        description="Onde o preço deve ser exibido: 'imagem' para destaque, 'legenda' para texto informativo, ou 'nenhum' se não houver preço."
    )
    hashtags: List[str] = Field(
        default_factory=list,
        description="Lista de hashtags sugeridas para esta postagem."
    )

class DiaPlanejamento(BaseModel):
    dia_numero: int = Field(description="O número do dia no cronograma (ex: 1, 2, 3...)")
    conteudos: List[ConteudoMidia] = Field(
        description="Lista de conteúdos planejados para este dia específico (mínimo 1, máximo 2 se houver post e storie)."
    )

class PlanejamentoSocialMedia(BaseModel):
    empresa_nome: str = Field(description="Nome da empresa analisada.")
    tom_de_voz_aplicado: str = Field(description="Breve justificativa de como o tom de voz foi adaptado nas legendas.")
    cronograma: List[DiaPlanejamento] = Field(description="Lista contendo o planejamento dia após dia.")
