"""
⚡ DevSuperSuite Official: Enterprise ABM Executive Outbound Cadence Tests
File: test_enterprise_abm_cadence.py
Governing Authority: DevSuperSuite Enterprise Solutions Directorate (enterprise@devsupersuite.com)
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
MARKETING_DIR = os.path.join(SCRATCH_DIR, "marketing")
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")

if SCRATCH_DIR not in sys.path:
    sys.path.insert(0, SCRATCH_DIR)
if SERVICES_DIR not in sys.path:
    sys.path.insert(0, SERVICES_DIR)

from services.enterprise_abm_cadence_engine import (
    SpamTriggerHeuristicScanner,
    ExecutiveOutreachCadenceManager,
    DEFAULT_TEMPLATES_PATH,
    REPORT_PATH,
    PLAYBOOK_PATH,
    SPAM_TRIGGER_TERMS,
)


@pytest.fixture
def cadence_manager():
    return ExecutiveOutreachCadenceManager(DEFAULT_TEMPLATES_PATH)


def test_01_campaign_templates_integrity(cadence_manager):
    """Verify campaign templates database contains 15 accounts with 4 touches each (60 total touches)."""
    accounts = cadence_manager.accounts
    assert len(accounts) >= 15, f"Expected at least 15 accounts, found {len(accounts)}"

    for acct in accounts:
        assert "account_id" in acct
        assert "company_name" in acct
        assert "domain" in acct
        assert "target_executive" in acct
        assert "title" in acct["target_executive"]
        assert "primary_stack" in acct and len(acct["primary_stack"]) > 0
        assert "target_tier" in acct

        touches = acct.get("touches", [])
        assert len(touches) == 4, f"Account {acct['company_name']} must have exactly 4 touches"
        for t in touches:
            assert "touch_number" in t
            assert "subject" in t and len(t["subject"]) > 10
            assert "body" in t and len(t["body"]) > 50


def test_02_spam_heuristic_scanner_clean_content():
    """Verify scanner confirms clean executive outreach text with spam score < 2.0%."""
    clean_sample = (
        "Subject: Slashing C++ AST context bloat across Raytheon defense systems\n\n"
        "Hi team,\n"
        "Raytheon's defense monorepos demand rigorous software integrity. "
        "DevSuperSuite executes locally via WebAssembly, slicing 83.5% of non-essential AST tokens in < 18ms. "
        "Zero source code or telemetry touches external servers.\n"
        "Would 10 minutes Thursday work to review our offline C++ AST benchmark report?"
    )
    res = SpamTriggerHeuristicScanner.scan_content(clean_sample)
    assert res["is_deliverable"] is True
    assert res["spam_score_pct"] < 2.0
    assert res["status"] == "DELIVERABLE_INBOX_PASS"
    assert len(res["matched_spam_terms"]) == 0


def test_03_spam_heuristic_scanner_violating_content():
    """Verify scanner flags content with known high-risk spam triggers, excessive capitalization, and exclamation."""
    spam_sample = (
        "Subject: URGENT WINNER CONGRATULATIONS YOU WON FREE GIFT 100% FREE!!!\n\n"
        "ACT NOW TO CLAIM YOUR GUARANTEED INCOME AND MAKE MONEY INSTANTLY! "
        "NO CATCH! NO CREDIT CARD REQUIRED! INSTANT WEALTH AWAITS YOU!!!"
    )
    res = SpamTriggerHeuristicScanner.scan_content(spam_sample)
    assert res["is_deliverable"] is False
    assert res["spam_score_pct"] >= 2.0
    assert res["status"] == "SPAM_RISK_WARNING"
    assert len(res["matched_spam_terms"]) > 0


def test_04_touch_theme_progression_across_accounts(cadence_manager):
    """Verify that all accounts follow the 4-touch thematic cadence."""
    for acct in cadence_manager.accounts:
        t1, t2, t3, t4 = acct["touches"]

        # Touch 1: Context bloat & token slicing
        t1_text = (t1["subject"] + " " + t1["body"]).lower()
        assert "context" in t1_text or "token" in t1_text or "ast" in t1_text

        # Touch 2: AgentShield & Shannon entropy / registers
        t2_text = (t2["subject"] + " " + t2["body"]).lower()
        assert "agentshield" in t2_text or "entropy" in t2_text or "invariant" in t2_text

        # Touch 3: Compliance (FIPS 140-3, SOC 2, or OpenVEX)
        t3_text = (t3["subject"] + " " + t3["body"]).lower()
        assert "soc 2" in t3_text or "fips" in t3_text or "compliance" in t3_text or "openvex" in t3_text

        # Touch 4: 30-Day Airgap POC & Mutual Action Plan (MAP)
        t4_text = (t4["subject"] + " " + t4["body"]).lower()
        assert "mutual action plan" in t4_text or "map" in t4_text or "poc" in t4_text


def test_05_account_cadence_lookup_by_id_and_name(cadence_manager):
    """Verify account lookup by account_id and company_name."""
    # Lookup by ID
    acct_rtx = cadence_manager.get_account_cadence("ACC-RTX-01")
    assert acct_rtx is not None
    assert acct_rtx["company_name"] == "Raytheon Technologies"

    # Lookup by partial name
    acct_blm = cadence_manager.get_account_cadence("bloomberg")
    assert acct_blm is not None
    assert acct_blm["company_name"] == "Bloomberg LP"

    # Nonexistent account
    assert cadence_manager.get_account_cadence("NON_EXISTENT_CO") is None


def test_06_deliverability_audit_and_dns_records(cadence_manager):
    """Verify deliverability audit evaluates spam scores and DNS authentication."""
    audit = cadence_manager.audit_deliverability()
    assert audit["total_accounts_mapped"] >= 15
    assert audit["total_touches_audited"] >= 60
    assert audit["pass_rate_pct"] >= 95.0
    assert audit["average_spam_score_pct"] < 2.0
    assert audit["overall_deliverability_status"] == "EXCELLENT_INBOX_READY"

    # Verify SPF, DKIM, and DMARC posture
    auth = audit["technical_authentication"]
    assert "spf" in auth["spf_record"]
    assert "v=DMARC1" in auth["dmarc_policy"]
    assert "p=reject" in auth["dmarc_policy"]
    assert "dss._domainkey" in auth["dkim_selector"]


def test_07_campaign_dossier_report_export(cadence_manager):
    """Verify markdown report generation for executive campaign dossier."""
    out_path = cadence_manager.render_campaign_dossier()
    assert os.path.exists(out_path)

    with open(out_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Executive Outreach Campaign & Deliverability Dossier" in content
    assert "Technical Email Authentication Posture" in content
    assert "4-Touch Sequence Architecture Across Target Accounts" in content
    assert "enterprise@devsupersuite.com" in content


def test_08_cli_commands_execution():
    """Verify all CLI subcommands execute successfully with exit code 0."""
    python_bin = sys.executable
    script_path = os.path.join(SERVICES_DIR, "enterprise_abm_cadence_engine.py")

    flags = [
        ["--summary"],
        ["--audit-email-deliverability"],
        ["--generate-executive-cadence", "ACC-RTX-01"],
        ["--generate-executive-cadence", "ALL"],
        ["--export-outreach-campaign"],
    ]

    for flag_group in flags:
        cmd = [python_bin, script_path] + flag_group
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        assert res.returncode == 0, f"Command {cmd} failed with stderr: {res.stderr}"


def test_09_strict_brand_anonymity():
    """Verify zero personal founder leaks across all Phase 24 assets."""
    forbidden_tokens = [
        bytes.fromhex("41746861727661").decode("utf-8"),
        bytes.fromhex("506164687965").decode("utf-8"),
        bytes.fromhex("39383930343431323933").decode("utf-8"),
    ]

    phase_24_files = [
        Path(SERVICES_DIR) / "enterprise_abm_cadence_engine.py",
        Path(MARKETING_DIR) / "enterprise_abm_email_templates.json",
        Path(MARKETING_DIR) / "executive_outreach_deliverability_playbook.md",
        Path(REPORTS_DIR) / "executive_outreach_campaign_dossier.md",
        Path(TESTS_DIR) / "test_enterprise_abm_cadence.py",
    ]

    for file_path in phase_24_files:
        assert file_path.exists(), f"File {file_path} must exist"
        content = file_path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token.lower() not in content.lower(), (
                f"Brand anonymity violation: found forbidden token in {file_path}"
            )
