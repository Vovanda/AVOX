from typing import Dict, Any, Optional
import uuid

# Для демо: база сессий в памяти. В production — использовать Redis/BД
# TODO AVOX-8
SESSIONS: Dict[str, Dict[str, Any]] = {}

async def create_or_get_user_session(user_info: dict) -> dict:
    """
    Создать или найти сессию для пользователя по user_info.
    Возвращает словарь: {'access_token': токен, ...}
    """
    user_id = str(user_info.get("id"))
    # Проверим, есть ли уже валидная сессия
    for token, session in SESSIONS.items():
        if session["user_id"] == user_id:
            return session

    # Если нет — создать новую сессию
    access_token = str(uuid.uuid4())
    session = {
        "user_id": user_id,
        "access_token": access_token,
        "user_info": user_info
        # ...доп. поля: expires, roles, refresh, etc.
    }
    SESSIONS[access_token] = session
    return session

async def get_session(access_token: str) -> Optional[dict]:
    """
    Получить сессию по access_token.
    """
    return SESSIONS.get(access_token)

async def invalidate_session(access_token: str):
    """
    Инвалидировать (удалить) сессию по токену.
    """
    SESSIONS.pop(access_token, None)