from pydantic import BaseModel

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str

class RefreshIn(BaseModel):
    refresh_token: str

class LoginIn(BaseModel):
    login: str
    password: str 