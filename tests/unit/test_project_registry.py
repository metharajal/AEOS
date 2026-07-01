"""Unit tests for aeos.project.registry and the project CLI sub-commands."""

from __future__ import annotations

import json
from pathlib import Path

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
    mem.mkdir(exist_ok=True)
    return mem


def _reg(tmp_path: Path) -> Path:
    return tmp_path / "registry.json"


def _make_reg(
    tmp_path: Path,
    name: str = "proj-a",
    project_type: str = "recovered-project",
    evidence_dir: Path | None = None,
) -> ProjectRegistration:
    return ProjectRegistration(
        name=name,
        project_type=project_type,
        memory_dir=_mem(tmp_path),
        evidence_dir=evidence_dir,
    )


# ---------------------------------------------------------------------------
# ProjectRegistration dataclass
# ---------------------------------------------------------------------------


def test_registration_registered_at_auto(tmp_path: Path) -> None:
    reg = ProjectRegistration(
        name="p", project_type="recovered-project", memory_dir=tmp_path
    )
    assert reg.registered_at != ""
    assert "T" in reg.registered_at


def test_registration_last_seen_at_auto(tmp_path: Path) -> None:
    reg = ProjectRegistration(
        name="p", project_type="recovered-project", memory_dir=tmp_path
    )
    assert reg.last_seen_at != ""
    assert "T" in reg.last_seen_at


def test_registration_custom_registered_at_preserved(tmp_path: Path) -> None:
    reg = ProjectRegistration(
        name="p",
        project_type="recovered-project",
        memory_dir=tmp_path,
        registered_at="2026-01-01T00:00:00Z",
    )
    assert reg.registered_at == "2026-01-01T00:00:00Z"


def test_registration_defaults_local_only_read_only(tmp_path: Path) -> None:
    reg = ProjectRegistration(
        name="p", project_type="recovered-project", memory_dir=tmp_path
    )
    assert reg.local_only is True
    assert reg.read_only is True


def test_registration_no_evidence_dir(tmp_path: Path) -> None:
    reg = ProjectRegistration(
        name="p", project_type="recovered-project", memory_dir=tmp_path
    )
    assert reg.evidence_dir is None


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
                "last_seen_at": "2026-01-01T00:00:00Z",
                "local_only": True,
                "read_only": True,
            }
        ],
    }
    reg_path.write_text(json.dumps(data), encoding="utf-8")
    registry = load_registry(reg_path)
    assert len(registry.projects) == 1
    assert registry.projects[0].name == "proj-a"
    assert registry.projects[0].local_only is True


def test_load_registry_evidence_dir_none_roundtrip(tmp_path: Path) -> None:
    reg_path = _reg(tmp_path)
    data = {
        "projects": [
            {
                "name": "p",
                "type": "recovered-project",
                "memory_dir": str(tmp_path),
                "evidence_dir": None,
                "registered_at": "2026-01-01T00:00:00Z",
                "last_seen_at": "2026-01-01T00:00:00Z",
                "local_only": True,
                "read_only": True,
            }
        ]
    }
    reg_path.write_text(json.dumps(data), encoding="utf-8")
    assert load_registry(reg_path).projects[0].evidence_dir is None


# ---------------------------------------------------------------------------
# save_registry
# ---------------------------------------------------------------------------


def test_save_creates_parent_dirs(tmp_path: Path) -> None:
    reg_path = tmp_path / "deep" / "nested" / "registry.json"
    save_registry(ProjectRegistry(registry_path=reg_path))
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
    save_registry(ProjectRegistry(registry_path=reg_path, projects=[reg]))
    loaded = load_registry(reg_path)
    assert loaded.projects[0].name == "proj-a"
    assert loaded.projects[0].evidence_dir == ev
    assert loaded.projects[0].local_only is True
    assert loaded.projects[0].read_only is True


def test_save_writes_local_only_read_only_at_root(tmp_path: Path) -> None:
    reg_path = _reg(tmp_path)
    save_registry(ProjectRegistry(registry_path=reg_path))
    data = json.loads(reg_path.read_text())
    assert data["local_only"] is True
    assert data["read_only"] is True


# ---------------------------------------------------------------------------
# find_project
# ---------------------------------------------------------------------------


def test_find_project_found(tmp_path: Path) -> None:
    reg = ProjectRegistration(
        name="p", project_type="recovered-project", memory_dir=tmp_path
    )
    registry = ProjectRegistry(registry_path=_reg(tmp_path), projects=[reg])
    assert find_project(registry, "p") is not None


def test_find_project_not_found(tmp_path: Path) -> None:
    assert find_project(ProjectRegistry(registry_path=_reg(tmp_path)), "x") is None


def test_find_project_case_sensitive(tmp_path: Path) -> None:
    reg = ProjectRegistration(
        name="Proj", project_type="recovered-project", memory_dir=tmp_path
    )
    registry = ProjectRegistry(registry_path=_reg(tmp_path), projects=[reg])
    assert find_project(registry, "proj") is None
    assert find_project(registry, "Proj") is not None


