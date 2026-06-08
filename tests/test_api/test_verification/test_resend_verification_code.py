from collections.abc import Callable

from dddshared.models.auth import UserSession
from dddshared.models.user import User
from httpx import AsyncClient
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession

from tests import TestVerificationBase


class TestResendVerification(TestVerificationBase):
    async def test_resend_success(
        self,
        http_client: AsyncClient,
        async_session: AsyncSession,
        another_user_fixture: User,
        get_auth_headers: Callable,
        another_user_session_fixture: UserSession,
        mocker: MockerFixture,
    ) -> None:
        mock_mail = mocker.patch("src.tasks.send_mail.kiq", return_value=None)
        response = await http_client.post(
            f"{self.root_url}resend/",
            headers=await get_auth_headers(
                another_user_fixture, another_user_session_fixture
            ),
        )
        assert response.status_code == 200

        assert mock_mail.call_count == 1

        recepient = mock_mail.call_args[1]["recepients"][0]
        assert recepient == another_user_fixture.email
