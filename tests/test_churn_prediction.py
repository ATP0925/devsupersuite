"""
⚡ DevSuperSuite Official: Developer Churn Prediction & Retention Interception Tests
File: test_churn_prediction.py
Governing Entity: DevSuperSuite Customer Success Directorate (success@devsupersuite.com)
Strict Protocol: 100% Brand Anonymity - Zero Founder Personal Identifiers
"""

import os
import sys
import json
import pytest
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Paths Setup
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(SCRATCH_DIR, "services")
DATA_DIR = os.path.join(SCRATCH_DIR, "data")
MARKETING_DIR = os.path.join(SCRATCH_DIR, "marketing")

sys.path.insert(0, SERVICES_DIR)

from churn_prediction_retention_engine import (
    ChurnRiskScorer,
    ChurnPredictionRetentionEngine,
    USAGE_TELEMETRY_PATH,
    CHURN_REGISTRY_PATH,
    RETENTION_QUEUE_PATH,
    MARKDOWN_RETENTION_REPORT_PATH
)


@pytest.fixture
def temp_engine(tmp_path):
    telemetry_file = os.path.join(tmp_path, "telemetry.json")
    registry_file = os.path.join(tmp_path, "registry.json")
    queue_file = os.path.join(tmp_path, "queue.json")

    seed_data = [
        {
            "customer_email": "active.dev@test.org",
            "customer_name": "Active Dev",
            "plan_name": "Hacker Solo",
            "primary_language": "Rust",
            "ide_environment": "Cursor",
            "days_inactive": 1.0,
            "ast_volume_drop_pct": 0.0,
            "precommit_drop_pct": 0.0,
            "crash_rate_pct": 0.0
        },
        {
            "customer_email": "medium.dev@test.org",
            "customer_name": "Medium Dev",
            "plan_name": "Hacker Solo",
            "primary_language": "Python",
            "ide_environment": "VS Code",
            "days_inactive": 6.0,
            "ast_volume_drop_pct": 50.0,
            "precommit_drop_pct": 40.0,
            "crash_rate_pct": 1.5
        },
        {
            "customer_email": "high.dev@test.org",
            "customer_name": "High Dev",
            "plan_name": "Hacker Solo",
            "primary_language": "TypeScript",
            "ide_environment": "Windsurf",
            "days_inactive": 10.0,
            "ast_volume_drop_pct": 80.0,
            "precommit_drop_pct": 70.0,
            "crash_rate_pct": 2.0
        },
        {
            "customer_email": "critical.dev@test.org",
            "customer_name": "Critical Dev",
            "plan_name": "Team 5-Seat",
            "primary_language": "Go",
            "ide_environment": "Claude Code",
            "days_inactive": 16.0,
            "ast_volume_drop_pct": 100.0,
            "precommit_drop_pct": 100.0,
            "crash_rate_pct": 7.5
        }
    ]
    with open(telemetry_file, "w", encoding="utf-8") as f:
        json.dump(seed_data, f, indent=2)

    return ChurnPredictionRetentionEngine(
        telemetry_path=telemetry_file,
        registry_path=registry_file,
        queue_path=queue_file
    )


def test_01_churn_risk_scorer_low_risk():
    """Verify active developer scores in LOW risk tier with 0 points penalty."""
    result = ChurnRiskScorer.calculate_score(
        days_inactive=1.0,
        ast_volume_drop_pct=0.0,
        precommit_drop_pct=0.0,
        crash_rate_pct=0.0
    )
    assert result["churn_risk_score"] == 0.0
    assert result["risk_tier"] == "LOW"
    assert result["recommended_action"] == "MONITOR_HEALTHY"
    assert result["breakdown"]["recency_penalty"] == 0.0
    assert result["breakdown"]["ast_volume_drop_penalty"] == 0.0


def test_02_churn_risk_scorer_medium_risk():
    """Verify moderate drop in activity falls into MEDIUM risk tier."""
    result = ChurnRiskScorer.calculate_score(
        days_inactive=6.0,
        ast_volume_drop_pct=50.0,
        precommit_drop_pct=40.0,
        crash_rate_pct=1.5
    )
    assert 30.0 < result["churn_risk_score"] <= 65.0
    assert result["risk_tier"] == "MEDIUM"
    assert result["recommended_action"] == "LANGUAGE_OPTIMIZATION_NURTURE"


def test_03_churn_risk_scorer_high_risk():
    """Verify significant inactivity and drop in pre-commit falls into HIGH risk tier."""
    result = ChurnRiskScorer.calculate_score(
        days_inactive=11.0,
        ast_volume_drop_pct=85.0,
        precommit_drop_pct=75.0,
        crash_rate_pct=2.5
    )
    assert 65.0 < result["churn_risk_score"] <= 85.0
    assert result["risk_tier"] == "HIGH"
    assert result["recommended_action"] == "OFFER_50_PCT_TEAM_UPGRADE"


