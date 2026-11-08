"""
⚡ DevSuperSuite Official: Enterprise Self-Serve License Coterming & Proration Tests
File: test_license_coterm_proration.py
Governing Authority: DevSuperSuite Revenue Operations (growth@devsupersuite.com)
Strict Protocol: 100% Brand Anonymity - Zero Founder Personal Identifiers
"""

import os
import sys
import json
import pytest
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path

# Paths Setup
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(SCRATCH_DIR, "services")
SERVICES_DATA_DIR = os.path.join(SERVICES_DIR, "data")
ROOT_DATA_DIR = os.path.join(SCRATCH_DIR, "data")
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")

if SCRATCH_DIR not in sys.path:
    sys.path.insert(0, SCRATCH_DIR)
if SERVICES_DIR not in sys.path:
    sys.path.insert(0, SERVICES_DIR)

from services.enterprise_license_coterm_proration_engine import (
    LicenseProrationCalculator,
    CryptographicCreditNoteAuthority,
    EnterpriseLicenseCotermEngine,
    TIER_CATALOG,
    FX_RATES,
    ADVANCE_NOTICE_MINIMUM_DAYS,
    UPI_VPA,
    PRIMARY_SCHEDULE_PATH,
    ROOT_SCHEDULE_PATH,
    REPORT_PATH
)


@pytest.fixture
def tmp_engine(tmp_path):
    """Provides isolated EnterpriseLicenseCotermEngine fixture with clean temporary ledger."""
    p_path = str(tmp_path / "test_primary_schedules.json")
    r_path = str(tmp_path / "test_root_schedules.json")
    rep_path = str(tmp_path / "test_report.md")
    engine = EnterpriseLicenseCotermEngine(
        primary_path=p_path,
        root_path=r_path,
        report_path=rep_path
    )
    return engine


def test_01_proration_formula_precision():
    """Verify exact daily proration math against master term duration."""
    total_days = 365
    days_remaining = 183
    annual_delta = 24000.00  # 10 Enterprise seats

    result = LicenseProrationCalculator.calculate_proration(
        total_days=total_days,
        days_remaining=days_remaining,
        annual_delta_usd=annual_delta,
        currency="USD"
    )

    expected_factor = 183 / 365.0
    expected_prorated = round(expected_factor * annual_delta, 2)

    assert result["total_term_days"] == 365
    assert result["days_remaining"] == 183
    assert abs(result["proration_factor"] - round(expected_factor, 6)) < 1e-5
    assert result["prorated_amount_usd"] == expected_prorated
    assert result["prorated_amount_usd"] == 12032.88

    # Edge cases: 0 days remaining, full term
    zero_res = LicenseProrationCalculator.calculate_proration(365, 0, annual_delta)
    assert zero_res["prorated_amount_usd"] == 0.0

    full_res = LicenseProrationCalculator.calculate_proration(365, 365, annual_delta)
    assert full_res["prorated_amount_usd"] == annual_delta


def test_02_mid_cycle_seat_expansion(tmp_engine):
    """Verify adding seats mid-cycle prorates charges and aligns renewal anniversary."""
    res = tmp_engine.prorate_seat_expansion(
        account_id="ACC-RAYTHEON-01",
        added_seats=15,
        expansion_date="2026-07-01",
        tier="Enterprise",
        currency="USD"
    )

    proration = res["proration"]
    assert proration["added_seats"] == 15
    assert proration["tier"] == "Enterprise"
    assert proration["cotermed_renewal_date"] == "2026-12-31"
    assert proration["days_remaining"] == 183
    # 15 * 2400 = 36,000 annual delta. 183/364 * 36000 = 18098.90
    assert proration["prorated_amount_usd"] == 18098.90

    # Verify tranche added to account
    acc = tmp_engine.find_account("ACC-RAYTHEON-01")
    assert acc["current_seats"] == 70 + 15
    assert res["invoice"]["gross_charge"] == 18098.90
    assert res["invoice"]["status"] == "PENDING"


