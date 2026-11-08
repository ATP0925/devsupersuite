"""
⚡ DevSuperSuite Global Treasury Desk - Corporate Capital Allocation Pytest Suite
File: test_treasury_capital_allocation.py
Version: 1.0.0
Author: DevSuperSuite Global Treasury Desk
Strict Compliance: 100% Brand Anonymity Protocol (treasury@devsupersuite.com).
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
sys.path.insert(0, SERVICES_DIR)

from services.enterprise_treasury_capital_allocation_engine import (
    EnterpriseTreasuryCapitalAllocationEngine,
    BASELINE_CAPITAL_POOL,
    SOVEREIGN_TBILL_APY,
    TARGET_TIER1_OPERATING_USD,
    TARGET_LCR_THRESHOLD_PCT,
    TARGET_NSFR_THRESHOLD_PCT,
    HURDLE_RATE_PCT,
    RAROC_INITIATIVES,
    DEFAULT_TREASURY_SCHEDULE_FILE,
    ROOT_TREASURY_SCHEDULE_FILE,
    DEFAULT_TREASURY_REPORT_FILE,
)


@pytest.fixture
def engine():
    return EnterpriseTreasuryCapitalAllocationEngine()


def test_01_multi_tier_capital_allocation_balances(engine):
    """Verifies Three-Tier Capital Allocation amounts, percentages, and total capital balance."""
    alloc = engine.audit_treasury_allocations()
    assert alloc["total_capital_usd"] == 650000.00
    assert alloc["tier1_operating_cash"]["total_tier1_usd"] == 72175.00
    assert alloc["tier2_sovereign_yield_reserve"]["total_tier2_usd"] == 350000.00
    assert alloc["tier3_strategic_defense_reserve"]["total_tier3_usd"] == 227825.00
    assert alloc["tier1_operating_cash"]["allocation_pct"] == 11.10
    assert alloc["tier2_sovereign_yield_reserve"]["allocation_pct"] == 53.85
    assert alloc["tier3_strategic_defense_reserve"]["allocation_pct"] == 35.05


def test_02_sovereign_yield_reserve_interest_generation(engine):
    """Verifies 5.15% APY yield generation on Tier 2 short-term US Treasury Bills."""
    alloc = engine.audit_treasury_allocations()
    t2 = alloc["tier2_sovereign_yield_reserve"]
    expected_yield = round(350000.00 * SOVEREIGN_TBILL_APY, 2)
    assert t2["annualized_interest_income_usd"] == expected_yield
    assert t2["annualized_interest_income_usd"] == 18025.00
    assert t2["us_tbill_4w_usd"] == 175000.00
    assert t2["us_tbill_13w_usd"] == 175000.00


def test_03_basel_iii_liquidity_coverage_ratio(engine):
    """Asserts Liquidity Coverage Ratio (LCR) exceeds the 140.0% policy threshold."""
    alloc = engine.audit_treasury_allocations()
    b3 = alloc["basel_iii_metrics"]
    assert b3["hqla_usd"] == 422175.00
    assert b3["lcr_ratio_pct"] >= TARGET_LCR_THRESHOLD_PCT
    assert b3["lcr_ratio_pct"] == 281.45
    assert b3["lcr_compliant"] is True


def test_04_basel_iii_net_stable_funding_ratio(engine):
    """Asserts Net Stable Funding Ratio (NSFR) exceeds the 120.0% institutional benchmark."""
    alloc = engine.audit_treasury_allocations()
    b3 = alloc["basel_iii_metrics"]
    assert b3["asf_usd"] == 650000.00
    assert b3["rsf_usd"] == 220000.00
    assert b3["nsfr_ratio_pct"] >= TARGET_NSFR_THRESHOLD_PCT
    assert b3["nsfr_ratio_pct"] == 295.45
    assert b3["nsfr_compliant"] is True


def test_05_raroc_initiatives_hurdle_rate_evaluation(engine):
    """Verifies all strategic capital initiatives exceed the 20.00% RAROC hurdle rate."""
    raroc = engine.evaluate_raroc_capital_budgeting()
    inits = raroc["initiatives"]
    assert len(inits) == 3

    # SCIF Hardware Run
    scif = inits["SCIF_HARDWARE_INVENTORY_RUN"]
    assert scif["raroc_pct"] == 55.00
    assert scif["status"] == "APPROVED"

    # AI Core R&D
    ai_rd = inits["PROPRIETARY_AI_CORE_RD"]
    assert ai_rd["raroc_pct"] == 56.00
    assert ai_rd["status"] == "APPROVED"

    # Channel Partner Alliance
    mdf = inits["GLOBAL_CHANNEL_ALLIANCE_MDF"]
    assert mdf["raroc_pct"] == 35.00
    assert mdf["status"] == "APPROVED"


def test_06_economic_value_added_portfolio_eva(engine):
    """Verifies Economic Value Added (EVA) calculation across portfolio initiatives."""
    raroc = engine.evaluate_raroc_capital_budgeting()
    psum = raroc["portfolio_summary"]
    assert psum["total_economic_capital_usd"] == 225000.00
    assert psum["total_risk_adjusted_return_usd"] == 114500.00
    assert psum["portfolio_raroc_pct"] == 50.89
    assert psum["portfolio_eva_usd"] == 69502.50
    assert psum["all_approved"] is True


def test_07_stress_scenario_arr_contraction(engine):
    """Simulates 40% ARR contraction, ensuring cash runway exceeds 36 months without dilution."""
    stress = engine.simulate_liquidity_stress()
    sc_a = stress["scenarios"]["scenario_a_arr_contraction"]
    assert sc_a["arr_drop_pct"] == 40.00
    assert sc_a["net_monthly_operating_cashflow_usd"] > 0
    assert sc_a["stressed_runway_months"] >= 60.0
    assert sc_a["capital_dilution_required"] is False


def test_08_stress_scenario_banking_freeze(engine):
    """Simulates 90-day banking freeze, verifying EMEA and APAC regional solvency."""
    stress = engine.simulate_liquidity_stress()
    sc_b = stress["scenarios"]["scenario_b_banking_freeze"]
    assert sc_b["freeze_duration_days"] == 90
    assert sc_b["ireland_surplus_eur"] > 0
    assert sc_b["ireland_solvency_passed"] is True
    assert sc_b["singapore_surplus_sgd"] > 0
    assert sc_b["singapore_solvency_passed"] is True
    assert sc_b["custodial_bankruptcy_remote_t_bills_usd"] == 350000.00
    assert sc_b["counterparty_default_loss_usd"] == 0.00


def test_09_stress_scenario_fx_volatility_hedging(engine):
    """Simulates +15% USD rally, verifying 80% FX forward hedge protection and minimal net drag."""
    stress = engine.simulate_liquidity_stress()
    sc_c = stress["scenarios"]["scenario_c_fx_volatility"]
    assert sc_c["usd_appreciation_pct"] == 15.00
    assert sc_c["gross_fx_translation_drag_usd"] == 2892.50
    assert sc_c["forward_hedging_offset_usd"] == 2314.00
    assert sc_c["net_unhedged_fx_impact_usd"] == 578.50
    assert sc_c["impact_on_total_capital_pct"] < 0.10


def test_10_treasury_rebalance_mechanics(engine):
    """Verifies calculation of excess Tier 1 operating cash and sweep recommendation."""
    reb = engine.rebalance_treasury_reserves()
    assert reb["rebalance_required"] is True
    assert reb["tier1_current_usd"] == 72175.00
    assert reb["tier1_target_usd"] == TARGET_TIER1_OPERATING_USD
    assert reb["excess_working_capital_usd"] == 22175.00
    assert len(reb["rebalance_actions"]) >= 1
    assert reb["rebalance_actions"][0]["action"] == "SWEEP_TIER1_TO_TIER2"
    assert reb["rebalance_actions"][0]["amount_usd"] == 22175.00


def test_11_cli_interface_all_flags():
    """Verifies that all CLI flags execute with exit code 0."""
    script_path = os.path.join(SERVICES_DIR, "enterprise_treasury_capital_allocation_engine.py")
    cli_flags = [
        "--audit-treasury-allocations",
        "--simulate-liquidity-stress",
        "--rebalance-reserves",
        "--export-treasury-binder",
        "--summary"
    ]

    for flag in cli_flags:
        res = subprocess.run(
            [sys.executable, script_path, flag],
            capture_output=True,
            text=True
        )
        assert res.returncode == 0, f"CLI flag {flag} failed: {res.stderr}"
        assert len(res.stdout.strip()) > 0


def test_12_brand_anonymity_strict_compliance():
    """Verifies 100% Brand Anonymity: zero occurrences of forbidden founder tokens."""
    forbidden_tokens = [
        "".join(["P", "r", "a", "t", "i", "k"]),
        "".join(["p", "r", "a", "t", "i", "k"]),
        "".join(["a", "t", "p", "a", "d"]),
        "".join(["a", "t", "p", "a", "d", "k", "a", "r"]),
        "".join(["g", "m", "a", "i", "l", ".", "c", "o", "m"]),
        "".join(["+", "9", "1", "9"]),
        "".join(["+", "9", "1", " ", "9"]),
    ]
    target_files = [
        os.path.join(SERVICES_DIR, "enterprise_treasury_capital_allocation_engine.py"),
        DEFAULT_TREASURY_SCHEDULE_FILE,
        ROOT_TREASURY_SCHEDULE_FILE,
        DEFAULT_TREASURY_REPORT_FILE,
    ]

    for fpath in target_files:
        assert os.path.exists(fpath), f"File {fpath} must exist for anonymity check"
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            for token in forbidden_tokens:
                assert token not in content, f"Forbidden brand anonymity token '{token}' discovered in {fpath}"
