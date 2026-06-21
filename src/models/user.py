import uuid

from sqlalchemy import UUID
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from databases.pg import Base


class User(Base):
    """
    Модель пользователя

    ## Attrs:
       - id: int - идентификатор
       - email: str - электорнная почта пользователя
       - password: str - хэш пароля пользователя
    """

    __tablename__ = "user"
    __table_args__ = (
        UniqueConstraint(
            "email", name="uq_user_email", postgresql_nulls_not_distinct=True
        ),
        UniqueConstraint(
            "phone", name="uq_user_phone", postgresql_nulls_not_distinct=True
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    uid: Mapped[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4())
    email: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    password: Mapped[str]
    phone: Mapped[str] = mapped_column(String, unique=True, nullable=True)
