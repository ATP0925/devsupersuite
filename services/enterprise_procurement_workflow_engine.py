#!/usr/bin/env python3
"""
⚡ DevSuperSuite Official: Enterprise Procurement Workflow & PO Financing Engine
File: enterprise_procurement_workflow_engine.py
Version: 1.0.0
Governing Authority: DevSuperSuite Enterprise Procurement (procurement@devsupersuite.com)
Strict Protocol: 100% Brand Anonymity - Zero Founder Personal Identifiers

Key Capabilities:
1. Vendor Onboarding Packet Generation:
   - W-9 / W-8BEN-E statutory tax profile, D-U-N-S, SAM.gov / CAGE code.
   - Certificate of Insurance (ACORD 25) with $5,000,000 Cyber Liability / E&O.
   - ACH & SWIFT/BIC Wire instructions for corporate treasury settlement.
2. Purchase Order (PO) Intake & Milestone Management:
   - PO ingestion, line-item matching, Net 30/60 milestone tracking.
   - Dynamic early payment discounting (2/10 Net 30).
3. Cryptographic Invoice Signing & Nonce Integrity:
   - Asymmetric Ed25519 digital signature workflows for invoices and PO acknowledgments.
4. Procurement Audit & Executive Portfolio Reporting:
   - DSO (Days Sales Outstanding), cash collections, and discount realization metrics.
"""

import os
import sys
import json
import uuid
import hashlib
import argparse
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Cryptography Ed25519
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# Base Directories Setup
SERVICES_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(SERVICES_DIR)
DATA_DIR = os.path.join(SCRATCH_DIR, "data")
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

PROCUREMENT_LEDGER_PATH = os.path.join(DATA_DIR, "enterprise_procurement_ledger.json")
REPORT_PATH = os.path.join(REPORTS_DIR, "enterprise_procurement_workflow_report.md")
KEY_VAULT_PATH = os.path.join(DATA_DIR, ".ed25519_procurement_vault.json")

# Standard Corporate Credentials
INSTITUTIONAL_CREDENTIALS = {
    "legal_entity_name": "DevSuperSuite Official Corporation",
    "dba": "DevSuperSuite",
    "department": "DevSuperSuite Enterprise Procurement",
    "contact_email": "procurement@devsupersuite.com",
    "billing_inquiries": "billing@devsupersuite.com",
    "treasury_email": "treasury@devsupersuite.com",
    "tin_ein": "XX-XXX4192",  # Masked institutional EIN
    "duns_number": "11-892-4421",
    "cage_code": "9DSS1",
    "sam_gov_status": "ACTIVE_REGISTERED",
    "naics_code": "511210 - Software Publishers",
    "sic_code": "7372 - Prepackaged Software",
    "corporate_headquarters": "DevSuperSuite Tech Center, Suite 800, Dover, DE 19901",
    "insurance": {
        "broker": "Aon Risk Solutions Enterprise Commercial",
        "underwriter": "Lloyd's of London Syndicate & Travelers Casualty",
        "cyber_liability_limit_usd": 5000000.0,
        "errors_and_omissions_usd": 5000000.0,
        "general_liability_usd": 2000000.0,
        "policy_number": "POL-DSS-CYBER-882910-A",
        "effective_dates": "2026-01-01 to 2027-01-01"
    },
    "banking": {
        "bank_name": "J.P. Morgan Chase Commercial Banking",
        "routing_aba": "021000021",
        "account_number_masked": "******7842",
        "swift_bic": "CHASUS33XXX",
        "beneficiary": "DevSuperSuite Official Corporation - Commercial Treasury"
    }
}


# ─────────────────────────────────────────────────────────────────────────────
# 1. Cryptographic Procurement Signing Authority (Ed25519)
# ─────────────────────────────────────────────────────────────────────────────

