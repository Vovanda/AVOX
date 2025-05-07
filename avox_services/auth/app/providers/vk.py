from typing import Any, Dict, Optional
import requests
from urllib.parse import urlencode

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

    def exchange_code(self, code: str) -> Dict[str, Any]:
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }
        url = "https://oauth.vk.com/access_token"
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        params = {
            "access_token": access_token,
            "v": "5.131",
        }
        url = "https://api.vk.com/method/users.get"
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("response"):
            return data["response"][0]
        raise Exception("VK user info error")