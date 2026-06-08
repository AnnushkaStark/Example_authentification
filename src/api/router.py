from fastapi import APIRouter

from src.api.endpoints.auth import router as auth_router
from src.api.endpoints.localization import router as localization_router
from src.api.endpoints.triggered_error import router as trigger_router
from src.api.endpoints.verificarion import router as verification_router

api_router = APIRouter(prefix="/api")


api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(
    verification_router, prefix="/verification", tags=["Verification"]
)
api_router.include_router(
    localization_router, prefix="/localization", tags=["Localization"]
)

api_router.include_router(
    trigger_router, prefix="/triggered_error", tags=["TriggeredError"]
)
