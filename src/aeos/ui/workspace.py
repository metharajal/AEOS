"""
AEOS UI Project Workspace — decision-ready project view from MemoryRecords.

Read-only. No network. No AI. No secrets. No .env.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import TYPE_CHECKING

from aeos.memory.models import MemoryRecord
from aeos.memory.timeline import (
    MemoryTimelineResult,
    build_timeline,
    load_project_records,
)

if TYPE_CHECKING:
    from aeos.agent.planner import ProjectPlanEntry

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: 'Courier New', Courier, monospace;
    background: #0d1117;
    color: #c9d1d9;
    padding: 32px;
    line-height: 1.7;
    font-size: 13px;
    max-width: 960px;
    margin: 0 auto;
}
h1 {
    color: #58a6ff;
    font-size: 20px;
    margin-bottom: 4px;
    letter-spacing: 0.02em;
}
h2 {
    color: #8b949e;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin: 32px 0 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid #21262d;
}
h3 { color: #c9d1d9; font-size: 13px; margin-bottom: 8px; }
p { margin-bottom: 8px; }
.meta { color: #6e7681; font-size: 11px; margin-bottom: 10px; }
.badge {
    display: inline-block;
    font-size: 10px;
    padding: 2px 7px;
    border-radius: 3px;
    margin-right: 6px;
    font-weight: bold;
    letter-spacing: 0.04em;
}
.badge-ro  { background: #0c2a1e; color: #3fb950; border: 1px solid #196c3a; }
.badge-app { background: #2a0c0c; color: #f85149; border: 1px solid #6c1919; }
.badge-hum { background: #2a1e0c; color: #d29922; border: 1px solid #6c4a19; }
.card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 4px;
    padding: 18px 20px;
    margin-bottom: 4px;
}
.summary-text {
    font-size: 14px;
    color: #e6edf3;
    line-height: 1.8;
}
.verdict {
    display: inline-block;
    font-size: 16px;
    font-weight: bold;
    padding: 10px 18px;
    border-radius: 4px;
    margin-bottom: 14px;
    letter-spacing: 0.04em;
}
.verdict-not-ready {
    background: #2a0c0c;
    color: #f85149;
    border: 2px solid #6c1919;
}
.verdict-ready {
    background: #0c2a1e;
    color: #3fb950;
    border: 2px solid #196c3a;
}
.reason-item {
    padding: 4px 0;
    border-bottom: 1px solid #21262d;
    color: #f85149;
}
.reason-item::before { content: "✗ "; }
.reason-item:last-child { border-bottom: none; }
table { border-collapse: collapse; width: 100%; }
th {
    background: #0d1117;
    color: #6e7681;
    font-size: 10px;
    text-align: left;
    padding: 7px 12px;
    border: 1px solid #21262d;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
td { padding: 7px 12px; border: 1px solid #21262d; }
.td-label { color: #8b949e; font-size: 12px; }
.td-val { font-variant-numeric: tabular-nums; text-align: right; }
.td-delta { text-align: right; font-size: 12px; }
.delta-neg { color: #3fb950; }
.delta-pos { color: #f85149; }
.delta-zero { color: #6e7681; }
.s-error  { color: #f85149; font-weight: bold; }
.s-warning { color: #d29922; }
.s-ok     { color: #3fb950; }
.kv { display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 4px; }
.kv-item { display: flex; flex-direction: column; min-width: 100px; }
.kv-lbl {
    font-size: 9px;
    color: #6e7681;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.kv-val { font-size: 16px; font-weight: bold; color: #c9d1d9; }
.kv-val.s-error  { color: #f85149; }
.kv-val.s-warning { color: #d29922; }
.kv-val.s-ok     { color: #3fb950; }
.gate-item {
    padding: 6px 0;
    border-bottom: 1px solid #21262d;
    color: #d29922;
}
.gate-item::before { content: "○ "; }
.gate-item:last-child { border-bottom: none; }
.action-item {
    padding: 5px 0;
    border-bottom: 1px solid #21262d;
}
.action-item:last-child { border-bottom: none; }
.action-num { color: #58a6ff; margin-right: 6px; }
.risk-row td:first-child { color: #f85149; font-weight: bold; }
.evidence-row { color: #6e7681; font-size: 12px; }
.evidence-val { color: #c9d1d9; }
footer {
    margin-top: 40px;
    padding-top: 12px;
    border-top: 1px solid #21262d;
    font-size: 10px;
    color: #6e7681;
}
.record-id { font-size: 10px; color: #6e7681; }
"""


