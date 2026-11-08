"""
⚡ DevSuperSuite Treasury & Corporate Finance - Unit & Integration Test Suite
File: test_captable_secondary_liquidity.py
Phase: 26 - Enterprise Cap Table Waterfall & Secondary Liquidity Engine
Author: DevSuperSuite Treasury & Corporate Finance
Strict Compliance: 100% Brand Anonymity - DevSuperSuite Treasury & Corporate Finance Only (cfo@devsupersuite.com).
"""

import os
import sys
import json
import subprocess
import pytest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(PROJECT_ROOT, "services")
DATA_DIR = os.path.join(SERVICES_DIR, "data")
ROOT_DATA_DIR = os.path.join(PROJECT_ROOT, "data")
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")

sys.path.insert(0, PROJECT_ROOT)

from services.enterprise_captable_secondary_liquidity_engine import (
    EnterpriseCapTableSecondaryLiquidityEngine,
    INITIAL_FOUNDER_SHARES,
    POST_MONEY_OPTION_POOL_PCT,
    SAFE_TERMS,
    SERIES_A_TERMS,
    DEFAULT_CAPTABLE_SCHEDULE_FILE,
    ROOT_CAPTABLE_SCHEDULE_FILE,
    DEFAULT_LIQUIDITY_BINDER_FILE
)

FORBIDDEN_FOUNDER_TOKENS = [
    "Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"
]


@pytest.fixture
def engine():
    return EnterpriseCapTableSecondaryLiquidityEngine()


def test_01_captable_fully_diluted_architecture(engine):
    """Verifies fully diluted share count, post-money valuation, and stakeholder equity percentages."""
    audit = engine.audit_captable_waterfall()

    assert audit["total_fully_diluted_shares"] > 10000000, "Fully diluted shares should exceed 10M"
    assert audit["series_a_share_price_usd"] > 0.0
    assert audit["post_money_valuation_usd"] >= 30000000.0, "Post-money valuation should be at least $30M"

    stakeholders = {s["name"]: s for s in audit["stakeholders"]}

    # Option Pool target verification (15.0%)
    esop = stakeholders["Unallocated Employee Option Pool (ESOP)"]
    assert esop["economic_ownership_pct"] == 15.00

    # Series A Preferred target verification (~16.67%)
    series_a = stakeholders["Lead Series A Institutional Investor"]
    assert 16.0 <= series_a["economic_ownership_pct"] <= 17.0

    # SAFE Note target verification (~6.83%)
    safe = stakeholders["Seed SAFE Note Investors"]
    assert 6.0 <= safe["economic_ownership_pct"] <= 7.5

    # Founder Common target verification (~61.5%)
    founders = stakeholders["Founding Operating Partners"]
    assert 60.0 <= founders["economic_ownership_pct"] <= 63.0


def test_02_founder_control_and_supermajority(engine):
    """Verifies dual-class voting architecture guarantees >75% voting supermajority."""
    audit = engine.audit_captable_waterfall()

    founder_voting_pct = audit["founder_voting_supermajority_pct"]
    assert founder_voting_pct >= 75.0, f"Founder voting power must be >= 75%, got {founder_voting_pct}%"
    assert founder_voting_pct >= 90.0, "With Class B 10:1 voting, founder control should exceed 90%"
    assert audit["supermajority_invariants_satisfied"] is True

    # Check voting votes math
    stakeholders = {s["name"]: s for s in audit["stakeholders"]}
    founders = stakeholders["Founding Operating Partners"]
    assert founders["voting_power_votes"] == founders["share_count"] * 10


def test_03_liquidation_waterfall_preferences(engine):
    """Verifies 1.0x non-participating pari-passu liquidation preference and crossover conversion."""
    audit = engine.audit_captable_waterfall()

    assert audit["total_senior_liquidation_preference_usd"] == 7000000.0
    assert audit["preferred_common_crossover_valuation_usd"] == 30000000.0

    scenarios = {w["exit_valuation_usd"]: w for w in audit["liquidation_waterfall_scenarios"]}

    # $5M distressed exit: Preferred recovers pro-rata; Common gets $0
    scen_5m = scenarios[5000000.0]
    assert scen_5m["founder_payout_usd"] == 0.0
    assert scen_5m["safe_investor_payout_usd"] > 0.0
    assert scen_5m["series_a_payout_usd"] > 0.0
    assert scen_5m["safe_moic"] < 1.0
    assert scen_5m["series_a_moic"] < 1.0

    # $10M exit: Preferred takes full $7M preference; Common takes $3M remainder
    scen_10m = scenarios[10000000.0]
    assert scen_10m["safe_investor_payout_usd"] == 2000000.0
    assert scen_10m["series_a_payout_usd"] == 5000000.0
    assert scen_10m["safe_moic"] == 1.0
    assert scen_10m["series_a_moic"] == 1.0
    assert scen_10m["founder_payout_usd"] > 2000000.0

    # $50M & $100M exits: Preferred converts to Common; MOICs expand
    scen_50m = scenarios[50000000.0]
    assert scen_50m["waterfall_distribution_mode"] == "FULL_COMMON_CONVERSION_EQUAL_PRO_RATA"
    assert scen_50m["founder_payout_usd"] > 30000000.0
    assert scen_50m["safe_moic"] >= 1.70
    assert scen_50m["series_a_moic"] >= 1.65

    scen_100m = scenarios[100000000.0]
    assert scen_100m["founder_payout_usd"] > 60000000.0
    assert scen_100m["safe_moic"] >= 3.40
    assert scen_100m["series_a_moic"] >= 3.30


