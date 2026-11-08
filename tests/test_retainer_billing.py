"""
⚡ DevSuperSuite Commercial Operations - Unit & Integration Test Suite
File: test_retainer_billing.py
Target: retainer_billing_engine.py (Enterprise Q2C Automated Billing & Retainer Engine)
Strict Compliance: 100% Brand Anonymity - DevSuperSuite Commercial Operations Only.
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

from retainer_billing_engine import (
    RetainerBillingEngine,
    BASELINE_RETAINER_FEE_USD,
    BASELINE_HOURS_INCLUDED,
    OVERAGE_HOURLY_RATE_USD,
    DEFAULT_LUT_REF,
    INVOICES_DIR
)

@pytest.fixture
def isolated_engine(tmp_path):
    """Initializes a retainer billing engine with isolated test database."""
    test_ledger = os.path.join(tmp_path, "test_retainer_ledger.json")
    engine = RetainerBillingEngine(ledger_file=test_ledger)
    return engine

def test_01_baseline_retainer_calculation(isolated_engine):
    """Verifies baseline monthly retainer ($8,500/mo) and direct margin metrics."""
    calc = isolated_engine.compute_billing_details("NEXUS-RET-2026")

    assert calc["baseline_fee_usd"] == BASELINE_RETAINER_FEE_USD
    assert calc["baseline_hours"] == BASELINE_HOURS_INCLUDED
    assert calc["total_hours_logged"] == 45.0
    assert calc["overage_hours"] == 0.0
    assert calc["total_invoiced_usd"] == 8500.00
    assert calc["gross_margin_pct"] >= 65.0  # Realized ~85.18%

def test_02_hour_logging_and_overage_trigger(isolated_engine):
    """Logs additional engineering hours to trigger $120.00/hr overage charges."""
    # Log 10.0 additional hours
    res = isolated_engine.record_hours(
        contract_key="NEXUS-RET-2026",
        hours=10.0,
        role="Principal Solutions Architect",
        task="Custom invariant AST visitors for auth gateway"
    )

    assert res["status"] == "HOURS_RECORDED"
    assert res["total_hours_logged"] == 55.0  # 45 base + 10 overage
    assert res["overage_hours"] == 10.0
    assert res["estimated_overage_charge_usd"] == 1200.00  # 10 * $120

    # Verify billing details reflect overage
    calc = isolated_engine.compute_billing_details("NEXUS-RET-2026")
    assert calc["overage_hours"] == 10.0
    assert calc["overage_amount_usd"] == 1200.00
    assert calc["total_invoiced_usd"] == 9700.00  # $8,500 + $1,200
    assert calc["gross_margin_pct"] >= 65.0

def test_03_statutory_late_interest_compounding(isolated_engine):
    """Verifies daily statutory interest compounding at 1.5%/month (18.0% APR)."""
    # 0 days overdue -> zero interest
    interest_0, total_0 = isolated_engine.compute_statutory_interest(8500.00, days_overdue=0)
    assert interest_0 == 0.0
    assert total_0 == 8500.00

    # 18 days overdue
    interest_18, total_18 = isolated_engine.compute_statutory_interest(8500.00, days_overdue=18)
    assert interest_18 > 70.0
    assert interest_18 == pytest.approx(75.77, abs=1.0)
    assert total_18 == 8500.00 + interest_18

    # 30 days overdue (approx 1 full month of 1.5% interest = ~$127.50)
    interest_30, total_30 = isolated_engine.compute_statutory_interest(8500.00, days_overdue=30)
    assert interest_30 == pytest.approx(126.60, abs=2.0)

def test_04_retainer_invoice_generation_and_tax_clauses(isolated_engine, tmp_path):
    """Generates official invoice and validates US/EU cross-border and LUT clauses."""
    invoice_file = os.path.join(tmp_path, "test_invoice.md")
    md = isolated_engine.generate_retainer_invoice_markdown(
        contract_key="NEXUS-RET-2026",
        invoice_id="INV-RET-2026-001",
        include_overage=False
    )
    with open(invoice_file, "w", encoding="utf-8") as f:
        f.write(md)

    assert os.path.exists(invoice_file)
    assert "INV-RET-2026-001" in md
    assert "$8,500.00 USD" in md
    assert "Nexus Enterprise Technologies Corp." in md

    # Tax & Export Compliance Annotations
    assert DEFAULT_LUT_REF in md
    assert "Article 7 (Business Profits)" in md
    assert "Active NFFE" in md
    assert "Article 196 of EU VAT Directive" in md
    assert "P0804" in md

    # Settlement Rails
    assert "DEVSUS33XXX" in md
    assert "OUR" in md

def test_05_dunning_notice_generation_and_work_freeze(isolated_engine, tmp_path):
    """Generates statutory dunning notice and verifies operational freeze triggers."""
    notice_file = os.path.join(tmp_path, "test_dunning.md")
    md = isolated_engine.generate_dunning_notice_markdown(
        contract_key="NEXUS-RET-2026",
        notice_id="DUN-2026-001-NOTICE",
        invoice_id="INV-RET-2026-001",
        principal_amount_usd=8500.00,
        days_overdue=18
    )
    with open(notice_file, "w", encoding="utf-8") as f:
        f.write(md)

    assert os.path.exists(notice_file)
    assert "DUN-2026-001-NOTICE" in md
    assert "FORMAL NOTICE OF DELINQUENCY" in md
    assert "18 Calendar Days Overdue" in md
    assert "SOFT FREEZE TRIGGER" in md
    assert "HARD FREEZE TRIGGER" in md
    assert "$8,575.77 USD" in md or "8,57" in md

def test_06_disk_artifacts_integrity():
    """Verifies that the generated production invoice and dunning notice exist on disk."""
    prod_invoice = os.path.join(INVOICES_DIR, "INV-RET-2026-001.md")
    prod_dunning = os.path.join(INVOICES_DIR, "DUN-2026-001-NOTICE.md")

    assert os.path.exists(prod_invoice), "INV-RET-2026-001.md must exist in invoices dir"
    assert os.path.exists(prod_dunning), "DUN-2026-001-NOTICE.md must exist in invoices dir"

    with open(prod_invoice, "r", encoding="utf-8") as f:
        inv_text = f.read()
    with open(prod_dunning, "r", encoding="utf-8") as f:
        dun_text = f.read()

    assert "$8,500.00" in inv_text
    assert "DevSuperSuite Commercial Operations" in inv_text
    assert "billing@devsupersuite.com" in inv_text
    assert "billing@devsupersuite.com" in dun_text

def test_07_strict_brand_anonymity(isolated_engine):
    """Enforces 100% Brand Anonymity across invoice and dunning notice artifacts."""
    inv_md = isolated_engine.generate_retainer_invoice_markdown()
    dun_md = isolated_engine.generate_dunning_notice_markdown()

    for text in (inv_md, dun_md):
        # Permitted Brand Identity
        assert "DevSuperSuite" in text
        assert "billing@devsupersuite.com" in text

        # Prohibited Leaks
        assert "pratik" not in text.lower()
        assert "atpad" not in text.lower()
        assert "+91" not in text

def test_08_cli_execution():
    """Tests execution of the Q2C CLI with various flags."""
    script_path = os.path.join(SERVICES_DIR, "retainer_billing_engine.py")

    res = subprocess.run(
        [sys.executable, script_path, "--summary"],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0
    assert "Retainer Q2C Executive Summary" in res.stdout
    assert "Monthly Baseline Fee:    $8,500.00 USD" in res.stdout
    assert "Nexus Enterprise Technologies Corp." in res.stdout
