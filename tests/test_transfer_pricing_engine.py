"""
⚡ DevSuperSuite Global Treasury & Tax Strategy Desk - Unit & Integration Test Suite
File: test_transfer_pricing_engine.py
Phase: 27 - Global Transfer Pricing & Intercompany OECD BEPS Safe Harbor Engine
Author: DevSuperSuite Global Treasury & Tax Strategy Desk
Strict Compliance: 100% Brand Anonymity - DevSuperSuite Global Treasury & Tax Strategy Desk Only (treasury@devsupersuite.com).
"""

import os
import sys
import json
import subprocess
import pytest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(PROJECT_ROOT, "services")
DATA_DIR = os.path.join(SERVICES_DIR, "data")
ROOT_DATA_DIR = os.path.join(PROJECT_ROOT, "data")
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")

sys.path.insert(0, PROJECT_ROOT)

from services.enterprise_transfer_pricing_engine import (
    EnterpriseTransferPricingEngine,
    BENCHMARK_INTERQUARTILE_RANGES,
    DEMPE_FUNCTIONS,
    DOUBLE_TAX_TREATY_MATRIX,
    BASELINE_GROUP_FINANCIALS,
    DEFAULT_TP_SCHEDULE_FILE,
    ROOT_TP_SCHEDULE_FILE,
    DEFAULT_TP_BINDER_FILE
)

FORBIDDEN_FOUNDER_TOKENS = [
    "Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"
]


@pytest.fixture
def engine():
    return EnterpriseTransferPricingEngine()


def test_01_cup_method_arm_length_benchmark(engine):
    """Verifies Comparable Uncontrolled Price (CUP) method calculation and interquartile boundary audit."""
    # Compliant case (18.5% median)
    res_compliant = engine.calculate_arm_length_methods(cup_applied_royalty_pct=18.50)
    cup = res_compliant["cup_method"]
    assert cup["is_arms_length_compliant"] is True
    assert cup["status"] == "ARM_LENGTH_COMPLIANT"
    assert cup["annual_intercompany_royalty_usd"] == 71225.00
    assert cup["applied_royalty_rate_pct"] == 18.50

    # Non-compliant low case (10.0% < 15.0% lower quartile)
    res_low = engine.calculate_arm_length_methods(cup_applied_royalty_pct=10.00)
    assert res_low["cup_method"]["is_arms_length_compliant"] is False
    assert res_low["cup_method"]["status"] == "AUDIT_FLAG_OUT_OF_RANGE"

    # Non-compliant high case (28.0% > 22.0% upper quartile)
    res_high = engine.calculate_arm_length_methods(cup_applied_royalty_pct=28.00)
    assert res_high["cup_method"]["is_arms_length_compliant"] is False
    assert res_high["cup_method"]["status"] == "AUDIT_FLAG_OUT_OF_RANGE"


def test_02_tnmm_distributor_margin_benchmark(engine):
    """Verifies Transactional Net Margin Method (TNMM) calculation and operating margin benchmarks."""
    # Compliant case (4.5% median)
    res_compliant = engine.calculate_arm_length_methods(tnmm_applied_margin_pct=4.50)
    tnmm = res_compliant["tnmm_method"]
    assert tnmm["is_arms_length_compliant"] is True
    assert tnmm["status"] == "ARM_LENGTH_COMPLIANT"
    assert tnmm["distributor_operating_profit_usd"] > 25000.0
    assert tnmm["residual_licensor_royalty_remitted_usd"] > 500000.0

    # Non-compliant low case (2.0% < 3.10% lower quartile)
    res_low = engine.calculate_arm_length_methods(tnmm_applied_margin_pct=2.00)
    assert res_low["tnmm_method"]["is_arms_length_compliant"] is False
    assert res_low["tnmm_method"]["status"] == "AUDIT_FLAG_OUT_OF_RANGE"

    # Non-compliant high case (8.0% > 5.80% upper quartile)
    res_high = engine.calculate_arm_length_methods(tnmm_applied_margin_pct=8.00)
    assert res_high["tnmm_method"]["is_arms_length_compliant"] is False
    assert res_high["tnmm_method"]["status"] == "AUDIT_FLAG_OUT_OF_RANGE"


