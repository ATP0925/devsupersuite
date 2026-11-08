"""
⚡ DevSuperSuite Treasury & Corporate Finance - Unit & Integration Test Suite
File: test_enterprise_usage_metering.py
Target: enterprise_usage_metering_engine.py (Institutional Usage-Based Metering & Overage Billing Engine)
Strict Compliance: 100% Brand Anonymity - DevSuperSuite Treasury & Corporate Finance Only (cfo@devsupersuite.com).
"""

import os
import sys
import json
import subprocess
import pytest

# Add services and repo root to sys.path
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(SCRATCH_DIR, "services")
if SERVICES_DIR not in sys.path:
    sys.path.insert(0, SERVICES_DIR)
if SCRATCH_DIR not in sys.path:
    sys.path.insert(0, SCRATCH_DIR)

from enterprise_usage_metering_engine import (
    EnterpriseUsageMeteringEngine,
    ENTERPRISE_TIERS,
    OVERAGE_RATES,
    SAMPLE_ENTERPRISE_ACCOUNTS,
    METERING_LEDGER_FILE,
    DEFAULT_METERING_REPORT_FILE
)

FORBIDDEN_FOUNDER_TOKENS = [
    "Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"
]


@pytest.fixture
def metering_engine(tmp_path):
    """Initializes Usage Metering Engine with isolated test paths."""
    test_ledger = os.path.join(tmp_path, "test_metering_ledger.json")
    test_report = os.path.join(tmp_path, "test_metering_report.md")
    return EnterpriseUsageMeteringEngine(
        ledger_path=test_ledger,
        report_path=test_report
    )


def test_01_tiers_and_overage_rates_structure():
    """Verifies that all enterprise tiers and statutory overage unit rates are calibrated."""
    assert "ENTERPRISE_CORE" in ENTERPRISE_TIERS
    assert "ENTERPRISE_SCALE" in ENTERPRISE_TIERS
    assert "ENTERPRISE_DEDICATED" in ENTERPRISE_TIERS

    core = ENTERPRISE_TIERS["ENTERPRISE_CORE"]
    assert core["monthly_base_fee_usd"] == 2500.00
    assert core["included_mad_seats"] == 10
    assert core["included_ast_tokens"] == 25_000_000
    assert core["included_secret_scans"] == 50_000
    assert core["included_compute_hours"] == 500.0

    scale = ENTERPRISE_TIERS["ENTERPRISE_SCALE"]
    assert scale["monthly_base_fee_usd"] == 6500.00
    assert scale["included_mad_seats"] == 35
    assert scale["included_ast_tokens"] == 75_000_000

    ded = ENTERPRISE_TIERS["ENTERPRISE_DEDICATED"]
    assert ded["monthly_base_fee_usd"] == 12500.00
    assert ded["included_mad_seats"] == 100
    assert ded["included_ast_tokens"] == 250_000_000

    assert OVERAGE_RATES["additional_seat_monthly_usd"] == 49.00
    assert OVERAGE_RATES["ast_tokens_per_million_usd"] == 4.00
    assert OVERAGE_RATES["secret_scans_per_thousand_usd"] == 0.05
    assert OVERAGE_RATES["compute_hours_per_hour_usd"] == 0.20


def test_02_mid_cycle_seat_proration_math(metering_engine):
    """Verifies exact day-count proration calculation for mid-cycle seat additions."""
    # 5 additional seats active for 15 days of 30-day month -> 5 * 49 * 0.5 = $122.50
    proration = metering_engine.calculate_seat_proration(
        additional_seats=5,
        days_active=15,
        cycle_days=30,
        monthly_seat_rate=49.00
    )
    assert proration["additional_seats"] == 5
    assert proration["days_active"] == 15
    assert proration["proration_factor"] == 0.50
    assert proration["prorated_charge_usd"] == 122.50

    # 2 seats active for 10 days of 30-day month -> 2 * 49 * (10/30) = $32.67
    proration_partial = metering_engine.calculate_seat_proration(2, 10, 30, 49.00)
    assert proration_partial["prorated_charge_usd"] == pytest.approx(32.67, abs=0.01)

    # Edge cases: 0 seats or 0 days
    assert metering_engine.calculate_seat_proration(0, 15, 30)["prorated_charge_usd"] == 0.00
    assert metering_engine.calculate_seat_proration(5, 0, 30)["prorated_charge_usd"] == 0.00


