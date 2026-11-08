"""
⚡ DevSuperSuite Official: Enterprise Stripe Usage-Based Billing & Metered Invoicing Tests
File: test_stripe_usage_billing.py
Governing Authority: DevSuperSuite Revenue Operations (growth@devsupersuite.com)
Strict Protocol: 100% Brand Anonymity - Zero Founder Personal Identifiers
"""

import os
import sys
import json
import hmac
import hashlib
import pytest
import subprocess
from pathlib import Path

# Paths Setup
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(SCRATCH_DIR, "services")
DATA_DIR = os.path.join(SCRATCH_DIR, "data")
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")

if SCRATCH_DIR not in sys.path:
    sys.path.insert(0, SCRATCH_DIR)
if SERVICES_DIR not in sys.path:
    sys.path.insert(0, SERVICES_DIR)

from services.enterprise_stripe_usage_billing_gateway import (
    StripeMeteredUsageCalculator,
    EnterpriseStripeUsageBillingGateway,
    METERED_BILLING_TIERS,
    WEBHOOK_SECRET,
    LEDGER_PATH,
    REPORT_PATH,
)


@pytest.fixture
def test_gateway(tmp_path):
    ledger_file = str(tmp_path / "test_stripe_ledger.json")
    report_file = str(tmp_path / "test_stripe_report.md")
    return EnterpriseStripeUsageBillingGateway(
        ledger_path=ledger_file,
        report_path=report_file,
        webhook_secret="test_whsec_secret_key"
    )


def test_01_metered_billing_tiers_configuration():
    """Verify standard tier parameters across DEVELOPER_FREE, TEAM_PRO, and ENTERPRISE_UNLIMITED."""
    free = METERED_BILLING_TIERS["DEVELOPER_FREE"]
    assert free["base_fee_usd"] == 0.0
    assert free["included_ast_queries"] == 10000
    assert free["hard_cap_enforced"] is True

    pro = METERED_BILLING_TIERS["TEAM_PRO"]
    assert pro["base_fee_usd"] == 29.0
    assert pro["included_ast_queries"] == 100000
    assert pro["overage_ast_query_usd"] == 0.001
    assert pro["hard_cap_enforced"] is False

    ent = METERED_BILLING_TIERS["ENTERPRISE_UNLIMITED"]
    assert ent["base_fee_usd"] == 499.0
    assert ent["included_ast_queries"] == 1000000
    assert ent["overage_ast_query_usd"] == 0.0005


def test_02_usage_overage_calculator_team_pro():
    """Verify Team Pro overage calculation for AST queries, entropy checks, and voice minutes."""
    bill = StripeMeteredUsageCalculator.calculate_monthly_bill(
        tier_id="TEAM_PRO",
        ast_queries_count=150000,   # 50k overage * 0.001 = $50.00
        entropy_checks_count=70000, # 20k overage * 0.0005 = $10.00
        voice_minutes_count=600     # 100 overage * 0.02 = $2.00
    )

    assert bill["base_fee_usd"] == 29.0
    assert bill["metrics"]["ast_queries"]["charge_usd"] == 50.0
    assert bill["metrics"]["entropy_checks"]["charge_usd"] == 10.0
    assert bill["metrics"]["voice_minutes"]["charge_usd"] == 2.0
    assert bill["total_overage_usd"] == 62.0
    assert bill["total_invoice_usd"] == 91.0  # 29 + 62


def test_03_usage_overage_calculator_developer_free_hard_cap():
    """Verify Developer Free tier enforces hard cap and incurs zero overage charges."""
    bill = StripeMeteredUsageCalculator.calculate_monthly_bill(
        tier_id="DEVELOPER_FREE",
        ast_queries_count=50000,
        entropy_checks_count=20000,
        voice_minutes_count=200
    )

    assert bill["base_fee_usd"] == 0.0
    assert bill["total_overage_usd"] == 0.0
    assert bill["total_invoice_usd"] == 0.0