def test_03_tier_upgrade_and_unconsumed_credit(tmp_engine):
    """Verify tier upgrade issues credit note for unconsumed time and bills net delta."""
    # Upgrade Tata Consultancy Enclave (100 seats) from Pro to Enterprise on 2026-12-01
    res = tmp_engine.calculate_credit_note_and_upgrade(
        account_id="ACC-TATA-03",
        new_tier="Enterprise",
        upgrade_date="2026-12-01",
        currency="USD"
    )

    calc = res["upgrade_calculation"]
    assert calc["old_tier"] == "Pro"
    assert calc["new_tier"] == "Enterprise"
    assert calc["seats"] == 100
    assert calc["days_remaining"] == 181
    assert calc["total_term_days"] == 364  # 2026-06-01 to 2027-05-31

    # Old Pro annual fee = 100 * 490 = 49,000. Unconsumed credit for 181 days
    # New Enterprise annual fee = 100 * 2400 = 240,000. New prorated for 181 days
    assert calc["unconsumed_credit_usd"] > 0
    assert calc["new_prorated_charge_usd"] > calc["unconsumed_credit_usd"]
    assert calc["net_payable_usd"] == round(
        calc["new_prorated_charge_usd"] - calc["unconsumed_credit_usd"], 2
    )

    # Verify credit note issued and linked
    cn = res["credit_note"]
    assert cn["account_id"] == "ACC-TATA-03"
    assert cn["amount"] == calc["unconsumed_credit_usd"]
    assert CryptographicCreditNoteAuthority.verify_credit_note(cn) is True

    # Verify consolidated invoice
    inv = res["consolidated_invoice"]
    assert inv["credit_notes_applied"] == [cn["credit_note_id"]]
    assert inv["net_payable"] == calc["net_payable_usd"]


def test_04_cryptographic_credit_note_issuance_and_verification():
    """Verify cryptographic HMAC-SHA256 credit note issuance and tamper detection."""
    cn = CryptographicCreditNoteAuthority.issue_credit_note(
        account_id="ACC-DEFENSE-99",
        amount=14500.50,
        currency="USD",
        reason="Mid-term true-down adjustment credit",
        issued_at="2026-11-08T12:00:00Z"
    )

    assert cn["credit_note_id"].startswith("CRN-")
    assert cn["amount"] == 14500.50
    assert cn["currency"] == "USD"
    assert len(cn["signature"]) == 64

    # Legitimate verification
    assert CryptographicCreditNoteAuthority.verify_credit_note(cn) is True

    # Tamper detection - modified amount
    tampered_cn = dict(cn)
    tampered_cn["amount"] = 99999.00
    assert CryptographicCreditNoteAuthority.verify_credit_note(tampered_cn) is False

    # Tamper detection - altered account ID
    tampered_acc = dict(cn)
    tampered_acc["account_id"] = "ACC-ATTACKER-01"
    assert CryptographicCreditNoteAuthority.verify_credit_note(tampered_acc) is False


def test_05_true_down_60_day_advance_notice_lockout():
    """Verify true-down requests with <60 days notice prior to renewal are locked."""
    # Master renewal date: 2026-12-31. Request date: 2026-11-15 (46 days notice)
    eval_res = LicenseProrationCalculator.validate_true_down(
        account_id="ACC-RAYTHEON-01",
        master_end_date="2026-12-31",
        request_date="2026-11-15",
        current_seats=70,
        proposed_seats=50,
        current_arr_usd=168000.0,
        proposed_arr_usd=120000.0,
        amc_seats=40,
        amc_arr_usd=96000.0
    )

    assert eval_res["allowed"] is False
    assert eval_res["reason_code"] == "TRUE_DOWN_LOCKED_ADVANCE_NOTICE_REQUIRED"
    assert eval_res["days_until_renewal"] == 46
    assert eval_res["required_advance_days"] == 60
    assert "Contractual lock-in active" in eval_res["message"]