def test_03_nexus_enterprise_core_overage_computation(metering_engine):
    """Verifies detailed multi-dimensional overage billing for Nexus Enterprise Tech."""
    nexus_acc = SAMPLE_ENTERPRISE_ACCOUNTS[0]
    inv = metering_engine.compute_client_overage_invoice(nexus_acc)

    assert inv["client_id"] == "CLIENT-NEXUS-TECH"
    assert inv["tier_code"] == "ENTERPRISE_CORE"
    assert inv["base_subscription_fee_usd"] == 2500.00

    # AST Tokens: 43.5M - 25M = 18.5M @ $4.00/1M = $74.00
    assert inv["ast_tokens"]["consumed"] == 43_500_000
    assert inv["ast_tokens"]["included"] == 25_000_000
    assert inv["ast_tokens"]["overage"] == 18_500_000
    assert inv["ast_tokens"]["charge_usd"] == 74.00

    # Secret Scans: 85k - 50k = 35k @ $0.05/1k = $1.75
    assert inv["secret_scans"]["consumed"] == 85_000
    assert inv["secret_scans"]["included"] == 50_000
    assert inv["secret_scans"]["overage"] == 35_000
    assert inv["secret_scans"]["charge_usd"] == 1.75

    # Compute Hours: 620h - 500h = 120h @ $0.20/h = $24.00
    assert inv["compute_hours"]["consumed"] == 620.0
    assert inv["compute_hours"]["included"] == 500.0
    assert inv["compute_hours"]["overage"] == 120.0
    assert inv["compute_hours"]["charge_usd"] == 24.00

    # Seat Prorations: 5 seats for 15 days = $122.50
    assert inv["seat_prorations"]["total_prorated_charge_usd"] == 122.50

    # Total Overages & Net Invoice: 74 + 1.75 + 24 + 122.50 = $222.25 overage; $2,722.25 net
    assert inv["total_overage_charges_usd"] == 222.25
    assert inv["total_net_invoice_usd"] == 2722.25
    assert inv["stripe_idempotency_key"].startswith("idemp_mtr_")


def test_04_apex_enterprise_scale_overage_computation(metering_engine):
    """Verifies overage billing for Apex Distributed Systems."""
    apex_acc = SAMPLE_ENTERPRISE_ACCOUNTS[1]
    inv = metering_engine.compute_client_overage_invoice(apex_acc)

    assert inv["client_id"] == "CLIENT-APEX-SYSTEMS"
    assert inv["tier_code"] == "ENTERPRISE_SCALE"
    assert inv["base_subscription_fee_usd"] == 6500.00

    # AST Tokens: 92M - 75M = 17M @ $4.00/1M = $68.00
    assert inv["ast_tokens"]["overage"] == 17_000_000
    assert inv["ast_tokens"]["charge_usd"] == 68.00

    # Scans & Compute: within allowance
    assert inv["secret_scans"]["overage"] == 0
    assert inv["secret_scans"]["charge_usd"] == 0.00
    assert inv["compute_hours"]["overage"] == 0.0
    assert inv["compute_hours"]["charge_usd"] == 0.00

    # Total Net Invoice: 6,500 + 68 = $6,568.00
    assert inv["total_overage_charges_usd"] == 68.00
    assert inv["total_net_invoice_usd"] == 6568.00


def test_05_cyber_defense_dedicated_overage_computation(metering_engine):
    """Verifies overage billing for Cyber Defense Aerospace Labs."""
    cyber_acc = SAMPLE_ENTERPRISE_ACCOUNTS[2]
    inv = metering_engine.compute_client_overage_invoice(cyber_acc)

    assert inv["client_id"] == "CLIENT-CYBER-DEFENSE-CORP"
    assert inv["tier_code"] == "ENTERPRISE_DEDICATED"
    assert inv["base_subscription_fee_usd"] == 12500.00

    # AST Tokens: 220M < 250M (within allowance)
    assert inv["ast_tokens"]["overage"] == 0
    assert inv["ast_tokens"]["charge_usd"] == 0.00

    # Secret Scans: 620k - 500k = 120k @ $0.05/1k = $6.00
    assert inv["secret_scans"]["overage"] == 120_000
    assert inv["secret_scans"]["charge_usd"] == 6.00

    # Compute Hours: 5250h - 5000h = 250h @ $0.20/h = $50.00
    assert inv["compute_hours"]["overage"] == 250.0
    assert inv["compute_hours"]["charge_usd"] == 50.00

    # Total Net Invoice: 12,500 + 56 = $12,556.00
    assert inv["total_overage_charges_usd"] == 56.00
    assert inv["total_net_invoice_usd"] == 12556.00


