"""
⚡ DevSuperSuite Global Treasury Desk - Unit & Integration Test Suite
File: test_corporate_nexus_engine.py
Phase: 30 - Enterprise Corporate Economic Nexus & State Apportionment Engine
Author: DevSuperSuite Global Treasury Desk
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
DATA_DIR = os.path.join(SERVICES_DIR, "data")
ROOT_DATA_DIR = os.path.join(PROJECT_ROOT, "data")
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")

sys.path.insert(0, PROJECT_ROOT)

from services.enterprise_corporate_nexus_engine import (
    EnterpriseCorporateNexusEngine,
    AUTHORIZED_SHARES_COUNT,
    TOTAL_GROSS_ASSETS_USD,
    STATE_NEXUS_THRESHOLDS,
    STATE_COMMERCIAL_SALES,
    DEFAULT_NEXUS_SCHEDULE_FILE,
    ROOT_NEXUS_SCHEDULE_FILE,
    DEFAULT_NEXUS_REPORT_FILE
)

FORBIDDEN_FOUNDER_TOKENS = [
    "Pratik", "pratik", "atpad", "atpadkar", "gmail.com", "+919", "+91 9"
]


@pytest.fixture
def engine():
    return EnterpriseCorporateNexusEngine()


def test_01_wayfair_economic_nexus_threshold_audits(engine):
    """Verifies multi-state economic nexus audit under South Dakota v. Wayfair standards."""
    audit = engine.audit_economic_nexus()

    assert audit["total_us_commercial_revenue_usd"] > 500000.0
    assert audit["total_direct_enterprise_revenue_usd"] == 425000.00
    assert audit["overall_economic_nexus_status"] == "ZERO_UNREGISTERED_NEXUS_EXPOSURE"
    assert audit["states_with_direct_nexus_count"] == 0

    audits = {a["state_code"]: a for a in audit["state_nexus_audits"]}

    # California check: $165k direct < $500k threshold
    ca = audits["CA"]
    assert ca["statutory_revenue_threshold_usd"] == 500000.00
    assert ca["seller_direct_nexus_established"] is False
    assert ca["nexus_status"] == "SAFE_HARBOR_EXEMPT"

    # New York check: $95k direct < $500k & 12 tx < 100 tx
    ny = audits["NY"]
    assert ny["statutory_revenue_threshold_usd"] == 500000.00
    assert ny["statutory_transaction_threshold"] == 100
    assert ny["seller_direct_nexus_established"] is False

    # Washington check: $45k direct < $100k threshold
    wa = audits["WA"]
    assert wa["statutory_revenue_threshold_usd"] == 100000.00
    assert wa["seller_direct_nexus_established"] is False

    # Illinois check: $35k direct < $100k & 5 tx < 200 tx
    il = audits["IL"]
    assert il["statutory_revenue_threshold_usd"] == 100000.00
    assert il["statutory_transaction_threshold"] == 200
    assert il["seller_direct_nexus_established"] is False


def test_02_marketplace_facilitator_statutory_relief(engine):
    """Verifies Gumroad marketplace facilitator volume tracking and statutory relief."""
    audit = engine.audit_economic_nexus()

    assert audit["total_marketplace_gumroad_revenue_usd"] == 127000.00
    assert audit["total_marketplace_transactions"] == 890
    assert audit["marketplace_facilitator_relief_pct"] == 100.0

    for a in audit["state_nexus_audits"]:
        assert "Gumroad, Inc." in a["marketplace_tax_remitted_by"]
        assert len(a["marketplace_facilitator_statute"]) > 5


def test_03_delaware_authorized_shares_calculation(engine):
    """Verifies Delaware Authorized Shares Method franchise tax calculation on 13.8M shares."""
    de_tax = engine.calculate_delaware_franchise_tax()

    auth = de_tax["authorized_shares_method"]
    assert auth["calculated_franchise_tax_usd"] == 117720.00
    assert auth["annual_report_fee_usd"] == 50.00
    assert auth["total_liability_usd"] == 117770.00
    assert de_tax["statutory_authorized_shares"] == 13821138


def test_04_delaware_assumed_par_value_minimization(engine):
    """Verifies Delaware Assumed Par Value Capital Method reduces tax to $400 statutory minimum."""
    de_tax = engine.calculate_delaware_franchise_tax()

    assumed = de_tax["assumed_par_value_capital_method"]
    assert assumed["calculated_franchise_tax_usd"] == 400.00
    assert assumed["annual_report_fee_usd"] == 50.00
    assert assumed["total_liability_usd"] == 450.00
    assert assumed["assumed_par_value_capital_usd"] == 125000.00
    assert assumed["assumed_par_value_per_share_usd"] > 0.0


def test_05_delaware_franchise_tax_savings(engine):
    """Verifies Delaware Franchise Tax savings exceed $115,000 USD (99%+ reduction)."""
    de_tax = engine.calculate_delaware_franchise_tax()

    assert de_tax["tax_savings_usd"] == 117320.00
    assert de_tax["savings_percentage"] > 99.0
    assert de_tax["savings_percentage"] == 99.62
    assert de_tax["optimal_method_selected"] == "ASSUMED_PAR_VALUE_CAPITAL_METHOD"


def test_06_single_sales_factor_apportionment_weights(engine):
    """Verifies Single Sales Factor (SSF) revenue apportionment weights sum to 100%."""
    apport = engine.apportion_state_revenue()

    assert apport["total_apportionable_us_direct_revenue_usd"] == 425000.00
    assert "Market-Based Sourcing" in apport["sourcing_doctrine"]

    schedule = {s["state_code"]: s for s in apport["apportionment_schedule"]}
    assert schedule["CA"]["single_sales_factor_pct"] == 38.82
    assert schedule["NY"]["single_sales_factor_pct"] == 22.35
    assert schedule["TX"]["single_sales_factor_pct"] == 17.65
    assert schedule["WA"]["single_sales_factor_pct"] == 10.59
    assert schedule["IL"]["single_sales_factor_pct"] == 8.24
    assert schedule["OTHER_STATES"]["single_sales_factor_pct"] == 2.35

    total_weight = sum(s["single_sales_factor_pct"] for s in apport["apportionment_schedule"])
    assert 99.9 <= total_weight <= 100.1


def test_07_nexus_breach_detection_sensitivity():
    """Verifies that exceeding statutory sales or transaction thresholds flags taxable nexus."""
    simulated_breach = {
        "CA": {
            "direct_enterprise_revenue_usd": 650000.00,  # Exceeds $500k
            "direct_transaction_count": 25,
            "marketplace_gumroad_revenue_usd": 10000.00,
            "marketplace_transaction_count": 50
        },
        "NY": {
            "direct_enterprise_revenue_usd": 50000.00,
            "direct_transaction_count": 5,
            "marketplace_gumroad_revenue_usd": 5000.00,
            "marketplace_transaction_count": 10
        },
        "TX": {
            "direct_enterprise_revenue_usd": 50000.00,
            "direct_transaction_count": 5,
            "marketplace_gumroad_revenue_usd": 5000.00,
            "marketplace_transaction_count": 10
        },
        "WA": {
            "direct_enterprise_revenue_usd": 150000.00,  # Exceeds $100k
            "direct_transaction_count": 10,
            "marketplace_gumroad_revenue_usd": 5000.00,
            "marketplace_transaction_count": 10
        },
        "IL": {
            "direct_enterprise_revenue_usd": 20000.00,
            "direct_transaction_count": 250,  # Exceeds 200 transactions
            "marketplace_gumroad_revenue_usd": 5000.00,
            "marketplace_transaction_count": 10
        }
    }

    engine_breach = EnterpriseCorporateNexusEngine(sales_data=simulated_breach)
    audit = engine_breach.audit_economic_nexus()

    assert audit["overall_economic_nexus_status"] == "NEXUS_ACTION_REQUIRED"
    assert audit["states_with_direct_nexus_count"] == 3
    assert set(audit["states_with_nexus"]) == {"CA", "WA", "IL"}


def test_08_artifact_export_and_json_persistence(engine):
    """Verifies JSON schedule and Markdown report persistence."""
    paths = engine.export_all_artifacts()

    for key, path in paths.items():
        assert os.path.exists(path), f"File {path} was not created"

    # Verify JSON schedule
    with open(paths["schedule_path"], "r", encoding="utf-8") as f:
        schedule = json.load(f)
    assert schedule["metadata"]["reporting_entity"] == "DevSuperSuite Group"
    assert "economic_nexus_audit" in schedule
    assert "delaware_franchise_tax_optimization" in schedule
    assert "single_sales_factor_apportionment" in schedule

    # Verify Markdown report
    with open(paths["report_path"], "r", encoding="utf-8") as f:
        report_md = f.read()
    assert "ENTERPRISE CORPORATE ECONOMIC NEXUS & STATE APPORTIONMENT REPORT" in report_md
    assert "South Dakota v. Wayfair" in report_md
    assert "Assumed Par Value Capital Method" in report_md


def test_09_cli_command_executions():
    """Verifies multi-action CLI commands execute cleanly."""
    script_path = os.path.join(SERVICES_DIR, "enterprise_corporate_nexus_engine.py")

    cmd = [
        sys.executable,
        script_path,
        "--audit-economic-nexus",
        "--calculate-delaware-tax",
        "--apportion-state-revenue",
        "--export-nexus-binder",
        "--summary"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"CLI failed: {res.stderr}"
    assert "Multi-State Economic Nexus Audit (South Dakota v. Wayfair)" in res.stdout
    assert "Delaware Corporate Franchise Tax Minimization (8 Del. C. § 503)" in res.stdout
    assert "Single Sales Factor (SSF) Multi-State Apportionment" in res.stdout


def test_10_strict_brand_anonymity():
    """Verifies 100% Brand Anonymity across all Phase 30 files."""
    files_to_check = [
        os.path.join(SERVICES_DIR, "enterprise_corporate_nexus_engine.py"),
        os.path.join(REPORTS_DIR, "corporate_economic_nexus_apportionment_report.md"),
        os.path.join(DATA_DIR, "corporate_economic_nexus_schedule.json"),
        os.path.join(ROOT_DATA_DIR, "corporate_economic_nexus_schedule.json")
    ]

    for file_path in files_to_check:
        assert os.path.exists(file_path), f"File {file_path} must exist for anonymity check"
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().lower()
        for token in FORBIDDEN_FOUNDER_TOKENS:
            assert token.lower() not in content, (
                f"Forbidden founder token '{token}' detected in {file_path}!"
            )
