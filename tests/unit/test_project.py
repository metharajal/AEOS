from pathlib import Path

from aeos.project.inspector import inspect_project


def test_inspect_full_project(tmp_path: Path) -> None:
    (tmp_path / "aeos.toml").write_text('[project]\nname = "test-project"\n')
    (tmp_path / "pyproject.toml").write_text("")
    (tmp_path / "README.md").write_text("")
    (tmp_path / "MANIFESTO.md").write_text("")
    (tmp_path / "CONSTITUTION.md").write_text("")
    (tmp_path / "governance").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text("")
    (tmp_path / ".git").mkdir()

    result = inspect_project(tmp_path)

    assert result.name == "test-project"
    assert result.aeos_toml is True
    assert result.pyproject_toml is True
    assert result.readme is True
    assert result.manifesto is True
    assert result.constitution is True
    assert result.governance is True
    assert result.docs is True
    assert result.src is True
    assert result.tests is True
    assert result.ci_yml is True
    assert result.git_present is True


def test_inspect_empty_project(tmp_path: Path) -> None:
    result = inspect_project(tmp_path)

    assert result.name == "(unknown)"
    assert result.aeos_toml is False
    assert result.pyproject_toml is False
    assert result.readme is False
    assert result.git_present is False
    assert result.remote_origin == ""


def test_inspect_reads_project_name(tmp_path: Path) -> None:
    (tmp_path / "aeos.toml").write_text('[project]\nname = "my-project"\n')

    result = inspect_project(tmp_path)

    assert result.name == "my-project"


def test_inspect_invalid_toml(tmp_path: Path) -> None:
    (tmp_path / "aeos.toml").write_text("not valid toml ][")

    result = inspect_project(tmp_path)

    assert result.name == "(unknown)"
