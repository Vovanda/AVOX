from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseOAuthProvider(ABC):
    name: str

    @abstractmethod
    def get_authorize_url(self, state: Optional[str] = None) -> str:
        """Генерирует URL для редиректа пользователя на провайдера OAuth."""
        pass

    def get_authorize_redirect_uri(self, state: Optional[str] = None) -> str:
        """
        По умолчанию вызывает get_authorize_url.
        """
        return self.get_authorize_url(state)

    @abstractmethod
    def exchange_code(self, code: str, code_verifier: Optional[str] = None) -> Dict[str, Any]:
        """Обменивает code на access_token (и refresh, если есть)."""
        pass

    @abstractmethod
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Обновляет access_token с использованием refresh_token."""
        pass

    @abstractmethod
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Получает базовые сведения о пользователе с помощью access_token."""
        pass
