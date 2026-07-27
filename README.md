# Coalesce Ops Console

A small full-stack app for monitoring Coalesce job runs. React frontend, FastAPI
backend, Coalesce REST API.

https://coalesce-ops-console.onrender.com/

The backend holds the Coalesce access token server-side and exposes a single
clean endpoint the frontend consumes. The browser never sees a credential.

## Architecture

```
React (Vite + TS)  ->  FastAPI (httpx)  ->  Coalesce REST API
   /api/runs             GET /runs            recent runs
```

- Token lives only in the backend `.env`. That is the reason the backend exists.
- Ships in mock mode, so it runs end to end with zero credentials.

## Run it

Two terminals.

### Backend

```
cd api
python -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

Check it: http://localhost:8000/runs should return mock runs as JSON.

### Frontend

```
cd web
npm install
npm run dev
```

Open http://localhost:5173. You should see the runs table.

## Going live against real Coalesce

1. In `api/.env`, set `USE_MOCK=false` and fill in `COALESCE_BASE_URL`,
   `COALESCE_TOKEN`, and `COALESCE_ENVIRONMENT_ID`.
2. The Coalesce API call lives in `_fetch_coalesce_runs` and `_normalize_run`
   in `api/main.py`; adjust the endpoint path or field names there if your
   environment differs.

