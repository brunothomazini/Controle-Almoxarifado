from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Patrimonio
from app.schemas.schemas import PatrimonioCreate, PatrimonioResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/patrimonio", tags=["Patrimonio"])


@router.get("", response_model=list[PatrimonioResponse])
def listar(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    pats = db.query(Patrimonio).offset(skip).limit(limit).all()
    result = []
    for p in pats:
        r = PatrimonioResponse.model_validate(p)
        r.item_nome = p.item.nome if p.item else None
        result.append(r)
    return result


@router.post("", response_model=PatrimonioResponse, status_code=201)
def criar(data: PatrimonioCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    pat = Patrimonio(**data.model_dump())
    db.add(pat)
    db.commit()
    db.refresh(pat)
    return pat


@router.get("/{patrimonio_id}", response_model=PatrimonioResponse)
def obter(patrimonio_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    pat = db.query(Patrimonio).filter(Patrimonio.id == patrimonio_id).first()
    if not pat:
        raise HTTPException(status_code=404, detail="Patrimonio nao encontrado")
    r = PatrimonioResponse.model_validate(pat)
    r.item_nome = pat.item.nome if pat.item else None
    return r