def test_04_create_metered_customer(test_gateway):
    """Verify creating customer creates customer_id, subscription_id, and initialized usage counters."""
    cust = test_gateway.create_metered_customer(
        company_name="Palantir Technologies",
        domain="palantir.com",
        billing_email="billing@palantir.com",
        tier_id="ENTERPRISE_UNLIMITED"
    )

    assert cust["customer_id"].startswith("cus_dss_")
    assert cust["subscription_id"].startswith("sub_dss_")
    assert cust["company_name"] == "Palantir Technologies"
    assert cust["tier_id"] == "ENTERPRISE_UNLIMITED"
    assert cust["status"] == "ACTIVE"
    assert cust["aggregated_usage"]["ast_queries"] == 0


def test_05_metered_usage_record_ingestion(test_gateway):
    """Verify ingesting usage updates cumulative customer metric counters."""
    cust = test_gateway.create_metered_customer("Datadog", "datadoghq.com", "billing@datadoghq.com")
    cid = cust["customer_id"]

    res1 = test_gateway.ingest_metered_usage_record(cid, "ast_queries", 50000)
    assert res1["status"] == "INGESTED_SUCCESS"
    assert res1["new_cumulative_total"] == 50000

    res2 = test_gateway.ingest_metered_usage_record(cid, "ast_queries", 25000)
    assert res2["status"] == "INGESTED_SUCCESS"
    assert res2["new_cumulative_total"] == 75000


def test_06_idempotent_usage_deduplication(test_gateway):
    """Verify duplicate idempotency keys are skipped without duplicate counting."""
    cust = test_gateway.create_metered_customer("Stripe Labs", "stripe.com", "billing@stripe.com")
    cid = cust["customer_id"]

    res1 = test_gateway.ingest_metered_usage_record(cid, "entropy_checks", 10000, idempotency_key="idem_test_101")
    assert res1["status"] == "INGESTED_SUCCESS"

    # Ingest duplicate
    res2 = test_gateway.ingest_metered_usage_record(cid, "entropy_checks", 10000, idempotency_key="idem_test_101")
    assert res2["status"] == "IDEMPOTENT_SKIPPED"

    # Counter should remain 10,000
    assert cust["aggregated_usage"]["entropy_checks"] == 10000


def test_07_invalid_customer_or_metric_handling(test_gateway):
    """Verify KeyError on unknown customer and ValueError on invalid metric name."""
    with pytest.raises(KeyError, match="Customer 'cus_unknown' not found"):
        test_gateway.ingest_metered_usage_record("cus_unknown", "ast_queries", 100)

    cust = test_gateway.create_metered_customer("Snowflake", "snowflake.com", "billing@snowflake.com")
    with pytest.raises(ValueError, match="Invalid metric 'invalid_metric'"):
        test_gateway.ingest_metered_usage_record(cust["customer_id"], "invalid_metric", 100)


def test_08_monthly_invoice_generation(test_gateway):
    """Verify invoice finalization generates line item breakdown and total calculation."""
    cust = test_gateway.create_metered_customer("Lockheed Martin", "lockheedmartin.com", "billing@lockheedmartin.com", "TEAM_PRO")
    cid = cust["customer_id"]

    test_gateway.ingest_metered_usage_record(cid, "ast_queries", 120000)  # 20k overage = $20
    test_gateway.ingest_metered_usage_record(cid, "voice_minutes", 600)   # 100 overage = $2

    inv = test_gateway.generate_monthly_invoice(cid)
    assert inv["invoice_id"].startswith("in_dss_")
    assert inv["customer_id"] == cid
    assert inv["base_fee_usd"] == 29.0
    assert inv["total_overage_usd"] == 22.0
    assert inv["total_invoice_usd"] == 51.0
    assert inv["status"] == "FINALIZED"