def test_06_stripe_api_payload_synthesis(metering_engine):
    """Verifies Stripe Metered Usage Record and Invoice Items payload synthesis."""
    nexus_acc = SAMPLE_ENTERPRISE_ACCOUNTS[0]
    inv = metering_engine.compute_client_overage_invoice(nexus_acc)
    stripe_payload = metering_engine.synthesize_stripe_api_payloads(inv)

    assert stripe_payload["client_id"] == "CLIENT-NEXUS-TECH"
    assert len(stripe_payload["stripe_usage_records"]) == 2

    # Usage records check
    tokens_rec = stripe_payload["stripe_usage_records"][0]
    assert tokens_rec["endpoint"] == "/v1/subscription_items/si_client-nexus-tech_tokens/usage_records"
    assert tokens_rec["payload"]["quantity"] == 43_500_000
    assert "Idempotency-Key" in tokens_rec["headers"]

    # Invoice item check
    inv_item = stripe_payload["stripe_invoice_item"]
    assert inv_item["endpoint"] == "/v1/invoiceitems"
    assert inv_item["payload"]["customer"] == "cus_client_nexus_tech"
    assert inv_item["payload"]["amount"] == 22225  # $222.25 in cents
    assert inv_item["payload"]["currency"] == "usd"
    assert "Idempotency-Key" in inv_item["headers"]


def test_07_all_monthly_metering_aggregation(metering_engine):
    """Verifies aggregated portfolio monthly billing revenue metrics."""
    summary = metering_engine.process_all_monthly_metering()

    assert summary["total_accounts_processed"] == 3
    assert summary["total_base_subscription_revenue_usd"] == 21500.00
    assert summary["total_token_overage_revenue_usd"] == 142.00
    assert summary["total_scan_overage_revenue_usd"] == 7.75
    assert summary["total_compute_overage_revenue_usd"] == 74.00
    assert summary["total_seat_proration_revenue_usd"] == 122.50
    assert summary["total_usage_overages_revenue_usd"] == 346.25
    assert summary["total_net_billed_revenue_usd"] == 21846.25


def test_08_save_reports_and_brand_anonymity(metering_engine):
    """Verifies report generation and strict 100% Brand Anonymity adherence."""
    paths = metering_engine.save_reports_and_ledger()

    assert os.path.exists(paths["report_path"])
    assert os.path.exists(paths["ledger_path"])

    with open(paths["report_path"], "r", encoding="utf-8") as f:
        content = f.read()

    assert "DevSuperSuite Treasury & Corporate Finance" in content
    assert "cfo@devsupersuite.com" in content
    assert "MONTHLY USAGE METERING & OVERAGE SCORECARD" in content
    assert "Nexus Enterprise Tech" in content

    # Anonymity verification on report
    for token in FORBIDDEN_FOUNDER_TOKENS:
        assert token not in content, f"Forbidden founder token '{token}' exposed in metering report!"

    # Anonymity verification on specification document
    spec_path = os.path.join(SERVICES_DIR, "enterprise_usage_billing_spec.md")
    assert os.path.exists(spec_path)
    with open(spec_path, "r", encoding="utf-8") as f:
        spec_content = f.read()
    for token in FORBIDDEN_FOUNDER_TOKENS:
        assert token not in spec_content, f"Forbidden founder token '{token}' exposed in billing spec!"


def test_09_cli_execution():
    """Verifies Usage Metering CLI commands execution."""
    cmd = [
        sys.executable,
        os.path.join(SERVICES_DIR, "enterprise_usage_metering_engine.py"),
        "--summary",
        "--process-monthly-metering",
        "--audit-overage-invoices",
        "--generate-billing-summary"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "DevSuperSuite Monthly Usage Metering & Overage Summary" in res.stdout
    assert "Total Gross Commercial Invoiced:  $21,846.25 USD" in res.stdout
    assert "AST Token Overages Revenue:       $142.00 USD" in res.stdout
