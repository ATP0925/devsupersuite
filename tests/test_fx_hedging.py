"""
⚡ DevSuperSuite Tech Services - Unit & Integration Test Suite
File: test_fx_hedging.py
Target: fx_hedging_payout_engine.py (Global FX Hedging Treasury Policy & Multi-Gateway Payout Engine)
Strict Compliance: 100% Brand Anonymity - DevSuperSuite Treasury Operations Only.
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

from fx_hedging_payout_engine import (
    FXHedgingPayoutEngine,
    CENTRAL_BANK_BENCHMARKS,
    LUT_REGISTRATION_NUMBER,
    NATURAL_HEDGE_RESERVE_CAP_USD,
    SETTLEMENT_LEDGER_FILE,
    DEFAULT_FX_REPORT_FILE
)

@pytest.fixture
def treasury_engine():
    """Initializes FX Hedging Payout Engine with primary settlement ledger."""
    return FXHedgingPayoutEngine(ledger_path=SETTLEMENT_LEDGER_FILE)

def test_01_optimal_routing_domestic_inr(treasury_engine):
    """Verifies lowest-friction domestic UPI/IMPS routing with 0% fee and 0% FX loss."""
    # Test by currency INR
    route_inr = treasury_engine.determine_optimal_payout_rail(
        amount=2500.00,
        currency="INR"
    )
    assert route_inr["route"] == "DOMESTIC_UPI_IMPS"
    assert route_inr["platform_fee_usd"] == 0.00
    assert route_inr["intermediary_fee_usd"] == 0.00
    assert route_inr["fx_spread_loss_pct"] == 0.00
    assert route_inr["fira_status"] == "NOT_APPLICABLE_DOMESTIC"
    assert route_inr["purpose_code"] == "DOMESTIC"
    assert "Instant Domestic UPI / IMPS" in route_inr["rail_name"]

    # Test by transaction type 'domestic'
    route_dom = treasury_engine.determine_optimal_payout_rail(
        amount=29.00,
        currency="USD",
        transaction_type="domestic"
    )
    assert route_dom["route"] == "DOMESTIC_UPI_IMPS"
    assert route_dom["platform_fee_usd"] == 0.00

def test_02_optimal_routing_enterprise_wire(treasury_engine):
    """Verifies enterprise wire transfer routing via SWIFT Code OUR with zero intermediary deduction."""
    route_wire = treasury_engine.determine_optimal_payout_rail(
        amount=24500.00,
        currency="USD",
        transaction_type="wire"
    )
    assert route_wire["route"] == "SWIFT_OUR_WIRE"
    assert route_wire["platform_fee_usd"] == 15.00  # Flat incoming wire depository charge
    assert route_wire["intermediary_fee_usd"] == 0.00  # Sender absorbs deductions under code OUR
    assert route_wire["fira_status"] == "FIRA_MANDATORY_CROSS_BORDER"
    assert route_wire["purpose_code"] == "P0802"
    assert "SWIFT MT103" in route_wire["rail_name"]
    assert route_wire["action"] == "CLEARED_IN_PRIMARY_USD_VAULT"

    # Threshold test: USD >= $5,000 routes to wire automatically
    route_auto = treasury_engine.determine_optimal_payout_rail(
        amount=5000.00,
        currency="USD",
        transaction_type="standard"
    )
    assert route_auto["route"] == "SWIFT_OUR_WIRE"

def test_03_optimal_routing_natural_balance_eur_gbp(treasury_engine):
    """Verifies European EUR & UK GBP routing into Natural Currency Balance Vault."""
    for curr in ("EUR", "GBP"):
        route = treasury_engine.determine_optimal_payout_rail(
            amount=100.00,
            currency=curr
        )
        assert route["route"] == "NATURAL_CURRENCY_VAULT"
        assert route["currency"] == curr
        assert route["action"] == "HOLD_IN_CURRENCY_BALANCE_FOR_NATURAL_OFFSET"
        assert route["fx_spread_loss_pct"] == 0.00
        assert route["fira_status"] == "FIRA_MANDATORY_CROSS_BORDER"
        assert route["purpose_code"] == "P0807"
        assert "trailing_stop_threshold" in route
        benchmark = CENTRAL_BANK_BENCHMARKS[f"{curr}_TO_USD"]
        assert route["trailing_stop_threshold"] > benchmark

def test_04_optimal_routing_stripe_usd(treasury_engine):
    """Verifies retail USD card transactions route into Stripe multi-currency depository."""
    route_card = treasury_engine.determine_optimal_payout_rail(
        amount=29.00,
        currency="USD",
        transaction_type="card"
    )
    assert route_card["route"] == "STRIPE_USD_VAULT"
    assert route_card["currency"] == "USD"
    assert route_card["action"] == "AUTOMATED_MULTI_CURRENCY_DEPOSIT"
    assert route_card["purpose_code"] == "P0807"
    # Fee: 2.9% + $0.30 = round(29 * 0.029 + 0.30, 2) = $1.14
    assert route_card["platform_fee_usd"] == 1.14

def test_05_fx_variance_and_gain_calculation(treasury_engine):
    """Verifies calculation of realized FX gains against official Central Bank reference rates."""
    audit = treasury_engine.audit_fx_settlements()

    assert audit["settlements_audited"] == 11
    assert audit["total_gross_inflow_usd"] == 24930.00
    assert audit["total_net_realized_usd"] == 24894.79
    # Realized rates (84.68 to 84.82) vs RBI benchmark (84.50) yield positive FX gain (~$93.72)
    assert audit["total_fx_gain_loss_usd"] > 0.0
    assert audit["total_fx_gain_loss_usd"] == pytest.approx(93.72, abs=0.5)

    # Check channel breakdown metrics
    channels = audit["channel_metrics"]
    assert "enterprise_wire" in channels
    assert "gumroad" in channels
    assert "paypal" in channels
    assert "stripe_and_domestic" in channels
    assert channels["enterprise_wire"]["fx_gain_loss_usd"] > 90.0

def test_06_natural_hedging_spread_savings(treasury_engine):
    """Verifies natural currency balance matching saves ~3.0% retail conversion spread."""
    audit = treasury_engine.audit_fx_settlements()

    assert audit["natural_hedge_savings_usd"] == pytest.approx(747.90, abs=1.0)
    assert audit["natural_hedge_savings_usd"] > 700.00

def test_07_fira_statutory_tracking_and_lut(treasury_engine):
    """Verifies statutory FIRA tracking and zero-rated LUT export compliance."""
    audit = treasury_engine.audit_fx_settlements()
    fira_data = audit["fira_audit"]

    assert audit["lut_reference"] == LUT_REGISTRATION_NUMBER
    assert fira_data["export_transactions_count"] == 10
    assert fira_data["fira_verified_count"] == 10
    assert fira_data["compliance_pct"] == 100.0

    # Ensure all cross-border transactions have valid FIRA references
    for rec in fira_data["records"]:
        if rec["fira_status"] == "FIRA_ISSUED_AND_VERIFIED":
            assert rec["fira_number"].startswith("FIRA-")
            assert rec["purpose_code"] in ("P0802", "P0807")
        else:
            assert rec["fira_status"] == "NOT_APPLICABLE_DOMESTIC"
            assert rec["purpose_code"] == "DOMESTIC"

def test_08_report_generation_and_brand_anonymity(treasury_engine, tmp_path):
    """Generates monthly FX settlement report and asserts strict 100% Brand Anonymity."""
    test_report_file = os.path.join(tmp_path, "test_fx_report.md")
    treasury_engine.generate_report(test_report_file)

    assert os.path.exists(test_report_file)
    with open(test_report_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Brand and Authority assertions
    assert "DevSuperSuite Treasury Operations" in content
    assert "treasury@devsupersuite.com" in content
    assert LUT_REGISTRATION_NUMBER in content
    assert "$24,894.79 USD" in content
    assert "99.86% Realized" in content
    assert "+$93.72 USD" in content
    assert "100.0% Compliant" in content

    # Anonymity verification: forbidden personal tokens
    forbidden = ["Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"]
    for word in forbidden:
        assert word not in content, f"Brand Anonymity violation: found '{word}' in generated FX report."

def test_09_cli_execution():
    """Verifies CLI execution with --route-payout, --audit-fx, and --summary flags."""
    script_path = os.path.join(SERVICES_DIR, "fx_hedging_payout_engine.py")

    # 1. Test routing CLI
    cmd_route = [
        sys.executable, script_path,
        "--route-payout",
        "--amount", "24500.00",
        "--currency", "USD",
        "--type", "wire"
    ]
    res_route = subprocess.run(cmd_route, capture_output=True, text=True, check=True)
    assert "Optimal Routing Rail:    Institutional Corporate Wire" in res_route.stdout
    assert "SWIFT MT103" in res_route.stdout
    assert "Platform Fee:            $15.00 USD" in res_route.stdout

    # 2. Test audit & summary CLI
    cmd_audit = [
        sys.executable, script_path,
        "--audit-fx",
        "--summary"
    ]
    res_audit = subprocess.run(cmd_audit, capture_output=True, text=True, check=True)
    assert "Net Realized Capital:         $24,894.79 USD (99.86% Realization)" in res_audit.stdout
    assert "Realized FX Gain / Loss:      +$93.72 USD (Favorable Gain)" in res_audit.stdout
    assert "Statutory FIRA Compliance:    100.0%" in res_audit.stdout