@dataclass
class ProductionReadiness:
    """Production deployment verdict derived from the latest MemoryRecord."""

    ready: bool
    verdict: str
    reasons: list[str] = field(default_factory=list)


@dataclass
class RecoveryProgress:
    """Before / after comparison across all audit records."""

    first_date: str
    last_date: str
    record_count: int
    baseline: dict[str, int]
    current: dict[str, int]
    deltas: dict[str, int]


@dataclass
class WorkspaceData:
    """All pre-computed data needed to render the workspace HTML."""

    project_name: str
    records: list[MemoryRecord]
    timeline: MemoryTimelineResult
    executive_summary: str
    production_readiness: ProductionReadiness
    recovery_progress: RecoveryProgress
    human_gates: list[str]
    next_actions: list[str]
    agent_plan_entry: ProjectPlanEntry | None = field(default=None)


# ---------------------------------------------------------------------------
# Derivation logic
# ---------------------------------------------------------------------------


def _derive_production_readiness(record: MemoryRecord) -> ProductionReadiness:
    fs = record.findings_summary
    critical = fs.get("critical", 0)
    generated = fs.get("generated", 0)
    manual = fs.get("manual", 0)

    reasons: list[str] = []
    if critical > 0:
        reasons.append(f"{critical} critical risk(s) unresolved")
    if generated > 0:
        reasons.append(
            f"{generated} SQL remediation block(s) not yet applied to staging"
        )
    if manual > 0:
        reasons.append(f"{manual} manual action(s) pending human review")
    if record.control_level == "weak":
        reasons.append(
            "project control level is 'weak'"
            " — portability and secrets not fully secured"
        )

    ready = len(reasons) == 0
    return ProductionReadiness(
        ready=ready,
        verdict="READY FOR PRODUCTION" if ready else "NOT READY FOR PRODUCTION",
        reasons=reasons,
    )


def _derive_executive_summary(
    record: MemoryRecord,
    progress: RecoveryProgress,
) -> str:
    fs = record.findings_summary
    critical = fs.get("critical", 0)
    important = fs.get("important", 0)
    imp_delta = progress.deltas.get("important", 0)

    if critical > 0 and important > 50:
        return (
            f"The project is in active recovery. Governance controls have been"
            f" established and {abs(imp_delta)} important risk(s) have been"
            f" addressed, but {critical} critical risk(s) and {important}"
            f" important risk(s) remain. The project is not ready for"
            f" production deployment."
        )
    if critical > 0:
        return (
            f"The project has progressed through initial recovery phases."
            f" {critical} critical risk(s) remain unresolved before any"
            f" production deployment is possible."
            f" Human validation is required for all remaining gates."
        )
    if important > 20:
        return (
            "Critical risks have been addressed. Important findings remain"
            " that require attention, but the project can proceed to staging"
            " validation with human approval."
        )
    return (
        "The project is in a controlled recovery state."
        " Known risks have been addressed. Human validation is required"
        " before production deployment."
    )


