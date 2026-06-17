from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field


class CategoriaBase(BaseModel):
    nome: str = Field(..., max_length=200)
    descricao: Optional[str] = None

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaResponse(CategoriaBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ItemBase(BaseModel):
    codigo: str = Field(..., max_length=100)
    codigo_usp: Optional[str] = None
    nome: str = Field(..., max_length=300)
    descricao: Optional[str] = None
    nome_comercial: Optional[str] = None
    unidade_medida: str = "un"
    quantidade_minima: float = 0
    quantidade_atual: float = 0
    quantidade_maxima: float = 0
    localizacao: Optional[str] = None
    solicitar_por_email: bool = False
    status: str = "disponivel"
    tipo_controle: str = "almoxarifado"
    categoria_id: Optional[int] = None
    fornecedor_id: Optional[int] = None
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    valor_unitario: float = 0
    observacoes: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    unidade_medida: Optional[str] = None
    quantidade_atual: Optional[float] = None
    quantidade_minima: Optional[float] = None
    quantidade_maxima: Optional[float] = None
    localizacao: Optional[str] = None
    solicitar_por_email: Optional[bool] = None
    nome_comercial: Optional[str] = None
    status: Optional[str] = None
    tipo_controle: Optional[str] = None
    categoria_id: Optional[int] = None
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    valor_unitario: Optional[float] = None
    observacoes: Optional[str] = None

class ItemResponse(ItemBase):
    id: int
    created_at: datetime
    updated_at: datetime
    categoria_nome: Optional[str] = None
    fornecedor_nome: Optional[str] = None

    class Config:
        from_attributes = True

class ItemEstoqueBaixo(BaseModel):
    id: int
    codigo: str
    nome: str
    quantidade_atual: float
    quantidade_minima: float
    diferenca: float


class MovimentacaoBase(BaseModel):
    item_id: int
    tipo: str
    quantidade: float = Field(..., gt=0)
    responsavel: Optional[str] = None
    destino: Optional[str] = None
    documento_referencia: Optional[str] = None
    observacoes: Optional[str] = None

class MovimentacaoCreate(MovimentacaoBase):
    pass

class MovimentacaoResponse(MovimentacaoBase):
    id: int
    data_movimentacao: datetime
    created_at: datetime
    item_nome: Optional[str] = None
    item_codigo: Optional[str] = None

    class Config:
        from_attributes = True


class FornecedorBase(BaseModel):
    nome: str = Field(..., max_length=300)
    cnpj: Optional[str] = None
    contato: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    observacoes: Optional[str] = None

class FornecedorCreate(FornecedorBase):
    pass

class FornecedorResponse(FornecedorBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UsuarioCreate(BaseModel):
    username: str = Field(..., max_length=100)
    email: Optional[str] = None
    nome_completo: Optional[str] = None
    password: str = Field(..., min_length=6)
    is_externo: bool = False

class UsuarioResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    nome_completo: Optional[str] = None
    is_admin: bool
    is_externo: bool
    ativo: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)


class ImportacaoResponse(BaseModel):
    id: int
    nome_arquivo: Optional[str]
    tipo_origem: Optional[str]
    total_registros: int
    importados: int
    erros: int
    detalhes: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardData(BaseModel):
    total_itens: int
    total_categorias: int
    itens_estoque_baixo: list[ItemEstoqueBaixo]
    itens_zerados: int
    movimentacoes_recentes: list[MovimentacaoResponse]
    valor_total_estoque: float
    itens_por_categoria: list[dict]


class RelatorioParams(BaseModel):
    tipo: str = "completo"
    formato: str = "pdf"
    categoria_id: Optional[int] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    status: Optional[str] = None


class PatrimonioBase(BaseModel):
    numero_patrimonio: str
    item_id: int
    numero_serie: Optional[str] = None
    data_aquisicao: Optional[date] = None
    valor_aquisicao: Optional[float] = None
    nota_fiscal: Optional[str] = None
    estado_conservacao: Optional[str] = None
    localizacao_atual: Optional[str] = None
    observacoes: Optional[str] = None

class PatrimonioCreate(PatrimonioBase):
    pass

class PatrimonioResponse(PatrimonioBase):
    id: int
    created_at: datetime
    item_nome: Optional[str] = None

    class Config:
        from_attributes = True


class SyncLogResponse(BaseModel):
    id: int
    tipo: str
    origem: str
    status: str
    total_extraidos: int
    total_importados: int
    erros: int
    detalhes: Optional[dict]
    iniciado_em: datetime
    concluido_em: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ConsumoResponse(BaseModel):
    id: int
    unidade: Optional[str] = None
    nome_unidade: Optional[str] = None
    centro_despacho: Optional[str] = None
    codigo_bem: Optional[str] = None
    descricao: Optional[str] = None
    quantidade: float = 0
    unidade_composicao: Optional[str] = None
    valor_total: float = 0
    created_at: datetime

    class Config:
        from_attributes = True


class ConsumoResumoCentro(BaseModel):
    centro_despacho: str
    total_itens: int
    total_quantidade: float
    total_valor: float


class ConsumoResumoItem(BaseModel):
    codigo_bem: str
    descricao: Optional[str] = None
    total_quantidade: float
    total_valor: float
    unidade_composicao: Optional[str] = None


class SyncConfigSchema(BaseModel):
    intervalo_horas: int = 48
    tipos_relatorio: list[str] = ["inventario", "movimentacoes"]
    ativo: bool = True
    horario_execucao: str = "06:00"
    apenas_dias_uteis: bool = False
