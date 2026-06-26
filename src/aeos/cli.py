import shutil
from pathlib import Path
from typing import Annotated

import typer

from aeos.version import __version__

app = typer.Typer(add_completion=False)

REQUIRED_TOOLS = ["python", "uv", "git", "docker", "node", "pnpm", "gh", "code"]


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=_version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = False,
) -> None:
    pass


@app.command()
def doctor() -> None:
    """Check that required developer tools are available."""
    missing = False

    for tool in REQUIRED_TOOLS:
        found = shutil.which(tool) is not None
        status = "OK     " if found else "MISSING"
        typer.echo(f"{tool:<10} {status}")
        if not found:
            missing = True

    if missing:
        raise typer.Exit(code=1)


@app.command()
def init(name: str = typer.Argument(..., help="Name of the new project.")) -> None:
    """Initialize a new AEOS-compliant project."""
    project = Path(name)

    if project.exists():
        typer.echo(f"Error: '{name}' already exists.", err=True)
        raise typer.Exit(code=1)

    dirs = [
        project / "governance" / "adr",
        project / "governance" / "rfc",
        project / "governance" / "dec",
        project / "governance" / "standards",
        project / "governance" / "playbooks",
        project / "docs",
        project / "src",
        project / "tests",
    ]
    for d in dirs:
        d.mkdir(parents=True)

    (project / "README.md").write_text(f"# {name}\n\nGenerated with AEOS.\n")
    (project / "aeos.toml").write_text(
        f'[project]\nname = "{name}"\naeos_version = "{__version__}"\n'
    )
    (project / ".gitignore").write_text(".venv/\n__pycache__/\n.DS_Store\n")

    typer.echo(f"Project '{name}' initialized.")
    typer.echo(f"  {name}/")
    typer.echo(f"  {name}/README.md")
    typer.echo(f"  {name}/aeos.toml")
    typer.echo(f"  {name}/.gitignore")
    typer.echo(f"  {name}/governance/")
    typer.echo(f"  {name}/docs/")
    typer.echo(f"  {name}/src/")
    typer.echo(f"  {name}/tests/")
