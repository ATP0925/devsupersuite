"""
⚡ DevSuperSuite Official: License Activation & Onboarding Telemetry Integration Tests
File: test_license_activation.py
Governing Entity: DevSuperSuite Official (support@devsupersuite.com)
Strict Protocol: 100% Brand Anonymity - Zero Founder Personal Identifiers
"""

import os
import sys
import json
import pytest
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Paths Setup
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(SCRATCH_DIR, "services")
DATA_DIR = os.path.join(SCRATCH_DIR, "data")
MARKETING_DIR = os.path.join(SCRATCH_DIR, "marketing")

sys.path.insert(0, SERVICES_DIR)

from license_activation_engine import (
    Ed25519LicenseAuthority,
    LicenseActivationEngine,
    LICENSES_REGISTRY_PATH,
    ACTIVATIONS_TELEMETRY_PATH
)


@pytest.fixture
def activation_engine(tmp_path):
    test_licenses = os.path.join(tmp_path, "test_licenses_registry.json")
    test_telemetry = os.path.join(tmp_path, "test_activations_telemetry.json")
    return LicenseActivationEngine(
        registry_path=test_licenses,
        telemetry_path=test_telemetry
    )


def test_01_license_generation_and_payload(activation_engine):
    """Verify license generation produces valid key token, canonical payload, and SHA256 digest."""
    lic = activation_engine.generate_license(
        order_id="GUM-TEST-1001",
        customer_email="developer.dan@cloudscale.io",
        plan_name="Hacker Solo",
        seats=1
    )

    assert lic["license_key"].startswith("DSS-PRO-2026-")
    assert lic["order_id"] == "GUM-TEST-1001"
    assert lic["customer_email"] == "developer.dan@cloudscale.io"
    assert lic["seats"] == 1
    assert "signature_hex" in lic
    assert "sha256_digest" in lic


def test_02_ed25519_offline_signature_verification(activation_engine):
    """Verify Ed25519 signature validates cleanly offline using local public key."""
    lic = activation_engine.generate_license(
        order_id="PP-TEST-2002",
        customer_email="elena.arch@neuralsec.io",
        plan_name="Team 5-Seat",
        seats=5
    )

    verify_res = activation_engine.verify_license(
        canonical_payload=lic["canonical_payload"],
        signature_hex=lic["signature_hex"],
        public_key_hex=lic["signer_public_key_hex"]
    )

    assert verify_res["verified"] is True
    assert verify_res["plan_name"] == "Team 5-Seat"
    assert verify_res["seats"] == 5
    assert verify_res["offline_airgap_safe"] is True


def test_03_tamper_rejection(activation_engine):
    """Verify tampering with license parameters invalidates the Ed25519 signature."""
    lic = activation_engine.generate_license(
        order_id="STR-TEST-3003",
        customer_email="kenji.sato@systems-tokyo.jp",
        plan_name="Hacker Solo",
        seats=1
    )

    # Tamper with payload: change seats from 1 to 100
    tampered_payload = lic["canonical_payload"].replace('"seats": 1', '"seats": 100')

    verify_res = activation_engine.verify_license(
        canonical_payload=tampered_payload,
        signature_hex=lic["signature_hex"],
        public_key_hex=lic["signer_public_key_hex"]
    )

    assert verify_res["verified"] is False


def test_04_cli_installer_one_liners(activation_engine):
    """Verify customized multi-platform installation commands are generated."""
    lic = activation_engine.generate_license(
        order_id="UPI-TEST-4004",
        customer_email="priya.dev@mumbai-tech.in",
        plan_name="Hacker Solo"
    )

    key = lic["license_key"]
    email = lic["customer_email"]

    # Bash one-liner
    assert "curl -fsSL https://devsupersuite.web.app/install.sh | bash" in lic["cli_install_bash"]
    assert f"--license-key {key}" in lic["cli_install_bash"]
    assert f"--email {email}" in lic["cli_install_bash"]

    # PowerShell one-liner
    assert "iwr -useb https://devsupersuite.web.app/install.ps1 | iex" in lic["cli_install_powershell"]
    assert f"omnikernel activate --key {key}" in lic["cli_install_powershell"]


