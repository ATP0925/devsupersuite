"""
⚡ DevSuperSuite Official: Enterprise Customer Health Scoring & Churn Interdiction Tests
File: test_churn_interdiction.py
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

from services.enterprise_churn_interdiction_engine import (
    CustomerHealthCalculator,
    EnterpriseChurnInterdictionEngine,
    SIGNAL_WEIGHTS,
    HEALTH_SCORES_PATH,
    REPORT_PATH,
)


@pytest.fixture
def test_engine(tmp_path):
    ledger_file = str(tmp_path / "test_health_scores.json")
    report_file = str(tmp_path / "test_churn_report.md")
    return EnterpriseChurnInterdictionEngine(
        ledger_path=ledger_file,
        report_path=report_file
    )


def test_01_signal_weights_and_normalization():
    """Verify behavioral signal weights sum exactly to 1.0 (100%)."""
    total_weight = sum(SIGNAL_WEIGHTS.values())
    assert round(total_weight, 4) == 1.0
    assert SIGNAL_WEIGHTS["ast_volume_trend"] == 0.25
    assert SIGNAL_WEIGHTS["secret_scan_frequency"] == 0.20
    assert SIGNAL_WEIGHTS["active_cli_sessions"] == 0.20
    assert SIGNAL_WEIGHTS["seat_utilization"] == 0.20
    assert SIGNAL_WEIGHTS["support_sentiment"] == 0.15


def test_02_healthy_customer_score_calculation():
    """Verify expanding usage and high seat utilization produces HEALTHY (>80) score."""
    health = CustomerHealthCalculator.calculate_health_score(
        ast_volume_trend_pct=25.0,
        weekly_secret_scans=150,
        daily_active_cli_users=45,
        licensed_seats=50,
        active_seats=48,
        support_csat_score=4.9,
        open_critical_tickets=0
    )

    assert health["health_score"] >= 80.0
    assert health["status"] == "HEALTHY"
    assert health["recommended_action"] == "EXPANSION_UPSELL_OPPORTUNITY"
    assert health["subscores"]["ast_volume_trend_score"] >= 80.0
    assert health["subscores"]["seat_utilization_score"] == 100.0


def test_03_at_risk_customer_score_calculation():
    """Verify mild volume decline and moderate seat utilization yields AT_RISK (50-80) score."""
    health = CustomerHealthCalculator.calculate_health_score(
        ast_volume_trend_pct=-15.0,
        weekly_secret_scans=30,
        daily_active_cli_users=15,
        licensed_seats=40,
        active_seats=20,
        support_csat_score=4.0,
        open_critical_tickets=0
    )

    assert 50.0 <= health["health_score"] < 80.0
    assert health["status"] == "AT_RISK"
    assert health["recommended_action"] == "PROACTIVE_TAM_OPTIMIZATION_TOUCHPOINT"


def test_04_critical_customer_score_calculation():
    """Verify severe activity drops and open critical P1 tickets trigger CRITICAL_INTERDICTION (<50)."""
    health = CustomerHealthCalculator.calculate_health_score(
        ast_volume_trend_pct=-65.0,
        weekly_secret_scans=3,
        daily_active_cli_users=2,
        licensed_seats=50,
        active_seats=6,
        support_csat_score=2.0,
        open_critical_tickets=2
    )

    assert health["health_score"] < 50.0
    assert health["status"] == "CRITICAL_INTERDICTION"
    assert health["recommended_action"] == "EMERGENCY_SOLUTIONS_ARCHITECT_OFFICE_HOURS_AND_EXTENSION"


def test_05_record_customer_health_persistence(test_engine):
    """Verify customer assessment is registered and persists accurately in the ledger."""
    rec = test_engine.assess_and_record_customer_health(
        account_id="ACC-TEST-01",
        company_name="Lockheed Martin",
        domain="lockheedmartin.com",
        contract_arr_usd=24999.0,
        ast_volume_trend_pct=30.0,
        weekly_secret_scans=120,
        daily_active_cli_users=40,
        licensed_seats=50,
        active_seats=45,
        support_csat_score=5.0
    )

    assert rec["account_id"] == "ACC-TEST-01"
    assert rec["company_name"] == "Lockheed Martin"
    assert rec["status"] == "HEALTHY"

    # Re-instantiate and verify persistence
    engine2 = EnterpriseChurnInterdictionEngine(
        ledger_path=test_engine.ledger_path,
        report_path=test_engine.report_path
    )
    assert len(engine2.ledger["customer_accounts"]) == 1
    assert engine2.ledger["customer_accounts"][0]["account_id"] == "ACC-TEST-01"


def test_06_trigger_critical_interdiction_playbook(test_engine):
    """Verify critical account triggers emergency playbook with 14-day license extension token."""
    test_engine.assess_and_record_customer_health(
        account_id="ACC-CRIT-99",
        company_name="Legacy Systems Corp",
        domain="legacysys.com",
        contract_arr_usd=19999.0,
        ast_volume_trend_pct=-70.0,
        weekly_secret_scans=2,
        daily_active_cli_users=1,
        licensed_seats=30,
        active_seats=3,
        support_csat_score=2.0,
        open_critical_tickets=2
    )

    intervention = test_engine.trigger_interdiction_playbook(
        account_id="ACC-CRIT-99",
        target_executive_email="ciso@legacysys.com"
    )

    assert intervention["event_id"].startswith("INT-")
    assert intervention["severity"] == "CRITICAL"
    assert intervention["status"] == "DISPATCHED_ACTIVE"
    assert intervention["extension_token"].startswith("DSS-EXT-14D-")
    assert any("solutions@devsupersuite.com" in act for act in intervention["actions_executed"])


def test_07_trigger_at_risk_and_healthy_interdictions(test_engine):
    """Verify warning severity for AT_RISK and opportunity logging for HEALTHY."""
    # At-Risk
    test_engine.assess_and_record_customer_health(
        account_id="ACC-RISK-01",
        company_name="Medium Corp",
        domain="mediumcorp.com",
        contract_arr_usd=15000.0,
        ast_volume_trend_pct=-10.0,
        weekly_secret_scans=40,
        daily_active_cli_users=12,
        licensed_seats=25,
        active_seats=15
    )
    int_risk = test_engine.trigger_interdiction_playbook("ACC-RISK-01")
    assert int_risk["severity"] == "WARNING"
    assert int_risk["extension_token"] is None

    # Healthy
    test_engine.assess_and_record_customer_health(
        account_id="ACC-HLTH-01",
        company_name="Growth Cloud",
        domain="growthcloud.io",
        contract_arr_usd=30000.0,
        ast_volume_trend_pct=40.0,
        weekly_secret_scans=200,
        daily_active_cli_users=30,
        licensed_seats=30,
        active_seats=30
    )
    int_hlth = test_engine.trigger_interdiction_playbook("ACC-HLTH-01")
    assert int_hlth["severity"] == "OPPORTUNITY"


def test_08_invalid_account_id_handling(test_engine):
    """Verify KeyError is raised when triggering interdiction for non-existent account."""
    with pytest.raises(KeyError, match="Customer account 'ACC-UNKNOWN' not found"):
        test_engine.trigger_interdiction_playbook("ACC-UNKNOWN")


def test_09_customer_health_portfolio_audit(test_engine):
    """Verify audit computes portfolio average, healthy/at-risk/critical breakdowns, and ARR at risk."""
    test_engine.assess_and_record_customer_health("ACC-1", "Corp 1", "c1.com", 25000.0, 30.0, 150, 40, 50, 45) # Healthy
    test_engine.assess_and_record_customer_health("ACC-2", "Corp 2", "c2.com", 15000.0, -15.0, 35, 15, 30, 18) # At-risk
    test_engine.assess_and_record_customer_health("ACC-3", "Corp 3", "c3.com", 20000.0, -60.0, 5, 2, 40, 5, open_critical_tickets=1) # Critical

    audit = test_engine.audit_customer_health_portfolio()
    assert audit["total_accounts"] == 3
    assert audit["healthy_accounts_count"] == 1
    assert audit["at_risk_accounts_count"] == 1
    assert audit["critical_accounts_count"] == 1
    assert audit["total_portfolio_arr_usd"] == 60000.0
    assert audit["healthy_arr_usd"] == 25000.0
    assert audit["total_arr_at_risk_usd"] == 35000.0  # 15k + 20k


def test_10_markdown_report_generation(test_engine):
    """Verify executive markdown scorecard report generation with all required sections."""
    test_engine.assess_and_record_customer_health("ACC-RPT", "Boeing Defense", "boeing.com", 24999.0, 20.0, 100, 30, 35, 32)
    test_engine.trigger_interdiction_playbook("ACC-RPT")

    report_path = test_engine.render_markdown_report()
    assert os.path.exists(report_path)

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "# ⚡ DevSuperSuite Official: Customer Health Scoring & Churn Interdiction Scorecard" in content
    assert "Boeing Defense" in content
    assert "Behavioral Signal" in content
    assert "growth@devsupersuite.com" in content


def test_11_cli_interface_execution():
    """Verify all CLI subcommands execute with exit code 0."""
    python_bin = sys.executable
    script_path = os.path.join(SERVICES_DIR, "enterprise_churn_interdiction_engine.py")

    commands = [
        ["--summary"],
        ["--calculate-health", "--account-id", "ACC-CLI-01", "--company", "Northrop", "--domain", "noc.com", "--arr", "20000.0", "--ast-trend", "20.0", "--scans", "100", "--cli-users", "25", "--licensed-seats", "30", "--active-seats", "28"],
        ["--trigger-interdiction", "--account-id", "ACC-CLI-01", "--email", "ciso@noc.com"],
        ["--audit-health"],
        ["--export-churn-report"]
    ]

    for args in commands:
        cmd = [python_bin, script_path] + args
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        assert res.returncode == 0, f"CLI command {cmd} failed with stderr: {res.stderr}"


def test_12_strict_brand_anonymity_compliance():
    """Verify zero personal founder leaks across all Phase 33 assets."""
    forbidden_tokens = [
        bytes.fromhex("41746861727661").decode("utf-8"),
        bytes.fromhex("506164687965").decode("utf-8"),
        bytes.fromhex("39383930343431323933").decode("utf-8"),
    ]

    phase_33_files = [
        Path(SERVICES_DIR) / "enterprise_churn_interdiction_engine.py",
        Path(DATA_DIR) / "customer_health_scores.json",
        Path(REPORTS_DIR) / "customer_churn_interdiction_report.md",
        Path(TESTS_DIR) / "test_churn_interdiction.py",
    ]

    for file_path in phase_33_files:
        assert file_path.exists(), f"File {file_path} must exist"
        content = file_path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token.lower() not in content.lower(), (
                f"Brand anonymity violation: found forbidden token in {file_path}"
            )
