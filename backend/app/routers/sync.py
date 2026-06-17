from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.auth_service import get_current_user
from app.services.sync_service import SyncOrchestrator
from app.services.scheduler_service import sync_scheduler
from app.schemas.schemas import SyncConfigSchema
from app.models.models import Usuario as User

router = APIRouter(prefix="/sync", tags=["Sincronizacao"])


def get_orquestrador(db: Session = Depends(get_db)):
    return SyncOrchestrator(db)


@router.post("/executar")
def executar_sincronizacao(
    orquestrador: SyncOrchestrator = Depends(get_orquestrador),
    usuario: User = Depends(get_current_user),
):
    resultado = orquestrador.executar_sincronizacao()
    return resultado


@router.get("/historico")
def listar_historico(
    limite: int = Query(20, ge=1, le=100),
    orquestrador: SyncOrchestrator = Depends(get_orquestrador),
    usuario: User = Depends(get_current_user),
):
    return orquestrador.listar_historico(limite)


@router.get("/status")
def status_sincronizacao(
    orquestrador: SyncOrchestrator = Depends(get_orquestrador),
    usuario: User = Depends(get_current_user),
):
    scheduler_status = sync_scheduler.get_status()
    ultimo_sync = orquestrador.obter_ultimo_sync()
    return {**scheduler_status, **ultimo_sync}


@router.post("/config")
def salvar_config(
    config: SyncConfigSchema,
    orquestrador: SyncOrchestrator = Depends(get_orquestrador),
    usuario: User = Depends(get_current_user),
):
    import json

    orquestrador.salvar_config("intervalo_horas", str(config.intervalo_horas))
    orquestrador.salvar_config("tipos_relatorio", json.dumps(config.tipos_relatorio))
    orquestrador.salvar_config("ativo", str(config.ativo).lower())
    orquestrador.salvar_config("horario_execucao", config.horario_execucao)

    sync_scheduler.stop()
    sync_scheduler.start(
        intervalo_horas=config.intervalo_horas,
        horario=config.horario_execucao,
    )

    return {"mensagem": "Configuracao salva com sucesso", "config": config.model_dump()}


@router.get("/config")
def obter_config(
    orquestrador: SyncOrchestrator = Depends(get_orquestrador),
    usuario: User = Depends(get_current_user),
):
    import json

    intervalo = int(orquestrador.config.get("intervalo_horas", "48"))
    horario = orquestrador.config.get("horario_execucao", "06:00")
    ativo = orquestrador.config.get("ativo", "true") == "true"
    tipos_raw = orquestrador.config.get("tipos_relatorio", '["inventario"]')

    try:
        tipos = json.loads(tipos_raw)
    except (json.JSONDecodeError, TypeError):
        tipos = ["inventario"]

    return {
        "intervalo_horas": intervalo,
        "horario_execucao": horario,
        "ativo": ativo,
        "tipos_relatorio": tipos,
        "uspdigital_credentials_configured": bool(
            orquestrador.config.get("uspdigital_user", "")
            and orquestrador.config.get("uspdigital_pass", "")
        ),
    }


@router.post("/credenciais")
def salvar_credenciais_uspdigital(
    usuario_usp: str = Query(..., description="Usuario USP Digital"),
    senha_usp: str = Query(..., description="Senha USP Digital"),
    orquestrador: SyncOrchestrator = Depends(get_orquestrador),
    usuario: User = Depends(get_current_user),
):
    orquestrador.salvar_config("uspdigital_user", usuario_usp)
    orquestrador.salvar_config("uspdigital_pass", senha_usp)
    return {"mensagem": "Credenciais USP Digital salvas com sucesso"}


@router.post("/testar-conexao")
def testar_conexao_uspdigital(
    orquestrador: SyncOrchestrator = Depends(get_orquestrador),
    usuario: User = Depends(get_current_user),
):
    username = orquestrador.config.get("uspdigital_user", "")
    password = orquestrador.config.get("uspdigital_pass", "")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Credenciais nao configuradas")

    from app.services.uspdigital_service import USPDigitalSyncService
    servico = USPDigitalSyncService(None)
    autenticou = servico.autenticar(username, password)
    servico.close()

    if autenticou:
        return {"status": "ok", "mensagem": "Conexao via API OK"}

    from app.integrations.uspdigital import USPDigitalClient
    cliente = USPDigitalClient()
    resultado = cliente.login(username, password)
    cliente.close()

    return {
        "status": "api_falhou" if not resultado else "ok",
        "detalhe": "API HTTP nao autenticou, mas o navegador pode funcionar na proxima sync automatica",
    }


@router.post("/scheduler/iniciar")
def iniciar_scheduler(
    usuario: User = Depends(get_current_user),
):
    sync_scheduler.start()
    return {"mensagem": "Scheduler iniciado"}


@router.post("/scheduler/parar")
def parar_scheduler(
    usuario: User = Depends(get_current_user),
):
    sync_scheduler.stop()
    return {"mensagem": "Scheduler parado"}


@router.post("/scheduler/pausar")
def pausar_scheduler(
    usuario: User = Depends(get_current_user),
):
    sync_scheduler.pausar()
    return {"mensagem": "Scheduler pausado"}


@router.post("/scheduler/retomar")
def retomar_scheduler(
    usuario: User = Depends(get_current_user),
):
    sync_scheduler.retomar()
    return {"mensagem": "Scheduler retomado"}
