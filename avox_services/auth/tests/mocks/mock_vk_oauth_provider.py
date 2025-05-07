from typing import Any, Dict, Optional

from auth.app.providers.base import BaseOAuthProvider


class MockVkOAuthProvider(BaseOAuthProvider):
    name = "vk"

    def get_authorize_url(self, state: Optional[str] = None) -> str:
        # Всегда возвращает валидный url (используется в тесте редиректа)
        return "https://oauth.vk.com/authorize"

    # get_authorize_redirect_uri унаследован от BaseOAuthProvider
    def exchange_code(self, code: str, code_verifier: Optional[str] = None) -> Dict[str, Any]:
        # Мок-ответ авторизации
        return {
            "access_token": "mock-access-token",
            "refresh_token": "mock-refresh-token",
            "expires_in": 3600,
        }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        # Мок обновления токена
        return {
            "access_token": "refreshed-access-token",
            "refresh_token": "refreshed-refresh-token",
            "expires_in": 3600,
        }

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        # Мок пользовательской информации
        return {
            "id": "12345",
            "first_name": "Mock",
            "last_name": "User",
            "domain": "mockuser"
        }
