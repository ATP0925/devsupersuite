"""
⚡ DevSuperSuite Global Treasury Desk - ASC 606 & IFRS 15 Revenue Recognition Test Suite
File: test_asc606_revrec.py
Target: enterprise_asc606_revrec_engine.py
Strict Compliance: 100% Brand Anonymity - DevSuperSuite Global Treasury Desk Only (treasury@devsupersuite.com).
"""

import os
import sys
import json
import subprocess
import pytest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(PROJECT_ROOT, "services")
sys.path.insert(0, SERVICES_DIR)

from enterprise_asc606_revrec_engine import (
    EnterpriseASC606RevRecEngine,
    SSP_CATALOG_BENCHMARKS,
    SAMPLE_ENTERPRISE_CONTRACTS,
    CORPORATE_ENTITY_NAME,
    TREASURY_DESK_TITLE,
    TREASURY_OFFICIAL_EMAIL,
    DEFAULT_REVREC_SCHEDULE_FILE,
    ROOT_REVREC_SCHEDULE_FILE,
    DEFAULT_REVREC_REPORT_FILE
)


@pytest.fixture
def revrec_engine():
    """Initializes the institutional ASC 606 & IFRS 15 revenue recognition engine."""
    return EnterpriseASC606RevRecEngine()


def test_01_asc606_5step_framework_compliance(revrec_engine):
    """Verifies that the engine complies with the 5-step model under US GAAP ASC 606 and IFRS 15."""
    alloc = revrec_engine.allocate_ssp_fair_value()
    assert alloc["accounting_standard"] == "US GAAP ASC 606 / IFRS 15"
    assert alloc["allocation_methodology"] == "Relative Fair Value Standalone Selling Price (SSP)"
    assert alloc["total_contracts_analyzed"] == 4
    assert alloc["total_portfolio_tcv_usd"] == 168797.60


def test_02_distinct_performance_obligations_mapping(revrec_engine):
    """Verifies that distinct performance obligations (POBs) are correctly mapped with recognition patterns."""
    alloc = revrec_engine.allocate_ssp_fair_value()
    first_contract = alloc["contract_allocations"][0]
    pobs = {p["element_key"]: p for p in first_contract["performance_obligations"]}

    assert "TERM_SOFTWARE_LICENSE" in pobs
    assert pobs["TERM_SOFTWARE_LICENSE"]["recognition_pattern"] == "POINT_IN_TIME"
    assert pobs["TERM_SOFTWARE_LICENSE"]["pob_code"] == "POB-01"

    assert "MAINTENANCE_AND_SLA" in pobs
    assert pobs["MAINTENANCE_AND_SLA"]["recognition_pattern"] == "OVER_TIME_RATABLE"
    assert pobs["MAINTENANCE_AND_SLA"]["pob_code"] == "POB-02"

    assert "AIRGAP_SCIF_TAM_SUPPORT" in pobs
    assert pobs["AIRGAP_SCIF_TAM_SUPPORT"]["recognition_pattern"] == "OVER_TIME_RATABLE"
    assert pobs["AIRGAP_SCIF_TAM_SUPPORT"]["pob_code"] == "POB-03"


def test_03_relative_ssp_allocation_fair_value(revrec_engine):
    """Verifies relative fair value SSP mathematics (allocated amounts sum exactly to TCV for each contract)."""
    alloc = revrec_engine.allocate_ssp_fair_value()

    for contract in alloc["contract_allocations"]:
        pobs_allocated_sum = sum(p["allocated_transaction_price_usd"] for p in contract["performance_obligations"])
        assert round(pobs_allocated_sum, 2) == contract["total_contract_value_usd"]
        
        # Verify relative weights sum to 100%
        weight_sum = sum(p["relative_ssp_weight_pct"] for p in contract["performance_obligations"])
        assert 99.9 <= weight_sum <= 100.1


def test_04_point_in_time_vs_over_time_mix(revrec_engine):
    """Verifies portfolio mix between upfront point-in-time delivery and over-time ratable subscription services."""
    alloc = revrec_engine.allocate_ssp_fair_value()
    
    assert alloc["total_allocated_point_in_time_usd"] == 80083.27
    assert alloc["total_allocated_over_time_usd"] == 88714.33
    assert alloc["point_in_time_mix_pct"] == 47.44
    assert alloc["over_time_mix_pct"] == 52.56
    assert round(alloc["total_allocated_point_in_time_usd"] + alloc["total_allocated_over_time_usd"], 2) == 168797.60


def test_05_multi_year_monthly_amortization_waterfall(revrec_engine):
    """Verifies 36-month monthly revenue recognition waterfall across multi-year contracts."""
    wf = revrec_engine.generate_revrec_waterfall(max_horizon_months=36)
    
    assert len(wf["monthly_waterfall"]) == 36
    assert wf["total_contract_value_usd"] == 168797.60
    assert wf["year_1_recognized_revenue_usd"] == 119218.51
    assert wf["year_2_recognized_revenue_usd"] == 35135.28
    assert wf["year_3_recognized_revenue_usd"] == 14443.92
    assert wf["final_deferred_revenue_balance_usd"] == 0.00


