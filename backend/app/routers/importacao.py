from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime
from app.database import get_db
from app.schemas.schemas import ImportacaoResponse
from app.services.import_service import importar_planilha, concatenar_planilhas
from app.services.auth_service import require_admin
from app.models.models import Importacao
from app.config import settings

router = APIRouter(prefix="/importacao", tags=["Importacao"])


@router.post("/upload", response_model=dict)
def upload_arquivo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename).suffix if file.filename else ".xlsx"
    caminho = settings.UPLOAD_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"

    content = file.file.read()
    with open(caminho, "wb") as f:
        f.write(content)

    resultado = importar_planilha(db, caminho)
    return resultado


@router.post("/concatenar", response_model=dict)
def concatenar(
    arquivos: list[str] = Form(...),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    caminhos = [Path(p) for p in arquivos]
    resultado = concatenar_planilhas(db, caminhos)
    return resultado


@router.get("/historico", response_model=list[ImportacaoResponse])
def historico(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(Importacao).order_by(Importacao.created_at.desc()).limit(50).all()
