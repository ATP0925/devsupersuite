"""
⚡ DevSuperSuite Treasury & Corporate Finance - Unit & Integration Test Suite
File: test_general_ledger_audit.py
Target: general_ledger_audit_engine.py (General Ledger Double-Entry Audit Defense & Financial Disclosure Engine)
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

from general_ledger_audit_engine import (
    GeneralLedgerAuditEngine,
    CHART_OF_ACCOUNTS,
    STANDARD_JOURNAL_ENTRIES,
    GL_LEDGER_FILE,
    DEFAULT_GL_REPORT_FILE
)

FORBIDDEN_FOUNDER_TOKENS = [
    "Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"
]


@pytest.fixture
def gl_engine(tmp_path):
    """Initializes General Ledger Audit Engine with isolated test paths."""
    test_ledger = os.path.join(tmp_path, "test_gl_ledger.json")
    test_report = os.path.join(tmp_path, "test_gl_report.md")
    return GeneralLedgerAuditEngine(
        ledger_path=test_ledger,
        report_path=test_report
    )


def test_01_chart_of_accounts_structure():
    """Verifies institutional 4-digit Chart of Accounts (COA) specifications."""
    assert len(CHART_OF_ACCOUNTS) >= 20
    required_codes = ["1010", "1020", "1100", "2010", "2300", "3010", "3020", "4010", "4020", "4030", "5010", "6010"]
    for code in required_codes:
        assert code in CHART_OF_ACCOUNTS
        assert "name" in CHART_OF_ACCOUNTS[code]
        assert "category" in CHART_OF_ACCOUNTS[code]
        assert "statement" in CHART_OF_ACCOUNTS[code]
        assert CHART_OF_ACCOUNTS[code]["statement"] in ("BALANCE_SHEET", "INCOME_STATEMENT")


def test_02_standard_journal_entries_invariants():
    """Verifies every operational journal entry adheres to debits == credits invariance."""
    assert len(STANDARD_JOURNAL_ENTRIES) == 14
    for je in STANDARD_JOURNAL_ENTRIES:
        total_debits = sum(line.get("debit", 0.0) for line in je["lines"])
        total_credits = sum(line.get("credit", 0.0) for line in je["lines"])
        diff = round(abs(total_debits - total_credits), 2)
        assert diff == 0.0, f"Entry {je['entry_id']} unbalanced: Debits={total_debits}, Credits={total_credits}"


def test_03_trial_balance_reconciliation(gl_engine):
    """Verifies formal Trial Balance ledger debit and credit equilibrium."""
    rec = gl_engine.reconcile_general_ledger()

    assert rec["total_entries_count"] == 14
    assert rec["trial_balance_balanced"] is True
    assert rec["trial_balance_discrepancy"] == 0.0
    assert rec["trial_balance_debits"] == rec["trial_balance_credits"]
    assert rec["trial_balance_debits"] > 50000.00
    assert all(entry["balanced"] for entry in rec["journal_audit"])


def test_04_income_statement_revenue_and_margins(gl_engine):
    """Verifies GAAP Statement of Operations (Income Statement) calculations and margins."""
    stmts = gl_engine.generate_financial_statements()
    inc = stmts["income_statement"]

    # Revenue
    rev = inc["commercial_revenue"]
    assert rev["software_licenses_usd"] == 440.00
    assert rev["turnkey_implementations_usd"] == 24500.00
    assert rev["recurring_retainer_pods_usd"] == 8500.00
    assert rev["total_commercial_revenue_usd"] == 33440.00

    # COGS & Gross Profit
    cogs = inc["cogs"]
    assert cogs["total_cogs_usd"] == pytest.approx(9463.37, abs=0.05)
    assert inc["gross_profit_usd"] == pytest.approx(23976.63, abs=0.05)
    assert inc["gross_margin_pct"] == pytest.approx(71.70, abs=0.2)

    # OpEx & Net Operating Income
    opex = inc["opex"]
    assert opex["total_opex_usd"] == 6500.00
    assert inc["other_income"]["sovereign_treasury_yield_usd"] == 91.50
    assert inc["operating_income_ebit_usd"] == pytest.approx(17476.63, abs=0.05)
    assert inc["net_income_usd"] == pytest.approx(17568.13, abs=0.05)
    assert inc["net_margin_pct"] > 50.0  # > 50% net operating margin


def test_05_balance_sheet_equilibrium(gl_engine):
    """Verifies Fundamental Balance Sheet Equation: Assets == Liabilities + Shareholders' Equity."""
    stmts = gl_engine.generate_financial_statements()
    bs = stmts["balance_sheet"]

    assert bs["balanced"] is True
    assert bs["discrepancy"] == 0.0
    assert bs["assets"]["total_assets_usd"] == pytest.approx(67571.03, abs=0.05)
    assert bs["liabilities"]["total_liabilities_usd"] == pytest.approx(2.90, abs=0.05)
    assert bs["liabilities"]["long_term_debt_usd"] == 0.00  # 100% Debt-Free
    assert bs["equity"]["total_shareholders_equity_usd"] == pytest.approx(67568.13, abs=0.05)
    assert bs["total_liabilities_and_equity_usd"] == bs["assets"]["total_assets_usd"]