def test_06_balance_sheet_deferred_revenue_rollforward(revrec_engine):
    """Verifies zero-variance balance sheet roll-forward of Contract Liabilities (Deferred Revenue)."""
    rec = revrec_engine.reconcile_deferred_revenue()
    
    assert rec["reconciliation_status"] == "ZERO_VARIANCE_BALANCED"
    assert rec["balance_sheet_variance_usd"] == 0.00
    assert rec["gross_contract_bookings_tcv_usd"] == 168797.60
    assert rec["year_1_recognized_revenue_usd"] == 119218.51
    assert rec["ending_deferred_revenue_liability_usd"] == 49579.09


def test_07_upfront_vs_ratable_timing_differences(revrec_engine):
    """Verifies Month 1 point-in-time upfront recognition vs subsequent monthly ratable service amortizations."""
    wf = revrec_engine.generate_revrec_waterfall()
    month_1 = wf["monthly_waterfall"][0]
    month_2 = wf["monthly_waterfall"][1]

    # Month 1 includes all upfront license delivery revenue
    assert month_1["point_in_time_recognized_usd"] == 80083.27
    assert month_1["total_month_recognized_usd"] > 80000.00

    # Month 2 has zero point-in-time and only ongoing ratable service revenue
    assert month_2["point_in_time_recognized_usd"] == 0.00
    assert month_2["over_time_recognized_usd"] > 0.00
    assert month_2["total_month_recognized_usd"] < 5000.00


def test_08_multi_contract_portfolio_integrity(revrec_engine):
    """Verifies contract portfolio diversity across defense, fintech, mission systems, and enterprise data."""
    alloc = revrec_engine.allocate_ssp_fair_value()
    customers = [c["customer_name"] for c in alloc["contract_allocations"]]
    
    assert "Lockheed Martin Enterprise" in customers
    assert "Barclays Capital Engineering" in customers
    assert "Raytheon Intelligence & Space" in customers
    assert "Palantir Tech Commercial" in customers


def test_09_revrec_schedule_json_persistence(revrec_engine):
    """Verifies export of JSON schedule files and mirrored persistence."""
    paths = revrec_engine.export_all()
    
    assert os.path.exists(paths["schedule_file"])
    assert os.path.exists(paths["root_schedule_file"])
    assert os.path.exists(paths["report_file"])

    with open(paths["schedule_file"], "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["binder_id"] == "DSS-ASC606-2026-REVREC-BINDER"
        assert data["executive_summary"]["total_tcv_usd"] == 168797.60
        assert data["executive_summary"]["year_1_recognized_revenue_usd"] == 119218.51
        assert "ssp_allocations" in data
        assert "monthly_waterfall" in data


def test_10_audit_report_markdown_integrity(revrec_engine):
    """Verifies that the markdown report contains executive dashboards, tables, and Mermaid flowcharts."""
    paths = revrec_engine.export_all()
    
    with open(paths["report_file"], "r", encoding="utf-8") as f:
        md = f.read()
        assert "DevSuperSuite Global Treasury Desk" in md
        assert "US GAAP ASC 606" in md
        assert "$168,797.60" in md
        assert "$119,218.51" in md
        assert "ZERO_VARIANCE_BALANCED" in md
        assert "flowchart TD" in md


def test_11_cli_interface_execution():
    """Smoke tests all CLI arguments for the ASC 606 revenue recognition engine."""
    cli_flags = [
        "--audit-contracts-asc606",
        "--allocate-ssp-fair-value",
        "--generate-revrec-waterfall",
        "--reconcile-deferred-revenue",
        "--export-revrec-binder",
        "--summary"
    ]
    script_path = os.path.join(SERVICES_DIR, "enterprise_asc606_revrec_engine.py")

    for flag in cli_flags:
        res = subprocess.run(
            [sys.executable, script_path, flag],
            capture_output=True,
            text=True
        )
        assert res.returncode == 0, f"CLI flag {flag} failed: {res.stderr}"
        assert len(res.stdout.strip()) > 0


def test_12_brand_anonymity_strict_compliance():
    """Verifies 100% Brand Anonymity Protocol: zero forbidden founder names or private emails."""
    forbidden_tokens = ["Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"]
    target_files = [
        os.path.join(SERVICES_DIR, "enterprise_asc606_revrec_engine.py"),
        DEFAULT_REVREC_SCHEDULE_FILE,
        ROOT_REVREC_SCHEDULE_FILE,
        DEFAULT_REVREC_REPORT_FILE
    ]

    for fpath in target_files:
        assert os.path.exists(fpath), f"File {fpath} must exist for anonymity check"
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            for token in forbidden_tokens:
                assert token not in content, f"Forbidden brand anonymity token '{token}' discovered in {fpath}"
