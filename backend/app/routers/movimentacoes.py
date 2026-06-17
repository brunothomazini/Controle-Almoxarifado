from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.models import Movimentacao
from app.schemas.schemas import MovimentacaoResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/movimentacoes", tags=["Movimentacoes"])


@router.get("", response_model=list[MovimentacaoResponse])
def listar(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    movs = db.query(Movimentacao).order_by(Movimentacao.data_movimentacao.desc()).offset(skip).limit(limit).all()
    result = []
    for m in movs:
        r = MovimentacaoResponse.model_validate(m)
        r.item_nome = m.item.nome if m.item else None
        r.item_codigo = m.item.codigo if m.item else None
        result.append(r)
    return result
