import logging
import time
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.config import Settings, get_settings
from app.db import get_engine

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])

Status = Literal["ok", "error"]


class DatabaseCheck(BaseModel):
    status: Status
    latency_ms: float | None = None


class HealthChecks(BaseModel):
    database: DatabaseCheck


class HealthResponse(BaseModel):
    status: Status
    version: str
    environment: str
    checks: HealthChecks


def check_database(engine: Engine) -> DatabaseCheck:
    started = time.perf_counter()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1")).scalar_one()
    except SQLAlchemyError as exc:
        # Log the type only: driver messages can include host/user details.
        logger.warning("Database health check failed: %s", type(exc).__name__)
        return DatabaseCheck(status="error")
    return DatabaseCheck(status="ok", latency_ms=round((time.perf_counter() - started) * 1000, 2))


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={503: {"model": HealthResponse, "description": "A dependency is unavailable"}},
)
def health(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
    engine: Annotated[Engine, Depends(get_engine)],
) -> HealthResponse:
    db = check_database(engine)
    overall: Status = "ok" if db.status == "ok" else "error"
    if overall != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status=overall,
        version=settings.app_version,
        environment=settings.app_env,
        checks=HealthChecks(database=db),
    )
