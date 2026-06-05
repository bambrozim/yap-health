# yap-health v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the v1 vertical slice of a local-first personal health dashboard covering the **Atividade** and **Cardíaco** domains: automatic ingestion → canonical SQLite → deterministic rules/score → FastAPI → React dashboard.

**Architecture:** A Python/FastAPI backend watches a synced inbox folder, imports health data (Health Connect SQLite export as canonical source, Health Sync FIT/TCX as workout supplement) into a deduplicated canonical SQLite schema, computes daily aggregates, evaluates them against guideline-backed targets to produce alerts/insights, and rolls metric adherence into per-domain sub-scores and an overall health score. A React (Vite + shadcn/ui + Recharts) frontend consumes the REST API.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2, pytest, watchdog, fitparse, tcxreader; React + TypeScript + Vite, shadcn/ui, Recharts, TanStack Query, axios; vitest.

---

## Shared contracts (used across tasks — keep names consistent)

**Canonical metric identifiers (strings):**
- Cardíaco: `heart_rate`, `hrv_rmssd`, `resting_heart_rate`, `spo2`
- Atividade: `steps`, `active_calories`, `total_calories`, `distance_km`

**Domains:** `cardio`, `activity` (v1). Future: `sleep`, `nutrition`, `body`.

**Aggregation rule per metric** (`domain/metrics.py`):
| metric | daily agg | unit |
|---|---|---|
| steps | sum | count |
| active_calories | sum | kcal |
| total_calories | sum | kcal |
| distance_km | sum | km |
| heart_rate | mean | bpm |
| hrv_rmssd | mean | ms |
| resting_heart_rate | min | bpm |
| spo2 | mean | % |

**Status enum:** `green` | `yellow` | `red`.

**Guideline targets (v1, cited):**
- `steps`: daily_min 8000 (heuristic; yellow 5000–8000, red <5000). Source: WHO physical-activity rationale + common step literature.
- `active_calories`: informational (no hard target in v1) — charted, not scored as pass/fail. (Activity score driven by steps + weekly active minutes proxy.)
- `weekly_active_minutes` (derived from workouts + activity_intensity): weekly_min 150 (moderate). Source: WHO 2020 (150–300 min/week). https://www.who.int/europe/publications/i/item/9789240014886
- `resting_heart_rate`: daily_range 60–100 bpm (green inside; yellow 50–60 or 100–110; red <50 or >110). Source: American Heart Association.
- `spo2`: daily_min 95% (green ≥95; yellow 92–95; red <92). Source: clinical norm (Mayo/AHA).
- `hrv_rmssd`: no fixed cutoff — trend insight only vs 4-week individual baseline.
- `heart_rate`: charted only (no pass/fail target).

---

## Phase 0 — Scaffolding

### Task 0.1: Backend project skeleton

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/tests/__init__.py`
- Create: `.gitignore`

- [ ] **Step 1: Create `.gitignore`** (protect personal data + build artifacts)

```gitignore
# Python
__pycache__/
*.pyc
.venv/
.pytest_cache/
# App data (personal health data — never commit)
backend/data/
data/
references/data/
# Frontend
frontend/node_modules/
frontend/dist/
# OS
.DS_Store
```

- [ ] **Step 2: Create `backend/pyproject.toml`**

```toml
[project]
name = "yap-health"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.30",
  "sqlalchemy>=2.0",
  "pydantic>=2.7",
  "pydantic-settings>=2.3",
  "watchdog>=4.0",
  "fitparse>=1.2",
  "tcxreader>=0.4",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "httpx>=0.27"]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

- [ ] **Step 3: Create `backend/app/config.py`**

```python
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="YAP_")
    data_dir: Path = Path(__file__).resolve().parents[1] / "data"
    db_path: Path | None = None
    inbox_dir: Path | None = None

    def model_post_init(self, __context) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if self.db_path is None:
            self.db_path = self.data_dir / "app.db"
        if self.inbox_dir is None:
            self.inbox_dir = self.data_dir / "inbox"
        self.inbox_dir.mkdir(parents=True, exist_ok=True)

settings = Settings()
```

- [ ] **Step 4: Create empty `backend/app/__init__.py` and `backend/tests/__init__.py`**

```python
# (empty file)
```

- [ ] **Step 5: Install and verify**

Run: `cd backend && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"`
Expected: installs without error.
Run: `python -c "from app.config import settings; print(settings.db_path)"`
Expected: prints a path ending in `data/app.db`.

- [ ] **Step 6: Commit**

```bash
git add .gitignore backend/pyproject.toml backend/app/__init__.py backend/app/config.py backend/tests/__init__.py
git commit -m "chore: scaffold backend project"
```

---

## Phase 1 — Canonical schema

### Task 1.1: SQLAlchemy models + database session

**Files:**
- Create: `backend/app/db/__init__.py`
- Create: `backend/app/db/database.py`
- Create: `backend/app/db/models.py`
- Test: `backend/tests/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_models.py
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.models import Base, Measurement

def test_measurement_roundtrip():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        s.add(Measurement(
            metric="steps", ts=datetime(2026, 6, 4, tzinfo=timezone.utc),
            value=43.0, unit="count", source="health_connect",
            dedup_key="hc:abc"))
        s.commit()
        row = s.query(Measurement).one()
        assert row.metric == "steps"
        assert row.value == 43.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: app.db.models`.

- [ ] **Step 3: Write `backend/app/db/models.py`**

```python
from datetime import datetime
from sqlalchemy import String, Float, DateTime, Integer, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Measurement(Base):
    __tablename__ = "measurements"
    __table_args__ = (UniqueConstraint("dedup_key", name="uq_measurement_dedup"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    metric: Mapped[str] = mapped_column(String, index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    dedup_key: Mapped[str] = mapped_column(String)

class Workout(Base):
    __tablename__ = "workouts"
    __table_args__ = (UniqueConstraint("dedup_key", name="uq_workout_dedup"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String)
    start_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_s: Mapped[int] = mapped_column(Integer)
    distance_km: Mapped[float] = mapped_column(Float, default=0.0)
    calories: Mapped[float] = mapped_column(Float, default=0.0)
    source: Mapped[str] = mapped_column(String)
    dedup_key: Mapped[str] = mapped_column(String)

class ImportRun(Base):
    __tablename__ = "import_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    rows_imported: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    error: Mapped[str] = mapped_column(String, default="")
```

- [ ] **Step 4: Write `backend/app/db/database.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.db.models import Base

engine = create_engine(f"sqlite:///{settings.db_path}")
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def init_db() -> None:
    Base.metadata.create_all(engine)
```

- [ ] **Step 5: Create empty `backend/app/db/__init__.py`, run test**

Run: `cd backend && pytest tests/test_models.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/db backend/tests/test_models.py
git commit -m "feat: add canonical SQLAlchemy schema"
```

---

## Phase 2 — Ingestion

### Task 2.1: Importer base + dedup helper

