#!/usr/bin/env python3
"""
Unit and Integration Tests for Enterprise POC Sandbox Deployment Kit
Reference: tests/test_poc_deployment_kit.py
Classification: Automated Quality Gate (100% Pass Required)
Contact: solutions@devsupersuite.com
"""

import hashlib
import hmac
import json
import math
import os
import sys
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from services.enterprise_poc_deployment_kit import (
    calculate_shannon_entropy,
    SecretInterceptionScanner,
    TrialLicenseManager,
    SandboxProvisioner,
    TelemetryIngestionEngine,
    run_cli,
    DEFAULT_SIGNING_KEY,
    DEFAULT_POC_DURATION_DAYS,
    DEFAULT_SEATS,
    TOKEN_COMPRESSION_TARGET,
    LATENCY_MS_TARGET
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Shannon Entropy & Secret Scanner Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_calculate_shannon_entropy_edge_cases():
    assert calculate_shannon_entropy("") == 0.0
    # Single character has zero entropy
    assert calculate_shannon_entropy("aaaaaaa") == 0.0
    # 8 uniform characters: log2(8) = 3.0
    assert calculate_shannon_entropy("abcdefgh") == 3.0
    # Random base64 string should exceed 3.5
    high_entropy_str = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    assert calculate_shannon_entropy(high_entropy_str) > 3.5


def test_secret_interception_scanner_detects_credentials():
    content_with_secrets = """
    # Enterprise Deployment Config
    DATABASE_URL = "postgres://user:pass@localhost:5432/app"
    AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
    GITHUB_TOKEN = "ghp_1234567890abcdefghijklmnopqrstuvwxyzAB"
    RSA_KEY = "-----BEGIN RSA PRIVATE KEY-----"
    SAFE_VAR = "This is a completely normal developer commit."
    """
    findings = SecretInterceptionScanner.scan_content(content_with_secrets)
    assert len(findings) >= 3

    types_found = {f["type"] for f in findings}
    assert "AWS_ACCESS_KEY" in types_found
    assert "GITHUB_TOKEN" in types_found
    assert "PRIVATE_KEY_BLOCK" in types_found


def test_secret_interception_scanner_clean_code():
    clean_code = """
    def add_integers(a: int, b: int) -> int:
        \"\"\"Calculates sum of two numbers.\"\"\"
        return a + b
    """
    findings = SecretInterceptionScanner.scan_content(clean_code)
    assert len(findings) == 0


# ─────────────────────────────────────────────────────────────────────────────
# 2. Trial License Manager Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_trial_license_creation():
    mgr = TrialLicenseManager(signing_key=DEFAULT_SIGNING_KEY)
    license_doc = mgr.create_trial_license(
        customer_name="Boeing Defense Systems",
        tier="kubernetes_airgap",
        seats=50,
        duration_days=14
    )

    assert "license" in license_doc
    assert "signature" in license_doc
    assert license_doc["verification_algorithm"] == "HMAC-SHA256"

    payload = license_doc["license"]
    assert payload["customer_name"] == "Boeing Defense Systems"
    assert payload["tier"] == "kubernetes_airgap"
    assert payload["max_seats"] == 50
    assert payload["duration_days"] == 14
    assert payload["airgap_enforced"] is True
    assert "tree_sitter_ast_context_pruning" in payload["features"]
    assert payload["sla_guarantee"]["min_token_reduction_pct"] == 70.0


def test_trial_license_verification_valid():
    mgr = TrialLicenseManager(signing_key=DEFAULT_SIGNING_KEY)
    license_doc = mgr.create_trial_license(
        customer_name="Northrop Grumman",
        seats=30
    )
    result = mgr.verify_trial_license(license_doc)

    assert result["is_valid"] is True
    assert result["status"] == "ACTIVE"
    assert result["customer_name"] == "Northrop Grumman"
    assert result["max_seats"] == 30
    assert result["days_remaining"] in [13, 14]


def test_trial_license_verification_tampered():
    mgr = TrialLicenseManager(signing_key=DEFAULT_SIGNING_KEY)
    license_doc = mgr.create_trial_license(
        customer_name="Lockheed Martin",
        seats=25
    )

    # Tamper with seat count
    license_doc["license"]["max_seats"] = 1000

    result = mgr.verify_trial_license(license_doc)
    assert result["is_valid"] is False
    assert result["status"] == "TAMPERED"


def test_trial_license_verification_expired():
    mgr = TrialLicenseManager(signing_key=DEFAULT_SIGNING_KEY)
    license_doc = mgr.create_trial_license(
        customer_name="Raytheon Missiles",
        seats=25,
        duration_days=14
    )

    # Force expiration into the past and recalculate signature
    past_date = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    license_doc["license"]["expires_at"] = past_date
    payload_str = json.dumps(license_doc["license"], sort_keys=True)
    license_doc["signature"] = hmac.new(
        DEFAULT_SIGNING_KEY.encode("utf-8"),
        payload_str.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    result = mgr.verify_trial_license(license_doc)
    assert result["is_valid"] is False
    assert result["status"] == "EXPIRED"
    assert result["days_remaining"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# 3. Sandbox Provisioning Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_provision_docker_sandbox():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_test_docker_"))
    try:
        provisioner = SandboxProvisioner()
        res = provisioner.provision_docker_sandbox(
            target_dir=temp_dir,
            customer_name="General Dynamics",
            seats=25
        )

        assert res["mode"] == "docker_standalone"
        docker_path = temp_dir / "docker"
        assert (docker_path / "docker-compose.poc.yml").exists()
        assert (docker_path / "license.json").exists()
        assert (docker_path / ".env.poc").exists()
        assert (docker_path / "start_poc.sh").exists()
        assert (docker_path / "verify_zero_egress.sh").exists()

        # Check docker-compose contains internal network lockdown
        compose_content = (docker_path / "docker-compose.poc.yml").read_text(encoding="utf-8")
        assert "internal: true" in compose_content
        assert "devsupersuite-core-proxy" in compose_content
        assert "devsupersuite-entropy-guard" in compose_content
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_provision_kubernetes_sandbox():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_test_k8s_"))
    try:
        provisioner = SandboxProvisioner()
        res = provisioner.provision_kubernetes_sandbox(
            target_dir=temp_dir,
            customer_name="BAE Systems",
            seats=40
        )

        assert res["mode"] == "kubernetes_airgap"
        k8s_path = temp_dir / "kubernetes"
        assert (k8s_path / "01-namespace-poc.yaml").exists()
        assert (k8s_path / "02-network-policy-zero-egress.yaml").exists()
        assert (k8s_path / "03-configmap-secrets.yaml").exists()
        assert (k8s_path / "04-deployment-poc-core.yaml").exists()
        assert (k8s_path / "05-service-poc.yaml").exists()

        # Check NetworkPolicy enforces egress lockdown
        netpol = (k8s_path / "02-network-policy-zero-egress.yaml").read_text(encoding="utf-8")
        assert "devsupersuite-zero-egress-lockdown" in netpol
        assert "kube-system" in netpol
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_inject_fixtures_and_hooks():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_test_fixtures_"))
    try:
        provisioner = SandboxProvisioner()
        res = provisioner.inject_fixtures_and_hooks(temp_dir)

        config_file = Path(res["config_rules"])
        hook_file = Path(res["precommit_hook"])
        assert config_file.exists()
        assert hook_file.exists()

        rules_json = json.loads(config_file.read_text(encoding="utf-8"))
        assert rules_json["strategies"]["target_compression_ratio_minimum"] == 70.0
        assert rules_json["entropy_guard"]["shannon_threshold"] == 3.0

        # Check AST benchmark files
        fixtures_dir = temp_dir / "fixtures" / "ast_slicing_benchmark"
        assert (fixtures_dir / "monolith_service_raw.py").exists()
        assert (fixtures_dir / "monolith_service_sliced.py").exists()
        assert (fixtures_dir / "benchmark_ast_slice.py").exists()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Telemetry Ingestion & Audit Engine Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_telemetry_sample_generation():
    records = TelemetryIngestionEngine.generate_sample_14day_telemetry(
        customer_name="L3Harris Technologies",
        seats=20
    )
    assert len(records) == 14
    for idx, r in enumerate(records, start=1):
        assert r["day"] == idx
        assert r["raw_tokens_requested"] > r["compressed_tokens_sent"]
        assert r["token_savings_pct"] >= 70.0
        assert r["egress_packets_leaked"] == 0
        assert r["secrets_leaked"] == 0


def test_telemetry_audit_passing():
    records = TelemetryIngestionEngine.generate_sample_14day_telemetry(
        customer_name="L3Harris Technologies",
        seats=25
    )
    audit = TelemetryIngestionEngine.audit_telemetry(records)

    assert audit["status"] == "COMPLETED"
    assert audit["overall_poc_passed"] is True
    assert audit["token_metrics"]["target_met"] is True
    assert audit["token_metrics"]["token_reduction_pct"] >= 70.0
    assert audit["cybersecurity_metrics"]["target_met"] is True
    assert audit["cybersecurity_metrics"]["total_secrets_leaked"] == 0
    assert audit["network_airgap_metrics"]["zero_egress_target_met"] is True
    assert "QUALIFIED_FOR_PRODUCTION_CONVERSION" in audit["commercial_recommendation"]


def test_telemetry_audit_failing_conditions():
    # Construct failing telemetry records
    failing_records = [
        {
            "day": 1,
            "raw_tokens_requested": 100_000,
            "compressed_tokens_sent": 80_000, # Only 20% savings, fails 70% threshold
            "entropy_scans_performed": 10,
            "secrets_intercepted_and_blocked": 1,
            "secrets_leaked": 2, # Leaks secret! Fails 0 leak tolerance
            "egress_packets_attempted": 5,
            "egress_packets_leaked": 3, # Air-gap egress leak!
            "average_duplex_latency_ms": 145.0 # Fails 110ms limit
        }
    ]
    audit = TelemetryIngestionEngine.audit_telemetry(failing_records)
    assert audit["overall_poc_passed"] is False
    assert audit["token_metrics"]["target_met"] is False
    assert audit["cybersecurity_metrics"]["target_met"] is False
    assert audit["network_airgap_metrics"]["zero_egress_target_met"] is False
    assert audit["performance_metrics"]["target_met"] is False
    assert "REMEDIATION_REQUIRED" in audit["commercial_recommendation"]


def test_telemetry_export_report():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_test_report_"))
    try:
        report_path = temp_dir / "test_poc_report.md"
        records = TelemetryIngestionEngine.generate_sample_14day_telemetry("Raytheon Corp", seats=25)
        audit = TelemetryIngestionEngine.audit_telemetry(records)

        out_file = TelemetryIngestionEngine.export_audit_report(
            audit, records, report_path, "Raytheon Corp"
        )
        assert out_file.exists()
        text = out_file.read_text(encoding="utf-8")
        assert "DevSuperSuite 14-Day Enterprise PoC Telemetry Audit Report" in text
        assert "Raytheon Corp" in text
        assert "PASSED - SLA GUARANTEES CERTIFIED" in text
        assert "AST Token Compression" in text
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# 5. CLI Gateway Integration Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_cli_generate_license_and_audit():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_test_cli_"))
    try:
        lic_out = temp_dir / "test_license.json"
        report_out = temp_dir / "test_report.md"

        # 1. Run license generation CLI
        ret_lic = run_cli([
            "--generate-trial-license",
            "--customer", "Safran Aero Systems",
            "--seats", "35",
            "--output", str(lic_out)
        ])
        assert ret_lic == 0
        assert lic_out.exists()

        # 2. Run telemetry audit CLI
        ret_audit = run_cli([
            "--audit-poc-telemetry",
            "--summary",
            "--customer", "Safran Aero Systems",
            "--export-report", str(report_out)
        ])
        assert ret_audit == 0
        assert report_out.exists()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
