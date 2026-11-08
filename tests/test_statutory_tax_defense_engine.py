"""
⚡ DevSuperSuite Global Treasury & Tax Strategy Desk - Unit & Integration Test Suite
File: test_statutory_tax_defense_engine.py
Phase: 28 - Enterprise Statutory Annual Report & Multi-Jurisdictional Tax Defense Pack
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

from services.enterprise_statutory_tax_defense_engine import (
    EnterpriseStatutoryTaxDefenseEngine,
    STATUTORY_PORTFOLIO_BASELINE,
    DEFAULT_ANNUAL_TAX_SCHEDULE_FILE,
    ROOT_ANNUAL_TAX_SCHEDULE_FILE,
    DEFAULT_ANNUAL_TAX_REPORT_FILE
)

FORBIDDEN_FOUNDER_TOKENS = [
    "Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"
]


@pytest.fixture
def engine():
    return EnterpriseStatutoryTaxDefenseEngine()


def test_01_gaap_vs_ifrs_revenue_reconciliation(engine):
    """Verifies US GAAP (ASC 606) vs IFRS 15 revenue recognition and timing difference reconciliation."""
    recon = engine.reconcile_gaap_vs_ifrs()

    assert recon["gross_commercial_inflows_usd"] > 550000.0
    asc = recon["asc_606_us_gaap"]
    ifrs = recon["ifrs_15"]

    assert asc["upfront_licenses_recognized_usd"] == 342000.00
    assert asc["total_recognized_revenue_usd"] > 520000.0
    assert asc["deferred_revenue_contract_liability_usd"] > 30000.0

    assert ifrs["upfront_licenses_recognized_usd"] == 342000.00
    assert ifrs["total_recognized_revenue_usd"] > 515000.0
    assert ifrs["deferred_revenue_contract_liability_usd"] > 35000.0

    # Timing variance check
    assert 5000.0 <= recon["reconciliation_variance_usd"] <= 6000.0
    assert "Timing discrepancy" in recon["timing_variance_explanation"]

    # Entities check
    entities = {e["entity"] for e in recon["jurisdiction_entities"]}
    assert len(entities) == 5
    frameworks = {e["accounting_framework"] for e in recon["jurisdiction_entities"]}
    assert "US GAAP (ASC 606)" in frameworks
    assert "IFRS (IFRS 15 / FRS 102)" in frameworks


def test_02_section_41_rd_tax_credit_calculation(engine):
    """Verifies IRC Section 41 R&D credit calculation under Alternative Simplified Credit (ASC) method."""
    rd = engine.calculate_rd_tax_credit_section_41(
        engineering_wages_usd=125000.00,
        cloud_compute_testing_usd=18500.00,
        contract_rd_qre_usd=0.00,
        historical_base_qre_usd=50000.00
    )

    assert rd["credit_statutory_authority"] == "IRC Section 41 (Credit for Increasing Research Activities)"
    assert rd["calculation_method"] == "Alternative Simplified Credit (ASC)"
    assert rd["qualified_research_expenses"]["total_qres_usd"] == 143500.00
    assert rd["base_period_amount_usd"] == 25000.00
    assert rd["excess_qres_over_base_usd"] == 118500.00
    assert rd["statutory_credit_rate_pct"] == 14.0
    assert rd["gross_section_41_credit_usd"] == 16590.00
    assert rd["compliance_verdict"] == "QUALIFIED_SECTION_41_CREDIT"

    # Verify Four-Part Test substantiation
    four_part = rd["four_part_test_substantiation"]
    assert "PASS" in four_part["1_permissible_purpose"]
    assert "PASS" in four_part["2_elimination_of_uncertainty"]
    assert "PASS" in four_part["3_process_of_experimentation"]
    assert "PASS" in four_part["4_technological_in_nature"]


def test_03_form_1120_tax_provision(engine):
    """Verifies US Form 1120 tax provision modeling with Section 41 credit reduction."""
    prov = engine.calculate_form_1120_tax_provision()

    assert prov["form_type"] == "IRS Form 1120 (U.S. Corporation Income Tax Return)"
    assert prov["filing_entity"] == "DevSuperSuite US LLC"
    assert prov["gross_receipts_usd"] == 425000.00
    assert prov["taxable_income_usd"] == 278250.00
    assert prov["statutory_federal_rate_pct"] == 21.0
    assert prov["tentative_federal_income_tax_usd"] == 58432.50
    assert prov["section_41_rd_credit_applied_usd"] == 16590.00
    assert prov["net_federal_income_tax_payable_usd"] == 41842.50

    # Verify effective tax rates
    assert prov["effective_federal_tax_rate_pct"] == 15.04
    assert prov["effective_total_tax_rate_pct"] < 22.0


def test_04_global_tax_provision_consolidation(engine):
    """Verifies multi-jurisdiction global tax provision consolidation across US, IE, IN, UK, SG."""
    consol = engine.consolidate_multi_jurisdiction_tax_provision()

    assert consol["global_pretax_income_usd"] > 400000.0
    assert consol["global_tax_provision_usd"] > 70000.0
    assert 17.0 <= consol["global_effective_tax_rate_pct"] <= 22.0

    provisions = {p["country"]: p for p in consol["jurisdiction_provisions"]}
    assert set(provisions.keys()) == {"United States", "Ireland", "India", "United Kingdom", "Singapore"}

    # Ireland 12.5% trading rate
    assert provisions["Ireland"]["statutory_tax_rate_pct"] == 12.50
    assert provisions["Ireland"]["effective_tax_rate_pct"] == 12.50

    # India corporate tax
    assert provisions["India"]["statutory_tax_rate_pct"] == 25.17


def test_05_audit_defense_binder_structure(engine):
    """Verifies audit defense binder structure and contemporaneous documentation."""
    defense = engine.generate_audit_defense_binder()

    assert defense["contemporaneous_documentation_status"] == "CERTIFIED_ACTIVE"
    memos = defense["defense_memos"]
    assert len(memos) >= 3

    topics = [m["defense_topic"] for m in memos]
    assert any("Section 482" in t for t in topics)
    assert any("Section 41" in t for t in topics)
    assert any("Anti-Hybrid" in t for t in topics)

    for m in memos:
        assert len(m["evidence_artifacts"]) >= 2
        assert "CONFIRMED" in m["risk_rating"] or "EXPOSURE" in m["risk_rating"]


def test_06_artifact_export_and_json_persistence(engine):
    """Verifies JSON schedule and Markdown annual report generation."""
    paths = engine.export_all_artifacts()

    for key, path in paths.items():
        assert os.path.exists(path), f"File {path} was not created"

    # Verify JSON schedule
    with open(paths["schedule_path"], "r", encoding="utf-8") as f:
        schedule = json.load(f)
    assert schedule["metadata"]["reporting_entity"] == "DevSuperSuite Group"
    assert "gaap_vs_ifrs_reconciliation" in schedule
    assert "form_1120_us_tax_provision" in schedule
    assert "global_tax_provision_consolidation" in schedule
    assert "audit_defense_binder" in schedule

    # Verify Markdown report
    with open(paths["report_path"], "r", encoding="utf-8") as f:
        report_md = f.read()
    assert "ENTERPRISE STATUTORY ANNUAL REPORT & MULTI-JURISDICTIONAL TAX DEFENSE PACK" in report_md
    assert "ASC 606" in report_md
    assert "IFRS 15" in report_md
    assert "IRC Section 41" in report_md


def test_07_cli_command_executions():
    """Verifies multi-action CLI commands execute cleanly."""
    script_path = os.path.join(SERVICES_DIR, "enterprise_statutory_tax_defense_engine.py")

    cmd = [
        sys.executable,
        script_path,
        "--reconcile-gaap-ifrs",
        "--calculate-tax-provision",
        "--calculate-rd-credit",
        "--generate-audit-defense",
        "--export-annual-report",
        "--summary"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"CLI failed: {res.stderr}"
    assert "Multi-Jurisdiction GAAP (ASC 606) vs IFRS (IFRS 15)" in res.stdout
    assert "IRC Section 41 Research & Development Tax Credit" in res.stdout
    assert "IRS Form 1120 & Global Consolidated Tax Provisions" in res.stdout
    assert "International Tax Audit Defense Binder" in res.stdout


def test_08_strict_brand_anonymity():
    """Verifies 100% Brand Anonymity across all Phase 28 files."""
    files_to_check = [
        os.path.join(SERVICES_DIR, "enterprise_statutory_tax_defense_engine.py"),
        os.path.join(REPORTS_DIR, "statutory_annual_tax_defense_report.md"),
        os.path.join(DATA_DIR, "statutory_annual_tax_schedule.json"),
        os.path.join(ROOT_DATA_DIR, "statutory_annual_tax_schedule.json")
    ]

    for file_path in files_to_check:
        assert os.path.exists(file_path), f"File {file_path} must exist for anonymity check"
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().lower()
        for token in FORBIDDEN_FOUNDER_TOKENS:
            assert token.lower() not in content, (
                f"Forbidden founder token '{token}' detected in {file_path}!"
            )
