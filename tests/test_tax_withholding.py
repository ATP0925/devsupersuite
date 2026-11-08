"""
⚡ DevSuperSuite Treasury & Tax Office - Unit & Integration Test Suite
File: test_tax_withholding.py
Target: tax_withholding_reconciler.py (Global Corporate Tax Withholding & Cross-Border VAT/GST Compliance Reconciler)
Strict Compliance: 100% Brand Anonymity - DevSuperSuite Treasury & Tax Office Only (tax@devsupersuite.com).
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

from tax_withholding_reconciler import (
    TaxWithholdingReconciler,
    STATUTORY_TAX_RATES,
    LUT_REGISTRATION_NUMBER,
    FOREIGN_TIN_IDENTIFIER,
    TAX_YEAR,
    BENEFICIAL_OWNER_LEGAL_ENTITY,
    TREASURY_TAX_AUTHORITY_EMAIL,
    STORE_LEDGER_FILE,
    SETTLEMENT_LEDGER_FILE
)

@pytest.fixture
def tax_reconciler():
    """Initializes Tax Withholding Reconciler with primary commercial ledgers."""
    return TaxWithholdingReconciler(
        store_ledger_path=STORE_LEDGER_FILE,
        settlement_ledger_path=SETTLEMENT_LEDGER_FILE
    )

def test_01_us_withholding_treaty_rate_calculation(tax_reconciler):
    """Verifies US IRC §1441/§1442 withholding: 0% certified with W-8BEN-E vs 30% statutory without."""
    # 1. With Form W-8BEN-E treaty certification (0.0% WHT)
    res_treaty = tax_reconciler.determine_withholding_obligation(
        country="US",
        amount_usd=24500.00,
        client_type="B2B",
        has_treaty_cert=True,
        service_type="engineering_services"
    )
    assert res_treaty["jurisdiction"] == "US"
    assert res_treaty["statutory_rate_pct"] == 30.0
    assert res_treaty["treaty_rate_pct"] == 0.0
    assert res_treaty["statutory_tax_amount_usd"] == 7350.00
    assert res_treaty["certified_withheld_amount_usd"] == 0.00
    assert res_treaty["tax_saved_usd"] == 7350.00
    assert res_treaty["chapter3_exemption_code"] == "02"  # Exempt under tax treaty
    assert res_treaty["chapter4_exemption_code"] == "15"  # Active NFFE
    assert res_treaty["compliance_status"] == "CERTIFIED_ZERO_WITHHOLDING"
    assert "Article 7 (Business Profits)" in res_treaty["governing_provision"]

    # 2. Without Form W-8BEN-E (Statutory 30.0% WHT mandatory)
    res_notreaty = tax_reconciler.determine_withholding_obligation(
        country="US",
        amount_usd=24500.00,
        client_type="B2B",
        has_treaty_cert=False
    )
    assert res_notreaty["treaty_rate_pct"] == 30.0
    assert res_notreaty["certified_withheld_amount_usd"] == 7350.00
    assert res_notreaty["tax_saved_usd"] == 0.00
    assert res_notreaty["compliance_status"] == "STATUTORY_DEDUCTION_MANDATORY"

def test_02_eu_vat_reverse_charge_and_oss(tax_reconciler):
    """Verifies EU VAT Article 196 B2B Reverse Charge (0%) vs B2C OSS destination VAT."""
    # 1. EU B2B with valid VAT ID (Reverse Charge Mechanism)
    res_b2b = tax_reconciler.determine_withholding_obligation(
        country="DE",
        amount_usd=1000.00,
        client_type="B2B",
        vat_id="DE309182741"
    )
    assert res_b2b["jurisdiction"] == "EU"
    assert res_b2b["certified_withheld_amount_usd"] == 0.00
    assert res_b2b["treaty_rate_pct"] == 0.0
    assert res_b2b["compliance_status"] == "REVERSE_CHARGE_APPLIED_0_VAT"
    assert "Article 196" in res_b2b["governing_provision"]
    assert res_b2b["vat_id"] == "DE309182741"

    # 2. EU B2C without VAT ID (One-Stop Shop Destination VAT applied)
    res_b2c = tax_reconciler.determine_withholding_obligation(
        country="FI",
        amount_usd=100.00,
        client_type="B2C",
        vat_id=None
    )
    assert res_b2c["jurisdiction"] == "EU"
    assert res_b2c["statutory_rate_pct"] == 25.5  # Finland VAT rate
    assert res_b2c["certified_withheld_amount_usd"] == 25.50
    assert res_b2c["compliance_status"] == "OSS_DESTINATION_VAT_COLLECTED"

def test_03_indian_tds_and_lut_export_compliance(tax_reconciler):
    """Verifies Section 195 TDS relief and zero-rated LUT export compliance."""
    res_in = tax_reconciler.determine_withholding_obligation(
        country="IN",
        amount_usd=29.00,
        client_type="B2B"
    )
    assert res_in["jurisdiction"] == "IN"
    assert res_in["certified_withheld_amount_usd"] == 0.00
    assert res_in["compliance_status"] == "ZERO_RATED_LUT_EXPORT_OR_DOMESTIC"
    assert "Section 195" in res_in["governing_provision"]

def test_04_form_1042s_annual_summary_data(tax_reconciler):
    """Verifies institutional Form 1042-S statement fields match IRS specifications."""
    f1042 = tax_reconciler.generate_form_1042s_summary(tax_year=TAX_YEAR)

    assert f1042["tax_year"] == TAX_YEAR
    assert "Form 1042-S" in f1042["form"]
    assert f1042["beneficial_owner"]["foreign_tin"] == FOREIGN_TIN_IDENTIFIER
    assert "Active NFFE" in f1042["beneficial_owner"]["chapter4_status"]
    assert f1042["beneficial_owner"]["authority_email"] == TREASURY_TAX_AUTHORITY_EMAIL

    # Totals verification
    totals = f1042["totals"]
    assert totals["total_us_gross_reported_usd"] == 24814.00
    assert totals["total_federal_tax_withheld_usd"] == 0.00
    assert totals["net_effective_us_wht_rate_pct"] == 0.00

    # Withholding Agent Boxes
    nexus_agent = next(a for a in f1042["withholding_agents"] if "Nexus" in a["agent_name"])
    assert nexus_agent["gross_paid_usd"] == 24500.00
    assert nexus_agent["income_code"] == "06"  # Other services
    assert nexus_agent["chapter3_exemption_code"] == "02"  # Treaty exempt
    assert nexus_agent["chapter4_exemption_code"] == "15"  # Active NFFE
    assert nexus_agent["tax_rate_pct"] == 0.00
    assert nexus_agent["federal_tax_withheld_usd"] == 0.00

def test_05_reconciliation_totals_and_savings(tax_reconciler):
    """Verifies multi-channel tax audit calculations and statutory tax savings."""
    audit = tax_reconciler.reconcile_all_tax_ledgers()
    m = audit["metrics"]

    assert m["total_gross_inflow_usd"] == 24930.00
    assert m["total_us_gross_usd"] == 24814.00
    assert m["total_eu_uk_gross_usd"] == 87.00
    assert m["export_gross_volume_usd"] == 24901.00
    assert m["certified_net_wht_usd"] == 0.00
    assert m["potential_statutory_wht_usd"] > 7400.00
    assert m["total_withholding_tax_saved_usd"] > 7400.00
    assert m["cross_border_vat_neutralized_usd"] > 0.00
    assert m["statutory_compliance_pct"] == 100.0

def test_06_w8bene_certificate_generation(tax_reconciler):
    """Verifies generation of certified Form W-8BEN-E Tax Exemption Dossier."""
    w8_md = tax_reconciler.generate_exemption_certificate_w8bene("Nexus Enterprise Technologies Corp.")

    assert "Form W-8BEN-E Specification" in w8_md
    assert "Nexus Enterprise Technologies Corp." in w8_md
    assert "Active NFFE" in w8_md
    assert "Article 7 (Business Profits)" in w8_md
    assert "0.00% (Zero Federal Withholding)" in w8_md
    assert FOREIGN_TIN_IDENTIFIER in w8_md
    assert LUT_REGISTRATION_NUMBER in w8_md
    assert "Through December 31, 2028" in w8_md

def test_07_strict_brand_anonymity(tax_reconciler, tmp_path):
    """Generates all reports and verifies strict 100% Brand Anonymity Protocol."""
    saved = tax_reconciler.save_all_reports(str(tmp_path))

    for key, path in saved.items():
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Institutional Authority Checks
        assert "DevSuperSuite" in content
        assert "tax@devsupersuite.com" in content

        # Zero PII Leaks: forbidden personal founder tokens
        forbidden = ["Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"]
        for word in forbidden:
            assert word not in content, f"Brand Anonymity violation: found '{word}' in {key}."

def test_08_cli_execution():
    """Verifies CLI execution with --reconcile-tax-ledgers, --generate-1042s, and --summary flags."""
    script_path = os.path.join(SERVICES_DIR, "tax_withholding_reconciler.py")

    cmd = [
        sys.executable, script_path,
        "--reconcile-tax-ledgers",
        "--generate-1042s",
        "--audit-withholding-rates",
        "--summary"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)

    assert "Form 1042-S Annual Summary" in res.stdout
    assert "Cross-Border Tax Audit Report" in res.stdout
    assert "Form W-8BEN-E Exemption Dossier" in res.stdout
    assert "Total Gross Revenue Audited:       $24,930.00 USD" in res.stdout
    assert "Certified Net Tax Withheld:        $0.00 USD" in res.stdout
    assert "Statutory Compliance Rate:         100.0% Compliant" in res.stdout
