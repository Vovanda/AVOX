# deps.py
import os
from typing import Annotated

import httpx
from fastapi import Depends

# базовый URL сервиса знаний
KNOWLEDGE_SERVICE_URL = os.getenv("KNOWLEDGE_SERVICE_URL")

async def get_http_client() -> httpx.AsyncClient:
    """
    Асинхронный HTTP клиент, общий для всех запросов.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client

# Заглушка для авторизации (легко отключить)
async def get_token_header() -> str | None:
    """
    Временно возвращает None (авторизация не используется).
    Если захочешь включить — раскомментируй проверку.
    """
    # raise HTTPException(status_code=401, detail="Unauthorized")
    return None


# Алиасы для Depends
HttpClientDep = Annotated[httpx.AsyncClient, Depends(get_http_client)]
AuthTokenDep = Annotated[str | None, Depends(get_token_header)]
