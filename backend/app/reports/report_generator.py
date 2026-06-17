from datetime import datetime
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from app.models.models import Item, Categoria, Movimentacao, StatusItem
from app.config import settings
import pandas as pd


def _coletar_dados_completos(db: Session, categoria_id: Optional[int] = None,
                              status: Optional[str] = None) -> pd.DataFrame:
    query = db.query(Item).join(Categoria, isouter=True)
    if categoria_id:
        query = query.filter(Item.categoria_id == categoria_id)
    if status:
        query = query.filter(Item.status == status)
    itens = query.all()

    return pd.DataFrame([
        {
            "Codigo": i.codigo, "Nome": i.nome,
            "Categoria": i.categoria.nome if i.categoria else "N/A",
            "Qtd Atual": i.quantidade_atual, "Qtd Minima": i.quantidade_minima,
            "Qtd Maxima": i.quantidade_maxima, "Unidade": i.unidade_medida,
            "Localizacao": i.localizacao or "N/A", "Status": i.status.value,
            "Valor Unit.": i.valor_unitario, "Valor Total": i.quantidade_atual * i.valor_unitario,
        }
        for i in itens
    ])


def gerar_relatorio_excel(db: Session, tipo: str = "completo",
                           categoria_id: Optional[int] = None,
                           status: Optional[str] = None) -> Path:
    settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho = settings.REPORTS_DIR / f"relatorio_estoque_{timestamp}.xlsx"

    df = _coletar_dados_completos(db, categoria_id, status)

    with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
        if tipo in ("completo", "estoque"):
            df.to_excel(writer, sheet_name="Inventario", index=False)

        if tipo in ("completo", "analise"):
            resumo = df.describe()
            resumo.to_excel(writer, sheet_name="Resumo")

            if "Valor Total" in df.columns:
                valor_total = df["Valor Total"].sum()
                total_itens = len(df)
                pd.DataFrame({
                    "Metrica": ["Total de Itens", "Valor Total do Estoque", "Data Geracao"],
                    "Valor": [total_itens, f"R$ {valor_total:.2f}", datetime.now().strftime("%d/%m/%Y %H:%M")],
                }).to_excel(writer, sheet_name="Indicadores", index=False)

        if tipo in ("completo", "categorias"):
            cats = (
                db.query(Categoria.nome)
                .join(Item, isouter=True)
                .group_by(Categoria.id)
                .all()
            )
            cat_data = []
            for (nome,) in cats:
                qtd = db.query(Item).filter(Item.categoria_id == Categoria.id).count() if nome else 0
                cat_data.append({"Categoria": nome or "Sem categoria", "Total Itens": qtd})
            pd.DataFrame(cat_data).to_excel(writer, sheet_name="Categorias", index=False)

        if tipo in ("completo", "movimentacoes"):
            movs = db.query(Movimentacao).order_by(Movimentacao.data_movimentacao.desc()).limit(100).all()
            mov_data = [
                {
                    "Data": m.data_movimentacao.strftime("%d/%m/%Y %H:%M"),
                    "Item": m.item.nome if m.item else "N/A",
                    "Tipo": m.tipo.value, "Quantidade": m.quantidade,
                    "Responsavel": m.responsavel or "N/A",
                    "Destino": m.destino or "N/A",
                }
                for m in movs
            ]
            pd.DataFrame(mov_data).to_excel(writer, sheet_name="Movimentacoes", index=False)

    return caminho


def gerar_relatorio_baixo_estoque(db: Session) -> Path:
    settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho = settings.REPORTS_DIR / f"estoque_baixo_{timestamp}.xlsx"

    itens = (
        db.query(Item)
        .filter(Item.quantidade_atual <= Item.quantidade_minima, Item.quantidade_minima > 0)
        .all()
    )
    df = pd.DataFrame([
        {
            "Codigo": i.codigo, "Nome": i.nome,
            "Qtd Atual": i.quantidade_atual, "Qtd Minima": i.quantidade_minima,
            "Diferenca": i.quantidade_atual - i.quantidade_minima,
            "Localizacao": i.localizacao or "N/A",
        }
        for i in itens
    ])
    df.to_excel(caminho, index=False, engine="openpyxl")
    return caminho


def gerar_relatorio_patrimonio(db: Session) -> Path:
    from app.models.models import Patrimonio

    settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho = settings.REPORTS_DIR / f"patrimonio_{timestamp}.xlsx"

    pats = db.query(Patrimonio).all()
    df = pd.DataFrame([
        {
            "Num. Patrimonio": p.numero_patrimonio,
            "Item": p.item.nome if p.item else "N/A",
            "Num. Serie": p.numero_serie or "N/A",
            "Data Aquisicao": p.data_aquisicao.strftime("%d/%m/%Y") if p.data_aquisicao else "N/A",
            "Valor": p.valor_aquisicao,
            "NF": p.nota_fiscal or "N/A",
            "Conservacao": p.estado_conservacao or "N/A",
            "Localizacao": p.localizacao_atual or "N/A",
        }
        for p in pats
    ])
    df.to_excel(caminho, index=False, engine="openpyxl")
    return caminho
