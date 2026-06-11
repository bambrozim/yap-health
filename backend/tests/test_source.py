from app.ingestion.source import find_health_root, resolve_source_dir


def _make_drive(tmp_path):
    # Mimic a Drive-for-Desktop mount: <root>/My Drive/yap/<health folders>
    root = tmp_path / "GoogleDrive-me@gmail.com" / "My Drive" / "yap"
    (root / "Clue Woman Health").mkdir(parents=True)
    (root / "Health Sync Steps").mkdir(parents=True)
    return tmp_path, root


def test_find_health_root_locates_folder_with_markers(tmp_path):
    search_base, expected = _make_drive(tmp_path)
    found = find_health_root([search_base])
    assert found == expected


def test_find_health_root_returns_none_when_absent(tmp_path):
    (tmp_path / "Documents" / "stuff").mkdir(parents=True)
    assert find_health_root([tmp_path]) is None


def test_explicit_override_wins(tmp_path):
    explicit = tmp_path / "custom"
    explicit.mkdir()
    assert resolve_source_dir(explicit=explicit, search_roots=[tmp_path]) == explicit


def test_resolve_falls_back_to_autodetect(tmp_path):
    search_base, expected = _make_drive(tmp_path)
    assert resolve_source_dir(explicit=None, search_roots=[search_base]) == expected
