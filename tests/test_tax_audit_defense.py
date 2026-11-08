"""
⚡ DevSuperSuite Treasury & Corporate Finance - Unit & Integration Test Suite
File: test_tax_audit_defense.py
Target: tax_audit_defense_engine.py (Automated Tax Audit Defense, Transfer Pricing & Statutory Disclosures Engine)
Strict Compliance: 100% Brand Anonymity - DevSuperSuite Treasury & Corporate Finance Only (cfo@devsupersuite.com).
"""

import os
import sys
import json
import subprocess
import pytest

# Add services and repo root to sys.path
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(SCRATCH_DIR, "services")
if SERVICES_DIR not in sys.path:
    sys.path.insert(0, SERVICES_DIR)
if SCRATCH_DIR not in sys.path:
    sys.path.insert(0, SCRATCH_DIR)

from tax_audit_defense_engine import (
    TaxAuditDefenseEngine,
    BENCHMARKS,
    DEMPE_MATRIX,
    TP_LEDGER_FILE,
    DEFAULT_DISCLOSURES_REPORT_FILE
)

FORBIDDEN_FOUNDER_TOKENS = [
    "Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"
]


@pytest.fixture
def tax_engine(tmp_path):
    """Initializes Tax Audit Defense Engine with isolated test paths."""
    test_ledger = os.path.join(tmp_path, "test_tp_ledger.json")
    test_report = os.path.join(tmp_path, "test_tp_report.md")
    return TaxAuditDefenseEngine(
        ledger_path=test_ledger,
        report_path=test_report
    )


def test_01_benchmarks_and_dempe_structure():
    """Verifies OECD transfer pricing benchmarks and Chapter VI DEMPE governance structure."""
    assert "cost_plus_markup" in BENCHMARKS
    assert "distributor_operating_margin" in BENCHMARKS

    cpm_bm = BENCHMARKS["cost_plus_markup"]
    assert cpm_bm["lower_quartile_pct"] == 8.20
    assert cpm_bm["median_pct"] == 10.15
    assert cpm_bm["upper_quartile_pct"] == 12.40

    tnmm_bm = BENCHMARKS["distributor_operating_margin"]
    assert tnmm_bm["lower_quartile_pct"] == 3.10
    assert tnmm_bm["median_pct"] == 4.60
    assert tnmm_bm["upper_quartile_pct"] == 5.85

    assert len(DEMPE_MATRIX) == 5
    elements = [d["element"] for d in DEMPE_MATRIX]
    assert any("Development" in e for e in elements)
    assert any("Enhancement" in e for e in elements)
    assert any("Maintenance" in e for e in elements)
    assert any("Protection" in e for e in elements)
    assert any("Exploitation" in e for e in elements)


def test_02_cost_plus_method_modeling(tax_engine):
    """Verifies Cost Plus Method (CPM) contract engineering markup calculations."""
    tp = tax_engine.model_transfer_pricing()
    cpm = tp["cost_plus_model"]

    assert cpm["direct_engineering_labor_usd"] == 8760.00
    assert cpm["allocated_rd_engineering_usd"] == 3500.00
    assert cpm["total_allowable_service_cost_base_usd"] == 12260.00
    assert cpm["applied_markup_pct"] == 10.00
    assert cpm["intercompany_service_markup_usd"] == 1226.00
    assert cpm["pass_through_compute_and_tokens_usd"] == 672.87
    assert cpm["total_intercompany_engineering_invoice_usd"] == 14158.87
    assert cpm["performing_entity"] == "DevSuperSuite Tech Services"


def test_03_tnmm_distribution_modeling(tax_engine):
    """Verifies Transactional Net Margin Method (TNMM) distributor margin and residual royalties."""
    tp = tax_engine.model_transfer_pricing()
    tnmm = tp["tnmm_distribution_model"]

    assert tnmm["total_commercial_revenue_distributed_usd"] == 33440.00
    assert tnmm["target_operating_margin_pct"] == 4.50
    assert tnmm["target_distributor_operating_profit_usd"] == 1504.80
    assert tnmm["distributor_operating_costs_and_fees_usd"] == 2130.50
    assert tnmm["distributor_retained_gross_margin_usd"] == 3635.30
    assert tnmm["intercompany_ip_license_royalty_usd"] == 29804.70
    assert tnmm["distributing_entity"] == "DevSuperSuite US LLC"


