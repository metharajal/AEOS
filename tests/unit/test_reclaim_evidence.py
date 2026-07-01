"""Tests for the Recovery Evidence Engine (Sprint 5E)."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from aeos.cli import app
from aeos.reclaim.evidence import (
    EvidenceItem,
    EvidenceReport,
    build_evidence_report,
    build_evidence_summary,
    evidence_report_to_dict,
    validate_confirmed_indices,
)
from aeos.reclaim.stages import get_recovery_stages, get_stage_by_id

runner = CliRunner()

_ALL_IDS = [s.id for s in get_recovery_stages()]
_FIRST_ID = _ALL_IDS[0]  # stage_0_baseline
_FIRST_STAGE = get_stage_by_id(_FIRST_ID)
assert _FIRST_STAGE is not None
_N = len(_FIRST_STAGE.expected_evidence)

# ---------------------------------------------------------------------------
# validate_confirmed_indices
# ---------------------------------------------------------------------------


def test_validate_confirmed_indices_all_valid() -> None:
    bad = validate_confirmed_indices(_FIRST_ID, [0, 1])
    assert bad == []


def test_validate_confirmed_indices_empty_is_valid() -> None:
    assert validate_confirmed_indices(_FIRST_ID, []) == []


def test_validate_confirmed_indices_negative_is_bad() -> None:
    bad = validate_confirmed_indices(_FIRST_ID, [-1])
    assert -1 in bad


def test_validate_confirmed_indices_out_of_bounds_is_bad() -> None:
    bad = validate_confirmed_indices(_FIRST_ID, [_N])
    assert _N in bad


def test_validate_confirmed_indices_mixed() -> None:
    bad = validate_confirmed_indices(_FIRST_ID, [0, _N, -1])
    assert _N in bad
    assert -1 in bad
    assert 0 not in bad


def test_validate_confirmed_indices_unknown_stage_returns_empty() -> None:
    assert validate_confirmed_indices("stage_99_unknown", [0]) == []


# ---------------------------------------------------------------------------
# build_evidence_report
# ---------------------------------------------------------------------------


def test_build_evidence_report_unknown_stage_returns_none() -> None:
    assert build_evidence_report("stage_99_unknown") is None


def test_build_evidence_report_returns_evidence_report() -> None:
    report = build_evidence_report(_FIRST_ID)
    assert isinstance(report, EvidenceReport)


def test_build_evidence_report_default_no_confirmed() -> None:
    report = build_evidence_report(_FIRST_ID)
    assert report is not None
    assert report.total_confirmed == 0
    assert report.total_pending == report.total_expected
    assert report.evidence_status == "unverified"


def test_build_evidence_report_none_confirmed_same_as_default() -> None:
    r1 = build_evidence_report(_FIRST_ID)
    r2 = build_evidence_report(_FIRST_ID, None)
    assert r1 == r2


def test_build_evidence_report_all_confirmed_verified() -> None:
    all_indices = list(range(_N))
    report = build_evidence_report(_FIRST_ID, all_indices)
    assert report is not None
    assert report.evidence_status == "verified"
    assert report.total_confirmed == _N
    assert report.total_pending == 0
    assert report.validation_blocked_reason is None


def test_build_evidence_report_partial() -> None:
    if _N < 2:
        return
    report = build_evidence_report(_FIRST_ID, [0])
    assert report is not None
    assert report.evidence_status == "partial"
    assert report.total_confirmed == 1
    assert report.total_pending == _N - 1
    assert report.validation_blocked_reason is not None
    assert "missing" in report.validation_blocked_reason


def test_build_evidence_report_unverified_has_blocked_reason() -> None:
    report = build_evidence_report(_FIRST_ID, [])
    assert report is not None
    assert report.evidence_status == "unverified"
    assert report.validation_blocked_reason == "No evidence confirmed for this stage."


def test_build_evidence_report_items_length() -> None:
    report = build_evidence_report(_FIRST_ID)
    assert report is not None
    assert len(report.items) == _N


def test_build_evidence_report_items_are_evidence_items() -> None:
    report = build_evidence_report(_FIRST_ID)
    assert report is not None
    for item in report.items:
        assert isinstance(item, EvidenceItem)


def test_build_evidence_report_items_indices_sequential() -> None:
    report = build_evidence_report(_FIRST_ID)
    assert report is not None
    for i, item in enumerate(report.items):
        assert item.index == i


def test_build_evidence_report_items_confirmed_status() -> None:
    report = build_evidence_report(_FIRST_ID, [0])
    assert report is not None
    assert report.items[0].status == "confirmed"
    for item in report.items[1:]:
        assert item.status == "pending"


def test_build_evidence_report_read_only_flag() -> None:
    report = build_evidence_report(_FIRST_ID)
    assert report is not None
    assert report.read_only is True


def test_build_evidence_report_applied_flag() -> None:
    report = build_evidence_report(_FIRST_ID)
    assert report is not None
    assert report.applied is False


def test_build_evidence_report_stage_name_set() -> None:
    report = build_evidence_report(_FIRST_ID)
    assert report is not None
    assert report.stage_name != ""


def test_build_evidence_report_partial_missing_message() -> None:
    if _N < 3:
        return
    report = build_evidence_report(_FIRST_ID, [0, 1])
    assert report is not None
    assert report.validation_blocked_reason is not None
    missing_count = _N - 2
    noun = "item" if missing_count == 1 else "items"
    blocked = report.validation_blocked_reason
    assert blocked is not None
    assert f"{missing_count} evidence {noun} missing" in blocked


def test_build_evidence_report_all_stages_return_report() -> None:
    for stage_id in _ALL_IDS:
        report = build_evidence_report(stage_id)
        assert report is not None, f"Expected report for {stage_id}"


# ---------------------------------------------------------------------------
# build_evidence_summary
# ---------------------------------------------------------------------------


def test_build_evidence_summary_returns_ten_reports() -> None:
    reports = build_evidence_summary()
    assert len(reports) == 10


def test_build_evidence_summary_all_are_evidence_reports() -> None:
    for r in build_evidence_summary():
        assert isinstance(r, EvidenceReport)


def test_build_evidence_summary_default_all_unverified() -> None:
    for r in build_evidence_summary():
        assert r.evidence_status == "unverified"


def test_build_evidence_summary_with_confirmed_by_stage() -> None:
    confirmed_by_stage = {_FIRST_ID: list(range(_N))}
    reports = build_evidence_summary(confirmed_by_stage)
    first = next(r for r in reports if r.stage_id == _FIRST_ID)
    assert first.evidence_status == "verified"


def test_build_evidence_summary_none_same_as_empty_dict() -> None:
    r1 = build_evidence_summary(None)
    r2 = build_evidence_summary({})
    assert r1 == r2


def test_build_evidence_summary_stage_ids_match_registry() -> None:
    reports = build_evidence_summary()
    report_ids = [r.stage_id for r in reports]
    assert report_ids == _ALL_IDS


# ---------------------------------------------------------------------------
# evidence_report_to_dict
# ---------------------------------------------------------------------------


def test_evidence_report_to_dict_keys() -> None:
    report = build_evidence_report(_FIRST_ID)
    assert report is not None
    d = evidence_report_to_dict(report)
    expected_keys = {
        "stage_id",
        "stage_name",
        "read_only",
        "applied",
        "total_expected",
        "total_confirmed",
        "total_pending",
        "evidence_status",
        "validation_blocked_reason",
        "items",
    }
    assert set(d.keys()) == expected_keys


def test_evidence_report_to_dict_items_keys() -> None:
    report = build_evidence_report(_FIRST_ID)
    assert report is not None
    d = evidence_report_to_dict(report)
    items = d["items"]
    assert isinstance(items, list)
    assert len(items) > 0
    for item in items:
        assert isinstance(item, dict)
        assert set(item.keys()) == {"index", "label", "status"}


def test_evidence_report_to_dict_is_json_serializable() -> None:
    report = build_evidence_report(_FIRST_ID)
    assert report is not None
    d = evidence_report_to_dict(report)
    serialized = json.dumps(d)
    assert isinstance(serialized, str)


def test_evidence_report_to_dict_values() -> None:
    report = build_evidence_report(_FIRST_ID, [0])
    assert report is not None
    d = evidence_report_to_dict(report)
    assert d["stage_id"] == _FIRST_ID
    assert d["read_only"] is True
    assert d["applied"] is False
    assert d["total_confirmed"] == 1
    assert d["evidence_status"] == "partial"


# ---------------------------------------------------------------------------
# CLI — aeos reclaim evidence report
# ---------------------------------------------------------------------------


def test_cli_evidence_report_unknown_stage_exits_1() -> None:
    result = runner.invoke(
        app, ["reclaim", "evidence", "report", "--stage", "stage_99"]
    )
    assert result.exit_code == 1
    assert "not found" in result.output


def test_cli_evidence_report_valid_stage_exits_0() -> None:
    result = runner.invoke(app, ["reclaim", "evidence", "report", "--stage", _FIRST_ID])
    assert result.exit_code == 0


def test_cli_evidence_report_json_output() -> None:
    result = runner.invoke(
        app, ["reclaim", "evidence", "report", "--stage", _FIRST_ID, "--json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["stage_id"] == _FIRST_ID
    assert "evidence_status" in data
    assert "items" in data


def test_cli_evidence_report_confirmed_indices() -> None:
    result = runner.invoke(
        app,
        ["reclaim", "evidence", "report", "--stage", _FIRST_ID, "--confirmed", "0"],
    )
    assert result.exit_code == 0
    assert "confirmed" in result.output


def test_cli_evidence_report_invalid_index_string_exits_1() -> None:
    result = runner.invoke(
        app,
        [
            "reclaim",
            "evidence",
            "report",
            "--stage",
            _FIRST_ID,
            "--confirmed",
            "abc",
        ],
    )
    assert result.exit_code == 1
    assert "not a valid integer" in result.output


def test_cli_evidence_report_out_of_bounds_index_exits_1() -> None:
    result = runner.invoke(
        app,
        [
            "reclaim",
            "evidence",
            "report",
            "--stage",
            _FIRST_ID,
            "--confirmed",
            str(_N),
        ],
    )
    assert result.exit_code == 1
    assert "out of bounds" in result.output


def test_cli_evidence_report_negative_index_exits_1() -> None:
    result = runner.invoke(
        app,
        [
            "reclaim",
            "evidence",
            "report",
            "--stage",
            _FIRST_ID,
            "--confirmed",
            "-1",
        ],
    )
    assert result.exit_code == 1
    assert "out of bounds" in result.output


def test_cli_evidence_report_text_shows_read_only() -> None:
    result = runner.invoke(app, ["reclaim", "evidence", "report", "--stage", _FIRST_ID])
    assert result.exit_code == 0
    assert "read_only: true" in result.output


# ---------------------------------------------------------------------------
# CLI — aeos reclaim evidence summary
# ---------------------------------------------------------------------------


def test_cli_evidence_summary_exits_0() -> None:
    result = runner.invoke(app, ["reclaim", "evidence", "summary"])
    assert result.exit_code == 0


def test_cli_evidence_summary_json_output() -> None:
    result = runner.invoke(app, ["reclaim", "evidence", "summary", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["total"] == 10
    assert len(data["reports"]) == 10
    assert data["read_only"] is True
    assert data["applied"] is False


def test_cli_evidence_summary_text_shows_ten_stages() -> None:
    result = runner.invoke(app, ["reclaim", "evidence", "summary"])
    assert result.exit_code == 0
    for stage_id in _ALL_IDS:
        assert stage_id in result.output


def test_cli_evidence_summary_text_shows_read_only() -> None:
    result = runner.invoke(app, ["reclaim", "evidence", "summary"])
    assert result.exit_code == 0
    assert "read_only: true" in result.output
