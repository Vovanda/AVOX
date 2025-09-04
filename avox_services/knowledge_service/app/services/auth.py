import os
import uuid

from fastapi import HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from knowledge_service.app.models.core.company import User
from knowledge_service.app.models.enums import UserRole, AuthProvider

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

APP_ENV = os.getenv("APP_ENV", "local")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = "HS256"

async def get_current_active_user(request: Request) -> User:
    """
    Возвращает текущего активного пользователя, используя заголовки или окружение.
    """

    if APP_ENV == "local":
        # Возврат пользователя-заглушки в локальной среде
        return User(
            id=uuid.UUID("32a77924-f937-416e-ab5b-8f3cb55bac25"),
            company_id=uuid.UUID("8eeaee24-0f71-4994-bb66-3fb8e5920648"),
            role=UserRole.ADMIN,
            provider=AuthProvider.INTERNAL
        )

    # Получаем данные из заголовков
    user_id = request.headers.get("X-User-Id")
    user_role = request.headers.get("X-User-Role")
    user_active = request.headers.get("X-User-Is-Active")

    # Проверка наличия всех необходимых заголовков
    if not user_id or not user_role or user_active is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing user identification headers"
        )

    # Проверка активности пользователя
    if user_active.lower() != "true":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    try:
        return User(
            id=uuid.UUID(user_id),
            role=UserRole(user_role)
            # Другие поля (email, provider и т.п.) можно добавить по необходимости
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user header values: {e}"
        )