def _derive_human_gates(record: MemoryRecord) -> list[str]:
    fs = record.findings_summary
    providers_lower = [p.lower() for p in record.providers]
    gates: list[str] = []

    if "supabase" in providers_lower:
        gates.append(
            "Rotate Supabase service_role and anon keys"
            " — verify no credential exposure in git history"
        )
        gates.append(
            "Validate that profiles.commune_id is populated for all users"
            " before applying RLS migration"
        )
        gates.append(
            "Apply RLS hardening migration to staging"
            " — review, test, then promote to production"
        )

    if fs.get("critical", 0) > 0:
        gates.append(
            "Resolve all critical findings — required before any production deployment"
        )

    if record.control_level in ("weak", "partial"):
        gates.append(
            "Decide public data access model for participatory features"
            " — Option A: commune-scoped, Option B: portal-public"
        )

    if fs.get("manual", 0) > 0:
        n = fs["manual"]
        gates.append(
            f"Review and validate {n} manual action(s)"
            " — see reclaim harden report for details"
        )

    return gates


def _derive_next_actions(
    record: MemoryRecord,
    pr: ProductionReadiness,
) -> list[str]:
    fs = record.findings_summary
    providers_lower = [p.lower() for p in record.providers]
    actions: list[str] = []

    if fs.get("generated", 0) > 0:
        n = fs["generated"]
        actions.append(
            f"Review and apply {n} auto-generated SQL remediation block(s)"
            " to staging — human approval required"
        )

    if "supabase" in providers_lower:
        actions.append(
            "Rotate Supabase credentials via dashboard"
            " — update .env.example if scope changed"
        )

    if fs.get("critical", 0) > 0:
        actions.append(
            "Apply RLS hardening migration after manual review"
            " — verify on staging before production"
        )

    if fs.get("manual", 0) > 0:
        actions.append(
            "Complete manual RLS policy review"
            " — FOR ALL policies require explicit command splits"
        )

    if record.control_level == "weak":
        actions.append(
            "Decide and document the public data access policy"
            " for participatory budget features"
        )

    if not actions:
        actions.append(
            "All known automated actions complete"
            " — run next harden cycle to verify state"
        )

    return actions


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_workspace_data(memory_dir: Path, project_name: str) -> WorkspaceData:
    """Load records and compute all derived workspace data.

    Raises FileNotFoundError if memory_dir doesn't exist.
    Raises ValueError if no records found for the given project.
    """
    records = load_project_records(memory_dir, project_name)
    if not records:
        raise ValueError(
            f"No records found for project '{project_name}' in {memory_dir}"
        )
    timeline = build_timeline(records)
    first = records[0]
    last = records[-1]

    baseline = {
        "critical": first.findings_summary.get("critical", 0),
        "important": first.findings_summary.get("important", 0),
        "manual": first.findings_summary.get("manual", 0),
        "generated": first.findings_summary.get("generated", 0),
    }
    current = {
        "critical": last.findings_summary.get("critical", 0),
        "important": last.findings_summary.get("important", 0),
        "manual": last.findings_summary.get("manual", 0),
        "generated": last.findings_summary.get("generated", 0),
    }
    deltas = {k: current[k] - baseline[k] for k in baseline}

    progress = RecoveryProgress(
        first_date=first.created_at[:10],
        last_date=last.created_at[:10],
        record_count=len(records),
        baseline=baseline,
        current=current,
        deltas=deltas,
    )

    pr = _derive_production_readiness(last)
    summary = _derive_executive_summary(last, progress)
    gates = _derive_human_gates(last)
    actions = _derive_next_actions(last, pr)

    from aeos.agent.planner import generate_project_entry

    agent_entry = generate_project_entry(
        name=project_name,
        memory_dir=memory_dir,
    )

    return WorkspaceData(
        project_name=project_name,
        records=records,
        timeline=timeline,
        executive_summary=summary,
        production_readiness=pr,
        recovery_progress=progress,
        human_gates=gates,
        next_actions=actions,
        agent_plan_entry=agent_entry,
    )


# ---------------------------------------------------------------------------
# HTML rendering helpers
# ---------------------------------------------------------------------------


def _h(tag: str, content: str, cls: str = "") -> str:
    attr = f" class='{cls}'" if cls else ""
    return f"<{tag}{attr}>{content}</{tag}>"


def _status_cls(status: str) -> str:
    return {
        "OK": "s-ok",
        "WARNING": "s-warning",
        "ERROR": "s-error",
        "CRITICAL": "s-error",
    }.get(status.upper(), "s-warning")


