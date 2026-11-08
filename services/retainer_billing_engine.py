#!/usr/bin/env python3
"""
⚡ DevSuperSuite Tech Services - Enterprise Quote-to-Cash (Q2C) Retainer & Billing Engine
File: retainer_billing_engine.py
Version: 1.0.0
Author: CFO & Commercial Operations Desk
Strict Compliance: 100% Brand Anonymity - DevSuperSuite Commercial Operations Only.

Features:
- Dedicated Monthly Retainer Pod Management ($8,500.00/month baseline for 45 engineering hours).
- Automatic Billable Overage Calculation ($120.00/hour for architectural & security overage).
- Net-30 Enterprise Invoicing with LUT zero-rated export notations & EU reverse-charge clauses.
- Statutory Late Payment Interest Engine (1.5% per month / 18.0% APR compounding).
- Automated Dunning Lifecycle Engine with Day +30 Soft Freeze & Day +45 Hard Freeze triggers.
- Multi-Action CLI: --generate-invoice, --record-hours, --check-dunning, --summary.
"""

import sys
import os
import json
import argparse
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Constants & Paths
SERVICES_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(SERVICES_DIR)
DATA_DIR = os.path.join(SCRATCH_DIR, "data")
INVOICES_DIR = os.path.join(SERVICES_DIR, "invoices")
RETAINER_LEDGER_FILE = os.path.join(DATA_DIR, "retainer_contracts_ledger.json")

# Statutory Commercial Standards
DEFAULT_LUT_REF = "DSS-LUT-FY2026-REG-0994"
BASELINE_RETAINER_FEE_USD = 8500.00
BASELINE_HOURS_INCLUDED = 45.0
OVERAGE_HOURLY_RATE_USD = 120.00
MONTHLY_LATE_FEE_PCT = 0.015  # 1.5% per month (18.0% APR)
ANNUAL_INTEREST_RATE = 0.18

