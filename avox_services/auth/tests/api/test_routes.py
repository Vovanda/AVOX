import pytest
from fastapi.testclient import TestClient

from auth.app.deps import get_vk_oauth_provider
from auth.app.main import app
from auth.tests.mocks.mock_vk_oauth_provider import MockVkOAuthProvider


#TODO: fix tests and locgic
@pytest.fixture(autouse=True)
def override_vk_provider():
    # Помечаем функцию как тестовую, чтобы сбросить кеш при вызове
    get_vk_oauth_provider._testing = True

    # Переопределяем провайдера OAuth VK на мок
    original = app.dependency_overrides.copy()
    app.dependency_overrides[get_vk_oauth_provider] = lambda: MockVkOAuthProvider()
    yield


@pytest.mark.displayname("Редирект на VK OAuth")
def test_login_via_vk_redirect():
    """Проверка редиректа пользователя на OAuth-авторизацию VK"""
    client = TestClient(app)

    # Диагностика
    print("\nДоступные маршруты в приложении:")
    for route in app.routes:
        print(f"  {route.path} - {route.methods}")

    # Также проверим, что маршрутизатор подключен
    if hasattr(app, 'routes_registered'):
        print(f"Маршрутизаторы подключены: {app.routes_registered}")

    response = client.client.request("GET", "/api/login/vk")
    assert response.status_code in (302, 307)

@pytest.mark.displayname("Refresh токена VK")
def test_refresh_access_token():
    """Проверка обновления access_token по refresh_token"""
    client = TestClient(app)
    # Допустим, endpoint api/auth/token/refresh реализует обновление токена
    response = client.post("api/auth/token/refresh", json={
        "refresh_token": "mock_refresh_token"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "new_mock_access_token"
    assert data["refresh_token"] == "mock_refresh_token"
    assert data["token_type"] == "Bearer"

@pytest.mark.displayname("Создание сессии после callback VK")
def test_vk_callback_creates_session():
    """Проверка успешного создания пользовательской сессии после возврата VK (callback)"""
    client = TestClient(app)
    response = client.get("api/auth/callback/vk", params={"code": "dummy_code"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["id"] == "12345"
    assert data["user"]["name"] == "Test VK User"