def _delta_cell(delta: int) -> str:
    if delta == 0:
        return "<td class='td-delta delta-zero'>→ unchanged</td>"
    sign = "+" if delta > 0 else ""
    cls = "delta-pos" if delta > 0 else "delta-neg"
    arrow = "↓" if delta > 0 else "↑"
    return f"<td class='td-delta {cls}'>{arrow} {sign}{delta}</td>"


def _kv(label: str, value: str, val_cls: str = "") -> str:
    cls = f"kv-val {val_cls}" if val_cls else "kv-val"
    return (
        "<div class='kv-item'>"
        f"<span class='kv-lbl'>{escape(label)}</span>"
        f"<span class='{cls}'>{value}</span>"
        "</div>"
    )


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------


def _render_overview(data: WorkspaceData) -> str:
    last = data.records[-1]
    sc = _status_cls(last.status)
    generator = escape(last.generator or "unknown")
    providers = escape(", ".join(last.providers) if last.providers else "none")
    ctrl = escape(last.control_level)
    ts = last.created_at[:19].replace("T", " ")

    return (
        "<div class='kv'>"
        + _kv("Status", last.status, sc)
        + _kv("Control Level", ctrl)
        + _kv("Generator", generator)
        + _kv("Providers", providers)
        + _kv("Last Audit", ts + " UTC")
        + _kv("Audit Records", str(data.recovery_progress.record_count))
        + "</div>"
    )


def _render_summary(data: WorkspaceData) -> str:
    return f"<p class='summary-text'>{escape(data.executive_summary)}</p>"


def _render_production_readiness(data: WorkspaceData) -> str:
    pr = data.production_readiness
    v_cls = "verdict-ready" if pr.ready else "verdict-not-ready"
    html = f"<div class='verdict {v_cls}'>{escape(pr.verdict)}</div>"
    if pr.reasons:
        html += "<div style='margin-top:8px'>"
        for r in pr.reasons:
            html += f"<div class='reason-item'>{escape(r)}</div>"
        html += "</div>"
    return html


def _render_recovery_progress(data: WorkspaceData) -> str:
    p = data.recovery_progress
    rows = ""
    labels = {
        "critical": "Critical risks",
        "important": "Important findings",
        "manual": "Manual actions",
        "generated": "Generatable SQL blocks",
    }
    for key, label in labels.items():
        b = p.baseline.get(key, 0)
        c = p.current.get(key, 0)
        d = p.deltas.get(key, 0)
        rows += (
            "<tr>"
            f"<td class='td-label'>{escape(label)}</td>"
            f"<td class='td-val'>{b}</td>"
            f"<td class='td-val'>{c}</td>" + _delta_cell(d) + "</tr>"
        )
    header = (
        "<thead><tr>"
        "<th>Metric</th>"
        f"<th>Baseline ({escape(p.first_date)})</th>"
        f"<th>Current ({escape(p.last_date)})</th>"
        "<th>Change</th>"
        "</tr></thead>"
    )
    return (
        "<div style='overflow-x:auto'>"
        f"<table>{header}<tbody>{rows}</tbody></table>"
        f"<p style='margin-top:8px;color:#6e7681;font-size:11px'>"
        f"{p.record_count} audit record(s) · "
        f"{escape(p.first_date)} → {escape(p.last_date)}"
        " · source: AEOS MemoryRecords</p>"
        "</div>"
    )


