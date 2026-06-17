from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Categoria
from app.schemas.schemas import CategoriaCreate, CategoriaResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/categorias", tags=["Categorias"])


@router.get("", response_model=list[CategoriaResponse])
def listar(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Categoria).order_by(Categoria.nome).all()


@router.post("", response_model=CategoriaResponse, status_code=201)
def criar(data: CategoriaCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    existing = db.query(Categoria).filter(Categoria.nome == data.nome).first()
    if existing:
        raise HTTPException(status_code=400, detail="Categoria ja existe")
    cat = Categoria(**data.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.put("/{categoria_id}", response_model=CategoriaResponse)
def atualizar(categoria_id: int, data: CategoriaCreate, db: Session = Depends(get_db),
              _=Depends(get_current_user)):
    cat = db.query(Categoria).filter(Categoria.id == categoria_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria nao encontrada")
    cat.nome = data.nome
    cat.descricao = data.descricao
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/{categoria_id}", status_code=204)
def deletar(categoria_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cat = db.query(Categoria).filter(Categoria.id == categoria_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria nao encontrada")
    db.delete(cat)
    db.commit()
