"""
AEOS Agent PR Management — local, controlled, read-only proposal store.

No GitHub API. No git commands. No network. No mutations.
All proposals live under workspace/proposals/<id>/proposal.json.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

DEFAULT_PROPOSALS_DIR: Path = Path.home() / ".aeos" / "workspace" / "proposals"


class ProposalStatus(StrEnum):
    pending = "pending"
    applied = "applied"
    dismissed = "dismissed"


@dataclass
class Proposal:
    """A single controlled PR proposal stored locally."""

    id: str
    title: str
    status: ProposalStatus
    created_at: str
    summary: str
    files: list[str] = field(default_factory=list)
    diff_preview: str | None = None


class ProposalRepository:
    """Read-only repository of local PR proposals.

    Reads proposal.json files from proposals_dir/<id>/proposal.json.
    Never writes. Never calls network. Never calls git.
    """

    def __init__(self, proposals_dir: Path | None = None) -> None:
        self._dir = (
            proposals_dir if proposals_dir is not None else DEFAULT_PROPOSALS_DIR
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _parse_proposal(self, proposal_json: Path) -> Proposal:
        """Parse a single proposal.json. Raises ValueError on bad data."""
        try:
            raw = json.loads(proposal_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {proposal_json}: {exc}") from exc

        proposal_id = str(raw.get("id", proposal_json.parent.name))
        title = str(raw.get("title", ""))
        created_at = str(raw.get("created_at", ""))
        summary = str(raw.get("summary", ""))
        files = [str(f) for f in raw.get("files", [])]
        diff_preview = raw.get("diff_preview") or None

        raw_status = raw.get("status", "")
        try:
            status = ProposalStatus(raw_status)
        except ValueError as exc:
            raise ValueError(
                f"Invalid status '{raw_status}' in {proposal_json}. "
                f"Allowed: {[s.value for s in ProposalStatus]}"
            ) from exc

        return Proposal(
            id=proposal_id,
            title=title,
            status=status,
            created_at=created_at,
            summary=summary,
            files=files,
            diff_preview=diff_preview,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list(self) -> list[Proposal]:
        """Return all valid proposals sorted by created_at descending.

        Silently skips proposal directories with invalid JSON or invalid
        status so that one corrupt entry does not break the full list.
        """
        if not self._dir.exists():
            return []

        proposals: list[Proposal] = []
        for entry in sorted(self._dir.iterdir()):
            if not entry.is_dir():
                continue
            proposal_json = entry / "proposal.json"
            if not proposal_json.exists():
                continue
            try:
                proposals.append(self._parse_proposal(proposal_json))
            except ValueError:
                continue

        proposals.sort(key=lambda p: p.created_at, reverse=True)
        return proposals

    def get(self, proposal_id: str) -> Proposal | None:
        """Return a proposal by ID, or None if not found.

        Raises ValueError if the proposal.json exists but is invalid.
        """
        proposal_json = self._dir / proposal_id / "proposal.json"
        if not proposal_json.exists():
            return None
        return self._parse_proposal(proposal_json)


# ---------------------------------------------------------------------------
# Terminal renderers
# ---------------------------------------------------------------------------


def render_proposal_list(proposals: list[Proposal]) -> str:
    """Render a formatted table of proposals for terminal output."""
    if not proposals:
        return "No proposals found.\n"

    col_id = max(len(p.id) for p in proposals)
    col_id = max(col_id, 2)
    col_status = max(len(p.status.value) for p in proposals)
    col_status = max(col_status, 6)

    header = (
        f"{'ID':<{col_id}}  {'STATUS':<{col_status}}  TITLE\n"
        + "-" * (col_id + 2 + col_status + 2 + 40)
        + "\n"
    )
    rows = "".join(
        f"{p.id:<{col_id}}  {p.status.value:<{col_status}}  {p.title}\n"
        for p in proposals
    )
    return header + rows


def render_proposal_detail(proposal: Proposal) -> str:
    """Render the full detail of a proposal for terminal output."""
    lines: list[str] = []
    a = lines.append

    a("AEOS PR Proposal")
    a("")
    a(f"Title:    {proposal.title}")
    a(f"ID:       {proposal.id}")
    a(f"Status:   {proposal.status.value}")
    a(f"Created:  {proposal.created_at}")
    a("")
    a("Summary:")
    a(f"  {proposal.summary}" if proposal.summary else "  (no summary)")
    a("")

    if proposal.files:
        a("Files:")
        for f in proposal.files:
            a(f"  {f}")
        a("")

    if proposal.diff_preview:
        a("Diff Preview:")
        for line in proposal.diff_preview.splitlines()[:20]:
            a(f"  {line}")
        a("")

    a("Suggested command:")
    a(f"  aeos workspace apply-pr {proposal.id}")
    a("")
    a("read_only: true  ·  applied: false  ·  human validation required")

    return "\n".join(lines)
