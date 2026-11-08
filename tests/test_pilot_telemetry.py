#!/usr/bin/env python3
"""
Unit and Integration Tests for Enterprise Pilot Telemetry & Customer Health Observability Engine
Reference: tests/test_pilot_telemetry.py
Classification: Automated Quality Gate (100% Pass Required)
Contact: telemetry@devsupersuite.com
"""

import json
import re
import shutil
import tempfile
from pathlib import Path
import pytest

from services.pilot_telemetry_observability_engine import (
    PilotTelemetryEngine,
    CustomerHealthScorer,
    PilotReportExporter,
    run_cli,
    CONVERSION_READY_THRESHOLD,
    MAX_AST_ERROR_RATE_PCT,
    MIN_TOKEN_REDUCTION_SLA_PCT,
    DEFAULT_LICENSED_SEATS
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. 30-Day Simulation & Progression Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_simulation_30day_records():
    records = PilotTelemetryEngine.simulate_30day_pilot(
        customer_name="Northrop Grumman",
        licensed_seats=100
    )
    assert len(records) == 30

    # Verify daily increments
    for idx, r in enumerate(records, start=1):
        assert r["day"] == idx
        assert r["active_seats"] <= r["licensed_seats"]
        assert r["tokens_saved"] > 0
        assert r["compression_ratio_pct"] >= MIN_TOKEN_REDUCTION_SLA_PCT
        assert r["secrets_leaked"] == 0
        assert r["dollars_saved_usd"] > 0

    # Verify utilization growth from week 1 to week 4
    week1_util = sum(r["seat_utilization_pct"] for r in records[:7]) / 7.0
    week4_util = sum(r["seat_utilization_pct"] for r in records[-7:]) / 7.0
    assert week4_util > week1_util


# ─────────────────────────────────────────────────────────────────────────────
# 2. Customer Health Scorecard Math Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_health_score_calculation_healthy_pilot():
    records = PilotTelemetryEngine.simulate_30day_pilot("Boeing Defense", licensed_seats=100)
    scorecard = CustomerHealthScorer.calculate_health_scorecard(records)

    assert scorecard["health_score"] >= CONVERSION_READY_THRESHOLD
    assert scorecard["conversion_ready"] is True
    assert scorecard["conversion_status"] == "EXECUTIVE_CLOSE_READY"
    assert "AUTOMATED EXECUTIVE CONVERSION ALERT" in scorecard["executive_alert"]

    # Verify Score Breakdown components sum to health_score
    sb = scorecard["score_breakdown"]
    assert "seat_utilization" in sb
    assert "token_reduction_sla" in sb
    assert "compiler_reliability" in sb
    assert "secret_defense" in sb
    assert "developer_sentiment" in sb
    assert round(sum(sb.values()), 1) == scorecard["health_score"]

    # Verify Cumulative Telemetry
    ct = scorecard["cumulative_telemetry"]
    assert ct["total_tokens_saved"] > 0
    assert ct["total_dollars_saved_usd"] > 0
    assert ct["cumulative_compression_pct"] >= MIN_TOKEN_REDUCTION_SLA_PCT
    assert ct["overall_ast_error_rate_pct"] < MAX_AST_ERROR_RATE_PCT


def test_health_score_degraded_low_seat_utilization():
    # Craft degraded records with only 15% seat utilization
    records = PilotTelemetryEngine.simulate_30day_pilot("Stagnant Corp", licensed_seats=100)
    for r in records:
        r["active_seats"] = 15
        r["seat_utilization_pct"] = 15.0

    scorecard = CustomerHealthScorer.calculate_health_scorecard(records)
    sb = scorecard["score_breakdown"]
    assert sb["seat_utilization"] == 8.0 # Minimum points
    assert scorecard["health_score"] < 100.0


def test_health_score_degraded_high_compiler_errors():
    records = PilotTelemetryEngine.simulate_30day_pilot("Buggy Engine Corp", licensed_seats=100)
    for r in records:
        # Inject high error rate (10%)
        r["ast_compiler_errors"] = int(r["ast_compiler_invocations"] * 0.10)

    scorecard = CustomerHealthScorer.calculate_health_scorecard(records)
    sb = scorecard["score_breakdown"]
    assert sb["compiler_reliability"] == 5.0 # Penalized score


def test_health_score_degraded_secret_leak():
    records = PilotTelemetryEngine.simulate_30day_pilot("Leaky Security Corp", licensed_seats=100)
    # Inject a secret leak
    records[15]["secrets_leaked"] = 1

    scorecard = CustomerHealthScorer.calculate_health_scorecard(records)
    sb = scorecard["score_breakdown"]
    assert sb["secret_defense"] == 0.0 # Strict zero points for secret leak


# ─────────────────────────────────────────────────────────────────────────────
# 3. Alert Triggering Logic Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_alert_triggering_thresholds():
    # Healthy pilot triggers close alert
    records = PilotTelemetryEngine.simulate_30day_pilot("Raytheon Space", licensed_seats=100)
    healthy_scorecard = CustomerHealthScorer.calculate_health_scorecard(records)
    assert healthy_scorecard["conversion_ready"] is True
    assert "EXECUTIVE_CLOSE_READY" in healthy_scorecard["conversion_status"]

    # Empty records test
    empty_res = CustomerHealthScorer.calculate_health_scorecard([])
    assert empty_res["status"] == "NO_DATA"
    assert empty_res["health_score"] == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 4. Brand Anonymity Verification Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_brand_anonymity_invariants():
    script_path = Path(r"C:\Users\atpad\.gemini\antigravity\scratch\agent-commerce\services\pilot_telemetry_observability_engine.py")
    dash_path = Path(r"C:\Users\atpad\.gemini\antigravity\scratch\agent-commerce\services\enterprise_pilot_sla_dashboard.md")

    for p in [script_path, dash_path]:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")

        # Must contain institutional brands
        assert "DevSuperSuite" in text
        assert "OmniKernel Labs" in text

        # Must not contain personal phone numbers or external emails
        assert not re.search(r"\+1[- ]?\d{3}[- ]?\d{3}[- ]?\d{4}", text)
        assert not re.search(r"\b\d{3}[-.]\d{3}[-.]\d{4}\b", text)
        assert "gmail.com" not in text
        assert "yahoo.com" not in text
        assert "hotmail.com" not in text


# ─────────────────────────────────────────────────────────────────────────────
# 5. Report Exporter Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_report_exporter_outputs():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_pilot_rep_"))
    try:
        dash_file = temp_dir / "pilot_dashboard.md"
        rep_file = temp_dir / "pilot_report.md"

        records = PilotTelemetryEngine.simulate_30day_pilot("General Dynamics", 100)
        scorecard = CustomerHealthScorer.calculate_health_scorecard(records)

        PilotReportExporter.export_pilot_sla_dashboard(dash_file)
        assert dash_file.exists()
        dash_text = dash_file.read_text(encoding="utf-8")
        assert "Enterprise Pilot SLA Telemetry & Customer Health Dashboard" in dash_text
        assert "Score >= 85.0 : EXECUTIVE CLOSE READY" in dash_text

        PilotReportExporter.export_executive_health_report(
            scorecard, records, rep_file, "General Dynamics"
        )
        assert rep_file.exists()
        rep_text = rep_file.read_text(encoding="utf-8")
        assert "30-Day Enterprise Pilot Health & Conversion Audit Report" in rep_text
        assert "General Dynamics" in rep_text
        assert "Cumulative Dollars Saved" in rep_text
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# 6. CLI Execution Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_cli_execution_all_flags():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_cli_pilot_"))
    try:
        rep_file = temp_dir / "cli_report.md"
        dash_file = temp_dir / "cli_dash.md"
        json_file = temp_dir / "cli_telemetry.json"

        ret = run_cli([
            "--simulate-pilot-telemetry",
            "--audit-poc-health",
            "--export-executive-health-deck",
            "--summary",
            "--customer", "Lockheed Titan Aerospace",
            "--seats", "150",
            "--token-price", "12.00",
            "--output-report", str(rep_file),
            "--output-dashboard", str(dash_file),
            "--output-json", str(json_file)
        ])

        assert ret == 0
        assert rep_file.exists()
        assert dash_file.exists()
        assert json_file.exists()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
