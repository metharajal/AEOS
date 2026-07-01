"""
AEOS UI Dashboard — static HTML cockpit view from MemoryRecords.

Read-only. No network. No AI. No secrets. No .env.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path

from aeos.memory.models import MemoryRecord
from aeos.memory.timeline import (
    MemoryTimelineResult,
    build_timeline,
    load_project_records,
)

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: 'Courier New', Courier, monospace;
    background: #0d1117;
    color: #c9d1d9;
    padding: 32px;
    line-height: 1.6;
    font-size: 13px;
    max-width: 1200px;
}
h1 { color: #58a6ff; font-size: 18px; margin-bottom: 4px; letter-spacing: 0.02em; }
h2 {
    color: #8b949e;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin: 28px 0 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid #21262d;
}
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
    padding: 16px 20px;
    margin-bottom: 4px;
}
.card-table { padding: 0; overflow-x: auto; }
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
td {
    padding: 6px 12px;
    border: 1px solid #21262d;
    font-size: 12px;
    vertical-align: middle;
}
tr.even td { background: #161b22; }
tr.odd  td { background: #0d1117; }
tr.latest td { background: #0c1e36 !important; }
.s-error  { color: #f85149; font-weight: bold; }
.s-warning { color: #d29922; }
.s-ok     { color: #3fb950; }
.trend-improved    { color: #3fb950; }
.trend-degraded    { color: #f85149; }
.trend-unchanged   { color: #6e7681; }
.trend-insufficient { color: #6e7681; font-style: italic; }
.dn { color: #3fb950; font-size: 10px; }
.dp { color: #f85149; font-size: 10px; }
.d0 { color: #6e7681; font-size: 10px; }
.num { text-align: right; white-space: nowrap; }
.kv { display: flex; flex-wrap: wrap; gap: 20px; }
.kv-item { display: flex; flex-direction: column; min-width: 90px; }
.kv-lbl {
    font-size: 9px;
    color: #6e7681;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.kv-val { font-size: 20px; font-weight: bold; line-height: 1.3; }
.kv-val.s-error  { color: #f85149; }
.kv-val.s-warning { color: #d29922; }
.kv-val.s-ok     { color: #3fb950; }
.kv-val.neutral  { color: #c9d1d9; }
.action { padding: 5px 0; border-bottom: 1px solid #21262d; }
.action:last-child { border-bottom: none; }
.action-num { color: #58a6ff; margin-right: 6px; }
.action-tag {
    font-size: 10px;
    padding: 1px 5px;
    border-radius: 2px;
    margin-right: 6px;
    font-weight: bold;
}
.tag-critical { background: #2a0c0c; color: #f85149; }
.tag-generated { background: #0c1e36; color: #58a6ff; }
.tag-manual  { background: #1e1a0c; color: #d29922; }
.tag-plan    { background: #0c2a1e; color: #3fb950; }
.tag-ok      { background: #0c2a1e; color: #3fb950; }
.option-item { padding: 4px 0; border-bottom: 1px solid #21262d; color: #8b949e; }
.option-item:last-child { border-bottom: none; }
footer {
    margin-top: 36px;
    padding-top: 12px;
    border-top: 1px solid #21262d;
    font-size: 10px;
    color: #6e7681;
}
"""


@dataclass
class DashboardData:
    """Intermediate container for dashboard rendering."""

    project_name: str
    records: list[MemoryRecord]
    timeline: MemoryTimelineResult


def load_dashboard_data(memory_dir: Path, project_name: str) -> DashboardData:
    """Load all records for a project and build timeline data.

    Raises FileNotFoundError if memory_dir doesn't exist.
    Raises ValueError if no records found for the given project.
    """
    records = load_project_records(memory_dir, project_name)
    if not records:
        raise ValueError(
            f"No records found for project '{project_name}' in {memory_dir}"
        )
    timeline = build_timeline(records)
    return DashboardData(
        project_name=project_name,
        records=records,
        timeline=timeline,
    )


def _status_cls(status: str) -> str:
    return {
        "OK": "s-ok",
        "WARNING": "s-warning",
        "ERROR": "s-error",
        "CRITICAL": "s-error",
    }.get(status.upper(), "s-warning")


def _trend_cls(trend: str) -> str:
    return {
        "improved": "trend-improved",
        "degraded": "trend-degraded",
        "unchanged": "trend-unchanged",
    }.get(trend, "trend-insufficient")


def _trend_arrow(trend: str) -> str:
    return {
        "improved": "↑",
        "degraded": "↓",
        "unchanged": "→",
        "insufficient_data": "·",
    }.get(trend, "·")