def test_09_stripe_webhook_processing_and_hmac_verification(test_gateway):
    """Verify Stripe webhook processing verifies HMAC signature and updates invoice status to PAID."""
    cust = test_gateway.create_metered_customer("CrowdStrike", "crowdstrike.com", "billing@crowdstrike.com")
    inv = test_gateway.generate_monthly_invoice(cust["customer_id"])
    inv_id = inv["invoice_id"]

    payload = {"id": "evt_test_hmac_01", "invoice_id": inv_id}
    payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
    valid_sig = hmac.new("test_whsec_secret_key".encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    res = test_gateway.process_stripe_webhook(
        event_type="invoice.payment_succeeded",
        event_payload=payload,
        signature_header=valid_sig
    )

    assert res["status"] == "PROCESSED"
    assert res["handled_status"] == "INVOICE_MARKED_PAID"
    assert res["hmac_verified"] is True

    # Check invoice status transitioned to PAID
    updated_inv = next(i for i in test_gateway.ledger["invoices"] if i["invoice_id"] == inv_id)
    assert updated_inv["status"] == "PAID"


def test_10_webhook_invalid_signature_rejection(test_gateway):
    """Verify invalid HMAC webhook signature raises ValueError."""
    payload = {"id": "evt_tampered", "invoice_id": "in_test"}
    with pytest.raises(ValueError, match="HMAC signature verification failed"):
        test_gateway.process_stripe_webhook(
            event_type="invoice.payment_succeeded",
            event_payload=payload,
            signature_header="bad_signature_hex"
        )


def test_11_audit_and_report_generation(test_gateway):
    """Verify portfolio audit and executive markdown report generation."""
    c1 = test_gateway.create_metered_customer("Raytheon", "rtx.com", "billing@rtx.com", "TEAM_PRO")
    test_gateway.ingest_metered_usage_record(c1["customer_id"], "ast_queries", 110000)
    inv1 = test_gateway.generate_monthly_invoice(c1["customer_id"])

    audit = test_gateway.audit_metered_billing_portfolio()
    assert audit["total_customers"] == 1
    assert audit["total_invoices_generated"] == 1
    assert audit["total_invoiced_usd"] == inv1["total_invoice_usd"]
    assert audit["total_overages_billed_usd"] == inv1["total_overage_usd"]

    report_path = test_gateway.render_markdown_report()
    assert os.path.exists(report_path)
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "# ⚡ DevSuperSuite Official: Stripe Usage-Based Billing & Metered Invoicing Report" in content
    assert "Raytheon" in content
    assert "TEAM_PRO" in content
    assert "growth@devsupersuite.com" in content


def test_12_cli_interface_execution():
    """Verify all CLI subcommands execute with exit code 0."""
    python_bin = sys.executable
    script_path = os.path.join(SERVICES_DIR, "enterprise_stripe_usage_billing_gateway.py")

    commands = [
        ["--summary"],
        ["--create-customer", "--company", "Booz Allen Hamilton", "--domain", "boozallen.com", "--email", "billing@boozallen.com", "--tier", "TEAM_PRO"],
        ["--ingest-usage", "--metric", "ast_queries", "--quantity", "120000"],
        ["--generate-invoice"],
        ["--simulate-webhook", "--event-type", "invoice.payment_succeeded"],
        ["--audit-billing"],
        ["--export-billing-report"]
    ]

    for args in commands:
        cmd = [python_bin, script_path] + args
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        assert res.returncode == 0, f"CLI command {cmd} failed with stderr: {res.stderr}"


def test_13_strict_brand_anonymity_compliance():
    """Verify zero personal founder leaks across all Phase 32 assets."""
    forbidden_tokens = [
        bytes.fromhex("41746861727661").decode("utf-8"),
        bytes.fromhex("506164687965").decode("utf-8"),
        bytes.fromhex("39383930343431323933").decode("utf-8"),
    ]

    phase_32_files = [
        Path(SERVICES_DIR) / "enterprise_stripe_usage_billing_gateway.py",
        Path(DATA_DIR) / "stripe_usage_billing_ledger.json",
        Path(REPORTS_DIR) / "stripe_usage_billing_report.md",
        Path(TESTS_DIR) / "test_stripe_usage_billing.py",
    ]

    for file_path in phase_32_files:
        assert file_path.exists(), f"File {file_path} must exist"
        content = file_path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token.lower() not in content.lower(), (
                f"Brand anonymity violation: found forbidden token in {file_path}"
            )
