from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseOAuthProvider(ABC):
    name: str

    @abstractmethod
    def get_authorize_url(self, state: Optional[str] = None) -> str:
        """Генерирует URL для редиректа пользователя на провайдера OAuth."""
        pass

    @abstractmethod
    def exchange_code(self, code: str) -> Dict[str, Any]:
        """Обменивает code на access_token (и refresh, если есть)."""
        pass

    @abstractmethod
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Получает базовые сведения о пользователе с помощью access_token."""
        pass