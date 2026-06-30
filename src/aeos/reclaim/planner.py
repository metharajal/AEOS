"""
AEOS Recovery Planner — transforms the stage registry into a structured plan.

Read-only. No filesystem access. No network. No secret reads. No MemoryRecord writes.
read_only: true · applied: false
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aeos.reclaim.stages import RecoveryStage, get_recovery_stages


@dataclass
class StageAssessment:
    """Status of one recovery stage given a set of completed stage IDs."""

    stage_id: str
    stage_name: str
    status: str  # "done" | "ready" | "blocked"
    missing_prerequisites: list[str] = field(default_factory=list)
    recommended_first_action: str = ""
    human_gate: str = ""
    memory_record_type: str = ""


@dataclass
class StagedRecoveryPlan:
    """Structured recovery plan derived from the stage registry. Read-only."""

    project_path: str
    read_only: bool
    applied: bool
    stages_done: list[str]
    stages_ready: list[str]
    stages_blocked: list[str]
    recommended_sequence: list[str]
    next_stage_id: str | None
    next_action: str | None
    items: list[StageAssessment]
    total: int


def validate_done_ids(done_ids: list[str]) -> list[str]:
    """Return the list of IDs not found in the stage registry. Empty means all valid."""
    known = {s.id for s in get_recovery_stages()}
    return [sid for sid in done_ids if sid not in known]


def assess_stage(stage: RecoveryStage, done_set: set[str]) -> StageAssessment:
    """Evaluate the status of one stage given a set of completed stage IDs."""
    if stage.id in done_set:
        return StageAssessment(
            stage_id=stage.id,
            stage_name=stage.name,
            status="done",
            missing_prerequisites=[],
            recommended_first_action="",
            human_gate=stage.human_gate,
            memory_record_type=stage.memory_record_type,
        )

    missing = [p for p in stage.prerequisites if p not in done_set]
    status = "blocked" if missing else "ready"
    first_action = stage.actions[0] if stage.actions else ""

    return StageAssessment(
        stage_id=stage.id,
        stage_name=stage.name,
        status=status,
        missing_prerequisites=missing,
        recommended_first_action=first_action,
        human_gate=stage.human_gate,
        memory_record_type=stage.memory_record_type,
    )


def build_staged_recovery_plan(
    done_ids: list[str] | None = None,
    project_path: str = "",
) -> StagedRecoveryPlan:
    """Build the structured plan from the stage registry and a set of completed stages.

    Read-only. No filesystem. No network. No MemoryRecord writes.
    """
    resolved = done_ids if done_ids is not None else []
    done_set = set(resolved)
    stages = get_recovery_stages()
    items = [assess_stage(s, done_set) for s in stages]

    stages_done = [a.stage_id for a in items if a.status == "done"]
    stages_ready = [a.stage_id for a in items if a.status == "ready"]
    stages_blocked = [a.stage_id for a in items if a.status == "blocked"]
    recommended_sequence = stages_done + stages_ready + stages_blocked

    next_item = next((a for a in items if a.status == "ready"), None)
    next_stage_id = next_item.stage_id if next_item else None
    next_action = next_item.recommended_first_action if next_item else None

    return StagedRecoveryPlan(
        project_path=project_path,
        read_only=True,
        applied=False,
        stages_done=stages_done,
        stages_ready=stages_ready,
        stages_blocked=stages_blocked,
        recommended_sequence=recommended_sequence,
        next_stage_id=next_stage_id,
        next_action=next_action,
        items=items,
        total=len(stages),
    )


def staged_plan_to_dict(plan: StagedRecoveryPlan) -> dict[str, object]:
    """Serialize a StagedRecoveryPlan to a JSON-compatible dict."""
    return {
        "read_only": plan.read_only,
        "applied": plan.applied,
        "project_path": plan.project_path,
        "total": plan.total,
        "stages_done": plan.stages_done,
        "stages_ready": plan.stages_ready,
        "stages_blocked": plan.stages_blocked,
        "recommended_sequence": plan.recommended_sequence,
        "next_stage_id": plan.next_stage_id,
        "next_action": plan.next_action,
        "items": [
            {
                "stage_id": a.stage_id,
                "stage_name": a.stage_name,
                "status": a.status,
                "missing_prerequisites": a.missing_prerequisites,
                "recommended_first_action": a.recommended_first_action,
                "human_gate": a.human_gate,
                "memory_record_type": a.memory_record_type,
            }
            for a in plan.items
        ],
    }
