"""
⚡ DevSuperSuite Tech Services - Unit & Integration Test Suite
File: test_reconciliation_engine.py
Target: reconciliation_engine.py (Automated Payment Gateway Settlement & Multi-Channel Reconciliation Engine)
Strict Compliance: 100% Brand Anonymity - DevSuperSuite Official Only.
"""

import os
import sys
import json
import pytest
from pathlib import Path

# Add services directory to sys.path
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(SCRATCH_DIR, "services")
sys.path.insert(0, SERVICES_DIR)

from reconciliation_engine import (
    MultiChannelReconciliationEngine,
    LUT_REGISTRATION_NUMBER,
    BENCHMARK_FX_RATES,
    DEFAULT_REPORT_PATH
)

@pytest.fixture
def test_engine(tmp_path):
    """Initializes a reconciliation engine with isolated temporary ledger paths."""
    test_ledger = os.path.join(tmp_path, "test_settlement_ledger.json")
    test_store = os.path.join(tmp_path, "test_store_ledger.json")
    engine = MultiChannelReconciliationEngine(
        store_ledger_path=test_store,
        settlement_ledger_path=test_ledger
    )
    return engine

def test_01_multi_channel_ingestion(test_engine):
    """Verifies that all four core payment channels are successfully ingested."""
    channels = test_engine.data.get("channels", {})
    assert "gumroad" in channels
    assert "paypal" in channels
    assert "enterprise_wire" in channels
    assert "stripe_and_domestic" in channels

    assert len(channels["gumroad"]["records"]) >= 2
    assert len(channels["paypal"]["records"]) >= 2
    assert len(channels["enterprise_wire"]["records"]) >= 2
    assert len(channels["stripe_and_domestic"]["records"]) >= 5

def test_02_gross_vs_net_reconciliation(test_engine):
    """Verifies mathematical consistency of Gross vs Net Realized Capital."""
    rec = test_engine.reconcile_all_channels()
    tot = rec["totals"]

    assert tot["total_transactions"] == 11
    assert tot["gross_invoiced_usd"] == 24930.00
    assert tot["platform_fees_usd"] > 0.0
    assert tot["dispute_reserves_usd"] > 0.0
    
    # Mathematical invariant: Gross = Net + Fees + Reserves
    calculated_sum = round(tot["net_realized_capital_usd"] + tot["platform_fees_usd"] + tot["dispute_reserves_usd"], 2)
    assert calculated_sum == tot["gross_invoiced_usd"]

    # Realization yield should exceed 99% due to high-value enterprise wire
    assert tot["effective_realization_rate_pct"] > 99.0

def test_03_paypal_dispute_reserve_calculation(test_engine):
    """Verifies that PayPal rolling 5.0% dispute reserve is accurately calculated."""
    rec = test_engine.reconcile_all_channels()
    paypal_summary = rec["channel_summaries"]["paypal"]

    # 2 transactions of $29 each = $58.00 gross
    assert paypal_summary["gross_invoiced_usd"] == 58.00
    # 5% of $58.00 = $2.90 reserve hold
    assert paypal_summary["dispute_reserves_usd"] == 2.90
    assert paypal_summary["platform_fees_usd"] == 3.00  # 1.50 * 2
    assert paypal_summary["net_realized_usd"] == 52.10  # 58.00 - 3.00 - 2.90

def test_04_enterprise_wire_reconciliation(test_engine):
    """Verifies Milestone 1 wire transfer ($24,500.00) with code OUR clearing."""
    rec = test_engine.reconcile_all_channels()
    wire_summary = rec["channel_summaries"]["enterprise_wire"]

    # $24,500 + $99 = $24,599.00 gross
    assert wire_summary["gross_invoiced_usd"] == 24599.00
    assert wire_summary["dispute_reserves_usd"] == 0.00
    assert wire_summary["platform_fees_usd"] == 15.00  # $15 flat wire bank fee
    assert wire_summary["net_realized_usd"] == 24584.00
    assert wire_summary["effective_payout_pct"] > 99.9

def test_05_fx_gain_loss_calculation(test_engine):
    """Verifies foreign exchange gain calculations against benchmark rates."""
    rec = test_engine.reconcile_all_channels()
    tot = rec["totals"]

    # In our settlement ledger, actual rates (84.70 - 84.82) exceed benchmark (84.50)
    assert tot["total_fx_gain_loss_usd"] > 0.0
    assert tot["total_fx_gain_loss_usd"] == pytest.approx(93.72, abs=0.5)

def test_06_fira_statutory_tracking_and_lut_compliance(test_engine):
    """Verifies statutory FIRA tracking and zero-rated LUT export compliance."""
    rec = test_engine.reconcile_all_channels()
    fira = rec["fira_audit"]

    # 10 export transactions, 1 domestic UPI
    assert fira["total_export_transactions"] == 10
    assert fira["domestic_exempt_count"] == 1
    assert fira["fira_verified_count"] == 10
    assert fira["fira_pending_count"] == 0
    assert fira["compliance_rate_pct"] == 100.0

    # Verify Purpose codes
    purpose_codes = {r["purpose_code"] for r in fira["fira_records"]}
    assert "P0802" in purpose_codes  # Software Implementation
    assert "P0807" in purpose_codes  # Software Supply / Licensing
    assert "DOMESTIC" in purpose_codes

def test_07_report_generation_and_brand_anonymity(test_engine, tmp_path):
    """Verifies report generation and enforces strict 100% Brand Anonymity."""
    report_file = os.path.join(tmp_path, "test_monthly_report.md")
    generated_path = test_engine.generate_report(report_file)

    assert os.path.exists(generated_path)
    with open(generated_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Identity Checks
    assert "DevSuperSuite Official" in content
    assert "DevSuperSuite Tech Services" in content
    assert LUT_REGISTRATION_NUMBER in content
    assert "100% Brand Anonymity Protocol Verified" in content

    # Anonymity Negative Checks (Ensure zero leaks of personal names or private numbers)
    assert "pratik" not in content.lower()
    assert "atpad" not in content.lower()
    assert "+91" not in content

def test_08_cli_execution():
    """Tests execution of the reconciliation CLI with various flags."""
    import subprocess
    script_path = os.path.join(SERVICES_DIR, "reconciliation_engine.py")

    # Test summary flag
    res_summary = subprocess.run(
        [sys.executable, script_path, "--summary"],
        capture_output=True,
        text=True
    )
    assert res_summary.returncode == 0
    assert "Multi-Channel Gateway Reconciliation" in res_summary.stdout
    assert "Gross Invoiced Capital" in res_summary.stdout

    # Test audit-fira flag
    res_fira = subprocess.run(
        [sys.executable, script_path, "--audit-fira"],
        capture_output=True,
        text=True
    )
    assert res_fira.returncode == 0
    assert "STATUTORY FIRA & LUT COMPLIANCE AUDIT" in res_fira.stdout
    assert "P0802" in res_fira.stdout
