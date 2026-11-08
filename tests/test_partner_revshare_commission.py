"""
⚡ DevSuperSuite Official: Enterprise Partner Revenue Share, Referral Commission & Withholding Tests
File: test_partner_revshare_commission.py
Governing Authority: DevSuperSuite Partner Commercial Desk (alliances@devsupersuite.com)
Strict Protocol: 100% Brand Anonymity - Zero Founder Personal Identifiers
"""

import os
import sys
import json
import pytest
import subprocess
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

# Paths Setup
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(SCRATCH_DIR, "services")
SERVICES_DATA_DIR = os.path.join(SERVICES_DIR, "data")
ROOT_DATA_DIR = os.path.join(SCRATCH_DIR, "data")
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")

if SCRATCH_DIR not in sys.path:
    sys.path.insert(0, SCRATCH_DIR)
if SERVICES_DIR not in sys.path:
    sys.path.insert(0, SERVICES_DIR)

from services.enterprise_partner_revshare_commission_engine import (
    CrossBorderTaxWithholdingAuthority,
    CryptographicPartnerPayoutAuthority,
    EnterprisePartnerRevshareEngine,
    PARTNER_TIERS,
    FX_RATES,
    EXCLUSIVE_DEAL_LOCK_DAYS,
    PRIMARY_SCHEDULE_PATH,
    ROOT_SCHEDULE_PATH,
    REPORT_PATH
)


@pytest.fixture
def tmp_engine(tmp_path):
    """Provides isolated EnterprisePartnerRevshareEngine with temporary ledger."""
    p_path = str(tmp_path / "test_primary_partner_schedules.json")
    r_path = str(tmp_path / "test_root_partner_schedules.json")
    rep_path = str(tmp_path / "test_partner_report.md")
    return EnterprisePartnerRevshareEngine(
        primary_path=p_path,
        root_path=r_path,
        report_path=rep_path
    )


def test_01_partner_tier_commission_rates():
    """Verify tier commission rates match commercial governance specifications."""
    # Tier 1 (CIP): 20% software, 0% hardware
    cip = PARTNER_TIERS["CIP"]
    assert cip["software_commission_pct"] == 20.0
    assert cip["hardware_margin_pct"] == 0.0

    # Tier 2 (SES): 28% software, 20% hardware
    ses = PARTNER_TIERS["SES"]
    assert ses["software_commission_pct"] == 28.0
    assert ses["hardware_margin_pct"] == 20.0

    # Tier 3 (ESA): 35% software, 35% hardware
    esa = PARTNER_TIERS["ESA"]
    assert esa["software_commission_pct"] == 35.0
    assert esa["hardware_margin_pct"] == 35.0

    assert EXCLUSIVE_DEAL_LOCK_DAYS == 120


def test_02_commission_calculation_precision(tmp_engine):
    """Verify tiered commission calculation precision across software ARR and hardware."""
    # 1. ESA Tier (Accenture Federal Services): $100k soft, $20k hard
    esa_calc = tmp_engine.calculate_partner_commission(
        partner_id="PARTNER-AFS-01",
        software_arr_usd=100000.0,
        hardware_usd=20000.0,
        currency="USD"
    )
    # 100k * 35% = 35k soft, 20k * 35% = 7k hard -> total gross = $42,000.00
    assert esa_calc["gross_software_commission_usd"] == 35000.00
    assert esa_calc["gross_hardware_commission_usd"] == 7000.00
    assert esa_calc["total_gross_commission_usd"] == 42000.00
    assert esa_calc["net_payout_usd"] == 42000.00  # 0% WHT for US W-9

    # 2. CIP Tier (Deloitte UK): $100k soft, $20k hard
    cip_calc = tmp_engine.calculate_partner_commission(
        partner_id="PARTNER-DTT-04",
        software_arr_usd=100000.0,
        hardware_usd=20000.0,
        currency="USD"
    )
    # 100k * 20% = 20k soft, 20k * 0% = 0k hard -> total gross = $20,000.00
    assert cip_calc["gross_software_commission_usd"] == 20000.00
    assert cip_calc["gross_hardware_commission_usd"] == 0.00
    assert cip_calc["total_gross_commission_usd"] == 20000.00


def test_03_us_domestic_partner_withholding_and_1099():
    """Verify US partner with Form W-9 receives 0% backup withholding and Form 1099-NEC."""
    wht = CrossBorderTaxWithholdingAuthority.determine_withholding(
        country_code="US",
        tax_form_status="W-9_VERIFIED",
        has_certified_treaty=True
    )
    assert wht["withholding_rate_pct"] == 0.0
    assert wht["reporting_form"] == "FORM_1099_NEC"
    assert wht["withholding_exempt"] is True
    assert "IRC §3406" in wht["statutory_basis"]


