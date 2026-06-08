from collections.abc import Callable

from dddshared.models.auth import UserSession
from dddshared.models.user import User
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests import TestAuthBase


class TestLogin(TestAuthBase):
    async def test_logout_success(
        self,
        http_client: AsyncClient,
        user_fixture: User,
        user_session_fixture: UserSession,
        get_auth_headers: Callable,
        async_session: AsyncSession,
    ) -> None:
        response = await http_client.post(
            f"{self.root_url}logout/",
            headers=await get_auth_headers(user_fixture, user_session_fixture),
            params={"mode": "one_device"},
        )
        assert response.status_code == 200

        await async_session.close()
        deactivetd_session = await async_session.get(
            UserSession, user_session_fixture.id
        )
        assert deactivetd_session.is_active is False
