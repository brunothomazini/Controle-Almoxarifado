import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import SessionLocal
from app.models.models import Categoria, Item
from sqlalchemy import func

db = SessionLocal()

# Delete categories with no items
subq = db.query(Item.categoria_id).distinct().subquery()
vazias = db.query(Categoria).filter(~Categoria.id.in_(subq)).all()

print(f"Categorias vazias a remover: {len(vazias)}")
for c in vazias:
    print(f"  Removendo: {c.nome} (id={c.id})")
    db.delete(c)

db.commit()

# Final check
restantes = db.query(Categoria).order_by(Categoria.nome).all()
print(f"\nCategorias restantes: {len(restantes)}")
for c in restantes:
    qtd = db.query(func.count(Item.id)).filter(Item.categoria_id == c.id).scalar()
    print(f"  {c.nome}: {qtd} itens")

db.close()
