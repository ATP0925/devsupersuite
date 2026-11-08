"""
⚡ DevSuperSuite Global Treasury Desk - Multi-Currency Treasury Sweep & FX Hedging Test Suite
File: test_fx_hedging_execution.py
Target: enterprise_fx_hedging_execution_engine.py
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

from enterprise_fx_hedging_execution_engine import (
    EnterpriseFXHedgingExecutionEngine,
    REGIONAL_COLLECTION_ACCOUNTS,
    BENCHMARK_SPOT_RATES,
    CENTRAL_BANK_RATES,
    TREASURY_ENTITY_NAME,
    TREASURY_DESK_TITLE,
    TREASURY_OFFICIAL_EMAIL,
    DEFAULT_SWEEP_SCHEDULE_FILE,
    ROOT_SWEEP_SCHEDULE_FILE,
    DEFAULT_SWEEP_REPORT_FILE
)


@pytest.fixture
def sweep_engine():
    """Initializes the multi-currency treasury sweep & FX hedging engine."""
    return EnterpriseFXHedgingExecutionEngine()


def test_01_regional_banking_accounts_topology(sweep_engine):
    """Verifies that all 5 premier commercial banking accounts (JPM, Barclays, MUFG, HDFC) are properly configured."""
    audit = sweep_engine.audit_multi_currency_balances()
    assert audit["total_accounts_audited"] == 5
    expected_ccy = {"USD", "EUR", "GBP", "JPY", "INR"}
    assert set(audit["accounts"].keys()) == expected_ccy
    assert audit["commercial_principal"] == TREASURY_ENTITY_NAME
    assert audit["treasury_desk"] == TREASURY_DESK_TITLE

    # Check bank affiliations
    accs = audit["accounts"]
    assert "J.P. Morgan Chase" in accs["USD"]["custodian_bank"]
    assert "J.P. Morgan SE" in accs["EUR"]["custodian_bank"]
    assert "Barclays" in accs["GBP"]["custodian_bank"]
    assert "MUFG" in accs["JPY"]["custodian_bank"]
    assert "HDFC" in accs["INR"]["custodian_bank"]


def test_02_cip_forward_pricing_and_points(sweep_engine):
    """Verifies Covered Interest Parity (CIP) forward FX pricing formula across foreign currencies."""
    # Test EUR (ECB 3.25% vs US 5.18%): US rate is higher, so forward EUR should trade at a premium to spot
    eur_spot = BENCHMARK_SPOT_RATES["EUR"]
    eur_fwd_90d = sweep_engine.calculate_cip_forward_rate("EUR", tenor_days=90)
    assert eur_fwd_90d > eur_spot

    # Test JPY (BoJ 0.25% vs US 5.18%): JPY forward USD rate should reflect huge interest rate differential
    jpy_spot = BENCHMARK_SPOT_RATES["JPY"]
    jpy_fwd_90d = sweep_engine.calculate_cip_forward_rate("JPY", tenor_days=90)
    assert jpy_fwd_90d > jpy_spot

    # USD forward rate should always equal 1.0
    usd_fwd = sweep_engine.calculate_cip_forward_rate("USD")
    assert usd_fwd == 1.0000


def test_03_delta_hedge_ratios_and_mechanisms(sweep_engine):
    """Verifies targeted hedge ratios and execution mechanisms for each currency."""
    audit = sweep_engine.audit_multi_currency_balances()
    accs = audit["accounts"]

    assert accs["USD"]["target_hedge_ratio"] == 0.00
    assert accs["USD"]["hedge_mechanism"] == "BASE_CURRENCY_NATURAL_SETTLEMENT"

    assert accs["EUR"]["target_hedge_ratio"] == 0.80
    assert accs["EUR"]["hedge_mechanism"] == "FORWARD_CONTRACT_CIP"

    assert accs["GBP"]["target_hedge_ratio"] == 0.80
    assert accs["GBP"]["hedge_mechanism"] == "FORWARD_CONTRACT_CIP"

    assert accs["JPY"]["target_hedge_ratio"] == 0.85
    assert accs["JPY"]["hedge_mechanism"] == "FORWARD_CONTRACT_CIP"

    assert accs["INR"]["target_hedge_ratio"] == 0.75
    assert accs["INR"]["hedge_mechanism"] == "NON_DELIVERABLE_FORWARD_NDF"


def test_04_var_volatility_mitigation(sweep_engine):
    """Verifies 99% 10-day Value-at-Risk (VaR) reduction exceeds 80% portfolio deflection."""
    hedging = sweep_engine.simulate_fx_hedging(tenor_days=90)
    
    assert hedging["overall_var_reduction_pct"] > 80.0
    assert hedging["overall_var_reduction_pct"] == 81.25
    assert hedging["total_unhedged_var_usd"] > 4000.00
    assert hedging["total_residual_var_usd"] < 1000.00
    assert hedging["total_non_usd_hedged_usd"] > 90000.00


def test_05_working_capital_buffer_retention(sweep_engine):
    """Verifies that regional working capital buffers are preserved across depository accounts."""
    audit = sweep_engine.audit_multi_currency_balances()
    
    # Check exact retained working capital
    assert audit["total_retained_buffer_usd"] == 65043.91
    assert audit["accounts"]["USD"]["working_capital_retention_usd"] == 50000.00
    assert audit["accounts"]["EUR"]["working_capital_retention_local"] == 5000.00
    assert audit["accounts"]["GBP"]["working_capital_retention_local"] == 3500.00
    assert audit["accounts"]["JPY"]["working_capital_retention_local"] == 500000.0
    assert audit["accounts"]["INR"]["working_capital_retention_local"] == 150000.0


def test_06_treasury_sweep_execution(sweep_engine):
    """Verifies execution of liquidity sweep moving surplus capital into US T-Bills."""
    sweep = sweep_engine.execute_treasury_sweep()
    
    assert sweep["total_accounts_swept"] == 5
    assert sweep["settlement_currency"] == "USD"
    assert sweep["total_capital_swept_to_tbills_usd"] == 494394.29
    assert sweep["total_working_capital_retained_usd"] == 65043.91

    for exec_item in sweep["sweep_executions"]:
        assert exec_item["sweep_status"] == "EXECUTED_CONFIRMED"
        assert exec_item["net_swept_usd"] > 0


def test_07_sovereign_yield_at_518_apy(sweep_engine):
    """Verifies 5.18% APY sovereign interest yield generation on swept T-Bill pool."""
    yld = sweep_engine.calculate_sovereign_yield()
    
    assert yld["sovereign_benchmark_apy_pct"] == 5.18
    assert yld["total_swept_capital_pool_usd"] == 494394.29
    assert yld["annual_interest_yield_usd"] == 25609.62
    assert yld["monthly_interest_yield_usd"] == 2134.13
    assert yld["daily_interest_yield_usd"] == 70.16


def test_08_rolling_t_bill_ladder_allocations(sweep_engine):
    """Verifies rolling ladder structure: 40% in 4-week bills, 60% in 13-week bills."""
    yld = sweep_engine.calculate_sovereign_yield()
    ladder = yld["rolling_t_bill_ladder"]
    
    assert "US_T_BILL_4W" in ladder
    assert "US_T_BILL_13W" in ladder
    
    bill_4w = ladder["US_T_BILL_4W"]
    bill_13w = ladder["US_T_BILL_13W"]
    
    assert bill_4w["allocation_pct"] == 40.0
    assert bill_13w["allocation_pct"] == 60.0
    assert bill_4w["principal_invested_usd"] == 197757.72
    assert bill_13w["principal_invested_usd"] == 296636.57
    assert bill_4w["cusip_prefix"] == "912797"
    assert bill_13w["cusip_prefix"] == "912796"


def test_09_binder_schedule_json_integrity(sweep_engine):
    """Verifies export of JSON schedule files and mirrored persistence."""
    paths = sweep_engine.export_all()
    
    assert os.path.exists(paths["schedule_file"])
    assert os.path.exists(paths["root_schedule_file"])
    assert os.path.exists(paths["report_file"])
    
    with open(paths["schedule_file"], "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["binder_id"] == "DSS-TREASURY-SWEEP-2026-BINDER"
        assert data["sovereign_apy_pct"] == 5.18
        assert data["portfolio_summary"]["annual_sovereign_yield_usd"] == 25609.62
        assert data["portfolio_summary"]["total_swept_to_tbills_usd"] == 494394.29
        assert "sweep_executions" in data


def test_10_audit_report_markdown_integrity(sweep_engine):
    """Verifies that the generated markdown audit report contains all necessary sections and tables."""
    paths = sweep_engine.export_all()
    
    with open(paths["report_file"], "r", encoding="utf-8") as f:
        md = f.read()
        assert "DevSuperSuite Global Treasury Desk" in md
        assert "5.18% APY" in md
        assert "$494,394.29" in md
        assert "+$25,609.62 / yr" in md
        assert "J.P. Morgan Chase" in md
        assert "Barclays" in md
        assert "MUFG" in md
        assert "HDFC" in md
        assert "flowchart TD" in md


def test_11_cli_interface_execution():
    """Smoke tests all CLI arguments for the execution engine."""
    cli_flags = [
        "--audit-multi-currency-balances",
        "--simulate-fx-hedging",
        "--execute-treasury-sweep",
        "--calculate-sovereign-yield",
        "--export-sweep-binder",
        "--summary"
    ]
    script_path = os.path.join(SERVICES_DIR, "enterprise_fx_hedging_execution_engine.py")

    for flag in cli_flags:
        res = subprocess.run(
            [sys.executable, script_path, flag],
            capture_output=True,
            text=True
        )
        assert res.returncode == 0, f"CLI flag {flag} failed: {res.stderr}"
        assert len(res.stdout.strip()) > 0


def test_12_brand_anonymity_strict_compliance():
    """Verifies 100% Brand Anonymity Protocol: zero forbidden founder names or private emails."""
    forbidden_tokens = ["Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"]
    target_files = [
        os.path.join(SERVICES_DIR, "enterprise_fx_hedging_execution_engine.py"),
        DEFAULT_SWEEP_SCHEDULE_FILE,
        ROOT_SWEEP_SCHEDULE_FILE,
        DEFAULT_SWEEP_REPORT_FILE
    ]

    for fpath in target_files:
        assert os.path.exists(fpath), f"File {fpath} must exist for anonymity check"
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            for token in forbidden_tokens:
                assert token not in content, f"Forbidden brand anonymity token '{token}' discovered in {fpath}"
