"""
⚡ DevSuperSuite Treasury & Corporate Finance - Unit & Integration Test Suite
File: test_saas_unit_economics.py
Target: saas_unit_economics_cohort_engine.py (SaaS Unit Economics, Cohort LTV/CAC & NRR Engine)
Strict Compliance: 100% Brand Anonymity - DevSuperSuite Treasury & Corporate Finance Only (cfo@devsupersuite.com).
"""

import os
import sys
import json
import subprocess
import pytest

# Add services directory to sys.path
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(SCRATCH_DIR, "services")
sys.path.insert(0, SERVICES_DIR)

from saas_unit_economics_cohort_engine import (
    SaaSUnitEconomicsCohortEngine,
    VENTURE_BENCHMARKS,
    COHORT_LEDGER_FILE,
    DEFAULT_SAAS_REPORT_FILE
)

@pytest.fixture
def saas_engine(tmp_path):
    """Initializes SaaS Unit Economics Engine with isolated test paths."""
    test_ledger = os.path.join(tmp_path, "test_saas_ledger.json")
    test_report = os.path.join(tmp_path, "test_saas_report.md")
    return SaaSUnitEconomicsCohortEngine(ledger_path=test_ledger, report_path=test_report)

def test_01_unit_economics_calculation(saas_engine):
    """Verifies CAC, LTV, and LTV/CAC ratios exceed venture hurdle rates."""
    econ = saas_engine.calculate_unit_economics()
    c = econ["consolidated"]
    ent = econ["segments"]["recurring_retainer_pods"]

    # Enterprise Retainer Pods
    assert ent["cac_usd"] == 16000.00
    assert ent["ltv_usd"] == 1283500.00
    assert ent["ltv_cac_ratio"] > 50.0  # Realizes ~80.22x
    assert ent["gross_margin_pct"] == 75.5

    # Consolidated Blended Unit Economics
    assert c["blended_cac_usd"] == 1850.00
    assert c["blended_ltv_usd"] == 15170.00
    assert c["blended_ltv_cac_ratio"] >= VENTURE_BENCHMARKS["min_ltv_cac_ratio"]  # >= 3.0x
    assert c["blended_ltv_cac_ratio"] == 8.20

def test_02_magic_number_benchmark(saas_engine):
    """Verifies SaaS Magic Number exceeds the top-quartile benchmark of 1.2x."""
    econ = saas_engine.calculate_unit_economics()
    magic = econ["consolidated"]["saas_magic_number"]

    assert magic >= VENTURE_BENCHMARKS["min_magic_number"]  # >= 1.2x
    assert magic == 1.85  # Realizes 1.85x (Top Decile SaaS)

def test_03_rule_of_40_score(saas_engine):
    """Verifies Rule of 40 score exceeds 50% (targeting 97.2%)."""
    econ = saas_engine.calculate_unit_economics()
    c = econ["consolidated"]

    assert c["revenue_growth_rate_pct"] == 65.0
    assert c["free_cash_flow_margin_pct"] == 32.2
    assert c["rule_of_40_score_pct"] == 97.2
    assert c["rule_of_40_score_pct"] >= 50.0

def test_04_net_revenue_retention_and_grr(saas_engine):
    """Verifies Net Revenue Retention (NRR > 130%) and Gross Revenue Retention (GRR > 95%)."""
    econ = saas_engine.calculate_unit_economics()
    c = econ["consolidated"]

    assert c["net_revenue_retention_nrr_pct"] >= 130.0  # Realizes 137.5%
    assert c["net_revenue_retention_nrr_pct"] == 137.5
    assert c["gross_revenue_retention_grr_pct"] >= 95.0  # Realizes 97.2%
    assert c["gross_revenue_retention_grr_pct"] == 97.2

def test_05_cac_payback_period(saas_engine):
    """Verifies CAC Payback Period is under 6 months (2.10 months blended, 2.49 months enterprise)."""
    econ = saas_engine.calculate_unit_economics()
    c = econ["consolidated"]
    ent = econ["segments"]["recurring_retainer_pods"]

    assert c["blended_payback_months"] < 6.0
    assert c["blended_payback_months"] == 2.10
    assert ent["payback_period_months"] < 6.0
    assert ent["payback_period_months"] == 2.49

def test_06_cohort_retention_matrix_decay_and_expansion(saas_engine):
    """Verifies 12-month cohort retention matrix has 12 intervals, 95% logo retention, and 137.5% NRR."""
    cohort = saas_engine.audit_cohort_retention()

    matrix = cohort["monthly_cohort_matrix"]
    assert len(matrix) == 12

    # Month 1 (Base)
    m1 = matrix[0]
    assert m1["month"] == 1
    assert m1["active_logos"] == 20
    assert m1["logo_retention_pct"] == 100.0
    assert m1["net_dollar_retention_nrr_pct"] == 100.0
    assert m1["total_cohort_mrr_usd"] == 170000.00

    # Month 12 (Expanded)
    m12 = matrix[11]
    assert m12["month"] == 12
    assert m12["active_logos"] == 19
    assert m12["logo_retention_pct"] == 95.0
    assert m12["net_dollar_retention_nrr_pct"] == 137.5
    assert m12["total_cohort_mrr_usd"] > 230000.00

    assert cohort["final_logo_retention_pct"] == 95.0
    assert cohort["final_net_dollar_retention_nrr_pct"] == 137.5

def test_07_markdown_report_generation_and_brand_anonymity(saas_engine, tmp_path):
    """Generates SaaS metrics markdown report and asserts strict 100% Brand Anonymity."""
    test_rep = os.path.join(tmp_path, "test_saas_metrics.md")
    test_led = os.path.join(tmp_path, "test_saas_ledger.json")

    saved = saas_engine.save_reports_and_ledger(report_path=test_rep, ledger_path=test_led)
    assert os.path.exists(saved["report_path"])
    assert os.path.exists(saved["ledger_path"])

    with open(saved["report_path"], "r", encoding="utf-8") as f:
        content = f.read()

    # Brand authority checks
    assert "DevSuperSuite Treasury & Corporate Finance" in content
    assert "cfo@devsupersuite.com" in content
    assert "8.20x Blended" in content
    assert "1.85x" in content
    assert "97.2%" in content
    assert "137.5%" in content

    # Zero PII Leaks: forbidden personal founder tokens
    forbidden = ["Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"]
    for word in forbidden:
        assert word not in content, f"Brand Anonymity violation: found '{word}' in SaaS report."

def test_08_cli_execution():
    """Verifies CLI execution with --calculate-unit-economics, --audit-cohort-retention, and --summary flags."""
    script_path = os.path.join(SERVICES_DIR, "saas_unit_economics_cohort_engine.py")

    cmd = [
        sys.executable, script_path,
        "--calculate-unit-economics",
        "--audit-cohort-retention",
        "--export-saas-metrics",
        "--summary"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert "SaaS Unit Economics Report" in res.stdout
    assert "Cohort Retention Ledger" in res.stdout
    assert "Customer Lifetime Value (LTV):    $1,283,500.00 USD" in res.stdout
    assert "Blended LTV / CAC Ratio:          8.20x" in res.stdout
    assert "Rule of 40 Score:                 97.2%" in res.stdout
    assert "Net Revenue Retention (NRR):      137.5%" in res.stdout
