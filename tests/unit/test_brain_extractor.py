"""Unit tests for BrainExtractor (CAP-2-B).

Tests are pure: no filesystem I/O except for BrainStore (uses tmp_path).
extract_from_record() is tested with in-memory MemoryRecord objects.
build() is tested against a real BrainStore opened on tmp_path.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aeos.brain.extractor import (
    BrainExtractor,
    ExtractionResult,
    _is_safe,
    _make_identity,
    _normalize_path,
)
from aeos.brain.models import KnowledgeFact
from aeos.brain.store import BrainStore
from aeos.memory.models import MemoryRecord

# ---------------------------------------------------------------------------
# Test fixture helpers
# ---------------------------------------------------------------------------


def _make_record(
    record_id: str = "rec-001",
    project_name: str = "test-proj",
    project_path: str = "/nonexistent/test-proj",
    rail: str = "reclaim",
    command: str = "reclaim harden",
    status: str = "OK",
    generator: str | None = None,
    providers: list[str] | None = None,
    control_level: str = "controlled",
    findings_summary: dict[str, int] | None = None,
    remediation_summary: dict[str, int] | None = None,
    strategic_options: list[str] | None = None,
    applied: bool = False,
    human_validated: bool = False,
) -> MemoryRecord:
    return MemoryRecord(
        record_id=record_id,
        created_at="2026-01-15T10:00:00+00:00",
        project_path=project_path,
        project_name=project_name,
        rail=rail,
        command=command,
        status=status,
        generator=generator,
        providers=providers or [],
        control_level=control_level,
        read_only=True,
        applied=applied,
        findings_summary=findings_summary or {},
        remediation_summary=remediation_summary,
        strategic_options=strategic_options or [],
        human_validated=human_validated,
    )


def _open_brain(tmp_path: Path, project: str = "test-proj") -> BrainStore:
    return BrainStore.open(tmp_path / "brain", project)


def _write_record_json(
    memory_dir: Path, project_name: str, record: MemoryRecord
) -> None:
    project_dir = memory_dir / project_name
    project_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "record_id": record.record_id,
        "created_at": record.created_at,
        "project_path": record.project_path,
        "project_name": record.project_name,
        "rail": record.rail,
        "command": record.command,
        "status": record.status,
        "generator": record.generator,
        "providers": record.providers,
        "control_level": record.control_level,
        "read_only": record.read_only,
        "applied": record.applied,
        "findings_summary": record.findings_summary,
        "remediation_summary": record.remediation_summary,
        "strategic_options": record.strategic_options,
        "human_validated": record.human_validated,
    }
    (project_dir / f"{record.record_id}.json").write_text(
        json.dumps(data), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Timeline fact — always produced
# ---------------------------------------------------------------------------


class TestTimelineFact:
    def test_always_produces_timeline_fact(self, tmp_path: Path) -> None:
        record = _make_record()
        with _open_brain(tmp_path) as brain:
            extractor = BrainExtractor(brain)
            facts = extractor.extract_from_record(record)
        timeline_facts = [f for f in facts if f.fact_type == "TIMELINE"]
        assert len(timeline_facts) == 1

    def test_timeline_fact_type_and_dimension(self, tmp_path: Path) -> None:
        record = _make_record()
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        tf = next(f for f in facts if f.fact_type == "TIMELINE")
        assert tf.fact_type == "TIMELINE"
        assert tf.dimension == "TIMELINE"

    def test_timeline_id_scheme(self, tmp_path: Path) -> None:
        record = _make_record(record_id="my-record-42")
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        tf = next(f for f in facts if f.fact_type == "TIMELINE")
        assert tf.id == "my-record-42::timeline"

    def test_timeline_source_record(self, tmp_path: Path) -> None:
        record = _make_record(record_id="src-001")
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        tf = next(f for f in facts if f.fact_type == "TIMELINE")
        assert tf.source_record == "src-001"

    def test_timeline_source_date(self, tmp_path: Path) -> None:
        record = _make_record()
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        tf = next(f for f in facts if f.fact_type == "TIMELINE")
        assert tf.source_date == record.created_at

    def test_timeline_severity_ok(self, tmp_path: Path) -> None:
        record = _make_record(status="OK")
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        tf = next(f for f in facts if f.fact_type == "TIMELINE")
        assert tf.severity == "INFO"

    def test_timeline_severity_warning(self, tmp_path: Path) -> None:
        record = _make_record(status="WARNING")
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        tf = next(f for f in facts if f.fact_type == "TIMELINE")
        assert tf.severity == "MEDIUM"

    def test_timeline_severity_critical(self, tmp_path: Path) -> None:
        record = _make_record(status="CRITICAL")
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        tf = next(f for f in facts if f.fact_type == "TIMELINE")
        assert tf.severity == "HIGH"

    def test_timeline_summary_normal(self, tmp_path: Path) -> None:
        record = _make_record(command="reclaim harden", status="OK")
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        tf = next(f for f in facts if f.fact_type == "TIMELINE")
        assert "reclaim harden" in tf.summary
        assert "OK" in tf.summary

    def test_timeline_summary_human_confirmed(self, tmp_path: Path) -> None:
        record = _make_record(
            rail="agent",
            command="agent pr apply",
            applied=True,
            human_validated=True,
        )
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        tf = next(f for f in facts if f.fact_type == "TIMELINE")
        assert "human confirmed" in tf.summary

    def test_timeline_detail_is_valid_json(self, tmp_path: Path) -> None:
        record = _make_record()
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        tf = next(f for f in facts if f.fact_type == "TIMELINE")
        assert tf.detail is not None
        parsed = json.loads(tf.detail)
        assert "rail" in parsed
        assert "command" in parsed


# ---------------------------------------------------------------------------
# Reclaim-specific facts
# ---------------------------------------------------------------------------


class TestReclaimFacts:
    def test_critical_finding_produced(self, tmp_path: Path) -> None:
        record = _make_record(findings_summary={"critical": 3})
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        ids = {f.id for f in facts}
        assert "rec-001::critical" in ids

    def test_critical_finding_zero_not_produced(self, tmp_path: Path) -> None:
        record = _make_record(findings_summary={"critical": 0})
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        ids = {f.id for f in facts}
        assert "rec-001::critical" not in ids

    def test_critical_fact_type_dimension_severity(self, tmp_path: Path) -> None:
        record = _make_record(findings_summary={"critical": 2})
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        cf = next(f for f in facts if f.id.endswith("::critical"))
        assert cf.fact_type == "FINDING"
        assert cf.dimension == "SECURITY"
        assert cf.severity == "CRITICAL"

    def test_important_finding_produced(self, tmp_path: Path) -> None:
        record = _make_record(findings_summary={"important": 5})
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        ids = {f.id for f in facts}
        assert "rec-001::important" in ids

    def test_important_fact_severity_is_high(self, tmp_path: Path) -> None:
        record = _make_record(findings_summary={"important": 1})
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        imf = next(f for f in facts if f.id.endswith("::important"))
        assert imf.severity == "HIGH"
        assert imf.dimension == "SECURITY"

    def test_manual_finding_produced(self, tmp_path: Path) -> None:
        record = _make_record(findings_summary={"manual": 2})
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        ids = {f.id for f in facts}
        assert "rec-001::manual" in ids

    def test_manual_fact_dimension_is_recovery(self, tmp_path: Path) -> None:
        record = _make_record(findings_summary={"manual": 1})
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        mf = next(f for f in facts if f.id.endswith("::manual"))
        assert mf.dimension == "RECOVERY"
        assert mf.severity == "MEDIUM"

    def test_remediation_fact_produced(self, tmp_path: Path) -> None:
        record = _make_record(
            remediation_summary={"phases_count": 2, "immediate": 5, "manual": 3}
        )
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        ids = {f.id for f in facts}
        assert "rec-001::remediation" in ids

    def test_remediation_fact_not_produced_when_all_zero(
        self, tmp_path: Path
    ) -> None:
        record = _make_record(
            remediation_summary={"phases_count": 0, "immediate": 0}
        )
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        ids = {f.id for f in facts}
        assert "rec-001::remediation" not in ids

    def test_control_level_low_produces_high_sovereignty(
        self, tmp_path: Path
    ) -> None:
        record = _make_record(control_level="low")
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        ctrl = next(f for f in facts if f.id.endswith("::control"))
        assert ctrl.fact_type == "SOVEREIGNTY"
        assert ctrl.dimension == "SOVEREIGNTY"
        assert ctrl.severity == "HIGH"
        assert "sovereignty at risk" in ctrl.summary

    def test_control_level_partial_produces_medium(self, tmp_path: Path) -> None:
        record = _make_record(control_level="partial")
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        ctrl = next(f for f in facts if f.id.endswith("::control"))
        assert ctrl.severity == "MEDIUM"

    def test_control_level_controlled_produces_info(self, tmp_path: Path) -> None:
        record = _make_record(control_level="controlled")
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        ctrl = next(f for f in facts if f.id.endswith("::control"))
        assert ctrl.severity == "INFO"

    def test_provider_fact_produced(self, tmp_path: Path) -> None:
        record = _make_record(providers=["supabase"])
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        ids = {f.id for f in facts}
        assert "rec-001::provider::supabase" in ids

    def test_provider_fact_type_and_dimension(self, tmp_path: Path) -> None:
        record = _make_record(providers=["supabase"])
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        pf = next(f for f in facts if "::provider::" in f.id)
        assert pf.fact_type == "ARCH"
        assert pf.dimension == "ARCH"
        assert pf.severity == "INFO"

    def test_generator_fact_produced(self, tmp_path: Path) -> None:
        record = _make_record(generator="lovable")
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        ids = {f.id for f in facts}
        assert "rec-001::generator" in ids

    def test_generator_fact_summary(self, tmp_path: Path) -> None:
        record = _make_record(generator="bolt")
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        gf = next(f for f in facts if f.id.endswith("::generator"))
        assert "bolt" in gf.summary

    def test_strategic_option_fact_produced(self, tmp_path: Path) -> None:
        record = _make_record(strategic_options=["Migrate to open stack"])
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        ids = {f.id for f in facts}
        assert "rec-001::option::0" in ids

    def test_strategic_option_summary_contains_exit_option(
        self, tmp_path: Path
    ) -> None:
        record = _make_record(strategic_options=["Remove Supabase dependency"])
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        of = next(f for f in facts if "::option::" in f.id)
        assert "Exit option" in of.summary


# ---------------------------------------------------------------------------
# Secret filtering
# ---------------------------------------------------------------------------


class TestSecretFiltering:
    def test_provider_that_looks_like_jwt_is_filtered(self, tmp_path: Path) -> None:
        jwt_like = "eyJhbGciOiJIUzI1NiJ9" + "A" * 25
        record = _make_record(providers=[jwt_like])
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        provider_facts = [f for f in facts if "::provider::" in f.id]
        assert len(provider_facts) == 0

    def test_safe_provider_not_filtered(self, tmp_path: Path) -> None:
        record = _make_record(providers=["supabase"])
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        provider_facts = [f for f in facts if "::provider::" in f.id]
        assert len(provider_facts) == 1

    def test_generator_that_looks_like_key_is_filtered(self, tmp_path: Path) -> None:
        key_like = "sk_live_" + "x" * 30
        record = _make_record(generator=key_like)
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        generator_facts = [f for f in facts if "::generator" in f.id]
        assert len(generator_facts) == 0

    def test_is_safe_passes_normal_fact(self) -> None:
        fact = KnowledgeFact(
            id="x::timeline",
            fact_type="TIMELINE",
            dimension="TIMELINE",
            summary='"reclaim harden" completed — status: OK',
            created_at="2026-01-01T00:00:00+00:00",
        )
        assert _is_safe(fact) is True

    def test_is_safe_rejects_jwt_in_summary(self) -> None:
        fact = KnowledgeFact(
            id="x::timeline",
            fact_type="TIMELINE",
            dimension="TIMELINE",
            summary="eyJhbGciOiJIUzI1NiJ9" + "A" * 25,
            created_at="2026-01-01T00:00:00+00:00",
        )
        assert _is_safe(fact) is False


# ---------------------------------------------------------------------------
# Project path handling
# ---------------------------------------------------------------------------


class TestNormalizePath:
    def test_path_not_under_home_returns_basename(self) -> None:
        result = _normalize_path("/nonexistent/ma-mairie-digitale")
        assert result == "ma-mairie-digitale"

    def test_path_under_home_returns_tilde_relative(self) -> None:
        home = Path.home()
        path = str(home / "projects" / "my-app")
        result = _normalize_path(path)
        assert result == "~/projects/my-app"

    def test_project_path_not_in_identity_facts(self, tmp_path: Path) -> None:
        project_path = "/nonexistent/secret-client-project"
        record = _make_record(project_path=project_path)
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        for fact in facts:
            assert project_path not in (fact.summary or "")
            assert project_path not in (fact.detail or "")

    def test_make_identity_uses_normalized_path(self) -> None:
        record = _make_record(project_path="/nonexistent/the-project")
        identity = _make_identity("the-project", record)
        assert identity.project_path == "the-project"
        assert "/nonexistent" not in identity.project_path


# ---------------------------------------------------------------------------
# Agent rail
# ---------------------------------------------------------------------------


class TestAgentRail:
    def test_agent_rail_only_produces_timeline(self, tmp_path: Path) -> None:
        record = _make_record(
            rail="agent",
            command="agent pr apply",
            applied=True,
            human_validated=True,
        )
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        assert len(facts) == 1
        assert facts[0].fact_type == "TIMELINE"

    def test_agent_rail_not_applied_has_no_human_confirmed(
        self, tmp_path: Path
    ) -> None:
        record = _make_record(
            rail="agent",
            command="agent pr apply",
            applied=False,
            human_validated=False,
        )
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        tf = facts[0]
        assert "human confirmed" not in tf.summary


# ---------------------------------------------------------------------------
# Idempotency and determinism
# ---------------------------------------------------------------------------


class TestIdempotency:
    def test_same_record_yields_same_fact_ids(self, tmp_path: Path) -> None:
        record = _make_record(
            findings_summary={"critical": 1},
            providers=["supabase"],
        )
        with _open_brain(tmp_path) as brain:
            extractor = BrainExtractor(brain)
            facts_a = extractor.extract_from_record(record)
            facts_b = extractor.extract_from_record(record)
        assert {f.id for f in facts_a} == {f.id for f in facts_b}

    def test_provider_id_is_deterministic(self, tmp_path: Path) -> None:
        record = _make_record(record_id="abc", providers=["stripe"])
        with _open_brain(tmp_path) as brain:
            facts = BrainExtractor(brain).extract_from_record(record)
        pf = next(f for f in facts if "::provider::" in f.id)
        assert pf.id == "abc::provider::stripe"


# ---------------------------------------------------------------------------
# build() method
# ---------------------------------------------------------------------------


class TestBrainExtractorBuild:
    def test_build_raises_when_project_memory_missing(
        self, tmp_path: Path
    ) -> None:
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        with _open_brain(tmp_path) as brain:
            extractor = BrainExtractor(brain)
            with pytest.raises(FileNotFoundError):
                extractor.build("nonexistent", memory_dir)

    def test_build_returns_zero_counts_when_no_json_files(
        self, tmp_path: Path
    ) -> None:
        memory_dir = tmp_path / "memory"
        (memory_dir / "test-proj").mkdir(parents=True)
        with _open_brain(tmp_path) as brain:
            extractor = BrainExtractor(brain)
            result = extractor.build("test-proj", memory_dir)
        assert result.records_processed == 0
        assert result.facts_extracted == 0
        assert result.facts_inserted == 0

    def test_build_processes_records_correctly(self, tmp_path: Path) -> None:
        memory_dir = tmp_path / "memory"
        record = _make_record(findings_summary={"critical": 1})
        _write_record_json(memory_dir, "test-proj", record)
        with _open_brain(tmp_path) as brain:
            extractor = BrainExtractor(brain)
            result = extractor.build("test-proj", memory_dir)
        assert result.records_processed == 1
        assert result.facts_extracted >= 1
        assert result.facts_inserted >= 1

    def test_build_is_idempotent(self, tmp_path: Path) -> None:
        memory_dir = tmp_path / "memory"
        record = _make_record(findings_summary={"critical": 1})
        _write_record_json(memory_dir, "test-proj", record)
        with _open_brain(tmp_path) as brain:
            extractor = BrainExtractor(brain)
            result1 = extractor.build("test-proj", memory_dir)
            result2 = extractor.build("test-proj", memory_dir)
        assert result1.facts_inserted > 0
        assert result2.facts_inserted == 0

    def test_build_upserts_project_identity(self, tmp_path: Path) -> None:
        memory_dir = tmp_path / "memory"
        record = _make_record(project_path="/nonexistent/test-proj")
        _write_record_json(memory_dir, "test-proj", record)
        with _open_brain(tmp_path) as brain:
            extractor = BrainExtractor(brain)
            extractor.build("test-proj", memory_dir)
            identity = brain.get_identity()
        assert identity is not None
        assert identity.project_name == "test-proj"

    def test_build_skips_corrupt_json_files(self, tmp_path: Path) -> None:
        memory_dir = tmp_path / "memory"
        project_dir = memory_dir / "test-proj"
        project_dir.mkdir(parents=True)
        (project_dir / "bad-record.json").write_text(
            "not valid json", encoding="utf-8"
        )
        valid = _make_record()
        _write_record_json(memory_dir, "test-proj", valid)
        with _open_brain(tmp_path) as brain:
            extractor = BrainExtractor(brain)
            result = extractor.build("test-proj", memory_dir)
        assert result.records_processed == 1

    def test_build_returns_extraction_result_type(self, tmp_path: Path) -> None:
        memory_dir = tmp_path / "memory"
        (memory_dir / "test-proj").mkdir(parents=True)
        with _open_brain(tmp_path) as brain:
            extractor = BrainExtractor(brain)
            result = extractor.build("test-proj", memory_dir)
        assert isinstance(result, ExtractionResult)

    def test_build_multiple_records(self, tmp_path: Path) -> None:
        memory_dir = tmp_path / "memory"
        r1 = _make_record(record_id="rec-001")
        r2 = _make_record(record_id="rec-002", findings_summary={"critical": 2})
        _write_record_json(memory_dir, "test-proj", r1)
        _write_record_json(memory_dir, "test-proj", r2)
        with _open_brain(tmp_path) as brain:
            extractor = BrainExtractor(brain)
            result = extractor.build("test-proj", memory_dir)
        assert result.records_processed == 2
        assert result.facts_inserted >= 2
