"""
⚡ DevSuperSuite Financial Operations - Unit & Integration Test Suite
File: test_financial_forecast.py
Target: generate_financial_forecast.py (5-Year Enterprise Financial Valuation & Blended ARR Model)
Strict Compliance: 100% Brand Anonymity - DevSuperSuite Financial Operations Only.
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
DATA_DIR = os.path.join(SCRATCH_DIR, "data")
sys.path.insert(0, SERVICES_DIR)

from generate_financial_forecast import (
    FinancialForecastEngine,
    OUTPUT_JSON_PATH,
    OUTPUT_MD_PATH
)

@pytest.fixture
def forecast_engine():
    return FinancialForecastEngine()

def test_01_5year_projections_structure(forecast_engine):
    """Verifies complete 5-year multi-stream model structure."""
    data = forecast_engine.build_5year_projections()
    
    assert len(data["consolidated"]["years"]) == 5
    assert "software_licenses" in data["streams"]
    assert "turnkey_implementations" in data["streams"]
    assert "recurring_retainer_pods" in data["streams"]
    assert "valuation" in data
    assert "unit_economics" in data

def test_02_stream_c_year3_arr_benchmark(forecast_engine):
    """Verifies that Year 3 ending retainer ARR hits exactly $5.10M across 50 pods."""
    data = forecast_engine.build_5year_projections()
    retainers = data["streams"]["recurring_retainer_pods"]
    
    # Year 3 is index 2
    assert retainers["pods_active"][2] == 50
    assert retainers["ending_mrr_usd"][2] == 425000.00  # 50 * $8,500
    assert retainers["ending_arr_usd"][2] == 5100000.00  # $5.10M ARR
    assert data["valuation"]["y3_retainer_arr_usd"] == 5100000.00

def test_03_software_scaling_to_50k_units(forecast_engine):
    """Verifies software license scaling to 50,000 developer seats and pricing tiers."""
    data = forecast_engine.build_5year_projections()
    software = data["streams"]["software_licenses"]

    assert software["units"][0] == 2500
    assert software["units"][1] == 8000
    assert software["units"][2] == 18000
    assert software["units"][4] == 50000  # 50k units in Year 5

    assert software["pricing_usd"][0] == 29.0
    assert software["pricing_usd"][1] == 49.0
    assert software["pricing_usd"][2] == 79.0
    assert software["revenue_usd"][4] == 3950000.00  # 50k * $79

def test_04_turnkey_deployment_growth(forecast_engine):
    """Verifies enterprise turnkey custom deployment trajectory ($54k per deal)."""
    data = forecast_engine.build_5year_projections()
    turnkey = data["streams"]["turnkey_implementations"]

    assert turnkey["clients"][0] == 10
    assert turnkey["clients"][1] == 30
    assert turnkey["clients"][2] == 65
    assert turnkey["revenue_usd"][0] == 540000.00
    assert turnkey["revenue_usd"][1] == 1620000.00
    assert turnkey["revenue_usd"][2] == 3510000.00

def test_05_cogs_and_gross_margins(forecast_engine):
    """Verifies gross margins exceed benchmarks (82%+ on software, 74%+ on retainers)."""
    data = forecast_engine.build_5year_projections()

    # Software margin target: > 82%
    software_margin = data["streams"]["software_licenses"]["gross_margin_pct"]
    assert software_margin >= 82.0
    assert software_margin == 90.5

    # Retainer margin target: > 74%
    retainer_margin = data["streams"]["recurring_retainer_pods"]["gross_margin_pct"]
    assert retainer_margin >= 74.0
    assert retainer_margin == 75.5

    # Blended consolidated margin should remain between 70% and 80%
    for margin in data["consolidated"]["gross_margin_pct"]:
        assert 70.0 <= margin <= 80.0

def test_06_unit_economics_ltv_cac_ratio(forecast_engine):
    """Verifies that LTV/CAC ratios exceed institutional > 8.5x targets."""
    data = forecast_engine.build_5year_projections()
    u = data["unit_economics"]

    soft_ltv_cac = u["developer_software"]["ltv_cac_ratio"]
    ret_ltv_cac = u["enterprise_retainer"]["ltv_cac_ratio"]

    assert soft_ltv_cac > 8.5
    assert soft_ltv_cac == pytest.approx(17.6, abs=0.5)

    assert ret_ltv_cac > 8.5
    assert ret_ltv_cac == pytest.approx(20.5, abs=0.5)

def test_07_valuation_multiples_and_dcf(forecast_engine):
    """Verifies institutional $45M - $60M valuation bracket and DCF output."""
    data = forecast_engine.build_5year_projections()
    val = data["valuation"]

    assert val["y3_blended_arr_usd"] == 6522000.00  # $5.10M + $1.422M
    assert val["ev_at_8x_arr_usd"] >= 45000000.00
    assert val["ev_at_9_2x_arr_usd"] == pytest.approx(60000000.00, abs=100000.00)
    assert "$45,000,000.00 - $60,000,000.00 USD" in val["established_valuation_range"]

    assert val["dcf_model_enterprise_value_usd"] > 50000000.00

def test_08_artifact_generation_and_brand_anonymity(forecast_engine, tmp_path):
    """Verifies file export and strict 100% Brand Anonymity."""
    test_json = os.path.join(tmp_path, "forecast.json")
    test_md = os.path.join(tmp_path, "valuation.md")

    forecast_engine.execute_and_export(json_output=test_json, md_output=test_md)

    assert os.path.exists(test_json)
    assert os.path.exists(test_md)

    with open(test_md, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Brand identity assertion
    assert "DevSuperSuite Financial Operations" in md_text
    assert "finance@devsupersuite.com" in md_text
    assert "$5,100,000.00 USD in Recurring Enterprise Retainer ARR" in md_text
    assert "$45,000,000.00 to $60,000,000.00 USD" in md_text

    # Negative PII assertion
    assert "pratik" not in md_text.lower()
    assert "atpad" not in md_text.lower()
    assert "+91" not in md_text

def test_09_cli_execution():
    """Tests execution of the forecasting CLI with various flags."""
    script_path = os.path.join(SERVICES_DIR, "generate_financial_forecast.py")

    res = subprocess.run(
        [sys.executable, script_path, "--summary"],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0
    assert "5-Year Valuation & Blended ARR Scorecard" in res.stdout
    assert "Year 3 Retainer ARR:     $5,100,000.00 USD" in res.stdout
    assert "Enterprise Valuation:    $45,000,000.00 - $60,000,000.00 USD" in res.stdout