def test_04_churn_risk_scorer_critical_risk():
    """Verify prolonged inactivity and complete stop in usage triggers CRITICAL tier."""
    result = ChurnRiskScorer.calculate_score(
        days_inactive=15.0,
        ast_volume_drop_pct=100.0,
        precommit_drop_pct=100.0,
        crash_rate_pct=8.0
    )
    assert result["churn_risk_score"] > 85.0
    assert result["risk_tier"] == "CRITICAL"
    assert result["recommended_action"] == "DEDICATED_ARCHITECT_TRIAGE_CALL"
    assert result["breakdown"]["recency_penalty"] == 40.0
    assert result["breakdown"]["ast_volume_drop_penalty"] == 30.0
    assert result["breakdown"]["precommit_drop_penalty"] == 20.0


def test_05_engine_audit_churn_risk(temp_engine):
    """Verify engine audits all telemetry accounts and persists churn risk registry."""
    audit_results = temp_engine.audit_churn_risk()
    assert len(audit_results) == 4

    tiers = {r["customer_email"]: r["risk_tier"] for r in audit_results}
    assert tiers["active.dev@test.org"] == "LOW"
    assert tiers["medium.dev@test.org"] == "MEDIUM"
    assert tiers["high.dev@test.org"] == "HIGH"
    assert tiers["critical.dev@test.org"] == "CRITICAL"

    assert os.path.exists(temp_engine.registry_path)
    with open(temp_engine.registry_path, "r", encoding="utf-8") as f:
        saved = json.load(f)
        assert len(saved) == 4


def test_06_engine_trigger_retention_flow_interventions(temp_engine):
    """Verify dynamic retention workflows are generated for non-LOW tiers with appropriate payloads."""
    interventions = temp_engine.trigger_retention_flow()
    # 3 interventions generated (MEDIUM, HIGH, CRITICAL; LOW is excluded)
    assert len(interventions) == 3

    interv_by_tier = {i["risk_tier"]: i for i in interventions}

    # MEDIUM intervention check
    med_i = interv_by_tier["MEDIUM"]
    assert med_i["payload"]["action_type"] == "NURTURE_OPTIMIZATION_TIPS"
    assert "Optimizing your Python AST Context Slicing" in med_i["subject"]
    assert "omnikernel config --language python" in med_i["body"]

    # HIGH intervention check
    high_i = interv_by_tier["HIGH"]
    assert high_i["payload"]["action_type"] == "OFFER_50_PCT_UPGRADE"
    assert high_i["payload"]["coupon_code"] == "RETAIN50"
    assert high_i["payload"]["offer_price_usd"] == 74.50
    assert "RETAIN50" in high_i["body"]

    # CRITICAL intervention check
    crit_i = interv_by_tier["CRITICAL"]
    assert crit_i["payload"]["action_type"] == "DEDICATED_ARCHITECT_TRIAGE"
    assert "Priority Triage Request" in crit_i["subject"]
    assert "schedule-architect-triage" in crit_i["payload"]["calendar_url"]
    assert "30-Day Money Back Guarantee" in crit_i["body"]


def test_07_retention_cooldown_deduplication(temp_engine):
    """Verify 14-day cooldown prevents duplicate messages from spamming the same developer."""
    first_run = temp_engine.trigger_retention_flow()
    assert len(first_run) == 3

    # Second run immediately after should create 0 new interventions due to 14-day cooldown
    second_run = temp_engine.trigger_retention_flow()
    assert len(second_run) == 0
    assert len(temp_engine.interventions_queue) == 3


def test_08_markdown_manifest_generation():
    """Verify markdown retention manifest exists and contains clean markdown table."""
    engine = ChurnPredictionRetentionEngine()
    engine.audit_churn_risk()
    engine._write_markdown_manifest()

    assert os.path.exists(MARKDOWN_RETENTION_REPORT_PATH)
    with open(MARKDOWN_RETENTION_REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "# ⚡ DevSuperSuite Official: Developer Retention & Churn Interception Manifest" in content
    assert "success@devsupersuite.com" in content
    assert "| Intervention ID | Recipient Email | Risk Score | Risk Tier |" in content


def test_09_cli_commands_execution():
    """Verify all 4 CLI command flags run cleanly with exit code 0."""
    script_path = os.path.join(SERVICES_DIR, "churn_prediction_retention_engine.py")

    cmds = [
        [sys.executable, script_path, "--audit-churn-risk"],
        [sys.executable, script_path, "--trigger-retention-flow"],
        [sys.executable, script_path, "--export-risk-registry"],
        [sys.executable, script_path, "--summary"]
    ]

    for cmd in cmds:
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0, f"CLI command failed: {' '.join(cmd)}\n{res.stderr}"


def test_10_strict_brand_anonymity():
    """Verify strict 100% brand anonymity: zero personal founder names or numbers."""
    files_to_check = [
        os.path.join(SERVICES_DIR, "churn_prediction_retention_engine.py"),
        os.path.join(MARKETING_DIR, "developer_retention_playbook.md"),
        os.path.abspath(__file__)
    ]

    forbidden_tokens = [
        bytes.fromhex("70726174696b").decode("utf-8"),
        bytes.fromhex("7061646b6172").decode("utf-8"),
        bytes.fromhex("37303230343738313730").decode("utf-8")
    ]

    for fpath in files_to_check:
        assert os.path.exists(fpath), f"Missing file: {fpath}"
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read().lower()
            for token in forbidden_tokens:
                assert token not in content, f"Brand anonymity violation in {fpath}: found forbidden token"
