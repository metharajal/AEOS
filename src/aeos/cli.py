import shutil
from pathlib import Path
from typing import Annotated

import typer

from aeos.generators import GENERATORS
from aeos.onboarding import check_project
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
def init(
    name: str = typer.Argument(..., help="Name of the new project."),
    project_type: str = typer.Option("basic", "--type", "-t", help="Project type."),
) -> None:
    """Initialize a new AEOS-compliant project."""
    project = Path(name)

    if project.exists():
        typer.echo(f"Error: '{name}' already exists.", err=True)
        raise typer.Exit(code=1)

    generator = GENERATORS.get(project_type)
    if generator is None:
        available = ", ".join(GENERATORS)
        typer.echo(
            f"Error: unknown type '{project_type}'. Available: {available}.",
            err=True,
        )
        raise typer.Exit(code=1)

    project.mkdir()
    created = generator(project, name)

    typer.echo(f"Project '{name}' initialized.")
    for item in created:
        typer.echo(f"  {item}")


@app.command()
def onboard(
    path: str = typer.Argument(..., help="Path to the project to onboard."),
    check: bool = typer.Option(False, "--check", help="Run in check mode (read-only)."),
) -> None:
    """Onboard an existing project into AEOS."""
    if not check:
        typer.echo(
            "Error: --check is required. Other modes are not available yet.",
            err=True,
        )
        raise typer.Exit(code=1)

    project = Path(path)
    if not project.exists():
        typer.echo(f"Error: '{path}' does not exist.", err=True)
        raise typer.Exit(code=1)

    results = check_project(project)
    missing = False
    for item, found in results:
        status = "OK     " if found else "MISSING"
        typer.echo(f"{item:<30} {status}")
        if not found:
            missing = True

    if missing:
        raise typer.Exit(code=1)
