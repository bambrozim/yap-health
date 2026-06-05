# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`yap-health` is a **local-first, offline** personal health dashboard. It ingests data exported
from Health Sync / Health Connect, stores it in a canonical SQLite DB, evaluates it against
guideline-backed targets, and serves per-domain charts + sub-scores + an overall health score.
No data leaves the machine. Implemented domains: **activity**, **cardio**, and **sleep**
(roadmap: nutrition → body). Each domain was added as a vertical slice following the same pattern.

Design + plan live in `docs/superpowers/specs/` and `docs/superpowers/plans/`.

## Commands

### Backend (Python 3.12, run from `backend/`)

**Use `uv` — not system or Homebrew Python.** System Python is 3.9 (too old). Homebrew's
`python@3.12` on this machine has a broken `pyexpat`/`libexpat` link that breaks pip. uv ships
a standalone interpreter that works.

```bash
cd backend
uv venv --python 3.12 .venv
uv pip install -e ".[dev]"

.venv/bin/python -m pytest -q                       # all tests
.venv/bin/python -m pytest tests/test_scoring.py -v # one file
.venv/bin/python -m pytest tests/test_api.py::test_score_endpoint -v  # one test

.venv/bin/python -m app.cli "<folder>"              # bulk-import a snapshot folder (.db/.tcx)
.venv/bin/uvicorn app.api.main:app --port 8000      # run API (auto-creates schema on startup)
```

### Frontend (run from `frontend/`)

```bash
npm install
npm run dev      # http://localhost:5173 (expects backend on :8000)
npm run build    # tsc -b && vite build
npm test         # vitest run
```

The frontend uses a **hardcoded date window** (`from=2026-04-01&to=2026-06-30`) in
`src/lib/api.ts` — the sample data is April–May 2026. Adjust there when working with other data.

## Architecture

Data flows in one direction through the backend, then out via REST to the React SPA:

```
inbox folder → ingestion → canonical SQLite → domain aggregation → rules → FastAPI → React
```

### Ingestion (`app/ingestion/`)

- **Two sources, Health Connect is canonical.** The `.db` SQLite export (`health_connect.py`)
  is the structured source of truth. Health Sync `.tcx` files (`health_sync_workouts.py`) only
  supplement workout summaries. Health Sync CSVs are derived from Health Connect, so they aren't
  re-imported.
- `runner.process_file()` dispatches by file suffix (`.db` → measurements, `.tcx` → workouts).
  `process_inbox()` walks a folder; `watcher.watch()` is the watchdog daemon for live imports.
- **Idempotency** is via `make_dedup_key()` in `base.py` (`base.py`): `source:uuid` when
  available, else `source:sha1(metric|ts|value)`. `persist.py` skips rows whose `dedup_key`
  already exists, so re-importing overlapping exports never double-counts.
- Health Connect quirks handled in `health_connect.py`: heart-rate samples come from
  `heart_rate_record_series_table` (not `heart_rate_record_table`); energy is in calories
  (÷1000 → kcal), distance in meters (÷1000 → km). The export's data range is set by its
  *contents*, not the date in the filename.

### Canonical schema (`app/db/models.py`)

Three tables: `measurements` (long-format scalar time series: `metric, ts, value, unit,
source, dedup_key`), `workouts`, and `import_runs` (audit). All metrics share the
`measurements` table keyed by a string `metric` id.

### Metrics & domains (`app/domain/metrics.py`)

The `METRICS` dict is the **single source of truth** for which metric ids exist, their domain
(`activity` | `cardio` | `sleep`), daily aggregation (`sum`/`mean`/`min`), and unit. `aggregation.daily_series()`
buckets measurements by UTC date using each metric's agg rule.

### Rules engine (`app/rules/`) — deterministic, no LLM

- `targets.py`: `TARGETS` maps a metric to a guideline target with green/yellow bands and a
  **cited source string** (OMS, AHA, etc.). Only some metrics have targets; others are
  chart-only.
- `evaluation.py`: `evaluate_value(metric, value)` → green/yellow/red status (or `None` if no
  target). Drives alerts.
- `scoring.py`: status → points (green 100, yellow 60, red 20); `domain_score()` averages a
  domain's scored metrics; `overall_score()` is the weighted mean of domains.
- `insights.py`: `trend_insight()` flags RHR rises / HRV drops vs a baseline window.

### Service + API (`app/domain/service.py`, `app/api/main.py`)

`service.build_scoreboard()` assembles overall + domain scores from the latest daily values.
FastAPI endpoints: `/api/score`, `/api/metrics/{metric}`, `/api/alerts`, `/api/insights`,
`/api/import/status`. All take `?from=&to=` date params — note `from` is a reserved word, so the
handlers use `Query(alias="from")` with a `from_` parameter.

### Frontend (`frontend/src/`)

Vite + React + TanStack Query + Recharts + Tailwind. No router: `App.tsx` switches between
`Home` and `Domain` via local state. `Home` shows score cards (clicking a domain opens its
charts) + alerts/insights feed. UI primitives in `components/ui/` are hand-written shadcn-style
components (the shadcn CLI is not used). The `@/` alias maps to `src/`.

## Conventions

- **TDD throughout.** Every backend module has a paired `tests/test_*.py`; write the failing
  test first. Commits are small and per-task.
- **In-memory SQLite tests need `StaticPool`** (see `test_api.py`) so the seeded data is visible
  to the request-scoped session — a plain `sqlite://` engine gives each connection its own DB.
- **Adding a metric:** add it to `METRICS`, map its source table/column in `health_connect.py`'s
  `_SCALAR_MAP`, optionally add a `TARGETS` entry, and surface it in the frontend's
  `DOMAIN_METRICS` (`pages/Domain.tsx`).
- **Adding a domain:** add metrics with the new domain tag, add it to `service.DOMAINS` and
  `scoring.DOMAIN_WEIGHTS`, and add a route + label in the frontend.
- This is health software: keep the rules engine deterministic and source-cited; preserve the
  "not medical advice" disclaimer in the UI.
