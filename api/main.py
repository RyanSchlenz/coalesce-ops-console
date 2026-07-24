"""Coalesce Ops Console - backend.

A thin FastAPI service that exposes a single endpoint, GET /runs, which returns
recent Coalesce job runs as clean, normalized JSON.

Design notes
------------
- The Coalesce access token lives here, server-side, and never touches the
  browser; the React app talks only to this service.
- USE_MOCK=true makes the whole app run end to end with zero credentials.
  Set it to false once a real token is configured in .env.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx
import truststore
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

# Trust the OS certificate store so outbound TLS works behind corporate
# HTTPS-inspection proxies, which re-sign traffic with a company root CA
# that Python's bundled CA list does not know about.
truststore.inject_into_ssl()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("coalesce-ops-console")


class Settings(BaseSettings):
    """Runtime configuration, loaded from environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    use_mock: bool = True
    coalesce_base_url: str = "https://your-org.app.coalescesoftware.io"
    coalesce_token: str = ""
    coalesce_environment_id: str = "1"


settings = Settings()


class Run(BaseModel):
    """A single Coalesce job run, normalized to a stable shape for the UI.

    This is the contract the frontend depends on. Keep it stable even if the
    upstream Coalesce response changes: adapt inside _normalize_run instead.
    """

    id: str
    name: str
    status: str
    environment: str
    started_at: str | None = None
    duration_seconds: float | None = None


app = FastAPI(title="Coalesce Ops Console", version="0.1.0")

# Belt-and-suspenders: the Vite dev server also proxies /api to this service,
# but allowing the dev origin means a direct fetch works too.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check. Returns mock/live mode so you can eyeball config."""
    return {"status": "ok", "mode": "mock" if settings.use_mock else "live"}


@app.get("/runs", response_model=list[Run])
async def get_runs() -> list[Run]:
    """Return recent runs, newest first.

    In mock mode this returns canned data. In live mode it calls the Coalesce
    REST API, then normalizes each record via _normalize_run.
    """
    if settings.use_mock:
        return _mock_runs()

    if not settings.coalesce_token:
        raise HTTPException(
            status_code=500,
            detail="COALESCE_TOKEN is empty. Set it in api/.env or keep USE_MOCK=true.",
        )

    try:
        raw_runs = await _fetch_coalesce_runs()
    except httpx.HTTPStatusError as exc:
        logger.error("Coalesce API returned %s: %s", exc.response.status_code, exc.response.text)
        raise HTTPException(status_code=502, detail="Coalesce API error. See server logs.") from exc
    except httpx.HTTPError as exc:
        logger.error("Could not reach Coalesce API: %s", exc)
        raise HTTPException(status_code=502, detail="Could not reach Coalesce API.") from exc

    return [_normalize_run(r) for r in raw_runs]


async def _fetch_coalesce_runs() -> list[dict[str, Any]]:
    """Call the Coalesce REST API and return the raw list of run records.

    The endpoint path, query params, and response parsing here are the one
    spot coupled to the exact Coalesce API surface; _normalize_run keeps the
    rest of the app insulated from its field names.
    """
    url = f"{settings.coalesce_base_url}/api/v1/runs"
    headers = {"Authorization": f"Bearer {settings.coalesce_token}"}
    params = {"orderBy": "runStartTime", "orderByDirection": "desc", "limit": "25"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        body = response.json()

    # Accept both a bare list and a list wrapped under a common key so a minor
    # response-shape difference does not crash the app.
    if isinstance(body, dict):
        for key in ("data", "runs", "results", "items"):
            if isinstance(body.get(key), list):
                return body[key]
        return []
    if isinstance(body, list):
        return body
    return []


def _normalize_run(raw: dict[str, Any]) -> Run:
    """Map one raw Coalesce run record onto the stable Run shape.

    Run objects carry no name field, so runs are identified by id. The API
    returns no duration either; it is computed from runStartTime/runEndTime
    when both are present (a still-running job has no end time yet).
    """
    run_id = str(_first(raw, "id", "runCounter", default="unknown"))
    return Run(
        id=run_id,
        name=str(_first(raw, "name", "runType", default=f"run {run_id}")),
        status=str(_first(raw, "status", "runStatus", default="unknown")).lower(),
        environment=str(_first(raw, "environmentName", "environmentID", default=settings.coalesce_environment_id)),
        started_at=_opt_str(_first(raw, "runStartTime", "startTime", default=None)),
        duration_seconds=_duration_seconds(raw),
    )


def _duration_seconds(raw: dict[str, Any]) -> float | None:
    """Compute run duration from timestamps; None while still running."""
    start = _first(raw, "runStartTime", "startTime", default=None)
    end = _first(raw, "runEndTime", "endTime", default=None)
    if start is None or end is None:
        return None
    try:
        delta = datetime.fromisoformat(str(end)) - datetime.fromisoformat(str(start))
        return delta.total_seconds()
    except ValueError:
        return None


def _first(raw: dict[str, Any], *keys: str, default: Any) -> Any:
    """Return the first present, non-null value among keys, else default."""
    for key in keys:
        if raw.get(key) is not None:
            return raw[key]
    return default


def _opt_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _mock_runs() -> list[Run]:
    """Canned data so the UI renders before any credentials exist."""
    return [
        Run(id="1042", name="daily_full_load", status="success",
            environment="PROD", started_at="2026-07-21T06:00:11Z", duration_seconds=412.0),
        Run(id="1041", name="hourly_incremental", status="running",
            environment="PROD", started_at="2026-07-21T14:00:03Z", duration_seconds=None),
        Run(id="1040", name="dim_customer_rebuild", status="failed",
            environment="PROD", started_at="2026-07-21T05:32:47Z", duration_seconds=88.0),
        Run(id="1039", name="hourly_incremental", status="success",
            environment="PROD", started_at="2026-07-21T13:00:02Z", duration_seconds=133.0),
        Run(id="1038", name="vault_sat_loads", status="success",
            environment="STAGING", started_at="2026-07-21T12:15:20Z", duration_seconds=201.0),
    ]
