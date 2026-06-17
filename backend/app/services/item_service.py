from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.models import Item, Categoria, Movimentacao, StatusItem, TipoMovimentacao
from app.schemas.schemas import ItemCreate, ItemUpdate, ItemEstoqueBaixo, MovimentacaoCreate


def listar_itens(
    db: Session,
    categoria_id: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Item]:
    query = db.query(Item).join(Categoria, isouter=True)
    if categoria_id:
        query = query.filter(Item.categoria_id == categoria_id)
    if status:
        query = query.filter(Item.status == status)
    if search:
        term = f"%{search}%"
        query = query.filter(
            Item.nome.ilike(term) | Item.codigo.ilike(term) | Item.descricao.ilike(term)
        )
    return query.order_by(Item.nome).offset(skip).limit(limit).all()


def criar_item(db: Session, data: ItemCreate) -> Item:
    item = Item(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def atualizar_item(db: Session, item_id: int, data: ItemUpdate) -> Optional[Item]:
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def deletar_item(db: Session, item_id: int) -> bool:
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True


def registrar_movimentacao(db: Session, data: MovimentacaoCreate) -> Optional[Movimentacao]:
    item = db.query(Item).filter(Item.id == data.item_id).first()
    if not item:
        return None

    mov = Movimentacao(**data.model_dump())
    db.add(mov)

    if data.tipo == TipoMovimentacao.ENTRADA:
        item.quantidade_atual += data.quantidade
    elif data.tipo == TipoMovimentacao.SAIDA:
        if item.quantidade_atual < data.quantidade:
            return None
        item.quantidade_atual -= data.quantidade
    elif data.tipo == TipoMovimentacao.AJUSTE:
        item.quantidade_atual = data.quantidade

    db.commit()
    db.refresh(mov)
    return mov


def obter_dashboard(db: Session) -> dict:
    total_itens = db.query(func.count(Item.id)).scalar() or 0
    total_categorias = db.query(func.count(Categoria.id)).scalar() or 0
    itens_zerados = db.query(func.count(Item.id)).filter(Item.quantidade_atual == 0).scalar() or 0

    itens_baixo = (
        db.query(Item)
        .filter(Item.quantidade_atual <= Item.quantidade_minima, Item.quantidade_minima > 0)
        .all()
    )
    estoque_baixo = [
        ItemEstoqueBaixo(
            id=i.id, codigo=i.codigo, nome=i.nome,
            quantidade_atual=i.quantidade_atual,
            quantidade_minima=i.quantidade_minima,
            diferenca=i.quantidade_atual - i.quantidade_minima,
        )
        for i in itens_baixo
    ]

    movs = (
        db.query(Movimentacao)
        .order_by(Movimentacao.data_movimentacao.desc())
        .limit(10)
        .all()
    )

    valor_total = (
        db.query(func.coalesce(func.sum(Item.quantidade_atual * Item.valor_unitario), 0))
        .scalar()
    )

    cats = (
        db.query(Categoria.nome, func.count(Item.id).label("total"))
        .join(Item, isouter=True)
        .group_by(Categoria.id)
        .all()
    )

    return {
        "total_itens": total_itens,
        "total_categorias": total_categorias,
        "itens_estoque_baixo": estoque_baixo,
        "itens_zerados": itens_zerados,
        "movimentacoes_recentes": movs,
        "valor_total_estoque": float(valor_total),
        "itens_por_categoria": [{"nome": c.nome, "total": c.total} for c in cats],
    }
