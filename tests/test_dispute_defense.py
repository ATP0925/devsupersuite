"""
⚡ DevSuperSuite Commercial Operations - Unit & Integration Test Suite
File: test_dispute_defense.py
Target: dispute_defense_engine.py (Enterprise Billing Dispute Resolution, Chargeback Defense & Escrow Protection Engine)
Strict Compliance: 100% Brand Anonymity - DevSuperSuite Commercial Operations Only.
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timezone
import pytest

# Add services directory to sys.path
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(SCRATCH_DIR, "services")
sys.path.insert(0, SERVICES_DIR)

from dispute_defense_engine import (
    DisputeDefenseEngine,
    SOFTWARE_PACKAGE_NAME,
    SOFTWARE_PACKAGE_SIZE_BYTES,
    SOFTWARE_PACKAGE_SHA256,
    TERMS_VERSION,
    DEFAULT_DISPUTE_RESERVE_PCT,
    CARD_BRAND_WARNING_THRESHOLD_BPS,
    STORE_LEDGER_FILE,
    SETTLEMENT_LEDGER_FILE
)

@pytest.fixture
def defense_engine():
    """Initializes Dispute Defense Engine with primary commercial ledgers."""
    return DisputeDefenseEngine(
        store_ledger_path=STORE_LEDGER_FILE,
        settlement_ledger_path=SETTLEMENT_LEDGER_FILE
    )

def test_01_rebuttal_evidence_compiler_existing_order(defense_engine):
    """Verifies evidence compiler retrieves order details and prepares dispute rebuttal."""
    evidence = defense_engine.compile_rebuttal_evidence(
        order_id="TXN-2026-DSS-001",
        dispute_reason="fraudulent_unauthorized",
        card_brand="Visa"
    )

    assert evidence["order_id"] == "TXN-2026-DSS-001"
    assert evidence["customer_email"] == "alex.chen@vibe-engineers.io"
    assert evidence["amount_usd"] == 29.00
    assert "Hacker Solo" in evidence["product_name"]
    assert evidence["card_brand"] == "Visa"
    assert evidence["dispute_reason"] == "fraudulent_unauthorized"
    assert evidence["merchant_authority"] == "DevSuperSuite Commercial Operations"
    assert evidence["contact_email"] == "billing@devsupersuite.com"

def test_02_cryptographic_proof_and_checksum_integrity(defense_engine):
    """Verifies Ed25519 asymmetric signature and SHA-256 binary package checksum."""
    evidence = defense_engine.compile_rebuttal_evidence("TXN-2026-DSS-001")
    crypto = evidence["cryptographic_proof"]
    dist = evidence["distribution_proof"]

    # Ed25519 Cryptographic Verification
    assert crypto["license_key"].startswith("DSS-")
    assert crypto["ed25519_signature"] is not None
    assert "Ed25519" in crypto["key_algorithm"]
    assert crypto["verification_status"] == "CRYPTOGRAPHICALLY_VERIFIED_AUTHENTIC"

    # Software Payload Checksum Verification
    assert dist["package_name"] == SOFTWARE_PACKAGE_NAME
    assert dist["package_size_bytes"] == SOFTWARE_PACKAGE_SIZE_BYTES
    assert dist["sha256_checksum"] == SOFTWARE_PACKAGE_SHA256
    assert "HTTP 200 OK" in dist["cdn_delivery_status"]

def test_03_clickwrap_acceptance_and_refund_policy_proof(defense_engine):
    """Verifies clickwrap binding and statutory waiver of withdrawal rights."""
    evidence = defense_engine.compile_rebuttal_evidence("TXN-2026-DSS-001")
    clickwrap = evidence["clickwrap_log"]

    assert clickwrap["terms_version"] == TERMS_VERSION
    assert clickwrap["checkbox_status"] == "CHECKED_TRUE"
    assert "16 CFR Part 436" in clickwrap["mandatory_waiver_text"]
    assert "2011/83/EU Article 16(m)" in clickwrap["mandatory_waiver_text"]
    assert clickwrap["accepted_at_utc"] is not None

def test_04_formal_representation_letters(defense_engine):
    """Verifies generation of formal representment letters for Stripe, PayPal, and Card Brands."""
    evidence_visa = defense_engine.compile_rebuttal_evidence("TXN-2026-DSS-001", card_brand="Visa")
    evidence_mc = defense_engine.compile_rebuttal_evidence("TXN-2026-DSS-001", card_brand="Mastercard")
    evidence_amex = defense_engine.compile_rebuttal_evidence("TXN-2026-DSS-001", card_brand="Amex")

    letters = evidence_visa["representation_letters"]

    # 1. Stripe Radar Letter
    assert "STRIPE RADAR & ACQUIRING ARBITRATION" in letters["stripe_radar"]
    assert "COMPELLING EVIDENCE 3.0" in letters["stripe_radar"]
    assert "DevSuperSuite Commercial Operations" in letters["stripe_radar"]
    assert evidence_visa["customer_email"] in letters["stripe_radar"]

    # 2. PayPal Resolution Center Letter
    assert "PAYPAL RESOLUTION CENTER" in letters["paypal_resolution_center"]
    assert "PAYPAL SELLER PROTECTION" in letters["paypal_resolution_center"]
    assert "INTANGIBLE DIGITAL GOODS DELIVERY" in letters["paypal_resolution_center"]

    # 3. Card Brand Letters (Visa, Mastercard, Amex)
    assert "Reason Code 10.4" in evidence_visa["representation_letters"]["card_brand_arbitration"]
    assert "Reason Code 4837" in evidence_mc["representation_letters"]["card_brand_arbitration"]
    assert "Reason Code F29" in evidence_amex["representation_letters"]["card_brand_arbitration"]

def test_05_rolling_escrow_reserve_calculation(defense_engine):
    """Verifies 5.0% rolling escrow reserve calculation and card brand threshold compliance."""
    reserves = defense_engine.audit_escrow_reserves()

    assert reserves["reserve_rate_pct"] == DEFAULT_DISPUTE_RESERVE_PCT
    assert reserves["total_gross_volume_usd"] == 24930.00
    assert reserves["retail_card_volume_usd"] == 331.00
    assert reserves["enterprise_wire_volume_usd"] == 24599.00
    assert reserves["actual_reserves_held_usd"] == 2.90
    assert reserves["target_retail_reserve_usd"] == round(331.00 * 0.05, 2)  # $16.55

    # Dispute Rate & Network Thresholds
    assert reserves["active_disputes_count"] == 0
    assert reserves["active_disputed_volume_usd"] == 0.00
    assert reserves["dispute_rate_bps"] == 0.0
    assert reserves["dispute_rate_bps"] < CARD_BRAND_WARNING_THRESHOLD_BPS  # < 90.0 bps
    assert "CARD_BRAND_SAFE_HARBOR" in reserves["compliance_status"]

    # Rolling Schedule
    assert len(reserves["rolling_schedule"]) == 3
    total_scheduled = sum(t["amount_usd"] for t in reserves["rolling_schedule"])
    assert total_scheduled == pytest.approx(reserves["target_retail_reserve_usd"], abs=0.05)

def test_06_velocity_tripwire_normal_traffic(defense_engine):
    """Verifies that <= 2 failed attempts in 10 minutes does not trip fraud velocity limit."""
    ip = "203.0.113.15"
    now_iso = datetime.now(timezone.utc).isoformat()
    attempts = [
        {"ip_address": ip, "status": "FAILED", "timestamp": now_iso},
        {"ip_address": ip, "status": "FAILED", "timestamp": now_iso}
    ]

    result = defense_engine.check_velocity_tripwire(ip, attempts, window_seconds=600)

    assert result["triggered"] is False
    assert result["status"] == "VELOCITY_NORMAL"
    assert result["action"] == "ALLOW_CHECKOUT"
    assert result["response_code"] == 200
    assert result["failed_attempts_in_window"] == 2

def test_07_velocity_tripwire_card_testing_detection(defense_engine):
    """Verifies that >= 3 failed attempts in 10 minutes triggers automated IP block."""
    attacker_ip = "192.0.2.88"
    now_iso = datetime.now(timezone.utc).isoformat()
    attempts = [
        {"ip_address": attacker_ip, "status": "FAILED", "timestamp": now_iso},
        {"ip_address": attacker_ip, "status": "DECLINED", "timestamp": now_iso},
        {"ip_address": attacker_ip, "status": "FAILED", "timestamp": now_iso}
    ]

    result = defense_engine.check_velocity_tripwire(attacker_ip, attempts, window_seconds=600)

    assert result["triggered"] is True
    assert result["status"] == "TRIPWIRE_TRIGGERED_IP_BANNED"
    assert result["action"] == "BLOCK_AND_RATE_LIMIT"
    assert result["response_code"] == 429
    assert result["failed_attempts_in_window"] == 3
    assert "Card testing detected" in result["tripwire_reason"]

def test_08_defense_packet_generation_and_brand_anonymity(defense_engine, tmp_path):
    """Generates chargeback defense packet and asserts strict 100% Brand Anonymity."""
    test_out = os.path.join(tmp_path, "test_defense_packet.md")
    defense_engine.save_defense_packet("TXN-2026-DSS-001", test_out)

    assert os.path.exists(test_out)
    with open(test_out, "r", encoding="utf-8") as f:
        content = f.read()

    # Brand authority assertions
    assert "DevSuperSuite Commercial Operations" in content
    assert "billing@devsupersuite.com" in content
    assert "TXN-2026-DSS-001" in content
    assert "1996298036b8b9bec31b97213fa9c467084d1f7196a46871321a941c439f8d19" in content
    assert "99,039 Bytes" in content
    assert "Terms v2026.1" in content
    assert "16 CFR Part 436" in content
    assert "2011/83/EU Article 16(m)" in content

    # Strict Anonymity: zero personal founder tokens
    forbidden = ["Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"]
    for word in forbidden:
        assert word not in content, f"Brand Anonymity violation: found '{word}' in defense packet."

def test_09_cli_execution():
    """Verifies dispute defense engine CLI execution with all flags."""
    script_path = os.path.join(SERVICES_DIR, "dispute_defense_engine.py")

    cmd = [
        sys.executable, script_path,
        "--compile-defense", "TXN-2026-DSS-001",
        "--audit-reserves",
        "--test-velocity",
        "--summary"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert "Chargeback Rebuttal Evidence" in res.stdout
    assert "TXN-2026-DSS-001" in res.stdout
    assert "Anti-Fraud Velocity Tripwire Diagnostics" in res.stdout
    assert "TRIPWIRE_TRIGGERED_IP_BANNED" in res.stdout
    assert "Rolling Escrow Reserves & Dispute Audit" in res.stdout
    assert "PASSED_WITHIN_CARD_BRAND_SAFE_HARBOR" in res.stdout