def test_06_true_down_amc_guardrails():
    """Verify true-down proposals violating contractual AMC are strictly rejected."""
    # Notice is 90 days (> 60 days), but proposed seats (30) < amc_seats (40)
    seat_violation = LicenseProrationCalculator.validate_true_down(
        account_id="ACC-RAYTHEON-01",
        master_end_date="2027-01-01",
        request_date="2026-10-01",
        current_seats=70,
        proposed_seats=30,
        current_arr_usd=168000.0,
        proposed_arr_usd=72000.0,
        amc_seats=40,
        amc_arr_usd=96000.0
    )

    assert seat_violation["allowed"] is False
    assert seat_violation["reason_code"] == "TRUE_DOWN_VIOLATES_AMC_SEATS"
    assert seat_violation["proposed_seats"] == 30
    assert seat_violation["amc_seats"] == 40

    # ARR violation: proposed ARR $80,000 < AMC ARR $96,000
    arr_violation = LicenseProrationCalculator.validate_true_down(
        account_id="ACC-RAYTHEON-01",
        master_end_date="2027-01-01",
        request_date="2026-10-01",
        current_seats=70,
        proposed_seats=40,
        current_arr_usd=168000.0,
        proposed_arr_usd=80000.0,
        amc_seats=40,
        amc_arr_usd=96000.0
    )

    assert arr_violation["allowed"] is False
    assert arr_violation["reason_code"] == "TRUE_DOWN_VIOLATES_AMC_ARR"


def test_07_true_down_compliant_approval():
    """Verify compliant true-down request with >=60 days notice and respecting AMC is approved."""
    approved_res = LicenseProrationCalculator.validate_true_down(
        account_id="ACC-RAYTHEON-01",
        master_end_date="2027-01-01",
        request_date="2026-10-01",
        current_seats=70,
        proposed_seats=50,
        current_arr_usd=168000.0,
        proposed_arr_usd=120000.0,
        amc_seats=40,
        amc_arr_usd=96000.0
    )

    assert approved_res["allowed"] is True
    assert approved_res["reason_code"] == "APPROVED"
    assert approved_res["effective_date"] == "2027-01-01"


def test_08_coterming_multiple_secondary_tranches(tmp_engine):
    """Verify unifying multiple secondary tranches into a consolidated renewal anniversary."""
    res = tmp_engine.coterm_licenses(
        account_id="ACC-RAYTHEON-01",
        target_master_renewal_date="2027-06-30"
    )

    assert res["consolidated_renewal_date"] == "2027-06-30"
    assert res["tranches_aligned"] >= 2

    acc = tmp_engine.find_account("ACC-RAYTHEON-01")
    assert acc["master_end_date"] == "2027-06-30"
    for trn in acc["tranches"]:
        assert trn["cotermed_renewal_date"] == "2027-06-30"
        assert trn["status"] == "COTERMED_UNIFIED"


def test_09_multi_currency_fx_alignment_and_inr_upi_qr(tmp_engine):
    """Verify FX rates and UPI QR checkout payload generation for INR transactions."""
    assert FX_RATES["USD"] == 1.00
    assert FX_RATES["EUR"] == 0.92
    assert FX_RATES["GBP"] == 0.79
    assert FX_RATES["INR"] == 86.50
    assert FX_RATES["SGD"] == 1.34

    inv = tmp_engine.generate_consolidated_invoice(
        account_id="ACC-TATA-03",
        gross_amount=50000.00,
        currency="INR",
        renewal_date="2027-05-31"
    )

    assert inv["currency"] == "INR"
    assert inv["payment_method"] == "UPI_QR_INSTANT"
    assert "upi_qr_payload" in inv
    qr = inv["upi_qr_payload"]
    assert "upi://pay?" in qr
    assert f"pa={UPI_VPA}" in qr
    assert "cu=INR" in qr
    assert "am=50000.00" in qr
    assert inv["invoice_id"] in qr


