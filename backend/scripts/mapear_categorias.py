import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import SessionLocal
from app.models.models import Item, Categoria

db = SessionLocal()

# Get the 8 main Excel categories by ID
excel_cats = db.query(Categoria).filter(Categoria.nome.in_([
    "Odontológico", "Médico-Hospitalar", "Papelaria", "Limpeza",
    "Informática", "Descartáveis Higiene e Limpeza",
    "Descartáveis médico-hospitalar", "Gêneros alimentícios e copa"
])).all()

excel_ids = {c.id for c in excel_cats}
print("Excel categories:")
for c in excel_cats:
    print(f"  ID {c.id}: {c.nome}")

# Map: old category name (exact DB string) -> new Excel category name
CAT_MAP = {
    "INSUMOS DE USO ODONTOLOGICO COM NOTIFIC.": "Odontológico",
    "INSUMOS DE USO ODONTOLOGICO SEM NOTIFIC.": "Odontológico",
    "MATERIAL DE CONSUMO ODONTOLÓGICO": "Odontológico",
    "MATERIAL DE CONSUMO ODONTOL�GICO": "Odontológico",
    "EXPEDIENTE": "Papelaria",
    "ARTIGOS PARA ESCRITORIOS": "Papelaria",
    "ARTIGOS DE PAPEL PARA HIGIENE PESSOAL": "Descartáveis Higiene e Limpeza",
    "MATERIAIS E SUPRIMENTOS DE USO DIDATICO.": "Papelaria",
    "MATERIAIS DE USO TECNICO HOSPITALAR COM.": "Médico-Hospitalar",
    "MATERIAL DE USO TECNICO HOSPITALAR SEM.": "Médico-Hospitalar",
    "CSV": "Médico-Hospitalar",
    "SUPRIMENTOS DE INFORMATICA": "Informática",
    "UTENSILIOS PARA HIGIENE E PROTECAO PESS.": "Descartáveis Higiene e Limpeza",
}

# Build cache of target category objects
target_cache = {}
for nome in set(CAT_MAP.values()):
    cat = db.query(Categoria).filter(Categoria.nome == nome).first()
    if not cat:
        cat = Categoria(nome=nome)
        db.add(cat)
        db.flush()
    target_cache[nome] = cat

total = 0
for old_nome, new_nome in CAT_MAP.items():
    old_cats = db.query(Categoria).filter(Categoria.nome == old_nome).all()
    for old_cat in old_cats:
        itens = db.query(Item).filter(Item.categoria_id == old_cat.id).all()
        for item in itens:
            if item.categoria_id != target_cache[new_nome].id:
                item.categoria_id = target_cache[new_nome].id
                total += 1
        print(f"  {old_nome} ({len(itens)} itens) -> {new_nome}")

db.commit()
print(f"\nAtualizados: {total} itens")

# Final distribution
from sqlalchemy import func
restantes = db.query(Categoria.nome, func.count(Item.id)).join(Item).group_by(Categoria.id).all()
print("\n=== Distribuição final ===")
for nome, qtd in sorted(restantes, key=lambda x: -x[1]):
    in_excel = " [Excel]" if nome in excel_cats else ""
    print(f"  {nome}: {qtd}{in_excel}")

db.close()
