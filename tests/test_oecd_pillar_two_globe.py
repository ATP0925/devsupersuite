"""
⚡ DevSuperSuite Global Tax & Treasury - OECD Pillar Two GloBE Minimum Tax Test Suite
File: test_oecd_pillar_two_globe.py
Target: enterprise_oecd_pillar_two_globe_engine.py
Strict Compliance: 100% Brand Anonymity - DevSuperSuite Global Tax & Treasury Only (treasury@devsupersuite.com).
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

from enterprise_oecd_pillar_two_globe_engine import (
    EnterpriseOECDPillarTwoGloBEEngine,
    GLOBE_MINIMUM_TAX_RATE_PCT,
    SBIE_PAYROLL_CARVEOUT_PCT_2026,
    SBIE_TANGIBLE_CARVEOUT_PCT_2026,
    SIMPLIFIED_ETR_THRESHOLD_PCT_2026,
    GROUP_PARENT_ENTITY,
    TAX_DESK_TITLE,
    TREASURY_OFFICIAL_EMAIL,
    DEFAULT_GLOBE_SCHEDULE_FILE,
    ROOT_GLOBE_SCHEDULE_FILE,
    DEFAULT_GLOBE_REPORT_FILE
)


@pytest.fixture
def globe_engine():
    """Initializes the institutional OECD Pillar Two GloBE engine."""
    return EnterpriseOECDPillarTwoGloBEEngine()


def test_01_globe_minimum_tax_rate_benchmark(globe_engine):
    """Verifies that the engine enforces the 15.00% OECD Pillar Two global minimum tax rate."""
    assert globe_engine.minimum_rate_pct == 15.00
    assert GLOBE_MINIMUM_TAX_RATE_PCT == 15.00


def test_02_jurisdictional_etr_calculations(globe_engine):
    """Verifies jurisdictional ETRs: US (24.50%), Ireland (12.50%), and Singapore (10.00%)."""
    audit = globe_engine.audit_jurisdictional_etr()
    etrs = audit["jurisdiction_etrs"]

    # US: 24.50% (exceeds 15% floor)
    assert etrs["UNITED_STATES"]["calculated_globe_etr_pct"] == 24.50
    assert etrs["UNITED_STATES"]["gross_top_up_tax_percentage"] == 0.00
    assert etrs["UNITED_STATES"]["is_low_taxed_jurisdiction"] is False

    # Ireland: 12.50% (2.50% top-up gap)
    assert etrs["IRELAND"]["calculated_globe_etr_pct"] == 12.50
    assert etrs["IRELAND"]["gross_top_up_tax_percentage"] == 2.50
    assert etrs["IRELAND"]["is_low_taxed_jurisdiction"] is True

    # Singapore: 10.00% (5.00% top-up gap)
    assert etrs["SINGAPORE"]["calculated_globe_etr_pct"] == 10.00
    assert etrs["SINGAPORE"]["gross_top_up_tax_percentage"] == 5.00
    assert etrs["SINGAPORE"]["is_low_taxed_jurisdiction"] is True


def test_03_substance_based_income_exclusion_carveouts(globe_engine):
    """Verifies 2026 transitional SBIE carve-out rates (9.8% payroll and 7.8% tangible assets)."""
    assert globe_engine.payroll_carveout_pct == 9.80
    assert globe_engine.tangible_carveout_pct == 7.80

    sbie = globe_engine.calculate_substance_based_income_exclusion()
    assert sbie["total_group_sbie_usd"] == 23532.73

    us_sbie = sbie["jurisdiction_sbie"]["UNITED_STATES"]
    assert us_sbie["payroll_carveout_amount_usd"] == 14210.00  # $145,000 * 9.8%
    assert us_sbie["tangible_carveout_amount_usd"] == 2730.00  # $35,000 * 7.8%
    assert us_sbie["total_sbie_carveout_usd"] == 16940.00


def test_04_excess_profit_calculation(globe_engine):
    """Verifies excess profit calculation: Excess Profit = max(0, GloBE Income - SBIE)."""
    sbie = globe_engine.calculate_substance_based_income_exclusion()
    
    us = sbie["jurisdiction_sbie"]["UNITED_STATES"]
    assert us["excess_profit_usd"] == round(385200.00 - 16940.00, 2)

    ie = sbie["jurisdiction_sbie"]["IRELAND"]
    assert ie["excess_profit_usd"] == 0.00  # SBIE exceeds €4.1k distribution profit

    sg = sbie["jurisdiction_sbie"]["SINGAPORE"]
    assert sg["excess_profit_usd"] == 0.00  # SBIE exceeds $1.7k profit


def test_05_qdmtt_domestic_top_up_tax_absorption(globe_engine):
    """Verifies that Ireland and Singapore have active QDMTT frameworks absorbing domestic top-up tax."""
    top_up = globe_engine.calculate_top_up_tax()
    ie = top_up["jurisdictions"]["IRELAND"]
    sg = top_up["jurisdictions"]["SINGAPORE"]

    assert ie["top_up_tax_rate_pct"] == 2.50
    assert sg["top_up_tax_rate_pct"] == 5.00
    assert top_up["total_iir_parent_tax_payable_usd"] == 0.00


def test_06_transitional_cbcr_de_minimis_safe_harbour(globe_engine):
    """Verifies De Minimis Safe Harbour: Total Revenue < €10M and Pre-Tax Profit < €1M."""
    sh = globe_engine.evaluate_transitional_safe_harbours()
    
    for code, data in sh["jurisdiction_safe_harbours"].items():
        assert data["de_minimis_test"]["passed"] is True
        assert data["safe_harbour_elected"] is True
        assert data["effective_top_up_tax_payable_usd"] == 0.00


def test_07_simplified_etr_safe_harbour_test(globe_engine):
    """Verifies that United States passes the Simplified ETR test (24.50% >= 17.00% for 2026)."""
    sh = globe_engine.evaluate_transitional_safe_harbours()
    us = sh["jurisdiction_safe_harbours"]["UNITED_STATES"]
    
    assert us["simplified_etr_test"]["passed"] is True
    assert us["simplified_etr_test"]["tested_etr_pct"] == 24.50
    assert us["simplified_etr_test"]["threshold_pct"] == 17.00


def test_08_iir_and_utpr_backstop_allocations(globe_engine):
    """Verifies that parent Income Inclusion Rule (IIR) top-up tax payable is $0.00 under safe harbour relief."""
    top_up = globe_engine.calculate_top_up_tax()
    
    assert top_up["safe_harbour_total_protection_applied"] is True
    assert top_up["total_iir_parent_tax_payable_usd"] == 0.00
    for j in top_up["jurisdictions"].values():
        assert j["final_net_top_up_tax_due_usd"] == 0.00


def test_09_schedule_json_persistence(globe_engine):
    """Verifies export of GloBE schedule JSON files and mirrored persistence."""
    paths = globe_engine.export_all()
    
    assert os.path.exists(paths["schedule_file"])
    assert os.path.exists(paths["root_schedule_file"])
    assert os.path.exists(paths["report_file"])

    with open(paths["schedule_file"], "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["binder_id"] == "DSS-OECD-PILLAR2-2026-DOSSIER"
        assert data["global_minimum_rate_pct"] == 15.00
        assert data["executive_summary"]["safe_harbour_election"] == "DE_MINIMIS_SAFE_HARBOUR_FULLY_QUALIFIED"
        assert "jurisdictional_etrs" in data


def test_10_audit_report_markdown_integrity(globe_engine):
    """Verifies that the markdown report contains executive summaries, tables, and Mermaid flowcharts."""
    paths = globe_engine.export_all()
    
    with open(paths["report_file"], "r", encoding="utf-8") as f:
        md = f.read()
        assert "DevSuperSuite Global Tax & Treasury" in md
        assert "OECD Pillar Two GloBE" in md
        assert "15.00%" in md
        assert "De Minimis Safe Harbour" in md
        assert "flowchart TD" in md


def test_11_cli_interface_execution():
    """Smoke tests all CLI arguments for the OECD Pillar Two GloBE engine."""
    cli_flags = [
        "--audit-jurisdictional-etr",
        "--evaluate-safe-harbours",
        "--calculate-top-up-tax",
        "--export-globe-binder",
        "--summary"
    ]
    script_path = os.path.join(SERVICES_DIR, "enterprise_oecd_pillar_two_globe_engine.py")

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
    forbidden_tokens = [
        "".join(["P", "r", "a", "t", "i", "k"]),
        "".join(["p", "r", "a", "t", "i", "k"]),
        "".join(["a", "t", "p", "a", "d"]),
        "".join(["a", "t", "p", "a", "d", "k", "a", "r"]),
        "".join(["g", "m", "a", "i", "l", ".", "c", "o", "m"]),
        "".join(["+", "9", "1", "9"]),
        "".join(["+", "9", "1", " ", "9"]),
    ]
    target_files = [
        os.path.join(SERVICES_DIR, "enterprise_oecd_pillar_two_globe_engine.py"),
        DEFAULT_GLOBE_SCHEDULE_FILE,
        ROOT_GLOBE_SCHEDULE_FILE,
        DEFAULT_GLOBE_REPORT_FILE
    ]

    for fpath in target_files:
        assert os.path.exists(fpath), f"File {fpath} must exist for anonymity check"
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            for token in forbidden_tokens:
                assert token not in content, f"Forbidden brand anonymity token '{token}' discovered in {fpath}"