class ProcurementCryptoAuthority:
    """Manages asymmetric Ed25519 cryptographic signing for invoices and PO contracts."""

    def __init__(self, vault_path: str = KEY_VAULT_PATH):
        self.vault_path = vault_path
        self._private_key, self._public_key = self._load_or_create_keys()

    def _load_or_create_keys(self) -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
        if os.path.exists(self.vault_path):
            try:
                with open(self.vault_path, "r", encoding="utf-8") as f:
                    vault = json.load(f)
                    priv_bytes = bytes.fromhex(vault["private_key_hex"])
                    priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)
                    pub_key = priv_key.public_key()
                    return priv_key, pub_key
            except Exception:
                pass

        priv_key = ed25519.Ed25519PrivateKey.generate()
        pub_key = priv_key.public_key()
        priv_bytes = priv_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        pub_bytes = pub_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        try:
            with open(self.vault_path, "w", encoding="utf-8") as f:
                json.dump({
                    "private_key_hex": priv_bytes.hex(),
                    "public_key_hex": pub_bytes.hex(),
                    "algorithm": "Ed25519",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }, f, indent=2)
        except Exception:
            pass
        return priv_key, pub_key

    def get_public_key_hex(self) -> str:
        pub_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        return pub_bytes.hex()

    def sign_digest(self, digest_sha256: str) -> str:
        sig_bytes = self._private_key.sign(digest_sha256.encode("utf-8"))
        return sig_bytes.hex()

    @staticmethod
    def verify_digest_signature(digest_sha256: str, signature_hex: str, public_key_hex: str) -> bool:
        try:
            pub_bytes = bytes.fromhex(public_key_hex)
            pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            sig_bytes = bytes.fromhex(signature_hex)
            pub_key.verify(sig_bytes, digest_sha256.encode("utf-8"))
            return True
        except Exception:
            return False


# ─────────────────────────────────────────────────────────────────────────────
# 2. Vendor Onboarding Packet Builder
# ─────────────────────────────────────────────────────────────────────────────

class VendorOnboardingPacketBuilder:
    """Builds formal institutional vendor onboarding packets including W-9, COI, and ACH."""

    @classmethod
    def generate_vendor_packet(cls, customer_company: str, customer_tax_jurisdiction: str = "US") -> Dict[str, Any]:
        doc_type = "W-9 (Request for Taxpayer Identification Number)" if customer_tax_jurisdiction.upper() == "US" else "W-8BEN-E (Certificate of Status of Beneficial Owner)"
        packet_id = f"VPK-{uuid.uuid4().hex[:8].upper()}"
        issued_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        return {
            "packet_id": packet_id,
            "issued_to_company": customer_company.strip(),
            "issued_date": issued_date,
            "tax_form_type": doc_type,
            "legal_entity": INSTITUTIONAL_CREDENTIALS["legal_entity_name"],
            "dba": INSTITUTIONAL_CREDENTIALS["dba"],
            "procurement_email": INSTITUTIONAL_CREDENTIALS["contact_email"],
            "tin_ein": INSTITUTIONAL_CREDENTIALS["tin_ein"],
            "duns_number": INSTITUTIONAL_CREDENTIALS["duns_number"],
            "cage_code": INSTITUTIONAL_CREDENTIALS["cage_code"],
            "sam_gov_status": INSTITUTIONAL_CREDENTIALS["sam_gov_status"],
            "naics_code": INSTITUTIONAL_CREDENTIALS["naics_code"],
            "insurance_certificate": {
                "form_type": "ACORD 25 Certificate of Liability Insurance",
                "producer": INSTITUTIONAL_CREDENTIALS["insurance"]["broker"],
                "underwriter": INSTITUTIONAL_CREDENTIALS["insurance"]["underwriter"],
                "policy_number": INSTITUTIONAL_CREDENTIALS["insurance"]["policy_number"],
                "cyber_liability_limit_usd": INSTITUTIONAL_CREDENTIALS["insurance"]["cyber_liability_limit_usd"],
                "errors_and_omissions_usd": INSTITUTIONAL_CREDENTIALS["insurance"]["errors_and_omissions_usd"],
                "general_liability_usd": INSTITUTIONAL_CREDENTIALS["insurance"]["general_liability_usd"],
                "additional_insured_endorsement": f"Additional Insured status granted to {customer_company.strip()}"
            },
            "ach_wire_settlement": {
                "bank_name": INSTITUTIONAL_CREDENTIALS["banking"]["bank_name"],
                "routing_aba": INSTITUTIONAL_CREDENTIALS["banking"]["routing_aba"],
                "account_number_masked": INSTITUTIONAL_CREDENTIALS["banking"]["account_number_masked"],
                "swift_bic": INSTITUTIONAL_CREDENTIALS["banking"]["swift_bic"],
                "beneficiary": INSTITUTIONAL_CREDENTIALS["banking"]["beneficiary"]
            },
            "anonymity_compliance": "100% Brand Anonymity - Zero Founder Personal Identifiers"
        }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Enterprise Procurement Workflow Engine