def _render_completed_work(data: WorkspaceData) -> str:
    p = data.recovery_progress
    items: list[str] = []

    imp_d = p.deltas.get("important", 0)
    gen_d = p.deltas.get("generated", 0)

    if imp_d < 0:
        items.append(
            f"{abs(imp_d)} important risk(s) addressed"
            f" (baseline: {p.baseline['important']}"
            f" → current: {p.current['important']})"
        )
    if gen_d < 0:
        items.append(
            f"{abs(gen_d)} SQL remediation block(s) resolved or committed"
            f" (baseline: {p.baseline['generated']}"
            f" → current: {p.current['generated']})"
        )

    items.append(
        f"{p.record_count} audit cycle(s) completed"
        f" between {p.first_date} and {p.last_date}"
    )
    items.append(
        "Underlying work (governance, security, CI) tracked"
        " in the project's git history"
    )

    rows = "".join(
        f"<tr><td style='color:#3fb950'>✓</td>"
        f"<td style='padding-left:8px'>{escape(item)}</td></tr>"
        for item in items
    )
    return f"<div style='overflow-x:auto'><table><tbody>{rows}</tbody></table></div>"


def _render_human_gates(data: WorkspaceData) -> str:
    if not data.human_gates:
        return "<p style='color:#3fb950'>No open human gates.</p>"
    return "".join(
        f"<div class='gate-item'>{escape(g)}</div>" for g in data.human_gates
    )


def _render_risk_register(data: WorkspaceData) -> str:
    last = data.records[-1]
    fs = last.findings_summary
    critical = fs.get("critical", 0)
    important = fs.get("important", 0)
    manual = fs.get("manual", 0)
    generated = fs.get("generated", 0)

    rows = (
        "<tr class='risk-row'>"
        "<td>CRITICAL</td>"
        f"<td class='td-val'>{critical}</td>"
        "<td>Must be resolved before any production deployment</td>"
        "</tr>"
        "<tr>"
        "<td class='td-label'>IMPORTANT</td>"
        f"<td class='td-val'>{important}</td>"
        "<td>Security, sovereignty, and RLS findings</td>"
        "</tr>"
        "<tr>"
        "<td class='td-label'>MANUAL ACTIONS</td>"
        f"<td class='td-val'>{manual}</td>"
        "<td>Require explicit human decision and execution</td>"
        "</tr>"
        "<tr>"
        "<td class='td-label'>GEN SQL BLOCKS</td>"
        f"<td class='td-val'>{generated}</td>"
        "<td>Auto-generated — require review before applying</td>"
        "</tr>"
    )
    header = "<thead><tr><th>Category</th><th>Count</th><th>Notes</th></tr></thead>"
    return (
        "<div style='overflow-x:auto'>"
        f"<table>{header}<tbody>{rows}</tbody></table>"
        "</div>"
    )


def _render_evidence(data: WorkspaceData) -> str:
    last = data.records[-1]
    first = data.records[0]
    p = data.recovery_progress

    rows = (
        "<tr class='evidence-row'>"
        "<td>Memory records</td>"
        f"<td class='evidence-val'>{p.record_count}</td>"
        "</tr>"
        "<tr class='evidence-row'>"
        "<td>First record</td>"
        f"<td class='evidence-val record-id'>{escape(first.record_id)}</td>"
        "</tr>"
        "<tr class='evidence-row'>"
        "<td>Latest record</td>"
        f"<td class='evidence-val record-id'>{escape(last.record_id)}</td>"
        "</tr>"
        "<tr class='evidence-row'>"
        "<td>read_only</td>"
        f"<td class='evidence-val' style='color:#3fb950'>"
        f"{str(last.read_only).lower()}</td>"
        "</tr>"
        "<tr class='evidence-row'>"
        "<td>applied</td>"
        f"<td class='evidence-val' style='color:#f85149'>"
        f"{str(last.applied).lower()}</td>"
        "</tr>"
        "<tr class='evidence-row'>"
        "<td>human_validated</td>"
        f"<td class='evidence-val' style='color:#d29922'>"
        f"{str(last.human_validated).lower()}</td>"
        "</tr>"
    )
    return f"<div style='overflow-x:auto'><table><tbody>{rows}</tbody></table></div>"


def _render_next_actions(data: WorkspaceData) -> str:
    return "".join(
        f"<div class='action-item'>"
        f"<span class='action-num'>{i}.</span>{escape(a)}"
        "</div>"
        for i, a in enumerate(data.next_actions, start=1)
    )