# ---------------------------------------------------------------------------
# register_project (upsert)
# ---------------------------------------------------------------------------


def test_register_project_new(tmp_path: Path) -> None:
    r, created = register_project(_make_reg(tmp_path), _reg(tmp_path))
    assert created is True
    assert len(r.projects) == 1


def test_register_project_persisted(tmp_path: Path) -> None:
    reg_path = _reg(tmp_path)
    register_project(_make_reg(tmp_path), reg_path)
    assert len(load_registry(reg_path).projects) == 1


def test_register_project_upsert_no_error(tmp_path: Path) -> None:
    reg_path = _reg(tmp_path)
    register_project(_make_reg(tmp_path), reg_path)
    _, created = register_project(_make_reg(tmp_path), reg_path)
    assert created is False


def test_register_project_upsert_updates_fields(tmp_path: Path) -> None:
    reg_path = _reg(tmp_path)
    mem = _mem(tmp_path)
    register_project(
        ProjectRegistration(name="p", project_type="recovered-project", memory_dir=mem),
        reg_path,
    )
    ev = tmp_path / "ev"
    register_project(
        ProjectRegistration(
            name="p", project_type="audited-project", memory_dir=mem, evidence_dir=ev
        ),
        reg_path,
    )
    loaded = load_registry(reg_path)
    assert loaded.projects[0].project_type == "audited-project"
    assert loaded.projects[0].evidence_dir == ev


def test_register_project_upsert_preserves_registered_at(tmp_path: Path) -> None:
    reg_path = _reg(tmp_path)
    mem = _mem(tmp_path)
    first = ProjectRegistration(
        name="p",
        project_type="recovered-project",
        memory_dir=mem,
        registered_at="2026-01-01T00:00:00Z",
    )
    register_project(first, reg_path)
    register_project(
        ProjectRegistration(name="p", project_type="audited-project", memory_dir=mem),
        reg_path,
    )
    loaded = load_registry(reg_path)
    assert loaded.projects[0].registered_at == "2026-01-01T00:00:00Z"


def test_register_project_sorted(tmp_path: Path) -> None:
    reg_path = _reg(tmp_path)
    mem = _mem(tmp_path)
    for n in ("zzz", "aaa", "mmm"):
        r = ProjectRegistration(
            name=n, project_type="recovered-project", memory_dir=mem
        )
        register_project(r, reg_path)
    names = [p.name for p in load_registry(reg_path).projects]
    assert names == sorted(names)


def test_register_project_preserves_others(tmp_path: Path) -> None:
    reg_path = _reg(tmp_path)
    mem = _mem(tmp_path)
    for n in ("proj-a", "proj-b"):
        r = ProjectRegistration(
            name=n, project_type="recovered-project", memory_dir=mem
        )
        register_project(r, reg_path)
    names = {p.name for p in load_registry(reg_path).projects}
    assert {"proj-a", "proj-b"} == names


# ---------------------------------------------------------------------------
# CLI: aeos project register
# ---------------------------------------------------------------------------


def test_cli_register_basic(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "project",
            "register",
            "--name",
            "my-proj",
            "--memory-dir",
            str(_mem(tmp_path)),
            "--registry",
            str(_reg(tmp_path)),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "my-proj" in result.output
    assert "read_only: true" in result.output


def test_cli_register_creates_registry_file(tmp_path: Path) -> None:
    reg_path = _reg(tmp_path)
    runner.invoke(
        app,
        [
            "project",
            "register",
            "--name",
            "p",
            "--memory-dir",
            str(_mem(tmp_path)),
            "--registry",
            str(reg_path),
        ],
    )
    assert reg_path.exists()
    assert json.loads(reg_path.read_text())["local_only"] is True


def test_cli_register_missing_memory_dir(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "project",
            "register",
            "--name",
            "p",
            "--memory-dir",
            str(tmp_path / "no-such"),
            "--registry",
            str(_reg(tmp_path)),
        ],
    )
    assert result.exit_code == 1


def test_cli_register_missing_evidence_dir(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "project",
            "register",
            "--name",
            "p",
            "--memory-dir",
            str(_mem(tmp_path)),
            "--evidence-dir",
            str(tmp_path / "no-such-evidence"),
            "--registry",
            str(_reg(tmp_path)),
        ],
    )
    assert result.exit_code == 1
    assert "evidence" in result.output.lower()


def test_cli_register_upsert_no_error(tmp_path: Path) -> None:
    args = [
        "project",
        "register",
        "--name",
        "p",
        "--memory-dir",
        str(_mem(tmp_path)),
        "--registry",
        str(_reg(tmp_path)),
    ]
    runner.invoke(app, args)
    result = runner.invoke(app, args)
    assert result.exit_code == 0
    assert "Updated" in result.output


