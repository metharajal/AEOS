import json
import shutil
from pathlib import Path
from typing import Annotated

import typer

from aeos.ai import AiRouterError, ask_ai, read_ai_config, run_ai_doctor
from aeos.generators import GENERATORS
from aeos.onboarding import check_project
from aeos.project import inspect_project
from aeos.providers.supabase import (
    run_rls_generate,
    run_rls_harden,
    run_rls_inspect,
    run_rls_plan,
    run_rls_review,
    run_rls_review_from_result,
    run_supabase_check,
)
from aeos.reclaim import run_reclaim_harden, run_reclaim_inspect
from aeos.reclaim.hardener import build_harden_report
from aeos.report import generate_report
from aeos.security import run_security_check as run_sec_check
from aeos.sovereignty import run_sovereignty_check
from aeos.version import __version__

app = typer.Typer(add_completion=False)
project_app = typer.Typer(help="Project management commands.")
ai_app = typer.Typer(help="AI configuration and orchestration commands.")
sovereignty_app = typer.Typer(help="Sovereignty audit commands.")
security_app = typer.Typer(help="Security audit commands.")
supabase_app = typer.Typer(help="Supabase integration audit and remediation.")
supabase_rls_app = typer.Typer(help="Supabase RLS policy inspection.")
reclaim_app = typer.Typer(help="Project reclaim and sovereignty analysis.")
reclaim_recovery_app = typer.Typer(help="Recovery planning commands.")
reclaim_stage_app = typer.Typer(help="Recovery stage model commands.")
reclaim_evidence_app = typer.Typer(help="Recovery evidence engine commands.")
memory_app = typer.Typer(help="Memory Layer — read and inspect local audit records.")
build_app = typer.Typer(help="Build Rail — plan and scaffold AEOS-native projects.")
ui_app = typer.Typer(help="UI commands — generate static dashboards.")
workspace_app = typer.Typer(
    help="Workspace commands — generate full project workspaces."
)
app.add_typer(project_app, name="project")
app.add_typer(ai_app, name="ai")
app.add_typer(sovereignty_app, name="sovereignty")
app.add_typer(security_app, name="security")
app.add_typer(supabase_app, name="supabase")
supabase_app.add_typer(supabase_rls_app, name="rls")
app.add_typer(reclaim_app, name="reclaim")
reclaim_app.add_typer(reclaim_recovery_app, name="recovery")
reclaim_app.add_typer(reclaim_stage_app, name="stage")
reclaim_app.add_typer(reclaim_evidence_app, name="evidence")
app.add_typer(memory_app, name="memory")
app.add_typer(build_app, name="build")
app.add_typer(ui_app, name="ui")
app.add_typer(workspace_app, name="workspace")

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
    path: str = typer.Option(".", "--path", "-p", help="Path to audit."),
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

    project = Path(path).resolve()
    if not project.is_dir():
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


# ---------------------------------------------------------------------------
# project register
# ---------------------------------------------------------------------------


@project_app.command("register")
def project_register(
    name: str = typer.Option(..., "--name", help="Project name."),
    memory_dir: str = typer.Option(
        ..., "--memory-dir", help="Path to the project's local memory directory."
    ),
    evidence_dir: str = typer.Option(
        "",
        "--evidence-dir",
        help="Path to the project's evidence output directory (optional).",
    ),
    project_type: str = typer.Option(
        "recovered-project",
        "--type",
        "-t",
        help="Project type (e.g. recovered-project, audited-project).",
    ),
    registry: str = typer.Option(
        "",
        "--registry",
        help="Registry file path (default: ~/.aeos/projects.json).",
    ),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Register or update a project in the local AEOS project registry."""
    from aeos.project.registry import (
        DEFAULT_REGISTRY,
        ProjectRegistration,
    )
    from aeos.project.registry import (
        register_project as _register,
    )

    mem_path = Path(memory_dir)
    if not mem_path.exists():
        typer.echo(f"Error: memory directory '{memory_dir}' does not exist.", err=True)
        raise typer.Exit(code=1)

    ev_path: Path | None = None
    if evidence_dir:
        ev_path = Path(evidence_dir)
        if not ev_path.exists():
            typer.echo(
                f"Error: evidence directory '{evidence_dir}' does not exist.", err=True
            )
            raise typer.Exit(code=1)

    reg_path = Path(registry) if registry else DEFAULT_REGISTRY

    registration = ProjectRegistration(
        name=name,
        project_type=project_type,
        memory_dir=mem_path,
        evidence_dir=ev_path,
    )

    updated, created = _register(registration, reg_path)

    if as_json:
        payload: dict[str, object] = {
            "registered": True,
            "created": created,
            "name": registration.name,
            "type": registration.project_type,
            "memory_dir": str(registration.memory_dir),
            "evidence_dir": (
                str(registration.evidence_dir)
                if registration.evidence_dir is not None
                else None
            ),
            "registered_at": registration.registered_at,
            "last_seen_at": registration.last_seen_at,
            "local_only": registration.local_only,
            "read_only": registration.read_only,
            "registry": str(reg_path),
            "total_projects": len(updated.projects),
        }
        typer.echo(json.dumps(payload, indent=2))
        return

    action = "Registered" if created else "Updated"
    typer.echo(f"{action}:     {name}")
    typer.echo(f"Type:         {project_type}")
    typer.echo(f"Memory:       {mem_path}")
    if ev_path is not None:
        typer.echo(f"Evidence:     {ev_path}")
    typer.echo(f"Last seen:    {registration.last_seen_at}")
    typer.echo(f"Registry:     {reg_path}")
    typer.echo(f"Total:        {len(updated.projects)} project(s) in registry")
    typer.echo("  read_only: true · applied: false")


# ---------------------------------------------------------------------------
# project list
# ---------------------------------------------------------------------------


@project_app.command("list")
def project_list(
    registry: str = typer.Option(
        "",
        "--registry",
        help="Registry file path (default: ~/.aeos/projects.json).",
    ),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List all projects in the local AEOS project registry."""
    from aeos.project.registry import DEFAULT_REGISTRY, load_registry

    reg_path = Path(registry) if registry else DEFAULT_REGISTRY

    if not reg_path.exists():
        if as_json:
            typer.echo(
                json.dumps(
                    {
                        "registry": str(reg_path),
                        "projects": [],
                        "total": 0,
                        "local_only": True,
                        "read_only": True,
                    },
                    indent=2,
                )
            )
            return
        typer.echo(f"Registry not found: {reg_path}")
        typer.echo("  Run 'aeos project register' to create it.")
        typer.echo("  read_only: true · applied: false")
        return

    data = load_registry(reg_path)

    if as_json:
        typer.echo(
            json.dumps(
                {
                    "registry": str(reg_path),
                    "total": len(data.projects),
                    "local_only": True,
                    "read_only": True,
                    "projects": [
                        {
                            "name": p.name,
                            "type": p.project_type,
                            "memory_dir": str(p.memory_dir),
                            "evidence_dir": (
                                str(p.evidence_dir)
                                if p.evidence_dir is not None
                                else None
                            ),
                            "registered_at": p.registered_at,
                            "last_seen_at": p.last_seen_at,
                            "local_only": p.local_only,
                            "read_only": p.read_only,
                        }
                        for p in data.projects
                    ],
                },
                indent=2,
            )
        )
        return

    typer.echo(
        f"Registry: {reg_path}"
        f"  ·  {len(data.projects)} project(s)"
        "  ·  local-only  ·  read-only"
    )

    if not data.projects:
        typer.echo("")
        typer.echo("  No projects registered yet.")
        typer.echo("  Run 'aeos project register --name <name> --memory-dir <path>'")
        typer.echo("  read_only: true · applied: false")
        return

    typer.echo("")
    col = f"  {'NAME':<30}  {'TYPE':<22}  LAST SEEN"
    typer.echo(col)
    typer.echo("  " + "─" * 70)
    for p in data.projects:
        last = p.last_seen_at[:10] if p.last_seen_at else "—"
        typer.echo(f"  {p.name:<30}  {p.project_type:<22}  {last}")
    typer.echo("")
    typer.echo("  read_only: true · applied: false")


# ---------------------------------------------------------------------------
# project show
# ---------------------------------------------------------------------------


@project_app.command("show")
def project_show(
    name: str = typer.Option(..., "--name", help="Project name to show."),
    registry: str = typer.Option(
        "",
        "--registry",
        help="Registry file path (default: ~/.aeos/projects.json).",
    ),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Show details for a registered project."""
    from aeos.project.registry import DEFAULT_REGISTRY, find_project, load_registry

    reg_path = Path(registry) if registry else DEFAULT_REGISTRY
    data = load_registry(reg_path)
    entry = find_project(data, name)

    if entry is None:
        typer.echo(f"Error: project '{name}' not found in registry.", err=True)
        typer.echo(f"  Registry: {reg_path}", err=True)
        typer.echo(
            "  Run 'aeos project list' to see all registered projects.", err=True
        )
        raise typer.Exit(code=1)

    if as_json:
        typer.echo(
            json.dumps(
                {
                    "name": entry.name,
                    "type": entry.project_type,
                    "memory_dir": str(entry.memory_dir),
                    "evidence_dir": (
                        str(entry.evidence_dir)
                        if entry.evidence_dir is not None
                        else None
                    ),
                    "registered_at": entry.registered_at,
                    "last_seen_at": entry.last_seen_at,
                    "local_only": entry.local_only,
                    "read_only": entry.read_only,
                    "registry": str(reg_path),
                },
                indent=2,
            )
        )
        return

    typer.echo(f"Project:      {entry.name}")
    typer.echo(f"Type:         {entry.project_type}")
    typer.echo(f"Memory:       {entry.memory_dir}")
    if entry.evidence_dir is not None:
        typer.echo(f"Evidence:     {entry.evidence_dir}")
    typer.echo(f"Registered:   {entry.registered_at}")
    typer.echo(f"Last seen:    {entry.last_seen_at}")
    typer.echo(f"Local only:   {str(entry.local_only).lower()}")
    typer.echo(f"Read only:    {str(entry.read_only).lower()}")
    typer.echo(f"Registry:     {reg_path}")
    typer.echo("  read_only: true · applied: false")


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
                    "evidence": f.evidence,
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


@security_app.command("check")
def security_check(
    path: str = typer.Option(".", "--path", "-p", help="Path to audit."),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Audit a project for security risks."""
    project = Path(path).resolve()
    if not project.is_dir():
        typer.echo(f"Error: '{path}' does not exist.", err=True)
        raise typer.Exit(code=1)

    result = run_sec_check(project)

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
                    "evidence": f.evidence,
                }
                for f in result.findings
            ],
        }
        typer.echo(json.dumps(payload, indent=2))
        if result.status == "ERROR":
            raise typer.Exit(code=1)
        return

    typer.echo("Security Check")
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
        if f.evidence:
            typer.echo(f"    Evidence:       {f.evidence}")
        typer.echo("")

    if result.status == "ERROR":
        raise typer.Exit(code=1)


