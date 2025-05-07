from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from .base import BaseOAuthProvider


class VKOAuthProvider(BaseOAuthProvider):
    name = "vk"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorize_url(self, state: Optional[str] = None) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "display": "page",
            "scope": "email",
            "response_type": "code",
            "v": "5.131",
        }
        if state:
            params["state"] = state
        url = "https://oauth.vk.com/authorize?" + urlencode(params)
        return url

    def exchange_code(self, code: str, code_verifier: Optional[str] = None) -> Dict[str, Any]:
        """
        Обмен авторизационного кода на токен VK через Authorization Code Flow (бэкенд).
        Использует PKCE при наличии code_verifier.
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
        }
        if code_verifier:
            data["code_verifier"] = code_verifier  # PKCE
        url = "https://id.vk.com/oauth2/token"
        response = requests.post(url, data=data)
        response.raise_for_status()
        result = response.json()
        # Возвращаем все полученные VK поля, как в спецификации VK:
        # access_token, refresh_token, token_type, expires_in, user_id, id_token, scope
        return result

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Обновление access_token с помощью refresh_token.
        """
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        url = "https://id.vk.com/oauth2/token"
        response = requests.post(url, data=data)
        response.raise_for_status()
        result = response.json()
        # Структура ответа аналогична методу exchange_code (VK спецификация)
        return result

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Получение информации о пользователе VK по access_token.
        Флаг is_verified: признак подтверждённого (верифицированного) аккаунта.
        """
        params = {
            "access_token": access_token,
            "v": "5.131",
            "fields": "id,first_name,last_name,domain,is_verified"
        }
        url = "https://api.vk.com/method/users.get"
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("response"):
            return data["response"][0]
        raise Exception("VK user info error")