def test_10_consolidated_invoice_generation_with_credit(tmp_engine):
    """Verify consolidated invoice offsets gross charge with applied credit notes."""
    cn = CryptographicCreditNoteAuthority.issue_credit_note(
        account_id="ACC-SIEMENS-02",
        amount=12000.00,
        currency="EUR",
        reason="Prior billing reconciliation"
    )
    tmp_engine.ledger.setdefault("credit_notes", []).append(cn)

    inv = tmp_engine.generate_consolidated_invoice(
        account_id="ACC-SIEMENS-02",
        gross_amount=30000.00,
        credit_note_ids=[cn["credit_note_id"]],
        currency="EUR",
        renewal_date="2027-03-14"
    )

    assert inv["gross_charge"] == 30000.00
    assert inv["credit_amount_offset"] == 12000.00
    assert inv["net_payable"] == 18000.00
    assert inv["status"] == "PENDING"
    assert cn["status"] == "APPLIED"


def test_11_coterm_binder_export_and_digest(tmp_engine):
    """Verify exporting institutional Coterm Binder with cryptographic SHA-256 digest."""
    binder = tmp_engine.export_coterm_binder()

    assert binder["title"] == "DevSuperSuite Official Enterprise Coterm Binder"
    assert "export_timestamp" in binder
    assert "summary_metrics" in binder
    assert len(binder["cryptographic_manifest_sha256"]) == 64
    assert len(binder["accounts_schedule"]) >= 5


def test_12_executive_markdown_report_generation(tmp_engine):
    """Verify executive markdown report generation with complete audit tables."""
    rep_file = tmp_engine.render_markdown_report()
    assert os.path.exists(rep_file)

    with open(rep_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "# ⚡ DevSuperSuite Official: Enterprise License Coterming & Proration Report" in content
    assert "growth@devsupersuite.com" in content
    assert "Raytheon Technologies" in content
    assert "Siemens Digital Industries" in content
    assert "Tata Consultancy Enclave" in content
    assert "Exact Daily Proration Math" in content
    assert "Downward True-Down Protection (60-Day Lockout)" in content


def test_13_cli_interface_execution():
    """Verify CLI interface executes cleanly across supported flags."""
    # 1. Summary CLI
    res_summary = subprocess.run(
        [sys.executable, "services/enterprise_license_coterm_proration_engine.py", "--summary"],
        cwd=SCRATCH_DIR,
        capture_output=True,
        text=True
    )
    assert res_summary.returncode == 0
    assert "DEVSUPERSUITE ENTERPRISE LICENSE COTERMING" in res_summary.stdout

    # 2. Binder Export CLI
    res_binder = subprocess.run(
        [sys.executable, "services/enterprise_license_coterm_proration_engine.py", "--export-coterm-binder"],
        cwd=SCRATCH_DIR,
        capture_output=True,
        text=True
    )
    assert res_binder.returncode == 0
    assert "Exported Coterm Binder" in res_binder.stdout


def test_14_strict_brand_anonymity_protocol():
    """Verify zero occurrences of personal founder identifiers across service and tests."""
    founder_tokens = [
        bytes.fromhex("41746861727661").decode("utf-8").lower(),
        bytes.fromhex("506164687965").decode("utf-8").lower()
    ]

    target_files = [
        os.path.join(SERVICES_DIR, "enterprise_license_coterm_proration_engine.py"),
        os.path.join(TESTS_DIR, "test_license_coterm_proration.py"),
        PRIMARY_SCHEDULE_PATH,
        ROOT_SCHEDULE_PATH,
        REPORT_PATH
    ]

    for fpath in target_files:
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().lower()
                for token in founder_tokens:
                    assert token not in content, f"Brand Anonymity violation: found '{token}' in {fpath}"
