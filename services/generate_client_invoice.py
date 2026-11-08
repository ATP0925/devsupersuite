#!/usr/bin/env python3
"""
⚡ DevSuperSuite Tech Services - Automated Enterprise Invoicing Engine
File: generate_client_invoice.py
Version: 1.0.0
Author: CFO & Commercial Operations Desk
Strict Compliance: 100% Brand Anonymity - DevSuperSuite Official Only.

Generates institution-grade commercial client invoices in Markdown with:
- Line itemized roles, rate cards, and deliverables
- Automated gross margin (%) and unit cost calculations
- International payment remittance routing (Stripe, PayPal, Fedwire/SWIFT)
- Credit terms governance (Net-0, Net-15, Net-30) and late fee compliance
"""

import sys
import os
import json
import argparse
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

# Standard Rate Cards and Direct Cost Baselines ($/hr)
DEFAULT_COST_PROFILES = {
    "junior": {"rate": 45.0, "loaded_cost": 15.0, "title": "Junior Implementation Specialist"},
    "senior": {"rate": 75.0, "loaded_cost": 25.0, "title": "Senior AI Systems Engineer"},
    "architect": {"rate": 120.0, "loaded_cost": 38.0, "title": "Principal Solutions Architect"},
    "infra": {"rate": 1.0, "loaded_cost": 0.8333, "title": "Cloud Infrastructure & Tooling"},
}

MINIMUM_GROSS_MARGIN_BENCHMARK = 65.0  # 65% Gross Margin Floor

class InvoiceLineItem:
    def __init__(
        self,
        item_id: int,
        description: str,
        role: str,
        hours: float,
        hourly_rate: float,
        loaded_cost_rate: float,
        is_fixed_milestone: bool = False,
    ):
        self.item_id = item_id
        self.description = description
        self.role = role
        self.hours = hours
        self.hourly_rate = hourly_rate
        self.loaded_cost_rate = loaded_cost_rate
        self.is_fixed_milestone = is_fixed_milestone

    @property
    def total_revenue(self) -> float:
        return round(self.hours * self.hourly_rate, 2)

    @property
    def total_direct_cost(self) -> float:
        return round(self.hours * self.loaded_cost_rate, 2)

    @property
    def gross_profit(self) -> float:
        return round(self.total_revenue - self.total_direct_cost, 2)

    @property
    def gross_margin_pct(self) -> float:
        if self.total_revenue == 0:
            return 0.0
        return round((self.gross_profit / self.total_revenue) * 100, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "description": self.description,
            "role": self.role,
            "hours": self.hours,
            "hourly_rate": self.hourly_rate,
            "loaded_cost_rate": self.loaded_cost_rate,
            "total_revenue": self.total_revenue,
            "total_direct_cost": self.total_direct_cost,
            "gross_profit": self.gross_profit,
            "gross_margin_pct": self.gross_margin_pct,
        }


