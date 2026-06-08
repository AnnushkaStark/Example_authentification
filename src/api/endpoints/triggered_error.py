from fastapi import APIRouter

router = APIRouter()


@router.post(
    "/",
    summary="Sentry triggered error",
)
async def trigger():
    return 1 / 0