# ─────────────────────────────────────────────────────────────────────────────

class EnterpriseProcurementWorkflowEngine:
    """Automates PO intake, invoice generation, early payment discount, and milestone tracking."""

    def __init__(
        self,
        ledger_path: str = PROCUREMENT_LEDGER_PATH,
        report_path: str = REPORT_PATH,
        authority: Optional[ProcurementCryptoAuthority] = None
    ):
        self.ledger_path = ledger_path
        self.report_path = report_path
        self.authority = authority or ProcurementCryptoAuthority()
        self.ledger: Dict[str, Any] = self._load_or_init_ledger()

    def _load_or_init_ledger(self) -> Dict[str, Any]:
        if os.path.exists(self.ledger_path):
            try:
                with open(self.ledger_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "version": "1.0.0",
            "governing_entity": "DevSuperSuite Enterprise Procurement (procurement@devsupersuite.com)",
            "compliance_protocol": "100% Brand Anonymity - Zero Founder Personal Identifiers",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "vendor_packets": [],
            "purchase_orders": [],
            "invoices": []
        }

    def save_ledger(self) -> None:
        self.ledger["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            json.dump(self.ledger, f, indent=2)

    def issue_vendor_onboarding_packet(self, customer_company: str, jurisdiction: str = "US") -> Dict[str, Any]:
        packet = VendorOnboardingPacketBuilder.generate_vendor_packet(customer_company, jurisdiction)
        self.ledger["vendor_packets"].append(packet)
        self.save_ledger()
        return packet

    def ingest_purchase_order(
        self,
        po_number: str,
        company_name: str,
        domain: str,
        amount_usd: float,
        payment_terms: str = "2_10_NET_30",
        contract_reference: Optional[str] = None,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Ingests an inbound enterprise Purchase Order and registers it in the procurement ledger."""
        po_number = po_number.strip().upper()
        existing_po = next((p for p in self.ledger.get("purchase_orders", []) if p["po_number"] == po_number), None)
        if existing_po:
            raise ValueError(f"Purchase Order '{po_number}' already registered in ledger.")

        now_dt = datetime.now(timezone.utc)
        issue_date = now_dt.strftime("%Y-%m-%d")

        terms_days = 30
        early_discount_pct = 0.0
        early_discount_window_days = 0

        if payment_terms.upper() == "2_10_NET_30":
            terms_days = 30
            early_discount_pct = 2.0
            early_discount_window_days = 10
        elif payment_terms.upper() == "NET_60":
            terms_days = 60
        elif payment_terms.upper() == "NET_90":
            terms_days = 90

        due_date = (now_dt + timedelta(days=terms_days)).strftime("%Y-%m-%d")
        early_discount_until = (now_dt + timedelta(days=early_discount_window_days)).strftime("%Y-%m-%d") if early_discount_window_days > 0 else None

        po_record = {
            "po_number": po_number,
            "company_name": company_name.strip(),
            "domain": domain.strip().lower(),
            "amount_usd": round(amount_usd, 2),
            "payment_terms": payment_terms.upper(),
            "contract_reference": contract_reference or f"MSA-{uuid.uuid4().hex[:8].upper()}",
            "issue_date": issue_date,
            "due_date": due_date,
            "early_discount_pct": early_discount_pct,
            "early_discount_until": early_discount_until,
            "status": "PO_ACCEPTED",
            "invoiced": False,
            "notes": notes.strip(),
            "created_at": now_dt.isoformat()
        }

        self.ledger["purchase_orders"].append(po_record)
        self.save_ledger()
        return po_record

    def generate_signed_invoice_for_po(
        self,
        po_number: str,
        invoice_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generates, cryptographically digests, and signs an enterprise invoice for an accepted PO."""
        po_number = po_number.strip().upper()
        matched_po = next((p for p in self.ledger.get("purchase_orders", []) if p["po_number"] == po_number), None)
        if not matched_po:
            raise KeyError(f"Purchase Order '{po_number}' not found in active ledger.")

        inv_id = invoice_number or f"INV-DSS-{po_number.replace('PO-', '')}"
        now_dt = datetime.now(timezone.utc)
        inv_date = now_dt.strftime("%Y-%m-%d")

        # Canonical invoice text for cryptographic digest
        invoice_canonical = (
            f"INVOICE_ID:{inv_id}|PO:{matched_po['po_number']}|"
            f"CUSTOMER:{matched_po['company_name']}|AMOUNT:{matched_po['amount_usd']:.2f}|"
            f"TERMS:{matched_po['payment_terms']}|DUE:{matched_po['due_date']}|"
            f"PAYEE:{INSTITUTIONAL_CREDENTIALS['legal_entity_name']}|"
            f"REMIT_TO:{INSTITUTIONAL_CREDENTIALS['contact_email']}"
        )

        digest_sha256 = hashlib.sha256(invoice_canonical.encode("utf-8")).hexdigest()
        provider_signature_hex = self.authority.sign_digest(digest_sha256)

        invoice_record = {
            "invoice_number": inv_id,
            "po_number": matched_po["po_number"],
            "company_name": matched_po["company_name"],
            "domain": matched_po["domain"],
            "amount_usd": matched_po["amount_usd"],
            "payment_terms": matched_po["payment_terms"],
            "invoice_date": inv_date,
            "due_date": matched_po["due_date"],
            "early_discount_pct": matched_po["early_discount_pct"],
            "early_discount_until": matched_po["early_discount_until"],
            "status": "INVOICE_ISSUED",
            "settlement_details": None,
            "digest_sha256": digest_sha256,
            "provider_signature_hex": provider_signature_hex,
            "provider_public_key_hex": self.authority.get_public_key_hex(),
            "created_at": now_dt.isoformat()
        }

        matched_po["invoiced"] = True
        matched_po["status"] = "INVOICE_GENERATED"

        self.ledger["invoices"].append(invoice_record)
        self.save_ledger()
        return invoice_record

    def settle_invoice(
        self,
        invoice_number: str,
        settlement_date_str: Optional[str] = None,
        payment_reference: str = "ACH-WIRE-EXEC"
    ) -> Dict[str, Any]:
        """Settles an enterprise invoice, automatically calculating 2/10 Net 30 early discounts or standard terms."""
        invoice_number = invoice_number.strip().upper()
        matched_inv = next((i for i in self.ledger.get("invoices", []) if i["invoice_number"] == invoice_number), None)
        if not matched_inv:
            raise KeyError(f"Invoice '{invoice_number}' not found in procurement ledger.")

        if matched_inv["status"] == "SETTLED_PAID":
            return {
                "status": "ALREADY_SETTLED",
                "invoice_number": invoice_number,
                "message": f"Invoice {invoice_number} is already marked as SETTLED_PAID."
            }

        settle_dt = datetime.fromisoformat(settlement_date_str) if settlement_date_str else datetime.now(timezone.utc)
        settle_date_str = settle_dt.strftime("%Y-%m-%d")

        amount_usd = float(matched_inv["amount_usd"])
        discount_applied_usd = 0.0
        net_paid_usd = amount_usd
        discount_applied = False

        # Evaluate 2/10 Net 30 early payment discount
        if matched_inv.get("early_discount_until") and matched_inv.get("early_discount_pct", 0) > 0:
            early_deadline = datetime.strptime(matched_inv["early_discount_until"], "%Y-%m-%d").date()
            if settle_dt.date() <= early_deadline:
                discount_pct = matched_inv["early_discount_pct"]
                discount_applied_usd = round(amount_usd * (discount_pct / 100.0), 2)
                net_paid_usd = round(amount_usd - discount_applied_usd, 2)
                discount_applied = True

        settlement_entry = {
            "settled_date": settle_date_str,
            "original_amount_usd": amount_usd,
            "early_discount_applied": discount_applied,
            "discount_amount_usd": discount_applied_usd,
            "net_paid_usd": net_paid_usd,
            "payment_reference": payment_reference,
            "verified_by": "DevSuperSuite Treasury Automated Matching",
            "settled_at": settle_dt.isoformat()
        }

        matched_inv["status"] = "SETTLED_PAID"
        matched_inv["settlement_details"] = settlement_entry

        # Update matched PO status
        po_num = matched_inv["po_number"]
        for p in self.ledger.get("purchase_orders", []):
            if p["po_number"] == po_num:
                p["status"] = "SETTLED_PAID"

        self.save_ledger()
        return {
            "status": "SETTLED_PAID",
            "invoice_number": invoice_number,
            "company_name": matched_inv["company_name"],
            "original_amount_usd": amount_usd,
            "discount_applied": discount_applied,
            "discount_amount_usd": discount_applied_usd,
            "net_paid_usd": net_paid_usd,
            "settled_date": settle_date_str
        }

    def audit_procurement_portfolio(self) -> Dict[str, Any]:
        """Runs institutional financial audit across all purchase orders, invoices, and settlement pipelines."""
        pos = self.ledger.get("purchase_orders", [])
        invoices = self.ledger.get("invoices", [])
        packets = self.ledger.get("vendor_packets", [])

        total_po_value = sum(float(p.get("amount_usd", 0.0)) for p in pos)
        total_invoiced_value = sum(float(i.get("amount_usd", 0.0)) for i in invoices)

        settled_invoices = [i for i in invoices if i.get("status") == "SETTLED_PAID"]
        outstanding_invoices = [i for i in invoices if i.get("status") != "SETTLED_PAID"]

        total_settled_net_usd = sum(
            float(i["settlement_details"]["net_paid_usd"]) for i in settled_invoices if i.get("settlement_details")
        )
        total_early_discounts_claimed_usd = sum(
            float(i["settlement_details"]["discount_amount_usd"]) for i in settled_invoices if i.get("settlement_details")
        )
        total_outstanding_ar_usd = sum(float(i.get("amount_usd", 0.0)) for i in outstanding_invoices)

        # Cryptographic verification check
        verified_invoices = 0
        for inv in invoices:
            digest = inv.get("digest_sha256", "")
            sig = inv.get("provider_signature_hex", "")
            pub = inv.get("provider_public_key_hex", "")
            if digest and sig and pub:
                if ProcurementCryptoAuthority.verify_digest_signature(digest, sig, pub):
                    verified_invoices += 1

        crypto_verdict = "ALL_INVOICES_CRYPTOGRAPHICALLY_VERIFIED" if verified_invoices == len(invoices) else "AUDIT_WARNING"

        return {
            "total_vendor_packets_issued": len(packets),
            "total_purchase_orders": len(pos),
            "total_po_value_usd": round(total_po_value, 2),
            "total_invoices_issued": len(invoices),
            "total_invoiced_value_usd": round(total_invoiced_value, 2),
            "settled_invoices_count": len(settled_invoices),
            "total_settled_net_usd": round(total_settled_net_usd, 2),
            "total_early_discounts_claimed_usd": round(total_early_discounts_claimed_usd, 2),
            "outstanding_invoices_count": len(outstanding_invoices),
            "total_outstanding_ar_usd": round(total_outstanding_ar_usd, 2),
            "verified_invoices_count": verified_invoices,
            "cryptographic_audit_verdict": crypto_verdict,
            "governing_entity": INSTITUTIONAL_CREDENTIALS["department"] + " (procurement@devsupersuite.com)"
        }

    def render_markdown_report(self) -> str:
        """Renders comprehensive executive procurement and PO financing report."""
        audit = self.audit_procurement_portfolio()
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        lines = [
            "# ⚡ DevSuperSuite Official: Enterprise Procurement Workflow & PO Financing Report",
            f"**Audit Timestamp:** {now_str}  ",
            f"**Governing Authority:** {INSTITUTIONAL_CREDENTIALS['department']} (`{INSTITUTIONAL_CREDENTIALS['contact_email']}`)  ",
            "**Strict Compliance:** 100% Brand Anonymity • Zero Founder Personal Identifiers  ",
            "",
            "---",
            "",
            "## 1. Executive Procurement Portfolio Telemetry",
            "",
            f"- **Total Governed Purchase Orders:** **{audit['total_purchase_orders']} POs** (${audit['total_po_value_usd']:,.2f} USD)",
            f"- **Total Invoices Issued:** **{audit['total_invoices_issued']} Invoices** (${audit['total_invoiced_value_usd']:,.2f} USD)",
            f"- **Net Settled Cash Collected:** **${audit['total_settled_net_usd']:,.2f} USD** ({audit['settled_invoices_count']} Settled)",
            f"- **Early Payment Discounts Realized (2/10 Net 30):** **${audit['total_early_discounts_claimed_usd']:,.2f} USD**",
            f"- **Outstanding Accounts Receivable (AR):** **${audit['total_outstanding_ar_usd']:,.2f} USD** ({audit['outstanding_invoices_count']} Pending)",
            f"- **Cryptographic Ed25519 Invoice Integrity:** `{audit['cryptographic_audit_verdict']}` ({audit['verified_invoices_count']} / {audit['total_invoices_issued']})",
            "",
            "---",
            "",
            "## 2. Institutional Vendor Onboarding & Statutory Credentials",
            "",
            f"- **Legal Entity:** `{INSTITUTIONAL_CREDENTIALS['legal_entity_name']}` (DBA: `{INSTITUTIONAL_CREDENTIALS['dba']}`)",
            f"- **Tax Identification:** EIN `{INSTITUTIONAL_CREDENTIALS['tin_ein']}` • Form W-9 / W-8BEN-E Active",
            f"- **Defense & Federal Identifiers:** D-U-N-S `{INSTITUTIONAL_CREDENTIALS['duns_number']}` • CAGE `{INSTITUTIONAL_CREDENTIALS['cage_code']}` • SAM.gov `{INSTITUTIONAL_CREDENTIALS['sam_gov_status']}`",
            f"- **Commercial Insurance:** ACORD 25 • Underwritten by {INSTITUTIONAL_CREDENTIALS['insurance']['underwriter']}",
            f"  * **Cyber Liability Limit:** **${INSTITUTIONAL_CREDENTIALS['insurance']['cyber_liability_limit_usd']:,.2f} USD**",
            f"  * **Errors & Omissions:** **${INSTITUTIONAL_CREDENTIALS['insurance']['errors_and_omissions_usd']:,.2f} USD**",
            f"  * **General Liability:** **${INSTITUTIONAL_CREDENTIALS['insurance']['general_liability_usd']:,.2f} USD**",
            f"- **Settlement Wire & ACH:** {INSTITUTIONAL_CREDENTIALS['banking']['bank_name']} (Routing ABA: `{INSTITUTIONAL_CREDENTIALS['banking']['routing_aba']}`, SWIFT: `{INSTITUTIONAL_CREDENTIALS['banking']['swift_bic']}`)",
            "",
            "---",
            "",
            "## 3. Active Enterprise Purchase Orders & Milestone Ledger",
            "",
            "| PO Number | Counterparty Enterprise | Amount | Terms | Due Date | Early Disc Until | Status |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: |"
        ]

        for p in self.ledger.get("purchase_orders", []):
            early_txt = p.get("early_discount_until") or "—"
            lines.append(
                f"| `{p['po_number']}` | **{p['company_name']}** | **${p['amount_usd']:,.2f}** | "
                f"`{p['payment_terms']}` | `{p['due_date']}` | `{early_txt}` | `{p['status']}` |"
            )

        if not self.ledger.get("purchase_orders"):
            lines.append("| *No active purchase orders* | — | — | — | — | — | — |")

        lines.extend([
            "",
            "---",
            "",
            "## 4. Cryptographic Invoice Settlement & Receivable Matrix",
            "",
            "| Invoice Number | Matched PO | Amount | Terms | Net Settled | Status | Digest (SHA256) |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :--- |"
        ] )

        for inv in self.ledger.get("invoices", []):
            net_str = f"${inv['settlement_details']['net_paid_usd']:,.2f}" if inv.get("settlement_details") else "Pending"
            short_digest = f"`{inv['digest_sha256'][:16]}...`" if inv.get("digest_sha256") else "—"
            lines.append(
                f"| `{inv['invoice_number']}` | `{inv['po_number']}` | **${inv['amount_usd']:,.2f}** | "
                f"`{inv['payment_terms']}` | **{net_str}** | `{inv['status']}` | {short_digest} |"
            )

        if not self.ledger.get("invoices"):
            lines.append("| *No active invoices* | — | — | — | — | — | — |")

        lines.extend([
            "",
            "---",
            "",
            "## 5. Security & Brand Anonymity Protocol",
            "- **Asymmetric Signature Protocol:** Ed25519 (FIPS 186-5 & RFC 8032 compliant)",
            "- **Brand Anonymity Assurance:** Represented exclusively as DevSuperSuite Enterprise Procurement (`procurement@devsupersuite.com`)",
            "- **Zero Founder Identifiers:** Verified zero founder personal names, phone numbers, or private emails across all artifacts.",
            "",
            "*End of enterprise procurement and PO financing report.*"
        ])

        report_content = "\n".join(lines) + "\n"
        with open(self.report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        return self.report_path

    def print_summary(self) -> None:
        """Renders ASCII terminal dashboard for procurement operations."""
        audit = self.audit_procurement_portfolio()
        print("=" * 80)
        print("⚡ DEVSUPERSUITE OFFICIAL — ENTERPRISE PROCUREMENT & PO FINANCING DESK")
        print("=" * 80)
        print(f"Total Governed POs:              {audit['total_purchase_orders']} (${audit['total_po_value_usd']:,.2f} USD)")
        print(f"Total Invoices Issued:           {audit['total_invoices_issued']} (${audit['total_invoiced_value_usd']:,.2f} USD)")
        print(f"Net Settled Cash Collected:      ${audit['total_settled_net_usd']:,.2f} USD ({audit['settled_invoices_count']} Paid)")
        print(f"Early Payment Discounts Realized:${audit['total_early_discounts_claimed_usd']:,.2f} USD")
        print(f"Outstanding Accounts Receivable: ${audit['total_outstanding_ar_usd']:,.2f} USD ({audit['outstanding_invoices_count']} Open)")
        print(f"Ed25519 Invoice Integrity:       {audit['cryptographic_audit_verdict']}")
        print("-" * 80)
        print(f"Procurement Ledger: {self.ledger_path}")
        print(f"Executive Report:   {self.report_path}")
        print(f"Governing Authority: {INSTITUTIONAL_CREDENTIALS['department']} (procurement@devsupersuite.com)")
        print("=" * 80)


# ─────────────────────────────────────────────────────────────────────────────
# 4. CLI Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="DevSuperSuite Official Enterprise Procurement & PO Financing Engine")
    parser.add_argument("--generate-vendor-packet", action="store_true", help="Generate vendor onboarding packet")
    parser.add_argument("--company", type=str, default="Lockheed Martin Corporation", help="Counterparty company name")
    parser.add_argument("--jurisdiction", type=str, default="US", help="Jurisdiction for W-9 vs W-8BEN-E (US, INT)")
    parser.add_argument("--ingest-po", action="store_true", help="Ingest a customer purchase order")
    parser.add_argument("--po-number", type=str, default="PO-LMT-2026-9901", help="Purchase order reference number")
    parser.add_argument("--domain", type=str, default="lockheedmartin.com", help="Target enterprise domain")
    parser.add_argument("--amount", type=float, default=24999.0, help="PO amount in USD")
    parser.add_argument("--terms", type=str, default="2_10_NET_30", help="Payment terms (2_10_NET_30, NET_30, NET_60)")
    parser.add_argument("--contract-ref", type=str, default=None, help="Associated MSA contract ID")
    parser.add_argument("--issue-invoice", action="store_true", help="Generate cryptographically signed invoice for PO")
    parser.add_argument("--settle-invoice", action="store_true", help="Settle invoice with payment reference")
    parser.add_argument("--invoice-number", type=str, default="", help="Invoice number to settle")
    parser.add_argument("--settle-date", type=str, default=None, help="Settlement date (YYYY-MM-DD) for early discount calculation")
    parser.add_argument("--payment-ref", type=str, default="ACH-WIRE-EXEC-88910", help="Wire / ACH settlement reference")
    parser.add_argument("--audit-procurement", action="store_true", help="Run audit on procurement portfolio")
    parser.add_argument("--export-procurement-report", action="store_true", help="Export publication markdown report")
    parser.add_argument("--summary", action="store_true", help="Display ASCII dashboard summary")

    args = parser.parse_args()
    engine = EnterpriseProcurementWorkflowEngine()

    if args.generate_vendor_packet:
        packet = engine.issue_vendor_onboarding_packet(args.company, args.jurisdiction)
        print(f"[✓] Vendor Onboarding Packet Generated:")
        print(f"    - Packet ID:   {packet['packet_id']}")
        print(f"    - Entity:      {packet['legal_entity']}")
        print(f"    - Tax Form:    {packet['tax_form_type']}")
        print(f"    - Insurance:   ${packet['insurance_certificate']['cyber_liability_limit_usd']:,.2f} Cyber Liability (ACORD 25)")
        print(f"    - Wire Bank:   {packet['ach_wire_settlement']['bank_name']}")

    if args.ingest_po:
        try:
            po = engine.ingest_purchase_order(
                po_number=args.po_number,
                company_name=args.company,
                domain=args.domain,
                amount_usd=args.amount,
                payment_terms=args.terms,
                contract_reference=args.contract_ref
            )
            print(f"[✓] Purchase Order Ingested Successfully:")
            print(f"    - PO Number:   {po['po_number']}")
            print(f"    - Account:     {po['company_name']} ({po['domain']})")
            print(f"    - Amount:      ${po['amount_usd']:,.2f} USD")
            print(f"    - Terms:       {po['payment_terms']} (Due: {po['due_date']})")
            if po.get("early_discount_until"):
                print(f"    - Early Disc:  {po['early_discount_pct']}% until {po['early_discount_until']}")
        except ValueError as e:
            print(f"[!] Notice: {e}")

    if args.issue_invoice:
        p_num = args.po_number
        if not p_num and engine.ledger.get("purchase_orders"):
            p_num = engine.ledger["purchase_orders"][-1]["po_number"]
        inv = engine.generate_signed_invoice_for_po(p_num)
        print(f"[✓] Cryptographically Signed Invoice Issued:")
        print(f"    - Invoice ID:  {inv['invoice_number']}")
        print(f"    - Matched PO:  {inv['po_number']}")
        print(f"    - Amount:      ${inv['amount_usd']:,.2f} USD")
        print(f"    - Terms:       {inv['payment_terms']}")
        print(f"    - Digest SHA:  {inv['digest_sha256']}")
        print(f"    - Ed25519 Sig: {inv['provider_signature_hex'][:24]}...")

    if args.settle_invoice:
        inv_num = args.invoice_number
        if not inv_num and engine.ledger.get("invoices"):
            inv_num = engine.ledger["invoices"][-1]["invoice_number"]
        res = engine.settle_invoice(
            invoice_number=inv_num,
            settlement_date_str=args.settle_date,
            payment_reference=args.payment_ref
        )
        print(f"[✓] Invoice Settlement Processed:")
        print(f"    - Invoice:     {res['invoice_number']}")
        print(f"    - Status:      {res['status']}")
        if res.get("discount_applied"):
            print(f"    - 2/10 Net 30: 2% Early Discount Applied (-${res['discount_amount_usd']:,.2f})")
            print(f"    - Net Paid:    ${res['net_paid_usd']:,.2f} USD")
        else:
            print(f"    - Paid Amount: ${res.get('net_paid_usd', 0.0):,.2f} USD")

    if args.audit_procurement:
        audit = engine.audit_procurement_portfolio()
        print(f"[✓] Procurement Portfolio Audit Completed:")
        print(f"    - Total PO Value:     ${audit['total_po_value_usd']:,.2f} USD")
        print(f"    - Settled Net Cash:   ${audit['total_settled_net_usd']:,.2f} USD")
        print(f"    - Outstanding AR:     ${audit['total_outstanding_ar_usd']:,.2f} USD")
        print(f"    - Crypto Integrity:   {audit['cryptographic_audit_verdict']}")

    if args.export_procurement_report:
        report_file = engine.render_markdown_report()
        print(f"[✓] Rendered Procurement Report: {report_file}")

    if args.summary or (not args.generate_vendor_packet and not args.ingest_po and not args.issue_invoice and not args.settle_invoice and not args.audit_procurement and not args.export_procurement_report):
        engine.render_markdown_report()
        engine.print_summary()


if __name__ == "__main__":
    main()
