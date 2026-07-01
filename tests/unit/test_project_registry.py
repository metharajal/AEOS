"""Unit tests for aeos.project.registry and the `aeos project register` CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aeos.cli import app
from aeos.project.registry import (
    ProjectRegistration,
    ProjectRegistry,
    find_project,
    load_registry,
    register_project,
    save_registry,
)

runner = CliRunner()


def _mem(tmp_path: Path) -> Path:
    mem = tmp_path / "memory"
    mem.mkdir()
    return mem


def _reg(tmp_path: Path) -> Path:
    return tmp_path / "registry.json"


# ---------------------------------------------------------------------------
# ProjectRegistration
# ---------------------------------------------------------------------------


def test_registration_registered_at_auto(tmp_path: Path) -> None:
    reg = ProjectRegistration(
        name="p", project_type="recovered-project", memory_dir=tmp_path
    )
    assert reg.registered_at != ""
    assert "T" in reg.registered_at


def test_registration_custom_registered_at_preserved(tmp_path: Path) -> None:
    reg = ProjectRegistration(
        name="p",
        project_type="recovered-project",
        memory_dir=tmp_path,
        registered_at="2026-01-01T00:00:00Z",
    )
    assert reg.registered_at == "2026-01-01T00:00:00Z"


def test_registration_no_evidence_dir(tmp_path: Path) -> None:
    reg = ProjectRegistration(
        name="p", project_type="recovered-project", memory_dir=tmp_path
    )
    assert reg.evidence_dir is None


def test_registration_with_evidence_dir(tmp_path: Path) -> None:
    ev = tmp_path / "evidence"
    reg = ProjectRegistration(
        name="p", project_type="recovered-project", memory_dir=tmp_path, evidence_dir=ev
    )
    assert reg.evidence_dir == ev


def test_registration_fields_stored(tmp_path: Path) -> None:
    reg = ProjectRegistration(
        name="my-proj", project_type="audited-project", memory_dir=tmp_path
    )
    assert reg.name == "my-proj"
    assert reg.project_type == "audited-project"
    assert reg.memory_dir == tmp_path


# ---------------------------------------------------------------------------
# load_registry
# ---------------------------------------------------------------------------


def test_load_registry_missing_file(tmp_path: Path) -> None:
    registry = load_registry(_reg(tmp_path))
    assert isinstance(registry, ProjectRegistry)
    assert registry.projects == []


def test_load_registry_invalid_json(tmp_path: Path) -> None:
    reg_path = _reg(tmp_path)
    reg_path.write_text("not valid json ][", encoding="utf-8")
    registry = load_registry(reg_path)
    assert registry.projects == []


def test_load_registry_with_projects(tmp_path: Path) -> None:
    reg_path = _reg(tmp_path)
    data = {
        "updated_at": "2026-01-01T00:00:00Z",
        "projects": [
            {
                "name": "proj-a",
                "type": "recovered-project",
                "memory_dir": str(tmp_path),
                "evidence_dir": None,
                "registered_at": "2026-01-01T00:00:00Z",
            }
        ],
    }
    reg_path.write_text(json.dumps(data), encoding="utf-8")
    registry = load_registry(reg_path)
    assert len(registry.projects) == 1
    assert registry.projects[0].name == "proj-a"


def test_load_registry_evidence_dir_none_roundtrip(tmp_path: Path) -> None:
    reg_path = _reg(tmp_path)
    data = {
        "updated_at": "2026-01-01T00:00:00Z",
        "projects": [
            {
                "name": "p",
                "type": "recovered-project",
                "memory_dir": str(tmp_path),
                "evidence_dir": None,
                "registered_at": "2026-01-01T00:00:00Z",
            }
        ],
    }
    reg_path.write_text(json.dumps(data), encoding="utf-8")
    registry = load_registry(reg_path)
    assert registry.projects[0].evidence_dir is None


# ---------------------------------------------------------------------------
# save_registry
# ---------------------------------------------------------------------------


def test_save_creates_parent_dirs(tmp_path: Path) -> None:
    reg_path = tmp_path / "deep" / "nested" / "registry.json"
    registry = ProjectRegistry(registry_path=reg_path)
    save_registry(registry)
    assert reg_path.exists()


def test_save_load_roundtrip(tmp_path: Path) -> None:
    reg_path = _reg(tmp_path)
    ev = tmp_path / "ev"
    mem = _mem(tmp_path)
    reg = ProjectRegistration(
        name="proj-a",
        project_type="recovered-project",
        memory_dir=mem,
        evidence_dir=ev,
        registered_at="2026-01-01T00:00:00Z",
    )
    registry = ProjectRegistry(registry_path=reg_path, projects=[reg])
    save_registry(registry)

    loaded = load_registry(reg_path)
    assert len(loaded.projects) == 1
    assert loaded.projects[0].name == "proj-a"
    assert loaded.projects[0].evidence_dir == ev


def test_save_updates_updated_at(tmp_path: Path) -> None:
    reg_path = _reg(tmp_path)
    registry = ProjectRegistry(
        registry_path=reg_path, updated_at="2020-01-01T00:00:00Z"
    )
    save_registry(registry)
    assert registry.updated_at != "2020-01-01T00:00:00Z"


# ---------------------------------------------------------------------------
# find_project
# ---------------------------------------------------------------------------


def test_find_project_found(tmp_path: Path) -> None:
    reg = ProjectRegistration(
        name="p", project_type="recovered-project", memory_dir=tmp_path
    )
    registry = ProjectRegistry(registry_path=_reg(tmp_path), projects=[reg])
    found = find_project(registry, "p")
    assert found is not None
    assert found.name == "p"


def test_find_project_not_found(tmp_path: Path) -> None:
    registry = ProjectRegistry(registry_path=_reg(tmp_path))
    assert find_project(registry, "missing") is None


def test_find_project_case_sensitive(tmp_path: Path) -> None:
    reg = ProjectRegistration(
        name="Proj", project_type="recovered-project", memory_dir=tmp_path
    )
    registry = ProjectRegistry(registry_path=_reg(tmp_path), projects=[reg])
    assert find_project(registry, "proj") is None
    assert find_project(registry, "Proj") is not None


# ---------------------------------------------------------------------------
# register_project
# ---------------------------------------------------------------------------


def test_register_project_new(tmp_path: Path) -> None:
    mem = _mem(tmp_path)
    reg = ProjectRegistration(
        name="proj-a", project_type="recovered-project", memory_dir=mem
    )
    updated = register_project(reg, _reg(tmp_path))
    assert len(updated.projects) == 1
    assert updated.projects[0].name == "proj-a"


def test_register_project_persisted(tmp_path: Path) -> None:
    mem = _mem(tmp_path)
    reg_path = _reg(tmp_path)
    reg = ProjectRegistration(
        name="proj-a", project_type="recovered-project", memory_dir=mem
    )
    register_project(reg, reg_path)
    loaded = load_registry(reg_path)
    assert len(loaded.projects) == 1


def test_register_project_duplicate_raises(tmp_path: Path) -> None:
    mem = _mem(tmp_path)
    reg = ProjectRegistration(
        name="proj-a", project_type="recovered-project", memory_dir=mem
    )
    register_project(reg, _reg(tmp_path))
    with pytest.raises(ValueError, match="already registered"):
        register_project(reg, _reg(tmp_path))


def test_register_project_overwrite_updates(tmp_path: Path) -> None:
    mem = _mem(tmp_path)
    reg_path = _reg(tmp_path)
    reg1 = ProjectRegistration(
        name="proj-a", project_type="recovered-project", memory_dir=mem
    )
    register_project(reg1, reg_path)
    ev = tmp_path / "ev"
    reg2 = ProjectRegistration(
        name="proj-a", project_type="audited-project", memory_dir=mem, evidence_dir=ev
    )
    register_project(reg2, reg_path, overwrite=True)
    loaded = load_registry(reg_path)
    assert len(loaded.projects) == 1
    assert loaded.projects[0].project_type == "audited-project"
    assert loaded.projects[0].evidence_dir == ev


def test_register_project_sorted(tmp_path: Path) -> None:
    mem = _mem(tmp_path)
    reg_path = _reg(tmp_path)
    for name in ("zzz", "aaa", "mmm"):
        r = ProjectRegistration(
            name=name, project_type="recovered-project", memory_dir=mem
        )
        register_project(r, reg_path)
    loaded = load_registry(reg_path)
    names = [p.name for p in loaded.projects]
    assert names == sorted(names)


def test_register_project_preserves_others(tmp_path: Path) -> None:
    mem = _mem(tmp_path)
    reg_path = _reg(tmp_path)
    r1 = ProjectRegistration(
        name="proj-a", project_type="recovered-project", memory_dir=mem
    )
    r2 = ProjectRegistration(
        name="proj-b", project_type="recovered-project", memory_dir=mem
    )
    register_project(r1, reg_path)
    register_project(r2, reg_path)
    loaded = load_registry(reg_path)
    names = {p.name for p in loaded.projects}
    assert "proj-a" in names
    assert "proj-b" in names


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------


def test_cli_register_basic(tmp_path: Path) -> None:
    mem = _mem(tmp_path)
    result = runner.invoke(
        app,
        [
            "project",
            "register",
            "--name",
            "my-proj",
            "--memory-dir",
            str(mem),
            "--registry",
            str(_reg(tmp_path)),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "my-proj" in result.output
    assert "Registered:" in result.output


def test_cli_register_creates_registry(tmp_path: Path) -> None:
    mem = _mem(tmp_path)
    reg_path = _reg(tmp_path)
    runner.invoke(
        app,
        [
            "project",
            "register",
            "--name",
            "my-proj",
            "--memory-dir",
            str(mem),
            "--registry",
            str(reg_path),
        ],
    )
    assert reg_path.exists()
    data = json.loads(reg_path.read_text())
    assert any(p["name"] == "my-proj" for p in data["projects"])


def test_cli_register_missing_memory_dir(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "project",
            "register",
            "--name",
            "my-proj",
            "--memory-dir",
            str(tmp_path / "no-such"),
            "--registry",
            str(_reg(tmp_path)),
        ],
    )
    assert result.exit_code == 1


def test_cli_register_duplicate_no_overwrite(tmp_path: Path) -> None:
    mem = _mem(tmp_path)
    args = [
        "project",
        "register",
        "--name",
        "my-proj",
        "--memory-dir",
        str(mem),
        "--registry",
        str(_reg(tmp_path)),
    ]
    runner.invoke(app, args)
    result = runner.invoke(app, args)
    assert result.exit_code == 1
    assert "already registered" in result.output


def test_cli_register_overwrite(tmp_path: Path) -> None:
    mem = _mem(tmp_path)
    reg_path = _reg(tmp_path)
    base_args = [
        "project",
        "register",
        "--name",
        "my-proj",
        "--memory-dir",
        str(mem),
        "--registry",
        str(reg_path),
    ]
    runner.invoke(app, base_args)
    result = runner.invoke(app, [*base_args, "--overwrite"])
    assert result.exit_code == 0, result.output


def test_cli_register_custom_registry(tmp_path: Path) -> None:
    mem = _mem(tmp_path)
    custom = tmp_path / "custom" / "reg.json"
    result = runner.invoke(
        app,
        [
            "project",
            "register",
            "--name",
            "my-proj",
            "--memory-dir",
            str(mem),
            "--registry",
            str(custom),
        ],
    )
    assert result.exit_code == 0, result.output
    assert custom.exists()


def test_cli_register_json_output(tmp_path: Path) -> None:
    mem = _mem(tmp_path)
    result = runner.invoke(
        app,
        [
            "project",
            "register",
            "--name",
            "my-proj",
            "--memory-dir",
            str(mem),
            "--registry",
            str(_reg(tmp_path)),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["name"] == "my-proj"
    assert payload["registered"] is True
    assert payload["total_projects"] == 1


def test_cli_register_type_stored(tmp_path: Path) -> None:
    mem = _mem(tmp_path)
    reg_path = _reg(tmp_path)
    result = runner.invoke(
        app,
        [
            "project",
            "register",
            "--name",
            "p",
            "--memory-dir",
            str(mem),
            "--type",
            "audited-project",
            "--registry",
            str(reg_path),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["type"] == "audited-project"


def test_cli_register_with_evidence_dir(tmp_path: Path) -> None:
    mem = _mem(tmp_path)
    ev = tmp_path / "evidence"
    ev.mkdir()
    result = runner.invoke(
        app,
        [
            "project",
            "register",
            "--name",
            "p",
            "--memory-dir",
            str(mem),
            "--evidence-dir",
            str(ev),
            "--registry",
            str(_reg(tmp_path)),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["evidence_dir"] == str(ev)


def test_cli_register_without_evidence_dir(tmp_path: Path) -> None:
    mem = _mem(tmp_path)
    result = runner.invoke(
        app,
        [
            "project",
            "register",
            "--name",
            "p",
            "--memory-dir",
            str(mem),
            "--registry",
            str(_reg(tmp_path)),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["evidence_dir"] is None


def test_cli_register_output_immutable(tmp_path: Path) -> None:
    mem = _mem(tmp_path)
    sentinel = mem / "sentinel.txt"
    sentinel.write_text("unchanged", encoding="utf-8")
    mtime_before = sentinel.stat().st_mtime
    runner.invoke(
        app,
        [
            "project",
            "register",
            "--name",
            "p",
            "--memory-dir",
            str(mem),
            "--registry",
            str(_reg(tmp_path)),
        ],
    )
    assert sentinel.stat().st_mtime == mtime_before


def test_cli_register_read_only_footer(tmp_path: Path) -> None:
    mem = _mem(tmp_path)
    result = runner.invoke(
        app,
        [
            "project",
            "register",
            "--name",
            "p",
            "--memory-dir",
            str(mem),
            "--registry",
            str(_reg(tmp_path)),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "read_only: true" in result.output
    assert "applied: false" in result.output
