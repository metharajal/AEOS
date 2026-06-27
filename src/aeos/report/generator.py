from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aeos.onboarding import check_project
from aeos.project import inspect_project
from aeos.project.inspector import InspectResult
from aeos.security import run_security_check
from aeos.security.checker import SecurityCheckResult
from aeos.sovereignty import run_sovereignty_check
from aeos.sovereignty.checker import SovereigntyCheckResult

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ReportSection:
    status: str
    summary: str
    details: dict[str, Any]


@dataclass
class ReportRisk:
    severity: str
    category: str
    message: str
    location: str


@dataclass
class ReportRecommendation:
    priority: int
    action: str


@dataclass
class ProjectReport:
    path: Path
    status: str
    sections: dict[str, ReportSection]
    top_risks: list[ReportRisk] = field(default_factory=list)
    recommendations: list[ReportRecommendation] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------


def _build_project_section(result: InspectResult) -> ReportSection:
    parts = [result.name]
    if result.remote_origin:
        parts.append(result.remote_origin)
    summary = " · ".join(parts)
    details: dict[str, Any] = {
        "name": result.name,
        "remote_origin": result.remote_origin,
        "aeos_toml": result.aeos_toml,
        "pyproject_toml": result.pyproject_toml,
        "readme": result.readme,
        "manifesto": result.manifesto,
        "constitution": result.constitution,
        "governance": result.governance,
        "src": result.src,
        "tests": result.tests,
        "docs": result.docs,
        "ci_yml": result.ci_yml,
        "git_present": result.git_present,
    }
    return ReportSection(status="OK", summary=summary, details=details)


def _build_governance_section(
    results: list[tuple[str, bool]],
) -> ReportSection:
    missing = [item for item, found in results if not found]
    present_count = sum(1 for _, found in results if found)
    total = len(results)
    status = "OK" if not missing else "WARNING"
    if missing:
        summary = (
            f"{present_count}/{total} items present — missing: {', '.join(missing)}"
        )
    else:
        summary = f"{total}/{total} items present"
    details: dict[str, Any] = {
        "total": total,
        "present": present_count,
        "missing": missing,
    }
    return ReportSection(status=status, summary=summary, details=details)


def _build_sovereignty_section(result: SovereigntyCheckResult) -> ReportSection:
    error_count = sum(1 for f in result.findings if f.severity == "ERROR")
    warning_count = sum(1 for f in result.findings if f.severity == "WARNING")
    findings_count = len(result.findings)
    top_findings: list[dict[str, Any]] = [
        {
            "category": f.category,
            "severity": f.severity,
            "message": f.message,
            "location": f.location,
        }
        for f in result.findings[:5]
    ]
    summary = (
        f"{findings_count} findings ({error_count} ERROR · {warning_count} WARNING)"
    )
    details: dict[str, Any] = {
        "findings_count": findings_count,
        "error_count": error_count,
        "warning_count": warning_count,
        "top_findings": top_findings,
    }
    return ReportSection(status=result.status, summary=summary, details=details)


def _build_security_section(result: SecurityCheckResult) -> ReportSection:
    error_count = sum(1 for f in result.findings if f.severity == "ERROR")
    warning_count = sum(1 for f in result.findings if f.severity == "WARNING")
    findings_count = len(result.findings)
    top_findings: list[dict[str, Any]] = [
        {
            "category": f.category,
            "severity": f.severity,
            "message": f.message,
            "location": f.location,
        }
        for f in result.findings[:5]
    ]
    summary = (
        f"{findings_count} findings ({error_count} ERROR · {warning_count} WARNING)"
    )
    details: dict[str, Any] = {
        "findings_count": findings_count,
        "error_count": error_count,
        "warning_count": warning_count,
        "top_findings": top_findings,
    }
    return ReportSection(status=result.status, summary=summary, details=details)


# ---------------------------------------------------------------------------
# Status computation
# ---------------------------------------------------------------------------


def _compute_report_status(sections: dict[str, ReportSection]) -> str:
    statuses = [s.status for s in sections.values()]
    if "ERROR" in statuses:
        return "ERROR"
    if "WARNING" in statuses:
        return "WARNING"
    return "OK"


# ---------------------------------------------------------------------------
# Top risks
# ---------------------------------------------------------------------------


