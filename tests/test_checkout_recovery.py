"""
⚡ DevSuperSuite Official: Automated Checkout Recovery Engine Integration Tests
File: test_checkout_recovery.py
Governing Entity: DevSuperSuite Official (cro@devsupersuite.com)
Strict Protocol: 100% Brand Anonymity - Zero Founder Personal Identifiers
"""

import os
import sys
import json
import pytest
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Paths Setup
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(SCRATCH_DIR, "services")
DATA_DIR = os.path.join(SCRATCH_DIR, "data")
MARKETING_DIR = os.path.join(SCRATCH_DIR, "marketing")

sys.path.insert(0, SERVICES_DIR)

from checkout_recovery_webhook_engine import (
    CheckoutRecoveryEngine,
    DynamicIncentiveCalculator,
    UtmAttributionLinkBuilder,
    ABANDONED_LEDGER_PATH,
    RECOVERY_PAYLOADS_PATH,
    RUNBOOK_DISPATCH_PATH
)


@pytest.fixture
def recovery_engine(tmp_path):
    test_ledger = os.path.join(tmp_path, "test_abandoned_ledger.json")
    return CheckoutRecoveryEngine(ledger_path=test_ledger)


def test_01_initial_ledger_seeding(recovery_engine):
    """Verify engine initializes with clean seed dataset when ledger does not exist."""
    assert len(recovery_engine.sessions) >= 3
    for session in recovery_engine.sessions:
        assert "session_id" in session
        assert "customer_email" in session
        assert "base_amount" in session
        assert session["base_amount"] in [29.00, 149.00]


def test_02_webhook_ingestion_multi_source(recovery_engine):
    """Verify ingestion of webhooks from Gumroad, Stripe, and Custom storefronts."""
    now = datetime.now(timezone.utc).isoformat()

    # Gumroad
    g_payload = {
        "session_id": "TEST-GUM-001",
        "email": "gumroad.user@test.org",
        "name": "Gumroad Dev",
        "product_name": "Hacker Solo",
        "price": 29.00,
        "abandoned_at": now,
        "utm_params": {"utm_source": "reddit", "utm_campaign": "test_launch"}
    }
    res_g = recovery_engine.ingest_webhook(g_payload, source="gumroad")
    assert res_g["status"] == "ingested"
    assert res_g["session"]["customer_email"] == "gumroad.user@test.org"

    # Stripe
    s_payload = {
        "session_id": "TEST-STR-002",
        "customer_details": {"email": "stripe.user@test.org", "name": "Stripe Dev"},
        "plan_name": "Team 5-Seat",
        "base_amount": 149.00,
        "abandoned_at": now
    }
    res_s = recovery_engine.ingest_webhook(s_payload, source="stripe")
    assert res_s["status"] == "ingested"
    assert res_s["session"]["customer_email"] == "stripe.user@test.org"

    # Deduplication test
    dup_res = recovery_engine.ingest_webhook(g_payload, source="gumroad")
    assert dup_res["status"] == "exists"


def test_03_time_decay_incentive_calculation():
    """Verify dynamic incentive discounting across time elapsed thresholds."""
    # Stage 1: 0.5 hours (< 1h) -> 0% discount
    t1 = DynamicIncentiveCalculator.evaluate_tier(0.5, 29.00)
    assert t1["stage"] == 1
    assert t1["discount_pct"] == 0.0
    assert t1["offer_price"] == 29.00
    assert t1["coupon"] is None

    # Stage 2: 5.0 hours (1h-24h) -> 10% discount
    t2 = DynamicIncentiveCalculator.evaluate_tier(5.0, 29.00)
    assert t2["stage"] == 2
    assert t2["discount_pct"] == 10.0
    assert t2["coupon"] == "RECOVER10"
    assert t2["offer_price"] == 26.10

    # Stage 3: 36.0 hours (24h-72h) -> 15% discount
    t3 = DynamicIncentiveCalculator.evaluate_tier(36.0, 29.00)
    assert t3["stage"] == 3
    assert t3["discount_pct"] == 15.0
    assert t3["coupon"] == "RECOVER15"
    assert t3["offer_price"] == 24.65

    # Stage 4: 90.0 hours (72h+) -> VIP Deal ($24.00 flat)
    t4 = DynamicIncentiveCalculator.evaluate_tier(90.0, 29.00)
    assert t4["stage"] == 4
    assert t4["coupon"] == "VIPDEV5"
    assert t4["offer_price"] == 24.00


