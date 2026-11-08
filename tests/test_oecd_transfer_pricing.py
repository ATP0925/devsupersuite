"""
⚡ DevSuperSuite Global Treasury Desk - OECD BEPS Transfer Pricing & CSA Test Suite
File: test_oecd_transfer_pricing.py
Target: enterprise_oecd_transfer_pricing_engine.py
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

from enterprise_oecd_transfer_pricing_engine import (
    EnterpriseOECDTransferPricingEngine,
    INTERCOMPANY_ENTITIES,
    ANNUAL_IDC_POOL_USD,
    RAB_SHARES,
    GROUP_PARENT_ENTITY,
    TREASURY_DESK_TITLE,
    TREASURY_OFFICIAL_EMAIL,
    DEFAULT_TP_SCHEDULE_FILE,
    ROOT_TP_SCHEDULE_FILE,
    DEFAULT_TP_REPORT_FILE
)


@pytest.fixture
def tp_engine():
    """Initializes the institutional OECD transfer pricing engine."""
    return EnterpriseOECDTransferPricingEngine()


def test_01_intercompany_entity_topology(tp_engine):
    """Verifies that all 3 intercompany entities (US Principal, Ireland EMEA Hub, Singapore APAC Hub) are configured."""
    csa = tp_engine.audit_csa_cost_sharing()
    assert len(csa["csa_allocations"]) == 3
    expected_entities = {"US_PARENT", "IE_EMEA", "SG_APAC"}
    assert set(csa["csa_allocations"].keys()) == expected_entities

    # Verify legal entity names
    assert INTERCOMPANY_ENTITIES["US_PARENT"]["entity_name"] == GROUP_PARENT_ENTITY
    assert "DevSuperSuite EMEA Limited" in INTERCOMPANY_ENTITIES["IE_EMEA"]["entity_name"]
    assert "DevSuperSuite APAC Pte. Ltd." in INTERCOMPANY_ENTITIES["SG_APAC"]["entity_name"]


def test_02_csa_cost_sharing_rab_allocation(tp_engine):
    """Verifies Reasonably Anticipated Benefits (RAB) revenue shares: US 75%, IE 18%, SG 7%."""
    csa = tp_engine.audit_csa_cost_sharing()
    allocs = csa["csa_allocations"]

    assert allocs["US_PARENT"]["rab_share_pct"] == 75.0
    assert allocs["IE_EMEA"]["rab_share_pct"] == 18.0
    assert allocs["SG_APAC"]["rab_share_pct"] == 7.0
    assert sum(a["rab_share_pct"] for a in allocs.values()) == 100.0


def test_03_idc_pool_and_regional_reimbursements(tp_engine):
    """Verifies $125k Intangible Development Cost pool and $31,250 total regional reimbursements."""
    csa = tp_engine.audit_csa_cost_sharing()
    
    assert csa["annual_intangible_development_costs_usd"] == 125000.00
    assert csa["total_regional_csa_contributions_usd"] == 31250.00
    assert csa["net_us_borne_rd_costs_usd"] == 93750.00

    allocs = csa["csa_allocations"]
    assert allocs["IE_EMEA"]["csa_true_up_reimbursement_to_us_usd"] == 22500.00
    assert allocs["SG_APAC"]["csa_true_up_reimbursement_to_us_usd"] == 8750.00


def test_04_cup_software_ip_royalty_benchmark(tp_engine):
    """Verifies tested 18.00% software royalty falls within 15.00%-22.00% interquartile safe harbor."""
    alp = tp_engine.benchmark_arm_length()
    cup = alp["benchmarks"]["CUP_SOFTWARE_ROYALTY"]

    assert cup["methodology"] == "Comparable Uncontrolled Price (CUP)"
    assert cup["lower_quartile_pct"] == 15.00
    assert cup["median_pct"] == 18.50
    assert cup["upper_quartile_pct"] == 22.00
    assert cup["tested_rate_pct"] == 18.00
    assert cup["interquartile_position"] == "SAFE_HARBOR_ALIGNED"


def test_05_tnmm_operating_margin_benchmarks(tp_engine):
    """Verifies EMEA (4.60%) and APAC (4.40%) distribution margins fall within 3.10%-5.80% TNMM safe harbor."""
    alp = tp_engine.benchmark_arm_length()
    emea = alp["benchmarks"]["TNMM_EMEA_DISTRIBUTOR"]
    apac = alp["benchmarks"]["TNMM_APAC_DISTRIBUTOR"]

    assert emea["tested_rate_pct"] == 4.60
    assert emea["interquartile_position"] == "SAFE_HARBOR_ALIGNED"

    assert apac["tested_rate_pct"] == 4.40
    assert apac["interquartile_position"] == "SAFE_HARBOR_ALIGNED"
    assert alp["overall_alp_compliance"] == "CONFIRMED_ARM_LENGTH"


def test_06_dempe_scoring_weights_and_breakdown(tp_engine):
    """Verifies DEMPE category weights sum to 100% across all 5 functions."""
    dempe = tp_engine.calculate_dempe_scoring()
    cats = dempe["dempe_categories"]

    assert cats["DEVELOPMENT"]["weight_pct"] == 30.0
    assert cats["ENHANCEMENT"]["weight_pct"] == 25.0
    assert cats["MAINTENANCE"]["weight_pct"] == 15.0
    assert cats["PROTECTION"]["weight_pct"] == 15.0
    assert cats["EXPLOITATION"]["weight_pct"] == 15.0
    assert sum(c["weight_pct"] for c in cats.values()) == 100.0


def test_07_dempe_economic_value_allocation(tp_engine):
    """Verifies US DEMPE score is 67.75%, EMEA is 20.00%, APAC is 12.25%."""
    dempe = tp_engine.calculate_dempe_scoring()
    scores = dempe["entity_dempe_scores"]

    assert scores["US_PARENT"]["dempe_weighted_score_pct"] == 67.75
    assert scores["IE_EMEA"]["dempe_weighted_score_pct"] == 20.00
    assert scores["SG_APAC"]["dempe_weighted_score_pct"] == 12.25
    assert round(sum(s["dempe_weighted_score_pct"] for s in scores.values()), 2) == 100.00


def test_08_oecd_action13_cbcr_table1(tp_engine):
    """Verifies OECD Action 13 Country-by-Country Reporting (CbCR) Table 1 revenue consolidation."""
    cbcr = tp_engine.generate_cbcr_tables()
    
    assert cbcr["global_consolidated_unrelated_revenues_usd"] == 558992.16
    assert cbcr["global_full_time_headcount"] == 24
    assert len(cbcr["cbcr_table_1"]) == 3

    # Check US unrelated revenues
    us_row = next(r for r in cbcr["cbcr_table_1"] if r["tax_jurisdiction"] == "United States")
    assert us_row["unrelated_party_revenues_usd"] == 429000.00
    assert us_row["related_party_csa_revenues_usd"] == 31250.00


def test_09_transfer_pricing_schedule_json_persistence(tp_engine):
    """Verifies export of transfer pricing schedule JSON files and mirrored persistence."""
    paths = tp_engine.export_all()
    
    assert os.path.exists(paths["schedule_file"])
    assert os.path.exists(paths["root_schedule_file"])
    assert os.path.exists(paths["report_file"])

    with open(paths["schedule_file"], "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["binder_id"] == "DSS-OECD-TP-2026-DOSSIER"
        assert data["executive_summary"]["annual_idc_pool_usd"] == 125000.00
        assert data["executive_summary"]["cup_royalty_tested_rate_pct"] == 18.00
        assert "cost_sharing_arrangement" in data
        assert "arm_length_benchmarks" in data


def test_10_defense_report_markdown_integrity(tp_engine):
    """Verifies that the markdown report contains executive summaries, tables, and Mermaid flowcharts."""
    paths = tp_engine.export_all()
    
    with open(paths["report_file"], "r", encoding="utf-8") as f:
        md = f.read()
        assert "DevSuperSuite Global Treasury Desk" in md
        assert "OECD BEPS Actions 8-10" in md
        assert "$125,000.00" in md
        assert "$31,250.00" in md
        assert "67.75%" in md
        assert "flowchart TD" in md


def test_11_cli_interface_execution():
    """Smoke tests all CLI arguments for the OECD transfer pricing engine."""
    cli_flags = [
        "--audit-csa-cost-sharing",
        "--benchmark-arm-length",
        "--calculate-dempe-scoring",
        "--generate-cbcr-tables",
        "--export-transfer-pricing-binder",
        "--summary"
    ]
    script_path = os.path.join(SERVICES_DIR, "enterprise_oecd_transfer_pricing_engine.py")

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
        os.path.join(SERVICES_DIR, "enterprise_oecd_transfer_pricing_engine.py"),
        DEFAULT_TP_SCHEDULE_FILE,
        ROOT_TP_SCHEDULE_FILE,
        DEFAULT_TP_REPORT_FILE
    ]

    for fpath in target_files:
        assert os.path.exists(fpath), f"File {fpath} must exist for anonymity check"
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            for token in forbidden_tokens:
                assert token not in content, f"Forbidden brand anonymity token '{token}' discovered in {fpath}"