def test_04_transfer_pricing_margin_audit_compliant(tax_engine):
    """Verifies that standard 10.0% CPM and 4.5% TNMM pass arm's length benchmark audits."""
    audit = tax_engine.audit_transfer_pricing_margins()

    assert audit["overall_audit_status"] == "COMPLIANT_ARMS_LENGTH"
    assert audit["cpm_service_markup_audit"]["status"] == "PASS_ARMS_LENGTH"
    assert audit["cpm_service_markup_audit"]["in_bounds"] is True
    assert audit["tnmm_distribution_margin_audit"]["status"] == "PASS_ARMS_LENGTH"
    assert audit["tnmm_distribution_margin_audit"]["in_bounds"] is True


def test_05_transfer_pricing_margin_audit_out_of_bounds(tax_engine):
    """Verifies that non-compliant transfer pricing markups trigger audit risk alerts."""
    # Deficient CPM markup (5.0% < 8.0% safe harbor)
    audit_cpm_low = tax_engine.audit_transfer_pricing_margins(observed_cpm_pct=5.0)
    assert audit_cpm_low["overall_audit_status"] == "NON_COMPLIANT_RISK_DETECTED"
    assert audit_cpm_low["cpm_service_markup_audit"]["status"] == "AUDIT_RISK_OUT_OF_BOUNDS"
    assert audit_cpm_low["cpm_service_markup_audit"]["in_bounds"] is False

    # Excessive TNMM margin (8.5% > 6.0% upper bound)
    audit_tnmm_high = tax_engine.audit_transfer_pricing_margins(observed_tnmm_pct=8.5)
    assert audit_tnmm_high["overall_audit_status"] == "NON_COMPLIANT_RISK_DETECTED"
    assert audit_tnmm_high["tnmm_distribution_margin_audit"]["status"] == "AUDIT_RISK_OUT_OF_BOUNDS"
    assert audit_tnmm_high["tnmm_distribution_margin_audit"]["in_bounds"] is False


def test_06_asc_606_revenue_disaggregation(tax_engine):
    """Verifies ASC 606 revenue disaggregation by offering, timing, and geography."""
    disc = tax_engine.compile_statutory_disclosures()
    rev = disc["note_1_asc_606_revenue_disaggregation"]

    # Offering Disaggregation
    off = rev["offering"]
    assert off["developer_software_licenses_usd"] == 440.00
    assert off["enterprise_turnkey_implementations_usd"] == 24500.00
    assert off["recurring_engineering_retainers_usd"] == 8500.00
    assert off["total_commercial_revenue_usd"] == 33440.00

    # Timing Disaggregation
    timing = rev["timing"]
    assert timing["point_in_time_usd"] == 440.00
    assert timing["over_time_milestone_acceptance_usd"] == 33000.00
    assert timing["total_usd"] == 33440.00

    # Geographic Disaggregation
    geo = rev["geography"]
    assert geo["americas_usd"] == pytest.approx(24912.80, abs=0.5)
    assert geo["emea_usd"] == pytest.approx(5082.88, abs=0.5)
    assert geo["apac_usd"] == pytest.approx(3444.32, abs=0.5)
    assert geo["total_usd"] == 33440.00


