import pytest
from fastapi.testclient import TestClient

from auth.app.deps import get_vk_oauth_provider, reset_vk_oauth_provider_singleton
from auth.app.main import app
from auth.tests.mocks.mock_vk_oauth_provider import MockVkOAuthProvider


@pytest.fixture(autouse=True)
def override_vk_provider():
    """
    Глобальная фикстура для подмены VK OAuth провайдера на тестовый мок
    и сброса singleton (test-friendly singleton pattern).
    """
    reset_vk_oauth_provider_singleton()
    app.dependency_overrides[get_vk_oauth_provider] = lambda: MockVkOAuthProvider()
    yield
    app.dependency_overrides = {}
    reset_vk_oauth_provider_singleton()

@pytest.mark.displayname("Refresh токена VK")
def test_refresh_access_token():
    """Проверка обновления access_token по refresh_token"""
    client = TestClient(app)
    response = client.post("/api/auth/token/refresh", json={
        "refresh_token": "mock_refresh_token"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "refreshed-access-token"
    assert data["refresh_token"] == "refreshed-refresh-token"
    assert data["expires_in"] == 3600
    assert data["token_type"] == "Bearer" or "token_type" not in data

@pytest.mark.displayname("Создание сессии после callback VK")
def test_vk_callback_creates_session():
    """Проверка успешного создания пользовательской сессии после возврата VK (callback)"""
    client = TestClient(app)
    response = client.get("/api/auth/callback/vk", params={"code": "dummy_code"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data.get("refresh_token") == "mock-refresh-token"
    assert data.get("expires_in") == 3600
    assert data["user"]["id"] == 12345
    assert data["user"]["name"] == "Mock User"
    assert data["user"]["email"] is None