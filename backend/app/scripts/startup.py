"""
Script de inicializacao do sistema.
Cria as pastas necessarias, inicializa o banco e insere dados de exemplo.

Uso:
    python -m app.scripts.startup
"""

from pathlib import Path
from app.database import init_db
from app.config import settings


def setup():
    print("Inicializando o Sistema de Controle de Almoxarifado...")

    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    init_db()
    print(f"Banco de dados criado em: {settings.DATA_DIR / 'almoxarifado.db'}")

    from app.scripts.seed_data import seed
    seed()

    print("\nPara iniciar o servidor:")
    print("  cd backend")
    print("  python run.py")
    print("\nServidor rodara em: http://localhost:8000")
    print("Documentacao da API: http://localhost:8000/docs")
    print("Consulta externa: abrir frontend/index.html no navegador")


if __name__ == "__main__":
    setup()