def test_04_india_partner_treaty_withholding_and_1042s(tmp_engine):
    """Verify India partner with Form W-8BEN-E incurs 15% treaty withholding and Form 1042-S."""
    wht = CrossBorderTaxWithholdingAuthority.determine_withholding(
        country_code="IN",
        tax_form_status="W-8BEN-E_CERTIFIED",
        has_certified_treaty=True
    )
    assert wht["withholding_rate_pct"] == 15.0
    assert wht["reporting_form"] == "FORM_1042_S"
    assert "Article 12" in wht["statutory_basis"]

    # Calculate TCS commission in INR: $100,000 software ARR at 28% = $28,000 gross
    # 15% withholding = $4,200. Net = $23,800 USD. In INR @ 86.50 = 2,058,700 INR
    tcs_calc = tmp_engine.calculate_partner_commission(
        partner_id="PARTNER-TCS-02",
        software_arr_usd=100000.0,
        hardware_usd=0.0,
        currency="INR"
    )
    assert tcs_calc["total_gross_commission_usd"] == 28000.00
    assert tcs_calc["tax_withholding"]["withholding_amount_usd"] == 4200.00
    assert tcs_calc["net_payout_usd"] == 23800.00
    assert tcs_calc["currency"] == "INR"
    assert tcs_calc["net_payout_local"] == round(23800.00 * FX_RATES["INR"], 2)
    assert tcs_calc["net_payout_local"] == 2058700.00


def test_05_eu_uk_partner_treaty_exemption():
    """Verify EU and UK partners with W-8BEN-E receive 0% treaty withholding."""
    for c_code in ["DE", "GB", "IE", "FR", "NL"]:
        wht = CrossBorderTaxWithholdingAuthority.determine_withholding(
            country_code=c_code,
            tax_form_status="W-8BEN-E_CERTIFIED",
            has_certified_treaty=True
        )
        assert wht["withholding_rate_pct"] == 0.0
        assert wht["reporting_form"] == "FORM_1042_S"
        assert wht["withholding_exempt"] is True
        assert "Article 7" in wht["statutory_basis"] or "Article 12" in wht["statutory_basis"]


def test_06_non_treaty_missing_w8bene_30pct_statutory_withholding(tmp_engine):
    """Verify non-treaty or missing W-8BEN-E partners incur 30% statutory withholding under IRC §1441."""
    wht = CrossBorderTaxWithholdingAuthority.determine_withholding(
        country_code="SG",
        tax_form_status="MISSING_W8BENE",
        has_certified_treaty=False
    )
    assert wht["withholding_rate_pct"] == 30.0
    assert wht["reporting_form"] == "FORM_1042_S"
    assert wht["withholding_exempt"] is False
    assert "IRC §1441" in wht["statutory_basis"]

    # Calculate NCS SG commission: $50,000 Software at 20% = $10,000 Gross
    # 30% statutory deduction = $3,000 USD. Net USD = $7,000. Net SGD @ 1.34 = 9,380 SGD
    sg_calc = tmp_engine.calculate_partner_commission(
        partner_id="PARTNER-NCS-05",
        software_arr_usd=50000.0,
        hardware_usd=0.0,
        currency="SGD"
    )
    assert sg_calc["total_gross_commission_usd"] == 10000.00
    assert sg_calc["tax_withholding"]["withholding_amount_usd"] == 3000.00
    assert sg_calc["net_payout_usd"] == 7000.00
    assert sg_calc["net_payout_local"] == round(7000.00 * 1.34, 2)
    assert sg_calc["net_payout_local"] == 9380.00


def test_07_120_day_exclusive_deal_lock_attribution(tmp_engine):
    """Verify 120-day exclusive deal registration lock attribution."""
    res = tmp_engine.lock_deal_registration(
        partner_id="PARTNER-AFS-01",
        prospect_organization="Boeing Defense Systems",
        software_arr_usd=150000.0,
        hardware_usd=30000.0,
        registration_date="2026-11-01"
    )

    assert res["registered"] is True
    assert res["reason_code"] == "DEAL_REGISTRATION_LOCKED"
    deal = res["deal"]
    assert deal["prospect_organization"] == "Boeing Defense Systems"
    assert deal["registration_date"] == "2026-11-01"
    assert deal["lock_expiration_date"] == "2027-03-01"  # 120 days from Nov 1
    assert deal["status"] == "LOCKED_EXCLUSIVE"


def test_08_deal_registration_collision_prevention(tmp_engine):
    """Verify collision prevention blocks duplicate registration of locked prospects."""
    # Register under AFS
    tmp_engine.lock_deal_registration(
        partner_id="PARTNER-AFS-01",
        prospect_organization="Lockheed Space Operations",
        software_arr_usd=100000.0,
        registration_date="2026-11-01"
    )

    # Attempt collision under TCS within lock window
    collision_res = tmp_engine.lock_deal_registration(
        partner_id="PARTNER-TCS-02",
        prospect_organization="Lockheed Space Operations",
        software_arr_usd=100000.0,
        registration_date="2026-11-15"
    )

    assert collision_res["registered"] is False
    assert collision_res["reason_code"] == "DEAL_REGISTRATION_COLLISION_REJECTED"
    assert "Channel Collision Detected" in collision_res["message"]
    assert collision_res["existing_partner_id"] == "PARTNER-AFS-01"


