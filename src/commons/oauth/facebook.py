from src.commons.base import ApiClientBase
from src.config.configs import facebook_settings
from src.constants.errors import DomainError
from src.constants.errors import ErrorCodes


class FacebookClient(ApiClientBase):
    token_url = "https://graph.facebook.com/v10.0/oauth/access_token"
    user_info_ulr = "ttps://graph.facebook.com/me"

    async def get_email(self, code) -> str:

        async with self._get_client() as client:
            token_response = await client.get(
                self.token_url,
                params={
                    "client_id": facebook_settings.FACEBOOK_APP_ID,
                    "redirect_uri": facebook_settings.FACEBOOK_CALLBACK_URL,
                    "client_secret": facebook_settings.FACEBOOK_APP_SECRET,
                    "code": code,
                },
                headers={"Accept": "application/json"},
            )
            token_response_data = token_response.json()
            token = token_response_data["access_token"]

            if not token:
                raise DomainError(ErrorCodes.OAUTH_TOKEN_ERROR)

            response = await client.get(
                self.user_info_ulr,
                headers={"Authorization": f"Bearer {token}"},
                params={"fields": "email"},
            )
            return response.json()["email"]
