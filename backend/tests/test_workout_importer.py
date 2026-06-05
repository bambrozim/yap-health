from app.ingestion.health_sync_workouts import TcxWorkoutImporter

TCX = """<?xml version="1.0"?>
<TrainingCenterDatabase><Activities><Activity Sport="Other">
<Id>2026-06-04T08:12:55Z</Id>
<Lap StartTime="2026-06-04T08:12:55Z">
<TotalTimeSeconds>3439</TotalTimeSeconds>
<DistanceMeters>0</DistanceMeters>
<Calories>250</Calories>
</Lap></Activity></Activities></TrainingCenterDatabase>"""


def test_tcx_parses_workout(tmp_path):
    f = tmp_path / "w.tcx"
    f.write_text(TCX)
    w = TcxWorkoutImporter().parse(f)
    assert w.duration_s == 3439
    assert w.calories == 250
    assert w.distance_km == 0.0
    assert w.type == "Other"


def test_tcx_sums_multiple_laps(tmp_path):
    tcx = TCX.replace(
        "</Lap></Activity>",
        "</Lap><Lap StartTime='2026-06-04T09:12:55Z'>"
        "<TotalTimeSeconds>61</TotalTimeSeconds>"
        "<DistanceMeters>1000</DistanceMeters>"
        "<Calories>50</Calories></Lap></Activity>")
    f = tmp_path / "w.tcx"
    f.write_text(tcx)
    w = TcxWorkoutImporter().parse(f)
    assert w.duration_s == 3500
    assert w.calories == 300
    assert w.distance_km == 1.0
