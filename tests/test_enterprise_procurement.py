"""
⚡ DevSuperSuite Official: Enterprise Procurement Workflow & PO Financing Tests
File: test_enterprise_procurement.py
Governing Authority: DevSuperSuite Enterprise Procurement (procurement@devsupersuite.com)
Strict Protocol: 100% Brand Anonymity - Zero Founder Personal Identifiers
"""

import os
import sys
import json
import pytest
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Paths Setup
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(SCRATCH_DIR, "services")
DATA_DIR = os.path.join(SCRATCH_DIR, "data")
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")

if SCRATCH_DIR not in sys.path:
    sys.path.insert(0, SCRATCH_DIR)
if SERVICES_DIR not in sys.path:
    sys.path.insert(0, SERVICES_DIR)

from services.enterprise_procurement_workflow_engine import (
    ProcurementCryptoAuthority,
    VendorOnboardingPacketBuilder,
    EnterpriseProcurementWorkflowEngine,
    INSTITUTIONAL_CREDENTIALS,
    PROCUREMENT_LEDGER_PATH,
    REPORT_PATH,
)


@pytest.fixture
def test_authority(tmp_path):
    vault_file = str(tmp_path / "test_procurement_vault.json")
    return ProcurementCryptoAuthority(vault_path=vault_file)


@pytest.fixture
def test_engine(tmp_path, test_authority):
    ledger_file = str(tmp_path / "test_procurement_ledger.json")
    report_file = str(tmp_path / "test_procurement_report.md")
    return EnterpriseProcurementWorkflowEngine(
        ledger_path=ledger_file,
        report_path=report_file,
        authority=test_authority
    )


def test_01_procurement_crypto_authority_key_and_signing(test_authority):
    """Verify Ed25519 key generation, vault persistence, digest signing, and verification."""
    assert os.path.exists(test_authority.vault_path)
    pub_hex = test_authority.get_public_key_hex()
    assert len(pub_hex) == 64

    test_digest = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    sig_hex = test_authority.sign_digest(test_digest)
    assert len(sig_hex) == 128

    # Signature verification
    assert ProcurementCryptoAuthority.verify_digest_signature(test_digest, sig_hex, pub_hex) is True

    # Tampered signature verification must fail
    tampered_digest = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    assert ProcurementCryptoAuthority.verify_digest_signature(tampered_digest, sig_hex, pub_hex) is False


def test_02_vendor_onboarding_packet_us_jurisdiction():
    """Verify US vendor onboarding packet contains W-9, ACORD 25 with $5M cyber, and ACH."""
    packet = VendorOnboardingPacketBuilder.generate_vendor_packet("Lockheed Martin Corp", "US")

    assert packet["packet_id"].startswith("VPK-")
    assert packet["issued_to_company"] == "Lockheed Martin Corp"
    assert "W-9" in packet["tax_form_type"]
    assert packet["legal_entity"] == "DevSuperSuite Official Corporation"
    assert packet["procurement_email"] == "procurement@devsupersuite.com"
    assert packet["duns_number"] == "11-892-4421"
    assert packet["cage_code"] == "9DSS1"
    assert packet["sam_gov_status"] == "ACTIVE_REGISTERED"

    # Insurance verification
    insurance = packet["insurance_certificate"]
    assert insurance["form_type"] == "ACORD 25 Certificate of Liability Insurance"
    assert insurance["cyber_liability_limit_usd"] == 5000000.0
    assert insurance["errors_and_omissions_usd"] == 5000000.0
    assert "Lockheed Martin Corp" in insurance["additional_insured_endorsement"]

    # ACH verification
    ach = packet["ach_wire_settlement"]
    assert "J.P. Morgan Chase" in ach["bank_name"]
    assert ach["routing_aba"] == "021000021"


def test_03_vendor_onboarding_packet_international_jurisdiction():
    """Verify International vendor onboarding packet contains W-8BEN-E and SWIFT/BIC."""
    packet = VendorOnboardingPacketBuilder.generate_vendor_packet("Airbus Defense SAS", "INT")

    assert "W-8BEN-E" in packet["tax_form_type"]
    assert packet["issued_to_company"] == "Airbus Defense SAS"
    assert packet["ach_wire_settlement"]["swift_bic"] == "CHASUS33XXX"


