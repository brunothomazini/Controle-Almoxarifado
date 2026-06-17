import pandas as pd
from sqlalchemy.orm import Session
from app.models.models import Item, Categoria, Movimentacao, StatusItem
from app.config import settings


def analisar_estoque(db: Session) -> dict:
    itens = db.query(Item).all()
    if not itens:
        return {"message": "Nenhum item cadastrado"}

    df = pd.DataFrame([
        {
            "id": i.id, "codigo": i.codigo, "nome": i.nome,
            "categoria": i.categoria.nome if i.categoria else "Sem categoria",
            "quantidade_atual": i.quantidade_atual,
            "quantidade_minima": i.quantidade_minima,
            "quantidade_maxima": i.quantidade_maxima,
            "valor_unitario": i.valor_unitario,
            "status": i.status.value,
        }
        for i in itens
    ])

    estoque_baixo = df[
        (df["quantidade_minima"] > 0) & (df["quantidade_atual"] <= df["quantidade_minima"])
    ]
    estoque_excesso = df[
        (df["quantidade_maxima"] > 0) & (df["quantidade_atual"] >= df["quantidade_maxima"])
    ]
    itens_zerados = df[df["quantidade_atual"] == 0]

    return {
        "total_itens": len(df),
        "valor_total_estoque": float((df["quantidade_atual"] * df["valor_unitario"]).sum()),
        "media_quantidade": float(df["quantidade_atual"].mean()),
        "estoque_baixo": {
            "quantidade": len(estoque_baixo),
            "itens": estoque_baixo[["codigo", "nome", "quantidade_atual", "quantidade_minima"]].to_dict(orient="records"),
        },
        "estoque_excesso": {
            "quantidade": len(estoque_excesso),
            "itens": estoque_excesso[["codigo", "nome", "quantidade_atual", "quantidade_maxima"]].to_dict(orient="records"),
        },
        "itens_zerados": {
            "quantidade": len(itens_zerados),
            "itens": itens_zerados[["codigo", "nome"]].to_dict(orient="records"),
        },
        "distribuicao_categorias": (
            df.groupby("categoria").agg(quantidade=("quantidade_atual", "sum"), itens=("id", "count"))
            .reset_index().to_dict(orient="records")
        ),
        "distribuicao_status": (
            df.groupby("status").agg(quantidade=("id", "count"))
            .reset_index().to_dict(orient="records")
        ),
    }


def analisar_movimentacoes(db: Session) -> dict:
    movs = db.query(Movimentacao).order_by(Movimentacao.data_movimentacao).all()
    if not movs:
        return {"message": "Nenhuma movimentacao registrada"}

    df = pd.DataFrame([
        {
            "id": m.id, "tipo": m.tipo.value,
            "quantidade": m.quantidade,
            "data": m.data_movimentacao,
            "item_nome": m.item.nome if m.item else "N/A",
            "item_codigo": m.item.codigo if m.item else "N/A",
            "responsavel": m.responsavel or "N/A",
        }
        for m in movs
    ])

    entradas = df[df["tipo"] == "entrada"]["quantidade"].sum()
    saidas = df[df["tipo"] == "saida"]["quantidade"].sum()

    return {
        "total_movimentacoes": len(df),
        "total_entradas": float(entradas),
        "total_saidas": float(saidas),
        "saldo_liquido": float(entradas - saidas),
        "por_tipo": df.groupby("tipo").agg(total=("quantidade", "sum"), ocorrencias=("id", "count"))
        .reset_index().to_dict(orient="records"),
        "itens_mais_movimentados": (
            df.groupby(["item_codigo", "item_nome"]).agg(movimentacoes=("id", "count"))
            .sort_values("movimentacoes", ascending=False)
            .head(10).reset_index().to_dict(orient="records")
        ),
    }
