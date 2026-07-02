"""
AEOS Agent PR Management — controlled proposal store.

No GitHub API. No git commands. No network.
ProposalRepository is read-only. The only write path in this module is
update_proposal_status() — a controlled status transition from pending only.
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


def update_proposal_status(
    proposals_dir: Path,
    proposal_id: str,
    new_status: ProposalStatus,
) -> Proposal:
    """Transition a proposal's status. Only allowed from pending.

    The only write path in this module. All other fields in proposal.json
    are preserved exactly. The caller (apply engine) is responsible for
    ensuring that the real action has succeeded before calling this function.

    Raises:
        FileNotFoundError: if proposals_dir/<proposal_id>/proposal.json does not exist.
        ValueError: if the proposal JSON is invalid or status is not pending.
    """
    proposal_json = proposals_dir / proposal_id / "proposal.json"
    if not proposal_json.exists():
        raise FileNotFoundError(
            f"Proposal '{proposal_id}' not found at {proposal_json}"
        )

    try:
        raw = json.loads(proposal_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {proposal_json}: {exc}") from exc

    raw_status = raw.get("status", "")
    try:
        current_status = ProposalStatus(raw_status)
    except ValueError as exc:
        raise ValueError(
            f"Invalid status '{raw_status}' in {proposal_json}. "
            f"Allowed: {[s.value for s in ProposalStatus]}"
        ) from exc

    if current_status != ProposalStatus.pending:
        raise ValueError(
            f"Cannot transition proposal '{proposal_id}': "
            f"current status is '{current_status.value}', expected 'pending'."
        )

    raw["status"] = new_status.value
    proposal_json.write_text(json.dumps(raw, indent=2), encoding="utf-8")

    diff_preview_raw = raw.get("diff_preview")
    return Proposal(
        id=str(raw.get("id", proposal_id)),
        title=str(raw.get("title", "")),
        status=new_status,
        created_at=str(raw.get("created_at", "")),
        summary=str(raw.get("summary", "")),
        files=[str(f) for f in raw.get("files", [])],
        diff_preview=str(diff_preview_raw) if diff_preview_raw is not None else None,
    )


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
    a(f"  aeos agent pr apply {proposal.id}")
    a("")
    a("read_only: true  ·  applied: false  ·  human validation required")

    return "\n".join(lines)
