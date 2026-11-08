"""
⚡ DevSuperSuite Treasury & Corporate Finance - Unit & Integration Test Suite
File: test_multi_currency_treasury_sweep.py
Target: multi_currency_treasury_sweep_engine.py (Multi-Currency Dynamic Treasury Hedging & Automated Bank Sweep Engine)
Strict Compliance: 100% Brand Anonymity - DevSuperSuite Treasury & Corporate Finance Only (cfo@devsupersuite.com).
"""

import os
import sys
import json
import subprocess
import pytest

# Add services directory to sys.path
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(SCRATCH_DIR, "services")
sys.path.insert(0, SERVICES_DIR)

from multi_currency_treasury_sweep_engine import (
    MultiCurrencyTreasurySweepEngine,
    CENTRAL_BANK_BENCHMARKS,
    SOVEREIGN_TREASURY_APY_PCT,
    TARGET_OPERATING_FLOATS,
    SETTLEMENT_LEDGER_FILE,
    SWEEP_LEDGER_FILE,
    DEFAULT_SWEEP_REPORT_FILE
)

@pytest.fixture
def sweep_engine(tmp_path):
    """Initializes Treasury Sweep Engine with isolated test paths."""
    test_ledger = os.path.join(tmp_path, "test_sweep_ledger.json")
    test_report = os.path.join(tmp_path, "test_sweep_report.md")
    return MultiCurrencyTreasurySweepEngine(
        sweep_ledger_path=test_ledger,
        report_path=test_report
    )

def test_01_currency_pools_consolidation(sweep_engine):
    """Verifies multi-currency cash pooling across USD, EUR, GBP, and INR vaults."""
    audit = sweep_engine.audit_currency_pools()
    pools = audit["pools"]

    assert "USD" in pools
    assert "EUR" in pools
    assert "GBP" in pools
    assert "INR" in pools

    # USD Pool
    usd = pools["USD"]
    assert usd["native_balance"] == 24683.00
    assert usd["usd_equivalent"] == 24683.00
    assert usd["target_float_native"] == TARGET_OPERATING_FLOATS["USD"]

    # EUR Pool (ECB benchmark 1.0850)
    eur = pools["EUR"]
    assert eur["native_balance"] == 100.00
    assert eur["usd_equivalent"] == round(100.00 * CENTRAL_BANK_BENCHMARKS["EUR_TO_USD"], 2)

    # Total liquidity equivalence
    assert audit["total_pools_usd_equivalent"] == pytest.approx(24894.78, abs=0.5)

def test_02_zba_sweep_mechanics(sweep_engine):
    """Verifies Zero-Balance Account (ZBA) sweep into sovereign treasury vault."""
    sweep = sweep_engine.simulate_zba_sweep()

    assert sweep["total_swept_capital_usd"] == 22183.00
    assert sweep["total_retained_operating_float_usd"] == pytest.approx(2711.78, abs=0.5)
    total_reconciled = sweep["total_swept_capital_usd"] + sweep["total_retained_operating_float_usd"]
    assert total_reconciled == pytest.approx(sweep["total_opening_liquidity_usd"], abs=0.1)

    # Verify USD pool sweep action
    usd_action = next(a for a in sweep["actions"] if a["currency"] == "USD")
    assert usd_action["action"] == "SURPLUS_SWEPT_TO_TREASURY_VAULT"
    assert usd_action["swept_surplus_usd"] == 22183.00
    assert usd_action["retained_float_usd"] == 2500.00

def test_03_yield_accrual_mathematics(sweep_engine):
    """Verifies compounding yield accrual on swept sovereign treasury capital (> 4.5% APY)."""
    y = sweep_engine.calculate_yield_accrual(swept_amount_usd=22183.00, apy_pct=4.95)

    assert y["sovereign_apy_pct"] == 4.95
    assert y["sovereign_apy_pct"] >= 4.50
    assert y["principal_swept_usd"] == 22183.00

    # Annualized yield: 22183 * 0.0495 = $1,098.06
    assert y["annualized_yield_usd"] == pytest.approx(1098.06, abs=0.5)
    assert y["daily_accrued_yield_usd"] > 2.50
    assert y["monthly_accrued_yield_usd"] > 90.00

    # Scale Scenarios (Seed & Series A)
    scenarios = {s["scenario"]: s for s in y["scenarios"]}
    assert scenarios["Post-Seed SAFE Tranche Pool"]["annual_yield_usd"] == 24750.00
    assert scenarios["Series A Post-Financing Treasury Vault"]["annual_yield_usd"] == 495000.00

