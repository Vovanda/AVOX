from fastapi import APIRouter, Request, Depends, HTTPException, Body
from fastapi.responses import RedirectResponse

from auth.app.deps import get_vk_oauth_provider
from auth.app.models.auth import AuthResponse
from auth.app.services.session import create_or_get_user_session

router = APIRouter()

@router.get(
    "/api/login/vk",
    summary="VK OAuth: инициация авторизации",
    description="Перенаправляет пользователя на страницу авторизации VK OAuth."
)
async def login_via_vk(vk_oauth_provider=Depends(get_vk_oauth_provider)):
    """VK OAuth вход: редиректит на страницу авторизации ВКонтакте."""
    redirect_uri = vk_oauth_provider.get_authorize_redirect_uri()
    return RedirectResponse(redirect_uri)

@router.get(
    "/api/auth/callback/vk",
    response_model=AuthResponse,
    summary="VK OAuth: callback обработчик",
    description="Обработка кода авторизации от ВКонтакте, получение токена и информации о пользователе."
)
async def vk_callback(
    request: Request,
    vk_oauth_provider=Depends(get_vk_oauth_provider)
):
    """
    Callback endpoint VK OAuth.
    Получает code, обменивает его на access_token, возвращает токен и профиль пользователя.
    """
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")
    token = await vk_oauth_provider.fetch_token(code)
    user_info = await vk_oauth_provider.get_user_info(token)
    session = await create_or_get_user_session(user_info)

    response = {
        "access_token": session["access_token"],
        "user": user_info
    }
    if "refresh_token" in token:
        response["refresh_token"] = token["refresh_token"]
    if "expires_in" in token:
        response["expires_in"] = token["expires_in"]
    return response

@router.post(
    "/api/auth/token/refresh",
    summary="Обновление access_token по refresh_token",
    description="Получает новый access_token по refresh_token из VK OAuth.",
    response_model=AuthResponse
)
async def refresh_token_via_vk(
    vk_oauth_provider=Depends(get_vk_oauth_provider),
    body: dict = Body(...)
):
    """
    Endpoint для обновления access_token по refresh_token.
    """
    refresh_token = body.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Missing refresh_token")
    token = await vk_oauth_provider.refresh_access_token(refresh_token)
    response = {
        "access_token": token.get("access_token"),
        "refresh_token": token.get("refresh_token"),
        "expires_in": token.get("expires_in"),
        "token_type": token.get("token_type", "Bearer"),
    }
    return response

@router.get(
    "/health",
    summary="Проверка здоровья сервиса",
    description="Возвращает статус работы сервиса.",
    tags=["Health"]
)
async def health_check():
    """
    Healthcheck endpoint.
    Используется для мониторинга работоспособности auth-сервиса.
    """
    return {"status": "ok"}
