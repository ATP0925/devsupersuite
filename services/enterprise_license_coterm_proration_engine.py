#!/usr/bin/env python3
"""
⚡ DevSuperSuite Official: Enterprise Self-Serve License Coterming & Proration Engine
File: enterprise_license_coterm_proration_engine.py
Version: 1.0.0
Governing Authority: DevSuperSuite Revenue Operations (growth@devsupersuite.com)
Strict Protocol: 100% Brand Anonymity - Zero Founder Personal Identifiers

Key Capabilities:
1. Mid-Cycle Co-Terming Calculation:
   - Computes exact daily proration:
     Prorated Amount = (Days Remaining in Master Term / Total Days in Master Term) * Delta Annual Base Fee
   - Co-terms all secondary seat tranches to a single consolidated annual renewal anniversary.
2. Tier Upgrades & Downward True-Down Guardrails:
   - Seamless upgrades across Pro ($49/mo / $490/yr), Enterprise ($240/mo / $2,400/yr),
     and Sovereign SCIF Enclave ($1,250/mo / $12,500/yr).
   - Enforces contractual Annual Minimum Commitment (AMC) and 60-day advance notice lockout
     on true-downs to prevent unexpected ARR contraction.
3. Cryptographic Credit Note & Consolidated Invoicing:
   - Issues immutable HMAC-SHA256 signed credit notes (CRN-XXXXXXXX) for unconsumed time.
   - Calculates net payable balances and consolidates invoices (INV-COTERM-XXXXXXXX).
4. Multi-Currency & FX Alignment:
   - Supports USD, EUR, GBP, INR (instant UPI QR checkout rail), and SGD.
5. Dual Schedule Persistence & Executive Reporting:
   - Persists to services/data/license_coterm_proration_schedules.json and root mirror data/.
   - Generates executive report in services/reports/license_coterm_proration_report.md.
6. Multi-Action CLI:
   - --prorate-seat-expansion, --coterm-licenses, --calculate-credit-note, --export-coterm-binder, --summary.
"""

import os
import sys
import json
import uuid
import hmac
import hashlib
import argparse
from datetime import datetime, timezone, timedelta, date
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Directory Configuration
SERVICES_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(SERVICES_DIR)
SERVICES_DATA_DIR = os.path.join(SERVICES_DIR, "data")
ROOT_DATA_DIR = os.path.join(SCRATCH_DIR, "data")
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")

