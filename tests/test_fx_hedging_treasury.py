"""
⚡ DevSuperSuite Treasury & Corporate Finance - Unit & Integration Test Suite
File: test_fx_hedging_treasury.py
Phase: 25 - Enterprise Multi-Currency FX Hedging & Treasury Stress Testing Engine
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

from services.enterprise_fx_hedging_treasury_engine import (
    EnterpriseFXHedgingTreasuryEngine,
    BENCHMARK_SPOT_RATES,
    SOVEREIGN_RISK_FREE_RATES,
    CROSS_BORDER_PORTFOLIO,
    TREASURY_BASE_LIQUIDITY,
    DEFAULT_HEDGING_SCHEDULE_FILE,
    ROOT_HEDGING_SCHEDULE_FILE,
    DEFAULT_STRESS_TEST_REPORT_FILE,
    DEFAULT_INVESTMENT_POLICY_FILE
)

FORBIDDEN_FOUNDER_TOKENS = [
    "Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"
]


@pytest.fixture
def engine():
    return EnterpriseFXHedgingTreasuryEngine()


def test_01_multi_currency_exposure_audit(engine):
    """Verifies cross-border currency exposures across USD, EUR, GBP, INR, JPY, and SGD."""
    audit = engine.audit_fx_exposure()

    assert audit["total_portfolio_arr_usd"] > 550000.0, "Portfolio ARR should exceed $550k"
    assert audit["functional_currency"] == "USD"
    assert audit["foreign_exposed_share_pct"] > 15.0, "Foreign currency exposure should be > 15% of ARR"

    currencies = {exp["currency"] for exp in audit["currency_exposures"]}
    expected_currencies = {"USD", "EUR", "GBP", "INR", "JPY", "SGD"}
    assert expected_currencies.issubset(currencies), f"Missing currencies: {expected_currencies - currencies}"

    usd_exp = next(e for e in audit["currency_exposures"] if e["currency"] == "USD")
    assert usd_exp["classification"] == "BASE_FUNCTIONAL_CURRENCY"
    assert usd_exp["hedging_target_pct"] == 0.0

    inr_exp = next(e for e in audit["currency_exposures"] if e["currency"] == "INR")
    assert inr_exp["annual_local_opex_local"] > 0, "INR local opex natural match must be accounted for"
    assert inr_exp["net_exposed_usd"] < inr_exp["annual_gross_inflow_usd"]


def test_02_delta_hedging_ratios_and_synthetic_collars(engine):
    """Verifies forward contract pricing and synthetic zero-cost collar boundaries."""
    hedges = engine.calculate_hedging_ratios(tenor_days=90)

    assert hedges["overall_foreign_hedge_ratio_pct"] >= 75.0, "Overall hedge ratio must be >= 75%"
    assert hedges["overall_foreign_hedge_ratio_pct"] <= 85.0
    assert hedges["total_foreign_hedged_notional_usd"] > 80000.0

    for pos in hedges["positions"]:
        assert pos["currency"] in {"EUR", "GBP", "INR", "JPY", "SGD"}
        assert pos["forward_rate"] > 0
        collar = pos["synthetic_collar"]
        spot = pos["spot_rate"]
        # Protective put floor strictly below spot (95%)
        assert collar["protective_put_floor"] < spot
        # Covered call ceiling strictly above spot (105.5%)
        assert collar["covered_call_ceiling"] > spot
        assert collar["net_option_premium"] == "ZERO_COST_SYNTHETIC_COLLAR"


def test_03_value_at_risk_unhedged_vs_hedged(engine):
    """Verifies 99% 10-day VaR calculation and significant downside risk reduction."""
    var_data = engine.calculate_var(horizon_days=10, confidence_level=0.99)

    assert var_data["confidence_level_pct"] == 99.0
    assert var_data["z_critical_value"] == 2.3263
    assert var_data["total_unhedged_portfolio_var_usd"] > var_data["total_hedged_portfolio_var_usd"]
    assert var_data["portfolio_risk_reduction_pct"] >= 60.0, "Dynamic hedging must achieve >= 60% VaR reduction"

    for v in var_data["currency_var_breakdown"]:
        assert v["unhedged_var_99_usd"] > v["hedged_var_99_usd"]
        assert v["risk_reduction_pct"] > 0


def test_04_macroeconomic_stress_test_scenarios(engine):
    """Verifies the 3 extreme macroeconomic liquidity stress test scenarios."""
    stress = engine.run_treasury_stress_test()
    assert stress["overall_stress_test_passed"] is True

    scenarios = {s["scenario_name"]: s for s in stress["scenarios"]}

    # Scenario 1: Bank Default & Liquidity Crunch
    scen1 = scenarios["SCENARIO_1_GLOBAL_LIQUIDITY_CRUNCH_AND_BANK_DEFAULT"]
    assert scen1["solvency_verdict"] == "SOLVENT_PASS"
    assert scen1["sovereign_tbill_impairment_pct"] == 0.0
    assert scen1["post_stress_available_liquidity_usd"] >= 45000.0
    assert scen1["post_stress_operating_runway_months"] >= 25.0

    # Scenario 2: Emerging Market FX Crash
    scen2 = scenarios["SCENARIO_2_EMERGING_MARKET_FX_CRASH"]
    assert scen2["solvency_verdict"] == "SOLVENT_PASS"
    assert scen2["hedge_deflection_efficiency_pct"] >= 78.0, "Collars must absorb >= 78% of EM shock"
    assert scen2["ebitda_margin_impact_pct"] < 1.0, "Net ARR EBITDA margin impact must be < 1.0%"

    # Scenario 3: Fed Rate Shock (+/- 250 bps)
    scen3 = scenarios["SCENARIO_3_FEDERAL_RESERVE_RATE_SHOCK_250_BPS"]
    assert scen3["solvency_verdict"] == "SOLVENT_PASS"
    assert scen3["weighted_average_duration_years"] < 0.35, "Duration must be ultra-low (< 0.35 years)"
    assert scen3["hike_shock_plus_250_bps"]["reinvestment_annual_yield_usd"] > 4500.0


def test_05_sovereign_tbill_ladder_and_runway(engine):
    """Verifies Sovereign U.S. T-Bill rolling ladder optimizer satisfies all buffer & runway mandates."""
    ladder = engine.optimize_sovereign_tbill_ladder()

    assert ladder["total_liquid_treasury_reserves_usd"] >= 65000.0, "Reserves must satisfy > $65,000 buffer"
    assert ladder["buffer_threshold_satisfied"] is True
    assert ladder["operating_runway_months"] >= 36.0, "Runway must satisfy > 36.0 months mandate"
    assert ladder["runway_threshold_satisfied"] is True
    assert ladder["portfolio_weighted_apy_pct"] >= 4.50, "Weighted APY must exceed 4.50%"
    assert ladder["annualized_accrued_yield_usd"] > 3000.0

    # Tranches verification
    tranches = ladder["tranches"]
    assert len(tranches) == 4
    durations = [t["duration_weeks"] for t in tranches]
    assert 0 in durations  # Overnight / MMF
    assert 4 in durations  # 4-week bill
    assert 13 in durations # 13-week bill
    assert 26 in durations # 26-week bill


def test_06_artifact_export_and_json_persistence(engine):
    """Verifies proper export of JSON schedule, Markdown risk report, and Investment Policy Statement."""
    paths = engine.export_all_artifacts()

    for key, path in paths.items():
        assert os.path.exists(path), f"File {path} was not created"

    # Verify JSON schedule content
    with open(paths["schedule_path"], "r", encoding="utf-8") as f:
        schedule = json.load(f)
    assert schedule["metadata"]["reporting_entity"] == "DevSuperSuite Tech Services"
    assert "fx_audit" in schedule
    assert "hedging_positions" in schedule
    assert "stress_tests" in schedule

    # Verify Markdown report content
    with open(paths["report_path"], "r", encoding="utf-8") as f:
        report_md = f.read()
    assert "ENTERPRISE MULTI-CURRENCY FX HEDGING & TREASURY STRESS TESTING REPORT" in report_md
    assert "SCENARIO_1_GLOBAL_LIQUIDITY_CRUNCH_AND_BANK_DEFAULT" in report_md
    assert "SOLVENT_PASS" in report_md

    # Verify Investment Policy content
    with open(paths["ips_path"], "r", encoding="utf-8") as f:
        ips_md = f.read()
    assert "SOVEREIGN CORPORATE INVESTMENT POLICY STATEMENT (IPS)" in ips_md
    assert "CAPITAL PRESERVATION" in ips_md
    assert "U.S. Sovereign Treasury Bills" in ips_md


def test_07_cli_command_executions():
    """Verifies multi-action CLI commands execute cleanly."""
    script_path = os.path.join(SERVICES_DIR, "enterprise_fx_hedging_treasury_engine.py")

    cmd = [
        sys.executable,
        script_path,
        "--audit-fx-exposure",
        "--calculate-hedging-ratios",
        "--run-treasury-stress-test",
        "--export-treasury-policy",
        "--summary"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"CLI failed: {res.stderr}"
    assert "Cross-Border Multi-Currency Exposure Audit" in res.stdout
    assert "FX Delta Hedging & Synthetic Collar Schedules" in res.stdout
    assert "Sovereign U.S. T-Bill Ladder & Macro Stress Testing Summary" in res.stdout


def test_08_strict_brand_anonymity():
    """Verifies 100% Brand Anonymity across all Phase 25 files."""
    files_to_check = [
        os.path.join(SERVICES_DIR, "enterprise_fx_hedging_treasury_engine.py"),
        os.path.join(SERVICES_DIR, "enterprise_treasury_investment_policy.md"),
        os.path.join(REPORTS_DIR, "treasury_fx_stress_test_report.md"),
        os.path.join(DATA_DIR, "treasury_fx_hedging_schedule.json"),
        os.path.join(ROOT_DATA_DIR, "treasury_fx_hedging_schedule.json")
    ]

    for file_path in files_to_check:
        assert os.path.exists(file_path), f"File {file_path} must exist for anonymity check"
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().lower()
        for token in FORBIDDEN_FOUNDER_TOKENS:
            assert token.lower() not in content, (
                f"Forbidden founder token '{token}' detected in {file_path}!"
            )
