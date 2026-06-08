from fastapi.requests import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.constants.errors import ERROR_STATUS_MAP
from src.constants.errors import DomainError


async def domain_error_exception_handler(request: Request, exc: DomainError):
    status_code = ERROR_STATUS_MAP.get(exc.code, 500)

    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.code.value},
    )


class BaseError(BaseModel):
    detail: str


def create_response_schema(description: str):
    return dict(
        model=BaseError,
        description=description,
    )


def _format_description(codes) -> str:
    return "".join(f"<br />{code.value}" for code in codes)[len("<br />") :]


def errs(**_codes):
    ret = dict()
    processed = set()

    for status_codes, codes in _codes.items():
        if not hasattr(codes, "__iter__"):
            codes = (codes,)

        if set(codes) & processed:
            raise RuntimeError("Error codes duplicated")

        processed |= set(codes)

        status_code = int(status_codes.strip("e"))

        ret[status_code] = dict(
            model=BaseError,
            description=_format_description(codes),
        )
    return ret
