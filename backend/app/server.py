from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.create_tables import create_tables
from app.logging_config import get_logger
from app.api.routes.health import router as health_router
from app.api.routes.review import router as review_router

_logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        create_tables()
    except Exception as exc:
        _logger.warning("DB not reachable at startup (create_tables skipped): %s", exc)
    yield


app = FastAPI(title="Agentic Literature Review", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(review_router)