def test_04_margin_floor_protection():
    """Verify engine enforces $24.00 Solo floor and $129.00 Team floor."""
    # Attempting extreme discount on Solo: floor must hold at $24.00
    res_solo = DynamicIncentiveCalculator.evaluate_tier(500.0, 29.00)
    assert res_solo["offer_price"] >= DynamicIncentiveCalculator.MINIMUM_SOLO_FLOOR_USD
    assert res_solo["offer_price"] == 24.00

    # Team plan floor: $149 -> 15% discount is $126.65, but floor enforces $129.00
    res_team = DynamicIncentiveCalculator.evaluate_tier(50.0, 149.00)
    assert res_team["offer_price"] >= DynamicIncentiveCalculator.MINIMUM_TEAM_FLOOR_USD


def test_05_utm_link_enrichment_and_paypal_synthesis():
    """Verify outbound URLs preserve inbound UTM tags and synthesize dual-gate PayPal links."""
    base_gumroad = "https://gumroad.com/l/tlzdco"
    inbound_utms = {"utm_source": "hackernews", "utm_campaign": "ast_demo", "ref": "hn_fp"}
    
    enriched_url = UtmAttributionLinkBuilder.enrich_gumroad_url(
        base_gumroad,
        coupon="RECOVER10",
        utm_params=inbound_utms,
        stage=2
    )

    assert "discount=RECOVER10" in enriched_url
    assert "utm_source=hackernews" in enriched_url
    assert "utm_campaign=cart_recovery_stage2" in enriched_url
    assert "utm_medium=recovery_email" in enriched_url

    # PayPal link synthesis
    paypal_url = UtmAttributionLinkBuilder.build_paypal_direct_url("https://paypal.me/devsupersuite", 26.10)
    assert "paypal.me/devsupersuite/26.10USD" in paypal_url

    paypal_url_int = UtmAttributionLinkBuilder.build_paypal_direct_url("https://paypal.me/devsupersuite", 24.0)
    assert "paypal.me/devsupersuite/24USD" in paypal_url_int


def test_06_process_abandoned_progression(recovery_engine):
    """Verify processing advances recovery stages based on simulated elapsed time."""
    now = datetime.now(timezone.utc)
    # Fast forward evaluation to 30 hours later
    future_time = now + timedelta(hours=30)
    processed = recovery_engine.process_abandoned(current_time=future_time)
    assert len(processed) >= 1
    for p in processed:
        assert p["new_stage"] >= 2
        assert "incentive" in p


def test_07_recovery_payload_generation(recovery_engine, tmp_path):
    """Verify multi-channel recovery payloads contain all required copy, pricing, and links."""
    payloads = recovery_engine.generate_recovery_payloads()
    assert len(payloads) >= 1

    sample = payloads[0]
    assert "session_id" in sample
    assert "customer_email" in sample
    assert "checkout_url_gumroad" in sample
    assert "checkout_url_paypal" in sample
    assert "email_subject" in sample
    assert "email_body" in sample
    assert "sms_body" in sample

    # Check trust badges in copy
    assert "30-Day" in sample["email_body"]
    assert "OmniKernel 5.0" in sample["email_body"]
    assert "cro@devsupersuite.com" in sample["email_body"]


def test_08_revenue_audit_metrics(recovery_engine):
    """Verify financial audit calculations for pipeline and recovery conversion rate."""
    stats = recovery_engine.audit_recovered_revenue()
    assert "total_abandoned_sessions" in stats
    assert "recovered_count" in stats
    assert "unrecovered_count" in stats
    assert "recovered_revenue_usd" in stats
    assert "abandoned_pipeline_usd" in stats
    assert "recovery_conversion_rate_pct" in stats

    assert stats["total_abandoned_sessions"] == stats["recovered_count"] + stats["unrecovered_count"]
    assert stats["recovered_revenue_usd"] >= 0.0


def test_09_cli_execution_commands():
    """Verify all 4 required CLI commands execute with exit code 0."""
    script_path = os.path.join(SERVICES_DIR, "checkout_recovery_webhook_engine.py")

    cmds = [
        [sys.executable, script_path, "--process-abandoned"],
        [sys.executable, script_path, "--generate-recovery-payloads"],
        [sys.executable, script_path, "--audit-recovered-revenue"],
        [sys.executable, script_path, "--summary"]
    ]

    for cmd in cmds:
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0, f"CLI command failed: {' '.join(cmd)}\n{res.stderr}"


def test_10_strict_brand_anonymity_recovery_service():
    """Verify strict 100% brand anonymity: zero personal founder names or numbers."""
    files_to_check = [
        os.path.join(SERVICES_DIR, "checkout_recovery_webhook_engine.py"),
        os.path.join(MARKETING_DIR, "cart_abandonment_recovery_automation_runbook.md"),
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
