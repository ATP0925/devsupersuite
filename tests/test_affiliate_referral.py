"""
⚡ DevSuperSuite Official: Developer Affiliate & Referral Revenue Share Engine Integration Tests
File: test_affiliate_referral.py
Governing Entity: DevSuperSuite Official (affiliates@devsupersuite.com)
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

from affiliate_referral_engine import (
    AffiliateTokenManager,
    AffiliateReferralEngine,
    AFFILIATE_COMMISSION_RATE,
    BUYER_REFERRAL_DISCOUNT_USD,
    MINIMUM_PAYOUT_THRESHOLD_USD,
    AFFILIATES_LEDGER_PATH,
    REFERRALS_LEDGER_PATH
)


@pytest.fixture
def affiliate_engine(tmp_path):
    test_partners = os.path.join(tmp_path, "test_affiliate_partners.json")
    test_referrals = os.path.join(tmp_path, "test_affiliate_referrals.json")
    test_payouts = os.path.join(tmp_path, "test_payout_batches.json")
    return AffiliateReferralEngine(
        partners_path=test_partners,
        referrals_path=test_referrals,
        payouts_path=test_payouts
    )


def test_01_token_generation_and_hmac_verification():
    """Verify affiliate tracking tokens embed valid cryptographic HMAC nonces."""
    token = AffiliateTokenManager.generate_token("ALICE_DEV")
    assert token.startswith("DEV_ALICE_DEV_")

    is_valid, extracted_id = AffiliateTokenManager.verify_token(token)
    assert is_valid is True
    assert extracted_id == "ALICE_DEV"


def test_02_token_tamper_detection():
    """Verify modified or corrupted tokens are rejected by HMAC validation."""
    valid_token = AffiliateTokenManager.generate_token("BOB_ARCHITECT")
    
    # Tamper with the HMAC suffix
    tampered_token = valid_token[:-2] + "99"
    is_valid, _ = AffiliateTokenManager.verify_token(tampered_token)
    assert is_valid is False

    # Tamper with the affiliate id prefix
    tampered_id = "DEV_HACKER_ARCHITECT" + valid_token[len("DEV_BOB_ARCHITECT"):]
    is_valid_id, _ = AffiliateTokenManager.verify_token(tampered_id)
    assert is_valid_id is False

    # Malformed tokens
    assert AffiliateTokenManager.verify_token("")[0] is False
    assert AffiliateTokenManager.verify_token("INVALID_TOKEN")[0] is False


def test_03_partner_registration_and_deduplication(affiliate_engine):
    """Verify new partner registration and idempotency."""
    partner = affiliate_engine.register_or_get_partner(
        affiliate_id="CAROL_CLOUD",
        name="Carol Danvers",
        email="carol@cloudscale.io",
        payout_address="carol.pay@paypal.com"
    )
    assert partner["affiliate_id"] == "CAROL_CLOUD"
    assert "tracking_token" in partner
    assert partner["status"] == "ACTIVE"

    # Duplicate call returns existing profile
    dup = affiliate_engine.register_or_get_partner(
        affiliate_id="CAROL_CLOUD",
        name="Carol Danvers",
        email="carol@cloudscale.io",
        payout_address="carol.pay@paypal.com"
    )
    assert dup["tracking_token"] == partner["tracking_token"]


def test_04_referral_url_synthesis(affiliate_engine):
    """Verify generation of UTM-enriched landing page and Gumroad direct checkout URLs."""
    token = AffiliateTokenManager.generate_token("DAVE_SYSTEMS")
    urls = affiliate_engine.build_referral_urls(token)

    assert "landing_page_url" in urls
    assert "gumroad_direct_url" in urls

    assert f"ref={token}" in urls["landing_page_url"]
    assert "utm_source=affiliate" in urls["landing_page_url"]

    assert "discount=VIPDEV5" in urls["gumroad_direct_url"]
    assert f"ref={token}" in urls["gumroad_direct_url"]


def test_05_two_sided_economics_processing(affiliate_engine):
    """Verify $5 buyer discount and 25% referring partner commission on Hacker Solo ($29)."""
    partner = affiliate_engine.partners[0]
    token = partner["tracking_token"]
    initial_balance = partner["pending_balance_usd"]

    res = affiliate_engine.process_referral_transaction(
        token=token,
        buyer_email="new.developer@fintech.io",
        plan_name="Hacker Solo",
        gross_price_usd=29.00
    )

    assert res["status"] == "APPROVED"
    assert res["buyer_savings_usd"] == 5.00
    assert res["net_paid_usd"] == 24.00
    # 25% of $24 = $6.00
    assert res["commission_earned_usd"] == 6.00
    assert partner["pending_balance_usd"] == initial_balance + 6.00


def test_06_team_plan_referral_commission(affiliate_engine):
    """Verify $5 discount and 25% commission on Team 5-Seat Pack ($149)."""
    partner = affiliate_engine.partners[0]
    token = partner["tracking_token"]

    res = affiliate_engine.process_referral_transaction(
        token=token,
        buyer_email="team.buyer@scaleup.de",
        plan_name="Team 5-Seat",
        gross_price_usd=149.00
    )

    assert res["status"] == "APPROVED"
    assert res["buyer_savings_usd"] == 5.00
    assert res["net_paid_usd"] == 144.00
    # 25% of $144 = $36.00
    assert res["commission_earned_usd"] == 36.00


def test_07_anti_fraud_self_referral_blocker(affiliate_engine):
    """Verify self-referral attempts are intercepted and rejected."""
    partner = affiliate_engine.partners[0]
    token = partner["tracking_token"]

    # Attempt to purchase using own email
    res1 = affiliate_engine.process_referral_transaction(
        token=token,
        buyer_email=partner["email"],
        plan_name="Hacker Solo"
    )
    assert res1["status"] == "REJECTED_FRAUD_SELF_REFERRAL"

    # Attempt to purchase using own payout address
    res2 = affiliate_engine.process_referral_transaction(
        token=token,
        buyer_email=partner["payout_address"],
        plan_name="Hacker Solo"
    )
    assert res2["status"] == "REJECTED_FRAUD_SELF_REFERRAL"


def test_08_payout_threshold_gating_and_rollover(affiliate_engine):
    """Verify $50 threshold gating filters eligible partners from rollover partners."""
    audit = affiliate_engine.audit_affiliate_payouts()

    assert audit["payout_threshold_usd"] == 50.00
    assert audit["eligible_partners_count"] >= 1
    assert audit["rolled_over_partners_count"] >= 1

    # Elena has $66 >= $50 -> eligible
    elena = next((e for e in audit["eligible_partners"] if e["affiliate_id"] == "ELENA_ROSTOVA"), None)
    assert elena is not None
    assert elena["amount_due_usd"] >= 50.00

    # Marcus has $30 < $50 -> rolled over
    marcus = next((r for r in audit["rolled_over_partners"] if r["affiliate_id"] == "MARCUS_CODE"), None)
    assert marcus is not None
    assert marcus["amount_due_usd"] < 50.00
    assert marcus["threshold_gap_usd"] > 0.00


def test_09_monthly_payout_batch_settlement(affiliate_engine):
    """Verify disbursement batch clears pending balances and updates referral statuses."""
    audit_pre = affiliate_engine.audit_affiliate_payouts()
    pre_eligible_count = audit_pre["eligible_partners_count"]
    assert pre_eligible_count >= 1

    batch_res = affiliate_engine.generate_monthly_payout_batch()
    assert batch_res["status"] == "BATCH_DISPATCHED"
    assert batch_res["batch_id"].startswith("PAYOUT-BATCH-")
    assert batch_res["amount_usd"] == audit_pre["eligible_payout_amount_usd"]

    # Verify Elena's balance is cleared
    elena = next(p for p in affiliate_engine.partners if p["affiliate_id"] == "ELENA_ROSTOVA")
    assert elena["pending_balance_usd"] == 0.00
    assert elena["paid_out_usd"] > 0.00

    # Post-batch audit: eligible partners should now be 0
    audit_post = affiliate_engine.audit_affiliate_payouts()
    assert audit_post["eligible_partners_count"] == 0


def test_10_cli_commands_execution():
    """Verify all 4 required CLI commands execute with exit code 0."""
    script_path = os.path.join(SERVICES_DIR, "affiliate_referral_engine.py")

    cmds = [
        [sys.executable, script_path, "--generate-affiliate-link", "--affiliate-id", "CLI_TEST_DEV"],
        [sys.executable, script_path, "--process-referrals"],
        [sys.executable, script_path, "--audit-affiliate-payouts"],
        [sys.executable, script_path, "--summary"]
    ]

    for cmd in cmds:
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0, f"CLI command failed: {' '.join(cmd)}\n{res.stderr}"


def test_11_strict_brand_anonymity_affiliate():
    """Verify strict 100% brand anonymity: zero personal founder names or numbers."""
    files_to_check = [
        os.path.join(SERVICES_DIR, "affiliate_referral_engine.py"),
        os.path.join(MARKETING_DIR, "developer_affiliate_program_handbook.md"),
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
