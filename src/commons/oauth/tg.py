import base64
import json
import secrets

from src.commons.base import ApiClientBase
from src.commons.state import State
from src.config.configs import app_settings
from src.config.configs import auth_bot_settings


class TgClient(ApiClientBase):
    def __init__(self, state: State):
        self.state = state
        self.key = "tg_auth"
        self.auth_url = "https://oauth.telegram.org/auth"
        self.token_url = "https://oauth.telegram.org/token"
        self.jwks_url = "https://oauth.telegram.org/.well-known/jwks.json"

    async def get_auth_uri(self) -> str:
        state = secrets.token_urlsafe(32)
        code_verifier, code_challenge = self._generate_pkce_pair()
        await self.state.set_state(key=state, value=code_verifier)
        return self._generate_redirect_uri(
            scope="openid profile phone",
            client_code=auth_bot_settings.AUTH_BOT_CLIENT_ID,
            redirect_uri=auth_bot_settings.AUTH_BOT_CALLBACK_URL,
            code_challenge=code_challenge,
            auth_url=self.auth_url,
            state=state,
        )

    async def get_user_phone(self, code: str, state: str) -> str:
        credentials = f"{auth_bot_settings.AUTH_BOT_CLIENT_ID}:{auth_bot_settings.AUTH_BOT_CLIENT_SECRET}"  # noqa: E501
        encoded_creds = base64.b64encode(credentials.encode()).decode()
        headers = {
            "Authorization": f"Basic {encoded_creds}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        verifier = await self.state.get_state(key=state)
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": auth_bot_settings.AUTH_BOT_CALLBACK_URL,
            "client_id": auth_bot_settings.AUTH_BOT_CLIENT_ID,
            "code_verifier": verifier.decode("utf-8"),
        }
        async with self._get_client(proxy=app_settings.TG_PROXY) as client:
            response = await client.post(
                self.token_url, data=data, headers=headers
            )
            data = response.json()
            id_token = data.get("id_token")
            if id_token:
                payload_b64 = id_token.split(".")[1]
                missing_padding = len(payload_b64) % 4
                if missing_padding:
                    payload_b64 += "=" * (4 - missing_padding)

                user_data = json.loads(
                    base64.b64decode(payload_b64).decode("utf-8")
                )
                phone = user_data.get("phone_number", "")

                if phone:
                    return f"+{phone}"
