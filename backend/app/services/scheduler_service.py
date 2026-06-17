import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class SyncScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.job_id = "sync_uspdigital"
        self._running = False

    def start(self, intervalo_horas: int = 48, horario: str = "06:00"):
        if self._running:
            return

        trigger = IntervalTrigger(hours=intervalo_horas, start_date=datetime.now().replace(
            hour=int(horario.split(":")[0]),
            minute=int(horario.split(":")[1]),
            second=0
        ))

        self.scheduler.add_job(
            self._executar_sync,
            trigger,
            id=self.job_id,
            name="Sincronizacao USP Digital",
            replace_existing=True,
        )
        self.scheduler.start()
        self._running = True
        logger.info(f"Scheduler iniciado: intervalo de {intervalo_horas}h, horario {horario}")

    def stop(self):
        if self._running:
            self.scheduler.remove_job(self.job_id)
            self.scheduler.shutdown(wait=False)
            self._running = False
            logger.info("Scheduler parado")

    def pausar(self):
        if self._running:
            self.scheduler.pause_job(self.job_id)
            logger.info("Scheduler pausado")

    def retomar(self):
        if self._running:
            self.scheduler.resume_job(self.job_id)
            logger.info("Scheduler retomado")

    def _executar_sync(self):
        db = SessionLocal()
        try:
            from app.services.sync_service import SyncOrchestrator
            orquestrador = SyncOrchestrator(db)
            resultado = orquestrador.executar_sincronizacao()
            logger.info(f"Sync automatico concluido: {resultado}")
            return resultado
        except Exception as e:
            logger.error(f"Sync automatico falhou: {e}")
            return {"status": "erro", "mensagem": str(e)}
        finally:
            db.close()

    def get_status(self) -> dict:
        from apscheduler.schedulers.base import STATE_RUNNING, STATE_PAUSED

        job = self.scheduler.get_job(self.job_id)

        estado = "parado"
        if self.scheduler.state == STATE_RUNNING:
            estado = "rodando"
        elif self.scheduler.state == STATE_PAUSED:
            estado = "pausado"

        intervalo = None
        if job and hasattr(job.trigger, 'interval_length'):
            intervalo = job.trigger.interval_length // 3600

        return {
            "ativo": self._running,
            "estado": estado,
            "proxima_execucao": job.next_run_time.isoformat() if job and job.next_run_time else None,
            "ultima_execucao": None,
            "intervalo_horas": intervalo,
        }


sync_scheduler = SyncScheduler()
