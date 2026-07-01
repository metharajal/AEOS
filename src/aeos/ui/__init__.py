"""AEOS UI — static dashboard, workspace, evidence pack, and portfolio."""

from aeos.ui.dashboard import DashboardData, load_dashboard_data, render_dashboard
from aeos.ui.evidence_pack import (
    EvidencePackResult,
    generate_evidence_pack,
    render_human_gates,
    render_index,
    render_next_actions,
    render_recovery_summary,
    render_risk_register,
)
from aeos.ui.portfolio import (
    PortfolioData,
    PortfolioProjectEntry,
    load_portfolio_data,
    render_portfolio,
)
from aeos.ui.workspace import (
    ProductionReadiness,
    RecoveryProgress,
    WorkspaceData,
    load_workspace_data,
    render_workspace,
)

__all__ = [
    "DashboardData",
    "EvidencePackResult",
    "PortfolioData",
    "PortfolioProjectEntry",
    "ProductionReadiness",
    "RecoveryProgress",
    "WorkspaceData",
    "generate_evidence_pack",
    "load_dashboard_data",
    "load_portfolio_data",
    "load_workspace_data",
    "render_dashboard",
    "render_human_gates",
    "render_index",
    "render_next_actions",
    "render_portfolio",
    "render_recovery_summary",
    "render_risk_register",
    "render_workspace",
]
