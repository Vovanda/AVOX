from fastapi import APIRouter, Request, Depends, HTTPException, Body

from auth.app.deps import get_vk_oauth_provider
from auth.app.models.auth import AuthResponse

router = APIRouter()

@router.get(
    "/callback/vk",
    response_model=AuthResponse,
    summary="VK OAuth: callback обработчик",
    description="Обработка кода авторизации от ВКонтакте, получение токена и информации о пользователе."
)
async def vk_callback(
    request: Request,
    vk_oauth_provider=Depends(get_vk_oauth_provider)
):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")
    token = vk_oauth_provider.exchange_code(code)
    vk_data = vk_oauth_provider.get_user_info(token["access_token"])
    user_info = {
        "id": int(vk_data["id"]),
        "name": f"{vk_data['first_name']} {vk_data['last_name']}",
        "email": vk_data.get("email")
    }
    return {
        "access_token": token.get("access_token", "..."),
        "refresh_token": token.get("refresh_token", "..."),
        "expires_in": token.get("expires_in", 3600),
        "token_type": token.get("token_type", "Bearer"),
        "user": user_info
    }
@router.post(
    "/token/refresh",
    summary="Обновление access_token по refresh_token",
    description="Получает новый access_token по refresh_token из VK OAuth.",
    response_model=AuthResponse
)
async def refresh_token_via_vk(
    vk_oauth_provider=Depends(get_vk_oauth_provider),
    body: dict = Body(...)
):
    refresh_token = body.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Missing refresh_token")
    token = vk_oauth_provider.refresh_access_token(refresh_token)
    response = {
        "access_token": token.get("access_token"),
        "refresh_token": token.get("refresh_token"),
        "expires_in": token.get("expires_in"),
        "token_type": token.get("token_type", "Bearer"),
    }
    return response
