from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.auth_service import get_current_user
from app.reports.report_generator import (
    gerar_relatorio_excel, gerar_relatorio_baixo_estoque,
    gerar_relatorio_patrimonio,
)
from app.schemas.schemas import RelatorioParams

router = APIRouter(prefix="/relatorios", tags=["Relatorios"])


@router.post("/gerar")
def gerar_relatorio(
    params: RelatorioParams,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    caminho = gerar_relatorio_excel(
        db,
        tipo=params.tipo,
        categoria_id=params.categoria_id,
        status=params.status,
    )
    return {"arquivo": str(caminho.name), "path": str(caminho)}


@router.get("/download/{nome_arquivo}")
def download_relatorio(nome_arquivo: str):
    from app.config import settings
    caminho = settings.REPORTS_DIR / nome_arquivo
    if not caminho.exists():
        raise HTTPException(status_code=404, detail="Arquivo nao encontrado")
    return FileResponse(
        caminho,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=nome_arquivo,
    )


@router.post("/estoque-baixo")
def relatorio_estoque_baixo(db: Session = Depends(get_db), _=Depends(get_current_user)):
    caminho = gerar_relatorio_baixo_estoque(db)
    return {"arquivo": str(caminho.name), "path": str(caminho)}


@router.post("/patrimonio")
def relatorio_patrimonio(db: Session = Depends(get_db), _=Depends(get_current_user)):
    caminho = gerar_relatorio_patrimonio(db)
    return {"arquivo": str(caminho.name), "path": str(caminho)}