def test_03_cpm_contract_rd_benchmark(engine):
    """Verifies Cost Plus Method (CPM) calculation for offshore R&D Center of Excellence."""
    # Compliant case (10.0% median)
    res_compliant = engine.calculate_arm_length_methods(cpm_applied_markup_pct=10.00)
    cpm = res_compliant["cpm_method"]
    assert cpm["is_arms_length_compliant"] is True
    assert cpm["status"] == "ARM_LENGTH_COMPLIANT"
    assert cpm["allowable_cost_base_usd"] == 85000.00
    assert cpm["operating_profit_markup_usd"] == 8500.00
    assert cpm["total_intercompany_rd_invoice_usd"] == 93500.00

    # Non-compliant low case (5.0% < 8.00% lower quartile)
    res_low = engine.calculate_arm_length_methods(cpm_applied_markup_pct=5.00)
    assert res_low["cpm_method"]["is_arms_length_compliant"] is False
    assert res_low["cpm_method"]["status"] == "AUDIT_FLAG_OUT_OF_RANGE"

    # Non-compliant high case (16.0% > 12.00% upper quartile)
    res_high = engine.calculate_arm_length_methods(cpm_applied_markup_pct=16.00)
    assert res_high["cpm_method"]["is_arms_length_compliant"] is False
    assert res_high["cpm_method"]["status"] == "AUDIT_FLAG_OUT_OF_RANGE"


def test_04_dempe_functions_and_substance_scoring(engine):
    """Verifies OECD BEPS Action 8-10 DEMPE functions allocation and substance score."""
    dempe = engine.evaluate_dempe_substance()

    assert dempe["framework"] == "OECD BEPS Action 8-10 Intangibles Chapter VI"
    assert dempe["total_dempe_weight_pct"] == 100.0
    assert dempe["aggregate_dempe_substance_score"] >= 90.0, "Substance score must be >= 90.0"
    assert dempe["substance_classification"] == "EXCELLENT_SUBSTANCE"
    assert dempe["total_dedicated_personnel_ftes"] >= 20

    elements = {d["dempe_element"] for d in dempe["dempe_functions_breakdown"]}
    expected_elements = {
        "Development (D)",
        "Enhancement (E)",
        "Maintenance (M)",
        "Protection (P)",
        "Exploitation (E)"
    }
    assert expected_elements.issubset(elements)


def test_05_cbcr_table_structure_and_equilibrium(engine):
    """Verifies OECD BEPS Action 13 Country-by-Country Reporting (CbCR) table generation."""
    beps = engine.generate_beps_documentation()
    cbcr = beps["cbcr_table"]
    summary = beps["cbcr_summary"]

    assert len(cbcr) == 6, "Must cover US, IE, UK, DE, SG, IN"
    jurisdictions = {c["iso_code"] for c in cbcr}
    assert {"US", "IE", "UK", "DE", "SG", "IN"}.issubset(jurisdictions)

    assert summary["total_unrelated_revenue_usd"] > 550000.0
    assert summary["total_profit_before_tax_usd"] > 400000.0
    assert summary["total_tax_paid_usd"] > 50000.0
    assert 10.0 <= summary["effective_tax_rate_pct"] <= 20.0
    assert summary["total_group_ftes"] >= 20


def test_06_double_tax_treaty_withholding_matrix(engine):
    """Verifies bilateral Double Tax Treaty (DTT) matrix and withholding tax optimization."""
    wht = engine.audit_wht_treaties()

    assert wht["total_statutory_withholding_usd"] > 150000.0
    assert wht["total_treaty_reduced_withholding_usd"] < 25000.0
    assert wht["total_withholding_tax_savings_usd"] > 140000.0
    assert wht["withholding_reduction_efficiency_pct"] >= 85.0

    corridors = {c["corridor"]: c for c in wht["treaty_corridors"]}

    # US -> Ireland (0% treaty WHT on royalties)
    us_ie = corridors["US -> IE"]
    assert us_ie["treaty_reduced_wht_pct"] == 0.0
    assert us_ie["statutory_wht_pct"] == 30.0
    assert us_ie["net_wht_savings_usd"] == 115500.00
    assert us_ie["lob_compliant"] is True

    # US -> India (15% treaty WHT vs 30% statutory)
    us_in = corridors["US -> IN"]
    assert us_in["treaty_reduced_wht_pct"] == 15.0
    assert us_in["statutory_wht_pct"] == 30.0
    assert us_in["net_wht_savings_usd"] == 14025.00


