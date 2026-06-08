from dddshared.models.user import User
from httpx import AsyncClient

from src.constants.errors import ErrorCodes
from src.schemas.auth import BaseRegister
from tests import TestAuthBase


class TestLogin(TestAuthBase):
    async def test_login_success(
        self,
        http_client: AsyncClient,
        user_fixture: User,
    ) -> None:
        data = BaseRegister(email=user_fixture.email, password="12345678")
        response = await http_client.post(
            f"{self.root_url}login_jwt/", json=data.model_dump()
        )
        assert response.status_code == 200

        tokens = response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens

    async def test_login_with_invalid_email(
        self,
        http_client: AsyncClient,
    ) -> None:
        response = await http_client.post(
            f"{self.root_url}login_jwt/",
            json=BaseRegister(
                email="invalidmail@gmail.com", password="12345678"
            ).model_dump(),
        )
        assert response.status_code == 404

        response_data = response.json()
        assert response_data["detail"] == ErrorCodes.EMAIL_NOT_FOUND.value

    async def test_login_with_invalid_password(
        self, http_client: AsyncClient, user_fixture: User
    ) -> None:
        response = await http_client.post(
            f"{self.root_url}login_jwt/",
            json=BaseRegister(
                email=user_fixture.email, password="123456789"
            ).model_dump(),
        )
        assert response.status_code == 400

        response_data = response.json()
        assert response_data["detail"] == ErrorCodes.INVALID_PASSWORD.value
