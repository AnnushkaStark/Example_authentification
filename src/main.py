from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.api.router import api_router as auth_app_router
from src.constants.errors import DomainError
from src.tasks import broker
from src.utils.errors import domain_error_exception_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.startup()
    yield
    await broker.shutdown()


app = FastAPI(
    title="AuthApp",
    openapi_url="/auth/openapi.json",
    docs_url="/auth/docs",
    exception_handlers={DomainError: domain_error_exception_handler},
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://3-doutlet.ru",
        "https://dev.3-doutlet.ru",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_app_router, prefix="/auth")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        reload=True,
        proxy_headers=True,
    )
