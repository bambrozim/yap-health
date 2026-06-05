import sqlite3
from pathlib import Path


def build(path: Path) -> Path:
    """Build a minimal Health Connect-shaped SQLite export for tests."""
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

        CREATE TABLE heart_rate_record_series_table (
            parent_key INTEGER, beats_per_minute INTEGER, epoch_millis INTEGER);
        INSERT INTO heart_rate_record_series_table VALUES
            (1, 64, 1749000000000),
            (1, 70, 1749000060000);
        """
    )
    con.commit()
    con.close()
    return path
