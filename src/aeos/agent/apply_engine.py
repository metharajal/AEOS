"""
AEOS Apply Engine — controlled, evidence-first proposal apply.

Invariant: apply-log.json is written before any status transition.
Status → applied only after the artifact exists on disk.
Confirmation must equal "APPLY <proposal.id>" — no shortcuts, no --yes.
"""

from __future__ import annotations

import json
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
    apply_log_path: Path  # proposals_dir/<id>/apply-log.json
    memory_record: MemoryRecord
    memory_record_path: Path


def _build_apply_log_payload(
    proposal: Proposal, confirmation: str
) -> dict[str, object]:
    """Build the apply-log.json payload (spec §5.5 + V1 practical fields)."""
    return {
        "proposal_id": proposal.id,
        "title": proposal.title,
        "applied_at": datetime.now(tz=UTC).isoformat(),
        "applied_by": "aeos agent pr apply",
        "confirmation": confirmation,
        "validation_result": "passed",
        "human_confirmed": True,
        "aeos_version": None,
        "pre_apply_harden_record_id": None,
        "steps_applied": [],
        "steps_skipped": [],
        "backup_path": None,
        "files": list(proposal.files),
        "notes": None,
    }


def run_apply(context: ApplyContext) -> ApplyResult:
    """Apply a proposal under strict invariants.

    Sequence (non-negotiable):
      1. Guard: proposal.status == pending
      2. Guard: confirmation == "APPLY <proposal.id>"
      3. Guard: apply-log.json does not exist (APPLY.PRE.05)
      4. Write apply-log.json  ← real action; I/O error propagates here
      5. update_proposal_status → applied  (only after step 4 succeeds)
      6. build + save MemoryRecord

    Raises:
        ValueError: status is not pending, or confirmation does not match.
        FileExistsError: if apply-log.json already exists (APPLY.PRE.05).
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

    # Step 3 — APPLY.PRE.05: abort if a previous apply-log exists
    apply_log_path = context.proposals_dir / proposal.id / "apply-log.json"
    if apply_log_path.exists():
        raise FileExistsError(
            f"apply-log.json already exists at {apply_log_path}. "
            "Proposal may have been partially applied. "
            "Manual investigation required before re-applying."
        )

    # Step 4 — the real action; if this raises, nothing else runs
    apply_log_path.write_text(
        json.dumps(_build_apply_log_payload(proposal, context.confirmation), indent=2),
        encoding="utf-8",
    )

    # Step 5 — status transition only after artifact is on disk
    applied_proposal = update_proposal_status(
        context.proposals_dir,
        proposal.id,
        ProposalStatus.applied,
    )

    # Step 6 — knowledge record
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
