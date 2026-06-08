from collections.abc import AsyncGenerator
from collections.abc import Callable
from datetime import UTC
from datetime import datetime
from datetime import timedelta

import pytest_asyncio
from dddshared.models.auth import UserSession
from dddshared.models.auth import VerificationCode
from dddshared.models.enums import DeviceType
from dddshared.models.enums import Locale
from dddshared.models.user import User
from dddshared.utils.query import queries
from httpx import ASGITransport
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from src.databases.pg import _add_to_session
from src.databases.pg import async_engine
from src.main import app
from src.security.password import hash_password
from src.security.security import TokenSubject
from src.security.security import access_security


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession]:
    session = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session() as s:
        async with async_engine.begin() as conn:
            for q in queries:
                await conn.execute(text(q))
        yield s

    async with async_engine.begin() as conn:
        await conn.execute(
            text("""
            TRUNCATE 
                user_db.user_policy_agreement,
                user_db."user",        
                auth_db.user_sessions, 
                auth_db.verification_code, 
                auth_db.token_blacklist 
            RESTART IDENTITY CASCADE;
        """)
        )
        await conn.commit()

    await async_engine.dispose()


@pytest_asyncio.fixture
async def user_fixture(
    async_session: AsyncSession,
) -> User:
    return await _add_to_session(
        session=async_session,
        obj=User(
            email="psk221219@gmail.com",
            password=hash_password("12345678"),
            country=Locale.RU,
            is_verified=True,
        ),
    )


@pytest_asyncio.fixture
async def another_user_fixture(
    async_session: AsyncSession,
) -> User:
    return await _add_to_session(
        session=async_session,
        obj=User(
            email="psk221230@gmail.com",
            password=hash_password("12345678"),
            country=Locale.RU,
            is_verified=False,
        ),
    )


@pytest_asyncio.fixture
async def verification_code_fixture(
    async_session: AsyncSession, another_user_fixture: User
) -> VerificationCode:
    expired = datetime.now().replace(tzinfo=None) + timedelta(minutes=10)
    return await _add_to_session(
        session=async_session,
        obj=VerificationCode(
            code="1234",
            expired_at=expired,
            user_id=another_user_fixture.id,
        ),
    )


@pytest_asyncio.fixture
async def expired_code_fixture(
    async_session: AsyncSession, another_user_fixture: User
) -> VerificationCode:
    expired = datetime.now().replace(tzinfo=None) - timedelta(minutes=12)
    return await _add_to_session(
        session=async_session,
        obj=VerificationCode(
            code="1234",
            expired_at=expired,
            user_id=another_user_fixture.id,
        ),
    )


@pytest_asyncio.fixture
async def unverify_user_fixture(
    async_session: AsyncSession,
) -> User:
    return await _add_to_session(
        session=async_session,
        obj=User(
            email="psk221220@gmail.com",
            password=hash_password("12345678"),
            country=Locale.RU,
            is_verified=False,
        ),
    )


@pytest_asyncio.fixture
async def deactivated_user_fixture(
    async_session: AsyncSession,
) -> User:
    return await _add_to_session(
        session=async_session,
        obj=User(
            email="psk221221@gmail.com",
            password=hash_password("12345678"),
            country=Locale.RU,
            is_verified=True,
            is_active=False,
        ),
    )


@pytest_asyncio.fixture
async def user_session_fixture(
    user_fixture: User, async_session: AsyncSession
) -> UserSession:
    return await _add_to_session(
        session=async_session,
        obj=UserSession(
            device_type=DeviceType.UNKNOWN,
            user_id=user_fixture.id,
            expired_at=datetime.now(UTC) + timedelta(hours=10),
        ),
    )


@pytest_asyncio.fixture
async def another_user_session_fixture(
    another_user_fixture: User, async_session: AsyncSession
) -> UserSession:
    return await _add_to_session(
        session=async_session,
        obj=UserSession(
            device_type=DeviceType.UNKNOWN,
            user_id=another_user_fixture.id,
            expired_at=datetime.now(UTC) + timedelta(hours=10),
        ),
    )


@pytest_asyncio.fixture
async def http_client(
    async_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://0.0.0.0:8000"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def get_auth_headers() -> Callable:
    async def _get_auth_headers(
        user_fixture: User, user_session_fixture: UserSession
    ):
        subject = TokenSubject(
            uid=str(user_fixture.uid),
            is_verified=user_fixture.is_verified,
            country=user_fixture.country,
            jti=str(user_session_fixture.uid),
        )
        access_token = access_security.create_access_token(subject=subject)
        headers = {"Authorization": f"Bearer {access_token}"}
        return headers

    return _get_auth_headers
