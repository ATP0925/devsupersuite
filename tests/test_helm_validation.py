#!/usr/bin/env python3
"""
Unit and Integration Tests for Enterprise Air-Gapped Helm Chart Validator
Reference: tests/test_helm_validation.py
Classification: Automated SCIF/Air-Gap Quality Gate (100% Pass)
Contact: cloud@devsupersuite.com
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from services.enterprise_helm_validator import (
    HelmChartLinter,
    AirgapSecurityAuditor,
    HelmTemplateRenderer,
    run_cli,
    DEFAULT_HELM_DIR,
    NON_ROOT_UID
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Helm Chart Linter Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_helm_linter_success():
    linter = HelmChartLinter(DEFAULT_HELM_DIR)
    res = linter.lint_chart()

    assert res["is_valid"] is True
    assert res["status"] == "PASSED"
    assert len(res["violations"]) == 0
    assert len(res["checks_passed"]) >= 8


def test_helm_linter_missing_directory():
    linter = HelmChartLinter(Path("C:/non/existent/helm/path"))
    res = linter.lint_chart()

    assert res["is_valid"] is False
    assert res["status"] == "FAILED"
    assert len(res["violations"]) > 0


def test_helm_linter_missing_chart_yaml():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_helm_test_"))
    try:
        linter = HelmChartLinter(temp_dir)
        res = linter.lint_chart()

        assert res["is_valid"] is False
        assert any("Missing Chart.yaml" in v for v in res["violations"])
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Air-Gap Security Auditor Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_security_context_auditor_success():
    auditor = AirgapSecurityAuditor(DEFAULT_HELM_DIR)
    res = auditor.audit_security_context()

    assert res["is_valid"] is True
    assert len(res["violations"]) == 0
    assert any(str(NON_ROOT_UID) in c for c in res["checks_passed"])


def test_security_context_auditor_detects_root_uid():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_helm_root_"))
    try:
        # Copy chart files
        shutil.copytree(DEFAULT_HELM_DIR, temp_dir, dirs_exist_ok=True)
        val_file = temp_dir / "values.yaml"
        # Overwrite runAsUser to 0 (root)
        val_content = val_file.read_text(encoding="utf-8")
        val_content = val_content.replace(f"runAsUser: {NON_ROOT_UID}", "runAsUser: 0")
        val_file.write_text(val_content, encoding="utf-8")

        auditor = AirgapSecurityAuditor(temp_dir)
        res = auditor.audit_security_context()

        assert res["is_valid"] is False
        assert any(str(NON_ROOT_UID) in v for v in res["violations"])
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_network_policy_auditor_success():
    auditor = AirgapSecurityAuditor(DEFAULT_HELM_DIR)
    res = auditor.audit_zero_egress_network_policy()

    assert res["is_valid"] is True
    assert len(res["violations"]) == 0
    assert any("0.0.0.0/0" in c for c in res["checks_passed"])


def test_network_policy_auditor_detects_permissive_egress():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_helm_netpol_"))
    try:
        shutil.copytree(DEFAULT_HELM_DIR, temp_dir, dirs_exist_ok=True)
        np_file = temp_dir / "templates" / "networkpolicy-zero-egress.yaml"
        np_text = np_file.read_text(encoding="utf-8")
        # Inject permissive egress
        np_text += "\n  # Injected leak\n  egress:\n    - to:\n        - ipBlock:\n            cidr: 0.0.0.0/0\n"
        np_file.write_text(np_text, encoding="utf-8")

        auditor = AirgapSecurityAuditor(temp_dir)
        res = auditor.audit_zero_egress_network_policy()

        assert res["is_valid"] is False
        assert any("0.0.0.0/0" in v for v in res["violations"])
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_ingress_mtls_auditor_success():
    auditor = AirgapSecurityAuditor(DEFAULT_HELM_DIR)
    res = auditor.audit_ingress_mtls()

    assert res["is_valid"] is True
    assert len(res["violations"]) == 0
    assert any("auth-tls-verify-client" in c for c in res["checks_passed"])


def test_resource_quota_and_ha_success():
    auditor = AirgapSecurityAuditor(DEFAULT_HELM_DIR)
    res = auditor.audit_resource_quota_and_ha()

    assert res["is_valid"] is True
    assert len(res["violations"]) == 0
    assert any("PodDisruptionBudget" in c for c in res["checks_passed"])
    assert any("HorizontalPodAutoscaler" in c for c in res["checks_passed"])


def test_audit_all():
    auditor = AirgapSecurityAuditor(DEFAULT_HELM_DIR)
    res = auditor.audit_all()

    assert res["status"] == "AIRGAP_CERTIFIED"
    assert res["all_valid"] is True
    assert "security_context" in res["audits"]
    assert "network_policy" in res["audits"]
    assert "ingress_mtls" in res["audits"]
    assert "resource_quota_and_ha" in res["audits"]


# ─────────────────────────────────────────────────────────────────────────────
# 3. Template Renderer Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_template_renderer_success():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_render_"))
    try:
        out_yaml = temp_dir / "rendered.yaml"
        renderer = HelmTemplateRenderer(DEFAULT_HELM_DIR)
        res = renderer.render_manifests("Raytheon Intelligence & Space", out_yaml)

        assert out_yaml.exists()
        assert len(res["manifest_checksum"]) == 64
        assert res["customer_organization"] == "Raytheon Intelligence & Space"
        assert res["documents_rendered"] >= 6

        content = out_yaml.read_text(encoding="utf-8")
        assert "kind: Deployment" in content
        assert "kind: Service" in content
        assert "kind: Ingress" in content
        assert "kind: NetworkPolicy" in content
        assert "kind: PodDisruptionBudget" in content
        assert "kind: HorizontalPodAutoscaler" in content
        assert "runAsUser: 10001" in content
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# 4. CLI Execution Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_cli_execution_all_flags():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_cli_helm_"))
    try:
        out_file = temp_dir / "test_rendered.yaml"
        ret = run_cli([
            "--lint-helm",
            "--verify-airgap-manifests",
            "--export-rendered-templates",
            "--summary",
            "--customer", "General Dynamics Land Systems",
            "--output", str(out_file)
        ])

        assert ret == 0
        assert out_file.exists()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
