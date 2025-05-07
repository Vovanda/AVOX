from auth.app.core import config
from auth.app.providers.vk import VKOAuthProvider

# Глобальный провайдер для production
_global_provider = None

def get_vk_oauth_provider():
    """
    FastAPI dependency для получения VKOAuthProvider (singleton).
    Поддерживает тестирование через dependency_overrides.
    """
    global _global_provider
    if _global_provider is None:
        _global_provider = VKOAuthProvider(
            client_id=config.VK_CLIENT_ID,
            client_secret=config.VK_CLIENT_SECRET,
            redirect_uri=config.VK_REDIRECT_URI
        )
    return _global_provider