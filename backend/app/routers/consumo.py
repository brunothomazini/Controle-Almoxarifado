import csv
import io
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.models import Consumo
from app.schemas.schemas import ConsumoResponse, ConsumoResumoCentro, ConsumoResumoItem
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/consumo", tags=["Consumo"])


def parse_float_br(valor_str: str) -> float:
    if not valor_str:
        return 0.0
    return float(valor_str.strip().replace(".", "").replace(",", "."))


@router.post("/importar-csv")
def importar_csv_consumo(
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    if not arquivo.filename or not arquivo.filename.endswith(".csv"):
        return {"erro": "Envie um arquivo .csv"}

    content = arquivo.file.read().decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(content), delimiter=";")

    header = next(reader, None)
    if not header:
        return {"erro": "CSV vazio"}

    total_registros = 0
    importados = 0
    erros = 0

    for row in reader:
        total_registros += 1
        try:
            if len(row) < 8:
                erros += 1
                continue

            consumo = Consumo(
                unidade=row[0].strip().strip('"'),
                nome_unidade=row[1].strip().strip('"'),
                centro_despacho=row[2].strip().strip('"'),
                codigo_bem=row[3].strip().strip('"'),
                descricao=row[4].strip().strip('"'),
                quantidade=parse_float_br(row[5]),
                unidade_composicao=row[6].strip().strip('"'),
                valor_total=parse_float_br(row[7]),
            )
            db.add(consumo)
            importados += 1
        except Exception:
            erros += 1

    db.commit()

    return {
        "mensagem": f"Importacao concluida: {importados} registros importados",
        "detalhes": {
            "total_registros": total_registros,
            "importados": importados,
            "erros": erros,
        },
    }


@router.get("", response_model=list[ConsumoResponse])
def listar_consumos(
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    centro: str = Query(None),
    busca: str = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(Consumo)
    if centro:
        q = q.filter(Consumo.centro_despacho == centro)
    if busca:
        q = q.filter(
            Consumo.codigo_bem.contains(busca)
            | Consumo.descricao.contains(busca)
            | Consumo.nome_unidade.contains(busca)
        )
    return q.order_by(Consumo.id.desc()).offset(skip).limit(limit).all()


@router.get("/resumo-por-centro", response_model=list[ConsumoResumoCentro])
def resumo_por_centro(
    centro: str = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(
        Consumo.centro_despacho,
        func.count(Consumo.id).label("total_itens"),
        func.sum(Consumo.quantidade).label("total_quantidade"),
        func.sum(Consumo.valor_total).label("total_valor"),
    )
    if centro:
        q = q.filter(Consumo.centro_despacho == centro)
    rows = (
        q.group_by(Consumo.centro_despacho)
        .order_by(func.sum(Consumo.valor_total).desc())
        .all()
    )
    return [
        ConsumoResumoCentro(
            centro_despacho=r.centro_despacho,
            total_itens=r.total_itens,
            total_quantidade=float(r.total_quantidade or 0),
            total_valor=float(r.total_valor or 0),
        )
        for r in rows
    ]


@router.get("/resumo-por-item", response_model=list[ConsumoResumoItem])
def resumo_por_item(
    centro: str = Query(None),
    busca: str = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(
        Consumo.codigo_bem,
        func.max(Consumo.descricao).label("descricao"),
        func.max(Consumo.unidade_composicao).label("unidade_composicao"),
        func.sum(Consumo.quantidade).label("total_quantidade"),
        func.sum(Consumo.valor_total).label("total_valor"),
    )
    if centro:
        q = q.filter(Consumo.centro_despacho == centro)
    if busca:
        q = q.filter(
            Consumo.codigo_bem.contains(busca) | Consumo.descricao.contains(busca)
        )
    rows = (
        q.group_by(Consumo.codigo_bem)
        .order_by(func.sum(Consumo.valor_total).desc())
        .all()
    )
    return [
        ConsumoResumoItem(
            codigo_bem=r.codigo_bem,
            descricao=r.descricao,
            total_quantidade=float(r.total_quantidade or 0),
            total_valor=float(r.total_valor or 0),
            unidade_composicao=r.unidade_composicao,
        )
        for r in rows
    ]


@router.delete("/limpar")
def limpar_consumos(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    count = db.query(Consumo).delete()
    db.commit()
    return {"mensagem": f"{count} registros de consumo removidos"}


@router.get("/centros")
def listar_centros(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    rows = (
        db.query(Consumo.centro_despacho)
        .distinct()
        .order_by(Consumo.centro_despacho)
        .all()
    )
    return [r.centro_despacho for r in rows]


@router.get("/item-por-centro")
def item_por_centro(
    codigo_bem: str = Query(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    rows = (
        db.query(
            Consumo.centro_despacho,
            func.sum(Consumo.quantidade).label("total_quantidade"),
            func.sum(Consumo.valor_total).label("total_valor"),
        )
        .filter(Consumo.codigo_bem == codigo_bem)
        .group_by(Consumo.centro_despacho)
        .order_by(func.sum(Consumo.valor_total).desc())
        .all()
    )
    return [
        {
            "centro_despacho": r.centro_despacho,
            "total_quantidade": float(r.total_quantidade or 0),
            "total_valor": float(r.total_valor or 0),
        }
        for r in rows
    ]