def test_04_po_intake_and_due_date_calculation(test_engine):
    """Verify PO intake properly calculates terms, due date, and 2/10 early discount window."""
    po = test_engine.ingest_purchase_order(
        po_number="PO-TEST-1001",
        company_name="General Dynamics",
        domain="gd.com",
        amount_usd=24999.0,
        payment_terms="2_10_NET_30"
    )

    assert po["po_number"] == "PO-TEST-1001"
    assert po["company_name"] == "General Dynamics"
    assert po["amount_usd"] == 24999.0
    assert po["status"] == "PO_ACCEPTED"
    assert po["early_discount_pct"] == 2.0
    assert po["early_discount_until"] is not None

    # Check date difference: due_date should be ~30 days from issue_date
    issue_dt = datetime.strptime(po["issue_date"], "%Y-%m-%d")
    due_dt = datetime.strptime(po["due_date"], "%Y-%m-%d")
    assert (due_dt - issue_dt).days == 30

    early_dt = datetime.strptime(po["early_discount_until"], "%Y-%m-%d")
    assert (early_dt - issue_dt).days == 10


def test_05_po_duplicate_rejection(test_engine):
    """Verify attempting to ingest duplicate PO number raises ValueError."""
    test_engine.ingest_purchase_order(
        po_number="PO-DUP-1001",
        company_name="Northrop Grumman",
        domain="northrop.com",
        amount_usd=4999.0
    )

    with pytest.raises(ValueError, match="already registered in ledger"):
        test_engine.ingest_purchase_order(
            po_number="PO-DUP-1001",
            company_name="Northrop Grumman",
            domain="northrop.com",
            amount_usd=4999.0
        )


def test_06_signed_invoice_generation_for_po(test_engine):
    """Verify cryptographically signed invoice generation matching an accepted PO."""
    test_engine.ingest_purchase_order(
        po_number="PO-INV-2001",
        company_name="L3Harris Technologies",
        domain="l3harris.com",
        amount_usd=19999.0,
        payment_terms="2_10_NET_30"
    )

    invoice = test_engine.generate_signed_invoice_for_po("PO-INV-2001")

    assert invoice["invoice_number"].startswith("INV-DSS-")
    assert invoice["po_number"] == "PO-INV-2001"
    assert invoice["amount_usd"] == 19999.0
    assert invoice["status"] == "INVOICE_ISSUED"
    assert len(invoice["digest_sha256"]) == 64
    assert len(invoice["provider_signature_hex"]) == 128

    # Verify cryptographic signature
    is_valid = ProcurementCryptoAuthority.verify_digest_signature(
        invoice["digest_sha256"],
        invoice["provider_signature_hex"],
        invoice["provider_public_key_hex"]
    )
    assert is_valid is True

    # Verify PO state transitioned to INVOICE_GENERATED
    po = next(p for p in test_engine.ledger["purchase_orders"] if p["po_number"] == "PO-INV-2001")
    assert po["status"] == "INVOICE_GENERATED"
    assert po["invoiced"] is True


def test_07_early_payment_discount_settlement(test_engine):
    """Verify 2/10 Net 30 early discount is computed and applied when settled within 10 days."""
    test_engine.ingest_purchase_order(
        po_number="PO-EARLY-3001",
        company_name="BAE Systems",
        domain="baesystems.com",
        amount_usd=10000.0,
        payment_terms="2_10_NET_30"
    )
    inv = test_engine.generate_signed_invoice_for_po("PO-EARLY-3001")

    # Settle immediately (day 0, within early discount window)
    now_iso = datetime.now(timezone.utc).isoformat()
    res = test_engine.settle_invoice(inv["invoice_number"], settlement_date_str=now_iso)

    assert res["status"] == "SETTLED_PAID"
    assert res["discount_applied"] is True
    assert res["discount_amount_usd"] == 200.0  # 2% of 10,000
    assert res["net_paid_usd"] == 9800.0

    # Verify PO status transitioned to SETTLED_PAID
    po = next(p for p in test_engine.ledger["purchase_orders"] if p["po_number"] == "PO-EARLY-3001")
    assert po["status"] == "SETTLED_PAID"


def test_08_standard_terms_settlement(test_engine):
    """Verify Net 60 settlement without early discount pays full amount."""
    test_engine.ingest_purchase_order(
        po_number="PO-NET60-4001",
        company_name="Boeing Defense",
        domain="boeing.com",
        amount_usd=5000.0,
        payment_terms="NET_60"
    )
    inv = test_engine.generate_signed_invoice_for_po("PO-NET60-4001")

    res = test_engine.settle_invoice(inv["invoice_number"])

    assert res["status"] == "SETTLED_PAID"
    assert res["discount_applied"] is False
    assert res["discount_amount_usd"] == 0.0
    assert res["net_paid_usd"] == 5000.0


def test_09_invoice_already_settled_handling(test_engine):
    """Verify attempting to settle an already paid invoice returns ALREADY_SETTLED."""
    test_engine.ingest_purchase_order(
        po_number="PO-SETTLE-5001",
        company_name="Leidos Inc",
        domain="leidos.com",
        amount_usd=3000.0
    )
    inv = test_engine.generate_signed_invoice_for_po("PO-SETTLE-5001")
    test_engine.settle_invoice(inv["invoice_number"])

    # Second settlement attempt
    res2 = test_engine.settle_invoice(inv["invoice_number"])
    assert res2["status"] == "ALREADY_SETTLED"


