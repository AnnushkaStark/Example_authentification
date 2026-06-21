from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from databases.pg import Base


class TokenBlacklist(Base):
    """
    Модель блэклиста токенов

    - jti: str - jti
    - created_at: datetime - дата и время создания сессии пользователя
    """

    __tablename__ = "token_blacklist"

    jti: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        index=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
