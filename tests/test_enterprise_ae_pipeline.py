"""
⚡ DevSuperSuite Official: Enterprise AE Deal Pipeline & MEDDPICC Tests
File: test_enterprise_ae_pipeline.py
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

from services.enterprise_ae_pipeline_engine import (
    MEDDPICCScoreCalculator,
    DiscountGovernanceEngine,
    EnterpriseAEPipelineManager,
    DEFAULT_PIPELINE_PATH,
    BACKUP_PIPELINE_PATH,
    REPORT_PATH,
    STAGE_PROBABILITIES,
)


@pytest.fixture
def pipeline_manager():
    return EnterpriseAEPipelineManager(DEFAULT_PIPELINE_PATH)


def test_01_pipeline_database_integrity(pipeline_manager):
    """Verify active enterprise deals pipeline contains 15 high-value opportunities."""
    deals = pipeline_manager.deals
    assert len(deals) >= 15, f"Expected at least 15 deals, found {len(deals)}"

    stages_present = set()
    for d in deals:
        assert "deal_id" in d
        assert "company_name" in d
        assert "domain" in d
        assert "deal_stage" in d
        assert "stage_probability" in d
        assert "target_acv_usd" in d
        assert d["target_acv_usd"] >= 14000
        assert "discount_percentage" in d
        assert "meddpicc" in d
        stages_present.add(d["deal_stage"])

    # Verify key stages are covered
    assert "Stage 1: Technical Discovery" in stages_present
    assert "Stage 2: Architecture PoC (30-day airgap)" in stages_present
    assert "Stage 3: Infosec & Legal Redlines" in stages_present
    assert "Stage 4: Procurement & Vendor Solvency Approval" in stages_present
    assert "Stage 5: Mutual Action Plan (MAP)" in stages_present
    assert "Stage 6: Closed-Won Execution" in stages_present


def test_02_meddpicc_score_calculation_and_thresholds():
    """Verify MEDDPICC scoring algorithm across 8 dimensions and qualification tiers."""
    # 1. Perfect score deal (12.5 * 8 = 100)
    perfect_meddpicc = {dim: 12.5 for dim in MEDDPICCScoreCalculator.DIMENSIONS}
    res_perfect = MEDDPICCScoreCalculator.calculate_deal_meddpicc(perfect_meddpicc)
    assert res_perfect["total_score"] == 100.0
    assert res_perfect["qualification_status"] == "HIGHLY_QUALIFIED"
    assert res_perfect["health_color"] == "GREEN"

    # 2. Moderate score deal (10.0 * 8 = 80)
    moderate_meddpicc = {dim: 10.0 for dim in MEDDPICCScoreCalculator.DIMENSIONS}
    res_mod = MEDDPICCScoreCalculator.calculate_deal_meddpicc(moderate_meddpicc)
    assert res_mod["total_score"] == 80.0
    assert res_mod["qualification_status"] == "QUALIFIED_WITH_GAPS"
    assert res_mod["health_color"] == "YELLOW"

    # 3. Low discovery score deal (7.0 * 8 = 56)
    low_meddpicc = {dim: 7.0 for dim in MEDDPICCScoreCalculator.DIMENSIONS}
    res_low = MEDDPICCScoreCalculator.calculate_deal_meddpicc(low_meddpicc)
    assert res_low["total_score"] == 56.0
    assert res_low["qualification_status"] == "AT_RISK_DISCOVERY"
    assert res_low["health_color"] == "RED"

    # 4. Score clamping test
    over_meddpicc = {dim: 25.0 for dim in MEDDPICCScoreCalculator.DIMENSIONS}
    res_clamp = MEDDPICCScoreCalculator.calculate_deal_meddpicc(over_meddpicc)
    assert res_clamp["total_score"] == 100.0


def test_03_discount_governance_rules_and_approval_routing():
    """Verify discount thresholds and approval tiers across contract sizes."""
    # 1. Tier 1 (<$50k): max 5%
    tier1_pass = DiscountGovernanceEngine.evaluate_discount(42000, 5.0)
    assert tier1_pass["is_auto_approved"] is True
    assert tier1_pass["approval_tier"] == "STANDARD_AUTO_APPROVED"
    assert tier1_pass["net_arr_usd"] == 39900.0

    tier1_fail = DiscountGovernanceEngine.evaluate_discount(42000, 10.0)
    assert tier1_fail["is_auto_approved"] is False
    assert tier1_fail["approval_tier"] == "DIRECTOR_APPROVAL_REQUIRED"

    # 2. Tier 2 ($50k-$100k): max 10%
    tier2_pass = DiscountGovernanceEngine.evaluate_discount(80000, 10.0)
    assert tier2_pass["is_auto_approved"] is True

    # 3. Tier 3 ($100k-$250k): max 18%
    tier3_pass = DiscountGovernanceEngine.evaluate_discount(250000, 15.0)
    assert tier3_pass["is_auto_approved"] is True
    assert tier3_pass["net_arr_usd"] == 212500.0

    # 4. Exception Tier (>20%): requires VP of Sales approval
    tier_high = DiscountGovernanceEngine.evaluate_discount(120000, 25.0)
    assert tier_high["is_auto_approved"] is False
    assert tier_high["approval_tier"] == "VP_SALES_APPROVAL_REQUIRED"


def test_04_stage_win_probability_and_weighted_arr(pipeline_manager):
    """Verify stage win probabilities and risk-adjusted weighted ARR calculation."""
    metrics = pipeline_manager.calculate_pipeline_metrics()
    assert metrics["total_deals_count"] >= 15
    assert metrics["total_unweighted_acv_usd"] > 1800000.0
    assert metrics["total_net_arr_usd"] > 1700000.0
    assert metrics["total_weighted_forecast_arr_usd"] > 1000000.0
    assert metrics["blended_pipeline_win_rate_pct"] > 50.0

    # Verify stage probability mapping
    for stage_name, prob in STAGE_PROBABILITIES.items():
        assert prob >= 0.0 and prob <= 1.0


def test_05_deal_lookup_and_audit_validation(pipeline_manager):
    """Verify individual deal lookup by ID and pipeline compliance audit."""
    deal_rtx = pipeline_manager.get_deal_by_id("DEAL-RTX-2026-01")
    assert deal_rtx is not None
    assert "Raytheon" in deal_rtx["company_name"]
    assert deal_rtx["target_acv_usd"] == 250000

    audit = pipeline_manager.audit_pipeline()
    assert audit["audit_status"] in ["PASSED", "WARNINGS_FOUND"]
    assert "enterprise@devsupersuite.com" in audit["governing_authority"]


def test_06_mutual_action_plan_generation(pipeline_manager):
    """Verify automated 30-Day Mutual Action Plan (MAP) document compilation."""
    map_text = pipeline_manager.generate_mutual_action_plan("DEAL-RTX-2026-01")
    assert "# ⚡ DevSuperSuite Enterprise Mutual Action Plan (MAP)" in map_text
    assert "Raytheon Technologies" in map_text
    assert "30-Day Milestone Execution Schedule" in map_text
    assert "enterprise@devsupersuite.com" in map_text
    assert "Zero Founder Personal Identifiers" in map_text


def test_07_forecast_report_export(pipeline_manager):
    """Verify formal markdown pipeline forecast report generation."""
    out_path = pipeline_manager.render_forecast_report()
    assert os.path.exists(out_path)

    with open(out_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "# ⚡ DevSuperSuite Official: Enterprise Pipeline & MEDDPICC Forecast Report" in content
    assert "Executive Pipeline Summary" in content
    assert "Pipeline Stage Distribution & Weighted ARR" in content
    assert "High-Priority Enterprise Opportunities Ledger" in content
    assert "enterprise@devsupersuite.com" in content


def test_08_cli_commands_execution():
    """Verify all CLI subcommands and flags execute successfully with exit code 0."""
    python_bin = sys.executable
    script_path = os.path.join(SERVICES_DIR, "enterprise_ae_pipeline_engine.py")

    flags = [
        ["--summary"],
        ["--audit-pipeline-stages"],
        ["--score-deal-meddpicc", "DEAL-RTX-2026-01"],
        ["--export-pipeline-forecast"],
        ["--generate-mutual-action-plan", "DEAL-RTX-2026-01"],
    ]

    for flag_group in flags:
        cmd = [python_bin, script_path] + flag_group
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        assert res.returncode == 0, f"Command {cmd} failed with stderr: {res.stderr}"


def test_09_strict_brand_anonymity():
    """Verify zero personal founder leaks across all Phase 23 assets."""
    forbidden_tokens = [
        bytes.fromhex("41746861727661").decode("utf-8"),
        bytes.fromhex("506164687965").decode("utf-8"),
        bytes.fromhex("39383930343431323933").decode("utf-8"),
    ]

    phase_23_files = [
        Path(SERVICES_DIR) / "enterprise_ae_pipeline_engine.py",
        Path(DATA_DIR) / "enterprise_active_deals_pipeline.json",
        Path(MARKETING_DIR) / "enterprise_deal_closing_playbook.md",
        Path(REPORTS_DIR) / "enterprise_pipeline_forecast_report.md",
        Path(TESTS_DIR) / "test_enterprise_ae_pipeline.py",
    ]

    for file_path in phase_23_files:
        assert file_path.exists(), f"File {file_path} must exist"
        content = file_path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token.lower() not in content.lower(), (
                f"Brand anonymity violation: found forbidden token in {file_path}"
            )
