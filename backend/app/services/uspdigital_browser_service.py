import time
import tempfile
import csv
from pathlib import Path
from typing import Optional
from app.config import settings


class USPDigitalBrowserService:
    def __init__(self, db):
        self.db = db

    def extrair_e_importar(self, username: str, password: str, tipos: list[str]) -> dict:
        resultado = {"extraidos": 0, "importados": 0, "erros": 0, "detalhes": []}

        try:
            cookies = self._autenticar_http(username, password)
            if not cookies:
                return {"erro": "Falha na autenticacao HTTP com USP Digital"}

            data = self._extrair_via_playwright(cookies)
            if data and len(data) > 1:
                csv_path = self._salvar_csv(data, "inventario")
                res = self._importar_arquivo(csv_path, "inventario")
                resultado["extraidos"] = res.get("itens", 0)
                resultado["importados"] = res.get("importados", 0)
                resultado["erros"] = res.get("erros", 0)
                resultado["detalhes"].append({"tipo": "inventario", **res})
            else:
                resultado["erro"] = "Nenhum dado encontrado no USP Digital"
                resultado["detalhes"].append({"tipo": "inventario", "itens": 0, "erro": "lista vazia"})

        except Exception as e:
            import traceback
            return {"erro": f"Erro na automacao: {str(e)}\n{traceback.format_exc()}"}

        return resultado

    def _autenticar_http(self, username: str, password: str) -> Optional[dict]:
        try:
            import httpx
            s = httpx.Client(follow_redirects=True, verify=False, timeout=30)
            s.post("https://uspdigital.usp.br/administrativo/autenticar", data={
                "codpes": username,
                "senusu": password,
                "url": "",
            })
            cookies = dict(s.cookies)
            s.close()
            if cookies.get("JSESSIONID") or cookies.get("SSOSESSIONID"):
                return cookies
            return None
        except Exception:
            return None

    def _extrair_via_playwright(self, cookies: dict) -> list:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=settings.BROWSER_HEADLESS,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            context.set_default_timeout(settings.BROWSER_TIMEOUT)

            for nome, valor in cookies.items():
                context.add_cookies([{"name": nome, "value": valor, "domain": "uspdigital.usp.br", "path": "/"}])

            page = context.new_page()
            page.goto("https://uspdigital.usp.br/administrativo/admAlmoxEstoqueListar?codatz=(123)&codmnu=9421", timeout=30000)
            page.wait_for_load_state("networkidle")
            time.sleep(2)

            data = page.evaluate("""
                () => new Promise((resolve, reject) => {
                    const timeout = setTimeout(() => reject('timeout'), 30000);

                    function obterDadosDoGrid() {
                        try {
                            const grid = $('#tableEstoque');
                            if (!grid || !grid.jqGrid) return null;
                            const rows = grid.jqGrid('getRowData');
                            if (rows && rows.length > 0) {
                                clearTimeout(timeout);
                                return rows;
                            }
                        } catch(e) {}
                        return null;
                    }

                    // Primeiro verifica se ja tem dados
                    const existentes = obterDadosDoGrid();
                    if (existentes) {
                        resolve(existentes);
                        return;
                    }

                    // Registrar callback antes de chamar a DWR
                    var _callbackRegistrado = true;

                    function listarComRetorno() {
                        var bean = {
                            codbem: $('#codbem').val() || '',
                            coditmmat: $('#coditmmat').val() || '',
                            codunddsp: $('#codunddsp').val() || '',
                            staqtdeatl: $('#staqtdeatl').val() || ''
                        };

                        ControleAutorizadoDWR.listar('admLisESTOQUE', bean, {
                            callback: function(lista) {
                                if (lista && lista.length > 0) {
                                    // Forcar o grid a carregar
                                    $('#tableEstoque').jqGrid('clearGridData');
                                    $('#tableEstoque').jqGrid('setGridParam', {
                                        datatype: 'local',
                                        data: lista
                                    }).trigger('reloadGrid');

                                    // Aguardar grid renderizar e extrair dados
                                    setTimeout(function() {
                                        var rows = $('#tableEstoque').jqGrid('getRowData');
                                        clearTimeout(timeout);
                                        resolve(rows);
                                    }, 1000);
                                } else {
                                    clearTimeout(timeout);
                                    resolve([]);
                                }
                            },
                            errorHandler: function(msg) {
                                clearTimeout(timeout);
                                reject(msg);
                            },
                            timeout: 30000,
                            preHook: function() {},
                            postHook: function() {}
                        });
                    }

                    // Tentar periodicamente se o DWR ja estiver pronto
                    var attempts = 0;
                    function tryListar() {
                        attempts++;
                        if (typeof ControleAutorizadoDWR !== 'undefined') {
                            listarComRetorno();
                        } else if (attempts < 20) {
                            setTimeout(tryListar, 500);
                        } else {
                            clearTimeout(timeout);
                            reject('DWR nao inicializado apos 10s');
                        }
                    }
                    tryListar();
                });
            """)

            browser.close()
            return data

    def _salvar_csv(self, data: list, tipo: str) -> str:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8-sig")
        if not data:
            data = []

        fieldnames = ["CODIGO", "DESCRICAO", "UNIDADE", "SALDO", "GRUPO"]

        renamed = []
        for row in data:
            new_row = {
                "CODIGO": row.get("codbem", row.get("coditmmat", "")),
                "DESCRICAO": row.get("nomitmmat", ""),
                "UNIDADE": row.get("sglunddsp", "UN"),
                "SALDO": row.get("qtdatl", "0"),
                "GRUPO": row.get("nomgrpitmmat", row.get("tipitmmat", tipo)),

            }
            renamed.append(new_row)

        writer = csv.DictWriter(tmp, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(renamed)
        tmp.close()
        return tmp.name

    def _importar_arquivo(self, caminho: str, tipo: str) -> dict:
        from app.services.import_spreadsheet_service import SpreadsheetImportService
        servico = SpreadsheetImportService(self.db)
        resultado = servico.importar_relatorio(caminho, tipo)

        if resultado.get("status") == "sucesso":
            return {
                "itens": resultado.get("total_itens", 0),
                "importados": resultado.get("total_itens", 0),
                "erros": 0,
                "arquivo": caminho,
            }
        return {"itens": 0, "importados": 0, "erros": 0, "erro": resultado.get("erro", "Falha ao importar")}
