"""
⚡ DevSuperSuite Official: Enterprise Multi-Currency Dunning & Smart Recovery Tests
File: test_dunning_gateway.py
Governing Authority: DevSuperSuite Revenue Operations (growth@devsupersuite.com)
Strict Protocol: 100% Brand Anonymity - Zero Founder Personal Identifiers
"""

import os
import sys
import json
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

from services.enterprise_dunning_gateway import (
    DunningGraceTokenAuthority,
    EnterpriseDunningGateway,
    RETRY_CADENCE_DAYS,
    LOCALIZED_FALLBACKS,
    DUNNING_SCHEDULES_PATH,
    REPORT_PATH,
)


@pytest.fixture
def test_gateway(tmp_path):
    ledger_file = str(tmp_path / "test_dunning_schedules.json")
    report_file = str(tmp_path / "test_dunning_report.md")
    return EnterpriseDunningGateway(
        ledger_path=ledger_file,
        report_path=report_file
    )


def test_01_smart_retry_cadence_days():
    """Verify smart retry cadence matches optimal 5-step interval (Days 1, 3, 5, 7, 14)."""
    assert RETRY_CADENCE_DAYS == [1, 3, 5, 7, 14]


def test_02_localized_payment_fallbacks():
    """Verify localized payment fallbacks across INR (UPI), EUR (SEPA), USD (ACH), GBP (Bacs)."""
    assert LOCALIZED_FALLBACKS["INR"]["primary_fallback"] == "UPI_DIRECT"
    assert "devsupersuite@icici" in LOCALIZED_FALLBACKS["INR"]["fallback_label"]

    assert LOCALIZED_FALLBACKS["EUR"]["primary_fallback"] == "SEPA_DIRECT_DEBIT"
    assert LOCALIZED_FALLBACKS["USD"]["primary_fallback"] == "ACH_DIRECT_DEBIT"
    assert LOCALIZED_FALLBACKS["GBP"]["primary_fallback"] == "BACS_DIRECT_DEBIT"


def test_03_cryptographic_grace_token_generation():
    """Verify 14-day cryptographic grace token generation and in-app warning banner text."""
    grace = DunningGraceTokenAuthority.generate_grace_token(
        case_id="DUN-TEST-01",
        customer_id="cus_test_01",
        duration_days=14
    )

    assert grace["token"].startswith("DSS-GRACE-14D-")
    assert grace["duration_days"] == 14
    assert "[WARNING]" in grace["in_app_banner"]
    assert "14-day" in grace["in_app_banner"]
    assert "Software binaries remain fully active" in grace["in_app_banner"]


def test_04_create_dunning_case(test_gateway):
    """Verify creating a dunning case schedules 5 smart retries and attaches 14-day grace token."""
    rec = test_gateway.create_dunning_case(
        invoice_id="in_fail_101",
        customer_id="cus_101",
        company_name="Raytheon Space Systems",
        domain="rtx.com",
        billing_email="billing@rtx.com",
        amount_usd=24999.0,
        currency="USD"
    )

    assert rec["case_id"].startswith("DUN-")
    assert rec["company_name"] == "Raytheon Space Systems"
    assert rec["current_status"] == "IN_GRACE_DUNNING"
    assert len(rec["smart_retries"]) == 5
    assert rec["smart_retries"][0]["retry_day"] == 1
    assert rec["smart_retries"][4]["retry_day"] == 14
    assert rec["grace_period"]["token"].startswith("DSS-GRACE-14D-")
    assert rec["localized_fallback"]["primary_fallback"] == "ACH_DIRECT_DEBIT"