def test_04_dynamic_fx_hedging_trailing_stop(sweep_engine):
    """Verifies trailing-stop auto-conversion trigger (+0.5% over benchmark)."""
    # EUR benchmark = 1.0850. Spot = 1.0920 (+0.645% appreciation)
    res = sweep_engine.check_dynamic_fx_hedging(currency="EUR", current_spot_rate=1.0920)

    assert res["tripwire_status"] == "TRIGGERED_TAKE_PROFIT"
    assert res["action"] == "TRAILING_STOP_AUTO_CONVERT_SURPLUS_TO_USD"
    assert res["variance_pct"] >= 0.5
    assert "Favorable FX appreciation" in res["rationale"]

def test_05_dynamic_fx_hedging_drawdown_freeze(sweep_engine):
    """Verifies drawdown stop-loss freeze trigger (-1.5% below benchmark)."""
    # GBP benchmark = 1.2750. Spot = 1.2500 (-1.961% depreciation)
    res = sweep_engine.check_dynamic_fx_hedging(currency="GBP", current_spot_rate=1.2500)

    assert res["tripwire_status"] == "TRIGGERED_STOP_LOSS_FREEZE"
    assert res["action"] == "DRAWDOWN_FREEZE_HOLD_IN_NATURAL_CURRENCY"
    assert res["variance_pct"] <= -1.5
    assert "Conversion frozen" in res["rationale"]

def test_06_dynamic_fx_hedging_normal_band(sweep_engine):
    """Verifies normal band operation holding natural balance to offset API expenses."""
    # EUR spot = 1.0860 (+0.092% within normal band)
    res = sweep_engine.check_dynamic_fx_hedging(currency="EUR", current_spot_rate=1.0860)

    assert res["tripwire_status"] == "NORMAL_OPERATING_BAND"
    assert res["action"] == "NATURAL_BALANCE_OFFSET_HOLD"
    assert "Retain natural balance" in res["rationale"]

def test_07_markdown_report_generation_and_brand_anonymity(sweep_engine, tmp_path):
    """Generates treasury sweep markdown report and asserts strict 100% Brand Anonymity."""
    test_rep = os.path.join(tmp_path, "test_sweep_report.md")
    test_led = os.path.join(tmp_path, "test_sweep_ledger.json")

    saved = sweep_engine.save_reports_and_ledger(report_path=test_rep, ledger_path=test_led)
    assert os.path.exists(saved["report_path"])
    assert os.path.exists(saved["ledger_path"])

    with open(saved["report_path"], "r", encoding="utf-8") as f:
        content = f.read()

    # Brand authority checks
    assert "DevSuperSuite Treasury & Corporate Finance" in content
    assert "cfo@devsupersuite.com" in content
    assert "4.95% APY" in content
    assert "$22,183.00 USD" in content

    # Zero PII Leaks: forbidden personal founder tokens
    forbidden = ["Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"]
    for word in forbidden:
        assert word not in content, f"Brand Anonymity violation: found '{word}' in treasury sweep report."

def test_08_cli_execution():
    """Verifies CLI execution with --audit-currency-pools, --simulate-zba-sweep, and --summary flags."""
    script_path = os.path.join(SERVICES_DIR, "multi_currency_treasury_sweep_engine.py")

    cmd = [
        sys.executable, script_path,
        "--audit-currency-pools",
        "--simulate-zba-sweep",
        "--calculate-yield-accrual",
        "--summary"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert "Treasury Sweep & Yield Report" in res.stdout
    assert "Sweep Persistence Ledger" in res.stdout
    assert "Surplus Capital Swept to T-Bills:  $22,183.00 USD" in res.stdout
    assert "Sovereign Portfolio APY:           4.95% APY" in res.stdout
    assert "Annualized Passive Treasury Yield: +$1,098.06 USD / Year" in res.stdout
