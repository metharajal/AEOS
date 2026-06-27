"""Unit tests for aeos.security.checker — Sprint 2O Security Check MVP."""

import json
from pathlib import Path

import pytest

from aeos.security.checker import (
    SecurityCheckResult,
    SecurityFinding,
    _check_config,
    _check_dependencies,
    _check_env_files,
    _check_gitignore,
    _check_source_code,
    _compile_secret_patterns,
    _compute_status,
    _is_placeholder,
    _scan_files_for_secrets,
    run_security_check,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp(tmp_path: Path) -> Path:
    """Minimal project root."""
    return tmp_path


@pytest.fixture()
def clean_project(tmp_path: Path) -> Path:
    """Project with .gitignore that covers everything — produces no findings."""
    gi = tmp_path / ".gitignore"
    gi.write_text(".env\n.env.*\n*.pem\n*.key\nnode_modules/\n.venv/\n")
    return tmp_path


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


class TestDataModel:
    def test_finding_defaults(self) -> None:
        f = SecurityFinding(
            category="secrets",
            severity="ERROR",
            message="msg",
            location="file.ts",
            recommendation="fix",
        )
        assert f.evidence == ""

    def test_result_empty_findings(self, tmp: Path) -> None:
        result = SecurityCheckResult(path=tmp, status="OK")
        assert result.findings == []

    def test_result_with_findings(self, tmp: Path) -> None:
        f = SecurityFinding("a", "WARNING", "m", "l", "r", "ev")
        result = SecurityCheckResult(path=tmp, status="WARNING", findings=[f])
        assert len(result.findings) == 1


# ---------------------------------------------------------------------------
# _compute_status
# ---------------------------------------------------------------------------


class TestComputeStatus:
    def test_no_findings_is_ok(self) -> None:
        assert _compute_status([]) == "OK"

    def test_warning_only(self) -> None:
        f = SecurityFinding("x", "WARNING", "m", "l", "r")
        assert _compute_status([f]) == "WARNING"

    def test_error_dominates_warning(self) -> None:
        findings = [
            SecurityFinding("x", "WARNING", "m", "l", "r"),
            SecurityFinding("y", "ERROR", "m", "l", "r"),
        ]
        assert _compute_status(findings) == "ERROR"

    def test_error_only(self) -> None:
        f = SecurityFinding("x", "ERROR", "m", "l", "r")
        assert _compute_status([f]) == "ERROR"


# ---------------------------------------------------------------------------
# _is_placeholder
# ---------------------------------------------------------------------------


class TestIsPlaceholder:
    def test_your_prefix(self) -> None:
        assert _is_placeholder("your-secret-key")

    def test_angle_bracket(self) -> None:
        assert _is_placeholder("<API_KEY>")

    def test_double_curly(self) -> None:
        assert _is_placeholder("{{ secret }}")

    def test_changeme(self) -> None:
        assert _is_placeholder("changeme")

    def test_real_value_not_placeholder(self) -> None:
        assert not _is_placeholder("sk-realvalue123")

    def test_dollar_brace(self) -> None:
        assert _is_placeholder("${SECRET}")


# ---------------------------------------------------------------------------
# _check_env_files
# ---------------------------------------------------------------------------


class TestCheckEnvFiles:
    def test_no_env_file_no_finding(self, tmp: Path) -> None:
        assert _check_env_files(tmp) == []

    def test_env_file_without_gitignore_is_error(self, tmp: Path) -> None:
        (tmp / ".env").write_text("SECRET=real\n")
        findings = _check_env_files(tmp)
        assert any(f.severity == "ERROR" and ".env" in f.message for f in findings)

    def test_env_file_with_gitignore_protection_ok(self, tmp: Path) -> None:
        (tmp / ".env").write_text("SECRET=real\n")
        (tmp / ".gitignore").write_text(".env\n")
        findings = _check_env_files(tmp)
        env_errors = [f for f in findings if "'.env'" in f.message]
        assert env_errors == []

    def test_env_star_pattern_covers_env_local(self, tmp: Path) -> None:
        (tmp / ".env.local").write_text("KEY=val\n")
        (tmp / ".gitignore").write_text(".env.*\n")
        findings = _check_env_files(tmp)
        assert not any(f.severity == "ERROR" for f in findings)

    def test_credential_file_is_error(self, tmp: Path) -> None:
        (tmp / "service-account.json").write_text("{}\n")
        findings = _check_env_files(tmp)
        assert any(
            f.severity == "ERROR" and "service-account.json" in f.message
            for f in findings
        )

    def test_pem_file_is_error(self, tmp: Path) -> None:
        (tmp / "cert.pem").write_text("-----BEGIN CERTIFICATE-----\n")
        findings = _check_env_files(tmp)
        assert any(f.severity == "ERROR" and "cert.pem" in f.message for f in findings)

    def test_multiple_env_files(self, tmp: Path) -> None:
        for name in (".env", ".env.production"):
            (tmp / name).write_text("X=1\n")
        findings = _check_env_files(tmp)
        errors = [f for f in findings if f.severity == "ERROR"]
        assert len(errors) >= 2

    def test_category_is_env_files(self, tmp: Path) -> None:
        (tmp / ".env").write_text("X=1\n")
        findings = _check_env_files(tmp)
        assert all(f.category == "env_files" for f in findings)


# ---------------------------------------------------------------------------
# _check_gitignore
# ---------------------------------------------------------------------------


class TestCheckGitignore:
    def test_no_gitignore_produces_warning(self, tmp: Path) -> None:
        findings = _check_gitignore(tmp)
        assert any(
            f.severity == "WARNING" and ".gitignore" in f.message for f in findings
        )
        # No gitignore → returns early with single finding
        assert len(findings) == 1

    def test_empty_gitignore_warns_on_env_and_keys(self, tmp: Path) -> None:
        (tmp / ".gitignore").write_text("")
        findings = _check_gitignore(tmp)
        categories = {f.message for f in findings}
        assert any(".env" in m for m in categories)
        assert any(".pem" in m or "*.key" in m for m in categories)

    def test_complete_gitignore_no_warnings(self, clean_project: Path) -> None:
        findings = _check_gitignore(clean_project)
        assert findings == []

    def test_missing_node_modules_warns_when_package_json_present(
        self, tmp: Path
    ) -> None:
        (tmp / ".gitignore").write_text(".env\n.env.*\n*.pem\n*.key\n")
        (tmp / "package.json").write_text('{"name":"app"}')
        findings = _check_gitignore(tmp)
        assert any("node_modules" in f.message for f in findings)

    def test_no_node_modules_warning_without_package_json(self, tmp: Path) -> None:
        (tmp / ".gitignore").write_text(".env\n.env.*\n*.pem\n*.key\n")
        findings = _check_gitignore(tmp)
        assert not any("node_modules" in f.message for f in findings)

    def test_missing_venv_warns_when_pyproject_present(self, tmp: Path) -> None:
        (tmp / ".gitignore").write_text(".env\n.env.*\n*.pem\n*.key\n")
        (tmp / "pyproject.toml").write_text("[project]\nname='x'\n")
        findings = _check_gitignore(tmp)
        assert any(".venv" in f.message for f in findings)

    def test_category_is_gitignore(self, tmp: Path) -> None:
        (tmp / ".gitignore").write_text("")
        findings = _check_gitignore(tmp)
        assert all(f.category == "gitignore" for f in findings)


# ---------------------------------------------------------------------------
# _scan_files_for_secrets
# ---------------------------------------------------------------------------


class TestScanFilesForSecrets:
    def _make_src(self, root: Path, filename: str, content: str) -> Path:
        src = root / "src"
        src.mkdir(exist_ok=True)
        f = src / filename
        f.write_text(content)
        return f

    def test_no_secrets_no_findings(self, tmp: Path) -> None:
        compiled = _compile_secret_patterns()
        assert _scan_files_for_secrets(tmp, compiled) == []

    def test_aws_key_detected(self, tmp: Path) -> None:
        self._make_src(tmp, "config.ts", "const key = 'AKIAIOSFODNN7EXAMPLE';\n")
        compiled = _compile_secret_patterns()
        findings = _scan_files_for_secrets(tmp, compiled)
        assert any(f.severity == "ERROR" and "AWS" in f.message for f in findings)

    def test_openai_key_detected(self, tmp: Path) -> None:
        self._make_src(tmp, "client.ts", "const key = 'sk-abcdefghijklmnopqrstuvwx';\n")
        compiled = _compile_secret_patterns()
        findings = _scan_files_for_secrets(tmp, compiled)
        assert any("OpenAI" in f.message for f in findings)

    def test_github_pat_detected(self, tmp: Path) -> None:
        self._make_src(tmp, "ci.ts", "const token = 'ghp_" + "A" * 36 + "';\n")
        compiled = _compile_secret_patterns()
        findings = _scan_files_for_secrets(tmp, compiled)
        assert any("GitHub" in f.message for f in findings)

    def test_evidence_never_contains_secret_value(self, tmp: Path) -> None:
        self._make_src(tmp, "config.ts", "const key = 'AKIAIOSFODNN7EXAMPLE';\n")
        compiled = _compile_secret_patterns()
        findings = _scan_files_for_secrets(tmp, compiled)
        for f in findings:
            assert "AKIAIOSFODNN7EXAMPLE" not in f.evidence

    def test_evidence_format_pattern(self, tmp: Path) -> None:
        self._make_src(tmp, "config.ts", "const key = 'AKIAIOSFODNN7EXAMPLE';\n")
        compiled = _compile_secret_patterns()
        findings = _scan_files_for_secrets(tmp, compiled)
        aws = next((f for f in findings if "AWS_ACCESS_KEY_ID" in f.message), None)
        assert aws is not None
        assert "file(s)" in aws.evidence
        assert "first match:" in aws.evidence

    def test_category_is_secrets(self, tmp: Path) -> None:
        self._make_src(tmp, "cfg.ts", "const k = 'AKIAIOSFODNN7EXAMPLE';\n")
        compiled = _compile_secret_patterns()
        findings = _scan_files_for_secrets(tmp, compiled)
        assert all(f.category == "secrets" for f in findings)

    def test_files_over_size_limit_skipped(self, tmp: Path) -> None:
        src = tmp / "src"
        src.mkdir()
        big = src / "big.ts"
        big.write_bytes(b"x" * (500 * 1024 + 1))
        compiled = _compile_secret_patterns()
        assert _scan_files_for_secrets(tmp, compiled) == []

    def test_node_modules_excluded(self, tmp: Path) -> None:
        nm = tmp / "src" / "node_modules"
        nm.mkdir(parents=True)
        (nm / "pkg.ts").write_text("const k = 'AKIAIOSFODNN7EXAMPLE';\n")
        compiled = _compile_secret_patterns()
        assert _scan_files_for_secrets(tmp, compiled) == []


# ---------------------------------------------------------------------------
# _check_config
# ---------------------------------------------------------------------------


class TestCheckConfig:
    def test_no_docker_no_findings(self, tmp: Path) -> None:
        assert _check_config(tmp) == []

    def test_dockerfile_no_user_warns(self, tmp: Path) -> None:
        (tmp / "Dockerfile").write_text("FROM node:20\nRUN echo hello\n")
        findings = _check_config(tmp)
        assert any("no USER" in f.message for f in findings)

    def test_dockerfile_user_root_warns(self, tmp: Path) -> None:
        (tmp / "Dockerfile").write_text("FROM node:20\nUSER root\n")
        findings = _check_config(tmp)
        assert any("USER root" in f.message for f in findings)

    def test_dockerfile_latest_warns(self, tmp: Path) -> None:
        (tmp / "Dockerfile").write_text("FROM node:latest\nUSER app\n")
        findings = _check_config(tmp)
        assert any("non-pinned" in f.message for f in findings)

    def test_dockerfile_pinned_image_ok(self, tmp: Path) -> None:
        (tmp / "Dockerfile").write_text("FROM node:20-alpine\nUSER app\n")
        findings = _check_config(tmp)
        no_pin = [f for f in findings if "non-pinned" in f.message]
        assert no_pin == []

    def test_docker_compose_sensitive_port_warns(self, tmp: Path) -> None:
        (tmp / "docker-compose.yml").write_text(
            "services:\n  db:\n    ports:\n      - '5432:5432'\n"
        )
        findings = _check_config(tmp)
        assert any("5432" in f.message for f in findings)

    def test_github_actions_prt_is_error(self, tmp: Path) -> None:
        wf_dir = tmp / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        (wf_dir / "ci.yml").write_text(
            "on:\n  pull_request_target:\n    branches: [main]\n"
        )
        findings = _check_config(tmp)
        assert any(
            f.severity == "ERROR" and "pull_request_target" in f.message
            for f in findings
        )

    def test_github_actions_echo_secret_is_error(self, tmp: Path) -> None:
        wf_dir = tmp / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        (wf_dir / "ci.yml").write_text("steps:\n  - run: echo ${{ secrets.TOKEN }}\n")
        findings = _check_config(tmp)
        assert any(f.severity == "ERROR" and "echo" in f.message for f in findings)

    def test_github_actions_curl_pipe_warns(self, tmp: Path) -> None:
        wf_dir = tmp / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        (wf_dir / "ci.yml").write_text(
            "steps:\n  - run: curl -fsSL https://example.com/install.sh | bash\n"
        )
        findings = _check_config(tmp)
        assert any(
            f.severity == "WARNING" and "pipe" in f.message.lower() for f in findings
        )

    def test_npm_script_curl_pipe_warns(self, tmp: Path) -> None:
        (tmp / "package.json").write_text(
            json.dumps({"scripts": {"setup": "curl https://example.com | bash"}})
        )
        findings = _check_config(tmp)
        assert any("pipe" in f.message.lower() for f in findings)

    def test_category_is_config(self, tmp: Path) -> None:
        (tmp / "Dockerfile").write_text("FROM node:latest\nRUN echo hi\n")
        findings = _check_config(tmp)
        assert all(f.category == "config" for f in findings)


# ---------------------------------------------------------------------------
# _check_dependencies
# ---------------------------------------------------------------------------


class TestCheckDependencies:
    def test_no_manifest_no_findings(self, tmp: Path) -> None:
        assert _check_dependencies(tmp) == []

    def test_package_json_without_lock_warns(self, tmp: Path) -> None:
        (tmp / "package.json").write_text('{"name":"app"}')
        findings = _check_dependencies(tmp)
        assert any("lock file" in f.message for f in findings)

    def test_package_json_with_lock_ok(self, tmp: Path) -> None:
        (tmp / "package.json").write_text('{"name":"app"}')
        (tmp / "package-lock.json").write_text("{}")
        assert _check_dependencies(tmp) == []

    def test_pnpm_lock_accepted(self, tmp: Path) -> None:
        (tmp / "package.json").write_text('{"name":"app"}')
        (tmp / "pnpm-lock.yaml").write_text("lockfileVersion: 5\n")
        assert _check_dependencies(tmp) == []

    def test_requirements_without_hashes_warns(self, tmp: Path) -> None:
        (tmp / "requirements.txt").write_text("requests==2.31.0\n")
        findings = _check_dependencies(tmp)
        assert any("hash" in f.message for f in findings)

    def test_requirements_with_hashes_ok(self, tmp: Path) -> None:
        (tmp / "requirements.txt").write_text("requests==2.31.0 --hash=sha256:abcdef\n")
        assert _check_dependencies(tmp) == []

    def test_category_is_dependencies(self, tmp: Path) -> None:
        (tmp / "package.json").write_text('{"name":"app"}')
        findings = _check_dependencies(tmp)
        assert all(f.category == "dependencies" for f in findings)


# ---------------------------------------------------------------------------
# _check_source_code
# ---------------------------------------------------------------------------


class TestCheckSourceCode:
    def _make_src(self, root: Path, filename: str, content: str) -> None:
        src = root / "src"
        src.mkdir(exist_ok=True)
        (src / filename).write_text(content)

    def test_no_src_no_findings(self, tmp: Path) -> None:
        assert _check_source_code(tmp) == []

    def test_eval_detected(self, tmp: Path) -> None:
        self._make_src(tmp, "util.py", "eval(user_input)\n")
        findings = _check_source_code(tmp)
        assert any("eval" in f.message for f in findings)

    def test_os_system_detected(self, tmp: Path) -> None:
        self._make_src(tmp, "run.py", "import os\nos.system(cmd)\n")
        findings = _check_source_code(tmp)
        assert any("os.system" in f.message for f in findings)

    def test_evidence_has_pattern_and_location(self, tmp: Path) -> None:
        self._make_src(tmp, "run.py", "os.system('ls')\n")
        findings = _check_source_code(tmp)
        sc = next((f for f in findings if "os.system" in f.message), None)
        assert sc is not None
        assert "file(s)" in sc.evidence
        assert "first match:" in sc.evidence

    def test_category_is_source_code(self, tmp: Path) -> None:
        self._make_src(tmp, "run.py", "eval('x')\n")
        findings = _check_source_code(tmp)
        assert all(f.category == "source_code" for f in findings)


# ---------------------------------------------------------------------------
# run_security_check (integration)
# ---------------------------------------------------------------------------


class TestRunSecurityCheck:
    def test_clean_project_is_ok(self, clean_project: Path) -> None:
        result = run_security_check(clean_project)
        assert isinstance(result, SecurityCheckResult)
        assert result.status == "OK"
        assert result.findings == []

    def test_result_path_is_absolute(self, clean_project: Path) -> None:
        result = run_security_check(clean_project)
        assert result.path.is_absolute()

    def test_project_with_bare_env_is_error(self, tmp: Path) -> None:
        (tmp / ".env").write_text("SECRET=real\n")
        result = run_security_check(tmp)
        assert result.status == "ERROR"

    def test_project_with_warnings_only_is_warning(self, tmp: Path) -> None:
        # Has .gitignore with missing patterns → WARNING
        (tmp / ".gitignore").write_text("node_modules/\n")
        result = run_security_check(tmp)
        assert result.status == "WARNING"

    def test_findings_have_required_fields(self, tmp: Path) -> None:
        (tmp / ".env").write_text("X=1\n")
        result = run_security_check(tmp)
        for f in result.findings:
            assert f.category
            assert f.severity in {"ERROR", "WARNING"}
            assert f.message
            assert f.location
            assert f.recommendation

    def test_error_finding_presence(self, tmp: Path) -> None:
        (tmp / ".env").write_text("X=1\n")
        result = run_security_check(tmp)
        severities = {f.severity for f in result.findings}
        assert "ERROR" in severities

    def test_no_secret_value_in_any_field(self, tmp: Path) -> None:
        (tmp / ".gitignore").write_text(".env\n.env.*\n*.pem\n*.key\n")
        src = tmp / "src"
        src.mkdir()
        (src / "config.ts").write_text("const k = 'AKIAIOSFODNN7EXAMPLE';\n")
        result = run_security_check(tmp)
        for f in result.findings:
            for field_val in (f.message, f.evidence, f.location, f.recommendation):
                assert "AKIAIOSFODNN7EXAMPLE" not in field_val