def _delta_html(val: int, prev: int | None) -> str:
    """Render value + optional delta. Lower is better for all finding counts."""
    if prev is None:
        return str(val)
    delta = val - prev
    if delta == 0:
        return str(val)
    sign = "+" if delta > 0 else ""
    cls = "dp" if delta > 0 else "dn"
    return f'{val} <span class="{cls}">({sign}{delta})</span>'


def _next_actions(records: list[MemoryRecord]) -> list[tuple[str, str]]:
    """Derive (tag, text) recommended action pairs from the latest record."""
    if not records:
        return [("ok", "No records available.")]
    last = records[-1]
    fs = last.findings_summary
    actions: list[tuple[str, str]] = []

    critical = fs.get("critical", 0)
    generated = fs.get("generated", 0)
    manual = fs.get("manual", 0)

    if critical > 0:
        actions.append(
            (
                "critical",
                f"Review and address {critical} critical risk(s)"
                " — priority before any deployment.",
            )
        )
    if generated > 0:
        actions.append(
            (
                "generated",
                f"Apply {generated} auto-generated SQL remediation block(s) to staging"
                " (human approval required — never apply without review).",
            )
        )
    if manual > 0:
        actions.append(
            (
                "manual",
                f"Complete {manual} manual review action(s) — run 'aeos reclaim harden'"
                " with --output to export the full remediation plan.",
            )
        )
    if last.remediation_summary:
        phases = last.remediation_summary.get("phases_count", 0)
        if phases > 0:
            actions.append(
                (
                    "plan",
                    f"Follow the {phases}-phase remediation plan:"
                    " aeos reclaim harden --path <project> --output /tmp/report.md",
                )
            )
    if not actions:
        actions.append(
            (
                "ok",
                "No immediate actions required — maintain monitoring cadence.",
            )
        )
    return actions


