from datetime import datetime, timezone

from app.ingestion.base import ParsedMeasurement, make_dedup_key


def test_dedup_key_prefers_source_uuid():
    assert make_dedup_key("steps", datetime(2026, 6, 4, tzinfo=timezone.utc),
                          43.0, "hc", "uuid-1") == "hc:uuid-1"


def test_dedup_key_falls_back_to_hash():
    k = make_dedup_key("steps", datetime(2026, 6, 4, tzinfo=timezone.utc),
                       43.0, "csv", None)
    assert k.startswith("csv:") and len(k) > 10
    k2 = make_dedup_key("steps", datetime(2026, 6, 4, tzinfo=timezone.utc),
                        43.0, "csv", None)
    assert k == k2


def test_parsed_measurement_holds_fields():
    p = ParsedMeasurement("spo2", datetime(2026, 6, 4, tzinfo=timezone.utc), 96.0, "%")
    assert p.metric == "spo2" and p.unit == "%"
