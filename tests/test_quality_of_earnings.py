"""
⚡ DevSuperSuite Treasury & Corporate Finance - Unit & Integration Test Suite
File: test_quality_of_earnings.py
Target: quality_of_earnings_due_diligence_engine.py (Quality of Earnings Due Diligence & EBITDA Bridge Engine)
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

from quality_of_earnings_due_diligence_engine import (
    QualityOfEarningsDueDiligenceEngine,
    AUDITED_FINANCIAL_INPUTS,
    QOE_NORMALIZATION_ITEMS,
    CUSTOMER_PORTFOLIO_SNAPSHOT,
    QOE_LEDGER_FILE_1,
    QOE_LEDGER_FILE_2,
    DEFAULT_QOE_REPORT_FILE
)

FORBIDDEN_FOUNDER_TOKENS = [
    "Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"
]


@pytest.fixture
def qoe_engine(tmp_path):
    """Initializes Quality of Earnings Engine with isolated test paths."""
    test_report = os.path.join(tmp_path, "test_qoe_binder.md")
    test_ledger_1 = os.path.join(tmp_path, "test_qoe_ledger_1.json")
    test_ledger_2 = os.path.join(tmp_path, "test_qoe_ledger_2.json")
    return QualityOfEarningsDueDiligenceEngine(
        report_path=test_report,
        ledger_path=test_ledger_1
    )


def test_01_ebitda_bridge_calculations(qoe_engine):
    """Verifies GAAP Net Income to Normalized QoE EBITDA bridge and pro-forma run-rate."""
    bridge = qoe_engine.calculate_ebitda_bridge()

    assert bridge["reported_net_income_usd"] == 17568.13
    assert bridge["deductions"]["sovereign_treasury_yield_interest_usd"] == -91.50
    assert bridge["reported_operating_ebit_usd"] == 17476.63
    assert bridge["reported_ebitda_usd"] == 17476.63
    assert bridge["reported_ebitda_margin_pct"] == 52.26

    # Normalization Addbacks
    addbacks = bridge["qoe_normalization_adjustments"]
    assert addbacks["total_addbacks_usd"] == 1350.00
    assert len(addbacks["items"]) == 3

    # Normalized EBITDA & Run-rate
    assert bridge["normalized_qoe_ebitda_usd"] == 18826.63
    assert bridge["normalized_ebitda_margin_pct"] == 56.30
    assert bridge["annualized_ebitda_run_rate_usd"] == 225919.56


def test_02_revenue_waterfall_and_gross_margins(qoe_engine):
    """Verifies ASC 606 revenue disaggregation and gross profit calculations."""
    rev = qoe_engine.calculate_revenue_waterfall()

    comm = rev["commercial_revenue"]
    assert comm["developer_software_licenses_usd"] == 440.00
    assert comm["enterprise_turnkey_implementations_usd"] == 24500.00
    assert comm["recurring_retainer_pods_usd"] == 8500.00
    assert comm["total_commercial_revenue_usd"] == 33440.00

    assert rev["gross_profit_usd"] == 23976.63
    assert rev["gross_margin_pct"] == 71.70


def test_03_net_working_capital_peg(qoe_engine):
    """Verifies Net Working Capital (NWC) peg and negative working capital model dynamics."""
    nwc = qoe_engine.calculate_net_working_capital_peg()

    assert nwc["operating_current_assets_usd"] == 0.00
    assert nwc["operating_current_liabilities_usd"] == 2.90
    assert nwc["actual_net_working_capital_usd"] == -2.90
    assert nwc["target_nwc_peg_usd"] == 0.00
    assert nwc["variance_to_peg_usd"] == -2.90
    assert "DEFICIT_COVERED_BY_CASH" in nwc["nwc_status"] or "SURPLUS" in nwc["nwc_status"]


def test_04_proof_of_cash_reconciliation(qoe_engine):
    """Verifies proof of cash tie-out from bank statements to ASC 606 general ledger ($0.00 variance)."""
    cash = qoe_engine.reconcile_proof_of_cash()

    assert cash["invoiced_asc606_revenue_usd"] == 33440.00
    assert cash["less_gateway_interchange_fees_usd"] == -30.50
    assert cash["expected_net_cash_receipts_usd"] == 33409.50
    assert cash["actual_cleared_bank_deposits_usd"] == 33409.50
    assert cash["discrepancy_variance_usd"] == 0.00
    assert cash["proof_of_cash_verified"] is True
    assert len(cash["bank_cleared_items"]) == 3


def test_05_customer_concentration_limits(qoe_engine):
    """Verifies customer portfolio concentration complies with < 12.0% ARR maximum risk ceiling."""
    conc = qoe_engine.audit_customer_concentration()

    assert conc["total_portfolio_arr_usd"] == 559000.00
    assert conc["concentration_threshold_ceiling_pct"] == 12.00
    assert conc["max_single_customer_concentration_pct"] <= 12.00
    assert conc["max_single_customer_concentration_pct"] == 11.21
    assert conc["is_concentration_compliant"] is True
    assert conc["compliance_status"] == "COMPLIANT_UNCONCENTRATED"

    # Herfindahl-Hirschman Index (HHI < 1,500)
    assert conc["herfindahl_hirschman_index_hhi"] < 1500.0
    assert "UNCONCENTRATED_MARKET" in conc["hhi_classification"]

    for c in conc["customer_breakdown"]:
        assert c["exceeds_12pct_threshold"] is False
        assert c["share_of_arr_pct"] <= 12.00


def test_06_save_reports_and_brand_anonymity(qoe_engine):
    """Verifies report and schedule generation to disk and strict 100% Brand Anonymity adherence."""
    paths = qoe_engine.save_reports_and_ledger()

    assert os.path.exists(paths["report_path"])
    assert os.path.exists(paths["ledger_path_1"])
    assert os.path.exists(paths["ledger_path_2"])

    with open(paths["report_path"], "r", encoding="utf-8") as f:
        content = f.read()

    assert "DevSuperSuite Treasury & Corporate Finance" in content
    assert "cfo@devsupersuite.com" in content
    assert "QUALITY OF EARNINGS (QoE) AUDIT SCORECARD" in content
    assert "18,826.63" in content
    assert "56.30%" in content
    assert "0.00 Discrepancy" in content

    # Anonymity verification on report
    for token in FORBIDDEN_FOUNDER_TOKENS:
        assert token not in content, f"Forbidden founder token '{token}' exposed in QoE report!"

    # Anonymity verification on json ledgers
    with open(paths["ledger_path_1"], "r", encoding="utf-8") as f:
        json_content = f.read()
    for token in FORBIDDEN_FOUNDER_TOKENS:
        assert token not in json_content, f"Forbidden founder token '{token}' exposed in QoE ledger!"


def test_07_cli_execution():
    """Verifies Quality of Earnings CLI flags execution."""
    cmd = [
        sys.executable,
        os.path.join(SERVICES_DIR, "quality_of_earnings_due_diligence_engine.py"),
        "--summary",
        "--generate-qoe-audit",
        "--calculate-ebitda-bridge",
        "--export-qoe-binder",
        "--audit-nwc-peg"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "DevSuperSuite Quality of Earnings (QoE) Due Diligence Summary" in res.stdout
    assert "Normalized QoE EBITDA:           $18,826.63 USD" in res.stdout
    assert "Proof of Cash Discrepancy:       $0.00 USD" in res.stdout
    assert "Max Single Customer Share:       11.21%" in res.stdout
