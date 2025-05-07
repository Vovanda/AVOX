import pytest

from auth.app.services import session


@pytest.mark.asyncio
@pytest.mark.displayname("Создание новой сессии пользователя")
async def test_create_or_get_user_session_creates_new_session():
    # Проверка, что при отсутствии сессии создаётся новая
    user_info = {"id": "42", "name": "Some User"}
    s = await session.create_or_get_user_session(user_info)
    assert s["user_id"] == "42"
    assert "access_token" in s

@pytest.mark.asyncio
@pytest.mark.displayname("Повторный вызов возвращает существующую сессию")
async def test_create_or_get_user_session_returns_existing():
    # Проверка, что повторный вызов возвращает ту же сессию пользователя
    user_info = {"id": "100", "name": "User100"}
    first = await session.create_or_get_user_session(user_info)
    second = await session.create_or_get_user_session(user_info)
    assert first["access_token"] == second["access_token"]

@pytest.mark.asyncio
@pytest.mark.displayname("Инвалидированная сессия удаляется")
async def test_invalidate_session_removes_token():
    # Проверка, что после инвалидирования сессии токен удаляется
    user_info = {"id": "1"}
    s = await session.create_or_get_user_session(user_info)
    await session.invalidate_session(s["access_token"])
    assert await session.get_session(s["access_token"]) is None