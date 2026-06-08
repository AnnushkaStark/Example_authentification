from contextlib import asynccontextmanager

import sentry_sdk
import uvicorn
from dddshared.logger import configure_default_logging
from fastapi import FastAPI
from sentry_sdk import metrics
from starlette.middleware.cors import CORSMiddleware

from src.api.router import api_router as auth_app_router
from src.config.configs import app_settings
from src.config.configs import sentry_settings
from src.constants.errors import DomainError
from src.tasks import broker
from src.utils.errors import domain_error_exception_handler

configure_default_logging(app_settings.log_level)

sentry_sdk.init(
    dsn=sentry_settings.AUTH_SENTRY_DNS,
    send_default_pii=True,
    enable_logs=True,
    traces_sample_rate=1.0,
    profile_session_sample_rate=1.0,
    profile_lifecycle="trace",
)

metrics.count("checkout.failed", 1)
metrics.gauge("queue.depth", 42)


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

# app.add_middleware(
#  MetricsMiddleware,
# service_name=app_settings.SERVICE_NAME,
# version=app_settings.SERVICE_VERSION,
#  excluded_urls=app_settings.EXCLUDED_URLS,
# )
# app.add_middleware(
#   RequestAccessMiddleware,
#  excluded_urls=app_settings.EXCLUDED_URLS,
# )
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

## fmt: off
# (#ObservabilityBuilder(
#   app,
#   service_name=app_settings.SERVICE_NAME,
#  service_version=app_settings.SERVICE_VERSION,
# ).with_otlp(app_settings.OTLP_ENDPOINT)
#   .with_logging()
#  .with_httpx()
#  .with_sqlalchemy(async_engine.sync_engine)
# .with_fastapi(app_settings.EXCLUDED_URLS)
# .done()
##.with_prometheus()
# .with_pyroscope(app_settings.PYROSCOPE_HOST, app_settings.PYROSCOPE_PORT))
# fmt: on

app.include_router(auth_app_router, prefix="/auth")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        reload=True,
        proxy_headers=True,
    )
