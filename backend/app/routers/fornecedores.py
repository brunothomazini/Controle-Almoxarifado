from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Fornecedor
from app.schemas.schemas import FornecedorCreate, FornecedorResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/fornecedores", tags=["Fornecedores"])


@router.get("", response_model=list[FornecedorResponse])
def listar(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1), db: Session = Depends(get_db),
           _=Depends(get_current_user)):
    return db.query(Fornecedor).offset(skip).limit(limit).all()


@router.post("", response_model=FornecedorResponse, status_code=201)
def criar(data: FornecedorCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    fornecedor = Fornecedor(**data.model_dump())
    db.add(fornecedor)
    db.commit()
    db.refresh(fornecedor)
    return fornecedor


@router.put("/{fornecedor_id}", response_model=FornecedorResponse)
def atualizar(fornecedor_id: int, data: FornecedorCreate, db: Session = Depends(get_db),
              _=Depends(get_current_user)):
    f = db.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Fornecedor nao encontrado")
    for key, value in data.model_dump().items():
        setattr(f, key, value)
    db.commit()
    db.refresh(f)
    return f


@router.delete("/{fornecedor_id}", status_code=204)
def deletar(fornecedor_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    f = db.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Fornecedor nao encontrado")
    db.delete(f)
    db.commit()