def test_07_asc_740_income_tax_provision(tax_engine):
    """Verifies ASC 740 tax expense provision, permanent differences, and effective tax rate (ETR)."""
    disc = tax_engine.compile_statutory_disclosures()
    tax = disc["note_2_asc_740_income_tax_provision"]

    assert tax["pretax_gaap_income_usd"] == 17568.13
    assert tax["statutory_federal_tax_rate_pct"] == 21.00
    assert tax["statutory_tax_expense_usd"] == pytest.approx(3689.31, abs=0.1)

    # Permanent deductions
    perm = tax["permanent_tax_reconciliations"]
    assert perm["irc_section_250_fdii_export_benefit_usd"] < 0
    assert perm["irc_section_41_rd_tax_credits_usd"] < 0

    assert tax["current_tax_expense_usd"] == pytest.approx(2840.76, abs=0.1)
    assert tax["effective_tax_rate_pct"] == pytest.approx(16.17, abs=0.1)
    assert tax["effective_tax_rate_pct"] < 21.00  # Tax optimized through FDII / R&D credits
    assert tax["valuation_allowance_usd"] == 0.00  # Zero valuation allowance required


def test_08_asc_280_segment_reporting(tax_engine):
    """Verifies ASC 280 reportable segments reconciliation with consolidated statements."""
    disc = tax_engine.compile_statutory_disclosures()
    seg = disc["note_3_asc_280_segment_reporting"]

    assert len(seg["segments"]) == 3
    segment_names = [s["segment_name"] for s in seg["segments"]]
    assert any("Enterprise Solutions" in name for name in segment_names)
    assert any("Developer Software" in name for name in segment_names)
    assert any("Corporate Treasury" in name for name in segment_names)

    rec = seg["reconciliation"]
    assert rec["total_segment_revenue_usd"] == rec["consolidated_revenue_usd"]
    assert rec["total_segment_profit_usd"] == pytest.approx(rec["consolidated_pretax_income_usd"], abs=0.01)
    assert rec["total_segment_assets_usd"] == rec["consolidated_total_assets_usd"]


def test_09_related_party_and_eliminations(tax_engine):
    """Verifies Related Party disclosures and 100% intercompany statutory elimination."""
    disc = tax_engine.compile_statutory_disclosures()
    rp = disc["note_4_related_party_disclosures"]

    assert rp["intercompany_service_fee_expense_usd"] == 14158.87
    assert rp["intercompany_ip_license_fee_usd"] == 29804.70
    assert rp["intercompany_receivables_usd"] == 0.00
    assert rp["intercompany_payables_usd"] == 0.00
    assert "eliminated upon corporate consolidation" in rp["elimination_status"]


def test_10_save_reports_and_brand_anonymity(tax_engine):
    """Verifies report generation to disk and strict 100% Brand Anonymity adherence."""
    paths = tax_engine.save_reports_and_ledger()

    assert os.path.exists(paths["report_path"])
    assert os.path.exists(paths["ledger_path"])

    with open(paths["report_path"], "r", encoding="utf-8") as f:
        content = f.read()

    assert "DevSuperSuite Treasury & Corporate Finance" in content
    assert "cfo@devsupersuite.com" in content
    assert "STATUTORY TAX DEFENSE & AUDIT SCORECARD" in content
    assert "ARM'S LENGTH" in content

    # Anonymity verification on report
    for token in FORBIDDEN_FOUNDER_TOKENS:
        assert token not in content, f"Forbidden founder token '{token}' found in tax disclosures report!"

    # Anonymity verification on transfer_pricing_documentation.md
    tp_doc = os.path.join(SERVICES_DIR, "transfer_pricing_documentation.md")
    assert os.path.exists(tp_doc)
    with open(tp_doc, "r", encoding="utf-8") as f:
        tp_content = f.read()
    for token in FORBIDDEN_FOUNDER_TOKENS:
        assert token not in tp_content, f"Forbidden founder token '{token}' found in transfer pricing documentation!"


def test_11_cli_execution():
    """Verifies Tax Audit Defense CLI commands execution."""
    cmd = [
        sys.executable,
        os.path.join(SERVICES_DIR, "tax_audit_defense_engine.py"),
        "--summary",
        "--compile-tax-defense-binder",
        "--audit-transfer-pricing-margins",
        "--generate-statutory-disclosures"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "DevSuperSuite Transfer Pricing & Tax Audit Defense Summary" in res.stdout
    assert "COMPLIANT_ARMS_LENGTH" in res.stdout
    assert "PASS_ARMS_LENGTH" in res.stdout