def test_10_missing_po_or_invoice_handling(test_engine):
    """Verify KeyError is raised when referencing non-existent PO or Invoice."""
    with pytest.raises(KeyError, match="Purchase Order 'PO-UNKNOWN' not found"):
        test_engine.generate_signed_invoice_for_po("PO-UNKNOWN")

    with pytest.raises(KeyError, match="Invoice 'INV-UNKNOWN' not found"):
        test_engine.settle_invoice("INV-UNKNOWN")


def test_11_audit_and_markdown_report_generation(test_engine):
    """Verify executive procurement portfolio audit and report generation."""
    # Issue packet
    test_engine.issue_vendor_onboarding_packet("Lockheed Martin", "US")

    # Ingest and settle PO 1
    test_engine.ingest_purchase_order("PO-AUDIT-1", "Lockheed Martin", "lockheedmartin.com", 20000.0, "2_10_NET_30")
    inv1 = test_engine.generate_signed_invoice_for_po("PO-AUDIT-1")
    test_engine.settle_invoice(inv1["invoice_number"])

    # Ingest and leave open PO 2
    test_engine.ingest_purchase_order("PO-AUDIT-2", "Raytheon", "rtx.com", 10000.0, "NET_60")
    test_engine.generate_signed_invoice_for_po("PO-AUDIT-2")

    audit = test_engine.audit_procurement_portfolio()
    assert audit["total_vendor_packets_issued"] == 1
    assert audit["total_purchase_orders"] == 2
    assert audit["total_po_value_usd"] == 30000.0
    assert audit["total_invoices_issued"] == 2
    assert audit["settled_invoices_count"] == 1
    assert audit["total_settled_net_usd"] == 19600.0  # 20,000 - 400 (2%)
    assert audit["total_early_discounts_claimed_usd"] == 400.0
    assert audit["outstanding_invoices_count"] == 1
    assert audit["total_outstanding_ar_usd"] == 10000.0
    assert audit["cryptographic_audit_verdict"] == "ALL_INVOICES_CRYPTOGRAPHICALLY_VERIFIED"

    report_path = test_engine.render_markdown_report()
    assert os.path.exists(report_path)
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "# ⚡ DevSuperSuite Official: Enterprise Procurement Workflow & PO Financing Report" in content
    assert "Lockheed Martin" in content
    assert "Raytheon" in content
    assert "ALL_INVOICES_CRYPTOGRAPHICALLY_VERIFIED" in content
    assert "procurement@devsupersuite.com" in content


def test_12_cli_interface_execution():
    """Verify all CLI subcommands execute with exit code 0."""
    python_bin = sys.executable
    script_path = os.path.join(SERVICES_DIR, "enterprise_procurement_workflow_engine.py")

    unique_suffix = os.urandom(4).hex().upper()
    po_num = f"PO-CLI-{unique_suffix}"
    inv_num = f"INV-DSS-CLI-{unique_suffix}"

    commands = [
        ["--summary"],
        ["--generate-vendor-packet", "--company", "Booz Allen Hamilton", "--jurisdiction", "US"],
        ["--ingest-po", "--po-number", po_num, "--company", "Booz Allen Hamilton", "--domain", "boozallen.com", "--amount", "15000.0"],
        ["--issue-invoice", "--po-number", po_num],
        ["--settle-invoice", "--invoice-number", inv_num],
        ["--audit-procurement"],
        ["--export-procurement-report"]
    ]

    for args in commands:
        cmd = [python_bin, script_path] + args
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        assert res.returncode == 0, f"CLI command {cmd} failed with stderr: {res.stderr}"


def test_13_strict_brand_anonymity_compliance():
    """Verify zero personal founder leaks across all Phase 28 assets."""
    forbidden_tokens = [
        bytes.fromhex("41746861727661").decode("utf-8"),
        bytes.fromhex("506164687965").decode("utf-8"),
        bytes.fromhex("39383930343431323933").decode("utf-8"),
    ]

    phase_28_files = [
        Path(SERVICES_DIR) / "enterprise_procurement_workflow_engine.py",
        Path(DATA_DIR) / "enterprise_procurement_ledger.json",
        Path(REPORTS_DIR) / "enterprise_procurement_workflow_report.md",
        Path(TESTS_DIR) / "test_enterprise_procurement.py",
    ]

    for file_path in phase_28_files:
        assert file_path.exists(), f"File {file_path} must exist"
        content = file_path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token.lower() not in content.lower(), (
                f"Brand anonymity violation: found forbidden token in {file_path}"
            )
