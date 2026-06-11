"""Resolve where to ingest health data from.

With Google Drive for Desktop the Drive is mounted as a local folder, so the
"fetch from Drive" requirement is just reading that path. We accept an explicit
override (``settings.source_dir`` / ``YAP_SOURCE_DIR``) and otherwise auto-detect
the folder that holds the health subfolders inside the Drive mount.
"""

from pathlib import Path

# A directory is the health-data root if it directly contains one of these.
_MARKERS = ("Clue Woman Health",)
_MARKER_PREFIXES = ("Health Sync",)
_MAX_DEPTH = 5


def _is_health_root(path: Path) -> bool:
    try:
        for child in path.iterdir():
            if not child.is_dir():
                continue
            if child.name in _MARKERS or child.name.startswith(_MARKER_PREFIXES):
                return True
    except (PermissionError, FileNotFoundError, NotADirectoryError):
        return False
    return False


def _walk(root: Path, depth: int):
    if depth < 0 or not root.is_dir():
        return
    if _is_health_root(root):
        yield root
        return  # do not descend further once found
    try:
        children = sorted(p for p in root.iterdir() if p.is_dir())
    except (PermissionError, FileNotFoundError):
        return
    for child in children:
        yield from _walk(child, depth - 1)


def default_search_roots() -> list[Path]:
    """Likely Drive-for-Desktop mount locations on macOS."""
    return sorted(Path.home().glob("Library/CloudStorage/GoogleDrive-*"))


def find_health_root(search_roots: list[Path]) -> Path | None:
    for base in search_roots:
        for match in _walk(base, _MAX_DEPTH):
            return match
    return None


def resolve_source_dir(explicit: Path | None,
                       search_roots: list[Path] | None = None) -> Path | None:
    if explicit and Path(explicit).is_dir():
        return Path(explicit)
    roots = search_roots if search_roots is not None else default_search_roots()
    return find_health_root(roots)
