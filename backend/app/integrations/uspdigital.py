import httpx
from typing import Optional
from app.config import settings


class USPDigitalClient:
    def __init__(self):
        self.wsusuario_url = settings.USP_DIGITAL_LOGIN_URL
        self.admin_url = settings.USP_DIGITAL_BASE_URL
        self.session_token: Optional[str] = None
        self.cookies = {}
        self.client = httpx.Client(
            timeout=settings.USP_DIGITAL_TIMEOUT,
            follow_redirects=True,
        )

    def login(self, username: str, password: str) -> bool:
        try:
            resp = self.client.post(
                f"{self.wsusuario_url}/j_security_check",
                data={"j_username": username, "j_password": password},
            )
            for name, value in self.client.cookies.items():
                self.cookies[name] = value
                if "jsessionid" in name.lower() or "session" in name.lower():
                    self.session_token = value
            return resp.status_code == 200 and bool(self.session_token)
        except httpx.HTTPError:
            return False

    def autenticado(self) -> bool:
        return self.session_token is not None

    def extrair_materiais(self, params: dict = None) -> list[dict]:
        return []

    def extrair_patrimonio(self, codigo_usp: str) -> Optional[dict]:
        return None

    def sincronizar_estoque(self, itens: list[dict]) -> dict:
        return {"success": False, "message": "Nao disponivel via API"}

    def close(self):
        self.client.close()
