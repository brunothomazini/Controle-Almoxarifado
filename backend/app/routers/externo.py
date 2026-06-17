from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.database import get_db
from app.models.models import Item, Categoria

router = APIRouter(prefix="/externo", tags=["Consulta Externa"])


@router.get("/consulta", response_model=dict)
def consulta_publica(
    codigo: Optional[str] = Query(None, description="Codigo do item"),
    nome: Optional[str] = Query(None, description="Nome do item (busca parcial)"),
    categoria: Optional[str] = Query(None, description="Nome da categoria"),
    pagina: int = Query(1, ge=1, description="Numero da pagina"),
    por_pagina: int = Query(50, ge=1, le=200, description="Itens por pagina"),
    db: Session = Depends(get_db),
):
    query = db.query(Item).join(Categoria, isouter=True)

    if codigo:
        query = query.filter(Item.codigo == codigo)

    if nome:
        query = query.filter(Item.nome.ilike(f"%{nome}%"))

    if categoria:
        query = query.filter(Categoria.nome == categoria)

    total = query.count()
    total_paginas = max(1, (total + por_pagina - 1) // por_pagina)
    if pagina > total_paginas:
        pagina = total_paginas

    offset = (pagina - 1) * por_pagina
    itens = query.order_by(Item.nome).offset(offset).limit(por_pagina).all()

    return {
        "total": total,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total_paginas": total_paginas,
        "itens": [
            {
                "codigo": i.codigo,
                "nome": i.nome,
                "nome_comercial": i.nome_comercial,
                "fabricante": i.fabricante,
                "categoria": i.categoria.nome if i.categoria else "N/A",
                "quantidade_disponivel": i.quantidade_atual,
                "unidade": i.unidade_medida,
                "solicitar_por_email": i.solicitar_por_email,
                "tipo_controle": i.tipo_controle.value if i.tipo_controle else "almoxarifado",
                "pedidos_info": (
                    "solicitar para o setor de Informática"
                    if i.categoria and i.categoria.nome == "Informática"
                    else "Almox"
                    if i.tipo_controle and i.tipo_controle.value == "almoxarifado"
                    else "e-mail padronizados@fob.usp.br"
                    if i.solicitar_por_email
                    else "Almox"
                ),
                "status": i.status.value,
            }
            for i in itens
        ],
        "consulta_publica": True,
        "aviso": "Dados limitados para consulta externa",
    }


@router.get("/categorias")
def listar_categorias_publicas(db: Session = Depends(get_db)):
    cats = db.query(Categoria.nome).order_by(Categoria.nome).all()
    return {"categorias": [c.nome for c in cats if c.nome]}
