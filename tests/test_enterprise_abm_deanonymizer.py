"""
⚡ DevSuperSuite Official: Enterprise B2B IP Deanonymization & Account-Based Intent Tests
File: test_enterprise_abm_deanonymizer.py
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
DATA_DIR = os.path.join(SCRATCH_DIR, "data")
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")

if SCRATCH_DIR not in sys.path:
    sys.path.insert(0, SCRATCH_DIR)
if SERVICES_DIR not in sys.path:
    sys.path.insert(0, SERVICES_DIR)

from services.enterprise_abm_deanonymizer import (
    IPToCompanyResolver,
    ABMIntentScorer,
    EnterpriseABMDeanonymizer,
    TARGET_ACCOUNTS_PATH,
    SESSIONS_LOG_PATH,
    DOSSIERS_EXPORT_PATH,
    ABM_REPORT_PATH,
    SURGE_ALERT_THRESHOLD,
)


@pytest.fixture
def target_accounts_db():
    assert os.path.exists(TARGET_ACCOUNTS_PATH), f"Missing database: {TARGET_ACCOUNTS_PATH}"
    with open(TARGET_ACCOUNTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


@pytest.fixture
def abm_engine(tmp_path):
    test_sessions = str(tmp_path / "test_sessions.json")
    test_dossiers = str(tmp_path / "test_dossiers.json")
    test_report = str(tmp_path / "test_report.md")
    return EnterpriseABMDeanonymizer(
        target_accounts_path=TARGET_ACCOUNTS_PATH,
        sessions_path=test_sessions,
        dossiers_path=test_dossiers,
        report_path=test_report,
    )


def test_01_database_completeness_and_cidr_compilation(target_accounts_db):
    """Verify target accounts database contains >= 50 enterprise accounts with valid CIDRs."""
    accounts = target_accounts_db.get("accounts", [])
    assert len(accounts) >= 50, f"Expected at least 50 target accounts, found {len(accounts)}"

    resolver = IPToCompanyResolver(TARGET_ACCOUNTS_PATH)
    assert len(resolver.compiled_cidrs) >= 50, "Should compile at least 50 CIDR subnets"

    for acct in accounts:
        assert "account_id" in acct
        assert "company_name" in acct
        assert "domain" in acct
        assert "industry" in acct
        assert "employee_tier" in acct
        assert "ip_ranges" in acct and len(acct["ip_ranges"]) > 0
        assert "target_acv_usd" in acct
        assert "primary_stack" in acct
        assert "recommended_tier" in acct


def test_02_ip_to_company_resolution(abm_engine):
    """Verify IP address resolution to enterprise company entities via subnet matching."""
    resolver = abm_engine.resolver

    # Bloomberg IP (160.43.12.88)
    bloomberg = resolver.resolve_ip("160.43.12.88")
    assert bloomberg is not None
    assert "Bloomberg" in bloomberg["company_name"]
    assert bloomberg["domain"] == "bloomberg.com"
    assert "Financial" in bloomberg["industry"]
    assert bloomberg["target_acv_usd"] >= 42000

    # Raytheon IP (192.138.10.15)
    raytheon = resolver.resolve_ip("192.138.10.15")
    assert raytheon is not None
    assert raytheon["company_name"] == "Raytheon Technologies"
    assert "Defense" in raytheon["industry"]
    assert "C++" in raytheon["primary_stack"]

    # Datadog IP (199.83.129.50)
    datadog = resolver.resolve_ip("199.83.129.50")
    assert datadog is not None
    assert datadog["company_name"] == "Datadog"
    assert "TypeScript" in datadog["primary_stack"] or "Go" in datadog["primary_stack"]

    # JPMorgan Chase IP (159.53.20.44)
    jpmorgan = resolver.resolve_ip("159.53.20.44")
    assert jpmorgan is not None
    assert "JPMorgan" in jpmorgan["company_name"]

    # Unmapped / Consumer IP (TEST-NET-2)
    consumer = resolver.resolve_ip("198.51.100.1")
    assert consumer is None


def test_03_intent_score_calculation_and_weights():
    """Verify intent scoring algorithm computes correct weights across visitor actions."""
    # 1. Base / Shallow visitor
    base_metrics = {
        "page_depth": 1,
        "playground_dwell_seconds": 10.0,
        "visited_pricing": False,
        "visited_security_compliance": False,
        "repeat_visit_24h": False,
    }
    res_base = ABMIntentScorer.calculate_intent_score(base_metrics)
    assert res_base["intent_score"] == 8.3  # 5 (page) + 3.3 (dwell)
    assert res_base["is_surge_alert"] is False
    assert res_base["intent_tier"] == "LOW_INTEREST"

    # 2. Pricing inspection (+20)
    pricing_metrics = dict(base_metrics)
    pricing_metrics["visited_pricing"] = True
    res_pricing = ABMIntentScorer.calculate_intent_score(pricing_metrics)
    assert res_pricing["score_breakdown"]["pricing_visit_pts"] == 20.0
    assert res_pricing["intent_score"] > res_base["intent_score"]

    # 3. Security / Compliance inspection (+15)
    sec_metrics = dict(base_metrics)
    sec_metrics["visited_security_compliance"] = True
    res_sec = ABMIntentScorer.calculate_intent_score(sec_metrics)
    assert res_sec["score_breakdown"]["security_docs_pts"] == 15.0

    # 4. AST Playground dwell maxes at 30 pts for 90s+
    dwell_metrics = dict(base_metrics)
    dwell_metrics["playground_dwell_seconds"] = 120.0
    res_dwell = ABMIntentScorer.calculate_intent_score(dwell_metrics)
    assert res_dwell["score_breakdown"]["playground_dwell_pts"] == 30.0

    # 5. Full engagement surges to 100 points
    full_metrics = {
        "page_depth": 5,
        "playground_dwell_seconds": 95.0,
        "visited_pricing": True,
        "visited_security_compliance": True,
        "repeat_visit_24h": True,
    }
    res_full = ABMIntentScorer.calculate_intent_score(full_metrics)
    assert res_full["intent_score"] == 100.0
    assert res_full["is_surge_alert"] is True
    assert res_full["intent_tier"] == "HIGH_INTENT_SURGE"
    assert res_full["action_recommended"] == "IMMEDIATE_ENTERPRISE_AE_OUTREACH"


def test_04_surge_alert_triggering_at_75_points(abm_engine):
    """Verify inbound enterprise session scoring >= 75 triggers surge alert with Slack payload."""
    surge_metrics = {
        "page_depth": 4,
        "playground_dwell_seconds": 90.0,
        "visited_pricing": True,
        "visited_security_compliance": True,
        "repeat_visit_24h": True,
    }
    # Bloomberg IP
    record = abm_engine.process_inbound_session("160.43.12.88", surge_metrics)
    assert record is not None
    assert "Bloomberg" in record["company_name"]
    assert record["intent_score"] >= SURGE_ALERT_THRESHOLD
    assert record["is_surge_alert"] is True
    assert record["alert_dispatched"] is True
    assert "alert_payload" in record

    payload = record["alert_payload"]
    assert payload["channel"] == "#enterprise-leads-live"
    assert "Bloomberg" in payload["text"]
    assert "SURGE" in payload["text"]
    assert "enterprise@devsupersuite.com" in payload["text"]


def test_05_moderate_and_low_intent_handling(abm_engine):
    """Verify sessions scoring < 75 do not trigger immediate surge alert dispatches."""
    low_metrics = {
        "page_depth": 1,
        "playground_dwell_seconds": 15.0,
        "visited_pricing": False,
        "visited_security_compliance": False,
        "repeat_visit_24h": False,
    }
    # Raytheon IP with minimal engagement
    record = abm_engine.process_inbound_session("192.138.10.15", low_metrics)
    assert record is not None
    assert record["company_name"] == "Raytheon Technologies"
    assert record["intent_score"] < SURGE_ALERT_THRESHOLD
    assert record["is_surge_alert"] is False
    assert record["alert_dispatched"] is False
    assert "alert_payload" not in record


def test_06_simulate_enterprise_traffic(abm_engine):
    """Verify simulate_enterprise_traffic exercises multiple enterprise sessions."""
    results = abm_engine.simulate_enterprise_traffic()
    assert len(results) >= 6
    assert len(abm_engine.sessions_log) >= 6

    surges = [r for r in results if r["is_surge_alert"]]
    assert len(surges) >= 3, "Expected at least 3 surge alerts from benchmark enterprise simulation"

    companies = [r["company_name"] for r in results]
    assert any("Bloomberg" in c for c in companies)
    assert any("Raytheon" in c for c in companies)
    assert any("Uber" in c for c in companies)


def test_07_export_dossiers_and_report_generation(abm_engine):
    """Verify account dossiers export and markdown signals report generation."""
    abm_engine.simulate_enterprise_traffic()

    # 1. Test Dossiers Export
    export_path = abm_engine.export_account_dossiers()
    assert os.path.exists(export_path)
    with open(export_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "dossiers" in data
    assert data["total_dossiers"] > 0
    assert "enterprise@devsupersuite.com" in data["governing_authority"]

    # 2. Test Markdown Report Generation
    report_file = abm_engine.render_markdown_report()
    assert os.path.exists(report_file)
    with open(report_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Enterprise B2B IP Deanonymization & Intent Signals Report" in content
    assert "Enterprise Ingress Intent Trajectory" in content
    assert "Target Enterprise Accounts Mapped" in content
    assert "enterprise@devsupersuite.com" in content


def test_08_cli_commands_execution():
    """Verify all CLI subcommands and flags execute successfully with exit code 0."""
    python_bin = sys.executable
    script_path = os.path.join(SERVICES_DIR, "enterprise_abm_deanonymizer.py")

    flags = [
        ["--summary"],
        ["--audit-abm-intent"],
        ["--simulate-enterprise-traffic"],
        ["--export-account-dossiers"],
    ]

    for flag_group in flags:
        cmd = [python_bin, script_path] + flag_group
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        assert res.returncode == 0, f"Command {cmd} failed with stderr: {res.stderr}"


def test_09_strict_brand_anonymity():
    """Verify zero personal founder leaks across all Phase 22 assets."""
    forbidden_tokens = [
        bytes.fromhex("41746861727661").decode("utf-8"),
        bytes.fromhex("506164687965").decode("utf-8"),
        bytes.fromhex("39383930343431323933").decode("utf-8"),
    ]

    phase_22_files = [
        Path(SERVICES_DIR) / "enterprise_abm_deanonymizer.py",
        Path(MARKETING_DIR) / "abm_target_accounts_signals.json",
        Path(MARKETING_DIR) / "cro_enterprise_abm_playbook.md",
        Path(TESTS_DIR) / "test_enterprise_abm_deanonymizer.py",
    ]

    for file_path in phase_22_files:
        assert file_path.exists(), f"File {file_path} must exist"
        content = file_path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token.lower() not in content.lower(), (
                f"Brand anonymity violation: found forbidden token in {file_path}"
            )
