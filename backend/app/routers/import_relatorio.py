from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth_service import get_current_user
from app.services.import_spreadsheet_service import SpreadsheetImportService
from app.models.models import Usuario

router = APIRouter(prefix="/importar-relatorio", tags=["Importar Relatorio"])


@router.post("/upload")
def upload_relatorio(
    arquivo: UploadFile = File(...),
    tipo: str = Form("inventario"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    if not arquivo.filename or not (arquivo.filename.endswith(".xlsx") or arquivo.filename.endswith(".csv")):
        return {"erro": "Formato invalido. Envie .xlsx ou .csv"}

    servico = SpreadsheetImportService(db)
    caminho = servico.salvar_arquivo(arquivo.file, arquivo.filename)
    resultado = servico.importar_relatorio(caminho, tipo)

    return {
        "mensagem": "Relatorio importado com sucesso" if resultado.get("status") == "sucesso" else "Erro na importacao",
        "arquivo": arquivo.filename,
        "detalhes": resultado,
        "instrucoes_upload": "Envie relatorios baixados do USP Digital (Sistema Administrativo)",
    }


@router.post("/upload-csv")
def upload_csv(
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    if not arquivo.filename or not arquivo.filename.endswith(".csv"):
        return {"erro": "Envie um arquivo .csv"}

    servico = SpreadsheetImportService(db)
    caminho = servico.salvar_arquivo(arquivo.file, arquivo.filename)
    resultado = servico.importar_relatorio(caminho, "inventario")

    return {
        "mensagem": "CSV importado com sucesso" if resultado.get("status") == "sucesso" else "Erro",
        "arquivo": arquivo.filename,
        "detalhes": resultado,
    }
