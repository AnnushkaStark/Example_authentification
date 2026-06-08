import re
from typing import Annotated

from pydantic import AfterValidator
from pydantic import BaseModel


def phone_validate(phone: str | None) -> str | None:
    if phone in (None, ""):
        return phone

    if not re.match(r"^\+\d{11}$", phone):
        raise ValueError("Телефон должен быть в формате +79991234567")

    return phone


PhoneString = Annotated[str | None, AfterValidator(phone_validate)]


class CartBase(BaseModel):
    user_id: int