**Files:**
- Create: `backend/app/ingestion/__init__.py`
- Create: `backend/app/ingestion/base.py`
- Test: `backend/tests/test_ingestion_base.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_ingestion_base.py
from datetime import datetime, timezone
from app.ingestion.base import make_dedup_key, ParsedMeasurement

def test_dedup_key_prefers_source_uuid():
    assert make_dedup_key("steps", datetime(2026,6,4,tzinfo=timezone.utc),
                           43.0, "hc", "uuid-1") == "hc:uuid-1"

def test_dedup_key_falls_back_to_hash():
    k = make_dedup_key("steps", datetime(2026,6,4,tzinfo=timezone.utc),
                       43.0, "csv", None)
    assert k.startswith("csv:") and len(k) > 10
    # deterministic
    k2 = make_dedup_key("steps", datetime(2026,6,4,tzinfo=timezone.utc),
                        43.0, "csv", None)
    assert k == k2

def test_parsed_measurement_holds_fields():
    p = ParsedMeasurement("spo2", datetime(2026,6,4,tzinfo=timezone.utc), 96.0, "%")
    assert p.metric == "spo2" and p.unit == "%"
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && pytest tests/test_ingestion_base.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `backend/app/ingestion/base.py`**

```python
import hashlib
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ParsedMeasurement:
    metric: str
    ts: datetime
    value: float
    unit: str

@dataclass
class ParsedWorkout:
    type: str
    start_ts: datetime
    end_ts: datetime
    duration_s: int
    distance_km: float
    calories: float
    source_uuid: str | None = None

def make_dedup_key(metric: str, ts: datetime, value: float,
                   source: str, source_uuid: str | None) -> str:
    if source_uuid:
        return f"{source}:{source_uuid}"
    raw = f"{metric}|{ts.isoformat()}|{value}"
    digest = hashlib.sha1(raw.encode()).hexdigest()[:16]
    return f"{source}:{digest}"
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && pytest tests/test_ingestion_base.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/ingestion/__init__.py backend/app/ingestion/base.py backend/tests/test_ingestion_base.py
git commit -m "feat: ingestion base types and dedup key"
```

### Task 2.2: Health Connect SQLite importer (primary source)

Maps the relevant `*_record_table` tables from the Health Connect export to `ParsedMeasurement`s. Health Connect stores time as epoch millis (`*_time`/`time`) and `zone_offset` (seconds). For v1 metrics:

| Table | metric | value column | agg-time column | unit |
|---|---|---|---|---|
| steps_record_table | steps | count | start_time | count |
| active_calories_burned_record_table | active_calories | energy (cal→kcal) | start_time | kcal |
| total_calories_burned_record_table | total_calories | energy | start_time | kcal |
| distance_record_table | distance_km | distance (m→km) | start_time | km |
| heart_rate_record_series_table / heart_rate_record_table | heart_rate | beats_per_minute | epoch_millis/time | bpm |
| heart_rate_variability_rmssd_record_table | hrv_rmssd | heart_rate_variability_millis | time | ms |
| resting_heart_rate_record_table | resting_heart_rate | beats_per_minute | time | bpm |
| oxygen_saturation_record_table | spo2 | percentage | time | % |

> During implementation, confirm exact column names with `sqlite3 <export.db> ".schema <table>"`. Energy units in Health Connect are stored in calories (divide by 1000 for kcal); distance in meters.

**Files:**
- Create: `backend/app/ingestion/health_connect.py`
- Test: `backend/tests/test_health_connect_importer.py`
- Fixture: `backend/tests/fixtures/make_hc_fixture.py`

- [ ] **Step 1: Create a tiny fixture DB generator**

```python
# backend/tests/fixtures/make_hc_fixture.py
import sqlite3
from pathlib import Path

