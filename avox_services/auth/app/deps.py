# deps.py

from auth.app.core import config
from auth.app.providers.vk import VKOAuthProvider

def get_vk_oauth_provider():
    """
    FastAPI dependency для получения VKOAuthProvider (safe singleton, test-friendly).
    В production всегда возвращает один экземпляр на приложение.
    При тестах/переопределениях singleton сбрасывается автоматически.
    """
    # Проверяем “test mode” для сброса singleton-а (например, через fixture)
    if getattr(get_vk_oauth_provider, "_force_new", False):
        if hasattr(get_vk_oauth_provider, "_provider"):
            del get_vk_oauth_provider._provider
        get_vk_oauth_provider._force_new = False

    if not hasattr(get_vk_oauth_provider, "_provider"):
        get_vk_oauth_provider._provider = VKOAuthProvider(
            client_id=config.VK_CLIENT_ID,
            client_secret=config.VK_CLIENT_SECRET,
            redirect_uri=config.VK_REDIRECT_URI
        )
    return get_vk_oauth_provider._provider

# --- Вспомогательные функции для тестов ---

def reset_vk_oauth_provider_singleton():
    """
    Сброс singleton-провайдера (вызывать в фикстурах перед/после теста).
    """
    if hasattr(get_vk_oauth_provider, "_provider"):
        del get_vk_oauth_provider._provider

def force_recreate_vk_provider():
    """
    Флаг для форсированной пересборки провайдера при следующем вызове.
    """
    get_vk_oauth_provider._force_new = True