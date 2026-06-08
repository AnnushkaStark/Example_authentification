from fastapi import APIRouter
from fastapi import status
from fastapi.requests import Request

from src.api.depends.localization import LocalizationServiceDepends

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
async def check_localization(
    request: Request, service: LocalizationServiceDepends
):
    return await service.get_localization(request_headers=request.headers)
