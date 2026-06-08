from datetime import datetime
from uuid import UUID

from dddshared.models.enums import DeviceType
from dddshared.models.enums import Locale
from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field

from schemas import PhoneString


class BaseRegister(BaseModel):
    email: EmailStr | None = None
    password: str


class Register(BaseRegister):
    name: str | None = None
    surname: str | None = None
    phone_number: PhoneString | None = None
    document_version: str
    accepted: bool = True


class UserCreate(BaseRegister):
    name: str | None = None
    surname: str | None = None
    phone_number: PhoneString | None = None
    is_verified: bool


class VerificationBase(BaseModel):
    code: str


class VerivficationCodeCreate(VerificationBase):
    user_id: int
    expired_at: datetime


class UserSessionBase(BaseModel):
    device_type: DeviceType
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
    is_verified: bool
    jti: str
    country: str | None = Field(default=Locale.RU)


class TokenBlacklistCreate(BaseModel):
    jti: str


class UserPolicyCreate(BaseModel):
    ip: str
    accepted: bool
    document_version: str
    user_id: int