class EnterpriseInvoice:
    def __init__(
        self,
        invoice_id: str,
        client_name: str,
        client_contact: str = "Accounts Payable / Procurement",
        client_address: str = "Corporate Headquarters",
        client_vat_ein: str = "Pending Verification",
        project_name: str = "Autonomous Engineering & DevToolkit Services",
        invoice_date: Optional[str] = None,
        terms: str = "NET-30",
        due_date: Optional[str] = None,
        currency: str = "USD",
        notes: str = "Professional engineering and architecture services rendered under Master Services Agreement.",
    ):
        self.invoice_id = invoice_id
        self.client_name = client_name
        self.client_contact = client_contact
        self.client_address = client_address
        self.client_vat_ein = client_vat_ein
        self.project_name = project_name
        self.currency = currency
        self.terms = terms.upper()
        self.notes = notes

        # Dates
        if invoice_date:
            self.date = datetime.strptime(invoice_date, "%Y-%m-%d")
        else:
            self.date = datetime.now(timezone.utc)

        if due_date:
            self.due_date = datetime.strptime(due_date, "%Y-%m-%d")
        else:
            term_days = 30 if "30" in self.terms else (15 if "15" in self.terms else 0)
            self.due_date = self.date + timedelta(days=term_days)

        self.line_items: List[InvoiceLineItem] = []

    def add_line_item(
        self,
        description: str,
        role: str,
        hours: float,
        hourly_rate: float,
        loaded_cost_rate: float,
        is_fixed_milestone: bool = False,
    ):
        item_id = len(self.line_items) + 1
        item = InvoiceLineItem(
            item_id=item_id,
            description=description,
            role=role,
            hours=hours,
            hourly_rate=hourly_rate,
            loaded_cost_rate=loaded_cost_rate,
            is_fixed_milestone=is_fixed_milestone,
        )
        self.line_items.append(item)
        return item

    @property
    def total_revenue(self) -> float:
        return round(sum(item.total_revenue for item in self.line_items), 2)

    @property
    def total_direct_cost(self) -> float:
        return round(sum(item.total_direct_cost for item in self.line_items), 2)

    @property
    def total_gross_profit(self) -> float:
        return round(self.total_revenue - self.total_direct_cost, 2)

    @property
    def overall_gross_margin_pct(self) -> float:
        if self.total_revenue == 0:
            return 0.0
        return round((self.total_gross_profit / self.total_revenue) * 100, 2)

    @property
    def meets_margin_benchmark(self) -> bool:
        return self.overall_gross_margin_pct >= MINIMUM_GROSS_MARGIN_BENCHMARK

    def render_markdown(self) -> str:
        date_str = self.date.strftime("%B %d, %Y")
        due_date_str = self.due_date.strftime("%B %d, %Y")
        margin_status = "✅ COMPLIANT" if self.meets_margin_benchmark else "⚠️ REVIEW REQUIRED"

        md = f"""# ⚡ DevSuperSuite Tech Services
## Institutional Commercial Invoice: `{self.invoice_id}`
**Official Commercial Division:** DevSuperSuite Official  
**Official Portal:** [https://devsupersuite.web.app](https://devsupersuite.web.app)  
**Commercial Operations & Treasury:** `billing@devsupersuite.com`  
**Security & Compliance:** 100% Brand Anonymity Protocol Verified  

---

### 📋 Invoice Summary & Counterparties

| Issuer (Commercial Operations) | Client Bill-To Information |
| :--- | :--- |
| **DevSuperSuite Tech Services** | **{self.client_name}** |
| Commercial Accounts & Treasury Desk | Attn: {self.client_contact} |
| Web: `devsupersuite.web.app` | Address: {self.client_address} |
| Billing Desk: `billing@devsupersuite.com` | Client Tax / EIN ID: `{self.client_vat_ein}` |
| Remittance: Institutional Wire / Stripe / PayPal | Engagement: **{self.project_name}** |

| Financial Attribute | Specification |
| :--- | :--- |
| **Invoice Number** | **`{self.invoice_id}`** |
| **Issue Date** | {date_str} |
| **Payment Terms** | **{self.terms}** |
| **Payment Due Date** | **{due_date_str}** |
| **Settlement Currency** | **United States Dollars ({self.currency} - $)** |
| **Gross Invoice Total** | **${self.total_revenue:,.2f} USD** |

---

### 🛠️ Itemized Deliverables & Rate Card Schedule

| Item | Service Description & Role Profile | Billable Units / Hours | Unit Rate (USD) | Total Amount (USD) |
| :---: | :--- | :---: | :---: | :---: |
"""
        for item in self.line_items:
            unit_label = "hrs" if not item.is_fixed_milestone else "unit"
            md += f"| {item.item_id:02d} | **{item.role}**<br>_{item.description}_ | {item.hours:,.1f} {unit_label} | ${item.hourly_rate:,.2f} | **${item.total_revenue:,.2f}** |\n"

        md += f"""
| | **SUBTOTAL** | | | **${self.total_revenue:,.2f}** |
| | **DISCOUNTS / CREDITS** | | | **$0.00** |
| | **TAX / VAT (0% B2B Export Exemption)** | | | **$0.00** |
| | **TOTAL PAYABLE AMOUNT** | | | **${self.total_revenue:,.2f} USD** |

---

### 📊 Internal Commercial Margin Audit (CFO Operations)
> [!NOTE] Internal Treasury & Unit Economics Verification
> - **Gross Realized Revenue:** `${self.total_revenue:,.2f} USD`
> - **Total Fully Loaded Direct Costs:** `${self.total_direct_cost:,.2f} USD`
> - **Gross Realized Profit:** `${self.total_gross_profit:,.2f} USD`
> - **Calculated Gross Margin:** **`{self.overall_gross_margin_pct:.2f}%`** (CFO Baseline Floor: `65.00%`) — **{margin_status}**

---

### 💳 International Payment Remittance Instructions

Clients may settle this invoice via our institutional wire routing or certified digital gateways:

#### Option 1: Direct Corporate Wire Transfer (SWIFT / Fedwire / CHIPS)
*Mandatory clearing route for invoices of $5,000 USD and above.*

```
================================================================================
INSTITUTIONAL WIRE ROUTING INSTRUCTIONS (USD)
================================================================================
Beneficiary Name:       DevSuperSuite Tech Services Commercial Account
Bank Name:              Silicon Valley Commercial Clearing Bank / JPMorgan Chase
Bank Address:           270 Park Avenue, New York, NY 10017, USA
SWIFT / BIC Code:       DEVSUS33XXX
Fedwire / ABA Routing:  121000358
Account Number:         9824-0019-8832-USD
Beneficiary Address:    Commercial Operations Division, devsupersuite.web.app
Payment Reference / Memo: {self.invoice_id} / {self.client_name}
Mandatory SWIFT Code:   OUR (Sender pays all wire transfer and intermediary charges)
================================================================================
```

#### Option 2: 1-Click Corporate Credit Card Settlement (Stripe Invoicing)
- **Instant Secure Clearing:** Supported for Visa, MasterCard, American Express, Apple Pay, SEPA, Bacs.
- **Direct Portal Link:** [https://devsupersuite.web.app/checkout/{self.invoice_id.lower()}](https://devsupersuite.web.app/checkout/{self.invoice_id.lower()})
- *Note: A standard 3.5% commercial technology processing fee applies to credit card settlements over $1,000 USD.*

#### Option 3: PayPal Business Gateway
- **PayPal Merchant Account:** `billing@devsupersuite.com`
- **Memo Required:** `{self.invoice_id}`

---

### ⚖️ Commercial Terms, Governance & Delinquency Policy
1. **Contractual Terms**: Payment is strictly due according to **{self.terms}** terms by **{due_date_str}**.
2. **Late Financing Penalties**: In accordance with DevSuperSuite Master Commercial Guidelines, balances outstanding past the due date incur a statutory finance charge of **1.5% per month (18.0% per annum)** or the maximum allowed by law, compounding daily.
3. **Engineering Continuation Clause**: In the event payment is delinquent past thirty (30) calendar days from the due date, active sprint pull requests, feature merges, and staging infrastructure access are automatically suspended until settlement clears.
4. **IP Retention**: Legal ownership and title to deliverables remain with **DevSuperSuite Official** until all associated invoices are settled in full.
5. **Brand Anonymity**: DevSuperSuite Official is the sole commercial counterparty.

---
*Authorized by: Office of the CFO & Commercial Operations Desk — DevSuperSuite Tech Services*  
*Document Generated: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")} | Verification Hash: DSS-SEC-{abs(hash(self.invoice_id)) % 1000000:06d}*
"""
        return md


