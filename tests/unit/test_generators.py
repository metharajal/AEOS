from pathlib import Path

from aeos.generators.basic import generate


def test_basic_generator_creates_structure(tmp_path: Path) -> None:
    name = "test-project"
    project = tmp_path / name
    project.mkdir()

    created = generate(project, name)

    readme = (project / "README.md").read_text()
    assert readme == f"# {name}\n\nGenerated with AEOS.\n"
    assert ".venv/" in (project / ".gitignore").read_text()
    assert (project / "aeos.toml").exists()
    for sub in [
        "governance/adr",
        "governance/rfc",
        "governance/dec",
        "governance/standards",
        "governance/playbooks",
        "docs",
        "src",
        "tests",
    ]:
        assert (project / sub).is_dir()
    assert f"{name}/" in created
    assert len(created) > 0
