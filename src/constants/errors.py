import enum

from pydantic import BaseModel


class Error(BaseModel):
    detail: str


class ErrorCodes(enum.Enum):
    COULD_NOT_VALIDATE_CREDENTIALS = "Could not validate credentials"
    UNAUTHORIZED = "Unauthorized"
    EMAIL_ALREADY_EXISTS = "Email already exsists"
    EMAIL_NOT_FOUND = "Email not found"
    INVALID_PASSWORD = "Invalid password"
    YOU_DONT_NAVE_PERMISSION = "You don`t have permission"
    USER_NOT_FOUND = "User not found"
    PASSWORDS_DONT_MATCH = "Passwords don't match"
    ERROR_SEND_MAIL = "Error send mail"
    INVALID_VERIFICATION_CODE = "Invalid_verification_code"
    VERIFICATION_CODE_NOT_FOUND = "Verification code not found"
    PHONE_NUMBER_ALREADY_EXISTS = "Phone number already exists"
    ERROR_SEND_SMS = "Error send sms"
    PHONE_NOT_FOUND = "Phone not found"
    OTP_NOT_FOUND = "Otp not found"
    OAUTH_TOKEN_ERROR = "Oauth token error"
    EMAIL_NOT_ADDED_IN_YOUR_ACCOUNT = "Email not added in your account"


class DomainError(Exception):
    code: ErrorCodes

    def __init__(self, code: ErrorCodes, message: str | None = None):
        self.code = code
        super().__init__(message)


ERROR_STATUS_MAP = {
    ErrorCodes.COULD_NOT_VALIDATE_CREDENTIALS: 403,
    ErrorCodes.UNAUTHORIZED: 401,
    ErrorCodes.EMAIL_ALREADY_EXISTS: 400,
    ErrorCodes.EMAIL_NOT_FOUND: 404,
    ErrorCodes.INVALID_PASSWORD: 400,
    ErrorCodes.YOU_DONT_NAVE_PERMISSION: 403,
    ErrorCodes.USER_NOT_FOUND: 404,
    ErrorCodes.PASSWORDS_DONT_MATCH: 400,
    ErrorCodes.ERROR_SEND_MAIL: 400,
    ErrorCodes.INVALID_VERIFICATION_CODE: 400,
    ErrorCodes.VERIFICATION_CODE_NOT_FOUND: 404,
    ErrorCodes.PHONE_NUMBER_ALREADY_EXISTS: 400,
    ErrorCodes.PHONE_NOT_FOUND: 404,
    ErrorCodes.OTP_NOT_FOUND: 404,
}
