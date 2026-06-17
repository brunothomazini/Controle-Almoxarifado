import csv
import io
from datetime import datetime
from typing import Optional
from app.integrations.uspdigital import USPDigitalClient
from app.config import settings


class USPDigitalSyncService:
    def __init__(self, db):
        self.db = db
        self.client = USPDigitalClient()

    def autenticar(self, username: str, password: str) -> bool:
        return self.client.login(username, password)

    def extrair_inventario(self, params: Optional[dict] = None) -> list[dict]:
        return self.client.extrair_materiais(params or {})

    def extrair_movimentacoes(self, data_inicio: str, data_fim: str) -> list[dict]:
        return self.client.extrair_materiais({
            "tipo": "movimentacao",
            "data_inicio": data_inicio,
            "data_fim": data_fim,
        })

    def extrair_e_importar(self, tipos: list[str], username: str, password: str) -> dict:
        resultado = {"extraidos": 0, "importados": 0, "erros": 0, "detalhes": []}

        autenticado = self.autenticar(username, password)
        if autenticado and self.client.autenticado():
            if "inventario" in tipos:
                dados = self.extrair_inventario()
                resultado["extraidos"] += len(dados)
                imp, err = self._importar_materiais(dados)
                resultado["importados"] += imp
                resultado["erros"] += err
                resultado["detalhes"].append({"tipo": "inventario", "extraidos": len(dados), "importados": imp, "erros": err})

            if "movimentacoes" in tipos:
                from datetime import timedelta
                hoje = datetime.now()
                inicio = (hoje - timedelta(days=2)).strftime("%Y-%m-%d")
                fim = hoje.strftime("%Y-%m-%d")
                dados = self.extrair_movimentacoes(inicio, fim)
                resultado["extraidos"] += len(dados)
                imp, err = self._importar_movimentacoes(dados)
                resultado["importados"] += imp
                resultado["erros"] += err
                resultado["detalhes"].append({"tipo": "movimentacoes", "extraidos": len(dados), "importados": imp, "erros": err})
        else:
            try:
                from app.services.uspdigital_browser_service import USPDigitalBrowserService
                browser_svc = USPDigitalBrowserService(self.db)
                resultado_browser = browser_svc.extrair_e_importar(username, password, tipos)
                if "erro" not in resultado_browser:
                    resultado = resultado_browser
                    resultado["metodo"] = "browser"
                else:
                    return {
                        "erro": "Falha na autenticacao via API e via navegador",
                        "detalhe_api": "API HTTP nao autenticou",
                        "detalhe_browser": resultado_browser.get("erro"),
                        "instrucao": (
                            "Faça login manual no USP Digital, baixe o relatorio e envie via "
                            "POST /api/importar-relatorio/upload"
                        ),
                    }
            except ImportError:
                return {
                    "erro": "Falha na autenticacao com USP Digital",
                    "instrucao": (
                        "Instale o Playwright para automacao via navegador: pip install playwright\n"
                        "Ou faca upload manual do relatorio via POST /api/importar-relatorio/upload"
                    ),
                }

        return resultado

    def _importar_materiais(self, dados: list[dict]) -> tuple[int, int]:
        from app.models.models import Item, Categoria

        importados = 0
        erros = 0

        for item_data in dados:
            try:
                codigo = str(item_data.get("codigo") or item_data.get("CODIGO") or "")
                if not codigo:
                    erros += 1
                    continue

                nome = item_data.get("nome") or item_data.get("NOME COMERCIAL") or item_data.get("DESCRICAO") or ""
                unidade = item_data.get("unidade") or item_data.get("UNIDADE") or "UN"
                categoria_nome = item_data.get("categoria") or item_data.get("CATEGORIA") or "Geral"

                cat = self.db.query(Categoria).filter(Categoria.nome == categoria_nome).first()
                if not cat:
                    cat = Categoria(nome=categoria_nome)
                    self.db.add(cat)
                    self.db.flush()

                existente = self.db.query(Item).filter(Item.codigo == codigo).first()
                if existente:
                    existente.nome = nome or existente.nome
                    existente.unidade_medida = unidade or existente.unidade_medida
                    existente.quantidade_atual = float(item_data.get("quantidade", existente.quantidade_atual))
                    existente.categoria_id = cat.id
                else:
                    item = Item(
                        codigo=codigo,
                        nome=nome,
                        descricao=item_data.get("descricao", ""),
                        unidade_medida=unidade,
                        quantidade_atual=float(item_data.get("quantidade", 0)),
                        quantidade_minima=float(item_data.get("quantidade_minima", 0)),
                        localizacao=item_data.get("localizacao", ""),
                        categoria_id=cat.id,
                    )
                    self.db.add(item)

                importados += 1
            except Exception:
                erros += 1

        self.db.commit()
        return importados, erros

    def _importar_movimentacoes(self, dados: list[dict]) -> tuple[int, int]:
        from app.models.models import Item, Movimentacao

        importados = 0
        erros = 0

        for mov_data in dados:
            try:
                codigo = str(mov_data.get("codigo") or mov_data.get("CODIGO") or "")
                if not codigo:
                    erros += 1
                    continue

                item = self.db.query(Item).filter(Item.codigo == codigo).first()
                if not item:
                    erros += 1
                    continue

                tipo = mov_data.get("tipo", "entrada").lower()
                if tipo not in ("entrada", "saida"):
                    tipo = "entrada"

                mov = Movimentacao(
                    item_id=item.id,
                    tipo=tipo,
                    quantidade=float(mov_data.get("quantidade", 1)),
                    data=datetime.strptime(mov_data.get("data", ""), "%Y-%m-%d") if mov_data.get("data") else datetime.now(),
                    origem="uspdigital",
                    observacoes=mov_data.get("observacoes", "Importado via sincronizacao USP Digital"),
                )
                self.db.add(mov)

                if tipo == "entrada":
                    item.quantidade_atual = (item.quantidade_atual or 0) + float(mov_data.get("quantidade", 1))
                else:
                    item.quantidade_atual = max(0, (item.quantidade_atual or 0) - float(mov_data.get("quantidade", 1)))

                importados += 1
            except Exception:
                erros += 1

        self.db.commit()
        return importados, erros

    def exportar_para_uspdigital(self, exportar_estoque: bool = False) -> dict:
        if not self.client.session_token:
            return {"success": False, "message": "Nao autenticado no USP Digital"}

        if not exportar_estoque:
            return {"success": True, "message": "Exportacao desabilitada"}

        from app.models.models import Item
        itens = self.db.query(Item).all()
        payload = [
            {
                "codigo": i.codigo,
                "nome": i.nome,
                "quantidade": i.quantidade_atual or 0,
                "unidade": i.unidade_medida,
            }
            for i in itens
        ]
        return self.client.sincronizar_estoque(payload)

    def close(self):
        self.client.close()