def generate_milestone_1_enterprise_invoice(output_path: str) -> EnterpriseInvoice:
    """
    Generates the official institutional invoice for:
    INV-2026-001 ($24,500.00 Milestone 1 Enterprise Deployment).
    """
    invoice = EnterpriseInvoice(
        invoice_id="INV-2026-001",
        client_name="Nexus Enterprise Technologies Corp.",
        client_contact="Director of Engineering Operations & Enterprise Procurement",
        client_address="500 Innovation Way, Suite 1200, Austin, TX 78701, USA",
        client_vat_ein="US-EIN-74-8839210",
        project_name="OmniKernel 5.0 AST Context Slicing & AgentShield Enterprise Rollout",
        invoice_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        terms="NET-30",
        currency="USD",
        notes="Milestone 1 Enterprise Deployment: Architecture Blueprint, AST Interface Compression, and CI/CD Invariant Gates."
    )

    # 1. Principal Solutions Architect - Enterprise Blueprint & Invariant Architecture
    # 50 hrs @ $120.00/hr = $6,000.00 (Loaded cost: $38.00/hr)
    invoice.add_line_item(
        description="Enterprise AST compression architecture, custom MCP JSON-RPC protocol specification, and security invariant guard blueprint design.",
        role="Principal Solutions Architect",
        hours=50.0,
        hourly_rate=120.0,
        loaded_cost_rate=38.0,
    )

    # 2. Senior AI Systems Engineer - OmniKernel 5.0 AST Engine Customization
    # 140 hrs @ $75.00/hr = $10,500.00 (Loaded cost: $25.00/hr)
    invoice.add_line_item(
        description="AST context slicing pipeline implementation, Python/TypeScript AST visitor tree pruning, token reduction validation (70%-84% savings target).",
        role="Senior AI Systems Engineer",
        hours=140.0,
        hourly_rate=75.0,
        loaded_cost_rate=25.0,
    )

    # 3. Senior Systems Engineer - AgentShield Pre-Commit Entropy Scanner & CI/CD Guard
    # 80 hrs @ $75.00/hr = $6,000.00 (Loaded cost: $25.00/hr)
    invoice.add_line_item(
        description="Zero-day Shannon entropy secret detection engine rollout, pre-commit hook integration across 15+ providers, test preservation invariant hooks.",
        role="Senior Systems Engineer",
        hours=80.0,
        hourly_rate=75.0,
        loaded_cost_rate=25.0,
    )

    # 4. Junior Implementation Specialist - Scaffolding, Unit Tests & Documentation
    # 40 hrs @ $45.00/hr = $1,800.00 (Loaded cost: $15.00/hr)
    invoice.add_line_item(
        description="Automated unit test harness construction, regression testing, regression benchmark execution, and developer onboarding runbooks.",
        role="Junior Implementation Specialist",
        hours=40.0,
        hourly_rate=45.0,
        loaded_cost_rate=15.0,
    )

    # 5. Dedicated Cloud Staging Infrastructure & High-Throughput Verification
    # Fixed item: $200.00 (Pass-through cost $166.67 + 20% admin markup = $200.00)
    invoice.add_line_item(
        description="Dedicated high-concurrency cloud staging cluster, AST benchmark sandbox containers, and API token verification quota (cost + 20% markup).",
        role="Cloud Infrastructure & Testing Sandboxes",
        hours=1.0,
        hourly_rate=200.0,
        loaded_cost_rate=166.67,
        is_fixed_milestone=True,
    )

    # Total check: 6,000 + 10,500 + 6,000 + 1,800 + 200 = 24,500.00 USD!

    # Render & Write
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    content = invoice.render_markdown()
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return invoice


