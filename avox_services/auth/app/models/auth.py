from pydantic import BaseModel

class UserInfo(BaseModel):
    id: int
    name: str
    email: str | None = None

class AuthResponse(BaseModel):
    access_token: str
    user: UserInfo | None = None
    refresh_token: str | None = None
    expires_in: int | None = None
    token_type: str | None = None
