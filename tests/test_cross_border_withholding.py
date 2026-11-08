"""
⚡ DevSuperSuite Global Treasury Desk - Comprehensive Unit & Integration Test Suite
File: test_cross_border_withholding.py
Target: enterprise_cross_border_withholding_engine.py
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

from enterprise_cross_border_withholding_engine import (
    EnterpriseCrossBorderWithholdingEngine,
    GLOBAL_COMMERCIAL_PORTFOLIO,
    TREASURY_ENTITY_NAME,
    TREASURY_DESK_TITLE,
    TREASURY_OFFICIAL_EMAIL,
    DEFAULT_SCHEDULE_FILE,
    ROOT_SCHEDULE_FILE,
    DEFAULT_REPORT_FILE
)


@pytest.fixture
def withholding_engine():
    """Initializes the institutional cross-border withholding engine."""
    return EnterpriseCrossBorderWithholdingEngine()


def test_01_dtaa_treaty_matrix_completeness(withholding_engine):
    """Verifies that all 7 premier commercial corridors are modeled with required statutory and treaty rates."""
    audit = withholding_engine.audit_dtaa_treaties()
    assert audit["total_corridors_audited"] == 7
    expected_corridors = {"US", "IE", "UK", "DE", "JP", "SG", "IN"}
    assert set(audit["corridors"].keys()) == expected_corridors
    assert audit["commercial_entity"] == TREASURY_ENTITY_NAME
    assert audit["treasury_desk"] == TREASURY_DESK_TITLE
    assert audit["contact_email"] == TREASURY_OFFICIAL_EMAIL


def test_02_us_eu_uk_zero_withholding_rates(withholding_engine):
    """Verifies 0% Article 12 treaty withholding for Ireland, United Kingdom, and Germany corridors."""
    audit = withholding_engine.audit_dtaa_treaties()
    
    # Ireland: 20% statutory reduced to 0% under DTAA Article 12(1) and EU Interest & Royalties Directive
    ie = audit["corridors"]["IE"]
    assert ie["statutory_wht_rate"] == 0.20
    assert ie["treaty_wht_rate"] == 0.00
    assert ie["treaty_wht_liability_usd"] == 0.00
    assert ie["withholding_tax_savings_usd"] == 9700.00

    # United Kingdom: 20% statutory reduced to 0% under US-UK Double Taxation Convention
    uk = audit["corridors"]["UK"]
    assert uk["statutory_wht_rate"] == 0.20
    assert uk["treaty_wht_rate"] == 0.00
    assert uk["treaty_wht_liability_usd"] == 0.00
    assert uk["withholding_tax_savings_usd"] == 8500.00

    # Germany: 15.825% (15% + 5.5% solidarity surcharge) reduced to 0% under US-Germany DTAA
    de = audit["corridors"]["DE"]
    assert de["statutory_wht_rate"] == 0.15825
    assert de["treaty_wht_rate"] == 0.00
    assert de["treaty_wht_liability_usd"] == 0.00
    assert de["withholding_tax_savings_usd"] == 4747.50


def test_03_us_japan_nta_article12_concession(withholding_engine):
    """Verifies US-Japan Tax Convention 0% Article 12 royalty exemption and NTA Form 3 filing requirement."""
    audit = withholding_engine.audit_dtaa_treaties()
    jp = audit["corridors"]["JP"]
    
    assert jp["statutory_wht_rate"] == 0.2042  # 20% + 2.1% reconstruction surtax
    assert jp["treaty_wht_rate"] == 0.00       # 0% treaty exemption
    assert jp["statutory_wht_liability_usd"] == 5920.20
    assert jp["treaty_wht_liability_usd"] == 0.00
    assert jp["withholding_tax_savings_usd"] == 5920.20
    assert "NTA Form 3" in jp["required_filing"]


def test_04_us_singapore_iras_rates(withholding_engine):
    """Verifies Singapore 10% IP royalty withholding rate and IRAS compliance."""
    audit = withholding_engine.audit_dtaa_treaties()
    sg = audit["corridors"]["SG"]
    
    assert sg["statutory_wht_rate"] == 0.10
    assert sg["treaty_wht_rate"] == 0.10
    assert sg["treaty_wht_liability_usd"] == 1400.00
    assert "IRAS Certificate of Residence" in sg["required_filing"]


def test_05_india_section_206aa_vs_dtaa_and_form_10f(withholding_engine):
    """Verifies India statutory TDS (Section 115A 20.8%) vs DTAA Article 12 (15%) and Form 10F/TRC/PAN mandates."""
    audit = withholding_engine.audit_dtaa_treaties()
    india = audit["corridors"]["IN"]
    
    assert india["statutory_wht_rate"] == 0.208
    assert india["treaty_wht_rate"] == 0.15
    assert india["statutory_wht_liability_usd"] == 2080.00
    assert india["treaty_wht_liability_usd"] == 1500.00
    assert india["withholding_tax_savings_usd"] == 580.00
    assert "Form 10F" in india["required_filing"]
    assert "TRC" in india["required_filing"]
    assert "PAN" in india["required_filing"]


def test_06_lob_limitation_on_benefits_substantiation(withholding_engine):
    """Verifies OECD BEPS and US Model Treaty Limitation on Benefits (LOB) test evaluations."""
    lob = withholding_engine.evaluate_lob_compliance()
    
    assert lob["lob_overall_status"] == "FULLY_COMPLIANT_QUALIFIED_PERSON"
    
    # Active conduct of trade or business test
    act = lob["active_business_test"]
    assert act["status"] == "PASS"
    assert act["substantial_activity_ratio_pct"] >= 75.0
    assert act["operational_headcount_full_time"] == 24

    # Ownership and base erosion test
    obe = lob["ownership_base_erosion_test"]
    assert obe["status"] == "PASS"
    assert obe["qualified_beneficial_ownership_pct"] >= 50.0
    assert obe["base_erosion_percentage"] < 50.0

    # Derivative benefits test
    der = lob["derivative_benefits_test"]
    assert der["status"] == "PASS"
    assert der["equivalent_beneficiaries_ownership_pct"] >= 95.0


def test_07_form_w8bene_certificate_generation(withholding_engine):
    """Verifies complete Form W-8BEN-E institutional profile generation."""
    w8 = withholding_engine.generate_w8bene_exemption_certificate()
    
    # Part I: Beneficial Owner Identification
    part_i = w8["part_I_identification_of_beneficial_owner"]
    assert part_i["line_1_name_of_organization"] == TREASURY_ENTITY_NAME
    assert part_i["line_4_chapter_3_status"] == "Corporation"
    assert part_i["line_5_chapter_4_code"] == "01"
    assert "Active NFFE" in part_i["line_5_chapter_4_status_fatca"]
    assert part_i["line_8_us_tin_ein"] == "XX-XXX8492"

    # Part III: Treaty Benefits Claim
    part_iii = w8["part_III_claim_of_tax_treaty_benefits"]
    assert part_iii["line_15_special_rates_and_conditions"]["withholding_rate_claimed_pct"] == 0.0
    assert "Article 12" in part_iii["line_15_special_rates_and_conditions"]["treaty_article_and_paragraph"]

    # Part XXV: Active NFFE passive income certification
    part_xxv = w8["part_XXV_active_nffe_certification"]
    assert "PASSED" in part_xxv["line_39a_gross_passive_income_test"]
    assert "PASSED" in part_xxv["line_39b_passive_assets_test"]

    # Part XXX: Perjury acknowledgement & 3-year validity
    part_xxx = w8["part_XXX_certification_and_signature"]
    assert part_xxx["perjury_acknowledgment"] is True
    assert "3 Full Calendar Years" in part_xxx["certification_validity_period"]


def test_08_form_1042s_reconciliation(withholding_engine):
    """Verifies Form 1042-S cross-border reporting codes and reconciliation."""
    w8 = withholding_engine.generate_w8bene_exemption_certificate()
    codes = w8["form_1042_s_reporting_codes"]
    
    assert codes["chapter_3_income_code"] == "12"       # Software Royalties
    assert codes["chapter_3_exemption_code"] == "04"    # Exempt under tax treaty
    assert codes["chapter_4_exemption_code"] == "15"    # Active NFFE / Foreign Entity Exemption
    assert codes["recipient_code"] == "02"             # Corporation


def test_09_withholding_tax_savings_quantification(withholding_engine):
    """Verifies portfolio-level withholding tax shield exceeds $140k (>85% reduction)."""
    rec = withholding_engine.reconcile_withholding_savings()
    
    assert rec["gross_portfolio_volume_usd"] == 558992.16
    assert rec["statutory_default_withholding_usd"] == 147847.70
    assert rec["treaty_mitigated_withholding_usd"] == 2900.00
    assert rec["net_withholding_cash_savings_usd"] == 144947.70
    assert rec["overall_cash_shield_pct"] > 85.0
    assert rec["overall_cash_shield_pct"] == 98.04


def test_10_cross_border_remittance_binder_export(withholding_engine):
    """Verifies export of JSON schedule files and Markdown report with valid schema."""
    paths = withholding_engine.export_all()
    
    assert os.path.exists(paths["schedule_file"])
    assert os.path.exists(paths["root_schedule_file"])
    assert os.path.exists(paths["report_file"])
    
    # Validate JSON content integrity
    with open(paths["schedule_file"], "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["binder_id"] == "DSS-REM-2026-GLOBAL-BINDER"
        assert data["portfolio_summary"]["net_withholding_savings_usd"] == 144947.70
        assert "US_DOMESTIC" in data["remittance_schedules"]
        assert "EU_IRELAND" in data["remittance_schedules"]
        assert "JP_JAPAN" in data["remittance_schedules"]
        assert "IN_INDIA" in data["remittance_schedules"]

    # Validate Markdown report
    with open(paths["report_file"], "r", encoding="utf-8") as f:
        md = f.read()
        assert "DevSuperSuite Global Treasury Desk" in md
        assert "Limitation on Benefits (LOB)" in md
        assert "$144,947.70" in md
        assert "treasury@devsupersuite.com" in md


def test_11_cli_interface_execution():
    """Smoke test the CLI interface across all mandatory arguments."""
    cli_flags = [
        "--audit-dtaa-treaties",
        "--generate-w8bene-exemption",
        "--reconcile-withholding-savings",
        "--export-remittance-binder",
        "--summary"
    ]
    script_path = os.path.join(SERVICES_DIR, "enterprise_cross_border_withholding_engine.py")

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
        os.path.join(SERVICES_DIR, "enterprise_cross_border_withholding_engine.py"),
        DEFAULT_SCHEDULE_FILE,
        ROOT_SCHEDULE_FILE,
        DEFAULT_REPORT_FILE
    ]

    for fpath in target_files:
        assert os.path.exists(fpath), f"File {fpath} must exist for anonymity verification"
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            for token in forbidden_tokens:
                assert token not in content, f"Forbidden brand anonymity token '{token}' discovered in {fpath}"
