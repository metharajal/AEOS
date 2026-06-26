from pathlib import Path

from aeos.onboarding.checker import REQUIRED_ITEMS, check_project


def _make_full_project(root: Path) -> None:
    for item, kind in REQUIRED_ITEMS:
        target = root / item
        if kind == "file":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("")
        else:
            target.mkdir(parents=True, exist_ok=True)


def test_check_project_all_present(tmp_path: Path) -> None:
    _make_full_project(tmp_path)
    results = check_project(tmp_path)
    assert all(found for _, found in results)
    assert len(results) == len(REQUIRED_ITEMS)


def test_check_project_empty(tmp_path: Path) -> None:
    results = check_project(tmp_path)
    assert all(not found for _, found in results)
    assert len(results) == len(REQUIRED_ITEMS)


def test_check_project_partial(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# test")
    results = check_project(tmp_path)
    found_map = dict(results)
    assert found_map["README.md"] is True
    assert found_map["aeos.toml"] is False
    assert found_map["governance"] is False
