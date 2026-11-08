"""
⚡ DevSuperSuite Official: Enterprise License Key Auto-Provisioning & Webhook Tests
File: test_license_autopilot_engine.py
Governing Authority: DevSuperSuite Revenue Operations (growth@devsupersuite.com)
Strict Protocol: 100% Brand Anonymity - Zero Founder Personal Identifiers
"""

import os
import sys
import json
import pytest
import subprocess
from pathlib import Path

# Paths Setup
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(SCRATCH_DIR, "services")
DATA_DIR = os.path.join(SCRATCH_DIR, "data")
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")

if SCRATCH_DIR not in sys.path:
    sys.path.insert(0, SCRATCH_DIR)
if SERVICES_DIR not in sys.path:
    sys.path.insert(0, SERVICES_DIR)

from services.enterprise_license_autopilot_engine import (
    AutopilotLicenseAuthority,
    CustomerOnboardingEmailBuilder,
    EnterpriseLicenseAutopilotEngine,
    DOWNLOAD_URI,
    INSTALL_SH_URI,
    MINIMUM_PRO_INR_AMOUNT,
    DISPATCH_LEDGER_PATH,
    REPORT_PATH,
)


@pytest.fixture
def test_authority(tmp_path):
    vault_file = str(tmp_path / "test_autopilot_vault.json")
    return AutopilotLicenseAuthority(vault_path=vault_file)


@pytest.fixture
def test_engine(tmp_path, test_authority):
    ledger_file = str(tmp_path / "test_dispatches.json")
    report_file = str(tmp_path / "test_report.md")
    return EnterpriseLicenseAutopilotEngine(
        ledger_path=ledger_file,
        report_path=report_file,
        authority=test_authority
    )


def test_01_ed25519_authority_key_generation_and_signing(test_authority):
    """Verify Ed25519 keypair generation, certificate signing, and public key extraction."""
    assert os.path.exists(test_authority.vault_path)
    pub_hex = test_authority.get_public_key_hex()
    assert len(pub_hex) == 64

    cert = test_authority.generate_license_certificate(
        customer_email="developer@company.com",
        plan_name="Pro Lifetime License",
        order_id="TEST-ORDER-101",
        gateway="GUMROAD",
        amount_paid=29.0,
        currency="USD",
        seats=1
    )

    assert cert["license_key"].startswith("DSS-PRO-")
    assert cert["customer_email"] == "developer@company.com"
    assert cert["order_id"] == "TEST-ORDER-101"
    assert cert["algorithm"] == "Ed25519"
    assert len(cert["signature_hex"]) == 128


def test_02_ed25519_offline_signature_verification(test_authority):
    """Verify offline local validation passes authentic signatures and rejects tampered claims."""
    cert = test_authority.generate_license_certificate(
        customer_email="security@defense.gov",
        plan_name="Air-Gap SCIF Unlimited",
        order_id="TEST-SCIF-889",
        gateway="STRIPE",
        amount_paid=250000.0,
        currency="USD",
        seats=500
    )

    # 1. Valid signature verification
    is_valid = AutopilotLicenseAuthority.verify_license_offline(
        canonical_claims=cert["canonical_claims"],
        signature_hex=cert["signature_hex"],
        public_key_hex=cert["public_key_hex"]
    )
    assert is_valid is True

    # 2. Tampered claims rejection
    tampered_claims = dict(cert["canonical_claims"])
    tampered_claims["seats"] = 999999
    is_tampered_valid = AutopilotLicenseAuthority.verify_license_offline(
        canonical_claims=tampered_claims,
        signature_hex=cert["signature_hex"],
        public_key_hex=cert["public_key_hex"]
    )
    assert is_tampered_valid is False

    # 3. Bad signature rejection
    assert AutopilotLicenseAuthority.verify_license_offline(
        canonical_claims=cert["canonical_claims"],
        signature_hex="0" * 128,
        public_key_hex=cert["public_key_hex"]
    ) is False


def test_03_gumroad_webhook_processing_and_autopilot(test_engine):
    """Verify processing Gumroad webhook auto-provisions license and formats onboarding email."""
    payload = {
        "sale_id": "GUM-SALE-991204",
        "email": "architect@bloomberg.com",
        "price": 2900,  # $29.00
        "product_name": "DevSuperSuite Pro Lifetime License",
        "quantity": 1
    }

    res = test_engine.process_gumroad_webhook(payload)
    assert res["success"] is True
    assert res["license_key"].startswith("DSS-PRO-")
    assert res["customer_email"] == "architect@bloomberg.com"
    assert res["download_url"] == DOWNLOAD_URI
    assert "curl" in res["cli_one_liner"]
    assert "email_payload" in res

    # Verify recorded in ledger
    ledger_records = test_engine.ledger["dispatched_licenses"]
    assert len(ledger_records) == 1
    assert ledger_records[0]["order_id"] == "GUM-SALE-991204"
    assert ledger_records[0]["gateway"] == "GUMROAD"


def test_04_gumroad_duplicate_sale_rejection(test_engine):
    """Verify resubmission of processed Gumroad sale is rejected due to idempotency."""
    payload = {
        "sale_id": "GUM-IDEMP-1002",
        "email": "lead@uber.com",
        "price": 2900
    }
    first_res = test_engine.process_gumroad_webhook(payload)
    assert first_res["success"] is True

    # Duplicate call
    second_res = test_engine.process_gumroad_webhook(payload)
    assert second_res["success"] is False
    assert second_res["error_code"] == "DUPLICATE_SALE_EVENT"
    assert second_res["license_key"] == first_res["license_key"]


