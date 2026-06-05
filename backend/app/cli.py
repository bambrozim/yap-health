import sys
from pathlib import Path

from app.db.database import SessionLocal, init_db
from app.ingestion.runner import process_inbox


def main() -> None:
    init_db()
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if folder is None:
        print("usage: python -m app.cli <folder>")
        return
    with SessionLocal() as s:
        runs = process_inbox(s, folder)
    ok = sum(r.rows_imported for r in runs if r.status == "ok")
    print(f"processed {len(runs)} files, imported {ok} rows")


if __name__ == "__main__":
    main()