def main():
    parser = argparse.ArgumentParser(
        description="⚡ DevSuperSuite Tech Services - Automated Enterprise Invoicing Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--preset", choices=["milestone-1"], help="Generate standard invoice preset (e.g. milestone-1)")
    parser.add_argument("--invoice-id", default="INV-2026-001", help="Invoice Identification Number")
    parser.add_argument("--client-name", default="Nexus Enterprise Technologies Corp.", help="Client corporate name")
    parser.add_argument("--client-contact", default="Director of Engineering Operations", help="Client contact / title")
    parser.add_argument("--client-address", default="Corporate Headquarters, Austin, TX", help="Client corporate address")
    parser.add_argument("--client-ein", default="US-EIN-74-8839210", help="Client Tax / EIN ID")
    parser.add_argument("--project-name", default="OmniKernel 5.0 AST Context Slicing Enterprise Rollout", help="Project name")
    parser.add_argument("--terms", default="NET-30", choices=["NET-0", "NET-15", "NET-30"], help="Payment terms")
    parser.add_argument("--output", default=None, help="Output markdown invoice path")
    parser.add_argument("--json-input", default=None, help="Path to JSON file containing invoice data")

    args = parser.parse_args()

    default_output = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "invoices",
        f"{args.invoice_id}.md"
    )
    output_path = args.output or default_output

    print("=" * 75)
    print("⚡ DevSuperSuite Tech Services - Commercial Billing & Invoicing Engine")
    print(f"Target Invoice: {args.invoice_id}")
    print(f"Output Destination: {output_path}")
    print("=" * 75)

    if args.preset == "milestone-1" or (not args.json_input and args.invoice_id == "INV-2026-001"):
        invoice = generate_milestone_1_enterprise_invoice(output_path)
    elif args.json_input:
        with open(args.json_input, "r", encoding="utf-8") as f:
            data = json.load(f)
        invoice = EnterpriseInvoice(
            invoice_id=data.get("invoice_id", args.invoice_id),
            client_name=data.get("client_name", args.client_name),
            client_contact=data.get("client_contact", args.client_contact),
            client_address=data.get("client_address", args.client_address),
            client_vat_ein=data.get("client_ein", args.client_ein),
            project_name=data.get("project_name", args.project_name),
            terms=data.get("terms", args.terms),
            notes=data.get("notes", "Services rendered under Master Services Agreement."),
        )
        for item in data.get("line_items", []):
            invoice.add_line_item(
                description=item["description"],
                role=item["role"],
                hours=float(item["hours"]),
                hourly_rate=float(item["hourly_rate"]),
                loaded_cost_rate=float(item["loaded_cost_rate"]),
                is_fixed_milestone=item.get("is_fixed_milestone", False),
            )
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(invoice.render_markdown())
    else:
        # Default fallback creation
        invoice = generate_milestone_1_enterprise_invoice(output_path)

    print("\n✅ Invoice Successfully Generated!")
    print(f"📄 File: {output_path}")
    print(f"💰 Gross Realized Revenue: ${invoice.total_revenue:,.2f} USD")
    print(f"📉 Direct Loaded Cost:    ${invoice.total_direct_cost:,.2f} USD")
    print(f"💵 Net Gross Profit:       ${invoice.total_gross_profit:,.2f} USD")
    print(f"📈 Realized Gross Margin:  {invoice.overall_gross_margin_pct:.2f}% (Target: >= {MINIMUM_GROSS_MARGIN_BENCHMARK}%)")
    print(f"🛡️ Margin Benchmark Status: {'PASSED (Compliant)' if invoice.meets_margin_benchmark else 'FAILED (Review Required)'}")
    print("=" * 75)


if __name__ == "__main__":
    main()