def build(path: Path) -> Path:
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE steps_record_table (
            uuid TEXT, start_time INTEGER, start_zone_offset INTEGER, count INTEGER);
        INSERT INTO steps_record_table VALUES
            ('s1', 1749000000000, -10800, 43),
            ('s2', 1749000600000, -10800, 17);
        CREATE TABLE oxygen_saturation_record_table (
            uuid TEXT, time INTEGER, zone_offset INTEGER, percentage REAL);
        INSERT INTO oxygen_saturation_record_table VALUES
            ('o1', 1749000000000, -10800, 96.0);
        """
    )
    con.commit(); con.close()
    return path
```

- [ ] **Step 2: Write the failing test**

```python
# backend/tests/test_health_connect_importer.py
from pathlib import Path
from app.ingestion.health_connect import HealthConnectSqliteImporter
from tests.fixtures.make_hc_fixture import build

def test_parses_steps_and_spo2(tmp_path):
    db = build(tmp_path / "export.db")
    importer = HealthConnectSqliteImporter()
    parsed = list(importer.parse(db))
    metrics = {p.metric for p in parsed}
    assert "steps" in metrics and "spo2" in metrics
    steps = [p for p in parsed if p.metric == "steps"]
    assert len(steps) == 2
    assert steps[0].value == 43.0 and steps[0].unit == "count"
    spo2 = [p for p in parsed if p.metric == "spo2"][0]
    assert spo2.value == 96.0
```

- [ ] **Step 3: Run to verify it fails**

Run: `cd backend && pytest tests/test_health_connect_importer.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 4: Write `backend/app/ingestion/health_connect.py`**

```python
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from app.ingestion.base import ParsedMeasurement

SOURCE = "health_connect"

# (table, metric, value_col, time_col, transform, unit)
_SCALAR_MAP = [
    ("steps_record_table", "steps", "count", "start_time", lambda v: float(v), "count"),
    ("active_calories_burned_record_table", "active_calories", "energy", "start_time", lambda v: float(v) / 1000.0, "kcal"),
    ("total_calories_burned_record_table", "total_calories", "energy", "start_time", lambda v: float(v) / 1000.0, "kcal"),
    ("distance_record_table", "distance_km", "distance", "start_time", lambda v: float(v) / 1000.0, "km"),
    ("heart_rate_variability_rmssd_record_table", "hrv_rmssd", "heart_rate_variability_millis", "time", lambda v: float(v), "ms"),
    ("resting_heart_rate_record_table", "resting_heart_rate", "beats_per_minute", "time", lambda v: float(v), "bpm"),
    ("oxygen_saturation_record_table", "spo2", "percentage", "time", lambda v: float(v), "%"),
]

def _table_exists(con: sqlite3.Connection, name: str) -> bool:
    cur = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None

def _columns(con: sqlite3.Connection, table: str) -> set[str]:
    return {r[1] for r in con.execute(f"PRAGMA table_info({table})")}

class HealthConnectSqliteImporter:
    source = SOURCE

    def matches(self, path: Path) -> bool:
        return path.suffix == ".db"

    def parse(self, path: Path) -> Iterator[ParsedMeasurement]:
        con = sqlite3.connect(path)
        try:
            for table, metric, vcol, tcol, fn, unit in _SCALAR_MAP:
                if not _table_exists(con, table):
                    continue
                cols = _columns(con, table)
                if vcol not in cols or tcol not in cols:
                    continue
                for value, millis in con.execute(
                        f"SELECT {vcol}, {tcol} FROM {table} WHERE {vcol} IS NOT NULL"):
                    ts = datetime.fromtimestamp(millis / 1000.0, tz=timezone.utc)
                    yield ParsedMeasurement(metric, ts, fn(value), unit)
            # heart_rate samples live in a series table in real exports;
            # try the flat table first, fall back gracefully.
            if _table_exists(con, "heart_rate_record_table"):
                hr_cols = _columns(con, "heart_rate_record_table")
                if {"beats_per_minute", "time"} <= hr_cols:
                    for bpm, millis in con.execute(
                            "SELECT beats_per_minute, time FROM heart_rate_record_table"):
                        ts = datetime.fromtimestamp(millis / 1000.0, tz=timezone.utc)
                        yield ParsedMeasurement("heart_rate", ts, float(bpm), "bpm")
        finally:
            con.close()
```

- [ ] **Step 5: Run to verify it passes**

Run: `cd backend && pytest tests/test_health_connect_importer.py -v`
Expected: PASS.

- [ ] **Step 6: Validate against the real export (manual sanity check)**

Run: `cd backend && python -c "from app.ingestion.health_connect import HealthConnectSqliteImporter as H; from pathlib import Path; p=list(H().parse(Path('../references/data/health_data/Clue Woman Health/health_connect_export.db'))); from collections import Counter; print(Counter(x.metric for x in p))"`
Expected: prints a Counter with `steps`, `spo2`, `heart_rate`, `total_calories`, etc. and non-zero counts. If a metric is missing, inspect that table's real column names and adjust `_SCALAR_MAP`.

- [ ] **Step 7: Commit**

```bash
git add backend/app/ingestion/health_connect.py backend/tests/test_health_connect_importer.py backend/tests/fixtures/make_hc_fixture.py
git commit -m "feat: Health Connect SQLite importer"
```

### Task 2.3: Health Sync workout importers (FIT + TCX)

Supplements Health Connect with workout detail. v1 only needs the workout summary (type, start/end, duration, distance, calories) for the Atividade domain.

**Files:**
- Create: `backend/app/ingestion/health_sync_workouts.py`
- Test: `backend/tests/test_workout_importer.py`

- [ ] **Step 1: Write the failing test (TCX is plain XML — easy to fixture)**

```python
# backend/tests/test_workout_importer.py
from app.ingestion.health_sync_workouts import TcxWorkoutImporter

TCX = """<?xml version="1.0"?>
<TrainingCenterDatabase><Activities><Activity Sport="Other">
<Id>2026-06-04T08:12:55Z</Id>
<Lap StartTime="2026-06-04T08:12:55Z">
<TotalTimeSeconds>3439</TotalTimeSeconds>
<DistanceMeters>0</DistanceMeters>
<Calories>250</Calories>
</Lap></Activity></Activities></TrainingCenterDatabase>"""

def test_tcx_parses_workout(tmp_path):
    f = tmp_path / "w.tcx"; f.write_text(TCX)
    w = TcxWorkoutImporter().parse(f)
    assert w.duration_s == 3439
    assert w.calories == 250
    assert w.distance_km == 0.0
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && pytest tests/test_workout_importer.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `backend/app/ingestion/health_sync_workouts.py`**

```python
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path
from app.ingestion.base import ParsedWorkout

SOURCE = "health_sync"
_NS = {"t": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}

def _parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)

class TcxWorkoutImporter:
    source = SOURCE

    def matches(self, path: Path) -> bool:
        return path.suffix == ".tcx"

    def parse(self, path: Path) -> ParsedWorkout:
        root = ET.parse(path).getroot()
        # handle namespaced and non-namespaced documents
        def find(el, tag):
            r = el.find(f"t:{tag}", _NS)
            return r if r is not None else el.find(tag)
        def findall(el, tag):
            r = el.findall(f".//t:{tag}", _NS)
            return r if r else el.findall(f".//{tag}")

        act = findall(root, "Activity")[0]
        sport = act.get("Sport", "unknown")
        start = _parse_iso(findall(act, "Id")[0].text)
        total = sum(float(findall(act, "TotalTimeSeconds")[i].text)
                    for i in range(len(findall(act, "TotalTimeSeconds"))))
        dist_m = sum(float(e.text) for e in findall(act, "DistanceMeters"))
        cals = sum(float(e.text) for e in findall(act, "Calories"))
        return ParsedWorkout(
            type=sport, start_ts=start,
            end_ts=start + timedelta(seconds=int(total)),
            duration_s=int(total), distance_km=dist_m / 1000.0, calories=cals,
            source_uuid=f"tcx:{start.isoformat()}")
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && pytest tests/test_workout_importer.py -v`
Expected: PASS.

- [ ] **Step 5: Validate against the real TCX (manual)**

Run: `cd backend && python -c "from app.ingestion.health_sync_workouts import TcxWorkoutImporter as T; from pathlib import Path; import glob; f=glob.glob('../references/data/health_data/**/*.tcx', recursive=True)[0]; print(T().parse(Path(f)))"`
Expected: prints a ParsedWorkout with duration_s ≈ 3439.

> FIT parsing (richer, optional in v1): note for a follow-up task using `fitparse`. Health Sync provides both `.tcx` and `.fit` for the same workout; TCX summary is sufficient for v1 scoring. Skip `.fit` if a matching `.tcx` exists (dedup by start time).

- [ ] **Step 6: Commit**

```bash
git add backend/app/ingestion/health_sync_workouts.py backend/tests/test_workout_importer.py
git commit -m "feat: TCX workout importer"
```

### Task 2.4: Persister — idempotent upsert into canonical DB

**Files:**
- Create: `backend/app/ingestion/persist.py`
- Test: `backend/tests/test_persist.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_persist.py
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.models import Base, Measurement
from app.ingestion.base import ParsedMeasurement
from app.ingestion.persist import persist_measurements

def _session():
    eng = create_engine("sqlite://"); Base.metadata.create_all(eng)
    return Session(eng)

def test_persist_is_idempotent():
    s = _session()
    items = [ParsedMeasurement("steps", datetime(2026,6,4,tzinfo=timezone.utc), 43.0, "count")]
    n1 = persist_measurements(s, items, source="csv")
    n2 = persist_measurements(s, items, source="csv")  # same data again
    assert n1 == 1
    assert n2 == 0  # deduped
    assert s.query(Measurement).count() == 1
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && pytest tests/test_persist.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `backend/app/ingestion/persist.py`**

```python
from collections.abc import Iterable
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import Measurement, Workout
from app.ingestion.base import ParsedMeasurement, ParsedWorkout, make_dedup_key

def persist_measurements(session: Session, items: Iterable[ParsedMeasurement],
                         source: str, source_uuid: str | None = None) -> int:
    inserted = 0
    for it in items:
        key = make_dedup_key(it.metric, it.ts, it.value, source, source_uuid)
        exists = session.scalar(select(Measurement.id).where(Measurement.dedup_key == key))
        if exists:
            continue
        session.add(Measurement(metric=it.metric, ts=it.ts, value=it.value,
                                unit=it.unit, source=source, dedup_key=key))
        inserted += 1
    session.commit()
    return inserted

def persist_workouts(session: Session, items: Iterable[ParsedWorkout], source: str) -> int:
    inserted = 0
    for w in items:
        key = make_dedup_key("workout", w.start_ts, w.duration_s, source, w.source_uuid)
        if session.scalar(select(Workout.id).where(Workout.dedup_key == key)):
            continue
        session.add(Workout(type=w.type, start_ts=w.start_ts, end_ts=w.end_ts,
                            duration_s=w.duration_s, distance_km=w.distance_km,
                            calories=w.calories, source=source, dedup_key=key))
        inserted += 1
    session.commit()
    return inserted
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && pytest tests/test_persist.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/ingestion/persist.py backend/tests/test_persist.py
git commit -m "feat: idempotent persistence of measurements and workouts"
```

### Task 2.5: File router + inbox runner + watcher

**Files:**
- Create: `backend/app/ingestion/runner.py`
- Create: `backend/app/ingestion/watcher.py`
- Test: `backend/tests/test_runner.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_runner.py
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.models import Base, Measurement
from app.ingestion.runner import process_file
from tests.fixtures.make_hc_fixture import build

def test_process_db_file_populates_measurements(tmp_path):
    eng = create_engine("sqlite://"); Base.metadata.create_all(eng)
    db = build(tmp_path / "export.db")
    with Session(eng) as s:
        run = process_file(s, db)
        assert run.status == "ok"
        assert run.rows_imported > 0
        assert s.query(Measurement).filter_by(metric="steps").count() == 2
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && pytest tests/test_runner.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `backend/app/ingestion/runner.py`**

```python
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.models import ImportRun
from app.ingestion.health_connect import HealthConnectSqliteImporter
from app.ingestion.health_sync_workouts import TcxWorkoutImporter
from app.ingestion.persist import persist_measurements, persist_workouts

def process_file(session: Session, path: Path) -> ImportRun:
    run = ImportRun(filename=path.name, source="", status="running",
                    started_at=datetime.now(timezone.utc))
    try:
        if path.suffix == ".db":
            imp = HealthConnectSqliteImporter()
            run.source = imp.source
            n = persist_measurements(session, imp.parse(path), source=imp.source)
            run.rows_imported = n
        elif path.suffix == ".tcx":
            imp = TcxWorkoutImporter()
            run.source = imp.source
            n = persist_workouts(session, [imp.parse(path)], source=imp.source)
            run.rows_imported = n
        else:
            run.status = "skipped"
            session.add(run); session.commit(); return run
        run.status = "ok"
    except Exception as exc:  # noqa: BLE001 — record failure, keep watcher alive
        run.status = "error"; run.error = str(exc)
    session.add(run); session.commit()
    return run

def process_inbox(session: Session, inbox: Path) -> list[ImportRun]:
    runs = []
    for path in sorted(inbox.rglob("*")):
        if path.is_file():
            runs.append(process_file(session, path))
    return runs
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && pytest tests/test_runner.py -v`
Expected: PASS.

- [ ] **Step 5: Write `backend/app/ingestion/watcher.py`** (thin watchdog wrapper)

```python
import time
from pathlib import Path
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from app.db.database import SessionLocal
from app.ingestion.runner import process_file

class _Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        with SessionLocal() as s:
            process_file(s, Path(event.src_path))

def watch(inbox: Path) -> None:
    obs = Observer()
    obs.schedule(_Handler(), str(inbox), recursive=True)
    obs.start()
    try:
        while True:
            time.sleep(1)
    finally:
        obs.stop(); obs.join()
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/ingestion/runner.py backend/app/ingestion/watcher.py backend/tests/test_runner.py
git commit -m "feat: inbox runner and folder watcher"
```

---

## Phase 3 — Daily aggregation

### Task 3.1: Metric definitions + daily aggregation

**Files:**
- Create: `backend/app/domain/__init__.py`
- Create: `backend/app/domain/metrics.py`
- Create: `backend/app/domain/aggregation.py`
- Test: `backend/tests/test_aggregation.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_aggregation.py
from datetime import datetime, timezone, date
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.models import Base, Measurement
from app.domain.aggregation import daily_series

def _seed(s):
    for v in (43.0, 17.0, 8.0):  # same day
        s.add(Measurement(metric="steps", ts=datetime(2026,6,4,9,tzinfo=timezone.utc),
                          value=v, unit="count", source="x", dedup_key=str(v)))
    s.add(Measurement(metric="spo2", ts=datetime(2026,6,4,9,tzinfo=timezone.utc),
                      value=96.0, unit="%", source="x", dedup_key="a"))
    s.add(Measurement(metric="spo2", ts=datetime(2026,6,4,10,tzinfo=timezone.utc),
                      value=94.0, unit="%", source="x", dedup_key="b"))
    s.commit()

def test_steps_sum_spo2_mean():
    eng = create_engine("sqlite://"); Base.metadata.create_all(eng)
    with Session(eng) as s:
        _seed(s)
        steps = daily_series(s, "steps", date(2026,6,1), date(2026,6,30))
        assert steps == [(date(2026,6,4), 68.0)]
        spo2 = daily_series(s, "spo2", date(2026,6,1), date(2026,6,30))
        assert spo2 == [(date(2026,6,4), 95.0)]
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && pytest tests/test_aggregation.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `backend/app/domain/metrics.py`**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class MetricDef:
    key: str
    domain: str
    agg: str   # "sum" | "mean" | "min"
    unit: str

METRICS = {m.key: m for m in [
    MetricDef("steps", "activity", "sum", "count"),
    MetricDef("active_calories", "activity", "sum", "kcal"),
    MetricDef("total_calories", "activity", "sum", "kcal"),
    MetricDef("distance_km", "activity", "sum", "km"),
    MetricDef("heart_rate", "cardio", "mean", "bpm"),
    MetricDef("hrv_rmssd", "cardio", "mean", "ms"),
    MetricDef("resting_heart_rate", "cardio", "min", "bpm"),
    MetricDef("spo2", "cardio", "mean", "%"),
]}

def metrics_for_domain(domain: str) -> list[str]:
    return [k for k, m in METRICS.items() if m.domain == domain]
```

- [ ] **Step 4: Write `backend/app/domain/aggregation.py`**

```python
from datetime import date, datetime, time, timezone
from statistics import mean
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import Measurement
from app.domain.metrics import METRICS

_AGG = {"sum": sum, "mean": mean, "min": min}

def daily_series(session: Session, metric: str, start: date, end: date
                 ) -> list[tuple[date, float]]:
    agg = _AGG[METRICS[metric].agg]
    lo = datetime.combine(start, time.min, tzinfo=timezone.utc)
    hi = datetime.combine(end, time.max, tzinfo=timezone.utc)
    rows = session.scalars(
        select(Measurement).where(
            Measurement.metric == metric,
            Measurement.ts >= lo, Measurement.ts <= hi)).all()
    buckets: dict[date, list[float]] = {}
    for r in rows:
        buckets.setdefault(r.ts.astimezone(timezone.utc).date(), []).append(r.value)
    return [(d, round(float(agg(vals)), 2)) for d, vals in sorted(buckets.items())]
```

- [ ] **Step 5: Create empty `backend/app/domain/__init__.py`, run test**

Run: `cd backend && pytest tests/test_aggregation.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/domain backend/tests/test_aggregation.py
git commit -m "feat: metric definitions and daily aggregation"
```

---

## Phase 4 — Rules: targets, evaluation, insights

### Task 4.1: Targets + per-day evaluation (status + alerts)

**Files:**
- Create: `backend/app/rules/__init__.py`
- Create: `backend/app/rules/targets.py`
- Create: `backend/app/rules/evaluation.py`
- Test: `backend/tests/test_evaluation.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_evaluation.py
from app.rules.evaluation import evaluate_value

def test_spo2_red_below_92():
    r = evaluate_value("spo2", 90.0)
    assert r.status == "red"
    assert "fonte" in r.source.lower() or r.source

def test_spo2_green_at_96():
    assert evaluate_value("spo2", 96.0).status == "green"

def test_rhr_yellow_just_above_range():
    assert evaluate_value("resting_heart_rate", 105.0).status == "yellow"

def test_steps_green_above_target():
    assert evaluate_value("steps", 9000.0).status == "green"

def test_metric_without_target_returns_none():
    assert evaluate_value("heart_rate", 70.0) is None
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && pytest tests/test_evaluation.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `backend/app/rules/targets.py`**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Target:
    metric: str
    kind: str            # "daily_min" | "daily_range"
    green: tuple         # range considered green
    yellow: tuple        # range considered yellow (outside -> red)
    unit: str
    source: str

TARGETS = {
    "steps": Target("steps", "daily_min", green=(8000, float("inf")),
                    yellow=(5000, 8000), unit="count",
                    source="WHO physical-activity rationale / step literature"),
    "spo2": Target("spo2", "daily_min", green=(95, 100),
                   yellow=(92, 95), unit="%",
                   source="Clinical norm (Mayo Clinic / AHA): normal SpO2 95-100%"),
    "resting_heart_rate": Target("resting_heart_rate", "daily_range",
                    green=(60, 100), yellow=(50, 110), unit="bpm",
                    source="American Heart Association: normal resting HR 60-100 bpm"),
}
```

- [ ] **Step 4: Write `backend/app/rules/evaluation.py`**

```python
from dataclasses import dataclass
from app.rules.targets import TARGETS, Target

@dataclass
class Evaluation:
    metric: str
    value: float
    status: str      # green | yellow | red
    message: str
    source: str

def _in(value: float, rng: tuple) -> bool:
    return rng[0] <= value <= rng[1]

def evaluate_value(metric: str, value: float) -> Evaluation | None:
    target: Target | None = TARGETS.get(metric)
    if target is None:
        return None
    if _in(value, target.green):
        status, msg = "green", f"{metric} dentro da meta"
    elif _in(value, target.yellow):
        status, msg = "yellow", f"{metric} em atenção"
    else:
        status, msg = "red", f"{metric} fora da faixa recomendada"
    return Evaluation(metric, value, status, msg, target.source)
```

- [ ] **Step 5: Create empty `backend/app/rules/__init__.py`, run test**

Run: `cd backend && pytest tests/test_evaluation.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/rules/__init__.py backend/app/rules/targets.py backend/app/rules/evaluation.py backend/tests/test_evaluation.py
git commit -m "feat: guideline targets and per-value evaluation"
```

### Task 4.2: Trend insights (RHR / HRV vs 4-week baseline)

**Files:**
- Create: `backend/app/rules/insights.py`
- Test: `backend/tests/test_insights.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_insights.py
from datetime import date
from app.rules.insights import trend_insight

def test_rhr_rise_flagged():
    baseline = [(date(2026,5,d), 60.0) for d in range(1,29)]
    recent = [(date(2026,6,1), 67.0)]
    msg = trend_insight("resting_heart_rate", baseline, recent)
    assert msg is not None
    assert "subiu" in msg.text.lower()

def test_stable_rhr_no_insight():
    baseline = [(date(2026,5,d), 60.0) for d in range(1,29)]
    recent = [(date(2026,6,1), 61.0)]
    assert trend_insight("resting_heart_rate", baseline, recent) is None
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && pytest tests/test_insights.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `backend/app/rules/insights.py`**

```python
from dataclasses import dataclass
from datetime import date
from statistics import mean

@dataclass
class Insight:
    metric: str
    text: str
    severity: str   # info | warning

# metric -> (delta threshold, label, source)
_TREND = {
    "resting_heart_rate": (5.0, "FC de repouso", "AHA: sustained RHR rise can reflect fatigue/stress"),
    "hrv_rmssd": (-10.0, "HRV", "HRV trends track recovery/autonomic balance"),
}

def trend_insight(metric: str, baseline: list[tuple[date, float]],
                  recent: list[tuple[date, float]]) -> Insight | None:
    cfg = _TREND.get(metric)
    if cfg is None or not baseline or not recent:
        return None
    threshold, label, _src = cfg
    base = mean(v for _, v in baseline)
    cur = mean(v for _, v in recent)
    delta = cur - base
    if threshold > 0 and delta >= threshold:
        return Insight(metric, f"Seu {label} subiu {delta:.0f} vs. a média das últimas 4 semanas", "warning")
    if threshold < 0 and delta <= threshold:
        return Insight(metric, f"Seu {label} caiu {abs(delta):.0f} vs. a média das últimas 4 semanas", "warning")
    return None
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && pytest tests/test_insights.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/rules/insights.py backend/tests/test_insights.py
git commit -m "feat: trend insights for RHR and HRV"
```

---

## Phase 5 — Scoring

### Task 5.1: Domain sub-scores + overall score

Scoring model: for each scored metric, map its latest daily value to a 0–100 adherence
(`green`→100, `yellow`→60, `red`→20, no target→excluded). Domain score = mean of its scored
metrics. Overall = weighted mean of domain scores (weights configurable; default equal).

**Files:**
- Create: `backend/app/rules/scoring.py`
- Test: `backend/tests/test_scoring.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_scoring.py
from app.rules.scoring import status_to_points, domain_score, overall_score

def test_status_points():
    assert status_to_points("green") == 100
    assert status_to_points("yellow") == 60
    assert status_to_points("red") == 20

def test_domain_score_is_mean_of_scored_metrics():
    # spo2 green (100), resting_heart_rate red (20) -> 60
    latest = {"spo2": 96.0, "resting_heart_rate": 130.0, "heart_rate": 70.0}
    assert domain_score("cardio", latest) == 60.0

def test_overall_is_weighted_mean():
    scores = {"cardio": 60.0, "activity": 100.0}
    assert overall_score(scores) == 80.0
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && pytest tests/test_scoring.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `backend/app/rules/scoring.py`**

```python
from statistics import mean
from app.domain.metrics import metrics_for_domain
from app.rules.evaluation import evaluate_value

_POINTS = {"green": 100, "yellow": 60, "red": 20}
DOMAIN_WEIGHTS = {"cardio": 1.0, "activity": 1.0}

def status_to_points(status: str) -> int:
    return _POINTS[status]

def domain_score(domain: str, latest_values: dict[str, float]) -> float | None:
    points = []
    for metric in metrics_for_domain(domain):
        if metric not in latest_values:
            continue
        ev = evaluate_value(metric, latest_values[metric])
        if ev is None:
            continue
        points.append(_POINTS[ev.status])
    if not points:
        return None
    return round(mean(points), 1)

def overall_score(domain_scores: dict[str, float]) -> float | None:
    pairs = [(s, DOMAIN_WEIGHTS.get(d, 1.0))
             for d, s in domain_scores.items() if s is not None]
    if not pairs:
        return None
    num = sum(s * w for s, w in pairs)
    den = sum(w for _, w in pairs)
    return round(num / den, 1)
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && pytest tests/test_scoring.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/rules/scoring.py backend/tests/test_scoring.py
git commit -m "feat: domain sub-scores and overall health score"
```

---

## Phase 6 — API

### Task 6.1: Service layer — assemble dashboard data

**Files:**
- Create: `backend/app/domain/service.py`
- Test: `backend/tests/test_service.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_service.py
from datetime import datetime, timezone, date
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.models import Base, Measurement
from app.domain.service import latest_daily_values, build_scoreboard

def _seed(s):
    s.add(Measurement(metric="spo2", ts=datetime(2026,6,4,9,tzinfo=timezone.utc),
                      value=96.0, unit="%", source="x", dedup_key="a"))
    s.add(Measurement(metric="resting_heart_rate", ts=datetime(2026,6,4,9,tzinfo=timezone.utc),
                      value=130.0, unit="bpm", source="x", dedup_key="b"))
    s.commit()

def test_latest_daily_values():
    eng = create_engine("sqlite://"); Base.metadata.create_all(eng)
    with Session(eng) as s:
        _seed(s)
        vals = latest_daily_values(s, ["spo2", "resting_heart_rate"],
                                   date(2026,6,1), date(2026,6,30))
        assert vals["spo2"] == 96.0

def test_build_scoreboard_has_overall_and_domains():
    eng = create_engine("sqlite://"); Base.metadata.create_all(eng)
    with Session(eng) as s:
        _seed(s)
        board = build_scoreboard(s, date(2026,6,1), date(2026,6,30))
        assert "overall" in board and "domains" in board
        assert board["domains"]["cardio"] is not None
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && pytest tests/test_service.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `backend/app/domain/service.py`**

```python
from datetime import date
from sqlalchemy.orm import Session
from app.domain.aggregation import daily_series
from app.domain.metrics import METRICS, metrics_for_domain
from app.rules.scoring import domain_score, overall_score

DOMAINS = ["cardio", "activity"]

def latest_daily_values(session: Session, metrics: list[str],
                        start: date, end: date) -> dict[str, float]:
    out: dict[str, float] = {}
    for m in metrics:
        series = daily_series(session, m, start, end)
        if series:
            out[m] = series[-1][1]
    return out

def build_scoreboard(session: Session, start: date, end: date) -> dict:
    all_metrics = list(METRICS.keys())
    latest = latest_daily_values(session, all_metrics, start, end)
    domains = {d: domain_score(d, latest) for d in DOMAINS}
    return {"overall": overall_score(domains), "domains": domains,
            "as_of": end.isoformat()}
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && pytest tests/test_service.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/domain/service.py backend/tests/test_service.py
git commit -m "feat: dashboard service layer"
```

### Task 6.2: FastAPI app + routes

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/main.py`
- Test: `backend/tests/test_api.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_api.py
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base, Measurement
from app.api.main import app, get_session

def _override():
    eng = create_engine("sqlite://"); Base.metadata.create_all(eng)
    SL = sessionmaker(bind=eng)
    with SL() as s:
        s.add(Measurement(metric="spo2", ts=datetime(2026,6,4,9,tzinfo=timezone.utc),
                          value=96.0, unit="%", source="x", dedup_key="a"))
        s.commit()
    def _dep():
        with SL() as s:
            yield s
    return _dep

def test_score_endpoint():
    app.dependency_overrides[get_session] = _override()
    client = TestClient(app)
    r = client.get("/api/score?from=2026-06-01&to=2026-06-30")
    assert r.status_code == 200
    body = r.json()
    assert "overall" in body and "domains" in body

def test_metric_series_endpoint():
    app.dependency_overrides[get_session] = _override()
    client = TestClient(app)
    r = client.get("/api/metrics/spo2?from=2026-06-01&to=2026-06-30")
    assert r.status_code == 200
    assert r.json()["points"][0]["value"] == 96.0
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && pytest tests/test_api.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `backend/app/api/main.py`**

```python
from datetime import date
from collections.abc import Iterator
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, init_db
from app.domain.aggregation import daily_series
from app.domain.metrics import METRICS
from app.domain.service import build_scoreboard

app = FastAPI(title="yap-health")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])

def get_session() -> Iterator[Session]:
    with SessionLocal() as s:
        yield s

@app.on_event("startup")
def _startup() -> None:
    init_db()

@app.get("/api/score")
def get_score(from_: date = None, to: date = None, session: Session = Depends(get_session)):
    # FastAPI maps query 'from' via alias below
    return build_scoreboard(session, from_, to)

@app.get("/api/metrics/{metric}")
def get_metric(metric: str, from_: date = None, to: date = None,
               session: Session = Depends(get_session)):
    if metric not in METRICS:
        raise HTTPException(404, "unknown metric")
    series = daily_series(session, metric, from_, to)
    return {"metric": metric, "unit": METRICS[metric].unit,
            "points": [{"date": d.isoformat(), "value": v} for d, v in series]}
```

> Note for the implementer: FastAPI cannot use `from` as a Python parameter name. Use
> `Query(alias="from")`. Update the two handlers:
> `from_: date = Query(None, alias="from")` and `to: date = Query(None, alias="to")`,
> importing `Query` from `fastapi`. Adjust the test URLs accordingly (already use `from=`/`to=`).

- [ ] **Step 4: Apply the `Query(alias=...)` fix and create empty `backend/app/api/__init__.py`**

```python
# in main.py, add to imports:
from fastapi import Query
# change both handler signatures to:
#   from_: date = Query(None, alias="from"), to: date = Query(None, alias="to")
```

- [ ] **Step 5: Run to verify it passes**

Run: `cd backend && pytest tests/test_api.py -v`
Expected: PASS (both tests).

- [ ] **Step 6: Add alerts/insights/import endpoints**

Add to `main.py`:

```python
from app.rules.evaluation import evaluate_value
from app.domain.service import latest_daily_values

@app.get("/api/alerts")
def get_alerts(from_: date = Query(None, alias="from"), to: date = Query(None, alias="to"),
               session: Session = Depends(get_session)):
    latest = latest_daily_values(session, list(METRICS.keys()), from_, to)
    out = []
    for metric, value in latest.items():
        ev = evaluate_value(metric, value)
        if ev and ev.status != "green":
            out.append({"metric": metric, "status": ev.status,
                        "message": ev.message, "source": ev.source, "value": value})
    return {"alerts": out}
```

- [ ] **Step 7: Manual smoke test of the running server**

Run: `cd backend && uvicorn app.api.main:app --reload &` then `sleep 2 && curl -s "http://localhost:8000/api/score?from=2026-06-01&to=2026-06-30"`
Expected: JSON with `overall`/`domains`. Then `kill %1`.

- [ ] **Step 8: Commit**

```bash
git add backend/app/api backend/tests/test_api.py
git commit -m "feat: FastAPI score/metrics/alerts endpoints"
```

### Task 6.3: CLI entrypoint to import the existing snapshot

**Files:**
- Create: `backend/app/cli.py`
- Test: manual

- [ ] **Step 1: Write `backend/app/cli.py`**

```python
import sys
from pathlib import Path
from app.db.database import SessionLocal, init_db
from app.ingestion.runner import process_inbox

def main() -> None:
    init_db()
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if folder is None:
        print("usage: python -m app.cli <folder>"); return
    with SessionLocal() as s:
        runs = process_inbox(s, folder)
    ok = sum(r.rows_imported for r in runs if r.status == "ok")
    print(f"processed {len(runs)} files, imported {ok} rows")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Import the real snapshot and verify**

Run: `cd backend && python -m app.cli "../references/data/health_data/Clue Woman Health"`
Expected: prints "processed N files, imported >0 rows".
Run: `curl -s "http://localhost:8000/api/score?from=2026-05-01&to=2026-06-30"` (server running)
Expected: a real overall score and cardio/activity sub-scores from the actual data.

- [ ] **Step 3: Commit**

```bash
git add backend/app/cli.py
git commit -m "feat: CLI to bulk-import a snapshot folder"
```

---

## Phase 7 — Frontend (React + Vite + shadcn/ui + Recharts)

> Frontend tasks favor concrete component code + a vitest smoke test + manual verification,
> since React UI is verified visually rather than via fine-grained TDD.

### Task 7.1: Vite + Tailwind + shadcn scaffold

**Files:**
- Create: `frontend/` (Vite React-TS)
- Create: `frontend/src/lib/api.ts`

- [ ] **Step 1: Scaffold**

Run:
```bash
cd /Users/bambrozim/Projects/yap-health
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install
npm install axios @tanstack/react-query recharts
npm install -D tailwindcss postcss autoprefixer vitest @testing-library/react jsdom
npx tailwindcss init -p
```

- [ ] **Step 2: Configure Tailwind** — set `content: ["./index.html","./src/**/*.{ts,tsx}"]` in `tailwind.config.js`; add the three `@tailwind` directives to `src/index.css`.

- [ ] **Step 3: Initialize shadcn/ui**

Run: `cd frontend && npx shadcn@latest init -d && npx shadcn@latest add card badge`
Expected: `src/components/ui/card.tsx` and `badge.tsx` created.

- [ ] **Step 4: Write `frontend/src/lib/api.ts`**

```ts
import axios from "axios";
const client = axios.create({ baseURL: "http://localhost:8000/api" });

export interface Scoreboard {
  overall: number | null;
  domains: Record<string, number | null>;
  as_of: string;
}
export interface Series {
  metric: string; unit: string;
  points: { date: string; value: number }[];
}
export interface Alert {
  metric: string; status: string; message: string; source: string; value: number;
}

const range = "from=2026-05-01&to=2026-06-30"; // v1: fixed window; make dynamic later
export const getScore = () => client.get<Scoreboard>(`/score?${range}`).then(r => r.data);
export const getMetric = (m: string) => client.get<Series>(`/metrics/${m}?${range}`).then(r => r.data);
export const getAlerts = () => client.get<{alerts: Alert[]}>(`/alerts?${range}`).then(r => r.data.alerts);
```

- [ ] **Step 5: Commit**

```bash
git add frontend
git commit -m "chore: scaffold React frontend with Tailwind + shadcn + api client"
```

### Task 7.2: Score cards + alerts feed on Home

**Files:**
- Create: `frontend/src/components/ScoreCard.tsx`
- Create: `frontend/src/components/AlertsFeed.tsx`
- Create: `frontend/src/pages/Home.tsx`
- Test: `frontend/src/components/ScoreCard.test.tsx`
- Modify: `frontend/src/main.tsx`, `frontend/src/App.tsx`

- [ ] **Step 1: Write the failing smoke test**

```tsx
// frontend/src/components/ScoreCard.test.tsx
import { render, screen } from "@testing-library/react";
import { ScoreCard } from "./ScoreCard";
import { describe, it, expect } from "vitest";

describe("ScoreCard", () => {
  it("shows label and score", () => {
    render(<ScoreCard label="Cardíaco" score={60} />);
    expect(screen.getByText("Cardíaco")).toBeTruthy();
    expect(screen.getByText("60")).toBeTruthy();
  });
  it("shows dash when score is null", () => {
    render(<ScoreCard label="Atividade" score={null} />);
    expect(screen.getByText("—")).toBeTruthy();
  });
});
```

Add to `package.json` scripts: `"test": "vitest run"`. Configure vitest with jsdom in `vite.config.ts` (`test: { environment: "jsdom" }`).

- [ ] **Step 2: Run to verify it fails**

Run: `cd frontend && npm test`
Expected: FAIL (ScoreCard not found).

- [ ] **Step 3: Write `frontend/src/components/ScoreCard.tsx`**

```tsx
import { Card } from "@/components/ui/card";

const color = (s: number | null) =>
  s == null ? "text-muted-foreground"
  : s >= 80 ? "text-green-600" : s >= 50 ? "text-yellow-600" : "text-red-600";

export function ScoreCard({ label, score }: { label: string; score: number | null }) {
  return (
    <Card className="p-6 flex flex-col gap-2">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className={`text-4xl font-bold ${color(score)}`}>
        {score == null ? "—" : Math.round(score)}
      </span>
    </Card>
  );
}
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd frontend && npm test`
Expected: PASS.

- [ ] **Step 5: Write `AlertsFeed.tsx`, `Home.tsx`, wire `App.tsx` + React Query provider**

```tsx
// frontend/src/components/AlertsFeed.tsx
import { Badge } from "@/components/ui/badge";
import type { Alert } from "@/lib/api";

const tone = (s: string) => (s === "red" ? "destructive" : "secondary") as const;

export function AlertsFeed({ alerts }: { alerts: Alert[] }) {
  if (!alerts.length) return <p className="text-muted-foreground">Sem alertas ativos.</p>;
  return (
    <ul className="space-y-3">
      {alerts.map((a) => (
        <li key={a.metric} className="flex flex-col gap-1 border-b pb-2">
          <div className="flex items-center gap-2">
            <Badge variant={tone(a.status)}>{a.status}</Badge>
            <span className="font-medium">{a.message}</span>
          </div>
          <span className="text-xs text-muted-foreground">Fonte: {a.source}</span>
        </li>
      ))}
    </ul>
  );
}
```

```tsx
// frontend/src/pages/Home.tsx
import { useQuery } from "@tanstack/react-query";
import { getScore, getAlerts } from "@/lib/api";
import { ScoreCard } from "@/components/ScoreCard";
import { AlertsFeed } from "@/components/AlertsFeed";

const LABELS: Record<string, string> = { cardio: "Cardíaco", activity: "Atividade" };

export function Home() {
  const score = useQuery({ queryKey: ["score"], queryFn: getScore });
  const alerts = useQuery({ queryKey: ["alerts"], queryFn: getAlerts });
  return (
    <main className="max-w-4xl mx-auto p-8 space-y-8">
      <h1 className="text-2xl font-bold">yap-health</h1>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <ScoreCard label="Score geral" score={score.data?.overall ?? null} />
        {Object.entries(score.data?.domains ?? {}).map(([k, v]) => (
          <ScoreCard key={k} label={LABELS[k] ?? k} score={v} />
        ))}
      </div>
      <section>
        <h2 className="text-lg font-semibold mb-3">Alertas & insights</h2>
        <AlertsFeed alerts={alerts.data ?? []} />
      </section>
      <p className="text-xs text-muted-foreground">
        Informativo — não é aconselhamento médico.
      </p>
    </main>
  );
}
```

```tsx
// frontend/src/App.tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Home } from "@/pages/Home";
const qc = new QueryClient();
export default function App() {
  return <QueryClientProvider client={qc}><Home /></QueryClientProvider>;
}
```

- [ ] **Step 6: Manual verification (full stack)**

Run backend: `cd backend && uvicorn app.api.main:app &`
Run frontend: `cd frontend && npm run dev`
Open `http://localhost:5173`.
Expected: Score geral + Cardíaco + Atividade cards with real numbers; alerts list with sources; medical disclaimer visible.

- [ ] **Step 7: Commit**

```bash
git add frontend/src
git commit -m "feat: Home dashboard with score cards and alerts feed"
```

### Task 7.3: Domain charts (Recharts) for Atividade + Cardíaco

**Files:**
- Create: `frontend/src/components/MetricChart.tsx`
- Create: `frontend/src/pages/Domain.tsx`
- Modify: `frontend/src/App.tsx` (simple state-based nav: Home ↔ Domain)

- [ ] **Step 1: Write `frontend/src/components/MetricChart.tsx`**

```tsx
import { useQuery } from "@tanstack/react-query";
import { getMetric } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export function MetricChart({ metric, title }: { metric: string; title: string }) {
  const q = useQuery({ queryKey: ["metric", metric], queryFn: () => getMetric(metric) });
  const data = q.data?.points ?? [];
  return (
    <Card className="p-4">
      <h3 className="font-medium mb-2">{title} <span className="text-xs text-muted-foreground">({q.data?.unit})</span></h3>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data}>
          <XAxis dataKey="date" hide />
          <YAxis width={40} />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke="#2563eb" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}
```

- [ ] **Step 2: Write `frontend/src/pages/Domain.tsx`**

```tsx
import { MetricChart } from "@/components/MetricChart";

const DOMAIN_METRICS: Record<string, { metric: string; title: string }[]> = {
  cardio: [
    { metric: "resting_heart_rate", title: "FC de repouso" },
    { metric: "spo2", title: "SpO₂" },
    { metric: "hrv_rmssd", title: "HRV (rmssd)" },
    { metric: "heart_rate", title: "Frequência cardíaca" },
  ],
  activity: [
    { metric: "steps", title: "Passos" },
    { metric: "active_calories", title: "Calorias ativas" },
    { metric: "distance_km", title: "Distância" },
  ],
};

export function Domain({ domain }: { domain: "cardio" | "activity" }) {
  return (
    <main className="max-w-4xl mx-auto p-8 space-y-4">
      <h1 className="text-2xl font-bold capitalize">{domain}</h1>
      <div className="grid md:grid-cols-2 gap-4">
        {DOMAIN_METRICS[domain].map((m) => (
          <MetricChart key={m.metric} {...m} />
        ))}
      </div>
    </main>
  );
}
```

- [ ] **Step 3: Add minimal nav in `App.tsx`** (no router dependency in v1)

```tsx
// frontend/src/App.tsx
import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Home } from "@/pages/Home";
import { Domain } from "@/pages/Domain";

const qc = new QueryClient();
export type Route = "home" | "cardio" | "activity";

export default function App() {
  const [route, setRoute] = useState<Route>("home");
  return (
    <QueryClientProvider client={qc}>
      {route !== "home" && (
        <button className="m-4 text-sm underline" onClick={() => setRoute("home")}>
          ← Home
        </button>
      )}
      {route === "home" ? <Home onOpenDomain={setRoute} /> : <Domain domain={route} />}
    </QueryClientProvider>
  );
}
```

Update `Home` to accept `onOpenDomain?: (r: "cardio" | "activity") => void` and wrap each
domain `ScoreCard` in a `<button onClick={() => onOpenDomain?.(k as "cardio" | "activity")}>`
so clicking a domain card navigates. The "Score geral" card stays non-clickable.

- [ ] **Step 4: Manual verification**

Run full stack (backend + `npm run dev`). Click a domain card → see its charts populated from real data.
Expected: line charts render with real series for steps, spo2, resting_heart_rate, etc.

- [ ] **Step 5: Commit**

```bash
git add frontend/src
git commit -m "feat: domain charts for activity and cardio"
```

---

## Phase 8 — Wrap-up

### Task 8.1: README + run instructions

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write `README.md`** documenting: what it is; privacy/disclaimer; how to run backend (`uvicorn app.api.main:app`) and watcher; how to bulk-import (`python -m app.cli <folder>`); how to run frontend (`npm run dev`); where the inbox folder is; data sources and dedup model; v1 scope (Atividade + Cardíaco) and roadmap (Sono → Nutrição → Corpo).

- [ ] **Step 2: Run the full test suite**

Run: `cd backend && pytest -v` and `cd frontend && npm test`
Expected: all green.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add README with run and data instructions"
```

---

## Self-review notes (coverage vs spec)

- §2 Architecture → Phases 0–7 (backend pipeline + API + React). ✓
- §3 Data inventory / §4 dedup & canonical schema → Tasks 1.1, 2.1–2.5. ✓ (Health Connect canonical, TCX workout supplement, idempotent dedup_key, ImportRun audit.)
- §5 Rule engine (targets w/ sources, status/alerts, sub-scores→overall, insights) → Tasks 4.1, 4.2, 5.1. ✓ (Targets cited: WHO, AHA, clinical norms.)
- §6 API endpoints → Tasks 6.1–6.3 (`/score`, `/metrics/{metric}`, `/alerts`, plus CLI import; `/import/status` and `/insights` endpoints deferred — insights computed but surfaced via a follow-up endpoint, noted below).
- §7 Frontend (Home score+cards+feed, domain charts, import status) → Tasks 7.1–7.3 (import-status panel deferred to roadmap).
- §8 v1 slice (Atividade + Cardíaco end-to-end) → all phases scoped to these two domains. ✓
- §9 Project structure → matches created paths. ✓

**Deferred within v1 (intentional, low-risk, add if time permits):**
- `/api/insights` endpoint + insights panel (trend logic already built in Task 4.2; wire baseline=prior 4 weeks, recent=last 3 days, expose via endpoint mirroring `/alerts`).
- `/api/import/status` endpoint + UI panel (ImportRun data already persisted in Task 2.5).
- FIT parsing (TCX summary covers v1 scoring).

These are explicitly out-of-critical-path for the vertical slice and tracked here so they aren't lost.
