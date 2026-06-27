import json
import shutil
from pathlib import Path
from typing import Annotated

import typer

from aeos.ai import AiRouterError, ask_ai, read_ai_config, run_ai_doctor
from aeos.generators import GENERATORS
from aeos.onboarding import check_project
from aeos.project import inspect_project
from aeos.sovereignty import run_sovereignty_check
from aeos.version import __version__

app = typer.Typer(add_completion=False)
project_app = typer.Typer(help="Project management commands.")
ai_app = typer.Typer(help="AI configuration and orchestration commands.")
sovereignty_app = typer.Typer(help="Sovereignty audit commands.")
app.add_typer(project_app, name="project")
app.add_typer(ai_app, name="ai")
app.add_typer(sovereignty_app, name="sovereignty")

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
    path: str = typer.Argument(".", help="Path to the project to onboard."),
    check: bool = typer.Option(False, "--check", help="Run in check mode (read-only)."),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
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
    missing_items = [item for item, found in results if not found]

    if as_json:
        payload = {
            "path": str(project.resolve()),
            "ok": len(missing_items) == 0,
            "items": {item: found for item, found in results},
            "missing": missing_items,
        }
        typer.echo(json.dumps(payload, indent=2))
        if missing_items:
            raise typer.Exit(code=1)
        return

    for item, found in results:
        status = "OK     " if found else "MISSING"
        typer.echo(f"{item:<30} {status}")

    if missing_items:
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


@ai_app.command("config")
def ai_config() -> None:
    """Display the effective AI configuration for the current project."""
    config = read_ai_config(Path("."))

    if config is None:
        typer.echo(
            "Error: 'aeos.toml' not found or invalid."
            " Run 'aeos init' to create a project.",
            err=True,
        )
        raise typer.Exit(code=1)

    def _line(label: str, value: str) -> None:
        typer.echo(f"{label:<30} {value}")

    typer.echo("AI Configuration")
    typer.echo(f"Source: {config.source}")
    typer.echo("")
    typer.echo("--- General ---")
    _line("mode", config.mode)
    _line("frontier_allowed", str(config.frontier_allowed).lower())
    _line("require_human_approval", str(config.require_human_approval).lower())
    typer.echo("")
    typer.echo("--- Local ---")
    _line("provider", config.local.provider)
    _line("base_url", config.local.base_url)
    _line("default_model", config.local.default_model)
    typer.echo("")
    typer.echo("--- Frontier ---")
    _line("provider", config.frontier.provider)
    _line("base_url_env", config.frontier.base_url_env)
    _line("api_key_env", config.frontier.api_key_env)
    _line("default_model_env", config.frontier.default_model_env)


@ai_app.command("doctor")
def ai_doctor() -> None:
    """Check the AI environment for the current project."""
    result = run_ai_doctor(Path("."))

    def _line(label: str, value: str) -> None:
        typer.echo(f"{label:<30} {value}")

    def _env_line(label: str, var_name: str, present: bool) -> None:
        status = "PRESENT" if present else "MISSING"
        typer.echo(f"{label:<30} {var_name:<30} {status}")

    typer.echo("AI Doctor")
    typer.echo("")
    typer.echo("--- Configuration ---")
    _line("aeos.toml", "OK" if result.config_ok else "ERROR")

    if not result.config_ok:
        typer.echo("")
        typer.echo("--- Result ---")
        _line("status", result.status)
        raise typer.Exit(code=1)

    _line("mode", result.mode)
    _line("frontier_allowed", str(result.frontier_allowed).lower())
    _line("require_human_approval", str(result.require_human_approval).lower())
    typer.echo("")
    typer.echo("--- Local AI ---")
    _line("provider", result.local.provider)
    _line("base_url", result.local.base_url)
    if result.local.endpoint_ok:
        endpoint_status = "OK"
    else:
        endpoint_status = f"ERROR: {result.local.endpoint_error}"
    _line("endpoint", endpoint_status)
    _line("default_model", result.local.default_model)
    typer.echo("")
    typer.echo("--- Frontier AI ---")
    _line("provider", result.frontier.provider)
    _env_line(
        "base_url_env",
        result.frontier.base_url_env,
        result.frontier.base_url_env_present,
    )
    _env_line(
        "api_key_env",
        result.frontier.api_key_env,
        result.frontier.api_key_env_present,
    )
    _env_line(
        "default_model_env",
        result.frontier.default_model_env,
        result.frontier.default_model_env_present,
    )
    typer.echo("")
    typer.echo("--- Result ---")
    _line("status", result.status)

    if result.status == "ERROR":
        raise typer.Exit(code=1)


@ai_app.command("ask")
def ai_ask(
    prompt: str = typer.Argument(..., help="Prompt to send to the AI provider."),
    provider: str = typer.Option(
        "local", "--provider", help="AI provider: local, frontier, auto."
    ),
    timeout: int = typer.Option(30, "--timeout", help="Request timeout in seconds."),
) -> None:
    """Send a prompt to the configured AI provider (local, frontier, or auto)."""
    if not prompt.strip():
        typer.echo("Error: prompt cannot be empty.", err=True)
        raise typer.Exit(code=1)

    config = read_ai_config(Path("."))
    if config is None:
        typer.echo(
            "Error: 'aeos.toml' not found or invalid."
            " Run 'aeos init' to create a project.",
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        response = ask_ai(prompt, config, provider=provider, timeout=timeout)
    except AiRouterError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from None

    if provider == "auto":
        typer.echo(f"Used provider: {response.provider_used}")
    typer.echo(response.text)


@sovereignty_app.command("check")
def sovereignty_check(
    path: str = typer.Option(".", "--path", "-p", help="Path to audit."),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Audit a project for sovereignty and external dependency risks."""
    project = Path(path).resolve()
    if not project.is_dir():
        typer.echo(f"Error: '{path}' does not exist.", err=True)
        raise typer.Exit(code=1)

    result = run_sovereignty_check(project)

    if as_json:
        payload = {
            "path": str(result.path),
            "status": result.status,
            "findings": [
                {
                    "category": f.category,
                    "severity": f.severity,
                    "message": f.message,
                    "location": f.location,
                    "recommendation": f.recommendation,
                }
                for f in result.findings
            ],
        }
        typer.echo(json.dumps(payload, indent=2))
        if result.status == "ERROR":
            raise typer.Exit(code=1)
        return

    typer.echo("Sovereignty Check")
    typer.echo(f"Path:   {result.path}")
    typer.echo(f"Status: {result.status}")

    if not result.findings:
        typer.echo("")
        typer.echo("No issues found.")
        return

    typer.echo(f"\nFindings ({len(result.findings)}):\n")
    for f in result.findings:
        typer.echo(f"  [{f.category}] {f.severity} — {f.message}")
        typer.echo(f"    Location:       {f.location}")
        typer.echo(f"    Recommendation: {f.recommendation}")
        typer.echo("")

    if result.status == "ERROR":
        raise typer.Exit(code=1)
