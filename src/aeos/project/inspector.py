import configparser
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class InspectResult:
    path: Path
    name: str
    aeos_toml: bool
    pyproject_toml: bool
    readme: bool
    manifesto: bool
    constitution: bool
    governance: bool
    docs: bool
    src: bool
    tests: bool
    ci_yml: bool
    git_present: bool
    remote_origin: str


def _read_project_name(path: Path) -> str:
    toml_path = path / "aeos.toml"
    if not toml_path.is_file():
        return "(unknown)"
    try:
        data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
        project = data.get("project")
        if not isinstance(project, dict):
            return "(unknown)"
        name = project.get("name")
        if not isinstance(name, str):
            return "(unknown)"
        return name
    except tomllib.TOMLDecodeError:
        return "(unknown)"


def _get_remote_origin(path: Path) -> str:
    git_config = path / ".git" / "config"
    if not git_config.is_file():
        return ""
    try:
        config = configparser.ConfigParser()
        config.read(git_config)
        return config.get('remote "origin"', "url", fallback="")
    except configparser.Error:
        return ""


def inspect_project(path: Path) -> InspectResult:
    return InspectResult(
        path=path,
        name=_read_project_name(path),
        aeos_toml=(path / "aeos.toml").is_file(),
        pyproject_toml=(path / "pyproject.toml").is_file(),
        readme=(path / "README.md").is_file(),
        manifesto=(path / "MANIFESTO.md").is_file(),
        constitution=(path / "CONSTITUTION.md").is_file(),
        governance=(path / "governance").is_dir(),
        docs=(path / "docs").is_dir(),
        src=(path / "src").is_dir(),
        tests=(path / "tests").is_dir(),
        ci_yml=(path / ".github" / "workflows" / "ci.yml").is_file(),
        git_present=(path / ".git").is_dir(),
        remote_origin=_get_remote_origin(path),
    )