@app.command()
def report(
    path: str = typer.Option(".", "--path", "-p", help="Path to audit."),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Generate a global AEOS project report."""
    project = Path(path).resolve()
    if not project.is_dir():
        typer.echo(f"Error: '{path}' does not exist.", err=True)
        raise typer.Exit(code=1)

    result = generate_report(project)

    if as_json:
        payload = {
            "path": str(result.path),
            "status": result.status,
            "sections": {
                name: {
                    "status": sec.status,
                    "summary": sec.summary,
                    "details": sec.details,
                }
                for name, sec in result.sections.items()
            },
            "top_risks": [
                {
                    "severity": r.severity,
                    "category": r.category,
                    "message": r.message,
                    "location": r.location,
                }
                for r in result.top_risks
            ],
            "recommendations": [
                {"priority": r.priority, "action": r.action}
                for r in result.recommendations
            ],
        }
        typer.echo(json.dumps(payload, indent=2))
        if result.status == "ERROR":
            raise typer.Exit(code=1)
        return

    typer.echo("AEOS Project Report")
    typer.echo(f"Path:   {result.path}")
    typer.echo(f"Status: {result.status}")

    # Project section
    proj = result.sections["project"]
    d = proj.details
    typer.echo("\n── Project ──────────────────────────────────────")
    typer.echo(f"  Status: {proj.status}")
    typer.echo(f"  Name:   {d.get('name', '(unknown)')}")
    if d.get("remote_origin"):
        typer.echo(f"  Remote: {d['remote_origin']}")
    for key, label in [
        ("aeos_toml", "aeos.toml"),
        ("pyproject_toml", "pyproject.toml"),
        ("readme", "README.md"),
        ("src", "src/"),
        ("tests", "tests/"),
        ("docs", "docs/"),
        ("ci_yml", ".github/workflows/ci.yml"),
    ]:
        val = "OK" if d.get(key) else "MISSING"
        typer.echo(f"  {label:<32} {val}")

    # Governance section
    gov = result.sections["governance"]
    gd = gov.details
    typer.echo("\n── Governance ───────────────────────────────────")
    typer.echo(f"  Status: {gov.status}")
    typer.echo(f"  Items:  {gd.get('present', 0)}/{gd.get('total', 0)} present")
    gov_missing = gd.get("missing", [])
    if isinstance(gov_missing, list) and gov_missing:
        typer.echo(f"  Missing: {', '.join(str(m) for m in gov_missing)}")

    # Sovereignty section
    sov = result.sections["sovereignty"]
    sd = sov.details
    typer.echo("\n── Sovereignty ──────────────────────────────────")
    typer.echo(f"  Status:   {sov.status}")
    typer.echo(
        f"  Findings: {sd.get('findings_count', 0)}"
        f"  ({sd.get('error_count', 0)} ERROR"
        f" · {sd.get('warning_count', 0)} WARNING)"
    )

    # Security section
    sec = result.sections["security"]
    secd = sec.details
    typer.echo("\n── Security ─────────────────────────────────────")
    typer.echo(f"  Status:   {sec.status}")
    typer.echo(
        f"  Findings: {secd.get('findings_count', 0)}"
        f"  ({secd.get('error_count', 0)} ERROR"
        f" · {secd.get('warning_count', 0)} WARNING)"
    )

    # Top risks
    typer.echo("\n── Top Risks ────────────────────────────────────")
    if result.top_risks:
        for i, risk in enumerate(result.top_risks, start=1):
            typer.echo(f"  {i}. [{risk.severity}] [{risk.category}] {risk.message}")
            typer.echo(f"     Location: {risk.location}")
    else:
        typer.echo("  No critical risks detected.")

    # Recommended next actions
    typer.echo("\n── Recommended Next Actions ─────────────────────")
    for rec in result.recommendations:
        typer.echo(f"  {rec.priority}. {rec.action}")

    typer.echo("")
    if result.status == "ERROR":
        raise typer.Exit(code=1)


@supabase_app.command("check")
def supabase_check(
    path: str = typer.Option(".", "--path", "-p", help="Path to audit."),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Audit Supabase integration and produce a local remediation plan."""
    project = Path(path).resolve()
    if not project.is_dir():
        typer.echo(f"Error: '{path}' does not exist.", err=True)
        raise typer.Exit(code=1)

    result = run_supabase_check(project)

    if as_json:
        payload = {
            "path": str(result.path),
            "status": result.status,
            "supabase_detected": result.supabase_detected,
            "key_risks": [
                {
                    "variable_name": r.variable_name,
                    "key_type": r.key_type,
                    "severity": r.severity,
                    "in_git_history": r.in_git_history,
                    "in_current_tracking": r.in_current_tracking,
                }
                for r in result.key_risks
            ],
            "rls_evidence": {
                "migrations_present": result.rls_evidence.migrations_present,
                "rls_enable_found": result.rls_evidence.rls_enable_found,
                "policies_found": result.rls_evidence.policies_found,
                "evidence": result.rls_evidence.evidence,
            },
            "local_fixes": {
                "gitignore_protects_env": result.local_fixes.gitignore_protects_env,
                "env_not_tracked": result.local_fixes.env_not_tracked,
                "env_example_exists": result.local_fixes.env_example_exists,
            },
            "remediation_steps": [
                {
                    "priority": s.priority,
                    "action": s.action,
                    "status": s.status,
                    "location": s.location,
                }
                for s in result.remediation_steps
            ],
            "requires_manual_action": result.requires_manual_action,
        }
        typer.echo(json.dumps(payload, indent=2))
        if result.status in ("ERROR", "CRITICAL"):
            raise typer.Exit(code=1)
        return

    typer.echo("Supabase Check")
    typer.echo(f"Path:   {result.path}")
    typer.echo(f"Status: {result.status}")

    if not result.supabase_detected:
        typer.echo("")
        typer.echo("Supabase not detected in this project.")
        return

    typer.echo("Supabase detected: yes")

    if result.key_risks:
        typer.echo(f"\nKey Risks ({len(result.key_risks)}):\n")
        for r in result.key_risks:
            history = "yes" if r.in_git_history else "no"
            tracked = "yes" if r.in_current_tracking else "no"
            typer.echo(f"  [{r.key_type}] {r.severity} — {r.variable_name}")
            typer.echo(f"    In Git history:    {history}")
            typer.echo(f"    Currently tracked: {tracked}")
            typer.echo("")

    rls = result.rls_evidence
    typer.echo("RLS Evidence:")
    typer.echo(f"  Migrations present: {'yes' if rls.migrations_present else 'no'}")
    typer.echo(f"  RLS enable found:   {'yes' if rls.rls_enable_found else 'no'}")
    typer.echo(f"  Policies found:     {'yes' if rls.policies_found else 'no'}")
    if rls.evidence:
        typer.echo(f"  Evidence:           {rls.evidence}")

    lf = result.local_fixes
    typer.echo("\nLocal Fixes:")
    gitignore_ok = "yes ✓" if lf.gitignore_protects_env else "no ✗"
    tracked_ok = "yes ✓" if lf.env_not_tracked else "no ✗"
    example_ok = "yes ✓" if lf.env_example_exists else "no ✗"
    typer.echo(f"  .gitignore protects .env: {gitignore_ok}")
    typer.echo(f"  .env not tracked:         {tracked_ok}")
    typer.echo(f"  .env.example exists:      {example_ok}")

    typer.echo("\nRemediation Steps:")
    for step in result.remediation_steps:
        typer.echo(f"  {step.priority}. [{step.status:<8}] {step.action}")
        typer.echo(f"              → {step.location}")

    typer.echo("")
    if result.status in ("ERROR", "CRITICAL"):
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# supabase rls inspect
# ---------------------------------------------------------------------------


@supabase_rls_app.command("inspect")
def supabase_rls_inspect(
    path: str = typer.Option(".", "--path", "-p", help="Path to project."),
    json_output: bool = typer.Option(False, "--json", help="JSON output."),
) -> None:
    """Inspect Supabase RLS policies from local migration files (read-only)."""
    project = Path(path).resolve()
    if not project.is_dir():
        typer.echo(f"Error: '{path}' does not exist.", err=True)
        raise typer.Exit(code=1)

    result = run_rls_inspect(project)

    if json_output:
        payload = {
            "status": result.status,
            "migrations_scanned": result.migrations_scanned,
            "tables": [
                {
                    "name": t.name,
                    "rls_enabled": t.rls_enabled,
                    "rls_forced": t.rls_forced,
                    "policy_count": len(t.policies),
                }
                for t in result.tables
            ],
            "policies": [
                {
                    "name": p.name,
                    "table": p.table,
                    "command": p.command,
                    "has_using": bool(p.using_expr),
                    "has_with_check": bool(p.with_check_expr),
                    "source_file": p.source_file,
                    "source_line": p.source_line,
                }
                for p in result.policies
            ],
            "findings": [
                {
                    "severity": f.severity,
                    "table": f.table,
                    "rule": f.rule,
                    "message": f.message,
                    "recommendation": f.recommendation,
                    "source_file": f.source_file,
                }
                for f in result.findings
            ],
            "recommendations": result.recommendations,
        }
        typer.echo(json.dumps(payload, indent=2))
        if result.status == "ERROR":
            raise typer.Exit(code=1)
        return

    typer.echo("Supabase RLS Inspect")
    typer.echo(f"Path:               {result.path}")
    typer.echo(f"Status:             {result.status}")
    typer.echo(f"Migrations scanned: {result.migrations_scanned}")
    typer.echo(f"Tables detected:    {len(result.tables)}")
    rls_tables = [t for t in result.tables if t.rls_enabled]
    typer.echo(f"Tables with RLS:    {len(rls_tables)}")
    typer.echo(f"Policies detected:  {len(result.policies)}")

    if result.tables:
        typer.echo("")
        typer.echo("── Tables ──────────────────────────────────────────────")
        for t in sorted(result.tables, key=lambda x: x.name):
            rls_tag = "RLS ✓" if t.rls_enabled else "NO RLS ✗"
            forced_tag = " (forced)" if t.rls_forced else ""
            typer.echo(
                f"  {t.name:<30} {rls_tag}{forced_tag}"
                f"  {len(t.policies)} polic{'y' if len(t.policies) == 1 else 'ies'}"
            )

    if result.findings:
        typer.echo("")
        typer.echo(f"── Findings ({len(result.findings)}) " + "─" * 40)
        for f in result.findings:
            typer.echo(f"  [{f.severity:<7}] [{f.rule}] {f.table}")
            typer.echo(f"    {f.message}")
            typer.echo(f"    → {f.recommendation}")
            if f.source_file:
                typer.echo(f"    @ {f.source_file}")
            typer.echo("")
    else:
        typer.echo("")
        typer.echo("No RLS findings.")

    typer.echo("── Recommendations ─────────────────────────────────────")
    for i, rec in enumerate(result.recommendations, start=1):
        typer.echo(f"  {i}. {rec}")

    typer.echo("")
    typer.echo("Read-only audit — no files modified, no database connection.")

    if result.status == "ERROR":
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# supabase rls plan
# ---------------------------------------------------------------------------


@supabase_rls_app.command("plan")
def supabase_rls_plan(
    path: str = typer.Option(".", "--path", "-p", help="Path to project."),
    json_output: bool = typer.Option(False, "--json", help="JSON output."),
) -> None:
    """Generate a prioritized RLS hardening plan (read-only)."""
    project = Path(path).resolve()
    if not project.is_dir():
        typer.echo(f"Error: '{path}' does not exist.", err=True)
        raise typer.Exit(code=1)

    result = run_rls_plan(project)

    if json_output:
        payload = {
            "status": result.status,
            "migrations_scanned": result.migrations_scanned,
            "read_only": result.read_only,
            "summary": {
                "total_actions": result.summary.total_actions,
                "by_priority": result.summary.by_priority,
                "riskiest_tables": result.summary.riskiest_tables,
                "application_order": result.summary.application_order,
            },
            "actions": [
                {
                    "order": a.order,
                    "priority": a.priority,
                    "table": a.table,
                    "policy": a.policy,
                    "risk_type": a.risk_type,
                    "severity": a.severity,
                    "problem": a.problem,
                    "fix": a.fix,
                    "functional_impact": a.functional_impact,
                    "recommended_test": a.recommended_test,
                    "source_file": a.source_file,
                }
                for a in result.actions
            ],
            "recommendations": result.recommendations,
        }
        typer.echo(json.dumps(payload, indent=2))
        if result.status == "ERROR":
            raise typer.Exit(code=1)
        return

    typer.echo("Supabase RLS Plan Advisor")
    typer.echo(f"Path:               {result.path}")
    typer.echo(f"Status:             {result.status}")
    typer.echo(f"Migrations scanned: {result.migrations_scanned}")
    typer.echo(f"Total actions:      {result.summary.total_actions}")

    if result.summary.total_actions == 0:
        typer.echo("")
        typer.echo("No hardening actions required.")
        typer.echo("")
        typer.echo("Read-only audit — no files modified, no database connection.")
        return

    typer.echo("")
    typer.echo("── Executive Summary ───────────────────────────────────")
    for priority in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        count = result.summary.by_priority.get(priority, 0)
        if count:
            label = f"{priority:<8}"
            noun = "action" if count == 1 else "actions"
            typer.echo(f"  {label}  {count} {noun}")

    if result.summary.riskiest_tables:
        tables_str = ", ".join(result.summary.riskiest_tables)
        typer.echo(f"\n  Riskiest tables: {tables_str}")

    if result.summary.application_order:
        order_str = " → ".join(result.summary.application_order)
        typer.echo(f"  Fix order:       {order_str}")

    current_priority = ""
    for action in result.actions:
        if action.priority != current_priority:
            current_priority = action.priority
            count = result.summary.by_priority.get(current_priority, 0)
            typer.echo("")
            typer.echo(
                f"── {current_priority} ({count})"
                + " "
                + "─" * max(0, 47 - len(current_priority) - len(str(count)))
            )

        typer.echo(f"\n  [{action.order}] {action.table} — {action.risk_type}")
        if action.policy:
            typer.echo(f"      Policy:   {action.policy}")
        typer.echo(f"      Problem:  {action.problem}")
        typer.echo(f"      Fix:      {action.fix}")
        typer.echo(f"      Impact:   {action.functional_impact}")
        typer.echo(f"      Test:     {action.recommended_test}")
        if action.source_file:
            typer.echo(f"      Source:   {action.source_file}")

    typer.echo("")
    typer.echo("── Recommendations ─────────────────────────────────────")
    for i, rec in enumerate(result.recommendations, start=1):
        typer.echo(f"  {i}. {rec}")

    typer.echo("")
    typer.echo("Read-only audit — no files modified, no database connection.")

    if result.status == "ERROR":
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# supabase rls generate
# ---------------------------------------------------------------------------


def _build_export_content(
    gen_result: object,
    review_result: object,
    source_command: str = "aeos supabase rls generate --output",
) -> str:
    """Build the full content of an exported RLS migration file."""
    from aeos.providers.supabase.rls.generator import RLSGenerateResult
    from aeos.providers.supabase.rls.reviewer import RLSReviewResult

    assert isinstance(gen_result, RLSGenerateResult)  # noqa: S101
    assert isinstance(review_result, RLSReviewResult)  # noqa: S101

    import datetime

    date_str = datetime.date.today().isoformat()
    verdict = review_result.verdict
    s = gen_result.summary
    rs = review_result.summary

    _SEP = "-- " + "=" * 61
    lines: list[str] = [
        _SEP,
        "-- AEOS RLS Migration Proposal",
        f"-- Generated by:   {source_command}",
        f"-- Date:           {date_str}",
        f"-- Project:        {gen_result.path}",
        f"-- Migrations:     {gen_result.migrations_scanned} scanned",
        f"-- Verdict:        {verdict}",
        "-- read_only:      true",
        "-- applied:        false",
        _SEP,
        "-- Summary:",
        f"--   Total blocks:    {s.total_blocks}",
        f"--   Auto-generated:  {s.auto_generated}",
        f"--   Manual TODOs:    {s.manual_todos}",
    ]
    for priority in ("CRITICAL", "HIGH", "MEDIUM"):
        count = s.by_priority.get(priority, 0)
        if count:
            lines.append(f"--   {priority}:         {count}")
    lines.append(_SEP)

    if review_result.warnings:
        lines.append("-- Warnings:")
        for w in review_result.warnings:
            lines.append(f"--   {w}")
        lines.append(_SEP)

    if review_result.todo_blocks:
        lines.append(
            f"-- Manual TODOs ({rs.manual_todo_blocks}) — resolve before applying:"
        )
        for b in review_result.todo_blocks:
            lines.append(f"--   [{b.priority}] {b.table} — {b.risk_type}")
        lines.append(_SEP)

    lines += [
        "-- WARNING: This migration has NOT been applied.",
        "-- Review every block carefully before applying to any database.",
        "-- Human approval required.",
        _SEP,
        "",
        gen_result.generated_sql,
    ]
    return "\n".join(lines)


@supabase_rls_app.command("generate")
def supabase_rls_generate(
    path: str = typer.Option(".", "--path", "-p", help="Path to project."),
    json_output: bool = typer.Option(False, "--json", help="JSON output."),
    include_medium: bool = typer.Option(
        False,
        "--include-medium",
        help="Include MEDIUM priority actions (default: CRITICAL + HIGH only).",
    ),
    output: str = typer.Option(
        "",
        "--output",
        "-o",
        help="Write proposed SQL to this file after review gate passes.",
    ),
    force_warning: bool = typer.Option(
        False,
        "--force-warning",
        help="Write output file even when review verdict is WARNING.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite output file if it already exists.",
    ),
) -> None:
    """Generate a proposed RLS SQL migration from Inspector findings (read-only)."""
    project = Path(path).resolve()
    if not project.is_dir():
        typer.echo(f"Error: '{path}' does not exist.", err=True)
        raise typer.Exit(code=1)

    result = run_rls_generate(project, include_medium=include_medium)

    # ── --output mode: generate → review → conditional write ────────────────
    if output:
        output_path = Path(output)
        review = run_rls_review_from_result(result)

        if review.verdict == "BLOCKED":
            typer.echo("Export refused — review verdict: BLOCKED ✗", err=True)
            if review.summary.block_reasons:
                for reason in review.summary.block_reasons:
                    typer.echo(f"  ✗ {reason}", err=True)
            raise typer.Exit(code=1)

        if review.verdict == "WARNING" and not force_warning:
            typer.echo(
                "Export refused — review verdict: WARNING ⚠\n"
                "  The migration has manual TODO blocks that must be resolved.\n"
                "  Use --force-warning to export anyway.",
                err=True,
            )
            raise typer.Exit(code=1)

        if output_path.exists() and not overwrite:
            typer.echo(
                f"Export refused — '{output_path}' already exists.\n"
                "  Use --overwrite to replace it.",
                err=True,
            )
            raise typer.Exit(code=1)

        content = _build_export_content(result, review)
        output_path.write_text(content, encoding="utf-8")

        _VERDICT_LABEL = {"PASS": "PASS ✓", "WARNING": "WARNING ⚠"}
        label = _VERDICT_LABEL.get(review.verdict, review.verdict)
        typer.echo(f"Exported: {output_path}")
        typer.echo(f"Verdict:  {label}")
        typer.echo(
            f"Blocks:   {result.summary.auto_generated} auto"
            f" · {result.summary.manual_todos} TODO"
        )
        typer.echo("Read-only — no migration applied, no database connection.")
        return

    # ── Standard mode (no --output) ─────────────────────────────────────────
    if json_output:
        payload = {
            "status": result.status,
            "migrations_scanned": result.migrations_scanned,
            "read_only": result.read_only,
            "applied": result.applied,
            "summary": {
                "total_blocks": result.summary.total_blocks,
                "auto_generated": result.summary.auto_generated,
                "manual_todos": result.summary.manual_todos,
                "by_priority": result.summary.by_priority,
                "include_medium": result.summary.include_medium,
            },
            "generated_sql": result.generated_sql,
            "warnings": result.warnings,
            "test_plan": result.test_plan,
        }
        typer.echo(json.dumps(payload, indent=2))
        if result.status == "ERROR":
            raise typer.Exit(code=1)
        return

    scope = "CRITICAL + HIGH" + (" + MEDIUM" if include_medium else "")
    typer.echo("Supabase RLS Migration Generator")
    typer.echo(f"Path:               {result.path}")
    typer.echo(f"Status:             {result.status}")
    typer.echo(f"Migrations scanned: {result.migrations_scanned}")
    typer.echo(f"Scope:              {scope}")
    typer.echo(f"Total blocks:       {result.summary.total_blocks}")
    typer.echo(f"  Auto-generated:   {result.summary.auto_generated}")
    typer.echo(f"  Manual TODOs:     {result.summary.manual_todos}")

    if result.summary.total_blocks == 0:
        typer.echo("")
        typer.echo("No SQL blocks to generate.")
        typer.echo("")
        typer.echo(
            "Read-only — no files modified, no migration applied,"
            " no database connection."
        )
        return

    typer.echo("")
    typer.echo("── Priority breakdown ───────────────────────────────────")
    for priority in ("CRITICAL", "HIGH", "MEDIUM"):
        count = result.summary.by_priority.get(priority, 0)
        if count:
            typer.echo(f"  {priority:<8}  {count} block(s)")

    if result.warnings:
        typer.echo("")
        typer.echo("── Warnings ─────────────────────────────────────────────")
        for w in result.warnings:
            typer.echo(f"  ! {w}")

    typer.echo("")
    typer.echo("── Generated SQL ────────────────────────────────────────")
    typer.echo(result.generated_sql)

    if result.test_plan:
        typer.echo("")
        typer.echo("── Test Plan ────────────────────────────────────────────")
        for item in result.test_plan:
            typer.echo(f"  • {item}")

    typer.echo("")
    typer.echo(
        "Read-only — no files modified, no migration applied, no database connection."
    )

    if result.status == "ERROR":
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# supabase rls review
# ---------------------------------------------------------------------------


@supabase_rls_app.command("review")
def supabase_rls_review(
    path: str = typer.Option(".", "--path", "-p", help="Path to project."),
    json_output: bool = typer.Option(False, "--json", help="JSON output."),
    include_medium: bool = typer.Option(
        False,
        "--include-medium",
        help="Include MEDIUM priority actions.",
    ),
) -> None:
    """Review a proposed RLS migration for safety (read-only)."""
    project = Path(path).resolve()
    if not project.is_dir():
        typer.echo(f"Error: '{path}' does not exist.", err=True)
        raise typer.Exit(code=1)

    result = run_rls_review(project, include_medium=include_medium)

    if json_output:
        payload = {
            "status": result.status,
            "verdict": result.verdict,
            "migrations_scanned": result.migrations_scanned,
            "read_only": result.read_only,
            "applied": result.applied,
            "summary": {
                "total_blocks": result.summary.total_blocks,
                "safe_executable_blocks": result.summary.safe_executable_blocks,
                "manual_todo_blocks": result.summary.manual_todo_blocks,
                "blocked_blocks": result.summary.blocked_blocks,
                "warnings_count": result.summary.warnings_count,
                "tables_affected": result.summary.tables_affected,
                "block_reasons": result.summary.block_reasons,
            },
            "safe_blocks": [
                {
                    "priority": b.priority,
                    "table": b.table,
                    "policy": b.policy,
                    "risk_type": b.risk_type,
                    "classification": b.classification,
                }
                for b in result.safe_blocks
            ],
            "todo_blocks": [
                {
                    "priority": b.priority,
                    "table": b.table,
                    "policy": b.policy,
                    "risk_type": b.risk_type,
                    "classification": b.classification,
                }
                for b in result.todo_blocks
            ],
            "blocked_blocks": [
                {
                    "priority": b.priority,
                    "table": b.table,
                    "policy": b.policy,
                    "risk_type": b.risk_type,
                    "classification": b.classification,
                    "reasons": b.reasons,
                }
                for b in result.blocked_blocks
            ],
            "warnings": result.warnings,
        }
        typer.echo(json.dumps(payload, indent=2))
        if result.verdict == "BLOCKED":
            raise typer.Exit(code=1)
        return

    _VERDICT_LABEL = {
        "PASS": "PASS ✓",
        "WARNING": "WARNING ⚠",
        "BLOCKED": "BLOCKED ✗",
    }
    label = _VERDICT_LABEL.get(result.verdict, result.verdict)

    typer.echo("Supabase RLS Review Gate")
    typer.echo(f"Path:               {result.path}")
    typer.echo(f"Status:             {result.status}")
    typer.echo(f"Verdict:            {label}")
    typer.echo(f"Migrations scanned: {result.migrations_scanned}")

    typer.echo("")
    typer.echo("── Review Summary ───────────────────────────────────────")
    typer.echo(f"  Safe blocks:      {result.summary.safe_executable_blocks}")
    typer.echo(f"  Manual TODOs:     {result.summary.manual_todo_blocks}")
    typer.echo(f"  Blocked blocks:   {result.summary.blocked_blocks}")
    typer.echo(f"  Warnings:         {result.summary.warnings_count}")

    if result.summary.block_reasons:
        typer.echo("")
        typer.echo("── Blocked — Reasons ────────────────────────────────────")
        for reason in result.summary.block_reasons:
            typer.echo(f"  ✗ {reason}")

    if result.blocked_blocks:
        typer.echo("")
        typer.echo(
            f"── Blocked Blocks ({result.summary.blocked_blocks})"
            " ─────────────────────────────"
        )
        for b in result.blocked_blocks:
            typer.echo(f"\n  [{b.priority}] {b.table} — {b.risk_type}")
            for r in b.reasons:
                typer.echo(f"    ✗ {r}")

    if result.safe_blocks:
        typer.echo("")
        typer.echo(
            f"── Safe Blocks ({result.summary.safe_executable_blocks})"
            " ───────────────────────────────"
        )
        for b in result.safe_blocks:
            policy_hint = f" ({b.policy})" if b.policy else ""
            typer.echo(f"  ✓ [{b.priority}] {b.table} — {b.risk_type}{policy_hint}")

    if result.todo_blocks:
        typer.echo("")
        typer.echo(
            f"── Manual TODOs ({result.summary.manual_todo_blocks})"
            " ──────────────────────────────"
        )
        for b in result.todo_blocks:
            typer.echo(f"  ? [{b.priority}] {b.table} — {b.risk_type}")

    if result.warnings:
        typer.echo("")
        typer.echo("── Warnings ─────────────────────────────────────────────")
        for w in result.warnings:
            typer.echo(f"  ! {w}")

    typer.echo("")
    typer.echo(
        "Read-only review — no files modified, no migration applied,"
        " no database connection."
    )

    if result.verdict == "BLOCKED":
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# supabase rls harden
# ---------------------------------------------------------------------------

_VERDICT_ICONS = {"PASS": "PASS ✓", "WARNING": "WARNING ⚠", "BLOCKED": "BLOCKED ✗"}


@supabase_rls_app.command("harden")
def supabase_rls_harden(
    path: str = typer.Option(".", "--path", "-p", help="Path to project."),
    json_output: bool = typer.Option(False, "--json", help="JSON output."),
    include_medium: bool = typer.Option(
        False,
        "--include-medium",
        help="Include MEDIUM priority actions (default: CRITICAL + HIGH only).",
    ),
    output: str = typer.Option(
        "",
        "--output",
        "-o",
        help="Write proposed SQL to this file after review gate passes.",
    ),
    force_warning: bool = typer.Option(
        False,
        "--force-warning",
        help="Write output file even when review verdict is WARNING.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite output file if it already exists.",
    ),
) -> None:
    """Orchestrate inspect → plan → generate → review in one command (read-only)."""
    project = Path(path).resolve()
    if not project.is_dir():
        typer.echo(f"Error: '{path}' does not exist.", err=True)
        raise typer.Exit(code=1)

    result = run_rls_harden(project, include_medium=include_medium)
    review = result.review
    gen = result.generate
    verdict_label = _VERDICT_ICONS.get(result.summary.verdict, result.summary.verdict)

    # ── --output mode ────────────────────────────────────────────────────────
    if output:
        output_path = Path(output)

        if review.verdict == "BLOCKED":
            typer.echo("Export refused — review verdict: BLOCKED ✗", err=True)
            if review.summary.block_reasons:
                for reason in review.summary.block_reasons:
                    typer.echo(f"  ✗ {reason}", err=True)
            raise typer.Exit(code=1)

        if review.verdict == "WARNING" and not force_warning:
            typer.echo(
                "Export refused — review verdict: WARNING ⚠\n"
                "  The migration has manual TODO blocks that must be resolved.\n"
                "  Use --force-warning to export anyway.",
                err=True,
            )
            raise typer.Exit(code=1)

        if output_path.exists() and not overwrite:
            typer.echo(
                f"Export refused — '{output_path}' already exists.\n"
                "  Use --overwrite to replace it.",
                err=True,
            )
            raise typer.Exit(code=1)

        content = _build_export_content(
            gen, review, source_command="aeos supabase rls harden --output"
        )
        output_path.write_text(content, encoding="utf-8")
        output_written = True

        if json_output:
            payload = _harden_json_payload(result, output_written, str(output_path))
            typer.echo(json.dumps(payload, indent=2))
            return

        typer.echo(f"Exported: {output_path}")
        typer.echo(f"Verdict:  {verdict_label}")
        typer.echo(
            f"Blocks:   {gen.summary.auto_generated} auto"
            f" · {gen.summary.manual_todos} TODO"
        )
        typer.echo("Read-only — no migration applied, no database connection.")
        return

    # ── JSON mode (no --output) ──────────────────────────────────────────────
    if json_output:
        typer.echo(json.dumps(_harden_json_payload(result, False, ""), indent=2))
        if result.summary.verdict == "BLOCKED":
            raise typer.Exit(code=1)
        return

    # ── Text summary ─────────────────────────────────────────────────────────
    s = result.summary
    typer.echo("Supabase RLS Harden")
    typer.echo(f"Path:               {result.path}")
    typer.echo(f"Status:             {result.status}")
    typer.echo(f"Migrations scanned: {result.migrations_scanned}")

    typer.echo("")
    typer.echo("── Inspect ──────────────────────────────────────────────────")
    typer.echo(f"  Findings:         {s.findings_count}")
    for sev in ("ERROR", "WARNING", "OK"):
        count = s.findings_by_severity.get(sev, 0)
        if count:
            typer.echo(f"    {sev}:  {count}")
    typer.echo(f"  Tables:           {len(result.inspect.tables)}")

    typer.echo("")
    typer.echo("── Plan ─────────────────────────────────────────────────────")
    typer.echo(f"  Actions:          {s.plan_actions}")
    for pri in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        count = s.plan_by_priority.get(pri, 0)
        if count:
            typer.echo(f"    {pri}:  {count}")
    if s.riskiest_tables:
        typer.echo(f"  Riskiest tables:  {', '.join(s.riskiest_tables)}")

    typer.echo("")
    typer.echo("── Generate ─────────────────────────────────────────────────")
    typer.echo(
        f"  Generated blocks: {s.generated_blocks}"
        f"  ({s.auto_blocks} auto · {s.todo_blocks} TODO)"
    )

    typer.echo("")
    typer.echo("── Review Verdict ───────────────────────────────────────────")
    typer.echo(f"  Verdict:          {verdict_label}")
    typer.echo(f"  Safe blocks:      {s.safe_blocks}")
    typer.echo(f"  Manual TODOs:     {s.todo_blocks}")
    typer.echo(f"  Blocked blocks:   {s.blocked_blocks}")
    typer.echo(f"  Warnings:         {review.summary.warnings_count}")

    if review.summary.block_reasons:
        typer.echo("")
        typer.echo("── Blocked — Reasons ────────────────────────────────────────")
        for reason in review.summary.block_reasons:
            typer.echo(f"  ✗ {reason}")

    if review.todo_blocks:
        typer.echo("")
        typer.echo(f"── Manual TODOs ({s.todo_blocks}) ───────────────────────────────")
        for b in review.todo_blocks[:10]:
            typer.echo(f"  ? [{b.priority}] {b.table} — {b.risk_type}")
        if len(review.todo_blocks) > 10:
            typer.echo(f"  … and {len(review.todo_blocks) - 10} more")

    if review.warnings:
        typer.echo("")
        typer.echo("── Warnings ─────────────────────────────────────────────────")
        for w in review.warnings[:10]:
            typer.echo(f"  ! {w}")
        if len(review.warnings) > 10:
            typer.echo(f"  … and {len(review.warnings) - 10} more")

    typer.echo("")
    typer.echo(
        "Read-only — no files modified, no migration applied, no database connection."
    )
    typer.echo("  read_only: true  ·  applied: false")

    if result.summary.verdict == "BLOCKED":
        typer.echo("")
        typer.echo(
            "  ⚠ Verdict BLOCKED — fix the issues above before exporting output."
        )
        raise typer.Exit(code=1)

    typer.echo("")
    typer.echo("── Next step ────────────────────────────────────────────────")
    force_flag = " --force-warning" if result.summary.verdict == "WARNING" else ""
    typer.echo(
        f"  aeos supabase rls harden --path {result.path}"
        f" --output /tmp/rls-proposal.sql{force_flag}"
    )


def _harden_json_payload(
    result: object,
    output_written: bool,
    output_path: str,
) -> dict[str, object]:
    """Build the JSON payload for the harden command."""
    from aeos.providers.supabase.rls.hardener import RLSHardenResult

    assert isinstance(result, RLSHardenResult)  # noqa: S101

    s = result.summary
    review = result.review
    gen = result.generate
    plan = result.plan
    inspect = result.inspect

    return {
        "status": result.status,
        "read_only": result.read_only,
        "applied": result.applied,
        "output_written": output_written,
        "output_path": output_path,
        "summary": {
            "findings_count": s.findings_count,
            "findings_by_severity": s.findings_by_severity,
            "plan_actions": s.plan_actions,
            "plan_by_priority": s.plan_by_priority,
            "generated_blocks": s.generated_blocks,
            "auto_blocks": s.auto_blocks,
            "todo_blocks": s.todo_blocks,
            "verdict": s.verdict,
            "safe_blocks": s.safe_blocks,
            "blocked_blocks": s.blocked_blocks,
            "tables_affected": s.tables_affected,
            "riskiest_tables": s.riskiest_tables,
        },
        "inspect": {
            "status": inspect.status,
            "migrations_scanned": inspect.migrations_scanned,
            "tables_count": len(inspect.tables),
            "policies_count": len(inspect.policies),
            "findings_count": len(inspect.findings),
        },
        "plan": {
            "status": plan.status,
            "total_actions": plan.summary.total_actions,
            "by_priority": plan.summary.by_priority,
            "riskiest_tables": plan.summary.riskiest_tables,
        },
        "generate": {
            "status": gen.status,
            "total_blocks": gen.summary.total_blocks,
            "auto_generated": gen.summary.auto_generated,
            "manual_todos": gen.summary.manual_todos,
            "warnings": gen.warnings,
        },
        "review": {
            "verdict": review.verdict,
            "safe_blocks": review.summary.safe_executable_blocks,
            "manual_todo_blocks": review.summary.manual_todo_blocks,
            "blocked_blocks": review.summary.blocked_blocks,
            "warnings_count": review.summary.warnings_count,
            "block_reasons": review.summary.block_reasons,
        },
    }


# ---------------------------------------------------------------------------
# reclaim harden
# ---------------------------------------------------------------------------

_STATUS_ICONS: dict[str, str] = {
    "OK": "OK ✓",
    "WARNING": "WARNING ⚠",
    "ERROR": "ERROR ✗",
    "CRITICAL": "CRITICAL ✗",
    "PASS": "PASS ✓",
    "BLOCKED": "BLOCKED ✗",
}


def _reclaim_harden_json(
    result: object,
    output_written: bool,
    output_path: str,
    memory_record_path: str = "",
) -> dict[str, object]:
    """Build the JSON payload for the reclaim harden command."""
    from aeos.reclaim.hardener import ReclaimHardenResult

    assert isinstance(result, ReclaimHardenResult)  # noqa: S101

    s = result.summary
    rls_data: dict[str, object] | None = None
    if result.rls is not None:
        rls = result.rls
        rls_data = {
            "status": rls.status,
            "verdict": rls.review.verdict,
            "generated_blocks": rls.summary.auto_blocks,
            "todo_blocks": rls.summary.todo_blocks,
            "blocked_blocks": rls.summary.blocked_blocks,
            "migrations_scanned": rls.migrations_scanned,
        }
    supa_data: dict[str, object] | None = None
    if result.supabase is not None:
        sup = result.supabase
        supa_data = {
            "status": sup.status,
            "supabase_detected": sup.supabase_detected,
            "requires_manual_action": sup.requires_manual_action,
        }
    return {
        "status": result.status,
        "read_only": result.read_only,
        "applied": result.applied,
        "output_written": output_written,
        "output_path": output_path,
        "project_path": str(result.path),
        "summary": {
            "generator_detected": s.generator_detected,
            "providers_detected": s.providers_detected,
            "control_level": s.control_level,
            "secrets_exposure": s.secrets_exposure,
            "security_status": s.security_status,
            "sovereignty_status": s.sovereignty_status,
            "supabase_status": s.supabase_status,
            "rls_verdict": s.rls_verdict,
            "generated_actions": s.generated_actions,
            "manual_actions": s.manual_actions,
            "critical_findings": s.critical_findings,
            "important_findings": s.important_findings,
        },
        "reclaim": {
            "status": result.reclaim.status,
            "control_map": {
                "portability": result.reclaim.control_map.portability,
                "secrets_exposure": result.reclaim.control_map.secrets_exposure,
                "backend_runtime": result.reclaim.control_map.backend_runtime,
            },
        },
        "security": {
            "status": result.security.status,
            "findings_count": len(result.security.findings),
        },
        "sovereignty": {
            "status": result.sovereignty.status,
            "findings_count": len(result.sovereignty.findings),
        },
        "supabase": supa_data,
        "rls": rls_data,
        "recommendations": result.recommendations,
        "exit_options": result.exit_options,
        "remediation_plan": _remediation_plan_json(result),
        "memory_record_path": memory_record_path,
    }


def _remediation_plan_json(result: object) -> dict[str, object] | None:
    """Serialize remediation_plan for JSON output. Returns None if not present."""
    from aeos.reclaim.hardener import ReclaimHardenResult

    assert isinstance(result, ReclaimHardenResult)  # noqa: S101
    plan = result.remediation_plan
    if plan is None:
        return None
    return {
        "phases_count": plan.phases_count,
        "immediate_actions_count": plan.immediate_actions_count,
        "manual_actions_count": plan.manual_actions_count,
        "generatable_actions_count": plan.generatable_actions_count,
        "strategic_options_count": plan.strategic_options_count,
        "phases": [
            {
                "id": ph.id,
                "label": ph.label,
                "priority": ph.priority,
                "goal": ph.goal,
                "actions": ph.actions,
                "automation_level": ph.automation_level,
                "expected_outcome": ph.expected_outcome,
                "risk_if_skipped": ph.risk_if_skipped,
            }
            for ph in plan.phases
        ],
    }


@reclaim_app.command("harden")
def reclaim_harden(
    path: str = typer.Option(".", "--path", "-p", help="Path to project."),
    json_output: bool = typer.Option(False, "--json", help="JSON output."),
    output: str = typer.Option(
        "",
        "--output",
        "-o",
        help="Write a Markdown report to this file.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite the output file if it already exists.",
    ),
    memory_dir: str = typer.Option(
        "",
        "--memory-dir",
        help="Save a memory record (JSON) to this local directory.",
        hidden=True,
    ),
) -> None:
    """Orchestrate the full project reclaim analysis (read-only)."""
    result = run_reclaim_harden(Path(path))
    s = result.summary

    output_written = False
    output_path_str = ""

    # ── --memory-dir: build and save a local memory record ───────────────────
    _memory_record_path: str = ""
    if memory_dir:
        from aeos.memory.store import (
            build_memory_record_from_reclaim_harden,
            save_record,
        )

        _mr = build_memory_record_from_reclaim_harden(result, Path(path))
        _memory_record_path = str(save_record(_mr, Path(memory_dir)))

    # ── --output mode: build report → conditional write ──────────────────────
    if output:
        output_path = Path(output)
        if output_path.exists() and not overwrite:
            typer.echo(
                f"Export refused — '{output_path}' already exists.\n"
                "Pass --overwrite to replace it.",
                err=True,
            )
            raise typer.Exit(code=1)

        content = build_harden_report(result)
        output_path.write_text(content, encoding="utf-8")
        output_written = True
        output_path_str = str(output_path)

        if json_output:
            typer.echo(
                json.dumps(
                    _reclaim_harden_json(
                        result,
                        output_written,
                        output_path_str,
                        _memory_record_path,
                    ),
                    indent=2,
                )
            )
            if result.status == "ERROR":
                raise typer.Exit(code=1)
            return

        status_label = _STATUS_ICONS.get(result.status, result.status)
        typer.echo(f"Status:           {status_label}")
        typer.echo(f"Exported:         {output_path}")
        typer.echo(f"Critical risks:   {s.critical_findings}")
        typer.echo(f"Manual actions:   {s.manual_actions}")
        typer.echo(f"Generatable SQL:  {s.generated_actions} block(s)")
        if _memory_record_path:
            typer.echo(f"Memory:           {_memory_record_path}")
        typer.echo("Read-only — no files modified, no migration applied.")
        typer.echo("  read_only: true  ·  applied: false")
        if result.status == "ERROR":
            raise typer.Exit(code=1)
        return

    if json_output:
        typer.echo(
            json.dumps(
                _reclaim_harden_json(
                    result,
                    output_written,
                    output_path_str,
                    _memory_record_path,
                ),
                indent=2,
            )
        )
        if result.status == "ERROR":
            raise typer.Exit(code=1)
        return

    # Text output
    typer.echo("")
    typer.echo("AEOS Reclaim Harden Report")
    typer.echo(f"Path:     {result.path}")
    typer.echo(f"Status:   {_STATUS_ICONS.get(result.status, result.status)}")
    typer.echo("")

    typer.echo("── Summary " + "─" * 49)
    gen_label = s.generator_detected if s.generator_detected else "none detected"
    providers_label = (
        " · ".join(s.providers_detected) if s.providers_detected else "none"
    )
    sec_label = _STATUS_ICONS.get(s.security_status, s.security_status)
    sov_label = _STATUS_ICONS.get(s.sovereignty_status, s.sovereignty_status)
    typer.echo(f"  Generator:          {gen_label}")
    typer.echo(f"  Providers:          {providers_label}")
    typer.echo(f"  Control level:      {s.control_level}")
    typer.echo(f"  Secrets exposure:   {s.secrets_exposure}")
    typer.echo(f"  Security:           {sec_label}")
    typer.echo(f"  Sovereignty:        {sov_label}")
    if s.supabase_status is not None:
        sup_label = _STATUS_ICONS.get(s.supabase_status, s.supabase_status)
        typer.echo(f"  Supabase:           {sup_label}")
    if s.rls_verdict is not None:
        rls_label = _STATUS_ICONS.get(s.rls_verdict, s.rls_verdict)
        typer.echo(f"  RLS verdict:        {rls_label}")
    typer.echo("")

    if s.critical_findings:
        typer.echo("── Critical Risks " + "─" * 42)
        for sf in result.security.findings:
            if sf.severity == "ERROR":
                typer.echo(f"  ✗ [security] {sf.message}")
        for svf in result.sovereignty.findings:
            if svf.severity == "ERROR":
                typer.echo(f"  ✗ [sovereignty] {svf.message}")
        if result.rls is not None:
            for rf in result.rls.inspect.findings:
                if rf.severity == "ERROR":
                    typer.echo(f"  ✗ [rls] {rf.table} — {rf.rule}: {rf.message}")
        typer.echo("")

    if s.important_findings:
        typer.echo("── Important Risks " + "─" * 41)
        shown = 0
        for sf in result.security.findings:
            if sf.severity == "WARNING" and shown < 5:
                typer.echo(f"  ! [security] {sf.message}")
                shown += 1
        for svf in result.sovereignty.findings:
            if svf.severity == "WARNING" and shown < 8:
                typer.echo(f"  ! [sovereignty] {svf.message}")
                shown += 1
        if result.rls is not None:
            for rf in result.rls.inspect.findings:
                if rf.severity == "WARNING" and shown < 10:
                    typer.echo(f"  ! [rls] {rf.table} — {rf.rule}: {rf.message}")
                    shown += 1
            remaining = s.important_findings - shown
            if remaining > 0:
                typer.echo(f"  … and {remaining} more")
        typer.echo("")

    if s.generated_actions:
        typer.echo("── Generatable Fixes " + "─" * 39)
        typer.echo(f"  SQL:  {s.generated_actions} auto-generated RLS block(s) ready")
        typer.echo(
            f"        run: aeos supabase rls harden --path {result.path} "
            "--output /tmp/rls-proposal.sql --force-warning"
        )
        typer.echo("")

    if s.manual_actions:
        typer.echo("── Manual Actions Required " + "─" * 33)
        if result.rls is not None and result.rls.summary.todo_blocks:
            typer.echo(
                f"  • Review {result.rls.summary.todo_blocks} RLS TODO block(s) "
                "before applying any migration."
            )
        if result.supabase is not None:
            manual_steps = [
                step
                for step in result.supabase.remediation_steps
                if step.status == "manual"
            ]
            for step in manual_steps[:3]:
                typer.echo(f"  • [supabase] {step.action}")
        typer.echo("")

    typer.echo("── Recommendations " + "─" * 41)
    for i, rec in enumerate(result.recommendations, start=1):
        typer.echo(f"  {i}. {rec}")
    typer.echo("")

    typer.echo("── Exit Options " + "─" * 44)
    for opt in result.exit_options:
        typer.echo(f"  {opt}")
    typer.echo("")

    if result.remediation_plan is not None:
        plan = result.remediation_plan
        typer.echo("── Remediation Plan " + "─" * 40)
        typer.echo(
            f"  {plan.phases_count} phases · "
            f"{plan.immediate_actions_count} immediate · "
            f"{plan.manual_actions_count} manual · "
            f"{plan.generatable_actions_count} generatable · "
            f"{plan.strategic_options_count} strategic paths"
        )
        _PRIO_ICON = {"critical": "✗", "high": "⚠", "medium": "·", "low": "·"}
        for ph in plan.phases:
            icon = _PRIO_ICON.get(ph.priority, "·")
            typer.echo(f"  {icon} [{ph.priority:<8}] {ph.id} — {ph.label}")
        typer.echo("  → Run with --output to export the full plan.")
        typer.echo("")

    if _memory_record_path:
        typer.echo(f"Memory:           {_memory_record_path}")
        typer.echo("")

    typer.echo(
        "Read-only — no files modified, no migration applied, no database connection."
    )
    typer.echo("  read_only: true  ·  applied: false")

    if result.status == "ERROR":
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# reclaim inspect
# ---------------------------------------------------------------------------

_CM_DESCRIPTIONS: dict[tuple[str, str], str] = {
    ("frontend_code", "partial"): "generated code, locally present",
    ("frontend_code", "controlled"): "local source code",
    ("backend_runtime", "likely_external"): "no local server/ · providers detected",
    ("backend_runtime", "controlled"): "local server/ detected",
    ("database_schema", "partial"): "supabase/migrations/ — runtime external",
    ("database_schema", "controlled"): "local migrations present",
    ("database_schema", "missing"): "no schema files found",
    ("auth", "external"): "external auth provider detected",
    ("auth", "likely_external"): "Supabase Auth inferred",
    ("storage", "likely_external"): "external storage inferred",
    ("secrets_control", "local"): ".gitignore protects · not tracked",
    ("secrets_control", "external"): ".env currently tracked by Git",
    ("secrets_exposure", "confirmed"): ".env found in Git history",
    ("secrets_exposure", "risk"): ".env tracked — risk on next push",
    ("secrets_exposure", "none"): "no exposure detected",
    ("deployment", "controlled"): "Dockerfile / docker-compose present",
    ("deployment", "external"): "cloud deployment config detected",
    ("deployment", "likely_external"): "no Dockerfile detected",
}


@reclaim_app.command("inspect")
def reclaim_inspect(
    path: str = typer.Option(".", "--path", "-p", help="Path to project."),
    json_output: bool = typer.Option(False, "--json", help="JSON output."),
) -> None:
    """Inspect a project for reclaim opportunities (read-only)."""
    result = run_reclaim_inspect(Path(path))

    if json_output:
        data = {
            "path": str(result.path),
            "status": result.status,
            "generators": [
                {"name": g.name, "detected": g.detected, "evidence": g.evidence}
                for g in result.generators
            ],
            "providers": [
                {
                    "name": p.name,
                    "detected": p.detected,
                    "roles": p.roles,
                    "evidence": p.evidence,
                }
                for p in result.providers
            ],
            "control_map": {
                "frontend_code": result.control_map.frontend_code,
                "backend_runtime": result.control_map.backend_runtime,
                "database_schema": result.control_map.database_schema,
                "auth": result.control_map.auth,
                "storage": result.control_map.storage,
                "secrets_control": result.control_map.secrets_control,
                "secrets_exposure": result.control_map.secrets_exposure,
                "deployment": result.control_map.deployment,
                "portability": result.control_map.portability,
            },
            "missing_assets": [
                {
                    "asset": m.asset,
                    "impact": m.impact,
                    "present": m.present,
                }
                for m in result.missing_assets
            ],
            "exit_options": [
                {
                    "id": e.id,
                    "label": e.label,
                    "complexity": e.complexity,
                    "sovereignty": e.sovereignty,
                    "advantages": e.advantages,
                    "risks": e.risks,
                    "next_action": e.next_action,
                }
                for e in result.exit_options
            ],
            "requires_manual_action": result.requires_manual_action,
            "recommended_next_action": result.recommended_next_action,
        }
        typer.echo(json.dumps(data, indent=2))
        return

    # ── Text output ──────────────────────────────────────────────────────────
    typer.echo("Reclaim Inspect")
    typer.echo(f"Path:   {result.path}")
    typer.echo(f"Status: {result.status}")
    typer.echo("")

    typer.echo("── Generator Detection " + "─" * 38)
    for g in result.generators:
        tag = "detected ⚠" if g.detected else "not detected"
        typer.echo(f"  {g.name:<10}  {tag}")
        if g.detected and g.evidence:
            typer.echo(f"    Evidence: {g.evidence}")
    typer.echo("")

    typer.echo("── Provider Detection " + "─" * 39)
    for p in result.providers:
        tag = "detected" if p.detected else "not detected"
        typer.echo(f"  {p.name:<10}  {tag}")
        if p.detected:
            if p.roles:
                typer.echo(f"    Roles:    {' · '.join(p.roles)}")
            if p.evidence:
                typer.echo(f"    Evidence: {p.evidence}")
    typer.echo("")

    typer.echo("── Control Map " + "─" * 45)
    cm = result.control_map
    cm_rows = [
        ("Frontend code", cm.frontend_code),
        ("Backend runtime", cm.backend_runtime),
        ("Database schema", cm.database_schema),
        ("Auth", cm.auth),
        ("Storage", cm.storage),
        ("Secrets control", cm.secrets_control),
        ("Secrets exposure", cm.secrets_exposure),
        ("Deployment", cm.deployment),
        ("Portability", cm.portability),
    ]
    for label, value in cm_rows:
        desc = _CM_DESCRIPTIONS.get((label.lower().replace(" ", "_"), value), "")
        line = f"  {label:<18}  {value:<18}"
        if desc:
            line += f"  ({desc})"
        typer.echo(line)
    typer.echo("")

    typer.echo("── Missing Local Assets " + "─" * 37)
    for m in result.missing_assets:
        if m.present:
            typer.echo(f"  {m.asset:<24}  present ✓")
        else:
            typer.echo(f"  {m.asset:<24}  missing  → {m.impact}")
    typer.echo("")

    typer.echo("── Exit Options " + "─" * 44)
    for i, opt in enumerate(result.exit_options, start=1):
        typer.echo(f"  {i}. [{opt.complexity:<9} / {opt.sovereignty:<9}] {opt.label}")
        typer.echo(f"     Next: {opt.next_action}")
    typer.echo("")

    typer.echo("── Recommended Next Action " + "─" * 33)
    typer.echo(f"  → {result.recommended_next_action}")

    if result.status == "ERROR":
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# memory list
# ---------------------------------------------------------------------------


@memory_app.command("list")
def memory_list(
    memory_dir: str = typer.Option(
        ..., "--memory-dir", help="Directory containing local memory records."
    ),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List all memory records stored in a local memory directory (read-only)."""
    from aeos.memory.store import list_records

    mem_path = Path(memory_dir)
    try:
        result = list_records(mem_path)
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None

    if as_json:
        payload: dict[str, object] = {
            "memory_dir": str(mem_path),
            "total": len(result.records),
            "records": [
                {
                    "record_id": r.record_id,
                    "project_name": r.project_name,
                    "created_at": r.created_at,
                    "source_command": r.command,
                    "status": r.status,
                    "generator_detected": r.generator,
                    "provider_count": r.provider_count,
                }
                for r in result.records
            ],
            "skipped_files": result.skipped_files,
        }
        typer.echo(json.dumps(payload, indent=2))
        return

    typer.echo(f"Memory Records — {mem_path}")
    typer.echo(f"Records found: {len(result.records)}")

    if result.skipped_files:
        for skipped in result.skipped_files:
            typer.echo(f"  Warning: skipped invalid JSON — {skipped}", err=True)

    if not result.records:
        typer.echo("")
        typer.echo("No records found.")
        typer.echo("Run 'aeos reclaim harden --memory-dir <dir>' to create one.")
        return

    typer.echo("")
    for rec in result.records:
        typer.echo(f"  record_id:      {rec.record_id}")
        typer.echo(f"  project_name:   {rec.project_name}")
        typer.echo(f"  created_at:     {rec.created_at}")
        typer.echo(f"  source_command: {rec.command}")
        typer.echo(f"  status:         {rec.status}")
        if rec.generator is not None:
            typer.echo(f"  generator:      {rec.generator}")
        typer.echo(f"  providers:      {rec.provider_count}")
        typer.echo("")

    typer.echo("Read-only — no files modified.")


# ---------------------------------------------------------------------------
# memory compare
# ---------------------------------------------------------------------------


@memory_app.command("compare")
def memory_compare(
    memory_dir: str = typer.Option(
        ..., "--memory-dir", help="Directory containing local memory records."
    ),
    left: str = typer.Option(
        ..., "--left", help="Left record: record_id or path to a JSON file."
    ),
    right: str = typer.Option(
        ..., "--right", help="Right record: record_id or path to a JSON file."
    ),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Compare two memory records and show what improved, degraded, or changed."""
    from aeos.memory.compare import (
        MemoryCompareDelta,
        compare_records,
        load_record_reference,
    )

    mem_path = Path(memory_dir)

    try:
        left_record = load_record_reference(mem_path, left)
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None

    try:
        right_record = load_record_reference(mem_path, right)
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None

    result = compare_records(left_record, right_record)

    if as_json:

        def _delta_dict(d: MemoryCompareDelta) -> dict[str, object]:
            return {
                "field": d.field,
                "left": d.left_value,
                "right": d.right_value,
                "trend": d.trend,
            }

        payload: dict[str, object] = {
            "left_id": result.left_id,
            "right_id": result.right_id,
            "project_name": result.project_name,
            "compatible": result.compatible,
            "synthesis": result.synthesis,
            "improved": [_delta_dict(d) for d in result.improved],
            "degraded": [_delta_dict(d) for d in result.degraded],
            "unchanged": [_delta_dict(d) for d in result.unchanged],
            "incompatible_fields": [_delta_dict(d) for d in result.incompatible_fields],
        }
        typer.echo(json.dumps(payload, indent=2))
        return

    typer.echo("Memory Compare")
    typer.echo(f"Left:      {result.left_id}")
    typer.echo(f"Right:     {result.right_id}")
    typer.echo(f"Project:   {result.project_name}")
    typer.echo(f"Synthesis: {result.synthesis}")

    if not result.compatible:
        typer.echo("")
        typer.echo(
            "Incompatible records — project names differ."
            " Compare records from the same project."
        )
        typer.echo("")
        typer.echo("Read-only — no files modified.")
        return

    def _fmt(d: MemoryCompareDelta) -> str:
        if d.left_value == d.right_value:
            return f"  {d.field:<16} {d.left_value} (unchanged)"
        return f"  {d.field:<16} {d.left_value} → {d.right_value}"

    if result.improved:
        typer.echo("")
        typer.echo(f"── Improved ({len(result.improved)}) " + "─" * 40)
        for d in result.improved:
            typer.echo(_fmt(d))

    if result.degraded:
        typer.echo("")
        typer.echo(f"── Degraded ({len(result.degraded)}) " + "─" * 40)
        for d in result.degraded:
            typer.echo(_fmt(d))

    if result.unchanged:
        typer.echo("")
        typer.echo(f"── Unchanged ({len(result.unchanged)}) " + "─" * 39)
        for d in result.unchanged:
            typer.echo(_fmt(d))

    if result.incompatible_fields:
        typer.echo("")
        typer.echo(
            f"── Incompatible fields ({len(result.incompatible_fields)}) " + "─" * 30
        )
        for d in result.incompatible_fields:
            typer.echo(f"  {d.field:<16} {d.left_value} / {d.right_value}")

    typer.echo("")
    typer.echo("Read-only — no files modified.")


# ---------------------------------------------------------------------------
# memory show
# ---------------------------------------------------------------------------


@memory_app.command("show")
def memory_show(
    memory_dir: str = typer.Option(
        ..., "--memory-dir", help="Directory containing local memory records."
    ),
    record_id: str = typer.Option(
        ..., "--record", help="ID of the memory record to display."
    ),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Show a single memory record in detail (read-only)."""
    from aeos.memory.store import load_record

    mem_path = Path(memory_dir)
    try:
        record = load_record(mem_path, record_id)
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None

    if as_json:
        payload = {
            "record_id": record.record_id,
            "project_name": record.project_name,
            "project_path": record.project_path,
            "created_at": record.created_at,
            "rail": record.rail,
            "source_command": record.command,
            "status": record.status,
            "generator_detected": record.generator,
            "providers": record.providers,
            "control_level": record.control_level,
            "read_only": record.read_only,
            "applied": record.applied,
            "findings_summary": record.findings_summary,
            "remediation_summary": record.remediation_summary,
            "strategic_options": record.strategic_options,
            "human_validated": record.human_validated,
            "notes": record.notes,
        }
        typer.echo(json.dumps(payload, indent=2))
        return

    typer.echo(f"Memory Record — {record.record_id}")
    typer.echo("")
    typer.echo(f"  project_name:   {record.project_name}")
    typer.echo(f"  project_path:   {record.project_path}")
    typer.echo(f"  created_at:     {record.created_at}")
    typer.echo(f"  source_command: {record.command}")
    typer.echo(f"  status:         {record.status}")
    typer.echo(f"  read_only:      {record.read_only}")
    typer.echo(f"  applied:        {record.applied}")
    typer.echo(f"  human_validated:{record.human_validated}")

    if record.generator:
        typer.echo(f"  generator:      {record.generator}")
    if record.providers:
        typer.echo(f"  providers:      {', '.join(record.providers)}")
    typer.echo(f"  control_level:  {record.control_level}")

    if record.findings_summary:
        typer.echo("")
        typer.echo("── Findings Summary ─────────────────────────────────────")
        for key, count in record.findings_summary.items():
            typer.echo(f"  {key:<12} {count}")

    if record.remediation_summary:
        typer.echo("")
        typer.echo("── Remediation Summary ──────────────────────────────────")
        for key, count in record.remediation_summary.items():
            typer.echo(f"  {key:<20} {count}")

    if record.strategic_options:
        typer.echo("")
        typer.echo("── Strategic Options ────────────────────────────────────")
        for opt in record.strategic_options:
            typer.echo(f"  {opt}")

    if record.notes:
        typer.echo("")
        typer.echo(f"  notes: {record.notes}")

    typer.echo("")
    typer.echo("Read-only — no files modified.")


# ---------------------------------------------------------------------------
# memory timeline
# ---------------------------------------------------------------------------

_TREND_ICON: dict[str, str] = {
    "improved": "↑",
    "degraded": "↓",
    "unchanged": "→",
    "insufficient_data": "?",
    "mixed": "~",
}


@memory_app.command("timeline")
def memory_timeline(
    memory_dir: str = typer.Option(
        ..., "--memory-dir", help="Directory containing local memory records."
    ),
    project: str = typer.Option(
        ..., "--project", help="Project name to build the timeline for."
    ),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Show the chronological timeline of memory records for a project (read-only)."""
    from aeos.memory.timeline import (
        build_timeline,
        load_project_records,
        timeline_to_dict,
    )

    mem_path = Path(memory_dir)

    try:
        records = load_project_records(mem_path, project)
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None

    if not records:
        typer.echo(
            f"Error: no records found for project '{project}' in {mem_path}",
            err=True,
        )
        raise typer.Exit(code=1) from None

    result = build_timeline(records)
    result.memory_dir = str(mem_path)

    if as_json:
        typer.echo(json.dumps(timeline_to_dict(result), indent=2))
        return

    typer.echo(f"Memory Timeline — {result.project_name}")
    typer.echo(f"Directory: {mem_path}")
    typer.echo(f"Records:   {len(result.entries)}")
    typer.echo("")
    typer.echo(
        f"{'#':<3}  {'date':<26}  {'status':<9}  "
        f"{'ctrl':<12}  {'crit':>4}  {'imp':>5}  {'man':>4}  {'gen':>4}"
    )
    typer.echo("─" * 80)
    for i, entry in enumerate(result.entries, start=1):
        date_str = entry.created_at[:19].replace("T", " ")
        typer.echo(
            f"{i:<3}  {date_str:<26}  {entry.status:<9}  "
            f"{entry.control_level:<12}  {entry.critical:>4}  "
            f"{entry.important:>5}  {entry.manual:>4}  {entry.generated:>4}"
        )
        typer.echo(f"     {entry.record_id}")

    if result.synthesis:
        syn = result.synthesis
        typer.echo("")
        typer.echo("── Synthesis ────────────────────────────────────────────")
        typer.echo(
            f"  Status:    {syn.first_status} → {syn.last_status}"
            f"  {_TREND_ICON.get(syn.overall, syn.overall)}"
        )
        typer.echo(f"  Overall:   {syn.overall}")
        typer.echo(
            f"  Critical:  {_TREND_ICON.get(syn.critical_trend, '')} "
            f"{syn.critical_trend}"
        )
        typer.echo(
            f"  Important: {_TREND_ICON.get(syn.important_trend, '')} "
            f"{syn.important_trend}"
        )
        typer.echo(
            f"  Manual:    {_TREND_ICON.get(syn.manual_trend, '')} {syn.manual_trend}"
        )
        typer.echo(
            f"  Generated: {_TREND_ICON.get(syn.generated_trend, '')} "
            f"{syn.generated_trend}"
        )

    typer.echo("")
    typer.echo("Read-only — no files modified.")


# ---------------------------------------------------------------------------
# build plan
# ---------------------------------------------------------------------------


@build_app.command("plan")
def build_plan_cmd(
    name: str = typer.Option(..., "--name", help="Project name."),
    project_type: str = typer.Option(..., "--type", help="Project type."),
    stack: str = typer.Option(..., "--stack", help="Technology stack."),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Generate a structured build plan for a new project (read-only)."""
    from aeos.build.planner import build_plan_to_dict, create_build_plan

    try:
        plan = create_build_plan(name, project_type, stack)
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None

    if as_json:
        typer.echo(json.dumps(build_plan_to_dict(plan), indent=2))
        return

    typer.echo("")
    typer.echo("── Build Plan ───────────────────────────────────────────")
    typer.echo("")
    typer.echo("── Project Identity ─────────────────────────────────────")
    typer.echo(f"  name:  {plan.project_name}")
    typer.echo(f"  type:  {plan.project_type}")
    typer.echo(f"  stack: {plan.stack}")
    typer.echo("")
    typer.echo("── Architecture Summary ─────────────────────────────────")
    typer.echo(f"  {plan.architecture_summary}")
    typer.echo("")
    typer.echo("── Suggested Folder Structure ───────────────────────────")
    for item in plan.folder_structure:
        typer.echo(f"  {item}")
    typer.echo("")
    typer.echo("── Required Governance Files ────────────────────────────")
    for gov_file in plan.governance_files:
        typer.echo(f"  {gov_file}")
    typer.echo("")
    typer.echo("── Security Baseline ────────────────────────────────────")
    for item in plan.security_baseline:
        typer.echo(f"  • {item}")
    typer.echo("")
    typer.echo("── Sovereignty Baseline ─────────────────────────────────")
    for item in plan.sovereignty_baseline:
        typer.echo(f"  • {item}")
    typer.echo("")
    typer.echo("── Testing Baseline ─────────────────────────────────────")
    for item in plan.testing_baseline:
        typer.echo(f"  • {item}")
    typer.echo("")
    typer.echo("── Deployment Baseline ──────────────────────────────────")
    for item in plan.deployment_baseline:
        typer.echo(f"  • {item}")
    typer.echo("")
    typer.echo("── Recommended Next Steps ───────────────────────────────")
    for i, step in enumerate(plan.recommended_next_steps, start=1):
        typer.echo(f"  {i}. {step}")
    typer.echo("")
    typer.echo("Read-only — no project created, no files modified.")
    typer.echo("  read_only: true  ·  applied: false")


# ---------------------------------------------------------------------------
# build scaffold
# ---------------------------------------------------------------------------


@build_app.command("scaffold")
def build_scaffold_cmd(
    name: str = typer.Option(..., "--name", help="Project name."),
    project_type: str = typer.Option(..., "--type", help="Project type."),
    stack: str = typer.Option(..., "--stack", help="Technology stack."),
    output: str = typer.Option(
        ..., "--output", help="Directory to write scaffold files into."
    ),
    force: bool = typer.Option(
        False, "--force", help="Overwrite non-empty output directory."
    ),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Generate a governance scaffold for a new project (writes to --output)."""
    from aeos.build.scaffold import scaffold_build_project, scaffold_result_to_dict

    output_path = Path(output)

    try:
        result = scaffold_build_project(
            name, project_type, stack, output_path, force=force
        )
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None

    if as_json:
        typer.echo(json.dumps(scaffold_result_to_dict(result), indent=2))
        return

    typer.echo("")
    typer.echo("── Build Scaffold ───────────────────────────────────────")
    typer.echo("")
    typer.echo("── Project Identity ─────────────────────────────────────")
    typer.echo(f"  name:   {result.project_name}")
    typer.echo(f"  type:   {result.project_type}")
    typer.echo(f"  stack:  {result.stack}")
    typer.echo("")
    typer.echo("── Output Directory ─────────────────────────────────────")
    typer.echo(f"  {result.output_directory}")
    typer.echo("")
    n = len(result.files_created)
    typer.echo(f"── Files Created ({n}) " + "─" * max(0, 38 - len(str(n))))
    for f in result.files_created:
        typer.echo(f"  {f}")
    if result.files_skipped:
        typer.echo("")
        typer.echo(f"── Files Skipped ({len(result.files_skipped)}) " + "─" * 36)
        for f in result.files_skipped:
            typer.echo(f"  {f}")
    typer.echo("")
    typer.echo("── Safety Guarantees ────────────────────────────────────")
    for item in result.safety_guarantees:
        typer.echo(f"  • {item}")
    typer.echo("")
    typer.echo("── Recommended Next Steps ───────────────────────────────")
    for i, step in enumerate(result.recommended_next_steps, start=1):
        typer.echo(f"  {i}. {step}")
    typer.echo("")
    typer.echo("  applied: true  ·  read_only: false")


# ---------------------------------------------------------------------------
# reclaim recovery plan
# ---------------------------------------------------------------------------


@reclaim_recovery_app.command("plan")
def reclaim_recovery_plan_cmd(
    path: str = typer.Option(".", "--path", "-p", help="Path to project."),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
    output: str = typer.Option(
        "",
        "--output",
        "-o",
        help="Write the recovery plan as Markdown to this file.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite the output file if it already exists.",
    ),
) -> None:
    """Generate a comprehensive recovery plan for an existing project (read-only)."""
    from aeos.reclaim.recovery import (
        build_recovery_markdown,
        build_recovery_plan,
        recovery_plan_to_dict,
    )

    project = Path(path).resolve()
    if not project.is_dir():
        typer.echo(f"Error: '{path}' does not exist.", err=True)
        raise typer.Exit(code=1)

    try:
        plan = build_recovery_plan(project)
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None

    # ── --output mode: write Markdown ────────────────────────────────────────
    if output:
        output_path = Path(output)
        if output_path.exists() and not overwrite:
            typer.echo(
                f"Error: '{output_path}' already exists."
                " Use --overwrite to replace it.",
                err=True,
            )
            raise typer.Exit(code=1)
        content = build_recovery_markdown(plan)
        output_path.write_text(content, encoding="utf-8")
        typer.echo(f"Recovery plan written to: {output_path}")
        typer.echo(f"Status:  {plan.status}")
        typer.echo(f"PRs:     {len(plan.recovery_pr_roadmap)} in roadmap")
        typer.echo("  read_only: true  ·  applied: false")
        return

    # ── JSON mode ────────────────────────────────────────────────────────────
    if as_json:
        typer.echo(json.dumps(recovery_plan_to_dict(plan), indent=2))
        return

    # ── Text output ──────────────────────────────────────────────────────────
    typer.echo("")
    typer.echo("── Recovery Plan " + "─" * 43)
    typer.echo(f"  Path:    {plan.project_path}")
    typer.echo(f"  Project: {plan.project_name}")
    typer.echo(f"  Status:  {plan.status}")
    typer.echo("")

    arch = plan.current_architecture
    gen_list = arch.get("detected_generators", [])
    prov_list = arch.get("detected_providers", [])
    typer.echo("── Current Architecture " + "─" * 36)
    typer.echo(f"  Frontend:    {arch.get('frontend', 'unknown')}")
    typer.echo(f"  Backend:     {arch.get('backend', 'unknown')}")
    typer.echo(f"  Database:    {arch.get('database', 'unknown')}")
    typer.echo(f"  Deployment:  {arch.get('deployment', 'unknown')}")
    typer.echo(f"  Portability: {arch.get('portability', 'unknown')}")
    if isinstance(gen_list, list) and gen_list:
        typer.echo(f"  Generators:  {', '.join(str(g) for g in gen_list)}")
    if isinstance(prov_list, list) and prov_list:
        typer.echo(f"  Providers:   {', '.join(str(p) for p in prov_list)}")
    typer.echo("")

    ctrl = plan.control_status
    typer.echo("── Control Status " + "─" * 42)
    typer.echo(f"  Secrets:         {ctrl.get('secrets', 'unknown')}")
    typer.echo(f"  Secrets exposure:{ctrl.get('secrets_exposure', 'unknown')}")
    typer.echo(f"  Source control:  {ctrl.get('source_control', 'unknown')}")
    typer.echo(f"  Portability:     {ctrl.get('portability', 'unknown')}")
    typer.echo("")

    sec = plan.security_recovery
    blockers = sec.get("immediate_blockers", [])
    typer.echo("── Security Recovery " + "─" * 39)
    typer.echo(f"  Status:           {sec.get('status', 'OK')}")
    typer.echo(f"  Secret exposure:  {sec.get('secret_exposure_status', 'unknown')}")
    if isinstance(blockers, list) and blockers:
        typer.echo(f"  Immediate blockers ({len(blockers)}):")
        for b in blockers[:3]:
            typer.echo(f"    ✗ {b}")
    else:
        typer.echo("  No immediate security blockers.")
    typer.echo("")

    sov = plan.sovereignty_recovery
    ext = sov.get("external_dependencies", [])
    typer.echo("── Sovereignty Recovery " + "─" * 36)
    typer.echo(f"  Status: {sov.get('status', 'OK')}")
    if isinstance(ext, list) and ext:
        typer.echo(f"  External deps ({len(ext)}): {' · '.join(str(d) for d in ext)}")
    typer.echo("")

    db = plan.database_recovery
    typer.echo("── Database Recovery " + "─" * 39)
    typer.echo(
        f"  Supabase detected:  {'yes' if db.get('supabase_detected') else 'no'}"
    )
    if db.get("rls_verdict"):
        typer.echo(f"  RLS verdict:        {db.get('rls_verdict')}")
    fixes = db.get("generated_fixes_count", 0)
    manual = db.get("manual_review_required", 0)
    if fixes or manual:
        typer.echo(f"  Auto-generated:     {fixes}")
        typer.echo(f"  Manual review:      {manual}")
    typer.echo("")

    gov = plan.governance_recovery
    typer.echo("── Governance Recovery " + "─" * 37)
    for key, label in [
        ("aeos_toml_present", "aeos.toml"),
        ("decisions_doc_present", "docs/DECISIONS.md"),
        ("security_doc_present", "docs/SECURITY.md"),
        ("sovereignty_doc_present", "docs/SOVEREIGNTY.md"),
    ]:
        val = "present ✓" if gov.get(key) else "missing"
        typer.echo(f"  {label:<24} {val}")
    typer.echo("")

    ci = plan.testing_ci_recovery
    typer.echo("── Testing and CI " + "─" * 41)
    typer.echo(f"  Tests:      {ci.get('tests_status', 'unknown')}")
    typer.echo(f"  CI gate:    {ci.get('ci_status', 'unknown')}")
    typer.echo("")

    typer.echo("── Local AI Policy " + "─" * 41)
    typer.echo(
        f"  Can do:              {len(plan.local_ai_policy.can_do)} tasks by default"
    )
    n_approval = len(plan.local_ai_policy.requires_human_approval)
    n_never = len(plan.local_ai_policy.must_never_send_to_frontier)
    typer.echo(f"  Needs approval:      {n_approval} actions")
    typer.echo(f"  Never send frontier: {n_never} types")
    typer.echo("")

    typer.echo("── Frontier AI Rules " + "─" * 39)
    for rule in plan.frontier_ai_rules[:3]:
        typer.echo(f"  ✗ {rule.rule}")
    if len(plan.frontier_ai_rules) > 3:
        typer.echo(f"  … and {len(plan.frontier_ai_rules) - 3} more rules")
    typer.echo("")

    n_prs = len(plan.recovery_pr_roadmap)
    typer.echo(f"── Recovery PR Roadmap ({n_prs} PRs) " + "─" * 24)
    for item in plan.recovery_pr_roadmap:
        prereq = f" (after {item.prerequisite})" if item.prerequisite else ""
        typer.echo(f"  PR {item.pr_number}  [{item.priority:<8}] {item.title}{prereq}")
    typer.echo("")

    n_cats = len(plan.development_continuation_backlog)
    typer.echo(f"── Backlog ({n_cats} categories) " + "─" * 36)
    for cat in plan.development_continuation_backlog:
        typer.echo(f"  {cat.name:<24} {len(cat.items)} items")
    typer.echo("")

    typer.echo("── Recommended Next Action " + "─" * 33)
    typer.echo(f"  → {plan.recommended_next_action}")
    typer.echo("")
    typer.echo(
        "Read-only — no files modified, no migration applied, no database connection."
    )
    typer.echo("  read_only: true  ·  applied: false")
    typer.echo("  → Use --output to export the full Markdown recovery plan.")


# ---------------------------------------------------------------------------
# reclaim stage list / show
# ---------------------------------------------------------------------------


@reclaim_stage_app.command("list")
def reclaim_stage_list_cmd(
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List all 10 recovery stages in the Total Sovereign Recovery model (read-only)."""
    from aeos.reclaim.stages import get_recovery_stages, recovery_stage_to_dict

    stages = get_recovery_stages()

    if as_json:
        payload = {
            "read_only": True,
            "applied": False,
            "total": len(stages),
            "stages": [recovery_stage_to_dict(s) for s in stages],
        }
        typer.echo(json.dumps(payload, indent=2))
        return

    typer.echo("")
    typer.echo("── Recovery Stage Model " + "─" * 36)
    typer.echo(f"  {len(stages)} stages  ·  read_only: true  ·  applied: false")
    typer.echo("")
    typer.echo(f"  {'STAGE ID':<36}  NAME")
    typer.echo("  " + "─" * 58)
    for stage in stages:
        typer.echo(f"  {stage.id:<36}  {stage.name}")
    typer.echo("")
    typer.echo("  Use: aeos reclaim stage show --id <stage_id>")
    typer.echo("  read_only: true  ·  applied: false")


@reclaim_stage_app.command("show")
def reclaim_stage_show_cmd(
    stage_id: str = typer.Option(..., "--id", help="Stage ID to display."),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Show details for one recovery stage (read-only)."""
    from aeos.reclaim.stages import get_stage_by_id, recovery_stage_to_dict

    stage = get_stage_by_id(stage_id)
    if stage is None:
        typer.echo(f"Error: stage '{stage_id}' not found.", err=True)
        typer.echo(
            "  Run 'aeos reclaim stage list' to see all available stage IDs.",
            err=True,
        )
        raise typer.Exit(code=1)

    if as_json:
        typer.echo(json.dumps(recovery_stage_to_dict(stage), indent=2))
        return

    typer.echo("")
    typer.echo(f"── {stage.id} " + "─" * max(0, 55 - len(stage.id)))
    typer.echo(f"  Name:       {stage.name}")
    typer.echo(f"  Objective:  {stage.objective}")
    typer.echo("")

    if stage.prerequisites:
        typer.echo(f"  Prerequisites: {', '.join(stage.prerequisites)}")
    else:
        typer.echo("  Prerequisites: none")
    typer.echo("")

    typer.echo("  Actions:")
    for i, action in enumerate(stage.actions, 1):
        typer.echo(f"    {i}. {action}")
    typer.echo("")

    typer.echo("  Risks:")
    for risk in stage.risks:
        typer.echo(f"    - {risk}")
    typer.echo("")

    typer.echo("  Expected Evidence:")
    for evidence in stage.expected_evidence:
        typer.echo(f"    - {evidence}")
    typer.echo("")

    typer.echo(f"  Human Gate:  {stage.human_gate}")
    rollback = stage.rollback_path if stage.rollback_path else "N/A — read-only"
    typer.echo(f"  Rollback:    {rollback}")
    typer.echo(f"  Memory Record Type:  {stage.memory_record_type}")
    typer.echo("")

    typer.echo("  Allowed Agents:")
    for agent in stage.allowed_agents:
        typer.echo(f"    - {agent}")
    typer.echo("")
    typer.echo("  read_only: true  ·  applied: false")


# ---------------------------------------------------------------------------
# reclaim stage plan
# ---------------------------------------------------------------------------


@reclaim_stage_app.command("plan")
def reclaim_stage_plan_cmd(
    done: str = typer.Option(
        "",
        "--done",
        help="Comma-separated completed stage IDs (e.g. stage_0_baseline,stage_1_governance).",  # noqa: E501
    ),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Build a structured staged recovery plan from completed stages (read-only)."""
    from aeos.reclaim.planner import (
        build_staged_recovery_plan,
        staged_plan_to_dict,
        validate_done_ids,
    )

    done_ids = [s.strip() for s in done.split(",") if s.strip()] if done else []

    unknown = validate_done_ids(done_ids)
    if unknown:
        for uid in unknown:
            typer.echo(f"Error: unknown stage ID '{uid}'.", err=True)
        typer.echo(
            "  Run 'aeos reclaim stage list' to see all valid stage IDs.",
            err=True,
        )
        raise typer.Exit(code=1)

    plan = build_staged_recovery_plan(done_ids=done_ids)

    if as_json:
        typer.echo(json.dumps(staged_plan_to_dict(plan), indent=2))
        return

    typer.echo("")
    typer.echo("── Staged Recovery Plan " + "─" * 36)
    typer.echo(
        f"  Done: {len(plan.stages_done)}"
        f"  ·  Ready: {len(plan.stages_ready)}"
        f"  ·  Blocked: {len(plan.stages_blocked)}"
        f"  ·  read_only: true  ·  applied: false"
    )
    typer.echo("")

    if plan.stages_done:
        typer.echo("  DONE")
        for item in plan.items:
            if item.status == "done":
                typer.echo(f"    ✓ {item.stage_id:<42} {item.stage_name}")
        typer.echo("")

    if plan.stages_ready:
        typer.echo("  READY")
        for item in plan.items:
            if item.status == "ready":
                typer.echo(f"    → {item.stage_id:<42} {item.stage_name}")
                if item.recommended_first_action:
                    typer.echo(f"      First action: {item.recommended_first_action}")
        typer.echo("")

    if plan.stages_blocked:
        typer.echo("  BLOCKED")
        for item in plan.items:
            if item.status == "blocked":
                missing = ", ".join(item.missing_prerequisites)
                typer.echo(f"    ✗ {item.stage_id:<42} [needs: {missing}]")
        typer.echo("")

    if plan.next_stage_id:
        typer.echo(f"  Next stage:  {plan.next_stage_id}")
    if plan.next_action:
        typer.echo(f"  Next action: {plan.next_action}")
    typer.echo("")
    typer.echo("  read_only: true  ·  applied: false")


# ---------------------------------------------------------------------------
# reclaim evidence report / summary
# ---------------------------------------------------------------------------


@reclaim_evidence_app.command("report")
def reclaim_evidence_report_cmd(
    stage: str = typer.Option(..., "--stage", help="Stage ID to report evidence for."),
    confirmed: str = typer.Option(
        "",
        "--confirmed",
        help="Comma-separated 0-based indices of confirmed evidence items (e.g. 0,1,2).",  # noqa: E501
    ),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Show expected and missing evidence for one recovery stage (read-only)."""
    from aeos.reclaim.evidence import (
        build_evidence_report,
        evidence_report_to_dict,
        validate_confirmed_indices,
    )
    from aeos.reclaim.stages import get_stage_by_id

    if get_stage_by_id(stage) is None:
        typer.echo(f"Error: stage '{stage}' not found.", err=True)
        typer.echo(
            "  Run 'aeos reclaim stage list' to see all available stage IDs.",
            err=True,
        )
        raise typer.Exit(code=1)

    confirmed_indices: list[int] = []
    if confirmed:
        for raw in confirmed.split(","):
            raw = raw.strip()
            if not raw:
                continue
            try:
                confirmed_indices.append(int(raw))
            except ValueError:
                typer.echo(
                    f"Error: '{raw}' is not a valid integer index.",
                    err=True,
                )
                raise typer.Exit(code=1) from None

    bad = validate_confirmed_indices(stage, confirmed_indices)
    if bad:
        for idx in bad:
            typer.echo(
                f"Error: index {idx} is out of bounds for stage '{stage}'.",
                err=True,
            )
        raise typer.Exit(code=1)

    report = build_evidence_report(stage, confirmed_indices)
    if report is None:
        typer.echo(f"Error: stage '{stage}' not found.", err=True)
        raise typer.Exit(code=1)

    if as_json:
        typer.echo(json.dumps(evidence_report_to_dict(report), indent=2))
        return

    sep = "─" * max(0, 40 - len(report.stage_id))
    typer.echo("")
    typer.echo(f"── Evidence Report: {report.stage_id} {sep}")
    typer.echo(f"  Stage:    {report.stage_name}")
    typer.echo(f"  Status:   {report.evidence_status}")
    typer.echo(
        f"  Items:    {report.total_confirmed}/{report.total_expected} confirmed"
        f"  ·  {report.total_pending} pending"
    )
    if report.validation_blocked_reason:
        typer.echo(f"  Blocked:  {report.validation_blocked_reason}")
    typer.echo("")
    typer.echo("  Evidence Items:")
    for item in report.items:
        icon = "✓" if item.status == "confirmed" else "·"
        typer.echo(f"    [{item.index}] {icon} {item.label}")
    typer.echo("")
    typer.echo("  read_only: true  ·  applied: false")


@reclaim_evidence_app.command("summary")
def reclaim_evidence_summary_cmd(
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Show evidence status for all 10 recovery stages (read-only)."""
    from aeos.reclaim.evidence import build_evidence_summary, evidence_report_to_dict

    reports = build_evidence_summary()

    if as_json:
        payload: dict[str, object] = {
            "read_only": True,
            "applied": False,
            "total": len(reports),
            "reports": [evidence_report_to_dict(r) for r in reports],
        }
        typer.echo(json.dumps(payload, indent=2))
        return

    typer.echo("")
    typer.echo("── Evidence Summary " + "─" * 40)
    typer.echo(f"  {len(reports)} stages  ·  read_only: true  ·  applied: false")
    typer.echo("")
    typer.echo(f"  {'STAGE ID':<36}  {'STATUS':<12}  ITEMS")
    typer.echo("  " + "─" * 64)
    for r in reports:
        typer.echo(
            f"  {r.stage_id:<36}  {r.evidence_status:<12}"
            f"  {r.total_confirmed}/{r.total_expected}"
        )
    typer.echo("")
    typer.echo("  Use: aeos reclaim evidence report --stage <stage_id>")
    typer.echo("  read_only: true  ·  applied: false")


# ---------------------------------------------------------------------------
# ui dashboard
# ---------------------------------------------------------------------------


@ui_app.command("dashboard")
def ui_dashboard(
    memory_dir: str = typer.Option(
        ..., "--memory-dir", help="Directory containing local memory records."
    ),
    project: str = typer.Option(
        ..., "--project", help="Project name to build the dashboard for."
    ),
    output: str = typer.Option(
        ..., "--output", "-o", help="Write the HTML dashboard to this file."
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite the output file if it already exists.",
    ),
) -> None:
    """Generate a static HTML dashboard from local memory records (read-only)."""
    from aeos.ui.dashboard import load_dashboard_data, render_dashboard

    mem_path = Path(memory_dir)
    output_path = Path(output)

    if output_path.exists() and not overwrite:
        typer.echo(
            f"Error: '{output_path}' already exists. Use --overwrite to replace it.",
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        data = load_dashboard_data(mem_path, project)
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None

    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_dashboard(data)
    output_path.write_text(html, encoding="utf-8")

    typer.echo(f"Dashboard:  {output_path}")
    typer.echo(f"Project:    {data.project_name}")
    typer.echo(f"Records:    {len(data.records)}")
    typer.echo("Read-only — no files modified, no migration applied.")
    typer.echo("  read_only: true  ·  applied: false")


# ---------------------------------------------------------------------------
# ui project-workspace
# ---------------------------------------------------------------------------


@ui_app.command("project-workspace")
def ui_project_workspace(
    memory_dir: str = typer.Option(
        ..., "--memory-dir", help="Directory containing local memory records."
    ),
    project: str = typer.Option(
        ..., "--project", help="Project name to build the workspace for."
    ),
    output: str = typer.Option(
        ..., "--output", "-o", help="Write the HTML workspace to this file."
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite the output file if it already exists.",
    ),
) -> None:
    """Generate a decision-ready HTML project workspace (read-only)."""
    from aeos.ui.workspace import load_workspace_data, render_workspace

    mem_path = Path(memory_dir)
    output_path = Path(output)

    if output_path.exists() and not overwrite:
        typer.echo(
            f"Error: '{output_path}' already exists. Use --overwrite to replace it.",
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        data = load_workspace_data(mem_path, project)
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None

    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_workspace(data)
    output_path.write_text(html, encoding="utf-8")

    typer.echo(f"Workspace:  {output_path}")
    typer.echo(f"Project:    {data.project_name}")
    typer.echo(f"Records:    {len(data.records)}")
    pr = data.production_readiness
    typer.echo(f"Verdict:    {pr.verdict}")
    typer.echo("Read-only — no files modified, no migration applied.")
    typer.echo("  read_only: true  ·  applied: false")


# ---------------------------------------------------------------------------
# ui evidence-pack
# ---------------------------------------------------------------------------


@ui_app.command("evidence-pack")
def ui_evidence_pack(
    memory_dir: str = typer.Option(
        ..., "--memory-dir", help="Directory containing local memory records."
    ),
    project: str = typer.Option(
        ..., "--project", help="Project name to build the evidence pack for."
    ),
    output_dir: str = typer.Option(
        ...,
        "--output-dir",
        help="Directory to write the evidence pack into.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing output directory contents.",
    ),
) -> None:
    """Generate a multi-file evidence pack from local memory records (read-only)."""
    from aeos.ui.evidence_pack import generate_evidence_pack

    mem_path = Path(memory_dir)
    out_path = Path(output_dir)

    try:
        result = generate_evidence_pack(mem_path, project, out_path, overwrite)
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None

    typer.echo(f"Pack:       {result.output_dir}")
    typer.echo(f"Project:    {result.project_name}")
    typer.echo(f"Records:    {result.record_count}")
    typer.echo(f"Verdict:    {result.verdict}")
    typer.echo(f"Files:      {len(result.files)}")
    for f in result.files:
        typer.echo(f"  {f.name}")
    typer.echo("Read-only — no files modified, no migration applied.")
    typer.echo("  read_only: true  ·  applied: false")


# ---------------------------------------------------------------------------
# ui portfolio
# ---------------------------------------------------------------------------


@ui_app.command("portfolio")
def ui_portfolio(
    memory_dir: str = typer.Option(
        "",
        "--memory-dir",
        help="Directory containing local memory records.",
    ),
    registry: str = typer.Option(
        "",
        "--registry",
        help="Project registry file (from 'aeos project register').",
    ),
    output: str = typer.Option(
        ..., "--output", "-o", help="Write the HTML portfolio to this file."
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite the output file if it already exists.",
    ),
) -> None:
    """Generate a static HTML portfolio from memory records or a project registry.

    Provide --memory-dir or --registry. If neither is given, the default
    registry (~/.aeos/projects.json) is used automatically.
    """
    from aeos.ui.portfolio import load_portfolio_data, render_portfolio

    if memory_dir and registry:
        typer.echo(
            "Error: --memory-dir and --registry are mutually exclusive.", err=True
        )
        raise typer.Exit(code=1)

    output_path = Path(output)
    if output_path.exists() and not overwrite:
        typer.echo(
            f"Error: '{output_path}' already exists. Use --overwrite to replace it.",
            err=True,
        )
        raise typer.Exit(code=1)

    # ── Registry mode (explicit --registry or implicit default) ─────────────
    if registry or not memory_dir:
        from aeos.project.registry import DEFAULT_REGISTRY, load_registry

        reg_path = Path(registry) if registry else DEFAULT_REGISTRY
        if not reg_path.exists():
            typer.echo(
                f"Error: registry file '{reg_path}' does not exist.\n"
                "  Use --memory-dir to specify a memory directory, or\n"
                "  run 'aeos project register' to create the default registry.",
                err=True,
            )
            raise typer.Exit(code=1)

        reg_data = load_registry(reg_path)
        mem_paths = [p.memory_dir for p in reg_data.projects if p.memory_dir.exists()]

        try:
            data = load_portfolio_data(mem_paths)
        except FileNotFoundError as exc:
            typer.echo(f"Error: {exc}", err=True)
            raise typer.Exit(code=1) from None

        output_path.parent.mkdir(parents=True, exist_ok=True)
        html = render_portfolio(data)
        output_path.write_text(html, encoding="utf-8")

        typer.echo(f"Portfolio:  {output_path}")
        typer.echo(f"Source:     registry ({reg_path})")
        typer.echo(f"Projects:   {len(data.projects)}")
        for entry in data.projects:
            typer.echo(f"  {entry.project_name}  →  {entry.verdict}")
        typer.echo("Read-only — no files modified, no migration applied.")
        typer.echo("  read_only: true  ·  applied: false")
        return

    # ── Memory-dir mode (existing behaviour) ────────────────────────────────
    mem_path = Path(memory_dir)

    try:
        data = load_portfolio_data([mem_path])
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None

    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_portfolio(data)
    output_path.write_text(html, encoding="utf-8")

    typer.echo(f"Portfolio:  {output_path}")
    typer.echo(f"Projects:   {len(data.projects)}")
    for entry in data.projects:
        typer.echo(f"  {entry.project_name}  →  {entry.verdict}")
    typer.echo("Read-only — no files modified, no migration applied.")
    typer.echo("  read_only: true  ·  applied: false")


# ---------------------------------------------------------------------------
# workspace demo
# ---------------------------------------------------------------------------


@workspace_app.command("demo")
def workspace_demo(
    registry: str = typer.Option(
        "",
        "--registry",
        help="Registry JSON file (default: ~/.aeos/projects.json).",
    ),
    output_dir: str = typer.Option(
        ...,
        "--output-dir",
        help="Directory to write the full workspace into.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing output files.",
    ),
) -> None:
    """Generate a full static workspace from a project registry (read-only).

    Produces: index.html (portfolio) + per-project dashboard, workspace,
    and evidence-pack for every registered project.
    If --registry is omitted, ~/.aeos/projects.json is used automatically.
    """
    from aeos.project.registry import DEFAULT_REGISTRY
    from aeos.workspace.demo import generate_workspace_demo

    reg_path = Path(registry) if registry else DEFAULT_REGISTRY
    out_path = Path(output_dir)

    try:
        result = generate_workspace_demo(reg_path, out_path, overwrite)
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None

    typer.echo(f"Workspace:  {result.output_dir}")
    typer.echo(f"Registry:   {result.registry_path}")
    typer.echo(f"Portfolio:  {result.portfolio}")
    typer.echo(
        f"Projects:   {result.generated_count} generated"
        f"  ·  {result.skipped_count} skipped"
    )
    for proj in result.projects:
        if proj.skipped:
            typer.echo(
                f"  [SKIP] {proj.name}  (memory_dir missing: {proj.skip_reason})"
            )
        else:
            typer.echo(f"  [OK]   {proj.name}  →  {proj.output_dir}")
    if result.warnings:
        typer.echo("")
        typer.echo("Warnings:")
        for w in result.warnings:
            typer.echo(f"  ! {w}")
    typer.echo("Read-only — no files modified, no migration applied.")
    typer.echo("  read_only: true  ·  applied: false")
