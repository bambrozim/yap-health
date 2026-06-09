import json
from datetime import date
from pathlib import Path
from typing import Iterator

from app.ingestion.base import ParsedCycleEntry

SOURCE = "clue"
_FILENAME = "measurements.json"


class ClueJsonImporter:
    """Imports menstruation (period/flow) entries from a Clue native JSON export.

    Clue's ``measurements.json`` is a flat list of ``{type, id, date, value}``
    tracking records. Only ``period`` entries are surfaced here; the broader
    symptom tracking (mood, pain, digestion, ...) is intentionally out of scope.
    """

    source = SOURCE

    def matches(self, path: Path) -> bool:
        return path.name == _FILENAME

    def parse(self, path: Path) -> Iterator[ParsedCycleEntry]:
        records = json.loads(path.read_text())
        for rec in records:
            if rec.get("type") != "period":
                continue
            value = rec.get("value") or {}
            flow = value.get("option")
            if not flow:
                continue
            yield ParsedCycleEntry(date.fromisoformat(rec["date"]), flow)
