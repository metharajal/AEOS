"""Tests for the Recovery Stage Model (Sprint 5C)."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from aeos.cli import app
from aeos.reclaim.stages import (
    RecoveryStage,
    get_recovery_stages,
    get_stage_by_id,
    recovery_stage_to_dict,
)

runner = CliRunner()

_EXPECTED_IDS = [
    "stage_0_baseline",
    "stage_1_governance",
    "stage_2_secrets_env",
    "stage_3_database_rls",
    "stage_4_tests_ci",
    "stage_5_local_run",
    "stage_6_portability",
    "stage_7_migration_readiness",
    "stage_8_local_ai_continuation",
    "stage_9_sovereign_operating_mode",
]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def test_get_recovery_stages_returns_ten() -> None:
    assert len(get_recovery_stages()) == 10


def test_stage_ids_are_unique() -> None:
    ids = [s.id for s in get_recovery_stages()]
    assert len(ids) == len(set(ids))


def test_stage_ids_match_expected() -> None:
    ids = [s.id for s in get_recovery_stages()]
    assert ids == _EXPECTED_IDS


def test_stages_ordered_ascending_by_numeric_prefix() -> None:
    stages = get_recovery_stages()
    prefixes = [int(s.id.split("_")[1]) for s in stages]
    assert prefixes == list(range(10))


# ---------------------------------------------------------------------------
# RecoveryStage dataclass
# ---------------------------------------------------------------------------


def test_all_stages_have_non_empty_name() -> None:
    for stage in get_recovery_stages():
        assert stage.name, f"{stage.id}: name is empty"


def test_all_stages_have_non_empty_objective() -> None:
    for stage in get_recovery_stages():
        assert stage.objective, f"{stage.id}: objective is empty"


def test_all_stages_have_non_empty_human_gate() -> None:
    for stage in get_recovery_stages():
        assert stage.human_gate, f"{stage.id}: human_gate is empty"


def test_all_stages_have_non_empty_memory_record_type() -> None:
    for stage in get_recovery_stages():
        assert stage.memory_record_type, f"{stage.id}: memory_record_type is empty"


def test_all_stages_have_at_least_one_action() -> None:
    for stage in get_recovery_stages():
        assert stage.actions, f"{stage.id}: actions list is empty"


def test_all_stages_have_at_least_one_risk() -> None:
    for stage in get_recovery_stages():
        assert stage.risks, f"{stage.id}: risks list is empty"


def test_all_stages_have_at_least_one_evidence() -> None:
    for stage in get_recovery_stages():
        assert stage.expected_evidence, f"{stage.id}: expected_evidence is empty"


def test_all_stages_have_at_least_one_agent() -> None:
    for stage in get_recovery_stages():
        assert stage.allowed_agents, f"{stage.id}: allowed_agents is empty"


def test_stage_0_has_no_prerequisites() -> None:
    stage = get_stage_by_id("stage_0_baseline")
    assert stage is not None
    assert stage.prerequisites == []


def test_stage_1_requires_stage_0() -> None:
    stage = get_stage_by_id("stage_1_governance")
    assert stage is not None
    assert "stage_0_baseline" in stage.prerequisites


def test_stage_9_requires_multiple_prerequisites() -> None:
    stage = get_stage_by_id("stage_9_sovereign_operating_mode")
    assert stage is not None
    assert len(stage.prerequisites) >= 4


def test_stage_0_rollback_path_is_none() -> None:
    stage = get_stage_by_id("stage_0_baseline")
    assert stage is not None
    assert stage.rollback_path is None


def test_stage_7_has_rollback_path() -> None:
    stage = get_stage_by_id("stage_7_migration_readiness")
    assert stage is not None
    assert stage.rollback_path is not None
    assert len(stage.rollback_path) > 0


def test_stage_dataclass_fields() -> None:
    stage = RecoveryStage(id="test", name="Test", objective="Test objective")
    assert stage.prerequisites == []
    assert stage.actions == []
    assert stage.risks == []
    assert stage.expected_evidence == []
    assert stage.human_gate == ""
    assert stage.rollback_path is None
    assert stage.memory_record_type == ""
    assert stage.allowed_agents == []


# ---------------------------------------------------------------------------
# get_stage_by_id
# ---------------------------------------------------------------------------


def test_get_stage_by_id_found() -> None:
    stage = get_stage_by_id("stage_0_baseline")
    assert stage is not None
    assert stage.id == "stage_0_baseline"


def test_get_stage_by_id_not_found_returns_none() -> None:
    assert get_stage_by_id("stage_99_nonexistent") is None


def test_get_stage_by_id_all_ids_resolve() -> None:
    for stage_id in _EXPECTED_IDS:
        stage = get_stage_by_id(stage_id)
        assert stage is not None, f"get_stage_by_id({stage_id!r}) returned None"
        assert stage.id == stage_id


# ---------------------------------------------------------------------------
# recovery_stage_to_dict
# ---------------------------------------------------------------------------


def test_recovery_stage_to_dict_has_all_keys() -> None:
    stage = get_stage_by_id("stage_0_baseline")
    assert stage is not None
    d = recovery_stage_to_dict(stage)
    expected_keys = {
        "id",
        "name",
        "objective",
        "prerequisites",
        "actions",
        "risks",
        "expected_evidence",
        "human_gate",
        "rollback_path",
        "memory_record_type",
        "allowed_agents",
    }
    assert set(d.keys()) == expected_keys


def test_recovery_stage_to_dict_is_json_serializable() -> None:
    for stage in get_recovery_stages():
        d = recovery_stage_to_dict(stage)
        serialized = json.dumps(d)
        assert isinstance(serialized, str)


def test_recovery_stage_to_dict_rollback_none_for_stage_0() -> None:
    stage = get_stage_by_id("stage_0_baseline")
    assert stage is not None
    d = recovery_stage_to_dict(stage)
    assert d["rollback_path"] is None


# ---------------------------------------------------------------------------
# CLI — aeos reclaim stage list
# ---------------------------------------------------------------------------


def test_cli_stage_list_exits_0() -> None:
    result = runner.invoke(app, ["reclaim", "stage", "list"])
    assert result.exit_code == 0


def test_cli_stage_list_contains_all_ids() -> None:
    result = runner.invoke(app, ["reclaim", "stage", "list"])
    assert result.exit_code == 0
    for stage_id in _EXPECTED_IDS:
        assert stage_id in result.output


def test_cli_stage_list_json_valid() -> None:
    result = runner.invoke(app, ["reclaim", "stage", "list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["read_only"] is True
    assert data["applied"] is False
    assert data["total"] == 10
    assert len(data["stages"]) == 10


def test_cli_stage_list_json_contains_all_ids() -> None:
    result = runner.invoke(app, ["reclaim", "stage", "list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    ids = [s["id"] for s in data["stages"]]
    assert ids == _EXPECTED_IDS


def test_cli_stage_list_text_mentions_read_only() -> None:
    result = runner.invoke(app, ["reclaim", "stage", "list"])
    assert "read_only: true" in result.output
    assert "applied: false" in result.output


# ---------------------------------------------------------------------------
# CLI — aeos reclaim stage show
# ---------------------------------------------------------------------------


def test_cli_stage_show_valid_id_exits_0() -> None:
    result = runner.invoke(
        app, ["reclaim", "stage", "show", "--id", "stage_0_baseline"]
    )
    assert result.exit_code == 0


def test_cli_stage_show_contains_stage_id() -> None:
    result = runner.invoke(
        app, ["reclaim", "stage", "show", "--id", "stage_1_governance"]
    )
    assert result.exit_code == 0
    assert "stage_1_governance" in result.output


def test_cli_stage_show_invalid_id_exits_1() -> None:
    result = runner.invoke(
        app, ["reclaim", "stage", "show", "--id", "stage_99_fake"]
    )
    assert result.exit_code == 1


def test_cli_stage_show_invalid_id_error_message() -> None:
    result = runner.invoke(
        app, ["reclaim", "stage", "show", "--id", "stage_99_fake"]
    )
    assert "stage_99_fake" in result.output


def test_cli_stage_show_json_valid() -> None:
    result = runner.invoke(
        app, ["reclaim", "stage", "show", "--id", "stage_3_database_rls", "--json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == "stage_3_database_rls"
    assert "actions" in data
    assert "risks" in data
    assert "expected_evidence" in data


def test_cli_stage_show_mentions_read_only() -> None:
    result = runner.invoke(
        app, ["reclaim", "stage", "show", "--id", "stage_0_baseline"]
    )
    assert "read_only: true" in result.output
    assert "applied: false" in result.output


def test_cli_stage_show_all_stages_exit_0() -> None:
    for stage_id in _EXPECTED_IDS:
        result = runner.invoke(
            app, ["reclaim", "stage", "show", "--id", stage_id]
        )
        assert result.exit_code == 0, (
            f"stage show --id {stage_id} failed: {result.output}"
        )
