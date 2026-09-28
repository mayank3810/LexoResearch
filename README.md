# Lexo

Compile fundamental research into a shared world model. Tickers are exposed to that model. The book follows thesis-state. Every transition cites a claim — or is painted as our policy.

The compiled model lives in [`data/fixtures/`](data/fixtures/). There is no PDF parser and no LLM on the decision path.

```text
research → shared world-model → thesis-state over time → position
```

## What you will see

1. **Thesis-state** — the as-of conclusion: BASE, Hold, no position, the one-row FY2028 disagreement.
2. **World graph** — events, factors, exposures. Click a node to a page. Contracts are a derived list.
3. **Workbench** — Simulated World A (17 Nov confirmation) and World B (two hyperscaler capex prints). Both tapes after the memo as-of are fabricated.

The workbench is labeled **SIMULATED — NOT MARKET DATA**. These are divergent futures for testing the model, not forecasts.

## Run

Python 3.13 (see `.venv`).

```bash
# backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend && ../.venv/bin/python -m pytest -q
../.venv/bin/uvicorn app.main:app --reload --port 8000

# frontend (second terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api` to the engine on port 8000.

## Deploy on Vercel

The frontend is a static Vite app. The engine is a Python serverless function at `/api`.

1. Push this repo to GitHub.
2. In Vercel: **Add New Project** → import the repo → root directory **leave as the repo root** (not `frontend`).
3. Vercel reads `vercel.json`. You should not need extra env vars.
4. Deploy. The live URL is `https://<project>.vercel.app`.

Preview deployments work the same way. World state is sent with each request, so serverless instances do not need shared memory.

## Tests that lock the model

- one-of-four does not exit
- two-of-four does
- ambiguous 17 Nov does not move state
- confirmation does, and retires the Neutral-spring override
- `$195` stop ignores a flat book
- kill-switch edges dominate
- a human-observable node does not fire until adjudicated
- identical tapes hash identically

## Out of scope

LangGraph, PDF ingest, live market data, brokers, auth, backtests, ML, native apps, invented conviction numbers, trading on summed factor impacts.

## Layout

```text
data/fixtures/        compiled model
backend/              FastAPI + deterministic engine
frontend/             Vite + React workbench
api/                  Vercel serverless entry
```
