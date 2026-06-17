from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path

from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    from app.services.auth_service import gerar_hash_senha
    from app.database import SessionLocal
    from app.models.models import Usuario, SyncConfig
    import json as _json
    db = SessionLocal()
    try:
        admin = db.query(Usuario).filter(Usuario.username == "admin").first()
        if not admin:
            admin = Usuario(
                username="admin",
                email="admin@almoxarifado.usp.br",
                nome_completo="Administrador",
                senha_hash=gerar_hash_senha("admin123"),
                is_admin=True,
            )
            db.add(admin)
            db.commit()
        cfg = db.query(SyncConfig).filter(SyncConfig.chave == "intervalo_horas").first()
        if not cfg:
            db.add_all([
                SyncConfig(chave="intervalo_horas", valor="48"),
                SyncConfig(chave="tipos_relatorio", valor=_json.dumps(["inventario"])),
                SyncConfig(chave="ativo", valor="true"),
                SyncConfig(chave="horario_execucao", valor="06:00"),
                SyncConfig(chave="apenas_dias_uteis", valor="false"),
            ])
            db.commit()
        from app.services.scheduler_service import sync_scheduler
        sync_scheduler.start(intervalo_horas=48, horario="06:00")
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    max_request_size=settings.MAX_UPLOAD_SIZE,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from app.routers import (
    auth, itens, movimentacoes, categorias,
    fornecedores, importacao, relatorios, analise, externo, patrimonio,
    sync, import_relatorio, consumo,
)

app.include_router(auth.router, prefix="/api")
app.include_router(itens.router, prefix="/api")
app.include_router(movimentacoes.router, prefix="/api")
app.include_router(categorias.router, prefix="/api")
app.include_router(fornecedores.router, prefix="/api")
app.include_router(importacao.router, prefix="/api")
app.include_router(relatorios.router, prefix="/api")
app.include_router(analise.router, prefix="/api")
app.include_router(externo.router, prefix="/api")
app.include_router(patrimonio.router, prefix="/api")
app.include_router(sync.router, prefix="/api")
app.include_router(import_relatorio.router, prefix="/api")
app.include_router(consumo.router, prefix="/api")


frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="frontend")

    @app.get("/")
    def serve_index():
        return FileResponse(frontend_path / "index.html")

    @app.get("/admin.html")
    def serve_admin():
        return FileResponse(frontend_path / "admin.html")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
