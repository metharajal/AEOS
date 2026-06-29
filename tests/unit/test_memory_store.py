"""
Unit tests for aeos.memory — MemoryRecord, build_memory_record_from_reclaim_harden,
save_record.
No network access. No real git repos. No secret values read.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from aeos.memory.models import MemoryRecord
from aeos.memory.store import (
    _iter_string_leaves,
    _looks_like_secret_value,
    build_memory_record_from_reclaim_harden,
    save_record,
)
from aeos.reclaim.hardener import (
    ReclaimHardenResult,
    ReclaimHardenSummary,
    RemediationPhase,
    RemediationPlan,
)
from aeos.reclaim.inspector import (
    ReclaimControlMap,
    ReclaimExitOption,
    ReclaimGenerator,
    ReclaimInspectResult,
    ReclaimProvider,
)
from aeos.security.checker import SecurityCheckResult
from aeos.sovereignty.checker import SovereigntyCheckResult

# ---------------------------------------------------------------------------
# Fixtures / builders
# ---------------------------------------------------------------------------


def _make_control_map(
    portability: str = "partial",
    secrets_exposure: str = "none",
) -> ReclaimControlMap:
    return ReclaimControlMap(
        frontend_code="partial",
        backend_runtime="likely_external",
        database_schema="partial",
        auth="external",
        storage="likely_external",
        secrets_control="external",
        deployment="external",
        portability=portability,
        secrets_exposure=secrets_exposure,
    )


def _make_exit_options() -> list[ReclaimExitOption]:
    return [
        ReclaimExitOption(
            id="1",
            label="Stay on current provider but secure",
            complexity="low",
            sovereignty="partial",
            advantages=["No migration required"],
            risks=["Continued lock-in"],
            next_action="Rotate exposed keys",
        ),
        ReclaimExitOption(
            id="2",
            label="Migrate to own Supabase Cloud project",
            complexity="medium",
            sovereignty="medium",
            advantages=["Own the project"],
            risks=["Data export required"],
            next_action="Export schema",
        ),
    ]


def _make_reclaim(secrets_exposure: str = "none") -> ReclaimInspectResult:
    generators = [
        ReclaimGenerator(name="lovable", detected=True, evidence=".lovable/:1"),
        ReclaimGenerator(name="bolt", detected=False, evidence=""),
    ]
    providers = [
        ReclaimProvider(
            name="supabase",
            detected=True,
            roles=["database", "auth"],
            evidence="supabase/migrations/:1",
        ),
    ]
    return ReclaimInspectResult(
        path=Path("/fake/project"),
        status="WARNING",
        generators=generators,
        providers=providers,
        control_map=_make_control_map(secrets_exposure=secrets_exposure),
        exit_options=_make_exit_options(),
        recommended_next_action="Run aeos supabase check",
    )


def _make_security(status: str = "WARNING") -> SecurityCheckResult:
    return SecurityCheckResult(
        path=Path("/fake/project"),
        status=status,
        findings=[],
    )


def _make_sovereignty(status: str = "WARNING") -> SovereigntyCheckResult:
    return SovereigntyCheckResult(
        path=Path("/fake/project"),
        status=status,
        findings=[],
    )


def _make_supabase_mock(status: str = "WARNING") -> MagicMock:
    m = MagicMock()
    m.status = status
    m.remediation_steps = []
    return m


def _make_rls_mock(verdict: str = "WARNING") -> MagicMock:
    m = MagicMock()
    m.verdict = verdict
    m.summary.todo_blocks = 3
    m.summary.auto_blocks = 25
    m.inspect.findings = []
    return m


def _make_plan() -> RemediationPlan:
    phase = RemediationPhase(
        id="phase_0",
        label="Immediate security stabilization",
        priority="critical",
        goal="Neutralize all active security risks.",
        why_it_matters="Exposed credentials remain active until rotated.",
        actions=["Rotate exposed keys.", "Remove .env from Git."],
        automation_level="manual",
        expected_outcome="No exposed credentials.",
        risk_if_skipped="Breach window remains open.",
    )
    return RemediationPlan(
        phases=[phase],
        phases_count=1,
        immediate_actions_count=2,
        manual_actions_count=2,
        generatable_actions_count=25,
        strategic_options_count=5,
    )


def _make_harden_result(
    status: str = "WARNING",
    secrets_exposure: str = "none",
    with_plan: bool = True,
) -> ReclaimHardenResult:
    reclaim = _make_reclaim(secrets_exposure=secrets_exposure)
    security = _make_security()
    sovereignty = _make_sovereignty()
    supabase = _make_supabase_mock()
    rls = _make_rls_mock()
    summary = ReclaimHardenSummary(
        generator_detected="lovable",
        providers_detected=["supabase"],
        control_level="partial",
        secrets_exposure=secrets_exposure,
        security_status="WARNING",
        sovereignty_status="WARNING",
        supabase_status="WARNING",
        rls_verdict="WARNING",
        generated_actions=25,
        manual_actions=3,
        critical_findings=0,
        important_findings=2,
    )
    return ReclaimHardenResult(
        path=Path("/fake/project"),
        status=status,
        summary=summary,
        reclaim=reclaim,
        security=security,
        sovereignty=sovereignty,
        supabase=supabase,
        rls=rls,
        recommendations=["Review RLS TODO blocks."],
        exit_options=[
            "1. [low/partial] Stay on current provider but secure",
            "2. [medium/medium] Migrate to own Supabase Cloud project",
        ],
        remediation_plan=_make_plan() if with_plan else None,
        read_only=True,
        applied=False,
    )


# ---------------------------------------------------------------------------
# TestMemoryRecordModel
# ---------------------------------------------------------------------------


class TestMemoryRecordModel:
    def test_required_fields(self) -> None:
        r = MemoryRecord(
            record_id="proj-20260629T120000-abc12345",
            created_at="2026-06-29T12:00:00+00:00",
            project_path="/fake/project",
            project_name="project",
            rail="reclaim",
            command="reclaim harden",
            status="WARNING",
            generator="lovable",
            providers=["supabase"],
            control_level="partial",
            read_only=True,
            applied=False,
            findings_summary={
                "critical": 0,
                "important": 2,
                "manual": 3,
                "generated": 25,
            },
            remediation_summary=None,
            strategic_options=["1. Stay on current provider"],
        )
        assert r.record_id == "proj-20260629T120000-abc12345"
        assert r.project_name == "project"
        assert r.rail == "reclaim"
        assert r.command == "reclaim harden"

    def test_defaults(self) -> None:
        r = MemoryRecord(
            record_id="x",
            created_at="2026-06-29T12:00:00+00:00",
            project_path="/p",
            project_name="p",
            rail="reclaim",
            command="reclaim harden",
            status="OK",
            generator=None,
            providers=[],
            control_level="controlled",
            read_only=True,
            applied=False,
            findings_summary={},
            remediation_summary=None,
            strategic_options=[],
        )
        assert r.human_validated is False
        assert r.notes is None

    def test_read_only_enforced_by_model(self) -> None:
        r = MemoryRecord(
            record_id="x",
            created_at="2026-06-29T12:00:00+00:00",
            project_path="/p",
            project_name="p",
            rail="reclaim",
            command="reclaim harden",
            status="OK",
            generator=None,
            providers=[],
            control_level="controlled",
            read_only=True,
            applied=False,
            findings_summary={},
            remediation_summary=None,
            strategic_options=[],
        )
        assert r.read_only is True
        assert r.applied is False


# ---------------------------------------------------------------------------
# TestBuildMemoryRecord
# ---------------------------------------------------------------------------


class TestBuildMemoryRecord:
    def test_record_id_contains_project_name(self) -> None:
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        assert "project" in record.record_id

    def test_record_project_name(self) -> None:
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/myapp"))
        assert record.project_name == "myapp"

    def test_record_rail_and_command(self) -> None:
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        assert record.rail == "reclaim"
        assert record.command == "reclaim harden"

    def test_record_status(self) -> None:
        result = _make_harden_result(status="ERROR")
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        assert record.status == "ERROR"

    def test_record_generator(self) -> None:
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        assert record.generator == "lovable"

    def test_record_providers(self) -> None:
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        assert record.providers == ["supabase"]

    def test_record_read_only_true(self) -> None:
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        assert record.read_only is True

    def test_record_applied_false(self) -> None:
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        assert record.applied is False

    def test_record_human_validated_false_by_default(self) -> None:
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        assert record.human_validated is False

    def test_record_findings_summary_keys(self) -> None:
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        assert set(record.findings_summary.keys()) == {
            "critical",
            "important",
            "manual",
            "generated",
        }

    def test_record_findings_counts(self) -> None:
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        assert record.findings_summary["generated"] == 25
        assert record.findings_summary["manual"] == 3

    def test_record_remediation_summary_present_when_plan(self) -> None:
        result = _make_harden_result(with_plan=True)
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        assert record.remediation_summary is not None
        assert record.remediation_summary["phases_count"] == 1
        assert record.remediation_summary["generatable"] == 25

    def test_record_remediation_summary_none_when_no_plan(self) -> None:
        result = _make_harden_result(with_plan=False)
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        assert record.remediation_summary is None

    def test_record_strategic_options_truncated(self) -> None:
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        for opt in record.strategic_options:
            assert len(opt) <= 80

    def test_record_created_at_is_iso(self) -> None:
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        assert "T" in record.created_at
        has_tz = (
            "+" in record.created_at
            or "Z" in record.created_at
            or record.created_at.endswith("+00:00")
        )
        assert has_tz

    def test_record_project_path_is_string(self) -> None:
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        assert isinstance(record.project_path, str)


# ---------------------------------------------------------------------------
# TestSaveRecord
# ---------------------------------------------------------------------------


class TestSaveRecord:
    def test_save_creates_file(self, tmp_path: Path) -> None:
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        path = save_record(record, tmp_path)
        assert path.exists()

    def test_save_writes_valid_json(self, tmp_path: Path) -> None:
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        path = save_record(record, tmp_path)
        data = json.loads(path.read_text())
        assert isinstance(data, dict)

    def test_save_json_has_required_fields(self, tmp_path: Path) -> None:
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        path = save_record(record, tmp_path)
        data = json.loads(path.read_text())
        required = {
            "record_id",
            "created_at",
            "project_path",
            "project_name",
            "rail",
            "command",
            "status",
            "generator",
            "providers",
            "control_level",
            "read_only",
            "applied",
            "findings_summary",
            "remediation_summary",
            "strategic_options",
            "human_validated",
            "notes",
        }
        assert required.issubset(data.keys())

    def test_save_json_read_only_true(self, tmp_path: Path) -> None:
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        path = save_record(record, tmp_path)
        data = json.loads(path.read_text())
        assert data["read_only"] is True

    def test_save_json_applied_false(self, tmp_path: Path) -> None:
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        path = save_record(record, tmp_path)
        data = json.loads(path.read_text())
        assert data["applied"] is False

    def test_save_json_has_remediation_summary(self, tmp_path: Path) -> None:
        result = _make_harden_result(with_plan=True)
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        path = save_record(record, tmp_path)
        data = json.loads(path.read_text())
        assert data["remediation_summary"] is not None
        assert "phases_count" in data["remediation_summary"]

    def test_save_creates_project_subdir(self, tmp_path: Path) -> None:
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/myapp"))
        save_record(record, tmp_path)
        assert (tmp_path / "myapp").is_dir()

    def test_save_memory_dir_configurable(self, tmp_path: Path) -> None:
        custom_dir = tmp_path / "custom-memory"
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        path = save_record(record, custom_dir)
        assert path.is_relative_to(custom_dir)

    def test_save_does_not_write_to_client_project(self, tmp_path: Path) -> None:
        client_project = tmp_path / "client-project"
        client_project.mkdir()
        memory_dir = tmp_path / "aeos-memory"
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, client_project)
        path = save_record(record, memory_dir)
        assert not path.is_relative_to(client_project)

    def test_save_refuses_jwt_value(self, tmp_path: Path) -> None:
        record = MemoryRecord(
            record_id="test-id",
            created_at="2026-06-29T12:00:00+00:00",
            project_path="/fake/project",
            project_name="project",
            rail="reclaim",
            command="reclaim harden",
            status="OK",
            generator=None,
            providers=[],
            control_level="controlled",
            read_only=True,
            applied=False,
            findings_summary={},
            remediation_summary=None,
            # Inject a JWT-like string in notes to test the guard
            strategic_options=[
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
                "eyJzdWIiOiIxMjM0NTY3ODkwIn0.secret"
            ],
            human_validated=False,
            notes=None,
        )
        with pytest.raises(ValueError, match="credential pattern"):
            save_record(record, tmp_path)

    def test_save_json_human_validated_false(self, tmp_path: Path) -> None:
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        path = save_record(record, tmp_path)
        data = json.loads(path.read_text())
        assert data["human_validated"] is False

    def test_save_json_notes_null(self, tmp_path: Path) -> None:
        result = _make_harden_result()
        record = build_memory_record_from_reclaim_harden(result, Path("/fake/project"))
        path = save_record(record, tmp_path)
        data = json.loads(path.read_text())
        assert data["notes"] is None


# ---------------------------------------------------------------------------
# TestSecretGuard
# ---------------------------------------------------------------------------


class TestSecretGuard:
    def test_jwt_detected(self) -> None:
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.secret"
        assert _looks_like_secret_value(jwt) is True

    def test_long_base64_detected(self) -> None:
        b64 = "A" * 65
        assert _looks_like_secret_value(b64) is True

    def test_short_string_safe(self) -> None:
        assert _looks_like_secret_value("lovable") is False

    def test_status_string_safe(self) -> None:
        assert _looks_like_secret_value("WARNING") is False

    def test_exit_option_label_safe(self) -> None:
        label = "1. [low/partial] Stay on current provider but secure"
        assert _looks_like_secret_value(label) is False

    def test_iso_timestamp_safe(self) -> None:
        assert _looks_like_secret_value("2026-06-29T12:00:00+00:00") is False


# ---------------------------------------------------------------------------
# TestIterStringLeaves
# ---------------------------------------------------------------------------


class TestIterStringLeaves:
    def test_flat_dict(self) -> None:
        obj = {"a": "hello", "b": "world"}
        result = _iter_string_leaves(obj)
        assert sorted(result) == ["hello", "world"]

    def test_nested_dict(self) -> None:
        obj = {"outer": {"inner": "deep"}}
        result = _iter_string_leaves(obj)
        assert "deep" in result

    def test_list_of_strings(self) -> None:
        obj = ["foo", "bar"]
        result = _iter_string_leaves(obj)
        assert result == ["foo", "bar"]

    def test_ignores_non_strings(self) -> None:
        obj = {"a": 1, "b": True, "c": None, "d": "keep"}
        result = _iter_string_leaves(obj)
        assert result == ["keep"]

    def test_mixed_nested(self) -> None:
        obj = {"a": ["x", "y"], "b": {"c": "z"}}
        result = _iter_string_leaves(obj)
        assert sorted(result) == ["x", "y", "z"]
