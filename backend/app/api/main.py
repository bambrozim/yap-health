from collections.abc import Iterator
from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, init_db
from app.db.models import ImportRun
from app.domain.aggregation import daily_series
from app.domain.metrics import METRICS
from app.domain.service import build_scoreboard, latest_daily_values
from app.rules.evaluation import evaluate_value
from app.rules.insights import trend_insight


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="yap-health", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_session() -> Iterator[Session]:
    with SessionLocal() as s:
        yield s


_From = Query(None, alias="from")
_To = Query(None, alias="to")


@app.get("/api/score")
def get_score(from_: date = _From, to: date = _To,
              session: Session = Depends(get_session)):
    return build_scoreboard(session, from_, to)


@app.get("/api/metrics/{metric}")
def get_metric(metric: str, from_: date = _From, to: date = _To,
               session: Session = Depends(get_session)):
    if metric not in METRICS:
        raise HTTPException(404, "unknown metric")
    series = daily_series(session, metric, from_, to)
    return {"metric": metric, "unit": METRICS[metric].unit,
            "points": [{"date": d.isoformat(), "value": v} for d, v in series]}


@app.get("/api/alerts")
def get_alerts(from_: date = _From, to: date = _To,
               session: Session = Depends(get_session)):
    latest = latest_daily_values(session, list(METRICS.keys()), from_, to)
    out = []
    for metric, value in latest.items():
        ev = evaluate_value(metric, value)
        if ev and ev.status != "green":
            out.append({"metric": metric, "status": ev.status,
                        "message": ev.message, "source": ev.source, "value": value})
    return {"alerts": out}


@app.get("/api/insights")
def get_insights(from_: date = _From, to: date = _To,
                 session: Session = Depends(get_session)):
    out = []
    for metric in ("resting_heart_rate", "hrv_rmssd"):
        series = daily_series(session, metric, from_, to)
        if len(series) < 4:
            continue
        recent, baseline = series[-3:], series[:-3]
        ins = trend_insight(metric, baseline, recent)
        if ins:
            out.append({"metric": ins.metric, "text": ins.text,
                        "severity": ins.severity})
    return {"insights": out}


@app.get("/api/import/status")
def get_import_status(session: Session = Depends(get_session)):
    rows = session.scalars(
        select(ImportRun).order_by(ImportRun.started_at.desc()).limit(10)).all()
    return {"runs": [
        {"filename": r.filename, "source": r.source, "status": r.status,
         "rows_imported": r.rows_imported,
         "started_at": r.started_at.isoformat() if r.started_at else None,
         "error": r.error}
        for r in rows]}
