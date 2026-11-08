"""
⚡ DevSuperSuite Global Treasury Desk - Secondary Cap Table Liquidity & Buyback Tender Test Suite
File: test_equity_liquidity_tender.py
Target: enterprise_equity_liquidity_tender_engine.py
Strict Compliance: 100% Brand Anonymity - DevSuperSuite Global Treasury Desk Only (treasury@devsupersuite.com).
"""

import os
import sys
import json
import subprocess
import pytest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(PROJECT_ROOT, "services")
sys.path.insert(0, SERVICES_DIR)

from enterprise_equity_liquidity_tender_engine import (
    EnterpriseEquityLiquidityTenderEngine,
    CAPITALIZATION_BASELINE,
    ANNUAL_RUN_RATE_ARR_USD,
    COMPANY_TENDER_BUYBACK_BUDGET_USD,
    TENDER_SHARE_PRICE_USD,
    CORPORATE_ENTITY_NAME,
    TREASURY_DESK_TITLE,
    TREASURY_OFFICIAL_EMAIL,
    DEFAULT_TENDER_SCHEDULE_FILE,
    ROOT_TENDER_SCHEDULE_FILE,
    DEFAULT_TENDER_REPORT_FILE
)


@pytest.fixture
def tender_engine():
    """Initializes the institutional secondary equity liquidity & tender engine."""
    return EnterpriseEquityLiquidityTenderEngine()


def test_01_cap_table_capitalization_waterfall(tender_engine):
    """Verifies fully diluted share count of 13,821,138 shares across all 5 share classes."""
    audit = tender_engine.audit_cap_table()
    assert audit["total_authorized_and_outstanding_shares"] == 13821138
    assert audit["corporate_entity"] == CORPORATE_ENTITY_NAME

    classes = audit["share_classes"]
    assert classes["FOUNDER_COMMON_CLASS_B"]["shares"] == 8500000
    assert classes["EMPLOYEE_COMMON_CLASS_A"]["shares"] == 500000
    assert classes["UNALLOCATED_ESOP_POOL"]["shares"] == 2073171
    assert classes["POST_MONEY_SAFE_NOTE"]["shares"] == 1382114
    assert classes["SERIES_A_PREFERRED"]["shares"] == 1365853

    # Check ownership percentages
    assert classes["FOUNDER_COMMON_CLASS_B"]["ownership_pct"] == 61.50
    assert classes["UNALLOCATED_ESOP_POOL"]["ownership_pct"] == 15.00


def test_02_founder_dual_class_voting_supermajority(tender_engine):
    """Verifies Class B 10 votes/share locks >90% founder voting control (96.32%), preserving supermajority."""
    audit = tender_engine.audit_cap_table()
    assert audit["founder_voting_power_pct"] == 96.32
    assert audit["supermajority_control_preserved"] is True
    assert audit["share_classes"]["FOUNDER_COMMON_CLASS_B"]["votes_per_share"] == 10


def test_03_arr_multiple_valuations(tender_engine):
    """Verifies enterprise ARR multiples at 18x, 21x, and 24x on $558,992.16 ARR baseline."""
    val = tender_engine.calculate_valuation_multiples()
    arr = val["arr_run_rate_baseline_usd"]
    assert arr == 558992.16

    multiples = val["arr_multiple_valuations"]
    assert multiples["conservative_18x"]["enterprise_value_usd"] == 10061858.88
    assert multiples["baseline_21x"]["enterprise_value_usd"] == 11738835.36
    assert multiples["premium_saas_24x"]["enterprise_value_usd"] == 13415811.84


def test_04_dcf_5year_valuation_model(tender_engine):
    """Verifies 5-year DCF valuation projections (45% CAGR, 35% FCF margin, 12% WACC)."""
    val = tender_engine.calculate_valuation_multiples()
    dcf = val["dcf_model"]

    assert dcf["wacc_discount_rate_pct"] == 12.00
    assert dcf["terminal_growth_rate_pct"] == 3.50
    assert dcf["dcf_enterprise_value_usd"] > 10000000.00
    assert len(dcf["fcf_projections"]) == 5
    assert val["blended_fair_market_value_usd"] > 11000000.00


def test_05_dgcl_160_solvency_and_no_impairment(tender_engine):
    """Verifies statutory compliance with Delaware General Corporation Law § 160 (no capital impairment)."""
    solv = tender_engine.verify_dgcl_160_solvency()
    
    assert solv["compliance_status"] == "CERTIFIED_SURPLUS_AVAILABLE"
    assert solv["capital_impairment_test"] == "PASSED"
    assert solv["treasury_cash_and_surplus_usd"] > solv["share_repurchase_budget_usd"]
    assert solv["senior_debt_liabilities_usd"] == 0.00
    assert solv["current_ratio"] > 15.0


