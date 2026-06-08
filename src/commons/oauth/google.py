from src.commons.base import ApiClientBase
from src.config.configs import google_settings
from src.constants.errors import DomainError
from src.constants.errors import ErrorCodes


class GoogleClient(ApiClientBase):
    async def get_email(self, code: str) -> dict[str, str]:
        async with self._get_client() as client:
            token_response = await client.post(
                google_settings.GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": google_settings.GOOGLE_CLIENT_ID,
                    "client_secret": google_settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": google_settings.GOOGLE_CALLBACK_URL,
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
            )

            token_response_data = token_response.json()
            token = token_response_data["access_token"]

            if not token:
                raise DomainError(ErrorCodes.OAUTH_TOKEN_ERROR)

            user_info_response = await client.get(
                google_settings.GOOGLE_USER_INFO_URL,
                headers={"Authorization": f"Bearer {token}"},
            )
            user_data = user_info_response.json()
            return user_data["email"]