def test_cli_register_json_output(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "project",
            "register",
            "--name",
            "p",
            "--memory-dir",
            str(_mem(tmp_path)),
            "--registry",
            str(_reg(tmp_path)),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["name"] == "p"
    assert payload["local_only"] is True
    assert payload["read_only"] is True
    assert payload["created"] is True


# ---------------------------------------------------------------------------
# CLI: aeos project list
# ---------------------------------------------------------------------------


def test_cli_list_missing_registry(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["project", "list", "--registry", str(_reg(tmp_path))],
    )
    assert result.exit_code == 0
    assert "not found" in result.output.lower() or "not" in result.output


def test_cli_list_empty_registry(tmp_path: Path) -> None:
    save_registry(ProjectRegistry(registry_path=_reg(tmp_path)))
    result = runner.invoke(
        app,
        ["project", "list", "--registry", str(_reg(tmp_path))],
    )
    assert result.exit_code == 0
    assert "No projects" in result.output


def test_cli_list_shows_project(tmp_path: Path) -> None:
    runner.invoke(
        app,
        [
            "project",
            "register",
            "--name",
            "ma-mairie",
            "--memory-dir",
            str(_mem(tmp_path)),
            "--registry",
            str(_reg(tmp_path)),
        ],
    )
    result = runner.invoke(
        app,
        ["project", "list", "--registry", str(_reg(tmp_path))],
    )
    assert result.exit_code == 0
    assert "ma-mairie" in result.output


def test_cli_list_json(tmp_path: Path) -> None:
    runner.invoke(
        app,
        [
            "project",
            "register",
            "--name",
            "p",
            "--memory-dir",
            str(_mem(tmp_path)),
            "--registry",
            str(_reg(tmp_path)),
        ],
    )
    result = runner.invoke(
        app,
        ["project", "list", "--registry", str(_reg(tmp_path)), "--json"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["total"] == 1
    assert payload["local_only"] is True
    assert payload["projects"][0]["name"] == "p"


def test_cli_list_multiple_projects(tmp_path: Path) -> None:
    mem = _mem(tmp_path)
    for n in ("proj-b", "proj-a"):
        runner.invoke(
            app,
            [
                "project",
                "register",
                "--name",
                n,
                "--memory-dir",
                str(mem),
                "--registry",
                str(_reg(tmp_path)),
            ],
        )
    result = runner.invoke(
        app,
        ["project", "list", "--registry", str(_reg(tmp_path))],
    )
    assert result.exit_code == 0
    assert "proj-a" in result.output
    assert "proj-b" in result.output
    assert result.output.index("proj-a") < result.output.index("proj-b")


# ---------------------------------------------------------------------------
# CLI: aeos project show
# ---------------------------------------------------------------------------


def test_cli_show_basic(tmp_path: Path) -> None:
    runner.invoke(
        app,
        [
            "project",
            "register",
            "--name",
            "ma-proj",
            "--memory-dir",
            str(_mem(tmp_path)),
            "--type",
            "recovered-project",
            "--registry",
            str(_reg(tmp_path)),
        ],
    )
    result = runner.invoke(
        app,
        ["project", "show", "--name", "ma-proj", "--registry", str(_reg(tmp_path))],
    )
    assert result.exit_code == 0
    assert "ma-proj" in result.output
    assert "recovered-project" in result.output
    assert "read_only: true" in result.output


def test_cli_show_not_found(tmp_path: Path) -> None:
    save_registry(ProjectRegistry(registry_path=_reg(tmp_path)))
    result = runner.invoke(
        app,
        ["project", "show", "--name", "no-such", "--registry", str(_reg(tmp_path))],
    )
    assert result.exit_code == 1


def test_cli_show_all_fields(tmp_path: Path) -> None:
    ev = tmp_path / "ev"
    ev.mkdir()
    runner.invoke(
        app,
        [
            "project",
            "register",
            "--name",
            "p",
            "--memory-dir",
            str(_mem(tmp_path)),
            "--evidence-dir",
            str(ev),
            "--registry",
            str(_reg(tmp_path)),
        ],
    )
    result = runner.invoke(
        app,
        ["project", "show", "--name", "p", "--registry", str(_reg(tmp_path))],
    )
    assert "Memory:" in result.output
    assert "Evidence:" in result.output
    assert "Registered:" in result.output
    assert "Last seen:" in result.output
    assert "Local only:   true" in result.output
    assert "Read only:    true" in result.output


def test_cli_show_json(tmp_path: Path) -> None:
    runner.invoke(
        app,
        [
            "project",
            "register",
            "--name",
            "p",
            "--memory-dir",
            str(_mem(tmp_path)),
            "--registry",
            str(_reg(tmp_path)),
        ],
    )
    result = runner.invoke(
        app,
        [
            "project",
            "show",
            "--name",
            "p",
            "--registry",
            str(_reg(tmp_path)),
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["name"] == "p"
    assert payload["local_only"] is True
    assert payload["read_only"] is True
    assert "registered_at" in payload
    assert "last_seen_at" in payload