def test_09_cash_collection_milestone_matching(tmp_engine):
    """Verify payout is released only upon verified cash settlement."""
    deal_res = tmp_engine.lock_deal_registration(
        partner_id="PARTNER-CAP-03",
        prospect_organization="Airbus Cyber Command",
        software_arr_usd=90000.0,
        hardware_usd=10000.0,
        registration_date="2026-10-01"
    )
    deal_id = deal_res["deal"]["deal_id"]

    # Process cash settlement milestone
    settle_res = tmp_engine.process_cash_settlement_and_payout(
        deal_id=deal_id,
        settlement_date="2026-11-08"
    )

    assert settle_res["settlement_status"] == "CASH_SETTLED"
    assert settle_res["deal_id"] == deal_id
    token = settle_res["payout_token"]
    assert token["payout_token_id"].startswith("PAYOUT-PARTNER-")
    assert token["net_payout_usd"] > 0
    assert CryptographicPartnerPayoutAuthority.verify_payout_token(token) is True


def test_10_cryptographic_partner_payout_token_issuance_and_verification():
    """Verify cryptographic HMAC-SHA256 partner payout token authenticity and tamper detection."""
    token = CryptographicPartnerPayoutAuthority.issue_payout_token(
        partner_id="PARTNER-TEST-99",
        deal_id="DEAL-LOCK-TEST",
        gross_commission_usd=25000.0,
        withholding_tax_usd=3750.0,
        net_payout_usd=21250.0,
        currency="USD",
        net_payout_local=21250.0,
        reporting_form="FORM_1042_S",
        issued_at="2026-11-08T12:00:00Z"
    )

    assert token["payout_token_id"].startswith("PAYOUT-PARTNER-")
    assert len(token["signature"]) == 64
    assert CryptographicPartnerPayoutAuthority.verify_payout_token(token) is True

    # Tampered net payout
    tampered_payout = dict(token)
    tampered_payout["net_payout_usd"] = 99999.0
    assert CryptographicPartnerPayoutAuthority.verify_payout_token(tampered_payout) is False

    # Tampered partner ID
    tampered_partner = dict(token)
    tampered_partner["partner_id"] = "PARTNER-ATTACKER-00"
    assert CryptographicPartnerPayoutAuthority.verify_payout_token(tampered_partner) is False


def test_11_multi_currency_and_indian_upi_neft_rail(tmp_engine):
    """Verify Indian SI partner banking coordinates and domestic UPI/NEFT rails."""
    tcs = tmp_engine.find_partner("PARTNER-TCS-02")
    assert tcs["currency"] == "INR"
    assert tcs["payout_rail"] == "DIRECT_DOMESTIC_UPI_NEFT"
    coords = tcs["banking_coordinates"]
    assert "SBIN" in coords["ifsc_code"]
    assert "icici" in coords["upi_vpa"]


def test_12_commission_binder_export_and_sha256_digest(tmp_engine):
    """Verify exporting institutional Partner Commission Binder with SHA-256 digest."""
    binder = tmp_engine.export_commission_binder()

    assert binder["title"] == "DevSuperSuite Official Enterprise Partner Commission Binder"
    assert "export_timestamp" in binder
    assert "summary_metrics" in binder
    assert len(binder["cryptographic_manifest_sha256"]) == 64
    assert len(binder["partners"]) >= 5
    assert len(binder["deals"]) >= 5


def test_13_executive_markdown_report_generation(tmp_engine):
    """Verify executive markdown report generation with complete audit tables."""
    rep_file = tmp_engine.render_markdown_report()
    assert os.path.exists(rep_file)

    with open(rep_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "# ⚡ DevSuperSuite Official: Enterprise Partner Revenue Share & Commission Report" in content
    assert "alliances@devsupersuite.com" in content
    assert "Accenture Federal Services LLC" in content
    assert "Tata Consultancy Services SI" in content
    assert "120-Day Deal Registration Locks Ledger" in content
    assert "Cryptographic Partner Payout Tokens" in content


def test_14_strict_brand_anonymity_protocol():
    """Verify zero occurrences of personal founder identifiers across service, tests, and reports."""
    founder_tokens = [
        bytes.fromhex("41746861727661").decode("utf-8").lower(),
        bytes.fromhex("506164687965").decode("utf-8").lower()
    ]

    target_files = [
        os.path.join(SERVICES_DIR, "enterprise_partner_revshare_commission_engine.py"),
        os.path.join(TESTS_DIR, "test_partner_revshare_commission.py"),
        PRIMARY_SCHEDULE_PATH,
        ROOT_SCHEDULE_PATH,
        REPORT_PATH
    ]

    for fpath in target_files:
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().lower()
                for token in founder_tokens:
                    assert token not in content, f"Brand Anonymity violation: found '{token}' in {fpath}"
