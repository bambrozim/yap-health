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
        obs.stop()
        obs.join()
