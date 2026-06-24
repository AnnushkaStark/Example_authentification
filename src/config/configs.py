from pathlib import Path

from .base import BaseSetting

BASE_DIR = Path(__file__).parent.parent


class DBSettings(BaseSetting):
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_USER_DB: str | None = None


class JWTSettings(BaseSetting):
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRES: int
    JWT_REFRESH_TOKEN_EXPIRES: int
    ACCESS_TOKEN_COOKIE_KEY: str
    REFRESH_TOKEN_COOKIE_KEY: str


class RedisSettings(BaseSetting):
    HOST: str = "redis"
    PORT: int = 6379
    REDIS_URL: str = "redis://redis:6379/0"


class FacebookSettings(BaseSetting):
    FACEBOOK_APP_ID: str
    FACEBOOK_APP_SECRET: str
    FACEBOOK_CALLBACK_URL: str
    FACEBOOK_TOKEN_URL: str
    FACEBOOK_USER_INFO_URL: str

    def get_authorization_uri(self) -> str:
        return f"https://www.facebook.com/v10.0/dialog/oauth?client_id={self.FACEBOOK_APP_ID}&redirect_uri={self.FACEBOOK_CALLBACK_URL}&scope=email&response_type=code"  # noqa: E231 E501


class YandexSettings(BaseSetting):
    YANDEX_CLIENT_ID: str
    YANDEX_CLIENT_SECRET: str
    YANDEX_REDIRECT_URI: str

    def get_redirect_uri(self) -> str:
        base_url = "https://oauth.yandex.ru/authorize"

        params = (
            f"?response_type=code"
            f"&client_id={self.YANDEX_CLIENT_ID}"
            f"&redirect_uri={self.YANDEX_REDIRECT_URI}"
            f"&scope=login:email"
            f"&force_confirm=yes"
        )

        return base_url + params


class AppSettings(BaseSetting):
    FRONTEND_URL: str
    OAUTH_SUCESS_URL: str
    TG_PROXY: str


class SmsSettings(BaseSetting):
    SMS_API_KEY: str
    SMS_CALLBACK_URL: str


class GoogleSettings(BaseSetting):
    GOOGLE_CALLBACK_URL: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_TOKEN_URL: str
    GOOGLE_USER_INFO_URL: str

    def get_authorization_uri(self) -> str:
        return f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={self.GOOGLE_CLIENT_ID}&redirect_uri={self.GOOGLE_CALLBACK_URL}&scope=openid%20email%20profile"  # noqa: E231 E501


class VkSettings(BaseSetting):
    APP_ID: str
    PRIVATE_KEY: str
    SERVICE_KEY: str
    VK_CALLBACK_URL: str


class TgGatwaySettings(BaseSetting):
    GATWAY_KEY: str


class SentrySettings(BaseSetting):
    AUTH_SENTRY_DNS: str | None = None


class AuthBotSettings(BaseSetting):
    AUTH_BOT_CLIENT_ID: str
    AUTH_BOT_CALLBACK_URL: str
    AUTH_BOT_CLIENT_SECRET: str


auth_bot_settings = AuthBotSettings()
sentry_settings = SentrySettings()
tg_api_gatway_settings = TgGatwaySettings()
vk_settings = VkSettings()
google_settings = GoogleSettings()
sms_settings = SmsSettings()
yandex_settings = YandexSettings()
app_settings = AppSettings()
facebook_settings = FacebookSettings()
redis_settings = RedisSettings()
jwt_settings = JWTSettings()
db_settings = DBSettings()