def test_05_smart_retry_success_resolution(test_gateway):
    """Verify simulated payment recovery on retry transitions status to RECOVERED_PAID."""
    case = test_gateway.create_dunning_case(
        invoice_id="in_fail_102",
        customer_id="cus_102",
        company_name="Lockheed Martin",
        domain="lockheedmartin.com",
        billing_email="billing@lockheedmartin.com",
        amount_usd=24999.0
    )
    cid = case["case_id"]

    # First retry fails (Day 1)
    res1 = test_gateway.execute_smart_retry(cid, simulate_success=False)
    assert res1["status"] == "RETRY_FAILED"
    assert res1["retry_day"] == 1

    # Second retry succeeds (Day 3)
    res2 = test_gateway.execute_smart_retry(cid, simulate_success=True)
    assert res2["status"] == "RECOVERED_PAID"
    assert res2["retry_day"] == 3

    # Check updated case status
    updated = next(c for c in test_gateway.ledger["dunning_cases"] if c["case_id"] == cid)
    assert updated["current_status"] == "RECOVERED_PAID"
    assert updated["recovery_method"] == "SMART_CARD_RETRY_DAY_3"
    assert updated["resolved_at"] is not None


def test_06_smart_retry_cadence_exhaustion(test_gateway):
    """Verify exhausting all 5 retries marks subscription as SUBSCRIPTION_PAUSED."""
    case = test_gateway.create_dunning_case(
        invoice_id="in_fail_103",
        customer_id="cus_103",
        company_name="Exhausted Corp",
        domain="exhausted.com",
        billing_email="billing@exhausted.com",
        amount_usd=5000.0
    )
    cid = case["case_id"]

    for _ in range(5):
        test_gateway.execute_smart_retry(cid, simulate_success=False)

    updated = next(c for c in test_gateway.ledger["dunning_cases"] if c["case_id"] == cid)
    assert updated["current_status"] == "SUBSCRIPTION_PAUSED"

    # Attempting retry after exhaustion returns CADENCE_EXHAUSTED
    res_ex = test_gateway.execute_smart_retry(cid)
    assert res_ex["status"] == "CADENCE_EXHAUSTED"


def test_07_resolve_case_via_localized_fallback(test_gateway):
    """Verify resolving case via localized fallback (e.g. UPI for India) records settlement."""
    case = test_gateway.create_dunning_case(
        invoice_id="in_fail_104",
        customer_id="cus_104",
        company_name="Tata Consultancy",
        domain="tcs.com",
        billing_email="billing@tcs.com",
        amount_usd=1499.0,
        currency="INR"
    )
    cid = case["case_id"]

    res = test_gateway.resolve_case_via_fallback(cid, payment_reference="UPI-REF-998877")
    assert res["status"] == "RECOVERED_PAID"
    assert res["company_name"] == "Tata Consultancy"
    assert "UPI_DIRECT" in res["recovery_method"]

    updated = next(c for c in test_gateway.ledger["dunning_cases"] if c["case_id"] == cid)
    assert updated["current_status"] == "RECOVERED_PAID"


def test_08_invalid_case_id_handling(test_gateway):
    """Verify KeyError is raised when referencing non-existent dunning case ID."""
    with pytest.raises(KeyError, match="Dunning case 'DUN-UNKNOWN' not found"):
        test_gateway.execute_smart_retry("DUN-UNKNOWN")

    with pytest.raises(KeyError, match="Dunning case 'DUN-UNKNOWN' not found"):
        test_gateway.resolve_case_via_fallback("DUN-UNKNOWN")