def render_dashboard(data: DashboardData) -> str:
    """Build and return the complete HTML dashboard string."""
    project = escape(data.project_name)
    records = data.records
    entries = data.timeline.entries
    syn = data.timeline.synthesis
    last = records[-1] if records else None

    # ── Timeline table rows ──────────────────────────────────────────────────
    rows: list[str] = []
    prev_crit: int | None = None
    prev_imp: int | None = None
    prev_man: int | None = None
    prev_gen: int | None = None

    for i, entry in enumerate(entries):
        if i == len(entries) - 1:
            row_cls = "latest"
        elif i % 2 == 0:
            row_cls = "even"
        else:
            row_cls = "odd"
        ts = entry.created_at[:19].replace("T", " ")
        stat_cls = _status_cls(entry.status)
        rows.append(
            f"<tr class='{row_cls}'>"
            f"<td>{i + 1}</td>"
            f"<td style='color:#6e7681;font-size:11px'>{escape(ts)}</td>"
            f"<td><span class='{stat_cls}'>{escape(entry.status)}</span></td>"
            f"<td style='color:#6e7681;font-size:11px'>"
            f"{escape(entry.control_level)}</td>"
            f"<td class='num'>{_delta_html(entry.critical, prev_crit)}</td>"
            f"<td class='num'>{_delta_html(entry.important, prev_imp)}</td>"
            f"<td class='num'>{_delta_html(entry.manual, prev_man)}</td>"
            f"<td class='num'>{_delta_html(entry.generated, prev_gen)}</td>"
            f"<td style='color:#6e7681;font-size:10px'>{escape(entry.record_id)}</td>"
            "</tr>"
        )
        prev_crit = entry.critical
        prev_imp = entry.important
        prev_man = entry.manual
        prev_gen = entry.generated

    rows_html = "\n".join(rows)

    # ── Synthesis ────────────────────────────────────────────────────────────
    if syn and syn.record_count >= 2:

        def _kv(lbl: str, trend: str) -> str:
            tc = _trend_cls(trend)
            ta = _trend_arrow(trend)
            return (
                f"<div class='kv-item'>"
                f"<span class='kv-lbl'>{escape(lbl)}</span>"
                f"<span class='kv-val {tc}'>{ta} {escape(trend)}</span>"
                "</div>"
            )

        syn_html = (
            "<div class='kv'>"
            + _kv("Overall", syn.overall)
            + _kv("Critical", syn.critical_trend)
            + _kv("Important", syn.important_trend)
            + _kv("Manual", syn.manual_trend)
            + _kv("Gen SQL", syn.generated_trend)
            + f"<div class='kv-item'><span class='kv-lbl'>Records</span>"
            f"<span class='kv-val neutral'>{syn.record_count}</span></div>" + "</div>"
        )
    else:
        syn_html = (
            "<p style='color:#6e7681'>"
            "Insufficient data — need ≥ 2 records for synthesis.</p>"
        )

    # ── Current state KV ─────────────────────────────────────────────────────
    if last:
        fs = last.findings_summary
        crit_v = fs.get("critical", 0)
        crit_cls = "s-error" if crit_v > 0 else "s-ok"
        state_html = (
            "<div class='kv'>"
            + f"<div class='kv-item'><span class='kv-lbl'>Status</span>"
            f"<span class='kv-val {_status_cls(last.status)}'>"
            f"{escape(last.status)}</span></div>"
            + f"<div class='kv-item'><span class='kv-lbl'>Control</span>"
            f"<span class='kv-val neutral'>{escape(last.control_level)}</span></div>"
            + f"<div class='kv-item'><span class='kv-lbl'>Critical</span>"
            f"<span class='kv-val {crit_cls}'>{crit_v}</span></div>"
            + f"<div class='kv-item'><span class='kv-lbl'>Important</span>"
            f"<span class='kv-val neutral'>{fs.get('important', 0)}</span></div>"
            + f"<div class='kv-item'><span class='kv-lbl'>Manual</span>"
            f"<span class='kv-val neutral'>{fs.get('manual', 0)}</span></div>"
            + f"<div class='kv-item'><span class='kv-lbl'>Gen SQL</span>"
            f"<span class='kv-val neutral'>{fs.get('generated', 0)}</span></div>"
            + f"<div class='kv-item'><span class='kv-lbl'>Generator</span>"
            f"<span class='kv-val neutral' style='font-size:14px'>"
            f"{escape(last.generator or 'unknown')}</span></div>"
            + f"<div class='kv-item'><span class='kv-lbl'>Providers</span>"
            f"<span class='kv-val neutral' style='font-size:14px'>"
            f"{escape(', '.join(last.providers) if last.providers else 'none')}"
            "</span></div>" + "</div>"
        )
        # strategic options from last record
        if last.strategic_options:
            opts = "\n".join(
                f"<div class='option-item'>{escape(opt)}</div>"
                for opt in last.strategic_options
            )
            state_html += (
                "<h2>Strategic Exit Options</h2>"
                f"<div style='margin-top:8px'>{opts}</div>"
            )
    else:
        state_html = "<p style='color:#6e7681'>No records available.</p>"

    # ── Next actions ─────────────────────────────────────────────────────────
    action_items: list[str] = []
    for i, (tag, text) in enumerate(_next_actions(records), start=1):
        tag_html = (
            f"<span class='action-tag tag-{escape(tag)}'>{escape(tag.upper())}</span>"
        )
        action_items.append(
            f"<div class='action'>"
            f"<span class='action-num'>{i}.</span>{tag_html}{escape(text)}"
            "</div>"
        )
    actions_html = "\n".join(action_items)

    # ── Footer metadata ───────────────────────────────────────────────────────
    last_ts = last.created_at[:19].replace("T", " ") if last else "unknown"
    record_count = len(records)

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>AEOS Dashboard — {project}</title>\n"
        f"<style>{_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        "<header>\n"
        f"<h1>AEOS Recovery Dashboard</h1>\n"
        f"<div class='meta'>{project}</div>\n"
        "<div style='margin-top:8px'>\n"
        "<span class='badge badge-ro'>read_only: true</span>\n"
        "<span class='badge badge-app'>applied: false</span>\n"
        "<span class='badge badge-hum'>human validation required</span>\n"
        "</div>\n"
        "</header>\n"
        "<h2>Current Status</h2>\n"
        f"<div class='card'>{state_html}</div>\n"
        f"<h2>Memory Timeline — {record_count} record(s)</h2>\n"
        "<div class='card card-table'>\n"
        "<table>\n"
        "<thead><tr>"
        "<th>#</th><th>Date (UTC)</th><th>Status</th><th>Control</th>"
        "<th>Critical</th><th>Important</th><th>Manual</th><th>Gen SQL</th>"
        "<th>Record ID</th>"
        "</tr></thead>\n"
        f"<tbody>{rows_html}</tbody>\n"
        "</table>\n"
        "</div>\n"
        "<h2>Synthesis</h2>\n"
        f"<div class='card'>{syn_html}</div>\n"
        "<h2>Recommended Next Actions</h2>\n"
        f"<div class='card'>{actions_html}</div>\n"
        "<footer>\n"
        f"Generated by AEOS UI Dashboard · project: {project}"
        f" · last record: {escape(last_ts)} UTC"
        f" · {record_count} record(s)"
        " · read_only: true · applied: false · human validation required\n"
        "</footer>\n"
        "</body>\n"
        "</html>"
    )
