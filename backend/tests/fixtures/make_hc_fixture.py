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

        -- one 8h session ending 2026-06-04 (1749002400000 = start; +8h end)
        CREATE TABLE sleep_session_record_table (
            uuid TEXT, start_time INTEGER, start_zone_offset INTEGER,
            end_time INTEGER, end_zone_offset INTEGER);
        INSERT INTO sleep_session_record_table VALUES
            ('sl1', 1748973600000, -10800, 1749002400000, -10800);

        CREATE TABLE sleep_stages_table (
            parent_key INTEGER, stage_start_time INTEGER,
            stage_end_time INTEGER, stage_type INTEGER);
        INSERT INTO sleep_stages_table VALUES
            (1, 1748973600000, 1748980800000, 5),   -- 2h deep
            (1, 1748980800000, 1748984400000, 6),   -- 1h rem
            (1, 1748984400000, 1748988000000, 4);   -- 1h light (ignored)

        CREATE TABLE nutrition_record_table (
            uuid TEXT, start_time INTEGER, start_zone_offset INTEGER,
            energy REAL, protein REAL, total_carbohydrate REAL, total_fat REAL,
            dietary_fiber REAL, sugar REAL, sodium REAL);
        INSERT INTO nutrition_record_table VALUES
            ('n1', 1749000000000, -10800, 1410000.0, 60.0, 150.0, 45.0, 19.2, 53.8, 2.017),
            ('n2', 1749003600000, -10800, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);  -- empty, skipped
        """
    )
    con.commit()
    con.close()
    return path
