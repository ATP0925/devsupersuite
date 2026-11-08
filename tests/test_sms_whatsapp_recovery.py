"""
⚡ DevSuperSuite Official: High-Velocity SMS & WhatsApp Cart Abandonment Recovery Tests
File: test_sms_whatsapp_recovery.py
Governing Entity: DevSuperSuite Growth Engineering (growth@devsupersuite.com)
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
MARKETING_DIR = os.path.join(SCRATCH_DIR, "marketing")
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")

sys.path.insert(0, SERVICES_DIR)

from sms_whatsapp_abandonment_recovery_engine import (
    InternationalPhoneNormalizer,
    SuppressionEngine,
    SMSWhatsAppAbandonmentRecoveryEngine,
    RECOVER_20_COUPON,
    BASE_RECOVERY_URL
)


@pytest.fixture
def temp_recovery_engine(tmp_path):
    suppression_file = os.path.join(tmp_path, "suppression.json")
    dispatches_file = os.path.join(tmp_path, "dispatches.json")
    report_file = os.path.join(tmp_path, "report.md")
    templates_file = os.path.join(MARKETING_DIR, "cro_sms_recovery_templates.json")

    return SMSWhatsAppAbandonmentRecoveryEngine(
        suppression_path=suppression_file,
        dispatches_path=dispatches_file,
        templates_path=templates_file,
        report_path=report_file
    )


def test_01_phone_number_normalization_e164():
    """Verify phone normalizer standardizes US, IN, DE, BR numbers and rejects invalid strings."""
    # US normalization
    valid, e164, country = InternationalPhoneNormalizer.normalize("(415) 555-0199", default_country="US")
    assert valid is True
    assert e164 == "+14155550199"
    assert country == "US/CA"

    # India normalization
    valid, e164, country = InternationalPhoneNormalizer.normalize("09876543210", default_country="IN")
    assert valid is True
    assert e164 == "+919876543210"
    assert country == "IN"

    # Germany normalization
    valid, e164, country = InternationalPhoneNormalizer.normalize("+49 170 8829102", default_country="DE")
    assert valid is True
    assert e164 == "+491708829102"
    assert country == "DE"

    # Brazil normalization
    valid, e164, country = InternationalPhoneNormalizer.normalize("11 98765-4321", default_country="BR")
    assert valid is True
    assert e164 == "+5511987654321"
    assert country == "BR"

    # Invalid cases
    valid, _, _ = InternationalPhoneNormalizer.normalize("12345")
    assert valid is False

    valid, _, _ = InternationalPhoneNormalizer.normalize("invalid_alphabet")
    assert valid is False


def test_02_sequence_stage_timing_determination(temp_recovery_engine):
    """Verify timing router correctly maps elapsed minutes to appropriate sequence stages."""
    # T+15m window
    assert temp_recovery_engine.determine_sequence_stage(20.0) == "STAGE_1_15M"
    assert temp_recovery_engine.determine_sequence_stage(180.0) == "STAGE_1_15M"

    # T+4h window
    assert temp_recovery_engine.determine_sequence_stage(300.0) == "STAGE_2_4H"
    assert temp_recovery_engine.determine_sequence_stage(1200.0) == "STAGE_2_4H"

    # T+24h window
    assert temp_recovery_engine.determine_sequence_stage(1500.0) == "STAGE_3_24H"
    assert temp_recovery_engine.determine_sequence_stage(2800.0) == "STAGE_3_24H"


def test_03_suppression_engine_and_stop_keyword(temp_recovery_engine):
    """Verify TCPA STOP keyword handling registers opt-out and blocks future dispatches."""
    test_phone = "+14155550199"
    suppression = temp_recovery_engine.suppression_engine

    assert suppression.is_suppressed(test_phone) is False

    # Simulate inbound STOP
    processed, reply = suppression.process_inbound_sms(test_phone, "STOP")
    assert processed is True
    assert "unsubscribed" in reply.lower()
    assert suppression.is_suppressed(test_phone) is True

    # Try preparing a dispatch for suppressed number
    cart = {
        "session_id": "ABND-SUPPRESSED-TEST",
        "customer_name": "Opted Out Dev",
        "customer_phone": test_phone,
        "country": "US"
    }
    dispatch_res = temp_recovery_engine.prepare_recovery_dispatch(cart)
    assert dispatch_res["status"] == "SUPPRESSED"
    assert "opt-out" in dispatch_res["reason"].lower()


def test_04_recovery_url_construction_and_utm(temp_recovery_engine):
    """Verify recovery URL builder includes discount coupon, email, and UTM attribution parameters."""
    url = temp_recovery_engine.build_recovery_url(
        coupon_code="RECOVER20",
        email="developer@quantum.io",
        stage_id="STAGE_3_24H"
    )

    assert BASE_RECOVERY_URL in url
    assert "discount=RECOVER20" in url
    assert "email=developer@quantum.io" in url
    assert "utm_source=sms_recovery" in url
    assert "utm_campaign=abandonment_stage_3_24h" in url


def test_05_prepare_recovery_dispatch_stage_3_incentive(temp_recovery_engine):
    """Verify Stage 3 dispatch applies 20% discount coupon and includes TCPA opt-out text."""
    from datetime import datetime, timezone, timedelta
    now_utc = datetime.now(timezone.utc)

    cart = {
        "session_id": "ABND-EXPIRY-001",
        "customer_name": "Elena Rostova",
        "customer_email": "elena@berlincloud.de",
        "customer_phone": "+49 170 1234567",
        "country": "DE",
        "abandoned_at": (now_utc - timedelta(hours=25)).isoformat()
    }

    dispatch = temp_recovery_engine.prepare_recovery_dispatch(cart)

    assert dispatch is not None
    assert dispatch["stage_id"] == "STAGE_3_24H"
    assert dispatch["coupon_applied"] == RECOVER_20_COUPON
    assert dispatch["status"] == "QUEUED_FOR_DISPATCH"

    # SMS Compliance check
    sms = dispatch["sms_payload"]
    assert sms["channel"] == "SMS"
    assert sms["opt_out_compliant"] is True
    assert "STOP" in sms["body"]
    assert "RECOVER20" in sms["body"]

    # WhatsApp Payload check
    wa = dispatch["whatsapp_payload"]
    assert wa["channel"] == "WHATSAPP"
    assert "RECOVER20" in wa["body"]


def test_06_dispatch_abandoned_recoveries_queue(temp_recovery_engine):
    """Verify processing batch queue successfully prepares and logs multi-national dispatches."""
    results = temp_recovery_engine.dispatch_abandoned_recoveries()
    assert len(results) == 4

    countries_seen = {r["country"] for r in results}
    assert "DE" in countries_seen
    assert "IN" in countries_seen
    assert "BR" in countries_seen
    assert "US/CA" in countries_seen

    assert len(temp_recovery_engine.dispatches_log) == 4
    for d in temp_recovery_engine.dispatches_log:
        assert d["status"] == "QUEUED_FOR_DISPATCH"
        assert d["phone_e164"].startswith("+")


def test_07_audit_compliance_and_report_generation(temp_recovery_engine):
    """Verify compliance audit and markdown report generation."""
    temp_recovery_engine.dispatch_abandoned_recoveries()
    audit = temp_recovery_engine.audit_sms_compliance()

    assert audit["total_dispatches_audited"] == 4
    assert audit["tcpa_compliant_dispatches"] == 4
    assert audit["is_fully_compliant"] is True

    report_path = temp_recovery_engine.render_markdown_report()
    assert os.path.exists(report_path)
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "# ⚡ DevSuperSuite Official: SMS & WhatsApp Cart Abandonment Recovery Report" in content
    assert "growth@devsupersuite.com" in content
    assert "| Dispatch ID | Session ID | E.164 Recipient |" in content


def test_08_cli_commands_execution():
    """Verify all 4 CLI command flags run cleanly with exit code 0."""
    script_path = os.path.join(SERVICES_DIR, "sms_whatsapp_abandonment_recovery_engine.py")

    cmds = [
        [sys.executable, script_path, "--dispatch-abandoned-recoveries"],
        [sys.executable, script_path, "--audit-sms-compliance"],
        [sys.executable, script_path, "--export-recovery-metrics"],
        [sys.executable, script_path, "--summary"]
    ]

    for cmd in cmds:
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0, f"CLI command failed: {' '.join(cmd)}\n{res.stderr}"


def test_09_strict_brand_anonymity():
    """Verify strict 100% brand anonymity: zero personal founder names or numbers."""
    files_to_check = [
        os.path.join(SERVICES_DIR, "sms_whatsapp_abandonment_recovery_engine.py"),
        os.path.join(MARKETING_DIR, "cro_sms_whatsapp_recovery_playbook.md"),
        os.path.join(MARKETING_DIR, "cro_sms_recovery_templates.json"),
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
