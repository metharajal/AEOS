"""
AEOS Apply Engine — controlled, evidence-first proposal apply.

Invariant: apply-log.md is written before any status transition.
Status → applied only after the artifact exists on disk.
Confirmation must equal "APPLY <proposal.id>" — no shortcuts, no --yes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from aeos.agent.pr_management import Proposal, ProposalStatus, update_proposal_status
from aeos.memory.models import MemoryRecord
from aeos.memory.store import build_memory_record_from_apply, save_record


@dataclass
class ApplyContext:
    """Input to run_apply(). confirmation must equal 'APPLY <proposal.id>'."""

    proposal: Proposal
    proposals_dir: Path
    memory_dir: Path
    project_name: str
    project_path: str
    confirmation: str


@dataclass
class ApplyResult:
    """Outcome of a successful apply."""

    proposal: Proposal  # status == applied
    apply_log_path: Path  # proposals_dir/<id>/apply-log.md
    memory_record: MemoryRecord
    memory_record_path: Path


def _build_apply_log_content(proposal: Proposal, confirmation: str) -> str:
    now = datetime.now(tz=UTC).isoformat()
    files_section = (
        "\n".join(f"- {f}" for f in proposal.files) if proposal.files else "(none)"
    )
    return (
        "# AEOS Apply Log\n"
        "\n"
        f"Proposal ID:   {proposal.id}\n"
        f"Title:         {proposal.title}\n"
        f"Applied at:    {now}\n"
        f"Confirmation:  {confirmation}\n"
        f"Applied by:    human\n"
        "\n"
        "## Summary\n"
        "\n"
        f"{proposal.summary or '(no summary)'}\n"
        "\n"
        "## Files\n"
        "\n"
        f"{files_section}\n"
        "\n"
        "applied: true  ·  read_only: false  ·  human_validated: true\n"
    )


def run_apply(context: ApplyContext) -> ApplyResult:
    """Apply a proposal under strict invariants.

    Sequence (non-negotiable):
      1. Guard: proposal.status == pending
      2. Guard: confirmation == "APPLY <proposal.id>"
      3. Write apply-log.md  ← real action; I/O error propagates here
      4. update_proposal_status → applied  (only after step 3 succeeds)
      5. build + save MemoryRecord

    Raises:
        ValueError: status is not pending, or confirmation does not match.
        OSError: if the apply-log write fails (proposal stays pending).
    """
    proposal = context.proposal

    if proposal.status != ProposalStatus.pending:
        raise ValueError(
            f"Cannot apply proposal '{proposal.id}': "
            f"status is '{proposal.status.value}', expected 'pending'."
        )

    expected = f"APPLY {proposal.id}"
    if context.confirmation != expected:
        raise ValueError(
            f"Invalid confirmation for proposal '{proposal.id}'. Expected '{expected}'."
        )

    # Step 3 — the real action; if this raises, nothing else runs
    apply_log_path = context.proposals_dir / proposal.id / "apply-log.md"
    apply_log_path.write_text(
        _build_apply_log_content(proposal, context.confirmation),
        encoding="utf-8",
    )

    # Step 4 — status transition only after artifact is on disk
    applied_proposal = update_proposal_status(
        context.proposals_dir,
        proposal.id,
        ProposalStatus.applied,
    )

    # Step 5 — knowledge record
    memory_record = build_memory_record_from_apply(
        proposal_id=applied_proposal.id,
        project_name=context.project_name,
        project_path=context.project_path,
        apply_log_path=apply_log_path,
    )
    memory_record_path = save_record(memory_record, context.memory_dir)

    return ApplyResult(
        proposal=applied_proposal,
        apply_log_path=apply_log_path,
        memory_record=memory_record,
        memory_record_path=memory_record_path,
    )
