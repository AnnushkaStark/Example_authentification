from collections.abc import Callable

from dddshared.models.auth import UserSession
from dddshared.models.auth import VerificationCode
from dddshared.models.user import User
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.constants.errors import ErrorCodes
from tests import TestVerificationBase


class TestVerification(TestVerificationBase):
    async def test_verification_success(
        self,
        http_client: AsyncClient,
        async_session: AsyncSession,
        another_user_fixture: User,
        verification_code_fixture: VerificationCode,
        get_auth_headers: Callable,
        another_user_session_fixture: UserSession,
    ) -> None:
        response = await http_client.post(
            f"{self.root_url}",
            params={"code": verification_code_fixture.code},
            headers=await get_auth_headers(
                another_user_fixture, another_user_session_fixture
            ),
        )
        assert response.status_code == 200

        await async_session.close()
        verify_user = await async_session.get(User, another_user_fixture.id)
        assert verify_user.is_verified is True

    async def test_verify_with_invalid_code(
        self,
        http_client: AsyncClient,
        another_user_fixture: User,
        get_auth_headers: Callable,
        another_user_session_fixture: UserSession,
    ) -> None:
        response = await http_client.post(
            f"{self.root_url}",
            params={"code": "0000"},
            headers=await get_auth_headers(
                another_user_fixture, another_user_session_fixture
            ),
        )
        assert response.status_code == 404

        response_data = response.json()
        assert (
            response_data["detail"]
            == ErrorCodes.VERIFICATION_CODE_NOT_FOUND.value
        )

    async def test_with_expired_code(
        self,
        http_client: AsyncClient,
        another_user_fixture: User,
        expired_code_fixture: VerificationCode,
        get_auth_headers: Callable,
        another_user_session_fixture: UserSession,
    ) -> None:
        response = await http_client.post(
            f"{self.root_url}",
            params={"code": expired_code_fixture.code},
            headers=await get_auth_headers(
                another_user_fixture, another_user_session_fixture
            ),
        )
        assert response.status_code == 400

        response_data = response.json()
        assert (
            response_data["detail"]
            == ErrorCodes.INVALID_VERIFICATION_CODE.value
        )