def test_06_cash_flow_statement_reconciliation(gl_engine):
    """Verifies Statement of Cash Flows reconciles with Balance Sheet cash & cash equivalents."""
    stmts = gl_engine.generate_financial_statements()
    cf = stmts["cash_flow_statement"]
    bs = stmts["balance_sheet"]

    assert cf["reconciled_with_balance_sheet"] is True
    assert cf["ending_cash_and_cash_equivalents_usd"] == bs["assets"]["cash_and_cash_equivalents_usd"]
    assert cf["operating_activities"]["net_cash_from_operating_activities_usd"] > 0
    assert cf["investing_activities"]["purchases_of_sovereign_treasuries_usd"] < 0
    assert cf["financing_activities"]["proceeds_from_equity_issuance_usd"] == 50000.00


def test_07_gaap_invariants_auditor(gl_engine):
    """Verifies automated GAAP / IFRS mathematical accounting invariant auditor."""
    inv = gl_engine.audit_gaap_invariants()

    assert inv["all_invariants_satisfied"] is True
    assert inv["invariant_1_journal_entries_balanced"]["status"] == "PASS"
    assert len(inv["invariant_1_journal_entries_balanced"]["failed_entries"]) == 0
    assert inv["invariant_2_trial_balance_equality"]["status"] == "PASS"
    assert inv["invariant_2_trial_balance_equality"]["discrepancy"] == 0.0
    assert inv["invariant_3_balance_sheet_equation"]["status"] == "PASS"
    assert inv["invariant_3_balance_sheet_equation"]["discrepancy"] == 0.0
    assert inv["invariant_4_cash_flow_reconciliation"]["status"] == "PASS"


def test_08_big4_audit_readiness_score(gl_engine):
    """Verifies Big-4 statutory audit readiness evaluation and clean opinion issuance."""
    readiness = gl_engine.compute_audit_readiness_score()

    assert readiness["audit_readiness_score_pct"] == 100.0
    assert readiness["statutory_audit_opinion"] == "UNQUALIFIED_CLEAN_OPINION_READY"
    assert len(readiness["workpapers"]) == 7
    workpaper_ids = [wp["wp_id"] for wp in readiness["workpapers"]]
    assert workpaper_ids == ["WP-100", "WP-200", "WP-300", "WP-400", "WP-500", "WP-600", "WP-700"]
    for wp in readiness["workpapers"]:
        assert wp["score"] == 100.0


def test_09_unbalanced_entry_detection(tmp_path):
    """Verifies that unbalanced fraudulent or erroneous journal entries are caught and flagged."""
    unbalanced_entries = [
        {
            "entry_id": "JE-MALFORMED-001",
            "date": "2026-11-09",
            "memo": "Erroneous unbalanced entry",
            "lines": [
                {"account_code": "1010", "debit": 1000.00, "credit": 0.00},
                {"account_code": "4010", "debit": 0.00, "credit": 900.00}  # $100 discrepancy
            ]
        }
    ]
    engine_broken = GeneralLedgerAuditEngine(
        ledger_path=os.path.join(tmp_path, "broken_gl.json"),
        report_path=os.path.join(tmp_path, "broken_rep.md"),
        entries=unbalanced_entries
    )

    rec = engine_broken.reconcile_general_ledger()
    assert rec["trial_balance_balanced"] is False
    assert rec["trial_balance_discrepancy"] == 100.00

    inv = engine_broken.audit_gaap_invariants()
    assert inv["all_invariants_satisfied"] is False
    assert inv["invariant_1_journal_entries_balanced"]["status"] == "FAIL"
    assert "JE-MALFORMED-001" in inv["invariant_1_journal_entries_balanced"]["failed_entries"]

    readiness = engine_broken.compute_audit_readiness_score()
    assert readiness["audit_readiness_score_pct"] < 100.0
    assert readiness["statutory_audit_opinion"] == "QUALIFIED_DISCREPANCY_DETECTED"


def test_10_save_reports_and_brand_anonymity(gl_engine):
    """Verifies saving audit packets to disk and strict 100% Brand Anonymity adherence."""
    paths = gl_engine.save_reports_and_ledger()

    assert os.path.exists(paths["report_path"])
    assert os.path.exists(paths["ledger_path"])

    with open(paths["report_path"], "r", encoding="utf-8") as f:
        content = f.read()

    assert "DevSuperSuite Treasury & Corporate Finance" in content
    assert "cfo@devsupersuite.com" in content
    assert "STATUTORY AUDIT READINESS SCORECARD" in content
    assert "UNQUALIFIED OPINION" in content

    # Strict anonymity check
    for token in FORBIDDEN_FOUNDER_TOKENS:
        assert token not in content, f"Forbidden founder token '{token}' exposed in audit markdown report!"

    # Also verify statutory_audit_defense_dossier.md anonymity
    dossier_path = os.path.join(SERVICES_DIR, "statutory_audit_defense_dossier.md")
    assert os.path.exists(dossier_path)
    with open(dossier_path, "r", encoding="utf-8") as f:
        dossier_content = f.read()
    for token in FORBIDDEN_FOUNDER_TOKENS:
        assert token not in dossier_content, f"Forbidden founder token '{token}' exposed in audit dossier!"


def test_11_cli_execution():
    """Verifies General Ledger CLI flags execution."""
    cmd = [
        sys.executable,
        os.path.join(SERVICES_DIR, "general_ledger_audit_engine.py"),
        "--summary",
        "--generate-financial-statements",
        "--reconcile-general-ledger",
        "--audit-gaap-invariants"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "DevSuperSuite GAAP / IFRS Double-Entry Accounting Audit Summary" in res.stdout
    assert "UNQUALIFIED_CLEAN_OPINION_READY" in res.stdout
    assert "PASS ($0.00 Discrepancy)" in res.stdout