def test_05_upi_utr_verification_success(test_engine):
    """Verify domestic UPI UTR redemption triggers instant Ed25519 key generation."""
    utr_code = "998877665544"
    res = test_engine.process_upi_utr_verification(
        utr_number=utr_code,
        customer_email="developer.india@infosys.com",
        amount_inr=1499.0,
        plan_name="Pro Lifetime License"
    )

    assert res["success"] is True
    assert res["license_key"].startswith("DSS-PRO-")
    assert res["order_id"] == f"UPI-{utr_code}"
    assert test_engine.is_utr_redeemed(utr_code) is True


def test_06_upi_utr_duplicate_rejection(test_engine):
    """Verify resubmission of already redeemed UPI UTR is rejected."""
    utr_code = "112233445566"
    test_engine.process_upi_utr_verification(
        utr_number=utr_code,
        customer_email="first@company.com",
        amount_inr=1499.0
    )

    dup_res = test_engine.process_upi_utr_verification(
        utr_number=utr_code,
        customer_email="fraudulent@attempt.com",
        amount_inr=1499.0
    )
    assert dup_res["success"] is False
    assert dup_res["error_code"] == "DUPLICATE_UTR_ALREADY_REDEEMED"


def test_07_upi_utr_invalid_format_and_insufficient_amount(test_engine):
    """Verify non-12-digit UTRs and short payments fail validation."""
    # Invalid length (10 digits)
    res_short = test_engine.process_upi_utr_verification(
        utr_number="1234567890",
        customer_email="test@co.com",
        amount_inr=1499.0
    )
    assert res_short["success"] is False
    assert res_short["error_code"] == "INVALID_UTR_FORMAT"

    # Insufficient payment amount (₹500 < ₹1,499)
    res_cheap = test_engine.process_upi_utr_verification(
        utr_number="123456789012",
        customer_email="test@co.com",
        amount_inr=500.0
    )
    assert res_cheap["success"] is False
    assert res_cheap["error_code"] == "INSUFFICIENT_PAYMENT_AMOUNT"


def test_08_customer_onboarding_email_payload(test_authority):
    """Verify transactional email payload contains keys, CLI installer, download URL, and anonymity."""
    cert = test_authority.generate_license_certificate(
        customer_email="eng@stripe.com",
        plan_name="Enterprise 100-Seat License",
        order_id="GUM-STRP-88",
        gateway="GUMROAD",
        amount_paid=42000.0,
        currency="USD",
        seats=100
    )

    email_payload = CustomerOnboardingEmailBuilder.build_payload(cert)
    assert email_payload["recipient"] == "eng@stripe.com"
    assert cert["license_key"] in email_payload["body_plain"]
    assert DOWNLOAD_URI in email_payload["body_plain"]
    assert INSTALL_SH_URI in email_payload["body_plain"]
    assert "growth@devsupersuite.com" in email_payload["body_plain"]
    assert "omnikernel --activate" in email_payload["body_plain"]


def test_09_audit_and_markdown_report_generation(test_engine):
    """Verify auditing dispatched licenses and rendering formal markdown report."""
    # Seed Gumroad & UPI dispatches
    test_engine.process_gumroad_webhook({
        "sale_id": "GUM-AUD-01",
        "email": "test1@co.com",
        "price": 2900
    })
    test_engine.process_upi_utr_verification(
        utr_number="888877776666",
        customer_email="test2@co.com",
        amount_inr=1499.0
    )

    audit = test_engine.audit_dispatched_licenses()
    assert audit["total_dispatches"] == 2
    assert audit["redeemed_utrs_count"] == 1
    assert audit["cryptographic_integrity_status"] == "100% VERIFIED"

    report_file = test_engine.render_markdown_report()
    assert os.path.exists(report_file)
    with open(report_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "License Key Auto-Provisioning & Webhook Unlock Report" in content
    assert "Multi-Gateway Distribution" in content
    assert "growth@devsupersuite.com" in content


def test_10_cli_interface_execution():
    """Verify all CLI subcommands execute successfully with exit code 0."""
    python_bin = sys.executable
    script_path = os.path.join(SERVICES_DIR, "enterprise_license_autopilot_engine.py")

    flags = [
        ["--summary"],
        ["--audit-dispatched-licenses"],
        ["--verify-upi-utr", "--utr", "990011223344", "--email", "cli.dev@co.com"],
        ["--process-gumroad-webhook", json.dumps({"sale_id": "GUM-CLI-901", "email": "cli@test.com", "price": 2900})],
        ["--export-autopilot-report"],
    ]

    for flag_group in flags:
        cmd = [python_bin, script_path] + flag_group
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        assert res.returncode == 0, f"Command {cmd} failed with stderr: {res.stderr}"


def test_11_strict_brand_anonymity_compliance():
    """Verify zero personal founder leaks across all Phase 26 assets."""
    forbidden_tokens = [
        bytes.fromhex("41746861727661").decode("utf-8"),
        bytes.fromhex("506164687965").decode("utf-8"),
        bytes.fromhex("39383930343431323933").decode("utf-8"),
    ]

    phase_26_files = [
        Path(SERVICES_DIR) / "enterprise_license_autopilot_engine.py",
        Path(DATA_DIR) / "autopilot_license_dispatches.json",
        Path(REPORTS_DIR) / "enterprise_license_autopilot_report.md",
        Path(TESTS_DIR) / "test_license_autopilot_engine.py",
    ]

    for file_path in phase_26_files:
        assert file_path.exists(), f"File {file_path} must exist"
        content = file_path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token.lower() not in content.lower(), (
                f"Brand anonymity violation: found forbidden token in {file_path}"
            )
