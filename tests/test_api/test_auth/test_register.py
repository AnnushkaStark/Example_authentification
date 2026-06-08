from dddshared.models import UserPolicyAgreement
from dddshared.models.auth import VerificationCode
from dddshared.models.cart.cart import Cart
from dddshared.models.user import User
from httpx import AsyncClient
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.constants.errors import ErrorCodes
from src.schemas.auth import Register
from tests import TestAuthBase


class TestRegister(TestAuthBase):
    async def test_register_success(
        self,
        async_session: AsyncSession,
        http_client: AsyncClient,
        mocker: MockerFixture,
    ) -> None:
        mock_mail = mocker.patch("src.tasks.send_mail.kiq", return_value=None)
        mock_locale = mocker.patch("src.tasks.get_user_ip.kiq")
        data = Register(
            email="new_email@gmail.com",
            password="12345678",
            name="test",
            surname="test",
            phone_number="+79643164478",
            document_version="v1",
            accepted=True,
        )
        response = await http_client.post(
            self.root_url,
            json=data.model_dump(),
            headers={"X-Real-Ip": "127.0.0.1"},
        )

        assert response.status_code == 201

        await async_session.commit()
        new_user = await async_session.execute(
            select(User).where(User.email == data.email)
        )
        new_user = new_user.scalar()
        assert new_user is not None

        user_cart = await async_session.execute(
            select(Cart).where(Cart.user_id == new_user.id)
        )
        assert user_cart is not None

        user_policy = await async_session.execute(
            select(UserPolicyAgreement).where(
                UserPolicyAgreement.user_id == new_user.id
            )
        )
        assert user_policy is not None

        verification_code = await async_session.execute(
            select(VerificationCode).where(
                VerificationCode.user_id == new_user.id
            )
        )
        assert verification_code is not None

        assert mock_mail.call_count == 1
        assert mock_locale.call_count == 1

        recepient = mock_mail.call_args[1]["recepients"][0]
        assert recepient == data.email

    async def test_register_with_dupliacate_email(
        self,
        user_fixture: User,
        http_client: AsyncClient,
    ) -> None:
        response = await http_client.post(
            self.root_url,
            json=Register(
                email=user_fixture.email,
                password="12345678",
                name="test",
                surname="test",
                phone_number="+79643164477",
                document_version="v1",
                accepted=True,
            ).model_dump(),
            headers={"X-Real-Ip": "127.0.0.1"},
        )
        assert response.status_code == 400

        response_data = response.json()
        assert response_data["detail"] == ErrorCodes.EMAIL_ALREADY_EXISTS.value

    async def test_register_wrong_phone_number(
        self,
        http_client: AsyncClient,
    ) -> None:
        response = await http_client.post(
            self.root_url,
            json={
                "email": "new_email@gmail.com",
                "password": "12345678",
                "name": "test",
                "surname": "test",
                "phone_number": "7964316447",
                "ip": "127.0.0.1",
                "document_version": "v1",
                "accepted": True,
            },
        )
        assert response.status_code == 422

        response_data = response.json()
        assert (
            response_data["detail"][0]["msg"]
            == "Value error, Телефон должен быть в формате +79991234567"
        )
