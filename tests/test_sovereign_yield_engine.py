"""
⚡ DevSuperSuite Global Treasury Desk - Unit & Integration Test Suite
File: test_sovereign_yield_engine.py
Phase: 29 - Enterprise Sovereign Treasury Cash Sweep & Automated Yield Engine
Author: DevSuperSuite Global Treasury Desk
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
DATA_DIR = os.path.join(SERVICES_DIR, "data")
ROOT_DATA_DIR = os.path.join(PROJECT_ROOT, "data")
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")

sys.path.insert(0, PROJECT_ROOT)

from services.enterprise_sovereign_yield_engine import (
    EnterpriseSovereignYieldEngine,
    OPERATIONAL_FLOAT_SWEEP_THRESHOLD_USD,
    MANDATORY_RUNWAY_DAYS,
    BASELINE_MONTHLY_BURN_USD,
    FDIC_INSURANCE_LIMIT_PER_INSTITUTION_USD,
    SOVEREIGN_PAPER_YIELDS,
    DEFAULT_TREASURY_POOLS,
    DEFAULT_SWEEP_SCHEDULE_FILE,
    ROOT_SWEEP_SCHEDULE_FILE,
    DEFAULT_SWEEP_REPORT_FILE
)

FORBIDDEN_FOUNDER_TOKENS = [
    "Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"
]


@pytest.fixture
def engine():
    return EnterpriseSovereignYieldEngine()


def test_01_sweep_threshold_trigger_above_50k(engine):
    """Verifies that depository cash in excess of $50,000 triggers an automated sweep."""
    buf = engine.audit_liquidity_buffers()
    assert buf["target_depository_float_threshold_usd"] == 50000.00
    assert buf["current_depository_cash_usd"] == 125000.00
    assert buf["surplus_capital_to_sweep_usd"] == 75000.00

    # Test boundary where cash is exactly $50,000 (zero surplus)
    engine_exact = EnterpriseSovereignYieldEngine(
        pools={
            "total_treasury_capital_usd": 50000.00,
            "jpmorgan_chase_depository_usd": 30000.00,
            "state_street_depository_usd": 20000.00,
            "bny_mellon_custodial_tbills_usd": 0.00
        }
    )
    buf_exact = engine_exact.audit_liquidity_buffers()
    assert buf_exact["surplus_capital_to_sweep_usd"] == 0.00


def test_02_mandatory_45_day_runway_compliance(engine):
    """Verifies that depository float maintains at least a 45-day operational cash runway."""
    buf = engine.audit_liquidity_buffers()
    assert buf["mandatory_runway_days"] == 45
    assert buf["mandatory_45d_cash_required_usd"] == 2700.00  # $60/day * 45 days
    assert buf["depository_retained_runway_days"] >= 45.0
    assert buf["depository_retained_runway_days"] > 800.0  # $50k gives 833.3 days
    assert buf["runway_mandate_satisfied"] is True


def test_03_sovereign_paper_blended_yield_band(engine):
    """Verifies that swept sovereign paper achieves a blended yield within 4.85% - 5.15% APY."""
    sweep = engine.simulate_cash_sweep()
    blended = sweep["blended_sovereign_apy_pct"]

    assert 4.85 <= blended <= 5.15, f"Yield {blended}% outside 4.85% - 5.15% band"
    assert sweep["yield_band_compliant"] is True
    assert sweep["annualized_accrued_yield_usd"] > 3500.0
    assert sweep["daily_accrued_yield_usd"] > 10.0


def test_04_t_bill_tranches_and_tenor_allocation(engine):
    """Verifies 4-week and 13-week U.S. Treasury Bill allocations and maturity schedules."""
    sweep = engine.simulate_cash_sweep()
    tranches = sweep["sovereign_tranches"]
    assert len(tranches) == 2

    t_4w = next(t for t in tranches if t["tenor_days"] == 28)
    t_13w = next(t for t in tranches if t["tenor_days"] == 91)

    assert t_4w["allocation_usd"] == 40000.00
    assert t_4w["apy_pct"] == 4.95
    assert t_4w["annual_yield_usd"] == 1980.00

    assert t_13w["allocation_usd"] == 35000.00
    assert t_13w["apy_pct"] == 5.10
    assert t_13w["annual_yield_usd"] == 1785.00


def test_05_fdic_insurance_limit_compliance_under_250k(engine):
    """Verifies that no depository counterparty exceeds the statutory $250,000 FDIC insurance limit."""
    stress = engine.stress_test_custodians()
    assert stress["all_custodians_under_250k_limit"] is True

    matrix = {c["institution"]: c for c in stress["custodian_exposure_matrix"]}
    assert matrix["JPMorgan Chase Bank, N.A."]["balance_usd"] == 30000.00
    assert matrix["JPMorgan Chase Bank, N.A."]["balance_usd"] <= FDIC_INSURANCE_LIMIT_PER_INSTITUTION_USD
    assert matrix["State Street Bank and Trust Company"]["balance_usd"] == 20000.00
    assert matrix["State Street Bank and Trust Company"]["balance_usd"] <= FDIC_INSURANCE_LIMIT_PER_INSTITUTION_USD


def test_06_multi_custodian_diversification(engine):
    """Verifies custodian diversification across BNY Mellon, State Street, and JPMorgan."""
    stress = engine.stress_test_custodians()
    institutions = {c["institution"] for c in stress["custodian_exposure_matrix"]}

    assert "The Bank of New York Mellon (BNY Mellon)" in institutions
    assert "JPMorgan Chase Bank, N.A." in institutions
    assert "State Street Bank and Trust Company" in institutions

    total_exposure = sum(c["exposure_pct"] for c in stress["custodian_exposure_matrix"])
    assert 99.9 <= total_exposure <= 100.1


def test_07_bank_run_stress_scenario(engine):
    """Verifies bank run stress test surviving runway exceeds the 45-day mandate."""
    stress = engine.stress_test_custodians()
    run = stress["bank_run_stress_test"]

    assert run["verdict"] == "PASS_ZERO_OPERATIONAL_CONTRACTION"
    assert run["immediate_surviving_depository_cash_usd"] == 20000.00
    assert run["immediate_surviving_runway_days"] >= 45.0
    assert run["immediate_surviving_runway_days"] > 300.0
    assert run["runway_mandate_survived"] is True


def test_08_sovereign_tbill_segregation_and_insulation(engine):
    """Verifies 100% of sovereign paper is held in segregated trust at BNY Mellon."""
    stress = engine.stress_test_custodians()
    run = stress["bank_run_stress_test"]

    assert run["sovereign_tbills_insulated_usd"] == 75000.00
    bny = next(c for c in stress["custodian_exposure_matrix"] if "BNY Mellon" in c["institution"])
    assert bny["asset_class"] == "U.S. Sovereign Treasury Bills (Direct Custody)"
    assert "Segregated" in bny["regulatory_protection"]


def test_09_artifact_export_and_json_persistence(engine):
    """Verifies persistence of cash sweep JSON schedule and Markdown report."""
    paths = engine.export_all_artifacts()

    for key, path in paths.items():
        assert os.path.exists(path), f"File {path} was not created"

    # Verify JSON schedule
    with open(paths["schedule_path"], "r", encoding="utf-8") as f:
        schedule = json.load(f)
    assert schedule["metadata"]["reporting_entity"] == "DevSuperSuite Group"
    assert "liquidity_buffers_audit" in schedule
    assert "sovereign_cash_sweep" in schedule
    assert "custodian_stress_testing" in schedule

    # Verify Markdown report
    with open(paths["report_path"], "r", encoding="utf-8") as f:
        report_md = f.read()
    assert "ENTERPRISE SOVEREIGN TREASURY CASH SWEEP & AUTOMATED YIELD REPORT" in report_md
    assert "4-Week US T-Bills" in report_md
    assert "13-Week US T-Bills" in report_md
    assert "BNY Mellon" in report_md


def test_10_cli_command_executions():
    """Verifies multi-action CLI commands execute cleanly."""
    script_path = os.path.join(SERVICES_DIR, "enterprise_sovereign_yield_engine.py")

    cmd = [
        sys.executable,
        script_path,
        "--simulate-cash-sweep",
        "--audit-liquidity-buffers",
        "--stress-test-custodians",
        "--export-treasury-binder",
        "--summary"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"CLI failed: {res.stderr}"
    assert "Dynamic Liquidity Buffer & Working Capital Audit" in res.stdout
    assert "Automated Cash Sweep to Sovereign U.S. Treasury Bills" in res.stdout
    assert "Custodial Counterparty Limits & Bank Run Stress Test" in res.stdout


def test_11_strict_brand_anonymity():
    """Verifies 100% Brand Anonymity across all Phase 29 files."""
    files_to_check = [
        os.path.join(SERVICES_DIR, "enterprise_sovereign_yield_engine.py"),
        os.path.join(REPORTS_DIR, "sovereign_treasury_cash_sweep_report.md"),
        os.path.join(DATA_DIR, "sovereign_treasury_sweep_schedule.json"),
        os.path.join(ROOT_DATA_DIR, "sovereign_treasury_sweep_schedule.json")
    ]

    for file_path in files_to_check:
        assert os.path.exists(file_path), f"File {file_path} must exist for anonymity check"
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().lower()
        for token in FORBIDDEN_FOUNDER_TOKENS:
            assert token.lower() not in content, (
                f"Forbidden founder token '{token}' detected in {file_path}!"
            )
