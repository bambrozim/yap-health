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
            run.rows_imported = persist_measurements(
                session, imp.parse(path), source=imp.source)
            run.status = "ok"
        elif path.suffix == ".tcx":
            imp = TcxWorkoutImporter()
            run.source = imp.source
            run.rows_imported = persist_workouts(
                session, [imp.parse(path)], source=imp.source)
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