def test_04_secondary_tender_qsbs_tax_efficiency(engine):
    """Verifies secondary tender offer model and IRC Section 1202 100% QSBS capital gains exemption."""
    tender = engine.simulate_secondary_tender()

    assert tender["qsbs_statutory_basis"] == "IRC Section 1202 (100% Capital Gains Exclusion up to $10M)"
    assert tender["section_1042_rollover_eligible"] is True
    assert len(tender["tender_scenarios"]) == 3

    for t in tender["tender_scenarios"]:
        assert t["qsbs_sec_1202_tax_liability_usd"] == 0.0
        assert t["qsbs_sec_1202_net_after_tax_proceeds_usd"] == t["founder_gross_proceeds_usd"]
        assert t["qsbs_tax_savings_usd"] == t["standard_ltcg_tax_liability_usd"]
        assert t["qsbs_exemption_pct"] == 100.0
        assert t["founder_retained_equity_pct"] > 30.0

    # Verify specific tax savings amounts
    savings_2m = tender["tender_scenarios"][0]["qsbs_tax_savings_usd"]
    savings_5m = tender["tender_scenarios"][1]["qsbs_tax_savings_usd"]
    savings_10m = tender["tender_scenarios"][2]["qsbs_tax_savings_usd"]
    assert savings_2m == 380800.0
    assert savings_5m == 952000.0
    assert savings_10m == 1904000.0


def test_05_arr_debt_vs_equity_decision(engine):
    """Verifies non-dilutive ARR debt facility preserves tens of millions in founder equity wealth."""
    comp = engine.compare_arr_debt_vs_equity(capital_needed_usd=3000000.0)

    assert comp["strategic_verdict"] == "ARR_DEBT_STRONGLY_FAVORED"
    debt = comp["debt_facility"]
    equity = comp["equity_financing"]

    assert debt["equity_dilution_pct"] == 0.0
    assert debt["interest_rate_pct"] == 8.5
    assert debt["total_interest_cost_usd"] == 765000.0
    assert equity["equity_dilution_pct"] == 20.0

    exits = {e["future_exit_valuation_usd"]: e for e in comp["exit_wealth_preservation"]}
    assert exits[50000000.0]["net_founder_wealth_preserved_usd"] == 9235000.0
    assert exits[100000000.0]["net_founder_wealth_preserved_usd"] == 19235000.0


def test_06_artifact_export_and_json_persistence(engine):
    """Verifies persistence of cap table schedule JSON and Markdown liquidity binder."""
    paths = engine.export_all_artifacts()

    for key, path in paths.items():
        assert os.path.exists(path), f"File {path} was not created"

    # Verify JSON schedule
    with open(paths["schedule_path"], "r", encoding="utf-8") as f:
        schedule = json.load(f)
    assert schedule["metadata"]["reporting_entity"] == "DevSuperSuite Tech Services"
    assert "captable_audit" in schedule
    assert "secondary_tender" in schedule
    assert "debt_vs_equity_comparison" in schedule

    # Verify Markdown binder
    with open(paths["binder_path"], "r", encoding="utf-8") as f:
        binder_md = f.read()
    assert "ENTERPRISE CAP TABLE WATERFALL & SECONDARY LIQUIDITY BINDER" in binder_md
    assert "IRC Section 1202" in binder_md
    assert "Dual-Class Voting Structure" in binder_md


def test_07_cli_command_executions():
    """Verifies CLI flags execute cleanly."""
    script_path = os.path.join(SERVICES_DIR, "enterprise_captable_secondary_liquidity_engine.py")

    cmd = [
        sys.executable,
        script_path,
        "--audit-captable-waterfall",
        "--simulate-secondary-tender",
        "--compare-arr-debt-vs-equity",
        "--export-liquidity-binder",
        "--summary"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"CLI failed: {res.stderr}"
    assert "Fully Diluted Cap Table Architecture" in res.stdout
    assert "Secondary Liquidity Tender Offer" in res.stdout
    assert "Non-Dilutive ARR Debt vs Venture Equity" in res.stdout


def test_08_strict_brand_anonymity():
    """Verifies 100% Brand Anonymity across all Phase 26 files."""
    files_to_check = [
        os.path.join(SERVICES_DIR, "enterprise_captable_secondary_liquidity_engine.py"),
        os.path.join(REPORTS_DIR, "captable_secondary_liquidity_binder.md"),
        os.path.join(DATA_DIR, "captable_liquidity_schedule.json"),
        os.path.join(ROOT_DATA_DIR, "captable_liquidity_schedule.json")
    ]

    for file_path in files_to_check:
        assert os.path.exists(file_path), f"File {file_path} must exist for anonymity check"
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().lower()
        for token in FORBIDDEN_FOUNDER_TOKENS:
            assert token.lower() not in content, (
                f"Forbidden founder token '{token}' detected in {file_path}!"
            )
