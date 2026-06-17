import logging
from datetime import datetime
from app.models.models import SyncLog, SyncConfig
from app.config import settings

logger = logging.getLogger(__name__)


class SyncOrchestrator:
    def __init__(self, db):
        self.db = db
        self.config = self._carregar_config()

    def _carregar_config(self) -> dict:
        padrao = {
            "intervalo_horas": "48",
            "tipos_relatorio": '["inventario"]',
            "ativo": "true",
            "horario_execucao": "06:00",
            "uspdigital_user": "",
            "uspdigital_pass": "",
        }
        resultado = {}
        for chave, valor_padrao in padrao.items():
            cfg = self.db.query(SyncConfig).filter(SyncConfig.chave == chave).first()
            if cfg:
                resultado[chave] = cfg.valor
            else:
                resultado[chave] = valor_padrao
        return resultado

    def salvar_config(self, chave: str, valor: str):
        cfg = self.db.query(SyncConfig).filter(SyncConfig.chave == chave).first()
        if cfg:
            cfg.valor = valor
        else:
            cfg = SyncConfig(chave=chave, valor=valor)
            self.db.add(cfg)
        self.db.commit()

    def _criar_log(self, tipo: str, status: str = "pendente") -> SyncLog:
        log = SyncLog(tipo=tipo, origem="uspdigital", status=status)
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def _finalizar_log(self, log: SyncLog, status: str, extraidos: int = 0, importados: int = 0, erros: int = 0, detalhes: dict = None):
        log.status = status
        log.total_extraidos = extraidos
        log.total_importados = importados
        log.erros = erros
        log.detalhes = detalhes
        log.concluido_em = datetime.now()
        self.db.commit()

    def executar_sincronizacao(self) -> dict:
        tipos = ["inventario"]
        config_tipos = self.config.get("tipos_relatorio", '["inventario"]')
        import json
        try:
            tipos = json.loads(config_tipos)
        except (json.JSONDecodeError, TypeError):
            tipos = ["inventario"]

        log = self._criar_log("sincronizacao", "em_andamento")

        username = self.config.get("uspdigital_user", "")
        password = self.config.get("uspdigital_pass", "")

        if not username or not password:
            self._finalizar_log(log, "erro", detalhes={"erro": "Credenciais USP Digital nao configuradas"})
            return {"status": "erro", "mensagem": "Credenciais nao configuradas"}

        from app.services.uspdigital_service import USPDigitalSyncService
        servico = USPDigitalSyncService(self.db)
        try:
            resultado = servico.extrair_e_importar(tipos, username, password)
            if "erro" in resultado:
                self._finalizar_log(log, "erro", detalhes=resultado)
                resp = {"status": "erro", "mensagem": resultado["erro"]}
                for campo in ["instrucao", "detalhe_api", "detalhe_browser", "metodo"]:
                    if campo in resultado:
                        resp[campo] = resultado[campo]
                return resp

            self._finalizar_log(
                log, "sucesso",
                extraidos=resultado.get("extraidos", 0),
                importados=resultado.get("importados", 0),
                erros=resultado.get("erros", 0),
                detalhes=resultado.get("detalhes"),
            )

            return {
                "status": "sucesso",
                "extraidos": resultado.get("extraidos", 0),
                "importados": resultado.get("importados", 0),
                "erros": resultado.get("erros", 0),
            }
        except Exception as e:
            self._finalizar_log(log, "erro", detalhes={"erro": str(e)})
            return {"status": "erro", "mensagem": str(e)}
        finally:
            servico.close()

    def listar_historico(self, limite: int = 20) -> list[dict]:
        logs = (
            self.db.query(SyncLog)
            .order_by(SyncLog.created_at.desc())
            .limit(limite)
            .all()
        )
        return [
            {
                "id": log.id,
                "tipo": log.tipo,
                "origem": log.origem,
                "status": log.status,
                "total_extraidos": log.total_extraidos,
                "total_importados": log.total_importados,
                "erros": log.erros,
                "detalhes": log.detalhes,
                "iniciado_em": log.iniciado_em.isoformat() if log.iniciado_em else None,
                "concluido_em": log.concluido_em.isoformat() if log.concluido_em else None,
            }
            for log in logs
        ]

    def obter_ultimo_sync(self) -> dict:
        log = (
            self.db.query(SyncLog)
            .filter(SyncLog.status == "sucesso")
            .order_by(SyncLog.created_at.desc())
            .first()
        )
        if not log:
            return {"ultimo_sync": None, "mensagem": "Nenhuma sincronizacao realizada"}
        return {
            "ultimo_sync": log.concluido_em.isoformat() if log.concluido_em else None,
            "status": log.status,
            "total_importados": log.total_importados,
        }
