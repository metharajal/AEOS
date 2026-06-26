from pathlib import Path

from aeos.version import __version__


def write_common_files(project: Path, name: str) -> None:
    (project / "README.md").write_text(f"# {name}\n\nGenerated with AEOS.\n")
    (project / "aeos.toml").write_text(
        f'[project]\nname = "{name}"\naeos_version = "{__version__}"\n'
    )
    (project / ".gitignore").write_text(".venv/\n__pycache__/\n.DS_Store\n")
