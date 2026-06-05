import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.ingestion.base import ParsedWorkout

SOURCE = "health_sync"
_NS = {"t": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}


def _parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def _findall(el: ET.Element, tag: str) -> list[ET.Element]:
    """Find descendants by tag, handling both namespaced and bare documents."""
    found = el.findall(f".//t:{tag}", _NS)
    return found if found else el.findall(f".//{tag}")


def _child_float(el: ET.Element, tag: str) -> float:
    """Read a direct child's float value (0.0 if absent).

    Uses direct children only so Lap-level totals are not conflated with
    per-Trackpoint values (e.g. DistanceMeters appears in both).
    """
    child = el.find(f"t:{tag}", _NS)
    if child is None:
        child = el.find(tag)
    return float(child.text) if child is not None and child.text else 0.0


class TcxWorkoutImporter:
    source = SOURCE

    def matches(self, path: Path) -> bool:
        return path.suffix == ".tcx"

    def parse(self, path: Path) -> ParsedWorkout:
        root = ET.parse(path).getroot()
        act = _findall(root, "Activity")[0]
        sport = act.get("Sport", "unknown")
        start = _parse_iso(_findall(act, "Id")[0].text)
        laps = _findall(act, "Lap")
        duration = int(sum(_child_float(lap, "TotalTimeSeconds") for lap in laps))
        dist_m = sum(_child_float(lap, "DistanceMeters") for lap in laps)
        cals = sum(_child_float(lap, "Calories") for lap in laps)
        return ParsedWorkout(
            type=sport,
            start_ts=start,
            end_ts=start + timedelta(seconds=duration),
            duration_s=duration,
            distance_km=dist_m / 1000.0,
            calories=cals,
            source_uuid=f"tcx:{start.isoformat()}")
