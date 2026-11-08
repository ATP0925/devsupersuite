"""
⚡ DevSuperSuite Treasury & Corporate Finance - Unit & Integration Test Suite
File: test_sox_soc1_controls.py
Target: sox_soc1_internal_controls_engine.py (SOC 1 Type II & SOX 404 Internal Controls Testing Engine)
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

from sox_soc1_internal_controls_engine import (
    SoxSoc1InternalControlsEngine,
    CORE_CONTROLS_CATALOG,
    SOD_ROLE_PERMISSIONS,
    SOC1_LEDGER_FILE,
    DEFAULT_SOC1_REPORT_FILE
)

FORBIDDEN_FOUNDER_TOKENS = [
    "Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"
]


@pytest.fixture
def controls_engine(tmp_path):
    """Initializes SOC 1 / SOX 404 Controls Engine with isolated test paths."""
    test_ledger = os.path.join(tmp_path, "test_soc1_ledger.json")
    test_report = os.path.join(tmp_path, "test_soc1_report.md")
    return SoxSoc1InternalControlsEngine(
        ledger_path=test_ledger,
        report_path=test_report
    )


def test_01_core_controls_catalog_completeness():
    """Verifies that all 25 core ICFR & ITGC controls are defined across 4 control families."""
    assert len(CORE_CONTROLS_CATALOG) == 25

    families = {c["family"] for c in CORE_CONTROLS_CATALOG}
    assert families == {
        "REVENUE_AND_BILLING",
        "CASH_AND_TREASURY",
        "EXPENDITURE_AND_COGS",
        "IT_GENERAL_CONTROLS"
    }

    rev_ctrls = [c for c in CORE_CONTROLS_CATALOG if c["family"] == "REVENUE_AND_BILLING"]
    trs_ctrls = [c for c in CORE_CONTROLS_CATALOG if c["family"] == "CASH_AND_TREASURY"]
    exp_ctrls = [c for c in CORE_CONTROLS_CATALOG if c["family"] == "EXPENDITURE_AND_COGS"]
    itgc_ctrls = [c for c in CORE_CONTROLS_CATALOG if c["family"] == "IT_GENERAL_CONTROLS"]

    assert len(rev_ctrls) == 6
    assert len(trs_ctrls) == 5
    assert len(exp_ctrls) == 4
    assert len(itgc_ctrls) == 10

    # Verify ID sequencing
    rev_ids = [c["control_id"] for c in rev_ctrls]
    assert rev_ids == [f"ICFR-REV-0{i}" for i in range(1, 7)]
    itgc_ids = [c["control_id"] for c in itgc_ctrls]
    assert itgc_ids == [f"ICFR-ITGC-{i:02d}" for i in range(1, 11)]


def test_02_audit_internal_controls_100_percent_pass(controls_engine):
    """Verifies programmatic audit across all 25 controls achieving 100.0% clean opinion."""
    audit = controls_engine.audit_internal_controls()

    assert audit["total_controls_audited"] == 25
    assert audit["controls_passing"] == 25
    assert audit["controls_failing"] == 0
    assert audit["icfr_effectiveness_score_pct"] == 100.0
    assert audit["soc1_statutory_opinion"] == "UNQUALIFIED_OPERATING_EFFECTIVENESS"

    for c in audit["controls_tested"]:
        assert c["exceptions_found"] == 0
        assert c["audit_status"] == "OPERATING_EFFECTIVELY"
        assert c["effectiveness_rate_pct"] == 100.0


def test_03_segregation_of_duties_authorized_roles(controls_engine):
    """Verifies that legitimate role actions are authorized under SoD policies."""
    # Software Engineer can write code and review PRs
    ok, _ = controls_engine.verify_segregation_of_duties("SOFTWARE_ENGINEER", "WRITE_CODE")
    assert ok is True
    ok, _ = controls_engine.verify_segregation_of_duties("SOFTWARE_ENGINEER", "APPROVE_PR")
    assert ok is True

    # Financial Controller can post GL entries and release routine wires
    ok, _ = controls_engine.verify_segregation_of_duties("FINANCIAL_CONTROLLER", "POST_GL_ENTRY")
    assert ok is True
    ok, _ = controls_engine.verify_segregation_of_duties("FINANCIAL_CONTROLLER", "RELEASE_WIRE_UNDER_5K")
    assert ok is True

    # CFO / Treasurer can approve large wires and authorize sweeps
    ok, _ = controls_engine.verify_segregation_of_duties("CFO_TREASURER", "APPROVE_WIRE_OVER_5K")
    assert ok is True
    ok, _ = controls_engine.verify_segregation_of_duties("CFO_TREASURER", "EXECUTE_TREASURY_INVESTMENT")
    assert ok is True

    # Internal Auditor has read-only privileges
    ok, _ = controls_engine.verify_segregation_of_duties("INTERNAL_AUDITOR", "READ_AUDIT_LOGS")
    assert ok is True


def test_04_segregation_of_duties_violation_traps(controls_engine):
    """Verifies that conflicting actions are intercepted and blocked by the SoD policy engine."""
    # Software Engineer cannot post GL entries or release wires
    ok, reason = controls_engine.verify_segregation_of_duties("SOFTWARE_ENGINEER", "POST_GL_ENTRY")
    assert ok is False
    assert "CRITICAL SoD CONFLICT" in reason

    ok, reason = controls_engine.verify_segregation_of_duties("SOFTWARE_ENGINEER", "RELEASE_WIRE_OVER_5K")
    assert ok is False
    assert "CRITICAL SoD CONFLICT" in reason

    ok, reason = controls_engine.verify_segregation_of_duties("SOFTWARE_ENGINEER", "EDIT_VENDOR_BANK_DETAILS")
    assert ok is False
    assert "CRITICAL SoD CONFLICT" in reason

    # Financial Controller cannot write code or deploy production releases
    ok, reason = controls_engine.verify_segregation_of_duties("FINANCIAL_CONTROLLER", "WRITE_CODE")
    assert ok is False
    assert "CRITICAL SoD CONFLICT" in reason

    # Unknown role is denied by default
    ok, reason = controls_engine.verify_segregation_of_duties("UNKNOWN_CONTRACTOR", "WRITE_CODE")
    assert ok is False
    assert "Unauthorized by default" in reason


def test_05_treasury_wire_dual_authorization_rules(controls_engine):
    """Verifies Treasury Control ICFR-TRS-01: Dual-authorization wire release thresholds ($5,000+)."""
    # 1. Routine wire (< $5,000) with single approval
    ok, reason = controls_engine.evaluate_wire_disbursement(3500.00, ["FINANCIAL_CONTROLLER"])
    assert ok is True
    assert "routine single-sign" in reason

    ok, reason = controls_engine.evaluate_wire_disbursement(4999.99, ["CFO_TREASURER"])
    assert ok is True

    # 2. Routine wire (< $5,000) without valid approval -> Blocked
    ok, reason = controls_engine.evaluate_wire_disbursement(3500.00, ["SOFTWARE_ENGINEER"])
    assert ok is False
    assert "rejected" in reason

    # 3. Large wire (>= $5,000) with only Controller -> Blocked
    ok, reason = controls_engine.evaluate_wire_disbursement(8500.00, ["FINANCIAL_CONTROLLER"])
    assert ok is False
    assert "Missing mandatory secondary approval from CFO/Treasurer" in reason

    # 4. Large wire (>= $5,000) with only CFO -> Blocked
    ok, reason = controls_engine.evaluate_wire_disbursement(8500.00, ["CFO_TREASURER"])
    assert ok is False
    assert "Missing mandatory primary approval from Financial Controller" in reason

    # 5. Large wire (>= $5,000) with BOTH Controller and CFO -> Approved
    ok, reason = controls_engine.evaluate_wire_disbursement(8500.00, ["FINANCIAL_CONTROLLER", "CFO_TREASURER"])
    assert ok is True
    assert "Dual-authorization satisfied" in reason

    # 6. Negative amount validation
    ok, reason = controls_engine.evaluate_wire_disbursement(-500.00, ["CFO_TREASURER"])
    assert ok is False
    assert "invalid" in reason


def test_06_revenue_posting_gate_asc606(controls_engine):
    """Verifies Revenue Controls ICFR-REV-01 & ICFR-REV-02 delivery and HMAC gates."""
    # Turnkey Implementation gate
    ok, _ = controls_engine.verify_revenue_posting_gate("TURNKEY_IMPLEMENTATION", has_bilateral_signoff=True)
    assert ok is True
    ok, reason = controls_engine.verify_revenue_posting_gate("TURNKEY_IMPLEMENTATION", has_bilateral_signoff=False)
    assert ok is False
    assert "PREVENTIVE GATE BLOCKED" in reason

    # Developer License gate
    ok, _ = controls_engine.verify_revenue_posting_gate("DEVELOPER_LICENSE", has_valid_webhook_hmac=True)
    assert ok is True
    ok, reason = controls_engine.verify_revenue_posting_gate("DEVELOPER_LICENSE", has_valid_webhook_hmac=False)
    assert ok is False
    assert "PREVENTIVE GATE BLOCKED" in reason

    # Retainer Pod gate
    ok, _ = controls_engine.verify_revenue_posting_gate("RETAINER_POD", is_active_retainer_term=True)
    assert ok is True
    ok, reason = controls_engine.verify_revenue_posting_gate("RETAINER_POD", is_active_retainer_term=False)
    assert ok is False
    assert "Deferred Revenue" in reason


def test_07_general_ledger_merkle_chain_integrity(controls_engine):
    """Verifies ITGC-03: SHA-256 Merkle chain cryptographic sealing and tamper detection."""
    entries = [
        {"entry_id": "JE-2026-001", "date": "2026-11-01", "memo": "Capitalization", "lines": [{"account_code": "1010", "debit": 50000.0}]},
        {"entry_id": "JE-2026-005", "date": "2026-11-06", "memo": "Milestone 1", "lines": [{"account_code": "1100", "debit": 24500.0}]},
        {"entry_id": "JE-2026-012", "date": "2026-11-08", "memo": "ZBA Sweep", "lines": [{"account_code": "1020", "debit": 22183.0}]}
    ]

    seal = controls_engine.compute_general_ledger_merkle_seal(entries)
    assert seal["total_sealed_entries"] == 3
    assert len(seal["root_merkle_hash"]) == 64
    assert seal["tamper_evident"] is True

    # Verification on unmodified ledger -> PASS
    verified, msg = controls_engine.verify_merkle_chain_integrity(seal, entries)
    assert verified is True
    assert "Zero unauthorized tampering detected" in msg

    # Verification on tampered ledger -> FAIL
    tampered_entries = [
        {"entry_id": "JE-2026-001", "date": "2026-11-01", "memo": "Capitalization", "lines": [{"account_code": "1010", "debit": 50001.0}]},  # Tampered $1.00
        {"entry_id": "JE-2026-005", "date": "2026-11-06", "memo": "Milestone 1", "lines": [{"account_code": "1100", "debit": 24500.0}]},
        {"entry_id": "JE-2026-012", "date": "2026-11-08", "memo": "ZBA Sweep", "lines": [{"account_code": "1020", "debit": 22183.0}]}
    ]
    tamper_verified, tamper_msg = controls_engine.verify_merkle_chain_integrity(seal, tampered_entries)
    assert tamper_verified is False
    assert "CRITICAL AUDIT FAILURE" in tamper_msg


def test_08_auditor_walkthrough_workpapers(controls_engine):
    """Verifies SSAE 18 auditor walkthrough workpaper generation across core cycles."""
    walkthroughs = controls_engine.generate_soc1_walkthroughs()

    assert len(walkthroughs) == 4
    wt_ids = [w["walkthrough_id"] for w in walkthroughs]
    assert wt_ids == ["WT-REV-01", "WT-TRS-01", "WT-EXP-01", "WT-ITGC-01"]

    for wt in walkthroughs:
        assert len(wt["walkthrough_steps"]) >= 4
        assert "PASSED" in wt["auditor_verification_result"]


def test_09_save_reports_and_brand_anonymity(controls_engine):
    """Verifies report generation and strict 100% Brand Anonymity adherence."""
    paths = controls_engine.save_reports_and_ledger()

    assert os.path.exists(paths["report_path"])
    assert os.path.exists(paths["ledger_path"])

    with open(paths["report_path"], "r", encoding="utf-8") as f:
        content = f.read()

    assert "DevSuperSuite Treasury & Corporate Finance" in content
    assert "cfo@devsupersuite.com" in content
    assert "SOC 1 TYPE II / SOX 404 AUDIT SCORECARD" in content
    assert "UNQUALIFIED OPINION" in content

    # Anonymity verification on report
    for token in FORBIDDEN_FOUNDER_TOKENS:
        assert token not in content, f"Forbidden founder token '{token}' exposed in SOC 1 report!"

    # Anonymity verification on controls matrix documentation
    matrix_file = os.path.join(SERVICES_DIR, "sox_soc1_internal_controls_matrix.md")
    assert os.path.exists(matrix_file)
    with open(matrix_file, "r", encoding="utf-8") as f:
        matrix_content = f.read()
    for token in FORBIDDEN_FOUNDER_TOKENS:
        assert token not in matrix_content, f"Forbidden founder token '{token}' exposed in controls matrix!"


def test_10_cli_execution():
    """Verifies SOC 1 / SOX 404 CLI flags execution."""
    cmd = [
        sys.executable,
        os.path.join(SERVICES_DIR, "sox_soc1_internal_controls_engine.py"),
        "--summary",
        "--audit-internal-controls",
        "--generate-soc1-walkthroughs",
        "--verify-segregation-of-duties"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "DevSuperSuite SOC 1 Type II & SOX 404 Executive Controls Summary" in res.stdout
    assert "UNQUALIFIED_OPERATING_EFFECTIVENESS" in res.stdout
    assert "Cryptographic Segregation of Duties (SoD) Policy Verification" in res.stdout
