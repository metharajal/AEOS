import json
import shutil
from pathlib import Path
from typing import Annotated

import typer

from aeos.generators import GENERATORS
from aeos.onboarding import check_project
from aeos.project import inspect_project
from aeos.version import __version__

app = typer.Typer(add_completion=False)
project_app = typer.Typer(help="Project management commands.")
app.add_typer(project_app, name="project")

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

    project_name = project.name
    project.mkdir()
    created = generator(project, project_name)

    typer.echo(f"Project '{project_name}' initialized.")
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


@project_app.command("inspect")
def project_inspect(
    path: str = typer.Option(".", "--path", "-p", help="Path to inspect."),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Inspect an AEOS project and display a summary."""
    project = Path(path).resolve()
    result = inspect_project(project)

    if as_json:
        payload = {
            "project": {"name": result.name, "path": str(result.path)},
            "checks": {
                "configuration": {
                    "aeos.toml": result.aeos_toml,
                    "pyproject.toml": result.pyproject_toml,
                },
                "documentation": {
                    "README.md": result.readme,
                    "MANIFESTO.md": result.manifesto,
                    "CONSTITUTION.md": result.constitution,
                },
                "governance": {"governance/": result.governance},
                "structure": {
                    "docs/": result.docs,
                    "src/": result.src,
                    "tests/": result.tests,
                },
                "ci": {".github/workflows/ci.yml": result.ci_yml},
                "git": {
                    "repository": result.git_present,
                    "remote_origin": result.remote_origin,
                },
            },
        }
        typer.echo(json.dumps(payload, indent=2))
        return

    def _status(found: bool) -> str:
        return "OK" if found else "MISSING"

    def _line(label: str, found: bool) -> None:
        typer.echo(f"{label:<30} {_status(found)}")

    typer.echo(f"Project: {result.name}")
    typer.echo(f"Path:    {result.path}")
    typer.echo("")
    typer.echo("--- Configuration ---")
    _line("aeos.toml", result.aeos_toml)
    _line("pyproject.toml", result.pyproject_toml)
    typer.echo("")
    typer.echo("--- Documentation ---")
    _line("README.md", result.readme)
    _line("MANIFESTO.md", result.manifesto)
    _line("CONSTITUTION.md", result.constitution)
    typer.echo("")
    typer.echo("--- Governance ---")
    _line("governance/", result.governance)
    typer.echo("")
    typer.echo("--- Structure ---")
    _line("docs/", result.docs)
    _line("src/", result.src)
    _line("tests/", result.tests)
    typer.echo("")
    typer.echo("--- CI ---")
    _line(".github/workflows/ci.yml", result.ci_yml)
    typer.echo("")
    typer.echo("--- Git ---")
    _line("repository", result.git_present)
    remote = result.remote_origin if result.remote_origin else "(none)"
    typer.echo(f"{'remote origin':<30} {remote}")
