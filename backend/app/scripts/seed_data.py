"""
Script para popular o banco com dados de exemplo.

Uso:
    python -m app.scripts.seed_data
"""

from app.database import SessionLocal, init_db
from app.models.models import Categoria, Item, Fornecedor, StatusItem
from app.services.auth_service import gerar_hash_senha
from app.models.models import Usuario


def seed():
    init_db()
    db = SessionLocal()

    if db.query(Categoria).count() > 0:
        print("Banco ja possui dados. Pulando seed.")
        db.close()
        return

    cats = [
        Categoria(nome="Informatica", descricao="Equipamentos de informatica e acessorios"),
        Categoria(nome="Material de Escritorio", descricao="Papelaria e materiais administrativos"),
        Categoria(nome="Laboratorio", descricao="Materiais e equipamentos de laboratorio"),
        Categoria(nome="Higiene e Limpeza", descricao="Produtos de higiene e limpeza"),
        Categoria(nome="Ferramentas", descricao="Ferramentas e utensilios diversos"),
    ]
    db.add_all(cats)
    db.flush()

    itens = [
        Item(codigo="INF001", nome="Mouse Optico USB", categoria_id=cats[0].id,
             quantidade_atual=45, quantidade_minima=10, quantidade_maxima=100,
             unidade_medida="un", localizacao="Prateleira A1", valor_unitario=35.00),
        Item(codigo="INF002", nome="Teclado USB ABNT2", categoria_id=cats[0].id,
             quantidade_atual=30, quantidade_minima=10, quantidade_maxima=80,
             unidade_medida="un", localizacao="Prateleira A2", valor_unitario=89.00),
        Item(codigo="INF003", nome="Monitor 21.5 LED Full HD", categoria_id=cats[0].id,
             quantidade_atual=5, quantidade_minima=3, quantidade_maxima=20,
             unidade_medida="un", localizacao="Sala 101", valor_unitario=850.00),
        Item(codigo="INF004", nome="Cabo HDMI 3m", categoria_id=cats[0].id,
             quantidade_atual=2, quantidade_minima=10, quantidade_maxima=50,
             unidade_medida="un", localizacao="Prateleira A3", valor_unitario=25.00),
        Item(codigo="INF005", nome="Webcam HD 1080p", categoria_id=cats[0].id,
             quantidade_atual=0, quantidade_minima=5, quantidade_maxima=30,
             unidade_medida="un", localizacao="Prateleira A1", valor_unitario=150.00),
        Item(codigo="ESC001", nome="Papel Sulfite A4 75g (cx 500fl)", categoria_id=cats[1].id,
             quantidade_atual=120, quantidade_minima=50, quantidade_maxima=300,
             unidade_medida="pacote", localizacao="Deposito 1", valor_unitario=22.00),
        Item(codigo="ESC002", nome="Caneta Esferografica Azul", categoria_id=cats[1].id,
             quantidade_atual=200, quantidade_minima=50, quantidade_maxima=500,
             unidade_medida="un", localizacao="Deposito 2", valor_unitario=1.50),
        Item(codigo="ESC003", nome="Grampeador Medio", categoria_id=cats[1].id,
             quantidade_atual=8, quantidade_minima=5, quantidade_maxima=30,
             unidade_medida="un", localizacao="Prateleira B1", valor_unitario=35.00),
        Item(codigo="ESC004", nome="Cartucho Toner HP 12A", categoria_id=cats[1].id,
             quantidade_atual=3, quantidade_minima=10, quantidade_maxima=40,
             unidade_medida="un", localizacao="Sala 102", valor_unitario=280.00),
        Item(codigo="LAB001", nome="Luvas de Latex descartaveis (cx)", categoria_id=cats[2].id,
             quantidade_atual=50, quantidade_minima=20, quantidade_maxima=200,
             unidade_medida="caixa", localizacao="Lab Quimica", valor_unitario=45.00),
        Item(codigo="LAB002", nome="Proveta 500ml Vidro", categoria_id=cats[2].id,
             quantidade_atual=12, quantidade_minima=5, quantidade_maxima=30,
             unidade_medida="un", localizacao="Lab Fisica", valor_unitario=120.00),
        Item(codigo="HL001", nome="Detergente Neutro 5L", categoria_id=cats[3].id,
             quantidade_atual=15, quantidade_minima=10, quantidade_maxima=50,
             unidade_medida="un", localizacao="Deposito 3", valor_unitario=18.00),
        Item(codigo="HL002", nome="Agua Sanitaria 2L", categoria_id=cats[3].id,
             quantidade_atual=4, quantidade_minima=10, quantidade_maxima=40,
             unidade_medida="un", localizacao="Deposito 3", valor_unitario=6.50),
        Item(codigo="FER001", nome="Chave de Fenda 6 pol", categoria_id=cats[4].id,
             quantidade_atual=20, quantidade_minima=5, quantidade_maxima=30,
             unidade_medida="un", localizacao="Oficina", valor_unitario=15.00),
        Item(codigo="FER002", nome="Martelo Unha 300g", categoria_id=cats[4].id,
             quantidade_atual=0, quantidade_minima=3, quantidade_maxima=15,
             unidade_medida="un", localizacao="Oficina", valor_unitario=32.00),
    ]
    db.add_all(itens)

    fornecedores = [
        Fornecedor(nome="Distribuidora de Informatica Ltda", cnpj="11.222.333/0001-44",
                   contato="Joao", email="joao@distinfo.com.br", telefone="(11) 99999-0001"),
        Fornecedor(nome="Papelaria Universal S/A", cnpj="22.333.444/0001-55",
                   contato="Maria", email="maria@universal.com.br", telefone="(11) 99999-0002"),
        Fornecedor(nome="Produtos para Laboratorio Ltda", cnpj="33.444.555/0001-66",
                   contato="Carlos", email="carlos@prolab.com.br", telefone="(11) 99999-0003"),
    ]
    db.add_all(fornecedores)

    if not db.query(Usuario).filter(Usuario.username == "externo").first():
        externo = Usuario(
            username="externo",
            email="externo@consulta.usp.br",
            nome_completo="Usuario Externo",
            senha_hash=gerar_hash_senha("externo123"),
            is_externo=True,
        )
        db.add(externo)

    db.commit()
    db.close()
    print("Dados de exemplo inseridos com sucesso!")
    print("Usuario admin: admin / admin123")
    print("Usuario externo: externo / externo123")


if __name__ == "__main__":
    seed()