def test_06_tender_offer_share_repurchase_mechanics(tender_engine):
    """Verifies $500k buyback budget at $0.85/share buys exactly 588,235 shares."""
    tender = tender_engine.simulate_tender_offer()
    
    assert tender["tender_share_price_usd"] == 0.85
    assert tender["shares_repurchased_count"] == 588235
    assert tender["total_buyback_capital_deployed_usd"] == 499999.75
    assert tender["share_cancellation_status"] == "RETIRED_TO_AUTHORIZED_UNISSUED_TREASURY_STOCK"


def test_07_post_tender_share_count_and_eps_accretion(tender_engine):
    """Verifies post-tender share count is 13,232,903 and per-share EPS accretion is +4.45%."""
    tender = tender_engine.simulate_tender_offer()
    
    assert tender["total_shares_pre_tender"] == 13821138
    assert tender["total_shares_post_tender"] == 13232903
    assert tender["founder_ownership_post_pct"] == 64.23
    assert tender["founder_ownership_accretion_pct"] == 2.73
    assert tender["per_share_earnings_accretion_pct"] == 4.45


def test_08_rofr_and_cosale_covenants(tender_engine):
    """Verifies Right of First Refusal (ROFR) 30-day corporate window and co-sale tag-along provisions."""
    rofr = tender_engine.verify_rofr_and_cosale_compliance()
    
    assert rofr["transfer_notice_period_days"] == 30
    assert rofr["primary_exercise_window_days"] == 30
    assert rofr["secondary_exercise_window_days"] == 15
    assert rofr["rofr_status"] == "COMPANY_EXERCISED_PRIMARY_OPTION"
    assert "Series A" in rofr["secondary_rofr_holder"]


def test_09_sec_rule_506c_accreditation_compliance(tender_engine):
    """Verifies SEC Rule 506(c) verification and Rule 506(d) bad actor clearance."""
    rofr = tender_engine.verify_rofr_and_cosale_compliance()
    sec = rofr["sec_rule_506c_compliance"]
    
    assert sec["exemption"] == "SEC Rule 506(c) of Regulation D"
    assert sec["general_solicitation_permitted"] is True
    assert "PASSED" in sec["bad_actor_disqualification_check"]


def test_10_tender_schedule_json_persistence(tender_engine):
    """Verifies that the tender schedule JSON is written to services/data/ and mirrored in root data/."""
    paths = tender_engine.export_all()
    
    assert os.path.exists(paths["schedule_file"])
    assert os.path.exists(paths["root_schedule_file"])
    assert os.path.exists(paths["report_file"])

    with open(paths["schedule_file"], "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["binder_id"] == "DSS-EQUITY-TENDER-2026-BINDER"
        assert data["tender_summary"]["tender_share_price_usd"] == 0.85
        assert data["tender_summary"]["shares_repurchased"] == 588235
        assert data["tender_summary"]["post_tender_shares"] == 13232903
        assert "cap_table_audit" in data


def test_11_audit_report_markdown_integrity(tender_engine):
    """Verifies that the markdown report contains executive summaries, tables, and Mermaid flowcharts."""
    paths = tender_engine.export_all()
    
    with open(paths["report_file"], "r", encoding="utf-8") as f:
        md = f.read()
        assert "DevSuperSuite Global Treasury Desk" in md
        assert "Delaware General Corporation Law § 160" in md
        assert "588,235" in md
        assert "$499,999.75" in md
        assert "+4.45%" in md
        assert "flowchart TD" in md


def test_12_cli_interface_execution():
    """Smoke tests all CLI arguments for the equity liquidity tender engine."""
    cli_flags = [
        "--audit-cap-table",
        "--calculate-valuation-multiples",
        "--simulate-tender-offer",
        "--verify-rofr-compliance",
        "--export-tender-binder",
        "--summary"
    ]
    script_path = os.path.join(SERVICES_DIR, "enterprise_equity_liquidity_tender_engine.py")

    for flag in cli_flags:
        res = subprocess.run(
            [sys.executable, script_path, flag],
            capture_output=True,
            text=True
        )
        assert res.returncode == 0, f"CLI flag {flag} failed: {res.stderr}"
        assert len(res.stdout.strip()) > 0


def test_13_brand_anonymity_strict_compliance():
    """Verifies 100% Brand Anonymity Protocol: zero forbidden founder names or private emails."""
    forbidden_tokens = ["Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"]
    target_files = [
        os.path.join(SERVICES_DIR, "enterprise_equity_liquidity_tender_engine.py"),
        DEFAULT_TENDER_SCHEDULE_FILE,
        ROOT_TENDER_SCHEDULE_FILE,
        DEFAULT_TENDER_REPORT_FILE
    ]

    for fpath in target_files:
        assert os.path.exists(fpath), f"File {fpath} must exist for anonymity check"
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            for token in forbidden_tokens:
                assert token not in content, f"Forbidden brand anonymity token '{token}' discovered in {fpath}"