def test_09_dunning_recovery_portfolio_audit(test_gateway):
    """Verify audit computes recovery rate, recovered ARR, and benchmark compliance."""
    # 3 cases recovered, 1 paused -> 75% recovery rate
    c1 = test_gateway.create_dunning_case("inv1", "cus1", "C1", "c1.com", "b@c1.com", 10000.0)
    test_gateway.execute_smart_retry(c1["case_id"], simulate_success=True)

    c2 = test_gateway.create_dunning_case("inv2", "cus2", "C2", "c2.com", "b@c2.com", 10000.0)
    test_gateway.resolve_case_via_fallback(c2["case_id"])

    c3 = test_gateway.create_dunning_case("inv3", "cus3", "C3", "c3.com", "b@c3.com", 10000.0)
    test_gateway.execute_smart_retry(c3["case_id"], simulate_success=True)

    c4 = test_gateway.create_dunning_case("inv4", "cus4", "C4", "c4.com", "b@c4.com", 10000.0)
    for _ in range(5):
        test_gateway.execute_smart_retry(c4["case_id"], simulate_success=False)

    audit = test_gateway.audit_dunning_recovery_portfolio()
    assert audit["total_dunning_cases"] == 4
    assert audit["recovered_cases_count"] == 3
    assert audit["paused_cases_count"] == 1
    assert audit["involuntary_churn_recovery_rate_pct"] == 75.0
    assert audit["involuntary_churn_recovery_rate_pct"] >= 74.2
    assert audit["target_benchmark_achieved"] is True
    assert audit["total_recovered_arr_usd"] == 30000.0


def test_10_ledger_persistence_and_reloading(tmp_path):
    """Verify dunning ledger persists to JSON and reloads state accurately."""
    ledger_file = str(tmp_path / "persist_dunning.json")
    gw1 = EnterpriseDunningGateway(ledger_path=ledger_file)

    rec = gw1.create_dunning_case("inv_p", "cus_p", "Persist Co", "persist.com", "b@persist.com", 8000.0)
    assert os.path.exists(ledger_file)

    gw2 = EnterpriseDunningGateway(ledger_path=ledger_file)
    assert len(gw2.ledger["dunning_cases"]) == 1
    assert gw2.ledger["dunning_cases"][0]["case_id"] == rec["case_id"]


def test_11_markdown_report_generation(test_gateway):
    """Verify executive markdown report generation with all required tables and brand headers."""
    case = test_gateway.create_dunning_case("inv_r", "cus_r", "Boeing Defense", "boeing.com", "b@boeing.com", 24999.0)
    test_gateway.execute_smart_retry(case["case_id"], simulate_success=True)

    report_path = test_gateway.render_markdown_report()
    assert os.path.exists(report_path)

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "# ⚡ DevSuperSuite Official: Enterprise Dunning & Smart Recovery Gateway Report" in content
    assert "Involuntary Churn Recovery Rate" in content
    assert "Boeing Defense" in content
    assert "growth@devsupersuite.com" in content


def test_12_cli_interface_execution():
    """Verify all CLI subcommands execute with exit code 0."""
    python_bin = sys.executable
    script_path = os.path.join(SERVICES_DIR, "enterprise_dunning_gateway.py")

    commands = [
        ["--summary"],
        ["--create-case", "--invoice-id", "in_cli_01", "--customer-id", "cus_cli_01", "--company", "Palantir Tech", "--domain", "palantir.com", "--email", "billing@palantir.com", "--amount", "24999.0", "--currency", "USD"],
        ["--execute-retry", "--simulate-success"],
        ["--audit-dunning"],
        ["--export-dunning-report"]
    ]

    for args in commands:
        cmd = [python_bin, script_path] + args
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        assert res.returncode == 0, f"CLI command {cmd} failed with stderr: {res.stderr}"


def test_13_strict_brand_anonymity_compliance():
    """Verify zero personal founder leaks across all Phase 34 assets."""
    forbidden_tokens = [
        bytes.fromhex("41746861727661").decode("utf-8"),
        bytes.fromhex("506164687965").decode("utf-8"),
        bytes.fromhex("39383930343431323933").decode("utf-8"),
    ]

    phase_34_files = [
        Path(SERVICES_DIR) / "enterprise_dunning_gateway.py",
        Path(DATA_DIR) / "enterprise_dunning_schedules.json",
        Path(REPORTS_DIR) / "enterprise_dunning_report.md",
        Path(TESTS_DIR) / "test_dunning_gateway.py",
    ]

    for file_path in phase_34_files:
        assert file_path.exists(), f"File {file_path} must exist"
        content = file_path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token.lower() not in content.lower(), (
                f"Brand anonymity violation: found forbidden token in {file_path}"
            )
