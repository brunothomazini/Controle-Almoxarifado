from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, Date,
    ForeignKey, Enum, Boolean, JSON, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.utils.time_utils import get_now_sp_naive
import enum


class TipoMovimentacao(str, enum.Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"
    AJUSTE = "ajuste"
    TRANSFERENCIA = "transferencia"


class StatusItem(str, enum.Enum):
    DISPONIVEL = "disponivel"
    EMPRESTADO = "emprestado"
    MANUTENCAO = "manutencao"
    BAIXADO = "baixado"
    RESERVADO = "reservado"


class TipoControle(str, enum.Enum):
    ALMOXARIFADO = "almoxarifado"
    PADRONIZADO = "padronizado"
    OUTRO = "outro"


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False, unique=True)
    descricao = Column(Text)
    created_at = Column(DateTime, default=get_now_sp_naive)
    updated_at = Column(DateTime, default=get_now_sp_naive, onupdate=get_now_sp_naive)

    itens = relationship("Item", back_populates="categoria")


class Item(Base):
    __tablename__ = "itens"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(100), unique=True, nullable=False, index=True)
    codigo_usp = Column(String(100), index=True)
    nome = Column(String(300), nullable=False)
    descricao = Column(Text)
    unidade_medida = Column(String(50), default="un")
    quantidade_minima = Column(Float, default=0)
    quantidade_atual = Column(Float, default=0)
    quantidade_maxima = Column(Float, default=0)
    localizacao = Column(String(200))
    solicitar_por_email = Column(Boolean, default=False)
    status = Column(Enum(StatusItem), default=StatusItem.DISPONIVEL)
    tipo_controle = Column(Enum(TipoControle), default=TipoControle.ALMOXARIFADO)
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    fornecedor_id = Column(Integer, ForeignKey("fornecedores.id"))
    nome_comercial = Column(String(300))
    fabricante = Column(String(200))
    modelo = Column(String(200))
    numero_serie = Column(String(200))
    valor_unitario = Column(Float, default=0)
    observacoes = Column(Text)
    created_at = Column(DateTime, default=get_now_sp_naive)
    updated_at = Column(DateTime, default=get_now_sp_naive, onupdate=get_now_sp_naive)

    categoria = relationship("Categoria", back_populates="itens")
    fornecedor = relationship("Fornecedor")
    movimentacoes = relationship("Movimentacao", back_populates="item", order_by="Movimentacao.data_movimentacao.desc()")


class Movimentacao(Base):
    __tablename__ = "movimentacoes"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("itens.id"), nullable=False)
    tipo = Column(Enum(TipoMovimentacao), nullable=False)
    quantidade = Column(Float, nullable=False)
    data_movimentacao = Column(DateTime, default=get_now_sp_naive)
    responsavel = Column(String(200))
    destino = Column(String(300))
    documento_referencia = Column(String(200))
    observacoes = Column(Text)
    created_at = Column(DateTime, default=get_now_sp_naive)

    item = relationship("Item", back_populates="movimentacoes")


class Fornecedor(Base):
    __tablename__ = "fornecedores"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(300), nullable=False)
    cnpj = Column(String(20), unique=True, index=True)
    contato = Column(String(200))
    email = Column(String(200))
    telefone = Column(String(30))
    endereco = Column(Text)
    observacoes = Column(Text)
    created_at = Column(DateTime, default=get_now_sp_naive)
    updated_at = Column(DateTime, default=get_now_sp_naive, onupdate=get_now_sp_naive)


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(200), unique=True)
    nome_completo = Column(String(300))
    senha_hash = Column(String(300), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_externo = Column(Boolean, default=False)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=get_now_sp_naive)
    updated_at = Column(DateTime, default=get_now_sp_naive, onupdate=get_now_sp_naive)


class Importacao(Base):
    __tablename__ = "importacoes"

    id = Column(Integer, primary_key=True, index=True)
    nome_arquivo = Column(String(500))
    tipo_origem = Column(String(50))
    total_registros = Column(Integer, default=0)
    importados = Column(Integer, default=0)
    erros = Column(Integer, default=0)
    detalhes = Column(JSON)
    created_at = Column(DateTime, default=get_now_sp_naive)


class Patrimonio(Base):
    __tablename__ = "patrimonios"

    id = Column(Integer, primary_key=True, index=True)
    numero_patrimonio = Column(String(100), unique=True, index=True)
    item_id = Column(Integer, ForeignKey("itens.id"), nullable=False)
    numero_serie = Column(String(200))
    data_aquisicao = Column(Date)
    valor_aquisicao = Column(Float)
    nota_fiscal = Column(String(100))
    estado_conservacao = Column(String(50))
    localizacao_atual = Column(String(300))
    observacoes = Column(Text)
    created_at = Column(DateTime, default=get_now_sp_naive)
    updated_at = Column(DateTime, default=get_now_sp_naive, onupdate=get_now_sp_naive)

    item = relationship("Item")


class Consumo(Base):
    __tablename__ = "consumos"

    id = Column(Integer, primary_key=True, index=True)
    unidade = Column(String(10), index=True)
    nome_unidade = Column(String(300))
    centro_despacho = Column(String(50), index=True)
    codigo_bem = Column(String(50), index=True)
    descricao = Column(Text)
    quantidade = Column(Float, default=0)
    unidade_composicao = Column(String(100))
    valor_total = Column(Float, default=0)
    created_at = Column(DateTime, default=get_now_sp_naive)


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(50), nullable=False)
    origem = Column(String(100), default="uspdigital")
    status = Column(String(20), default="pendente")
    total_extraidos = Column(Integer, default=0)
    total_importados = Column(Integer, default=0)
    erros = Column(Integer, default=0)
    detalhes = Column(JSON)
    iniciado_em = Column(DateTime, default=get_now_sp_naive)
    concluido_em = Column(DateTime)
    created_at = Column(DateTime, default=get_now_sp_naive)


class SyncConfig(Base):
    __tablename__ = "sync_config"

    id = Column(Integer, primary_key=True, index=True)
    chave = Column(String(100), unique=True, nullable=False)
    valor = Column(String(500))
    atualizado_em = Column(DateTime, default=get_now_sp_naive, onupdate=get_now_sp_naive)
