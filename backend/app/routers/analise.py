from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analysis_service import analisar_estoque, analisar_movimentacoes
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/analise", tags=["Analise"])


@router.get("/estoque")
def analise_estoque(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return analisar_estoque(db)


@router.get("/movimentacoes")
def analise_movimentacoes(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return analisar_movimentacoes(db)
