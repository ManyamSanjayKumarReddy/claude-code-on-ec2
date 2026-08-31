import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from tortoise.contrib.fastapi import RegisterTortoise

from app.api.products import router as products_router
from app.core.config import settings
from app.core.logging import configure_logging, logger
from app.core.tortoise_config import TORTOISE_ORM

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with RegisterTortoise(app, config=TORTOISE_ORM, add_exception_handlers=True):
        yield


app = FastAPI(title="Claude Code on EC2 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)

    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_finished",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response


Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

app.include_router(products_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


@app.get("/hello")
def hello() -> dict[str, str]:
    return {"message": "Hello from FastAPI, served through Nginx on EC2."}