def test_07_permanent_establishment_risk_scoring(engine):
    """Verifies Permanent Establishment (PE) risk scoring and safe harbor compliance."""
    pe = engine.assess_permanent_establishment_risk()

    assert pe["total_pe_risk_score"] <= pe["maximum_risk_threshold"], "PE score must be within safe harbor"
    assert pe["safe_harbor_status"] == "LOW_RISK_SAFE_HARBOR_CONFIRMED"
    assert pe["all_safe_harbors_met"] is True
    assert pe["risk_percentage"] < 15.0

    for v in pe["pe_vectors"]:
        assert v["status"] == "SAFE_HARBOR_SATISFIED"
        assert v["risk_score_points"] <= 5.0


def test_08_master_and_local_file_components(engine):
    """Verifies Master File and Local File institutional documentation structure."""
    beps = engine.generate_beps_documentation()

    # Master file checks
    mf = beps["master_file"]
    assert mf["document_type"] == "OECD BEPS Action 13 Master File"
    assert mf["mne_group_name"] == "DevSuperSuite Group"
    assert "Ireland" in mf["global_headquarters"]

    # Local file checks
    lf = beps["local_file"]
    assert lf["document_type"] == "OECD BEPS Action 13 Local File"
    assert len(lf["tested_entities"]) == 2
    roles = {t["role"] for t in lf["tested_entities"]}
    assert "Limited-Risk Distributor" in roles
    assert "Contract R&D Center of Excellence" in roles


def test_09_artifact_export_and_json_persistence(engine):
    """Verifies proper persistence of JSON transfer pricing schedule and Markdown dossier."""
    paths = engine.export_all_artifacts()

    for key, path in paths.items():
        assert os.path.exists(path), f"File {path} was not created"

    # Verify JSON schedule
    with open(paths["schedule_path"], "r", encoding="utf-8") as f:
        schedule = json.load(f)
    assert schedule["metadata"]["reporting_entity"] == "DevSuperSuite Group"
    assert "arm_length_methods" in schedule
    assert "beps_documentation" in schedule
    assert "withholding_tax_optimizer" in schedule
    assert "permanent_establishment_audit" in schedule

    # Verify Markdown binder
    with open(paths["binder_path"], "r", encoding="utf-8") as f:
        binder_md = f.read()
    assert "GLOBAL TRANSFER PRICING & INTERCOMPANY OECD BEPS SAFE HARBOR DOSSIER" in binder_md
    assert "Comparable Uncontrolled Price (CUP)" in binder_md
    assert "Transactional Net Margin Method (TNMM)" in binder_md
    assert "Cost Plus Method (CPM)" in binder_md
    assert "Country-by-Country Reporting (CbCR)" in binder_md


def test_10_cli_command_executions():
    """Verifies multi-action CLI flags execute cleanly."""
    script_path = os.path.join(SERVICES_DIR, "enterprise_transfer_pricing_engine.py")

    cmd = [
        sys.executable,
        script_path,
        "--calculate-arm-length",
        "--generate-beps-files",
        "--audit-wht-treaties",
        "--assess-pe-risk",
        "--export-transfer-pricing-binder",
        "--summary"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"CLI execution failed: {res.stderr}"
    assert "Arm's Length Principle (ALP) Multi-Method Benchmark Audit" in res.stdout
    assert "OECD BEPS Action 8-10 DEMPE Substance & CbCR Reporting" in res.stdout
    assert "Bilateral Double Tax Treaty (DTT) Withholding Tax Optimizer" in res.stdout
    assert "Permanent Establishment (PE) Risk & Safe Harbor Audit" in res.stdout


def test_11_strict_brand_anonymity():
    """Verifies 100% Brand Anonymity across all Phase 27 files."""
    files_to_check = [
        os.path.join(SERVICES_DIR, "enterprise_transfer_pricing_engine.py"),
        os.path.join(REPORTS_DIR, "global_transfer_pricing_beps_dossier.md"),
        os.path.join(DATA_DIR, "transfer_pricing_schedule.json"),
        os.path.join(ROOT_DATA_DIR, "transfer_pricing_schedule.json")
    ]

    for file_path in files_to_check:
        assert os.path.exists(file_path), f"File {file_path} must exist for anonymity check"
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().lower()
        for token in FORBIDDEN_FOUNDER_TOKENS:
            assert token.lower() not in content, (
                f"Forbidden founder token '{token}' detected in {file_path}!"
            )