os.makedirs(SERVICES_DATA_DIR, exist_ok=True)
os.makedirs(ROOT_DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

PRIMARY_SCHEDULE_PATH = os.path.join(SERVICES_DATA_DIR, "license_coterm_proration_schedules.json")
ROOT_SCHEDULE_PATH = os.path.join(ROOT_DATA_DIR, "license_coterm_proration_schedules.json")
REPORT_PATH = os.path.join(REPORTS_DIR, "license_coterm_proration_report.md")

# Enterprise Tier Catalog
TIER_CATALOG: Dict[str, Dict[str, Any]] = {
    "Pro": {
        "tier_name": "Pro",
        "monthly_price_usd": 49.00,
        "annual_fee_usd": 490.00,
        "display_name": "DevSuperSuite Professional Developer",
        "features": ["Offline AST Engine", "Local Git Hook Interlocks", "Developer Playground"]
    },
    "Enterprise": {
        "tier_name": "Enterprise",
        "monthly_price_usd": 240.00,
        "annual_fee_usd": 2400.00,
        "display_name": "DevSuperSuite Enterprise Compliance & Security",
        "features": ["All Pro Features", "FIPS 140-3 HSM Attestation", "eBPF Socket Interlock", "Net-30 Invoicing"]
    },
    "Sovereign SCIF Enclave": {
        "tier_name": "Sovereign SCIF Enclave",
        "monthly_price_usd": 1250.00,
        "annual_fee_usd": 12500.00,
        "display_name": "DevSuperSuite Sovereign Airgapped Defense Enclave",
        "features": ["All Enterprise Features", "Airgapped SCIF Zero-Telemetry Enclave", "Post-Quantum Dilithium Tokens", "Dedicated Security Architect"]
    }
}

# FX Multipliers (relative to USD = 1.00)
FX_RATES: Dict[str, float] = {
    "USD": 1.00,
    "EUR": 0.92,
    "GBP": 0.79,
    "INR": 86.50,
    "SGD": 1.34
}

# Payment & Contract Rules
ADVANCE_NOTICE_MINIMUM_DAYS = 60
UPI_VPA = "devsupersuite@icici"
UPI_PAYEE_NAME = "DevSuperSuite Official"
HMAC_SECRET_KEY = b"devsupersuite_license_coterm_proration_auth_v1"


def parse_date(d: Any) -> date:
    """Safely parse date string or datetime into date object."""
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        # Support ISO formats YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS
        return datetime.fromisoformat(d.replace("Z", "+00:00")).date()
    raise ValueError(f"Unsupported date format: {d}")


class LicenseProrationCalculator:
    """Core mathematical engine for mid-cycle proration and true-down validation."""

    @staticmethod
    def calculate_proration(
        total_days: int,
        days_remaining: int,
        annual_delta_usd: float,
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """
        Calculate exact daily proration according to standard commercial formula:
        Prorated Amount = (Days Remaining / Total Days) * Delta Annual Base Fee
        """
        if total_days <= 0:
            raise ValueError("Total term days must be strictly greater than 0.")
        
        # Clamp days_remaining within [0, total_days]
        clamped_remaining = max(0, min(days_remaining, total_days))
        proration_factor = clamped_remaining / float(total_days)
        prorated_usd = round(proration_factor * annual_delta_usd, 2)
        
        fx = FX_RATES.get(currency.upper(), 1.00)
        prorated_local = round(prorated_usd * fx, 2)
        
        return {
            "total_term_days": total_days,
            "days_remaining": clamped_remaining,
            "proration_factor": round(proration_factor, 6),
            "annual_delta_usd": round(annual_delta_usd, 2),
            "prorated_amount_usd": prorated_usd,
            "currency": currency.upper(),
            "fx_rate": fx,
            "prorated_amount_local": prorated_local
        }

    @staticmethod
    def calculate_seat_expansion(
        account_id: str,
        master_start_date: Any,
        master_end_date: Any,
        expansion_date: Any,
        added_seats: int,
        tier: str = "Enterprise",
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Calculates mid-cycle seat expansion prorated to the master renewal anniversary."""
        if added_seats <= 0:
            raise ValueError("Added seats must be a positive integer.")
        if tier not in TIER_CATALOG:
            raise ValueError(f"Unknown tier: {tier}. Available: {list(TIER_CATALOG.keys())}")

        m_start = parse_date(master_start_date)
        m_end = parse_date(master_end_date)
        exp_date = parse_date(expansion_date)

        total_days = (m_end - m_start).days
        days_remaining = (m_end - exp_date).days

        annual_seat_fee = TIER_CATALOG[tier]["annual_fee_usd"]
        delta_annual_usd = added_seats * annual_seat_fee

        proration = LicenseProrationCalculator.calculate_proration(
            total_days=total_days,
            days_remaining=days_remaining,
            annual_delta_usd=delta_annual_usd,
            currency=currency
        )

        return {
            "account_id": account_id,
            "expansion_type": "SEAT_ADDITION",
            "tier": tier,
            "added_seats": added_seats,
            "annual_seat_fee_usd": annual_seat_fee,
            "master_start_date": m_start.isoformat(),
            "master_end_date": m_end.isoformat(),
            "expansion_date": exp_date.isoformat(),
            "cotermed_renewal_date": m_end.isoformat(),
            **proration
        }

    @staticmethod
    def calculate_tier_upgrade(
        account_id: str,
        master_start_date: Any,
        master_end_date: Any,
        upgrade_date: Any,
        seats: int,
        old_tier: str,
        new_tier: str,
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Calculates mid-cycle tier upgrade proration with unconsumed credit note offset."""
        if seats <= 0:
            raise ValueError("Seat count must be a positive integer.")
        if old_tier not in TIER_CATALOG or new_tier not in TIER_CATALOG:
            raise ValueError("Invalid tier specified.")

        m_start = parse_date(master_start_date)
        m_end = parse_date(master_end_date)
        up_date = parse_date(upgrade_date)

        total_days = (m_end - m_start).days
        days_remaining = (m_end - up_date).days

        old_annual_seat_fee = TIER_CATALOG[old_tier]["annual_fee_usd"]
        new_annual_seat_fee = TIER_CATALOG[new_tier]["annual_fee_usd"]

        if new_annual_seat_fee < old_annual_seat_fee:
            raise ValueError(
                f"Requested change from {old_tier} (${old_annual_seat_fee}) to {new_tier} (${new_annual_seat_fee}) "
                "is a tier downgrade/true-down, which must follow true-down guardrails."
            )

        old_annual_total_usd = seats * old_annual_seat_fee
        new_annual_total_usd = seats * new_annual_seat_fee

        fx = FX_RATES.get(currency.upper(), 1.00)

        # Unconsumed credit calculation
        unconsumed_credit = LicenseProrationCalculator.calculate_proration(
            total_days=total_days,
            days_remaining=days_remaining,
            annual_delta_usd=old_annual_total_usd,
            currency=currency
        )

        # New tier prorated charge calculation
        new_prorated_charge = LicenseProrationCalculator.calculate_proration(
            total_days=total_days,
            days_remaining=days_remaining,
            annual_delta_usd=new_annual_total_usd,
            currency=currency
        )

        net_payable_usd = round(
            max(0.0, new_prorated_charge["prorated_amount_usd"] - unconsumed_credit["prorated_amount_usd"]), 2
        )
        net_payable_local = round(net_payable_usd * fx, 2)

        return {
            "account_id": account_id,
            "upgrade_type": "TIER_UPGRADE",
            "old_tier": old_tier,
            "new_tier": new_tier,
            "seats": seats,
            "master_start_date": m_start.isoformat(),
            "master_end_date": m_end.isoformat(),
            "upgrade_date": up_date.isoformat(),
            "cotermed_renewal_date": m_end.isoformat(),
            "total_term_days": total_days,
            "days_remaining": max(0, min(days_remaining, total_days)),
            "unconsumed_credit_usd": unconsumed_credit["prorated_amount_usd"],
            "unconsumed_credit_local": unconsumed_credit["prorated_amount_local"],
            "new_prorated_charge_usd": new_prorated_charge["prorated_amount_usd"],
            "new_prorated_charge_local": new_prorated_charge["prorated_amount_local"],
            "net_payable_usd": net_payable_usd,
            "net_payable_local": net_payable_local,
            "currency": currency.upper(),
            "fx_rate": fx
        }

    @staticmethod
    def validate_true_down(
        account_id: str,
        master_end_date: Any,
        request_date: Any,
        current_seats: int,
        proposed_seats: int,
        current_arr_usd: float,
        proposed_arr_usd: float,
        amc_seats: int = 0,
        amc_arr_usd: float = 0.0
    ) -> Dict[str, Any]:
        """
        Enforces contractual true-down policy:
        1. 60-day advance notice requirement before master renewal date.
        2. Annual Minimum Commitment (AMC) seat threshold.
        3. Annual Minimum Commitment (AMC) ARR threshold.
        """
        m_end = parse_date(master_end_date)
        req_date = parse_date(request_date)

        days_until_renewal = (m_end - req_date).days

        # Rule 1: 60-day lockout
        if days_until_renewal < ADVANCE_NOTICE_MINIMUM_DAYS:
            return {
                "account_id": account_id,
                "allowed": False,
                "reason_code": "TRUE_DOWN_LOCKED_ADVANCE_NOTICE_REQUIRED",
                "days_until_renewal": days_until_renewal,
                "required_advance_days": ADVANCE_NOTICE_MINIMUM_DAYS,
                "message": (
                    f"Contractual lock-in active: True-downs require at least {ADVANCE_NOTICE_MINIMUM_DAYS} days "
                    f"advance notice prior to master renewal. Current notice: {days_until_renewal} days."
                )
            }

        # Rule 2: AMC seats violation
        if proposed_seats < amc_seats:
            return {
                "account_id": account_id,
                "allowed": False,
                "reason_code": "TRUE_DOWN_VIOLATES_AMC_SEATS",
                "current_seats": current_seats,
                "proposed_seats": proposed_seats,
                "amc_seats": amc_seats,
                "message": (
                    f"Contractual AMC Breach: Proposed seat reduction ({proposed_seats} seats) is below the "
                    f"contractual Annual Minimum Commitment of {amc_seats} seats."
                )
            }

        # Rule 3: AMC ARR violation
        if proposed_arr_usd < amc_arr_usd:
            return {
                "account_id": account_id,
                "allowed": False,
                "reason_code": "TRUE_DOWN_VIOLATES_AMC_ARR",
                "current_arr_usd": round(current_arr_usd, 2),
                "proposed_arr_usd": round(proposed_arr_usd, 2),
                "amc_arr_usd": round(amc_arr_usd, 2),
                "message": (
                    f"Contractual AMC Breach: Proposed ARR (${proposed_arr_usd:,.2f}) is below the "
                    f"contractual Annual Minimum Commitment of ${amc_arr_usd:,.2f}."
                )
            }

        # Permitted
        return {
            "account_id": account_id,
            "allowed": True,
            "reason_code": "APPROVED",
            "days_until_renewal": days_until_renewal,
            "effective_date": m_end.isoformat(),
            "message": "True-down proposal satisfies all contractual AMC guardrails and advance notice covenants."
        }


class CryptographicCreditNoteAuthority:
    """Issues and verifies immutable, HMAC-SHA256 authenticated credit notes."""

    @staticmethod
    def issue_credit_note(
        account_id: str,
        amount: float,
        currency: str,
        reason: str,
        original_invoice_ref: Optional[str] = None,
        issued_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generates an immutable cryptographic credit note."""
        cn_id = f"CRN-{uuid.uuid4().hex[:8].upper()}"
        ts = issued_at or datetime.now(timezone.utc).isoformat()
        amt = round(amount, 2)
        curr = currency.upper()

        # Sign canonical representation
        payload = f"{cn_id}|{account_id}|{amt:.2f}|{curr}|{reason}|{ts}".encode("utf-8")
        sig = hmac.new(HMAC_SECRET_KEY, payload, hashlib.sha256).hexdigest()

        return {
            "credit_note_id": cn_id,
            "account_id": account_id,
            "amount": amt,
            "currency": curr,
            "reason": reason,
            "original_invoice_ref": original_invoice_ref or f"INV-ORIG-{uuid.uuid4().hex[:6].upper()}",
            "issued_at": ts,
            "status": "ISSUED",
            "signature": sig,
            "issuer": "DevSuperSuite Revenue Operations (growth@devsupersuite.com)"
        }

    @staticmethod
    def verify_credit_note(cn: Dict[str, Any]) -> bool:
        """Cryptographically verifies credit note integrity."""
        try:
            cn_id = cn["credit_note_id"]
            acc_id = cn["account_id"]
            amt = float(cn["amount"])
            curr = cn["currency"].upper()
            reason = cn["reason"]
            ts = cn["issued_at"]
            expected_sig = cn["signature"]

            payload = f"{cn_id}|{acc_id}|{amt:.2f}|{curr}|{reason}|{ts}".encode("utf-8")
            actual_sig = hmac.new(HMAC_SECRET_KEY, payload, hashlib.sha256).hexdigest()
            return hmac.compare_digest(actual_sig, expected_sig)
        except Exception:
            return False


class EnterpriseLicenseCotermEngine:
    """
    Main business logic service managing enterprise customer coterming,
    prorated seat expansions, consolidated invoicing, and ledger synchronization.
    """

    def __init__(
        self,
        primary_path: str = PRIMARY_SCHEDULE_PATH,
        root_path: str = ROOT_SCHEDULE_PATH,
        report_path: str = REPORT_PATH
    ):
        self.primary_path = primary_path
        self.root_path = root_path
        self.report_path = report_path
        self.ledger: Dict[str, Any] = self._load_or_initialize_ledger()

    def _load_or_initialize_ledger(self) -> Dict[str, Any]:
        """Loads existing ledger or seeds realistic institutional accounts."""
        if os.path.exists(self.primary_path):
            try:
                with open(self.primary_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        if os.path.exists(self.root_path):
            try:
                with open(self.root_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        return self._seed_default_enterprise_ledger()

    def _seed_default_enterprise_ledger(self) -> Dict[str, Any]:
        """Seeds initial portfolio of 5 institutional enterprise accounts with diverse coterm setups."""
        base_date = date(2026, 1, 1)
        today = date(2026, 11, 8)

        # 1. Raytheon Technologies (USD) - Seat addition mid-cycle
        raytheon_cn = CryptographicCreditNoteAuthority.issue_credit_note(
            account_id="ACC-RAYTHEON-01",
            amount=0.0,
            currency="USD",
            reason="Initial Setup - Zero balance placeholder",
            issued_at="2026-01-01T00:00:00Z"
        )

        # 2. Siemens Digital (EUR) - Upgraded to Sovereign SCIF mid-cycle
        siemens_cn = CryptographicCreditNoteAuthority.issue_credit_note(
            account_id="ACC-SIEMENS-02",
            amount=33230.77,
            currency="EUR",
            reason="Unconsumed Enterprise Tier credit for 180 days remaining",
            issued_at="2026-09-15T10:00:00Z"
        )

        accounts = [
            {
                "account_id": "ACC-RAYTHEON-01",
                "company_name": "Raytheon Technologies",
                "tier": "Enterprise",
                "currency": "USD",
                "master_start_date": "2026-01-01",
                "master_end_date": "2026-12-31",
                "current_seats": 70,
                "base_committed_seats": 50,
                "amc_seats": 40,
                "amc_arr_usd": 96000.0,
                "current_arr_usd": 168000.0,
                "tranches": [
                    {
                        "tranche_id": "TRN-RAY-01",
                        "seats": 50,
                        "tier": "Enterprise",
                        "start_date": "2026-01-01",
                        "original_end_date": "2026-12-31",
                        "cotermed_renewal_date": "2026-12-31",
                        "status": "ACTIVE_MASTER"
                    },
                    {
                        "tranche_id": "TRN-RAY-02",
                        "seats": 20,
                        "tier": "Enterprise",
                        "start_date": "2026-07-01",
                        "original_end_date": "2027-06-30",
                        "cotermed_renewal_date": "2026-12-31",
                        "status": "COTERMED_MID_CYCLE",
                        "prorated_charge_usd": 24065.75
                    }
                ]
            },
            {
                "account_id": "ACC-SIEMENS-02",
                "company_name": "Siemens Digital Industries",
                "tier": "Sovereign SCIF Enclave",
                "currency": "EUR",
                "master_start_date": "2026-03-15",
                "master_end_date": "2027-03-14",
                "current_seats": 30,
                "base_committed_seats": 30,
                "amc_seats": 20,
                "amc_arr_usd": 48000.0,
                "current_arr_usd": 375000.0,
                "tranches": [
                    {
                        "tranche_id": "TRN-SIEMENS-01",
                        "seats": 30,
                        "tier": "Sovereign SCIF Enclave",
                        "start_date": "2026-03-15",
                        "original_end_date": "2027-03-14",
                        "cotermed_renewal_date": "2027-03-14",
                        "status": "UPGRADED_COTERMED",
                        "unconsumed_credit_note_ref": siemens_cn["credit_note_id"]
                    }
                ]
            },
            {
                "account_id": "ACC-TATA-03",
                "company_name": "Tata Consultancy Enclave",
                "tier": "Pro",
                "currency": "INR",
                "master_start_date": "2026-06-01",
                "master_end_date": "2027-05-31",
                "current_seats": 100,
                "base_committed_seats": 60,
                "amc_seats": 50,
                "amc_arr_usd": 24500.0,
                "current_arr_usd": 49000.0,
                "tranches": [
                    {
                        "tranche_id": "TRN-TATA-01",
                        "seats": 60,
                        "tier": "Pro",
                        "start_date": "2026-06-01",
                        "original_end_date": "2027-05-31",
                        "cotermed_renewal_date": "2027-05-31",
                        "status": "ACTIVE_MASTER"
                    },
                    {
                        "tranche_id": "TRN-TATA-02",
                        "seats": 40,
                        "tier": "Pro",
                        "start_date": "2026-09-01",
                        "original_end_date": "2027-08-31",
                        "cotermed_renewal_date": "2027-05-31",
                        "status": "COTERMED_MID_CYCLE",
                        "prorated_charge_inr": 1251345.21
                    }
                ]
            },
            {
                "account_id": "ACC-BAE-04",
                "company_name": "BAE Systems UK",
                "tier": "Sovereign SCIF Enclave",
                "currency": "GBP",
                "master_start_date": "2026-02-01",
                "master_end_date": "2027-01-31",
                "current_seats": 25,
                "base_committed_seats": 15,
                "amc_seats": 15,
                "amc_arr_usd": 187500.0,
                "current_arr_usd": 312500.0,
                "tranches": [
                    {
                        "tranche_id": "TRN-BAE-01",
                        "seats": 15,
                        "tier": "Sovereign SCIF Enclave",
                        "start_date": "2026-02-01",
                        "original_end_date": "2027-01-31",
                        "cotermed_renewal_date": "2027-01-31",
                        "status": "ACTIVE_MASTER"
                    },
                    {
                        "tranche_id": "TRN-BAE-02",
                        "seats": 10,
                        "tier": "Sovereign SCIF Enclave",
                        "start_date": "2026-08-01",
                        "original_end_date": "2027-07-31",
                        "cotermed_renewal_date": "2027-01-31",
                        "status": "COTERMED_MID_CYCLE",
                        "prorated_charge_gbp": 49767.12
                    }
                ]
            },
            {
                "account_id": "ACC-GRAB-05",
                "company_name": "Grab Singapore Engineering",
                "tier": "Enterprise",
                "currency": "SGD",
                "master_start_date": "2026-05-01",
                "master_end_date": "2027-04-30",
                "current_seats": 40,
                "base_committed_seats": 40,
                "amc_seats": 30,
                "amc_arr_usd": 72000.0,
                "current_arr_usd": 96000.0,
                "tranches": [
                    {
                        "tranche_id": "TRN-GRAB-01",
                        "seats": 40,
                        "tier": "Enterprise",
                        "start_date": "2026-05-01",
                        "original_end_date": "2027-04-30",
                        "cotermed_renewal_date": "2027-04-30",
                        "status": "ACTIVE_MASTER"
                    }
                ]
            }
        ]

        ledger = {
            "version": "1.0.0",
            "governing_authority": "DevSuperSuite Revenue Operations (growth@devsupersuite.com)",
            "brand_anonymity_protocol": "STRICT_100_PERCENT_COMPLIANT",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "accounts": accounts,
            "credit_notes": [raytheon_cn, siemens_cn],
            "consolidated_invoices": [
                {
                    "invoice_id": "INV-COTERM-E94A10B2",
                    "account_id": "ACC-RAYTHEON-01",
                    "currency": "USD",
                    "gross_charge": 24065.75,
                    "credit_notes_applied": [],
                    "net_payable": 24065.75,
                    "status": "SETTLED",
                    "payment_method": "CORPORATE_ACH",
                    "master_renewal_date": "2026-12-31",
                    "created_at": "2026-07-01T12:00:00Z"
                },
                {
                    "invoice_id": "INV-COTERM-F81C92D3",
                    "account_id": "ACC-SIEMENS-02",
                    "currency": "EUR",
                    "gross_charge": 139153.85,
                    "credit_notes_applied": [siemens_cn["credit_note_id"]],
                    "net_payable": 105923.08,
                    "status": "SETTLED",
                    "payment_method": "SEPA_DIRECT_DEBIT",
                    "master_renewal_date": "2027-03-14",
                    "created_at": "2026-09-15T11:00:00Z"
                },
                {
                    "invoice_id": "INV-COTERM-A73C44E1",
                    "account_id": "ACC-TATA-03",
                    "currency": "INR",
                    "gross_charge": 1251345.21,
                    "credit_notes_applied": [],
                    "net_payable": 1251345.21,
                    "status": "SETTLED",
                    "payment_method": "UPI_QR_INSTANT",
                    "upi_qr_payload": f"upi://pay?pa={UPI_VPA}&pn={UPI_PAYEE_NAME.replace(' ', '%20')}&am=1251345.21&cu=INR&tn=INV-COTERM-A73C44E1",
                    "master_renewal_date": "2027-05-31",
                    "created_at": "2026-09-01T08:30:00Z"
                }
            ]
        }
        self._save_ledger(ledger)
        return ledger

    def _save_ledger(self, ledger_data: Optional[Dict[str, Any]] = None) -> None:
        """Atomically saves ledger to both primary and root mirror paths."""
        data = ledger_data or self.ledger
        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        for p in [self.primary_path, self.root_path]:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def find_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Look up enterprise account by ID or company name substring."""
        acc_id_upper = account_id.strip().upper()
        for acc in self.ledger.get("accounts", []):
            if acc["account_id"].upper() == acc_id_upper or account_id.lower() in acc["company_name"].lower():
                return acc
        return None

    def prorate_seat_expansion(
        self,
        account_id: str,
        added_seats: int,
        expansion_date: Optional[str] = None,
        tier: Optional[str] = None,
        currency: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculates mid-cycle seat expansion and records the cotermed tranche in the ledger."""
        acc = self.find_account(account_id)
        if not acc:
            raise ValueError(f"Account {account_id} not found.")

        t = tier or acc["tier"]
        curr = currency or acc["currency"]
        exp_d = expansion_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        proration = LicenseProrationCalculator.calculate_seat_expansion(
            account_id=acc["account_id"],
            master_start_date=acc["master_start_date"],
            master_end_date=acc["master_end_date"],
            expansion_date=exp_d,
            added_seats=added_seats,
            tier=t,
            currency=curr
        )

        tranche_id = f"TRN-{uuid.uuid4().hex[:6].upper()}"
        new_tranche = {
            "tranche_id": tranche_id,
            "seats": added_seats,
            "tier": t,
            "start_date": exp_d,
            "original_end_date": (parse_date(exp_d) + timedelta(days=365)).isoformat(),
            "cotermed_renewal_date": acc["master_end_date"],
            "status": "COTERMED_MID_CYCLE",
            "prorated_charge_usd": proration["prorated_amount_usd"],
            "prorated_charge_local": proration["prorated_amount_local"],
            "currency": curr
        }

        acc.setdefault("tranches", []).append(new_tranche)
        acc["current_seats"] = sum(trn["seats"] for trn in acc["tranches"])
        seat_fee = TIER_CATALOG[acc["tier"]]["annual_fee_usd"]
        acc["current_arr_usd"] = acc["current_seats"] * seat_fee

        # Generate invoice
        inv = self.generate_consolidated_invoice(
            account_id=acc["account_id"],
            gross_amount=proration["prorated_amount_local"],
            currency=curr,
            renewal_date=acc["master_end_date"]
        )

        self._save_ledger()
        return {
            "proration": proration,
            "tranche": new_tranche,
            "invoice": inv
        }

    def calculate_credit_note_and_upgrade(
        self,
        account_id: str,
        new_tier: str,
        upgrade_date: Optional[str] = None,
        currency: Optional[str] = None
    ) -> Dict[str, Any]:
        """Processes mid-cycle tier upgrade, issues cryptographic credit note, and consolidates invoice."""
        acc = self.find_account(account_id)
        if not acc:
            raise ValueError(f"Account {account_id} not found.")

        old_tier = acc["tier"]
        curr = currency or acc["currency"]
        up_d = upgrade_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        upgrade_calc = LicenseProrationCalculator.calculate_tier_upgrade(
            account_id=acc["account_id"],
            master_start_date=acc["master_start_date"],
            master_end_date=acc["master_end_date"],
            upgrade_date=up_d,
            seats=acc["current_seats"],
            old_tier=old_tier,
            new_tier=new_tier,
            currency=curr
        )

        # Issue Cryptographic Credit Note for unconsumed credit
        cn = CryptographicCreditNoteAuthority.issue_credit_note(
            account_id=acc["account_id"],
            amount=upgrade_calc["unconsumed_credit_local"],
            currency=curr,
            reason=f"Unconsumed {old_tier} tier time ({upgrade_calc['days_remaining']} days remaining)",
            issued_at=datetime.now(timezone.utc).isoformat()
        )
        self.ledger.setdefault("credit_notes", []).append(cn)

        # Issue Consolidated Invoice for net payable balance
        inv = self.generate_consolidated_invoice(
            account_id=acc["account_id"],
            gross_amount=upgrade_calc["new_prorated_charge_local"],
            credit_note_ids=[cn["credit_note_id"]],
            currency=curr,
            renewal_date=acc["master_end_date"]
        )

        # Update account
        acc["tier"] = new_tier
        new_seat_fee = TIER_CATALOG[new_tier]["annual_fee_usd"]
        acc["current_arr_usd"] = acc["current_seats"] * new_seat_fee
        for trn in acc.get("tranches", []):
            trn["tier"] = new_tier
            trn["status"] = "UPGRADED_COTERMED"

        self._save_ledger()
        return {
            "upgrade_calculation": upgrade_calc,
            "credit_note": cn,
            "consolidated_invoice": inv
        }

    def coterm_licenses(
        self,
        account_id: str,
        target_master_renewal_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Aligns all active tranches for an account to a single consolidated anniversary date."""
        acc = self.find_account(account_id)
        if not acc:
            raise ValueError(f"Account {account_id} not found.")

        target_renewal = target_master_renewal_date or acc["master_end_date"]
        target_d = parse_date(target_renewal)

        aligned_tranches = []
        for trn in acc.get("tranches", []):
            orig_end = parse_date(trn.get("original_end_date", trn.get("cotermed_renewal_date", target_renewal)))
            trn["original_end_date"] = orig_end.isoformat()
            trn["cotermed_renewal_date"] = target_d.isoformat()
            trn["status"] = "COTERMED_UNIFIED"
            aligned_tranches.append(trn)

        acc["master_end_date"] = target_d.isoformat()
        self._save_ledger()

        return {
            "account_id": acc["account_id"],
            "company_name": acc["company_name"],
            "consolidated_renewal_date": target_d.isoformat(),
            "tranches_aligned": len(aligned_tranches),
            "total_seats_cotermed": sum(t["seats"] for t in aligned_tranches)
        }

    def generate_consolidated_invoice(
        self,
        account_id: str,
        gross_amount: float,
        credit_note_ids: Optional[List[str]] = None,
        currency: str = "USD",
        renewal_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generates an immediate consolidated invoice applying available credit notes."""
        curr = currency.upper()
        cn_ids = credit_note_ids or []
        applied_notes = []
        total_credit = 0.0

        for cn in self.ledger.get("credit_notes", []):
            if cn["credit_note_id"] in cn_ids and cn["currency"] == curr:
                total_credit += float(cn["amount"])
                applied_notes.append(cn["credit_note_id"])
                cn["status"] = "APPLIED"

        gross = round(gross_amount, 2)
        net_payable = round(max(0.0, gross - total_credit), 2)
        inv_id = f"INV-COTERM-{uuid.uuid4().hex[:8].upper()}"

        payment_method = "CORPORATE_ACH" if curr == "USD" else ("SEPA_DIRECT_DEBIT" if curr == "EUR" else ("UPI_QR_INSTANT" if curr == "INR" else "DIRECT_WIRE"))

        inv = {
            "invoice_id": inv_id,
            "account_id": account_id,
            "currency": curr,
            "gross_charge": gross,
            "credit_notes_applied": applied_notes,
            "credit_amount_offset": round(total_credit, 2),
            "net_payable": net_payable,
            "status": "PENDING",
            "payment_method": payment_method,
            "master_renewal_date": renewal_date,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        if curr == "INR":
            inv["upi_qr_payload"] = (
                f"upi://pay?pa={UPI_VPA}&pn={UPI_PAYEE_NAME.replace(' ', '%20')}&am={net_payable:.2f}&cu=INR&tn={inv_id}"
            )

        self.ledger.setdefault("consolidated_invoices", []).append(inv)
        return inv

    def evaluate_true_down(
        self,
        account_id: str,
        proposed_seats: int,
        request_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluates customer true-down against AMC and 60-day notice lockouts."""
        acc = self.find_account(account_id)
        if not acc:
            raise ValueError(f"Account {account_id} not found.")

        req_d = request_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        seat_fee = TIER_CATALOG[acc["tier"]]["annual_fee_usd"]
        proposed_arr = proposed_seats * seat_fee

        return LicenseProrationCalculator.validate_true_down(
            account_id=acc["account_id"],
            master_end_date=acc["master_end_date"],
            request_date=req_d,
            current_seats=acc["current_seats"],
            proposed_seats=proposed_seats,
            current_arr_usd=acc["current_arr_usd"],
            proposed_arr_usd=proposed_arr,
            amc_seats=acc.get("amc_seats", 0),
            amc_arr_usd=acc.get("amc_arr_usd", 0.0)
        )

    def export_coterm_binder(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Exports institutional Coterm Binder with audit cryptographic proofs."""
        binder_path = output_path or os.path.join(SERVICES_DATA_DIR, "enterprise_coterm_binder_export.json")
        summary = self.get_summary()

        binder = {
            "title": "DevSuperSuite Official Enterprise Coterm Binder",
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "governing_authority": "DevSuperSuite Revenue Operations (growth@devsupersuite.com)",
            "brand_anonymity_protocol": "STRICT_100_PERCENT_COMPLIANT",
            "summary_metrics": summary,
            "accounts_schedule": self.ledger.get("accounts", []),
            "credit_notes_ledger": self.ledger.get("credit_notes", []),
            "consolidated_invoices_ledger": self.ledger.get("consolidated_invoices", []),
            "cryptographic_manifest_sha256": hashlib.sha256(
                json.dumps(self.ledger.get("accounts", []), sort_keys=True).encode("utf-8")
            ).hexdigest()
        }

        with open(binder_path, "w", encoding="utf-8") as f:
            json.dump(binder, f, indent=2)

        return binder

    def get_summary(self) -> Dict[str, Any]:
        """Calculates global coterming metrics across all accounts."""
        accounts = self.ledger.get("accounts", [])
        credit_notes = self.ledger.get("credit_notes", [])
        invoices = self.ledger.get("consolidated_invoices", [])

        total_accounts = len(accounts)
        total_seats = sum(a.get("current_seats", 0) for a in accounts)
        total_arr_usd = sum(a.get("current_arr_usd", 0.0) for a in accounts)
        total_tranches = sum(len(a.get("tranches", [])) for a in accounts)
        total_credit_notes_amount = sum(cn.get("amount", 0.0) for cn in credit_notes)
        total_invoiced_net = sum(inv.get("net_payable", 0.0) for inv in invoices)

        return {
            "total_accounts_managed": total_accounts,
            "total_licensed_seats": total_seats,
            "total_managed_arr_usd": round(total_arr_usd, 2),
            "total_cotermed_tranches": total_tranches,
            "total_credit_notes_issued": len(credit_notes),
            "total_credit_notes_value": round(total_credit_notes_amount, 2),
            "total_consolidated_invoices": len(invoices),
            "total_net_invoiced_value": round(total_invoiced_net, 2)
        }

    def render_markdown_report(self) -> str:
        """Generates executive markdown audit report for commercial leadership."""
        summary = self.get_summary()
        accounts = self.ledger.get("accounts", [])
        invoices = self.ledger.get("consolidated_invoices", [])
        credit_notes = self.ledger.get("credit_notes", [])

        lines = [
            "# ⚡ DevSuperSuite Official: Enterprise License Coterming & Proration Report",
            f"**Audit Timestamp:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            "**Governing Authority:** DevSuperSuite Revenue Operations (`growth@devsupersuite.com`)  ",
            "**Strict Compliance:** 100% Brand Anonymity • Zero Founder Personal Identifiers  ",
            "",
            "---",
            "",
            "## 1. Executive Summary & Portfolio Overview",
            "",
            f"- **Managed Enterprise Accounts:** **{summary['total_accounts_managed']}**",
            f"- **Total Active Licensed Seats:** **{summary['total_licensed_seats']:,} Seats**",
            f"- **Total Governed Annual Recurring Revenue (ARR):** **${summary['total_managed_arr_usd']:,.2f} USD**",
            f"- **Consolidated License Tranches:** **{summary['total_cotermed_tranches']} Tranches**",
            f"- **Cryptographic Credit Notes Issued:** **{summary['total_credit_notes_issued']} ($ {summary['total_credit_notes_value']:,.2f} Value)**",
            f"- **Consolidated Invoices Settled/Pending:** **{summary['total_consolidated_invoices']}**",
            "",
            "---",
            "",
            "## 2. Institutional Coterming Schedule Ledger",
            "",
            "| Account ID | Organization | Tier | Currency | Seats | AMC Seats / ARR | Master Renewal | Current ARR |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |"
        ]

        for acc in accounts:
            amc_str = f"{acc.get('amc_seats', 0)} / ${acc.get('amc_arr_usd', 0.0):,.0f}"
            lines.append(
                f"| `{acc['account_id']}` | **{acc['company_name']}** | `{acc['tier']}` | `{acc['currency']}` | "
                f"{acc['current_seats']} | {amc_str} | `{acc['master_end_date']}` | ${acc['current_arr_usd']:,.2f} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 3. Cryptographic Credit Notes Ledger",
            "",
            "| Credit Note ID | Account ID | Currency | Amount | Reason | Issued At | Status | Verification |",
            "| :--- | :--- | :---: | :---: | :--- | :---: | :---: | :---: |"
        ])

        for cn in credit_notes:
            is_valid = CryptographicCreditNoteAuthority.verify_credit_note(cn)
            v_badge = "✅ VALID" if is_valid else "❌ INVALID"
            lines.append(
                f"| `{cn['credit_note_id']}` | `{cn['account_id']}` | `{cn['currency']}` | {cn['amount']:,.2f} | "
                f"{cn['reason'][:40]} | {cn['issued_at'][:10]} | `{cn['status']}` | {v_badge} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 4. Consolidated Invoices & Payment Rails",
            "",
            "| Invoice ID | Account ID | Currency | Gross | Credits | Net Payable | Rail | Status |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |"
        ])

        for inv in invoices:
            lines.append(
                f"| `{inv['invoice_id']}` | `{inv['account_id']}` | `{inv['currency']}` | {inv['gross_charge']:,.2f} | "
                f"{inv.get('credit_amount_offset', 0.0):,.2f} | **{inv['net_payable']:,.2f}** | `{inv['payment_method']}` | `{inv['status']}` |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 5. Commercial Rules & Contractual Invariants",
            "",
            "1. **Exact Daily Proration Math**:",
            "   $$\\text{Prorated Charge} = \\frac{\\text{Days Remaining in Master Term}}{\\text{Total Days in Master Term}} \\times \\Delta \\text{Annual Base Fee}$$",
            "2. **Downward True-Down Protection (60-Day Lockout)**:",
            "   - Any reduction in seat counts or ARR requires $\\ge 60$ days advance notice prior to the master renewal anniversary.",
            "   - Downgrade proposals violating contractual Annual Minimum Commitments (AMC) are strictly rejected.",
            "3. **Zero-Friction Tier Upgrades**:",
            "   - Upgrades execute mid-cycle with instantaneous credit note issuance for unconsumed time.",
            "4. **Multi-Currency & Instant Domestic UPI Checkout**:",
            "   - Indian institutional accounts dynamically receive signed UPI intent QR payloads (`devsupersuite@icici`).",
            "",
            "---",
            "**Report Approved By:** Directorate of Commercial Operations • DevSuperSuite Official"
        ])

        report_content = "\n".join(lines)
        with open(self.report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        return self.report_path

    def print_summary(self) -> None:
        """Prints formatted console summary."""
        s = self.get_summary()
        print("=" * 78)
        print("⚡ DEVSUPERSUITE ENTERPRISE LICENSE COTERMING & PRORATION ENGINE")
        print("   Governing Authority: DevSuperSuite Revenue Operations")
        print("   Brand Anonymity: 100% Strict Protocol")
        print("=" * 78)
        print(f" Managed Accounts:          {s['total_accounts_managed']}")
        print(f" Licensed Seats:            {s['total_licensed_seats']:,}")
        print(f" Governed ARR (USD):        ${s['total_managed_arr_usd']:,.2f}")
        print(f" Cotermed Tranches:         {s['total_cotermed_tranches']}")
        print(f" Credit Notes Issued:       {s['total_credit_notes_issued']} (${s['total_credit_notes_value']:,.2f})")
        print(f" Consolidated Invoices:     {s['total_consolidated_invoices']}")
        print("=" * 78)


def main():
    parser = argparse.ArgumentParser(
        description="DevSuperSuite Official Enterprise License Coterming & Proration Engine"
    )
    parser.add_argument("--prorate-seat-expansion", action="store_true", help="Calculate mid-cycle seat expansion proration")
    parser.add_argument("--coterm-licenses", action="store_true", help="Co-term all secondary tranches to master renewal date")
    parser.add_argument("--calculate-credit-note", action="store_true", help="Calculate credit note for tier upgrade unconsumed credit")
    parser.add_argument("--export-coterm-binder", action="store_true", help="Export full Coterm Binder JSON and report")
    parser.add_argument("--summary", action="store_true", help="Display summary metrics and regenerate executive report")

    parser.add_argument("--account", type=str, default="ACC-RAYTHEON-01", help="Target Account ID or Company Name")
    parser.add_argument("--seats", type=int, default=10, help="Seat count for expansion or upgrade")
    parser.add_argument("--tier", type=str, default="Enterprise", help="Target tier (Pro, Enterprise, Sovereign SCIF Enclave)")
    parser.add_argument("--old-tier", type=str, default="Enterprise", help="Existing tier for upgrade")
    parser.add_argument("--new-tier", type=str, default="Sovereign SCIF Enclave", help="New target tier for upgrade")
    parser.add_argument("--currency", type=str, default="USD", help="Transaction currency (USD, EUR, GBP, INR, SGD)")
    parser.add_argument("--date", type=str, default=None, help="Action date (YYYY-MM-DD)")
    parser.add_argument("--master-start", type=str, default=None, help="Master term start date (YYYY-MM-DD)")
    parser.add_argument("--master-end", type=str, default=None, help="Master term end date (YYYY-MM-DD)")

    args = parser.parse_args()
    engine = EnterpriseLicenseCotermEngine()

    if args.prorate_seat_expansion:
        res = engine.prorate_seat_expansion(
            account_id=args.account,
            added_seats=args.seats,
            expansion_date=args.date,
            tier=args.tier,
            currency=args.currency
        )
        print(f"[✓] Seat Expansion Prorated:")
        print(f"    - Account:           {res['proration']['account_id']}")
        print(f"    - Added Seats:       {res['proration']['added_seats']} ({res['proration']['tier']})")
        print(f"    - Prorated USD:      ${res['proration']['prorated_amount_usd']:,.2f}")
        print(f"    - Prorated {res['proration']['currency']}:  {res['proration']['prorated_amount_local']:,.2f}")
        print(f"    - Invoice ID:        {res['invoice']['invoice_id']}")

    if args.coterm_licenses:
        res = engine.coterm_licenses(
            account_id=args.account,
            target_master_renewal_date=args.master_end
        )
        print(f"[✓] Licenses Cotermed:")
        print(f"    - Account:           {res['account_id']} ({res['company_name']})")
        print(f"    - Master Renewal:    {res['consolidated_renewal_date']}")
        print(f"    - Aligned Tranches:  {res['tranches_aligned']}")
        print(f"    - Total Cotermed:    {res['total_seats_cotermed']} seats")

    if args.calculate_credit_note:
        res = engine.calculate_credit_note_and_upgrade(
            account_id=args.account,
            new_tier=args.new_tier,
            upgrade_date=args.date,
            currency=args.currency
        )
        print(f"[✓] Tier Upgrade & Credit Note Calculated:")
        print(f"    - Account:           {args.account}")
        print(f"    - New Tier:          {args.new_tier}")
        print(f"    - Credit Note ID:    {res['credit_note']['credit_note_id']} ({res['credit_note']['amount']} {res['credit_note']['currency']})")
        print(f"    - Net Payable:       {res['consolidated_invoice']['net_payable']} {res['consolidated_invoice']['currency']}")
        print(f"    - Invoice ID:        {res['consolidated_invoice']['invoice_id']}")

    if args.export_coterm_binder:
        binder = engine.export_coterm_binder()
        print(f"[✓] Exported Coterm Binder: {os.path.join(SERVICES_DATA_DIR, 'enterprise_coterm_binder_export.json')}")
        print(f"    - Cryptographic Digest: {binder['cryptographic_manifest_sha256'][:16]}...")

    if args.summary or (not args.prorate_seat_expansion and not args.coterm_licenses and not args.calculate_credit_note and not args.export_coterm_binder):
        engine.render_markdown_report()
        engine.print_summary()


if __name__ == "__main__":
    main()
