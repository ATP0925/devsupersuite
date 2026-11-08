"""
⚡ DevSuperSuite Treasury & Corporate Finance - Unit & Integration Test Suite
File: test_saas_cohort_ltv.py
Target: saas_cohort_ltv_engine.py (SaaS Cohort Retention & Net Margin LTV Expansion Engine)
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

from saas_cohort_ltv_engine import (
    SaaSCohortLTVEngine,
    BASELINE_UNIT_ECONOMICS,
    EMPIRICAL_COHORT_TIMELINE,
    COHORT_LEDGER_FILE,
    DEFAULT_COHORT_REPORT_FILE
)

FORBIDDEN_FOUNDER_TOKENS = [
    "Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"
]


@pytest.fixture
def cohort_engine(tmp_path):
    """Initializes SaaS Cohort LTV Engine with isolated test paths."""
    test_ledger = os.path.join(tmp_path, "test_cohort_ledger.json")
    test_report = os.path.join(tmp_path, "test_cohort_report.md")
    return SaaSCohortLTVEngine(
        ledger_path=test_ledger,
        report_path=test_report
    )


def test_01_unit_economics_audit_ltv_cac(cohort_engine):
    """Verifies institutional LTV ($12,450), CAC Payback (2.4 mo), and LTV/CAC ratio (8.4x)."""
    econ = cohort_engine.audit_ltv_cac_metrics()

    assert econ["gross_margin_adjusted_ltv_usd"] == 12450.00
    assert econ["blended_cac_usd"] == 1480.00
    assert econ["ltv_cac_ratio"] == 8.4
    assert econ["cac_payback_period_months"] == 2.4
    assert econ["magic_number"] == 1.45
    assert econ["rule_of_40_score_pct"] == 68.5

    bench = econ["benchmark_evaluation"]
    assert "ELITE" in bench["ltv_cac_status"]
    assert "EXEMPLARY" in bench["payback_status"]
    assert "PRISTINE" in bench["rule_of_40_status"]


def test_02_24m_cohort_expansion_matrix(cohort_engine):
    """Verifies 24-month empirical cohort retention decay and Net Dollar Retention (NDR) curve."""
    matrix = cohort_engine.generate_24m_cohort_expansion_matrix(initial_cohort_arr_usd=100000.00)

    assert matrix["initial_cohort_arr_usd"] == 100000.00
    assert matrix["m12_net_dollar_retention_pct"] == 134.5
    assert matrix["m24_net_dollar_retention_pct"] == 152.0
    assert matrix["m12_gross_revenue_retention_pct"] == 94.8
    assert matrix["m24_logo_retention_pct"] == 84.5

    timeline = matrix["cohort_timeline"]
    assert len(timeline) == len(EMPIRICAL_COHORT_TIMELINE)

    # M1 Baseline
    m1 = timeline[0]
    assert m1["month_number"] == 1
    assert m1["net_dollar_retention_pct"] == 100.0
    assert m1["cohort_arr_usd"] == 100000.00

    # M3 Expansion
    m3 = next(r for r in timeline if r["month_number"] == 3)
    assert m3["net_dollar_retention_pct"] == 112.0
    assert m3["cohort_arr_usd"] == 112000.00

    # M12 Milestone
    m12 = next(r for r in timeline if r["month_number"] == 12)
    assert m12["net_dollar_retention_pct"] == 134.5
    assert m12["cohort_arr_usd"] == 134500.00

    # M24 Milestone
    m24 = next(r for r in timeline if r["month_number"] == 24)
    assert m24["net_dollar_retention_pct"] == 152.0
    assert m24["cohort_arr_usd"] == 152000.00
    assert m24["expansion_multiplier"] == 1.52


def test_03_cohort_revenue_waterfall(cohort_engine):
    """Verifies annual SaaS portfolio revenue waterfall simulation."""
    waterfall = cohort_engine.simulate_cohort_revenue_waterfall(
        starting_arr_usd=100000.00,
        new_logo_arr_usd=25000.00
    )

    assert waterfall["starting_arr_usd"] == 100000.00
    assert waterfall["new_logo_arr_usd"] == 25000.00
    assert waterfall["expansion_arr_usd"] == 39700.00
    assert waterfall["contraction_arr_usd"] == -2100.00
    assert waterfall["churned_arr_usd"] == -3100.00
    assert waterfall["net_expansion_arr_usd"] == 34500.00
    assert waterfall["ending_arr_usd"] == 159500.00
    assert waterfall["net_new_arr_usd"] == 59500.00
    assert waterfall["annual_growth_rate_pct"] == 59.5


def test_04_churn_deflection_signals(cohort_engine):
    """Verifies telemetry signal evaluation for proactive churn deflection."""
    client_signals = [
        {"client_id": "CLIENT-HEALTHY", "days_silent": 1, "scan_decay_pct": 5.0, "parser_error_rate": 0.1},
        {"client_id": "CLIENT-AT-RISK", "days_silent": 10, "scan_decay_pct": 42.0, "parser_error_rate": 0.5},
        {"client_id": "CLIENT-ATTENTION", "days_silent": 5, "scan_decay_pct": 22.0, "parser_error_rate": 2.5}
    ]
    results = cohort_engine.evaluate_churn_deflection_signals(client_signals)

    assert len(results) == 3
    assert results[0]["risk_level"] == "LOW_HEALTHY"
    assert results[0]["deflection_action"] == "CONTINUE_STANDARD_MONITORING"

    assert results[1]["risk_level"] == "HIGH_CHURN_RISK"
    assert results[1]["deflection_action"] == "TRIGGER_AUTOMATED_DEVREL_TAM_OUTREACH"

    assert results[2]["risk_level"] == "MEDIUM_ATTENTION_NEEDED"
    assert results[2]["deflection_action"] == "DISPATCH_AST_OPTIMIZATION_DIAGNOSTIC_SUITE"


def test_05_save_reports_and_brand_anonymity(cohort_engine):
    """Verifies markdown report generation and strict 100% Brand Anonymity adherence."""
    paths = cohort_engine.save_reports_and_ledger()

    assert os.path.exists(paths["report_path"])
    assert os.path.exists(paths["ledger_path"])

    with open(paths["report_path"], "r", encoding="utf-8") as f:
        content = f.read()

    assert "DevSuperSuite Treasury & Corporate Finance" in content
    assert "cfo@devsupersuite.com" in content
    assert "INSTITUTIONAL SAAS UNIT ECONOMICS SCORECARD" in content
    assert "134.5%" in content
    assert "8.40x" in content or "8.4x" in content

    # Anonymity verification on report
    for token in FORBIDDEN_FOUNDER_TOKENS:
        assert token not in content, f"Forbidden founder token '{token}' exposed in cohort report!"

    # Anonymity verification on expansion guide document
    guide_path = os.path.join(SERVICES_DIR, "saas_cohort_expansion_guide.md")
    assert os.path.exists(guide_path)
    with open(guide_path, "r", encoding="utf-8") as f:
        guide_content = f.read()
    for token in FORBIDDEN_FOUNDER_TOKENS:
        assert token not in guide_content, f"Forbidden founder token '{token}' exposed in expansion guide!"


def test_06_cli_execution():
    """Verifies SaaS Cohort LTV CLI flags execution."""
    cmd = [
        sys.executable,
        os.path.join(SERVICES_DIR, "saas_cohort_ltv_engine.py"),
        "--summary",
        "--calculate-cohort-waterfall",
        "--audit-ltv-cac",
        "--generate-expansion-matrix"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "DevSuperSuite SaaS Cohort Retention & LTV Expansion Summary" in res.stdout
    assert "Gross-Margin Adjusted LTV:        $12,450.00 USD" in res.stdout
    assert "M12 Net Dollar Retention (NDR):   134.5%" in res.stdout
    assert "CAC Payback Period:               2.4 Months" in res.stdout
