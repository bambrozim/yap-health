import sys
from pathlib import Path

from app.db.database import SessionLocal, init_db
from app.ingestion.runner import process_inbox, sync_from_source


def main() -> None:
    init_db()
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    with SessionLocal() as s:
        if folder is not None:
            runs = process_inbox(s, folder)
            ok = sum(r.rows_imported for r in runs if r.status == "ok")
            print(f"processed {len(runs)} files, imported {ok} rows from {folder}")
        else:
            # No path: resolve the configured/auto-detected source (e.g. Drive).
            result = sync_from_source(s)
            if not result["ok"]:
                print(result["reason"])
                return
            print(f"processed {result['files']} files, imported {result['rows']} "
                  f"rows from {result['source_dir']}")


if __name__ == "__main__":
    main()