def _render_agent_recommendations(data: WorkspaceData) -> str:
    entry = data.agent_plan_entry
    if entry is None:
        return "<p style='color:#6e7681'>Agent plan not available.</p>"

    sc = _status_cls(entry.status)

    header = (
        "<div style='margin-bottom:12px'>"
        "<span style='font-size:10px;color:#6e7681;text-transform:uppercase;"
        "letter-spacing:0.08em'>Mode</span><br>"
        "<span style='color:#58a6ff'>deterministic read-only planner</span>"
        f"&nbsp;&nbsp;<span class='{sc}' style='font-weight:bold'>"
        f"[{escape(entry.status)}]</span>"
        "</div>"
    )

    risks_html = ""
    if entry.risks:
        items = "".join(
            f"<div class='gate-item' style='color:#f85149'>{escape(r)}</div>"
            for r in entry.risks
        )
        risks_html = (
            "<div style='margin-bottom:10px'>"
            "<span style='font-size:10px;color:#6e7681;text-transform:uppercase;"
            "letter-spacing:0.08em'>Risks / Blockers</span>"
            f"<div style='margin-top:6px'>{items}</div>"
            "</div>"
        )

    actions_html = ""
    if entry.actions:
        items = "".join(
            f"<div class='action-item'>"
            f"<span class='action-num'>{i}.</span>{escape(a)}"
            "</div>"
            for i, a in enumerate(entry.actions, start=1)
        )
        actions_html = (
            "<div style='margin-bottom:10px'>"
            "<span style='font-size:10px;color:#6e7681;text-transform:uppercase;"
            "letter-spacing:0.08em'>Recommended Actions</span>"
            f"<div style='margin-top:6px'>{items}</div>"
            "</div>"
        )

    footer = (
        "<div style='margin-top:12px;font-size:11px;color:#6e7681'>"
        "read_only: true &nbsp;·&nbsp; applied: false"
        " &nbsp;·&nbsp; human validation required"
        "</div>"
    )

    return header + risks_html + actions_html + footer


# ---------------------------------------------------------------------------
# Main renderer
# ---------------------------------------------------------------------------


def render_workspace(data: WorkspaceData) -> str:
    """Build and return the complete HTML workspace string."""
    project = escape(data.project_name)
    last_ts = data.records[-1].created_at[:19].replace("T", " ")

    sections = [
        ("<h2>Project Overview</h2>", _render_overview(data)),
        ("<h2>Executive Summary</h2>", _render_summary(data)),
        ("<h2>Agent Recommendations</h2>", _render_agent_recommendations(data)),
        ("<h2>Production Readiness</h2>", _render_production_readiness(data)),
        ("<h2>Recovery Progress</h2>", _render_recovery_progress(data)),
        ("<h2>Completed Recovery Work</h2>", _render_completed_work(data)),
        ("<h2>Human Gates</h2>", _render_human_gates(data)),
        ("<h2>Risk Register</h2>", _render_risk_register(data)),
        ("<h2>Evidence</h2>", _render_evidence(data)),
        ("<h2>Next Recommended Actions</h2>", _render_next_actions(data)),
    ]

    body = ""
    for header, content in sections:
        body += header + f"<div class='card'>{content}</div>\n"

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>AEOS Workspace — {project}</title>\n"
        f"<style>{_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        "<header>\n"
        "<h1>AEOS Project Workspace</h1>\n"
        f"<div class='meta'>{project}</div>\n"
        "<div style='margin-top:8px'>\n"
        "<span class='badge badge-ro'>read_only: true</span>\n"
        "<span class='badge badge-app'>applied: false</span>\n"
        "<span class='badge badge-hum'>human validation required</span>\n"
        "</div>\n"
        "</header>\n" + body + "<footer>\n"
        f"Generated by AEOS Project Workspace · {project}"
        f" · last audit: {escape(last_ts)} UTC"
        " · read_only: true · applied: false · human validation required\n"
        "</footer>\n"
        "</body>\n"
        "</html>"
    )