def _build_top_risks(
    sovereignty_result: SovereigntyCheckResult,
    security_result: SecurityCheckResult,
    governance_section: ReportSection,
) -> list[ReportRisk]:
    risks: list[ReportRisk] = []
    seen: set[tuple[str, str, str, str]] = set()

    def _add(severity: str, category: str, message: str, location: str) -> None:
        if len(risks) >= 5:
            return
        key = (severity, category, message, location)
        if key in seen:
            return
        seen.add(key)
        risks.append(
            ReportRisk(
                severity=severity,
                category=category,
                message=message,
                location=location,
            )
        )

    # ERROR first: security then sovereignty
    for sf in security_result.findings:
        if sf.severity == "ERROR":
            _add(sf.severity, sf.category, sf.message, sf.location)
    for sv in sovereignty_result.findings:
        if sv.severity == "ERROR":
            _add(sv.severity, sv.category, sv.message, sv.location)

    # WARNING: security then sovereignty
    for sf in security_result.findings:
        if sf.severity == "WARNING":
            _add(sf.severity, sf.category, sf.message, sf.location)
    for sv in sovereignty_result.findings:
        if sv.severity == "WARNING":
            _add(sv.severity, sv.category, sv.message, sv.location)

    # Governance synthetic risk
    missing = governance_section.details.get("missing", [])
    if isinstance(missing, list) and missing:
        sample = ", ".join(str(m) for m in missing[:3])
        _add(
            "WARNING",
            "governance",
            f"Missing governance items: {sample}",
            "governance/",
        )

    return risks


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------


def _build_recommendations(
    governance_section: ReportSection,
    sovereignty_result: SovereigntyCheckResult,
    security_result: SecurityCheckResult,
) -> list[ReportRecommendation]:
    recs: list[ReportRecommendation] = []
    seen: set[str] = set()
    priority = 0

    def _add(action: str) -> None:
        nonlocal priority
        if action in seen:
            return
        seen.add(action)
        priority += 1
        recs.append(ReportRecommendation(priority=priority, action=action))

    sec = security_result.findings
    sov = sovereignty_result.findings

    # 1. env_files ERROR
    if any(f.category == "env_files" and f.severity == "ERROR" for f in sec):
        _add("Add .env and .env.* to .gitignore immediately")

    # 2. secrets ERROR
    if any(f.category == "secrets" and f.severity == "ERROR" for f in sec):
        _add("Remove hardcoded secrets from codebase")

    # 3. governance missing
    missing = governance_section.details.get("missing", [])
    if isinstance(missing, list) and missing:
        _add("Complete AEOS governance structure")

    # 4. sovereignty portability: Dockerfile
    if any(f.category == "portability" and "Dockerfile" in f.message for f in sov):
        _add("Add a Dockerfile for portable containerized deployment")

    # 5. sovereignty source_scan (external SaaS)
    if any(f.category == "source_scan" for f in sov):
        _add("Document external dependencies and plan exit strategy")

    # 6. security dependencies
    if any(f.category == "dependencies" for f in sec):
        _add("Add lockfiles or pin dependency hashes")

    # 7. Dockerfile config
    if any(
        f.category == "config" and ("USER" in f.message or "Dockerfile" in f.message)
        for f in sec
    ):
        _add("Set non-root USER in Dockerfile")

    # 8. GitHub Actions
    if any(
        f.category == "config"
        and (
            "pull_request_target" in f.message
            or "GitHub Actions" in f.message
            or "echo" in f.message
        )
        for f in sec
    ):
        _add("Audit GitHub Actions workflow permissions")

    # 9. Fallback
    if not recs:
        _add("No blocking issues — continue development")

    return recs[:6]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def generate_report(path: Path) -> ProjectReport:
    resolved = path.resolve()

    inspect_result = inspect_project(resolved)
    onboard_results = check_project(resolved)
    sovereignty_result = run_sovereignty_check(resolved)
    security_result = run_security_check(resolved)

    project_section = _build_project_section(inspect_result)
    governance_section = _build_governance_section(onboard_results)
    sovereignty_section = _build_sovereignty_section(sovereignty_result)
    security_section = _build_security_section(security_result)

    sections: dict[str, ReportSection] = {
        "project": project_section,
        "governance": governance_section,
        "sovereignty": sovereignty_section,
        "security": security_section,
    }

    status = _compute_report_status(sections)
    top_risks = _build_top_risks(
        sovereignty_result, security_result, governance_section
    )
    recommendations = _build_recommendations(
        governance_section, sovereignty_result, security_result
    )

    return ProjectReport(
        path=resolved,
        status=status,
        sections=sections,
        top_risks=top_risks,
        recommendations=recommendations,
    )