def test_05_airgap_offline_license_generation(activation_engine):
    """Verify air-gap offline SCIF license includes offline activation flags."""
    lic = activation_engine.generate_license(
        order_id="SCIF-TEST-5005",
        customer_email="scif-admin@defense-contractor.gov",
        plan_name="SCIF Defense Unlimited",
        seats=1000,
        is_airgap=True
    )

    assert lic["is_airgap"] is True
    assert "cli_offline_activate" in lic
    assert "devsupersuite license activate" in lic["cli_offline_activate"]
    assert "--public-key" in lic["cli_offline_activate"]


def test_06_record_activation_telemetry(activation_engine):
    """Verify local activation telemetry logs IDE, language, and TTFA."""
    lic = activation_engine.generate_license(
        order_id="GUM-TEST-6006",
        customer_email="marcus@devstream.org",
        plan_name="Hacker Solo"
    )

    act = activation_engine.record_activation_telemetry(
        license_key=lic["license_key"],
        customer_email=lic["customer_email"],
        ide_environment="Cursor",
        primary_language="Rust",
        repo_languages=["Rust", "Python", "TOML"],
        ast_nodes_sliced=28400,
        time_to_first_activation_min=3.5
    )

    assert act["activation_id"].startswith("ACT-")
    assert act["ide_environment"] == "Cursor"
    assert act["primary_language"] == "Rust"
    assert act["time_to_first_activation_min"] == 3.5

    # Check license status transitioned to ACTIVATED
    updated_lic = next(l for l in activation_engine.licenses if l["license_key"] == lic["license_key"])
    assert updated_lic["status"] == "ACTIVATED"


def test_07_audit_activation_metrics(activation_engine):
    """Verify activation audit statistics, TTFA averages, and distribution breakdowns."""
    audit = activation_engine.audit_activations()

    assert "total_licenses_issued" in audit
    assert "total_activations_completed" in audit
    assert "average_time_to_first_activation_min" in audit
    assert "ide_distribution" in audit
    assert "primary_language_distribution" in audit

    assert audit["total_licenses_issued"] >= 3
    assert audit["average_time_to_first_activation_min"] > 0.0


def test_08_cli_commands_execution():
    """Verify all 4 required CLI commands execute with exit code 0."""
    script_path = os.path.join(SERVICES_DIR, "license_activation_engine.py")

    cmds = [
        [sys.executable, script_path, "--generate-license", "--order-id", "CLI-TEST-001", "--email", "cli@test.com"],
        [sys.executable, script_path, "--verify-license"],
        [sys.executable, script_path, "--audit-activations"],
        [sys.executable, script_path, "--summary"]
    ]

    for cmd in cmds:
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0, f"CLI command failed: {' '.join(cmd)}\n{res.stderr}"


def test_09_strict_brand_anonymity_license_activation():
    """Verify strict 100% brand anonymity: zero personal founder names or numbers."""
    files_to_check = [
        os.path.join(SERVICES_DIR, "license_activation_engine.py"),
        os.path.join(MARKETING_DIR, "developer_onboarding_activation_playbook.md"),
        os.path.abspath(__file__)
    ]

    forbidden_tokens = [
        bytes.fromhex("70726174696b").decode("utf-8"),
        bytes.fromhex("7061646b6172").decode("utf-8"),
        bytes.fromhex("37303230343738313730").decode("utf-8")
    ]

    for fpath in files_to_check:
        assert os.path.exists(fpath), f"Missing file: {fpath}"
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read().lower()
            for token in forbidden_tokens:
                assert token not in content, f"Brand anonymity violation in {fpath}: found forbidden token"
