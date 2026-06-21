from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import EmailStr


class UserLogin(BaseModel):
    email: EmailStr | None = None
    password: str


class BaseRegister(UserLogin):
    phone: str


class UserSessionBase(BaseModel):
    client_info: dict[str, str | None] = dict()
    expired_at: datetime
    user_id: int


class TokenAccessRefresh(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenVerify(BaseModel):
    is_valid: bool


class TokenPayload(BaseModel):
    uid: UUID
    jti: str


class TokenBlacklistCreate(BaseModel):
    jti: str
