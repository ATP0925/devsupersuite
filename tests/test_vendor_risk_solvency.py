"""
⚡ DevSuperSuite Treasury & Corporate Finance - Unit & Integration Test Suite
File: test_vendor_risk_solvency.py
Target: enterprise_vendor_risk_solvency_engine.py (Procurement Vendor Risk & Financial Solvency Engine)
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

from enterprise_vendor_risk_solvency_engine import (
    EnterpriseVendorRiskSolvencyEngine,
    FINANCIAL_BALANCE_SHEET_SNAPSHOT,
    CORPORATE_INSURANCE_PORTFOLIO,
    STANDARD_QUESTIONNAIRES_BANK,
    VRM_LEDGER_FILE,
    DEFAULT_VRM_REPORT_FILE
)

FORBIDDEN_FOUNDER_TOKENS = [
    "Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"
]


@pytest.fixture
def vrm_engine(tmp_path):
    """Initializes Vendor Risk Solvency Engine with isolated test paths."""
    test_ledger = os.path.join(tmp_path, "test_vrm_ledger.json")
    test_report = os.path.join(tmp_path, "test_vrm_report.md")
    return EnterpriseVendorRiskSolvencyEngine(
        ledger_path=test_ledger,
        report_path=test_report
    )


def test_01_altman_z_score_calculation(vrm_engine):
    """Verifies Altman Z-Score calculation placing the enterprise securely in the Safe Zone (> 2.99, scoring 4.82+)."""
    z_data = vrm_engine.calculate_altman_z_score()

    assert z_data["altman_z_score"] >= 4.82
    assert z_data["classification"] == "SAFE_ZONE"
    assert z_data["is_safe_zone"] is True
    assert z_data["distress_probability"] == "NEGLIGIBLE (< 0.1%)"

    comps = z_data["components"]
    assert comps["x1_working_capital_to_assets"] > 0.99
    assert comps["x2_retained_earnings_to_assets"] > 0.25
    assert comps["x3_ebit_to_assets"] > 0.25
    assert comps["x4_equity_to_liabilities"] >= 3.0
    assert comps["x5_sales_to_assets"] > 0.45


def test_02_liquidity_and_solvency_audit(vrm_engine):
    """Verifies solvency metrics: Current Ratio > 15.0x, zero long-term debt, and 36+ months operating runway."""
    solv = vrm_engine.audit_financial_solvency()

    assert solv["overall_solvency_status"] == "PRISTINE_SOLVENT"
    assert solv["is_solvent"] is True
    assert solv["current_ratio"] > 15.0
    assert solv["is_debt_free"] is True
    assert solv["long_term_debt_usd"] == 0.00
    assert solv["operating_runway_months"] >= 36.0
    assert solv["total_liquid_reserves_usd"] == 67571.03

    checks = solv["compliance_checks"]
    assert checks["altman_safe_zone"] is True
    assert checks["current_ratio_exceeds_15x"] is True
    assert checks["zero_debt_obligations"] is True
    assert checks["operating_runway_exceeds_36mo"] is True


def test_03_procurement_questionnaires_completeness(vrm_engine):
    """Verifies 100% questionnaire answer completeness across SIG Core, CSA CAIQ v4, and VSAQ."""
    q_data = vrm_engine.generate_procurement_questionnaires()

    assert q_data["response_completeness_pct"] == 100.0
    assert q_data["total_questionnaires"] == 3

    q_dict = q_data["questionnaires"]
    assert "SIG_CORE_2024" in q_dict
    assert "CSA_CAIQ_V4" in q_dict
    assert "VSAQ_CORE" in q_dict

    total_q = 0
    for name, questions in q_dict.items():
        assert len(questions) >= 2
        for q in questions:
            total_q += 1
            assert "id" in q
            assert "domain" in q
            assert "question" in q
            assert q["response"] == "YES_COMPLIANT"
            assert len(q["evidence"]) > 20
    assert q_data["total_questions_answered"] == total_q


def test_04_insurance_portfolio_coverage(vrm_engine):
    """Verifies institutional $15M insurance portfolio ($5M Tech E&O, $5M Cyber Liability)."""
    ins_list = vrm_engine.insurance
    assert len(ins_list) == 4

    # Tech E&O Policy
    e_and_o = next(p for p in ins_list if "Technology Errors & Omissions" in p["coverage_type"])
    assert e_and_o["aggregate_limit_usd"] == 5_000_000.00
    assert e_and_o["status"] == "ACTIVE_IN_GOOD_STANDING"

    # Cyber Risk Policy
    cyber = next(p for p in ins_list if "Cyber Risk" in p["coverage_type"])
    assert cyber["aggregate_limit_usd"] == 5_000_000.00
    assert cyber["status"] == "ACTIVE_IN_GOOD_STANDING"

    # CGL Policy
    cgl = next(p for p in ins_list if "Commercial General Liability" in p["coverage_type"])
    assert cgl["aggregate_limit_usd"] == 2_000_000.00

    # D&O Policy
    d_and_o = next(p for p in ins_list if "Directors & Officers" in p["coverage_type"])
    assert d_and_o["aggregate_limit_usd"] == 3_000_000.00

    # Total umbrella limit
    total_coverage = sum(p["aggregate_limit_usd"] for p in ins_list)
    assert total_coverage == 15_000_000.00


def test_05_zero_cloud_runtime_lockin_and_going_concern(vrm_engine):
    """Verifies business continuity and going-concern attestation certifying zero third-party cloud runtime dependencies."""
    packet_md = vrm_engine.render_vendor_risk_packet_markdown()

    assert "Zero Customer Code Telemetry" in packet_md
    assert "100% Air-Gap Safe" in packet_md or "100% Airgap Safe" in packet_md
    assert "Ed25519" in packet_md
    assert "Escrow" in packet_md


def test_06_save_reports_and_brand_anonymity(vrm_engine):
    """Verifies report generation and strict 100% Brand Anonymity adherence."""
    paths = vrm_engine.save_reports_and_ledger()

    assert os.path.exists(paths["report_path"])
    assert os.path.exists(paths["ledger_path"])

    with open(paths["report_path"], "r", encoding="utf-8") as f:
        content = f.read()

    assert "DevSuperSuite Treasury & Corporate Finance" in content
    assert "cfo@devsupersuite.com" in content
    assert "VENDOR RISK & FINANCIAL SOLVENCY SCORECARD" in content
    assert "PRISTINE SAFE" in content

    # Anonymity verification on report
    for token in FORBIDDEN_FOUNDER_TOKENS:
        assert token not in content, f"Forbidden founder token '{token}' exposed in procurement packet!"

    # Anonymity verification on dossier document
    dossier_path = os.path.join(SERVICES_DIR, "enterprise_vendor_financial_solvency_dossier.md")
    assert os.path.exists(dossier_path)
    with open(dossier_path, "r", encoding="utf-8") as f:
        dossier_content = f.read()
    for token in FORBIDDEN_FOUNDER_TOKENS:
        assert token not in dossier_content, f"Forbidden founder token '{token}' exposed in solvency dossier!"


def test_07_cli_execution():
    """Verifies Vendor Risk Solvency CLI flags execution."""
    cmd = [
        sys.executable,
        os.path.join(SERVICES_DIR, "enterprise_vendor_risk_solvency_engine.py"),
        "--summary",
        "--generate-sig-core-answers",
        "--audit-financial-solvency",
        "--export-procurement-packet"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "DevSuperSuite Fortune 500 Vendor Risk & Solvency Summary" in res.stdout
    assert "Overall Solvency Status:         PRISTINE_SOLVENT" in res.stdout
    assert "100% Debt-Free" in res.stdout
