from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.models import Item
from app.schemas.schemas import (
    ItemCreate, ItemUpdate, ItemResponse, MovimentacaoCreate, MovimentacaoResponse, DashboardData,
)
from app.services.item_service import (
    listar_itens, criar_item, atualizar_item, deletar_item,
    registrar_movimentacao, obter_dashboard,
)
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/itens", tags=["Itens"])


@router.get("", response_model=list[ItemResponse])
def listar(
    categoria_id: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    itens = listar_itens(db, categoria_id, status, search, skip, limit)
    result = []
    for i in itens:
        r = ItemResponse.model_validate(i)
        r.categoria_nome = i.categoria.nome if i.categoria else None
        r.fornecedor_nome = i.fornecedor.nome if i.fornecedor else None
        result.append(r)
    return result


@router.get("/{item_id}", response_model=ItemResponse)
def obter(item_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item nao encontrado")
    r = ItemResponse.model_validate(item)
    r.categoria_nome = item.categoria.nome if item.categoria else None
    r.fornecedor_nome = item.fornecedor.nome if item.fornecedor else None
    return r


@router.post("", response_model=ItemResponse, status_code=201)
def criar(data: ItemCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return criar_item(db, data)


@router.put("/{item_id}", response_model=ItemResponse)
def atualizar(item_id: int, data: ItemUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    item = atualizar_item(db, item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Item nao encontrado")
    return item


@router.delete("/{item_id}", status_code=204)
def deletar(item_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    if not deletar_item(db, item_id):
        raise HTTPException(status_code=404, detail="Item nao encontrado")


@router.get("/dashboard/resumo", response_model=DashboardData)
def dashboard(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return obter_dashboard(db)


@router.post("/{item_id}/movimentacao", response_model=MovimentacaoResponse)
def movimentar(
    item_id: int, data: MovimentacaoCreate,
    db: Session = Depends(get_db), _=Depends(get_current_user),
):
    data.item_id = item_id
    mov = registrar_movimentacao(db, data)
    if not mov:
        raise HTTPException(status_code=400, detail="Movimentacao invalida (estoque insuficiente ou item inexistente)")
    return mov
