from pydantic import BaseModel

class UserInfo(BaseModel):
    id: int
    name: str
    email: str | None = None

class AuthResponse(BaseModel):
    access_token: str
    user: UserInfo