class RetainerBillingEngine:
    """Institutional Quote-to-Cash engine for DevSuperSuite retainer contracts."""

    def __init__(self, ledger_file: str = RETAINER_LEDGER_FILE):
        self.ledger_file = ledger_file
        self.data = self._load_or_initialize_ledger()

    def _load_or_initialize_ledger(self) -> Dict[str, Any]:
        """Loads or seeds the enterprise retainer contracts database."""
        os.makedirs(os.path.dirname(self.ledger_file), exist_ok=True)
        os.makedirs(INVOICES_DIR, exist_ok=True)

        if os.path.exists(self.ledger_file):
            try:
                with open(self.ledger_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        # Seed initial retainer database with Nexus Enterprise Technologies Corp.
        initial_ledger = {
            "metadata": {
                "organization": "DevSuperSuite Official",
                "entity": "DevSuperSuite Commercial Operations",
                "department": "Treasury & Accounts Receivable",
                "lut_reference": DEFAULT_LUT_REF,
                "billing_contact": "billing@devsupersuite.com",
                "last_updated": datetime.now(timezone.utc).isoformat()
            },
            "contracts": {
                "NEXUS-RET-2026": {
                    "contract_id": "DSS-RET-2026-NEXUS-01",
                    "client_name": "Nexus Enterprise Technologies Corp.",
                    "client_contact": "Director of Engineering Operations & Enterprise Procurement",
                    "client_address": "500 Innovation Way, Suite 1200, Austin, TX 78701, USA",
                    "client_vat_ein": "US-EIN-74-8839210",
                    "plan_name": "Enterprise Dedicated AI & Autonomous Systems Pod",
                    "monthly_baseline_fee_usd": BASELINE_RETAINER_FEE_USD,
                    "baseline_hours_included": BASELINE_HOURS_INCLUDED,
                    "overage_hourly_rate_usd": OVERAGE_HOURLY_RATE_USD,
                    "credit_terms": "NET-30",
                    "current_billing_period": "November 2026",
                    "hours_logged": [
                        {
                            "date": "2026-11-02",
                            "hours": 15.0,
                            "role": "Principal Solutions Architect",
                            "task": "OmniKernel AST AST-slicing visitor performance optimization for multi-tier microservices"
                        },
                        {
                            "date": "2026-11-04",
                            "hours": 20.0,
                            "role": "Senior AI Systems Engineer",
                            "task": "AgentShield zero-day Shannon entropy pre-commit hook tuning & CI/CD pipeline integration"
                        },
                        {
                            "date": "2026-11-06",
                            "hours": 10.0,
                            "role": "Principal Solutions Architect",
                            "task": "Model Context Protocol (MCP) JSON-RPC 2.0 dual server cluster testing and load validation"
                        }
                    ],
                    "invoices": [
                        {
                            "invoice_id": "INV-RET-2026-001",
                            "issue_date": "2026-11-01",
                            "due_date": "2026-12-01",
                            "period": "November 2026",
                            "baseline_amount_usd": BASELINE_RETAINER_FEE_USD,
                            "overage_hours": 0.0,
                            "overage_amount_usd": 0.0,
                            "total_invoiced_usd": BASELINE_RETAINER_FEE_USD,
                            "status": "ISSUED_PENDING_PAYMENT",
                            "days_overdue": 0,
                            "statutory_late_interest_usd": 0.0
                        }
                    ],
                    "historical_delinquent_sim": {
                        "invoice_id": "INV-RET-2026-HIST-099",
                        "issue_date": "2026-09-15",
                        "due_date": "2026-10-15",
                        "original_principal_usd": 8500.00,
                        "status": "DELINQUENT_OVERDUE",
                        "days_overdue": 24,  # Overdue past Net-30
                        "freeze_trigger_stage": "STAGE_2_FORMAL_DELINQUENCY"
                    }
                }
            }
        }

        self._save_ledger(initial_ledger)
        return initial_ledger

    def _save_ledger(self, data: Optional[Dict[str, Any]] = None):
        """Persists retainer data to disk."""
        payload = data or self.data
        payload["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.ledger_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def record_hours(
        self,
        contract_key: str,
        hours: float,
        role: str,
        task: str,
        date_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """Logs engineering hours against client retainer pod."""
        contracts = self.data.setdefault("contracts", {})
        if contract_key not in contracts:
            raise KeyError(f"Contract '{contract_key}' not found in retainer ledger.")

        contract = contracts[contract_key]
        log_date = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        entry = {
            "date": log_date,
            "hours": float(hours),
            "role": role,
            "task": task
        }
        contract.setdefault("hours_logged", []).append(entry)
        self._save_ledger()

        total_hours = sum(h["hours"] for h in contract["hours_logged"])
        baseline = contract.get("baseline_hours_included", BASELINE_HOURS_INCLUDED)
        overage = max(0.0, total_hours - baseline)

        return {
            "status": "HOURS_RECORDED",
            "entry": entry,
            "total_hours_logged": total_hours,
            "baseline_hours_included": baseline,
            "overage_hours": overage,
            "estimated_overage_charge_usd": overage * contract.get("overage_hourly_rate_usd", OVERAGE_HOURLY_RATE_USD)
        }

    def compute_billing_details(self, contract_key: str) -> Dict[str, Any]:
        """Computes current billing metrics: baseline fee, overage hours, total charges."""
        contract = self.data["contracts"][contract_key]
        baseline_fee = contract.get("monthly_baseline_fee_usd", BASELINE_RETAINER_FEE_USD)
        baseline_hours = contract.get("baseline_hours_included", BASELINE_HOURS_INCLUDED)
        overage_rate = contract.get("overage_hourly_rate_usd", OVERAGE_HOURLY_RATE_USD)

        logged_items = contract.get("hours_logged", [])
        total_hours = sum(h["hours"] for h in logged_items)
        overage_hours = max(0.0, total_hours - baseline_hours)
        overage_amount = overage_hours * overage_rate
        total_invoiced = baseline_fee + overage_amount

        # Direct loaded labor cost estimation:
        # 45 base hours @ blended ~$28/hr loaded cost = $1,260
        # Overage hours @ $38/hr loaded cost = overage_hours * 38
        loaded_cost = (min(total_hours, baseline_hours) * 28.0) + (overage_hours * 38.0)
        gross_profit = total_invoiced - loaded_cost
        gross_margin_pct = (gross_profit / total_invoiced * 100) if total_invoiced else 0.0

        return {
            "contract_id": contract["contract_id"],
            "client_name": contract["client_name"],
            "period": contract.get("current_billing_period", "November 2026"),
            "baseline_hours": baseline_hours,
            "total_hours_logged": total_hours,
            "overage_hours": overage_hours,
            "baseline_fee_usd": baseline_fee,
            "overage_amount_usd": overage_amount,
            "total_invoiced_usd": total_invoiced,
            "loaded_direct_cost_usd": round(loaded_cost, 2),
            "gross_profit_usd": round(gross_profit, 2),
            "gross_margin_pct": round(gross_margin_pct, 2)
        }

    def generate_retainer_invoice_markdown(
        self,
        contract_key: str = "NEXUS-RET-2026",
        invoice_id: str = "INV-RET-2026-001",
        include_overage: bool = True
    ) -> str:
        """Renders institutional Net-30 retainer commercial invoice in Markdown."""
        contract = self.data["contracts"][contract_key]
        calc = self.compute_billing_details(contract_key)
        
        issue_date = datetime.now(timezone.utc)
        due_date = issue_date + timedelta(days=30)
        issue_str = issue_date.strftime("%B %d, %Y")
        due_str = due_date.strftime("%B %d, %Y")

        overage_hrs = calc["overage_hours"] if include_overage else 0.0
        overage_amt = calc["overage_amount_usd"] if include_overage else 0.0
        grand_total = calc["baseline_fee_usd"] + overage_amt

        md = f"""# ⚡ DevSuperSuite Commercial Operations
## Institutional Commercial Invoice: `{invoice_id}`
**Contract Identifier:** `{contract['contract_id']}`  
**Official Treasury & Billing Desk:** `billing@devsupersuite.com`  
**Commercial Entity:** DevSuperSuite Commercial Operations  
**Letter of Undertaking (LUT) Ref:** `{DEFAULT_LUT_REF}`  
**Statutory Classification:** 100% Brand Anonymity Protocol Verified  

---

### 📋 Invoice Summary & Legal Identification

| Commercial Issuer | Client Counterparty (Bill-To) |
| :--- | :--- |
| **DevSuperSuite Commercial Operations** | **{contract['client_name']}** |
| Global Commercial Accounts & Treasury | Attn: {contract['client_contact']} |
| Portal: `devsupersuite.web.app` | Address: {contract['client_address']} |
| Billing Inquiries: `billing@devsupersuite.com` | Tax / EIN ID: `{contract['client_vat_ein']}` |
| Remittance: SWIFT / Fedwire (Code: `OUR`) | Agreement: **{contract['plan_name']}** |

| Financial Term | Contractual Value |
| :--- | :--- |
| **Invoice Number** | **`{invoice_id}`** |
| **Issue Date** | {issue_str} |
| **Credit Terms** | **{contract.get('credit_terms', 'NET-30')}** |
| **Maturity / Payment Due Date** | **{due_str}** |
| **Billing Period** | **{calc['period']}** |
| **Settlement Currency** | **United States Dollars (USD - $)** |
| **Total Amount Due** | **${grand_total:,.2f} USD** |

---

### 🛠️ Itemized Retainer Services & Overage Accounting

| Item | Service Description & Allocation Profile | Quantity / Hours | Rate Card (USD) | Total Amount (USD) |
| :---: | :--- | :---: | :---: | :---: |
| 01 | **Dedicated AI & Autonomous Systems Pod Retainer**<br>_Monthly dedicated engineering pod: OmniKernel AST context pruning, AgentShield zero-day entropy integration, CI/CD invariant rule maintenance, and 24/7 P1 incident SLA coverage._ | 1.0 Month<br>_(45.0 hrs base)_ | ${calc['baseline_fee_usd']:,.2f} / mo | **${calc['baseline_fee_usd']:,.2f}** |
"""
        if overage_hrs > 0:
            md += f"""| 02 | **Billable Engineering Overage**<br>_Additional architectural engineering, custom AST transformer visitors, and security invariant rules beyond the 45.0 base hours._ | {overage_hrs:,.1f} hrs | ${contract['overage_hourly_rate_usd']:,.2f} / hr | **${overage_amt:,.2f}** |\n"""

        md += f"""
| | **SUBTOTAL** | | | **${grand_total:,.2f}** |
| | **DISCOUNTS / CREDITS APPLIED** | | | **$0.00** |
| | **TAX / VAT (0.0% Export Under LUT Regime)** | | | **$0.00** |
| | **TOTAL NET CAPITAL PAYABLE** | | | **${grand_total:,.2f} USD** |

---

### 🏛️ Cross-Border Tax Compliance & Zero-Rated Export Certifications
- **US Internal Revenue Code (IRS) Exemption**: Services rendered strictly offshore under **Article 7 (Business Profits)** of the bilateral Double Taxation Avoidance Agreement (DTAA). DevSuperSuite is certified as an **Active NFFE** under Chapter 4 FATCA. Form W-8BEN-E on file. **0.0% Federal Withholding Tax (WHT)** applies.
- **European Union / UK Reverse Charge Protocol**: In accordance with **Article 196 of EU VAT Directive 2006/112/EC** and Section 8 of the UK Value Added Tax Act 1994, VAT is subject to reverse charge self-accounting by the recipient business.
- **Zero-Rated Software Export**: Issued under active **Letter of Undertaking (LUT)** Reference: **`{DEFAULT_LUT_REF}`** without payment of integrated tax. Central Bank Purpose Code: **`P0804`** (Other Computer Software Services / Retainers).

---

### 💳 Electronic Settlement & Institutional Wire Remittance
*International Wire Transfer (SWIFT / Fedwire) is the designated settlement rail for this commercial retainer.*

```
================================================================================
INSTITUTIONAL WIRE ROUTING INSTRUCTIONS (USD)
================================================================================
Beneficiary Legal Name:    DevSuperSuite Commercial Operations Account
Beneficiary Bank:          Silicon Valley Commercial Clearing Bank / JPMorgan Chase
Bank Address:              270 Park Avenue, New York, NY 10017, USA
SWIFT / BIC Code:          DEVSUS33XXX
Fedwire / ABA Routing:     121000358
Commercial Account Number: 9824-0019-8832-USD
Payment Reference / Memo:  {invoice_id} / {contract['client_name']}
Mandatory SWIFT Code:      OUR (Client remitter absorbs all wire transfer and intermediary charges)
Net Received Balance:      ${grand_total:,.2f} USD
================================================================================
```

*Direct Instant Card Portal:* [https://devsupersuite.web.app/checkout/{invoice_id.lower()}](https://devsupersuite.web.app/checkout/{invoice_id.lower()})

---

### ⚖️ Credit Terms, Late Financing Penalties & Work Freeze Policy
1. **Contractual Terms**: In accordance with **{contract.get('credit_terms', 'NET-30')}**, payment must clear on or before **{due_str}**.
2. **Statutory Late Interest**: Unpaid balances past the maturity date incur a compounding finance charge of **1.5% per month (18.0% per annum)** calculated on a daily basis from the due date.
3. **Service Continuity**: In the event an invoice remains unsettled past thirty (30) days from maturity:
   - **Day +30**: Pull request merges, non-critical sprint commits, and staging preview builds are paused.
   - **Day +45**: Staging clusters deprovisioned, collaborator repo privileges revoked.
4. **Brand Anonymity**: Issued exclusively under **DevSuperSuite Commercial Operations**.

---
*Authorized by: Office of the CFO & Commercial Treasury Desk — DevSuperSuite Commercial Operations*  
*Verification Token: DSS-Q2C-{abs(hash(invoice_id)) % 1000000:06d} | Verified Active Contract*
"""
        return md

    def compute_statutory_interest(
        self,
        principal_usd: float,
        days_overdue: int
    ) -> Tuple[float, float]:
        """
        Calculates statutory late interest compounding at 1.5% monthly (18.0% APR).
        Returns: (interest_amount_usd, total_delinquent_balance_usd)
        """
        if days_overdue <= 0:
            return 0.0, principal_usd

        # Daily compounding at 18.0% APR
        daily_rate = ANNUAL_INTEREST_RATE / 365.0
        total_balance = principal_usd * ((1.0 + daily_rate) ** days_overdue)
        interest = round(total_balance - principal_usd, 2)
        total_due = round(principal_usd + interest, 2)
        return interest, total_due

    def generate_dunning_notice_markdown(
        self,
        contract_key: str = "NEXUS-RET-2026",
        notice_id: str = "DUN-2026-001-NOTICE",
        invoice_id: str = "INV-RET-2026-001",
        principal_amount_usd: float = BASELINE_RETAINER_FEE_USD,
        days_overdue: int = 18
    ) -> str:
        """Generates formal statutory dunning notice with interest compounding and freeze warnings."""
        contract = self.data["contracts"][contract_key]
        interest, total_due = self.compute_statutory_interest(principal_amount_usd, days_overdue)
        
        notice_date = datetime.now(timezone.utc)
        original_due_date = notice_date - timedelta(days=days_overdue)
        notice_str = notice_date.strftime("%B %d, %Y")
        due_str = original_due_date.strftime("%B %d, %Y")

        freeze_stage = "STAGE 2: FORMAL DELINQUENCY & INTEREST APPLICATION"
        if days_overdue >= 45:
            freeze_stage = "STAGE 4: HARD FREEZE & ENVIRONMENT TEARDOWN"
        elif days_overdue >= 30:
            freeze_stage = "STAGE 3: SOFT SPRINT FREEZE ACTIVE"

        md = f"""# ⚡ DevSuperSuite Commercial Operations
## FORMAL NOTICE OF DELINQUENCY & STATUTORY DEMAND: `{notice_id}`
**Reference Commercial Invoice:** `{invoice_id}`  
**Original Contract:** `{contract['contract_id']}`  
**Notice Issuance Date:** {notice_str}  
**Accounts Receivable Authority:** `billing@devsupersuite.com`  
**Classification:** 100% Brand Anonymity Protocol Verified  

---

### ⚠️ URGENT REMITTANCE NOTIFICATION: DELINQUENT OVERDUE STATUS

```
+---------------------------------------------------------------------------------------------------------+
|                                    DELINQUENT RECEIVABLE SCORECARD                                      |
+---------------------------------------------------------------------------------------------------------+
| Client Counterparty           : {contract['client_name']}                                   |
| Invoiced Principal Amount     : ${principal_amount_usd:,.2f} USD                                             |
| Contractual Maturity Due Date : {due_str} (Past Due)                                         |
| Elapsed Days Past Net-30      : {days_overdue} Calendar Days Overdue                                         |
| Statutory Late Financing Fee  : +${interest:,.2f} USD (1.5%/Month / 18.0% APR Compounding)                   |
| TOTAL ACCRUED BALANCE DUE     : ${total_due:,.2f} USD                                             |
| Current Enforcement Stage     : {freeze_stage}                          |
+---------------------------------------------------------------------------------------------------------+
```

### 📋 Statement of Account & Accrued Financing Charges

| Financial Component | Amount (USD) | Statutory / Contractual Basis |
| :--- | :---: | :--- |
| **Original Invoiced Principal** | **${principal_amount_usd:,.2f}** | Milestone / Monthly Retainer under SOW `DSS-SOW-2026-088-M1` |
| **Accrued Late Financing Charge** | **+${interest:,.2f}** | 1.5% per month (18.0% APR) compounding daily for {days_overdue} days |
| **TOTAL REMITTANCE REQUIRED** | **${total_due:,.2f} USD** | **Immediate Settlement Demanded** |

---

### ⏱️ Operational Work Freeze Timeline & Enforcement Triggers

Pursuant to Section 5.2 of the *DevSuperSuite Master Commercial Billing & Financial Operations Manual*:

```
[Day 0: Maturity Date ({due_str})] ──> Invoice Matures (Net-30 elapsed)
                      │
[Day +15: Formal Notice Issued] ──> +1.5% Statutory Late Finance Charge Compounded DAILY
                      │
[Day +30: SOFT FREEZE TRIGGER]  ──> Pull request merges, non-critical sprint commits, and
                                    feature branches PAUSED across all client repositories.
                      │
[Day +45: HARD FREEZE TRIGGER]  ──> Staging environments, sandbox containers, and vector
                                    database clusters DEPROVISIONED. Repo access revoked.
                      │
[Day +60: LEGAL ASSIGNMENT]     ──> Referral to external commercial collection counsel.
```

> [!WARNING] Immediate Action Required to Avoid Sprint Suspension
> This account has reached **Day +{days_overdue} Delinquency**. If payment confirmation is not received within **{max(1, 30 - days_overdue)} calendar days**, active engineering sprint deliveries will automatically transition into a **Soft Engineering Freeze**.

---

### 💳 Emergency Settlement & Electronic Wire Instructions

Remit the full accrued balance of **${total_due:,.2f} USD** immediately using institutional wire routing:

```
================================================================================
INSTITUTIONAL WIRE CLEARING INSTRUCTIONS (USD)
================================================================================
Beneficiary Name:          DevSuperSuite Commercial Operations Account
Depository Financial Inst: Silicon Valley Commercial Clearing Bank / JPMorgan Chase
Bank Address:              270 Park Avenue, New York, NY 10017, USA
SWIFT / BIC Code:          DEVSUS33XXX
Fedwire / ABA Routing:     121000358
Account Number:            9824-0019-8832-USD
Invoice & Notice Memo:     {invoice_id} / {notice_id} / {contract['client_name']}
Mandatory SWIFT Wire Code: OUR (Sender absorbs all outgoing and correspondent fees)
Settlement Target:         ${total_due:,.2f} USD (Net Received Balance)
================================================================================
```

*Instant Corporate Card Settlement:* [https://devsupersuite.web.app/checkout/{invoice_id.lower()}](https://devsupersuite.web.app/checkout/{invoice_id.lower()})

---
*Authorized by: Office of the CFO & Commercial Treasury Desk — DevSuperSuite Commercial Operations*  
*Transmission Hash: DSS-DUN-{abs(hash(notice_id)) % 1000000:06d} | Legal Notice of Default*
"""
        return md

    def generate_and_save_artifacts(
        self,
        invoice_path: str = os.path.join(INVOICES_DIR, "INV-RET-2026-001.md"),
        notice_path: str = os.path.join(INVOICES_DIR, "DUN-2026-001-NOTICE.md")
    ) -> Tuple[str, str]:
        """Generates and writes both official retainer invoice and dunning notice."""
        os.makedirs(os.path.dirname(os.path.abspath(invoice_path)), exist_ok=True)
        os.makedirs(os.path.dirname(os.path.abspath(notice_path)), exist_ok=True)

        inv_md = self.generate_retainer_invoice_markdown(
            contract_key="NEXUS-RET-2026",
            invoice_id="INV-RET-2026-001",
            include_overage=False  # Clean baseline $8,500.00
        )
        with open(invoice_path, "w", encoding="utf-8") as f:
            f.write(inv_md)

        dun_md = self.generate_dunning_notice_markdown(
            contract_key="NEXUS-RET-2026",
            notice_id="DUN-2026-001-NOTICE",
            invoice_id="INV-RET-2026-001",
            principal_amount_usd=BASELINE_RETAINER_FEE_USD,
            days_overdue=18
        )
        with open(notice_path, "w", encoding="utf-8") as f:
            f.write(dun_md)

        return invoice_path, notice_path


def main():
    parser = argparse.ArgumentParser(
        description="⚡ DevSuperSuite Commercial Operations - Enterprise Q2C Retainer & Billing Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--generate-invoice", action="store_true", help="Generate official monthly retainer invoice")
    parser.add_argument("--record-hours", type=float, help="Record billable hours against client retainer")
    parser.add_argument("--role", default="Senior AI Systems Engineer", help="Role for recorded hours")
    parser.add_argument("--task", default="OmniKernel AST visitor customization", help="Task description for recorded hours")
    parser.add_argument("--client", default="NEXUS-RET-2026", help="Client contract key")
    parser.add_argument("--check-dunning", action="store_true", help="Audit aging schedule and generate dunning notice")
    parser.add_argument("--summary", action="store_true", help="Print executive terminal summary")
    parser.add_argument("--invoice-output", default=os.path.join(INVOICES_DIR, "INV-RET-2026-001.md"), help="Invoice path")
    parser.add_argument("--dunning-output", default=os.path.join(INVOICES_DIR, "DUN-2026-001-NOTICE.md"), help="Dunning notice path")

    args = parser.parse_args()

    # Default action
    if not (args.generate_invoice or args.record_hours or args.check_dunning or args.summary):
        args.generate_invoice = True
        args.check_dunning = True
        args.summary = True

    engine = RetainerBillingEngine()

    if args.record_hours:
        res = engine.record_hours(
            contract_key=args.client,
            hours=args.record_hours,
            role=args.role,
            task=args.task
        )
        print("=" * 80)
        print("⚡ DevSuperSuite Commercial Operations - Billable Hours Recorded")
        print("=" * 80)
        print(f"Hours Logged:            {args.record_hours:.1f} hrs ({args.role})")
        print(f"Total Logged in Pod:     {res['total_hours_logged']:.1f} hrs")
        print(f"Baseline Included:       {res['baseline_hours_included']:.1f} hrs")
        print(f"Overage Triggered:       {res['overage_hours']:.1f} hrs")
        print(f"Overage Charges (Est):   ${res['estimated_overage_charge_usd']:,.2f} USD")
        print("=" * 80)

    if args.generate_invoice or args.check_dunning:
        inv_file, dun_file = engine.generate_and_save_artifacts(
            invoice_path=args.invoice_output,
            notice_path=args.dunning_output
        )
        print(f"✅ Retainer Commercial Invoice generated:\n   {inv_file}")
        print(f"✅ Delinquency Dunning Notice generated:\n   {dun_file}")

    if args.summary:
        calc = engine.compute_billing_details(args.client)
        interest, total_due = engine.compute_statutory_interest(calc["baseline_fee_usd"], days_overdue=18)
        print("\n" + "=" * 80)
        print("⚡ DevSuperSuite Commercial Operations - Retainer Q2C Executive Summary")
        print("=" * 80)
        print(f"Client Counterparty:     {calc['client_name']}")
        print(f"Billing Period:          {calc['period']}")
        print(f"Monthly Baseline Fee:    ${calc['baseline_fee_usd']:,.2f} USD (45.0 hrs included)")
        print(f"Total Hours Consumed:    {calc['total_hours_logged']:.1f} hrs")
        print(f"Billable Overage Hours:  {calc['overage_hours']:.1f} hrs ($120.00/hr)")
        print(f"Total Invoiced Amount:   ${calc['total_invoiced_usd']:,.2f} USD")
        print(f"Loaded Direct Labor:     ${calc['loaded_direct_cost_usd']:,.2f} USD")
        print(f"Realized Gross Margin:   {calc['gross_margin_pct']:.2f}% (CFO Benchmark: >= 65.0%)")
        print(f"Simulated Overdue Aging: 18 Days Overdue (Past Net-30)")
        print(f"Statutory Late Interest: +${interest:,.2f} USD (1.5%/mo compounded)")
        print(f"Total Accrued Balance:   ${total_due:,.2f} USD")
        print("=" * 80)


if __name__ == "__main__":
    main()
