from pathlib import Path

REQUIRED_ITEMS: list[tuple[str, str]] = [
    ("README.md", "file"),
    ("aeos.toml", "file"),
    ("governance", "dir"),
    ("governance/adr", "dir"),
    ("governance/rfc", "dir"),
    ("governance/dec", "dir"),
    ("governance/standards", "dir"),
    ("governance/playbooks", "dir"),
    ("docs", "dir"),
    ("src", "dir"),
    ("tests", "dir"),
]


def check_project(project: Path) -> list[tuple[str, bool]]:
    results = []
    for item, kind in REQUIRED_ITEMS:
        target = project / item
        found = target.is_file() if kind == "file" else target.is_dir()
        results.append((item, found))
    return results
