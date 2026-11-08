"""
⚡ DevSuperSuite Global Treasury Desk - FASB ASC 830 FX Translation & Revaluation Test Suite
File: test_asc830_fx_translation.py
Target: enterprise_asc830_fx_translation_engine.py
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

from enterprise_asc830_fx_translation_engine import (
    EnterpriseASC830FXTranslationEngine,
    ASC830_EXCHANGE_RATES,
    GROUP_SUBSIDIARY_BALANCES,
    GROUP_PARENT_ENTITY,
    TREASURY_DESK_TITLE,
    TREASURY_OFFICIAL_EMAIL,
    DEFAULT_FX_SCHEDULE_FILE,
    ROOT_FX_SCHEDULE_FILE,
    DEFAULT_FX_REPORT_FILE
)


@pytest.fixture
def fx_engine():
    """Initializes the institutional FASB ASC 830 foreign currency translation engine."""
    return EnterpriseASC830FXTranslationEngine()


def test_01_functional_currency_determinations(fx_engine):
    """Verifies functional currency determinations for US Parent, Ireland Hub, and Singapore Hub under ASC 830-10."""
    audit = fx_engine.audit_functional_currencies()
    ents = audit["entity_audits"]

    assert ents["US_PARENT"]["functional_currency"] == "USD"
    assert ents["US_PARENT"]["translation_required"] is False

    assert ents["IE_EMEA"]["functional_currency"] == "EUR"
    assert ents["IE_EMEA"]["translation_required"] is True
    assert ents["IE_EMEA"]["accounting_method"] == "CURRENT_RATE_METHOD_ASC830"

    assert ents["SG_APAC"]["functional_currency"] == "SGD"
    assert ents["SG_APAC"]["translation_required"] is True
    assert ents["SG_APAC"]["accounting_method"] == "CURRENT_RATE_METHOD_ASC830"


def test_02_foreign_transaction_remeasurement_pnl(fx_engine):
    """Verifies ASC 830-20 non-functional monetary remeasurement gains recognized directly in Net Income P&L."""
    remeas = fx_engine.remeasure_foreign_transactions()
    
    assert remeas["accounting_treatment"] == "ASC 830-20 (Immediate P&L Recognition in Net Income)"
    assert remeas["total_net_income_fx_gain_usd"] == 578.85
    assert len(remeas["remeasurement_entries"]) == 2

    ie_entry = next(e for e in remeas["remeasurement_entries"] if "EMEA" in e["entity"])
    assert ie_entry["consolidated_pnl_fx_gain_usd"] == 488.25

    sg_entry = next(e for e in remeas["remeasurement_entries"] if "APAC" in e["entity"])
    assert sg_entry["consolidated_pnl_fx_gain_usd"] == 90.60


def test_03_current_rate_method_assets_and_liabilities(fx_engine):
    """Verifies that foreign assets and liabilities are translated at current period-end spot exchange rates."""
    trans = fx_engine.translate_balance_sheets()
    subs = trans["subsidiary_translations"]

    ie = subs["IE_EMEA"]
    assert ie["spot_rate"] == 1.0850
    assert ie["total_assets_usd"] == 85072.50
    assert ie["total_liabilities_usd"] == 36062.50

    sg = subs["SG_APAC"]
    assert sg["spot_rate"] == 0.7550
    assert sg["total_assets_usd"] == 34060.00
    assert sg["total_liabilities_usd"] == 13657.50


def test_04_historical_rate_capital_translation(fx_engine):
    """Verifies that subsidiary common stock / share capital is translated at historical transaction rates."""
    trans = fx_engine.translate_balance_sheets()
    subs = trans["subsidiary_translations"]

    assert subs["IE_EMEA"]["historical_rate"] == 1.0500
    assert subs["IE_EMEA"]["share_capital_usd"] == 10500.00  # €10,000 * 1.0500

    assert subs["SG_APAC"]["historical_rate"] == 0.7300
    assert subs["SG_APAC"]["share_capital_usd"] == 3650.00   # S$5,000 * 0.7300


def test_05_period_average_rate_retained_earnings(fx_engine):
    """Verifies that subsidiary retained earnings are translated at weighted-average exchange rates."""
    trans = fx_engine.translate_balance_sheets()
    subs = trans["subsidiary_translations"]

    assert subs["IE_EMEA"]["average_rate"] == 1.0720
    assert subs["IE_EMEA"]["retained_earnings_usd"] == 37702.78  # €35,170.50 * 1.0720

    assert subs["SG_APAC"]["average_rate"] == 0.7420
    assert subs["SG_APAC"]["retained_earnings_usd"] == 16341.20  # S$22,023.18 * 0.7420


def test_06_cumulative_translation_adjustment_cta_oci(fx_engine):
    """Verifies Cumulative Translation Adjustment (CTA) recorded in Other Comprehensive Income (OCI)."""
    trans = fx_engine.translate_balance_sheets()
    cons = trans["consolidated_balance_sheet"]

    assert cons["accumulated_other_comprehensive_income_cta_usd"] == 1218.52
    assert trans["subsidiary_translations"]["IE_EMEA"]["cumulative_translation_adjustment_cta_usd"] > 0
    assert trans["subsidiary_translations"]["SG_APAC"]["cumulative_translation_adjustment_cta_usd"] > 0


def test_07_consolidated_balance_sheet_equilibrium_proof(fx_engine):
    """Verifies zero-variance balance sheet accounting equilibrium proof (Assets = Liabilities + Equity)."""
    trans = fx_engine.translate_balance_sheets()
    cons = trans["consolidated_balance_sheet"]

    assert cons["balance_sheet_status"] == "ZERO_VARIANCE_BALANCED"
    assert cons["accounting_equilibrium_variance_usd"] == 0.00
    assert cons["consolidated_assets_usd"] == 644376.79
    assert cons["consolidated_liabilities_usd"] == 33870.00
    assert cons["consolidated_stockholders_equity_usd"] == 610506.79
    assert round(cons["consolidated_liabilities_usd"] + cons["consolidated_stockholders_equity_usd"], 2) == 644376.79


def test_08_intercompany_eliminations_integrity(fx_engine):
    """Verifies elimination of intercompany CSA receivables ($31,250) and subsidiary investments ($14,150)."""
    trans = fx_engine.translate_balance_sheets()
    cons = trans["consolidated_balance_sheet"]
    
    # Capital on consolidated balance sheet reflects only Parent common stock + APIC ($125,000)
    assert cons["consolidated_capital_and_apic_usd"] == 125000.00


def test_09_fx_translation_schedule_json_persistence(fx_engine):
    """Verifies export of translation schedule JSON files and mirrored persistence."""
    paths = fx_engine.export_all()
    
    assert os.path.exists(paths["schedule_file"])
    assert os.path.exists(paths["root_schedule_file"])
    assert os.path.exists(paths["report_file"])

    with open(paths["schedule_file"], "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["binder_id"] == "DSS-ASC830-2026-FX-BINDER"
        assert data["executive_summary"]["balance_sheet_proof"] == "ZERO_VARIANCE_BALANCED"
        assert data["executive_summary"]["consolidated_assets_usd"] == 644376.79
        assert "asc830_translations" in data


def test_10_audit_report_markdown_integrity(fx_engine):
    """Verifies that the markdown report contains executive summaries, tables, and Mermaid flowcharts."""
    paths = fx_engine.export_all()
    
    with open(paths["report_file"], "r", encoding="utf-8") as f:
        md = f.read()
        assert "DevSuperSuite Global Treasury Desk" in md
        assert "FASB ASC 830" in md
        assert "$644,376.79" in md
        assert "ZERO_VARIANCE_BALANCED" in md
        assert "flowchart TD" in md


def test_11_cli_interface_execution():
    """Smoke tests all CLI arguments for the ASC 830 FX translation engine."""
    cli_flags = [
        "--audit-functional-currencies",
        "--remeasure-foreign-transactions",
        "--translate-balance-sheets",
        "--calculate-cta-oci",
        "--export-fx-binder",
        "--summary"
    ]
    script_path = os.path.join(SERVICES_DIR, "enterprise_asc830_fx_translation_engine.py")

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
        os.path.join(SERVICES_DIR, "enterprise_asc830_fx_translation_engine.py"),
        DEFAULT_FX_SCHEDULE_FILE,
        ROOT_FX_SCHEDULE_FILE,
        DEFAULT_FX_REPORT_FILE
    ]

    for fpath in target_files:
        assert os.path.exists(fpath), f"File {fpath} must exist for anonymity check"
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            for token in forbidden_tokens:
                assert token not in content, f"Forbidden brand anonymity token '{token}' discovered in {fpath}"
