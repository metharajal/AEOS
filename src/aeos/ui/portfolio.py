"""
AEOS UI Portfolio — multi-project overview page from MemoryRecords.

Read-only. No network. No AI. No secrets. No .env.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from html import escape
from pathlib import Path

from aeos.memory.models import MemoryRecord
from aeos.memory.timeline import load_project_records

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class PortfolioProjectEntry:
    """Per-project summary derived from the latest MemoryRecord."""

    project_name: str
    last_record_date: str
    status: str
    control_level: str
    critical: int
    important: int
    manual: int
    generated: int
    verdict: str
    ready: bool
    blocking_reasons: list[str]
    next_action: str
    record_count: int
    generator: str | None
    providers: list[str]


@dataclass
class PortfolioData:
    """All projects discovered across one or more memory directories."""

    memory_dirs: list[Path]
    projects: list[PortfolioProjectEntry] = field(default_factory=list)
    generated_at: str = ""

    def __post_init__(self) -> None:
        if not self.generated_at:
            self.generated_at = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")


# ---------------------------------------------------------------------------
# Discovery and derivation
# ---------------------------------------------------------------------------


def _discover_projects(memory_dir: Path) -> list[str]:
    """Return sorted unique project names found in memory_dir.

    Records are stored in memory_dir/{project_name}/*.json —
    scanning subdirectory names is the authoritative discovery method.
    """
    names: list[str] = []
    for d in memory_dir.iterdir():
        if d.is_dir() and not d.name.startswith(".") and any(d.glob("*.json")):
            names.append(d.name)
    return sorted(names)


def _derive_verdict(record: MemoryRecord) -> tuple[bool, str, list[str]]:
    fs = record.findings_summary
    critical = fs.get("critical", 0)
    generated = fs.get("generated", 0)
    manual = fs.get("manual", 0)

    reasons: list[str] = []
    if critical > 0:
        reasons.append(f"{critical} critical risk(s) unresolved")
    if generated > 0:
        reasons.append(f"{generated} SQL block(s) not yet applied to staging")
    if manual > 0:
        reasons.append(f"{manual} manual action(s) pending review")
    if record.control_level == "weak":
        reasons.append("control level is 'weak'")

    ready = len(reasons) == 0
    verdict = "READY FOR PRODUCTION" if ready else "NOT READY FOR PRODUCTION"
    return ready, verdict, reasons


def _derive_next_action(record: MemoryRecord) -> str:
    fs = record.findings_summary
    if fs.get("generated", 0) > 0:
        n = fs["generated"]
        return (
            f"Review and apply {n} auto-generated SQL block(s)"
            " to staging — human approval required"
        )
    if "supabase" in [p.lower() for p in record.providers]:
        return "Rotate Supabase credentials — verify no key exposure in git"
    if fs.get("critical", 0) > 0:
        return (
            "Apply RLS hardening migration after manual review"
            " — verify on staging first"
        )
    if fs.get("manual", 0) > 0:
        return f"Complete {fs['manual']} manual action(s) — see reclaim harden report"
    if record.control_level == "weak":
        return "Decide public data access policy — document the decision"
    return "Run next harden cycle to verify state"


def _build_entry(
    project_name: str, records: list[MemoryRecord]
) -> PortfolioProjectEntry:
    last = records[-1]
    fs = last.findings_summary
    ready, verdict, reasons = _derive_verdict(last)
    return PortfolioProjectEntry(
        project_name=project_name,
        last_record_date=last.created_at[:10],
        status=last.status,
        control_level=last.control_level,
        critical=fs.get("critical", 0),
        important=fs.get("important", 0),
        manual=fs.get("manual", 0),
        generated=fs.get("generated", 0),
        verdict=verdict,
        ready=ready,
        blocking_reasons=reasons,
        next_action=_derive_next_action(last),
        record_count=len(records),
        generator=last.generator,
        providers=last.providers,
    )


# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------


def load_portfolio_data(memory_dirs: list[Path]) -> PortfolioData:
    """Load and aggregate portfolio data from one or more memory directories.

    Raises FileNotFoundError if any memory_dir does not exist.
    Silently skips directories that contain no readable records.
    """
    for d in memory_dirs:
        if not d.exists():
            raise FileNotFoundError(f"Memory directory not found: {d}")

    data = PortfolioData(memory_dirs=memory_dirs)
    seen: set[str] = set()

    for memory_dir in memory_dirs:
        for project_name in _discover_projects(memory_dir):
            if project_name in seen:
                continue
            seen.add(project_name)
            records = load_project_records(memory_dir, project_name)
            if records:
                data.projects.append(_build_entry(project_name, records))

    data.projects.sort(key=lambda e: e.project_name)
    return data


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: 'Courier New', Courier, monospace;
    background: #0d1117;
    color: #c9d1d9;
    padding: 32px;
    font-size: 13px;
    line-height: 1.6;
}
h1 { color: #58a6ff; font-size: 22px; margin-bottom: 4px; }
h2 {
    color: #8b949e;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin: 28px 0 12px;
    padding-bottom: 5px;
    border-bottom: 1px solid #21262d;
}
.meta { color: #6e7681; font-size: 11px; margin-bottom: 12px; }
.badge {
    display: inline-block;
    font-size: 10px;
    padding: 2px 7px;
    border-radius: 3px;
    margin-right: 5px;
    font-weight: bold;
}
.badge-ro  { background:#0c2a1e; color:#3fb950; border:1px solid #196c3a; }
.badge-app { background:#2a0c0c; color:#f85149; border:1px solid #6c1919; }
.badge-hum { background:#2a1e0c; color:#d29922; border:1px solid #6c4a19; }
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
    gap: 16px;
    margin-top: 4px;
}
.card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    padding: 18px 20px;
}
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 12px;
}
.project-name {
    color: #e6edf3;
    font-size: 15px;
    font-weight: bold;
}
.project-sub { color: #6e7681; font-size: 11px; margin-top: 2px; }
.verdict {
    display: inline-block;
    font-size: 9px;
    font-weight: bold;
    padding: 3px 8px;
    border-radius: 3px;
    text-align: center;
    white-space: nowrap;
    letter-spacing: 0.04em;
}
.verdict-not-ready {
    background: #2a0c0c;
    color: #f85149;
    border: 1px solid #6c1919;
}
.verdict-ready {
    background: #0c2a1e;
    color: #3fb950;
    border: 1px solid #196c3a;
}
.metrics {
    display: flex;
    gap: 16px;
    margin-bottom: 12px;
    flex-wrap: wrap;
}
.metric { display: flex; flex-direction: column; min-width: 52px; }
.metric-lbl {
    font-size: 9px;
    color: #6e7681;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.metric-val { font-size: 18px; font-weight: bold; }
.m-critical { color: #f85149; }
.m-important { color: #d29922; }
.m-neutral { color: #c9d1d9; }
.m-ok { color: #3fb950; }
.next-action {
    background: #0d1117;
    border-left: 2px solid #21262d;
    padding: 6px 10px;
    font-size: 11px;
    color: #8b949e;
    margin-bottom: 12px;
    border-radius: 0 3px 3px 0;
}
.next-action-lbl {
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #6e7681;
    margin-bottom: 2px;
}
.links { display: flex; gap: 10px; flex-wrap: wrap; }
.link-btn {
    font-size: 10px;
    color: #58a6ff;
    text-decoration: none;
    padding: 3px 8px;
    border: 1px solid #21262d;
    border-radius: 3px;
    background: #0d1117;
}
.link-btn:hover { border-color: #58a6ff; }
.divider {
    border: none;
    border-top: 1px solid #21262d;
    margin: 10px 0;
}
.status-ok     { color: #3fb950; }
.status-warn   { color: #d29922; }
.status-error  { color: #f85149; }
.empty-state {
    color: #6e7681;
    font-size: 13px;
    padding: 32px;
    text-align: center;
    border: 1px dashed #21262d;
    border-radius: 6px;
}
footer {
    margin-top: 40px;
    padding-top: 12px;
    border-top: 1px solid #21262d;
    font-size: 10px;
    color: #6e7681;
}
"""


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------


def _status_cls(status: str) -> str:
    s = status.upper()
    if s == "OK":
        return "status-ok"
    if s in ("ERROR", "CRITICAL"):
        return "status-error"
    return "status-warn"


def _metric_cls(key: str, val: int) -> str:
    if key == "critical":
        return "m-critical" if val > 0 else "m-ok"
    if key == "important":
        return "m-important" if val > 20 else "m-neutral"
    return "m-neutral"


def _render_card(entry: PortfolioProjectEntry) -> str:
    v_cls = "verdict-not-ready" if not entry.ready else "verdict-ready"
    sc = _status_cls(entry.status)
    gen = escape(entry.generator or "—")
    prov = escape(", ".join(entry.providers) if entry.providers else "—")

    metrics = (
        "<div class='metrics'>"
        f"<div class='metric'><span class='metric-lbl'>Critical</span>"
        f"<span class='metric-val {_metric_cls('critical', entry.critical)}'>"
        f"{entry.critical}</span></div>"
        f"<div class='metric'><span class='metric-lbl'>Important</span>"
        f"<span class='metric-val {_metric_cls('important', entry.important)}'>"
        f"{entry.important}</span></div>"
        f"<div class='metric'><span class='metric-lbl'>Manual</span>"
        f"<span class='metric-val m-neutral'>{entry.manual}</span></div>"
        f"<div class='metric'><span class='metric-lbl'>Gen SQL</span>"
        f"<span class='metric-val m-neutral'>{entry.generated}</span></div>"
        "</div>"
    )

    meta_line = (
        f"<div class='project-sub'>"
        f"status: <span class='{sc}'>{escape(entry.status)}</span>"
        f" · control: {escape(entry.control_level)}"
        f" · {entry.record_count} record(s)"
        f" · {escape(entry.last_record_date)}"
        f"</div>"
        f"<div class='project-sub' style='margin-top:3px'>"
        f"generator: {gen} · providers: {prov}"
        "</div>"
    )

    slug = escape(entry.project_name)
    links = (
        "<div class='links'>"
        f"<a class='link-btn' href='{slug}/dashboard.html'>Dashboard</a>"
        f"<a class='link-btn' href='{slug}/project-workspace.html'>"
        "Workspace</a>"
        f"<a class='link-btn' href='{slug}/evidence-pack/index.html'>"
        "Evidence Pack</a>"
        "</div>"
    )

    return (
        "<div class='card'>"
        "<div class='card-header'>"
        f"<div><div class='project-name'>{slug}</div>{meta_line}</div>"
        f"<div class='verdict {v_cls}'>{escape(entry.verdict)}</div>"
        "</div>" + metrics + "<hr class='divider'>"
        "<div class='next-action'>"
        "<div class='next-action-lbl'>Recommended next action</div>"
        f"{escape(entry.next_action)}"
        "</div>" + links + "</div>"
    )


def render_portfolio(data: PortfolioData) -> str:
    """Build and return the complete portfolio HTML string."""
    total = len(data.projects)
    not_ready = sum(1 for p in data.projects if not p.ready)
    ready = total - not_ready

    summary = (
        f"<span style='color:#c9d1d9'>{total} project(s)</span>"
        f" · <span style='color:#3fb950'>{ready} ready</span>"
        f" · <span style='color:#f85149'>{not_ready} not ready</span>"
        f" · generated {escape(data.generated_at)}"
    )

    if data.projects:
        grid = (
            "<div class='grid'>"
            + "".join(_render_card(e) for e in data.projects)
            + "</div>"
        )
    else:
        grid = (
            "<div class='empty-state'>"
            "No projects found in the specified memory directory."
            "</div>"
        )

    dirs_listed = " · ".join(str(d) for d in data.memory_dirs)

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>AEOS Portfolio</title>\n"
        f"<style>{_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        "<header>\n"
        "<h1>AEOS Portfolio</h1>\n"
        f"<div class='meta'>{summary}</div>\n"
        "<div>\n"
        "<span class='badge badge-ro'>local-first</span>\n"
        "<span class='badge badge-ro'>read-only</span>\n"
        "<span class='badge badge-app'>no backend</span>\n"
        "<span class='badge badge-app'>no cloud</span>\n"
        "<span class='badge badge-hum'>no secrets</span>\n"
        "</div>\n"
        "</header>\n"
        "<h2>Projects</h2>\n" + grid + "\n"
        "<footer>\n"
        "AEOS Portfolio"
        f" · source: {escape(dirs_listed)}"
        f" · {escape(data.generated_at)}"
        " · read_only: true · applied: false · human validation required\n"
        "</footer>\n"
        "</body>\n"
        "</html>"
    )
