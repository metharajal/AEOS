"""Tests for the Recovery Planner (Sprint 5D)."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from aeos.cli import app
from aeos.reclaim.planner import (
    assess_stage,
    build_staged_recovery_plan,
    staged_plan_to_dict,
    validate_done_ids,
)
from aeos.reclaim.stages import get_recovery_stages, get_stage_by_id

runner = CliRunner()

_ALL_IDS = [s.id for s in get_recovery_stages()]

# ---------------------------------------------------------------------------
# validate_done_ids
# ---------------------------------------------------------------------------


def test_validate_done_ids_empty_is_valid() -> None:
    assert validate_done_ids([]) == []


def test_validate_done_ids_all_valid() -> None:
    assert validate_done_ids(_ALL_IDS) == []


def test_validate_done_ids_unknown_returned() -> None:
    unknown = validate_done_ids(["stage_99_fake", "stage_0_baseline"])
    assert unknown == ["stage_99_fake"]


def test_validate_done_ids_multiple_unknown() -> None:
    unknown = validate_done_ids(["bad_a", "stage_0_baseline", "bad_b"])
    assert "bad_a" in unknown
    assert "bad_b" in unknown
    assert "stage_0_baseline" not in unknown


# ---------------------------------------------------------------------------
# assess_stage
# ---------------------------------------------------------------------------


def test_assess_stage_done() -> None:
    stage = get_stage_by_id("stage_0_baseline")
    assert stage is not None
    result = assess_stage(stage, {"stage_0_baseline"})
    assert result.status == "done"
    assert result.missing_prerequisites == []
    assert result.recommended_first_action == ""


def test_assess_stage_ready_no_prereqs() -> None:
    stage = get_stage_by_id("stage_0_baseline")
    assert stage is not None
    result = assess_stage(stage, set())
    assert result.status == "ready"
    assert result.missing_prerequisites == []
    assert result.recommended_first_action != ""


def test_assess_stage_ready_prereqs_met() -> None:
    stage = get_stage_by_id("stage_1_governance")
    assert stage is not None
    result = assess_stage(stage, {"stage_0_baseline"})
    assert result.status == "ready"
    assert result.missing_prerequisites == []


def test_assess_stage_blocked_missing_prereq() -> None:
    stage = get_stage_by_id("stage_1_governance")
    assert stage is not None
    result = assess_stage(stage, set())
    assert result.status == "blocked"
    assert "stage_0_baseline" in result.missing_prerequisites


def test_assess_stage_blocked_partial_prereqs() -> None:
    stage = get_stage_by_id("stage_9_sovereign_operating_mode")
    assert stage is not None
    # Only stage_0 done — still blocked (needs 0, 1, 2, 4)
    result = assess_stage(stage, {"stage_0_baseline"})
    assert result.status == "blocked"
    assert len(result.missing_prerequisites) >= 3


def test_assess_stage_recommended_first_action_for_ready() -> None:
    stage = get_stage_by_id("stage_0_baseline")
    assert stage is not None
    result = assess_stage(stage, set())
    assert result.recommended_first_action == stage.actions[0]


def test_assess_stage_preserves_human_gate() -> None:
    stage = get_stage_by_id("stage_0_baseline")
    assert stage is not None
    result = assess_stage(stage, set())
    assert result.human_gate == stage.human_gate


def test_assess_stage_preserves_memory_record_type() -> None:
    stage = get_stage_by_id("stage_7_migration_readiness")
    assert stage is not None
    result = assess_stage(stage, set())
    assert result.memory_record_type == stage.memory_record_type


# ---------------------------------------------------------------------------
# build_staged_recovery_plan — structure
# ---------------------------------------------------------------------------


def test_plan_total_is_ten() -> None:
    plan = build_staged_recovery_plan()
    assert plan.total == 10


def test_plan_items_count_is_ten() -> None:
    plan = build_staged_recovery_plan()
    assert len(plan.items) == 10


def test_plan_read_only_true() -> None:
    plan = build_staged_recovery_plan()
    assert plan.read_only is True


def test_plan_applied_false() -> None:
    plan = build_staged_recovery_plan()
    assert plan.applied is False


def test_plan_recommended_sequence_covers_all_stages() -> None:
    plan = build_staged_recovery_plan()
    assert set(plan.recommended_sequence) == set(_ALL_IDS)


def test_plan_recommended_sequence_length() -> None:
    plan = build_staged_recovery_plan()
    assert len(plan.recommended_sequence) == 10


def test_plan_items_order_matches_registry() -> None:
    plan = build_staged_recovery_plan()
    ids = [a.stage_id for a in plan.items]
    assert ids == _ALL_IDS


# ---------------------------------------------------------------------------
# build_staged_recovery_plan — empty done_ids
# ---------------------------------------------------------------------------


def test_plan_no_done_stage_0_is_ready() -> None:
    plan = build_staged_recovery_plan()
    assert "stage_0_baseline" in plan.stages_ready


def test_plan_no_done_no_stages_done() -> None:
    plan = build_staged_recovery_plan()
    assert plan.stages_done == []


def test_plan_no_done_next_stage_is_stage_0() -> None:
    plan = build_staged_recovery_plan()
    assert plan.next_stage_id == "stage_0_baseline"


def test_plan_no_done_next_action_is_not_none() -> None:
    plan = build_staged_recovery_plan()
    assert plan.next_action is not None
    assert len(plan.next_action) > 0


def test_plan_no_done_nine_stages_blocked() -> None:
    plan = build_staged_recovery_plan()
    # stage_0 has no prereqs → ready; all others blocked
    assert len(plan.stages_blocked) == 9


# ---------------------------------------------------------------------------
# build_staged_recovery_plan — partial done_ids
# ---------------------------------------------------------------------------


def test_plan_done_stage_0_stage_1_becomes_ready() -> None:
    plan = build_staged_recovery_plan(done_ids=["stage_0_baseline"])
    assert "stage_1_governance" in plan.stages_ready


def test_plan_done_stage_0_stage_0_is_done() -> None:
    plan = build_staged_recovery_plan(done_ids=["stage_0_baseline"])
    assert "stage_0_baseline" in plan.stages_done


def test_plan_done_stage_0_1_unlocks_2_4_5() -> None:
    plan = build_staged_recovery_plan(
        done_ids=["stage_0_baseline", "stage_1_governance"]
    )
    ready = set(plan.stages_ready)
    assert "stage_2_secrets_env" in ready
    assert "stage_4_tests_ci" in ready
    assert "stage_5_local_run" in ready


def test_plan_done_stage_0_1_stage_3_still_blocked() -> None:
    plan = build_staged_recovery_plan(
        done_ids=["stage_0_baseline", "stage_1_governance"]
    )
    assert "stage_3_database_rls" in plan.stages_blocked


def test_plan_recommended_sequence_done_before_ready_before_blocked() -> None:
    plan = build_staged_recovery_plan(done_ids=["stage_0_baseline"])
    done_indices = [plan.recommended_sequence.index(s) for s in plan.stages_done]
    ready_indices = [plan.recommended_sequence.index(s) for s in plan.stages_ready]
    blocked_indices = [plan.recommended_sequence.index(s) for s in plan.stages_blocked]
    assert max(done_indices) < min(ready_indices)
    assert max(ready_indices) < min(blocked_indices)


# ---------------------------------------------------------------------------
# build_staged_recovery_plan — all done
# ---------------------------------------------------------------------------


def test_plan_all_done_no_ready() -> None:
    plan = build_staged_recovery_plan(done_ids=_ALL_IDS)
    assert plan.stages_ready == []


def test_plan_all_done_no_blocked() -> None:
    plan = build_staged_recovery_plan(done_ids=_ALL_IDS)
    assert plan.stages_blocked == []


def test_plan_all_done_next_stage_is_none() -> None:
    plan = build_staged_recovery_plan(done_ids=_ALL_IDS)
    assert plan.next_stage_id is None


def test_plan_all_done_next_action_is_none() -> None:
    plan = build_staged_recovery_plan(done_ids=_ALL_IDS)
    assert plan.next_action is None


def test_plan_none_done_ids_treated_as_empty() -> None:
    plan_none = build_staged_recovery_plan(done_ids=None)
    plan_empty = build_staged_recovery_plan(done_ids=[])
    assert plan_none.stages_done == plan_empty.stages_done
    assert plan_none.stages_ready == plan_empty.stages_ready


# ---------------------------------------------------------------------------
# staged_plan_to_dict
# ---------------------------------------------------------------------------


def test_staged_plan_to_dict_top_level_keys() -> None:
    plan = build_staged_recovery_plan()
    d = staged_plan_to_dict(plan)
    expected = {
        "read_only",
        "applied",
        "project_path",
        "total",
        "stages_done",
        "stages_ready",
        "stages_blocked",
        "recommended_sequence",
        "next_stage_id",
        "next_action",
        "items",
    }
    assert set(d.keys()) == expected


def test_staged_plan_to_dict_read_only_is_true() -> None:
    d = staged_plan_to_dict(build_staged_recovery_plan())
    assert d["read_only"] is True


def test_staged_plan_to_dict_applied_is_false() -> None:
    d = staged_plan_to_dict(build_staged_recovery_plan())
    assert d["applied"] is False


def test_staged_plan_to_dict_is_json_serializable() -> None:
    d = staged_plan_to_dict(build_staged_recovery_plan(done_ids=["stage_0_baseline"]))
    serialized = json.dumps(d)
    assert isinstance(serialized, str)


def test_staged_plan_to_dict_item_keys() -> None:
    d = staged_plan_to_dict(build_staged_recovery_plan())
    item = d["items"][0]  # type: ignore[index]
    assert isinstance(item, dict)
    expected_item_keys = {
        "stage_id",
        "stage_name",
        "status",
        "missing_prerequisites",
        "recommended_first_action",
        "human_gate",
        "memory_record_type",
    }
    assert set(item.keys()) == expected_item_keys


# ---------------------------------------------------------------------------
# CLI — aeos reclaim stage plan
# ---------------------------------------------------------------------------


def test_cli_stage_plan_no_args_exits_0() -> None:
    result = runner.invoke(app, ["reclaim", "stage", "plan"])
    assert result.exit_code == 0


def test_cli_stage_plan_text_contains_staged_recovery_plan() -> None:
    result = runner.invoke(app, ["reclaim", "stage", "plan"])
    assert result.exit_code == 0
    assert "Staged Recovery Plan" in result.output


def test_cli_stage_plan_text_mentions_read_only() -> None:
    result = runner.invoke(app, ["reclaim", "stage", "plan"])
    assert "read_only: true" in result.output
    assert "applied: false" in result.output


def test_cli_stage_plan_text_shows_ready_section() -> None:
    result = runner.invoke(app, ["reclaim", "stage", "plan"])
    assert result.exit_code == 0
    assert "READY" in result.output


def test_cli_stage_plan_text_shows_blocked_section() -> None:
    result = runner.invoke(app, ["reclaim", "stage", "plan"])
    assert result.exit_code == 0
    assert "BLOCKED" in result.output


def test_cli_stage_plan_json_exits_0() -> None:
    result = runner.invoke(app, ["reclaim", "stage", "plan", "--json"])
    assert result.exit_code == 0


def test_cli_stage_plan_json_valid() -> None:
    result = runner.invoke(app, ["reclaim", "stage", "plan", "--json"])
    data = json.loads(result.output)
    assert data["read_only"] is True
    assert data["applied"] is False
    assert data["total"] == 10


def test_cli_stage_plan_json_next_stage_is_stage_0_when_no_done() -> None:
    result = runner.invoke(app, ["reclaim", "stage", "plan", "--json"])
    data = json.loads(result.output)
    assert data["next_stage_id"] == "stage_0_baseline"


def test_cli_stage_plan_done_stage_0_exits_0() -> None:
    result = runner.invoke(
        app, ["reclaim", "stage", "plan", "--done", "stage_0_baseline"]
    )
    assert result.exit_code == 0


def test_cli_stage_plan_done_stage_0_json_shows_done() -> None:
    result = runner.invoke(
        app, ["reclaim", "stage", "plan", "--done", "stage_0_baseline", "--json"]
    )
    data = json.loads(result.output)
    assert "stage_0_baseline" in data["stages_done"]
    assert "stage_1_governance" in data["stages_ready"]


def test_cli_stage_plan_done_multiple_comma_separated() -> None:
    result = runner.invoke(
        app,
        [
            "reclaim",
            "stage",
            "plan",
            "--done",
            "stage_0_baseline,stage_1_governance",
            "--json",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "stage_0_baseline" in data["stages_done"]
    assert "stage_1_governance" in data["stages_done"]
    assert "stage_2_secrets_env" in data["stages_ready"]


def test_cli_stage_plan_done_shows_done_section_in_text() -> None:
    result = runner.invoke(
        app, ["reclaim", "stage", "plan", "--done", "stage_0_baseline"]
    )
    assert result.exit_code == 0
    assert "DONE" in result.output
    assert "stage_0_baseline" in result.output


def test_cli_stage_plan_unknown_id_exits_1() -> None:
    result = runner.invoke(
        app, ["reclaim", "stage", "plan", "--done", "stage_99_fake"]
    )
    assert result.exit_code == 1


def test_cli_stage_plan_unknown_id_error_message() -> None:
    result = runner.invoke(
        app, ["reclaim", "stage", "plan", "--done", "stage_99_fake"]
    )
    assert "stage_99_fake" in result.output


def test_cli_stage_plan_unknown_mixed_with_valid_exits_1() -> None:
    result = runner.invoke(
        app,
        [
            "reclaim",
            "stage",
            "plan",
            "--done",
            "stage_0_baseline,stage_99_fake",
        ],
    )
    assert result.exit_code == 1


def test_cli_stage_plan_all_done_json_no_next_stage() -> None:
    all_ids = ",".join(_ALL_IDS)
    result = runner.invoke(
        app, ["reclaim", "stage", "plan", "--done", all_ids, "--json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["next_stage_id"] is None
    assert data["next_action"] is None
    assert data["stages_ready"] == []
    assert data["stages_blocked"] == []
