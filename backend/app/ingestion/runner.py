from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import ImportRun
from app.ingestion.source import resolve_source_dir
from app.ingestion.clue import ClueJsonImporter
from app.ingestion.health_connect import HealthConnectSqliteImporter
from app.ingestion.health_sync_csv import HealthSyncCsvImporter
from app.ingestion.health_sync_workouts import TcxWorkoutImporter
from app.ingestion.persist import (
    persist_cycle_entries,
    persist_measurements,
    persist_workouts,
)


def process_file(session: Session, path: Path) -> ImportRun:
    run = ImportRun(filename=path.name, source="", status="running",
                    started_at=datetime.now(timezone.utc))
    try:
        if path.suffix == ".db":
            imp = HealthConnectSqliteImporter()
            run.source = imp.source
            run.rows_imported = persist_measurements(
                session, imp.parse(path), source=imp.source)
            run.status = "ok"
        elif path.suffix == ".tcx":
            imp = TcxWorkoutImporter()
            run.source = imp.source
            run.rows_imported = persist_workouts(
                session, [imp.parse(path)], source=imp.source)
            run.status = "ok"
        elif path.suffix == ".csv":
            imp = HealthSyncCsvImporter()
            run.source = imp.source
            run.rows_imported = persist_measurements(
                session, imp.parse(path), source=imp.source)
            run.status = "ok"
        elif ClueJsonImporter().matches(path):
            imp = ClueJsonImporter()
            run.source = imp.source
            run.rows_imported = persist_cycle_entries(
                session, imp.parse(path), source=imp.source)
            run.status = "ok"
        else:
            run.status = "skipped"
    except Exception as exc:  # noqa: BLE001 — record failure, keep watcher alive
        run.status = "error"
        run.error = str(exc)
    session.add(run)
    session.commit()
    return run


def process_inbox(session: Session, inbox: Path) -> list[ImportRun]:
    runs = []
    for path in sorted(inbox.rglob("*")):
        if path.is_file():
            runs.append(process_file(session, path))
    return runs


def sync_from_source(session: Session) -> dict:
    """Resolve the configured/auto-detected source folder and ingest it."""
    source = resolve_source_dir(explicit=settings.source_dir)
    if source is None:
        return {"ok": False, "source_dir": None, "files": 0, "rows": 0,
                "reason": "Nenhuma pasta de origem encontrada. Instale o Google "
                          "Drive for Desktop ou defina YAP_SOURCE_DIR."}
    runs = process_inbox(session, source)
    rows = sum(r.rows_imported for r in runs if r.status == "ok")
    return {"ok": True, "source_dir": str(source),
            "files": len(runs), "rows": rows}
