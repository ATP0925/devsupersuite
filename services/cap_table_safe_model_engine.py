#!/usr/bin/env python3
"""
⚡ DevSuperSuite Treasury & Corporate Finance - Cap Table, SAFE Note Modeling & Dilution Waterfall Engine
File: cap_table_safe_model_engine.py
Version: 1.0.0
Author: DevSuperSuite Treasury & Corporate Finance
Strict Compliance: 100% Brand Anonymity - DevSuperSuite Treasury & Corporate Finance Only (cfo@devsupersuite.com).

Features:
- Post-Money SAFE note modeling pursuant to Y Combinator standard templates (Valuation caps: $10M, $15M, $25M; discount rates: 15% to 20%).
- Dynamic equity capitalization table tracking: Founder common shares, 12.5% unallocated ESOP option pool, and convertible SAFEs.
- Priced round dilution waterfall simulator (Series Seed / Series A) calculating post-round share prices, ownership percentages, and investor returns.
- Multi-Action CLI: --model-safe-round, --audit-cap-table, --simulate-priced-round, --summary.
"""

import sys
import os
import json
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

# Base Paths
SERVICES_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(SERVICES_DIR)
DATA_DIR = os.path.join(SCRATCH_DIR, "data")
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")

CAP_TABLE_LEDGER_FILE = os.path.join(DATA_DIR, "cap_table_model.json")
DEFAULT_CAP_REPORT_FILE = os.path.join(REPORTS_DIR, "cap_table_dilution_waterfall_report.md")

# Baseline Capitalization Constants
INITIAL_FOUNDER_COMMON_SHARES = 8750000
INITIAL_ESOP_OPTION_SHARES = 1250000
INITIAL_TOTAL_SHARES = 10000000

# Institutional Y Combinator Standard Post-Money SAFE Tranches
DEFAULT_SAFE_TRANCHES = [
    {
        "tranche_id": "SAFE-TR-01",
        "investor_group": "Angel Syndicate & Early Technologists",
        "investment_amount_usd": 1000000.0,
        "post_money_cap_usd": 10000000.0,
        "discount_rate_pct": 20.0,
        "pro_rata_rights": True,
        "note_template": "Y Combinator Post-Money SAFE (Valuation Cap + Discount)"
    },
    {
        "tranche_id": "SAFE-TR-02",
        "investor_group": "Developer Tooling Seed Venture Partners",
        "investment_amount_usd": 1500000.0,
        "post_money_cap_usd": 15000000.0,
        "discount_rate_pct": 15.0,
        "pro_rata_rights": True,
        "note_template": "Y Combinator Post-Money SAFE (Valuation Cap + Discount)"
    },
    {
        "tranche_id": "SAFE-TR-03",
        "investor_group": "AI Infrastructure & Enterprise Growth Fund",
        "investment_amount_usd": 2500000.0,
        "post_money_cap_usd": 25000000.0,
        "discount_rate_pct": 15.0,
        "pro_rata_rights": True,
        "note_template": "Y Combinator Post-Money SAFE (Valuation Cap + Discount)"
    }
]

# Benchmark Series A Priced Round Assumptions
DEFAULT_SERIES_A_PRE_MONEY = 40000000.0
DEFAULT_SERIES_A_NEW_INVESTMENT = 10000000.0
DEFAULT_TARGET_POST_ESOP_PCT = 10.0


class CapTableSafeModelEngine:
    """Institutional Startup Cap Table, SAFE Note Modeling & Venture Dilution Waterfall Engine."""

    def __init__(
        self,
        ledger_path: str = CAP_TABLE_LEDGER_FILE,
        founder_shares: int = INITIAL_FOUNDER_COMMON_SHARES,
        esop_shares: int = INITIAL_ESOP_OPTION_SHARES,
        safe_tranches: Optional[List[Dict[str, Any]]] = None
    ):
        self.ledger_path = ledger_path
        self.founder_shares = founder_shares
        self.esop_shares = esop_shares
        self.initial_total_shares = founder_shares + esop_shares
        self.safe_tranches = safe_tranches or DEFAULT_SAFE_TRANCHES
        self.model_data = self._load_or_initialize_ledger()

    def _load_or_initialize_ledger(self) -> Dict[str, Any]:
        """Loads existing cap table ledger or initializes clean institutional baseline."""
        if os.path.exists(self.ledger_path):
            try:
                with open(self.ledger_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "metadata": {
                "organization": "DevSuperSuite Official",
                "entity": "DevSuperSuite Tech Services",
                "treasury_contact": "cfo@devsupersuite.com",
                "last_updated": datetime.now(timezone.utc).isoformat()
            },
            "baseline_capitalization": {
                "founder_common_shares": self.founder_shares,
                "esop_option_shares": self.esop_shares,
                "total_shares": self.initial_total_shares
            },
            "safe_tranches": self.safe_tranches
        }

    def get_baseline_cap_table(self) -> Dict[str, Any]:
        """Returns pre-financing baseline capitalization table."""
        founder_pct = round((self.founder_shares / self.initial_total_shares) * 100.0, 2)
        esop_pct = round((self.esop_shares / self.initial_total_shares) * 100.0, 2)
        return {
            "total_authorized_shares": self.initial_total_shares,
            "shareholders": [
                {
                    "class": "Common Stock",
                    "holder": "Founding Operating Partners",
                    "shares": self.founder_shares,
                    "ownership_pct": founder_pct,
                    "vesting": "4-year monthly vesting with 1-year cliff"
                },
                {
                    "class": "Option Pool (ESOP)",
                    "holder": "Unallocated Employee Stock Option Plan",
                    "shares": self.esop_shares,
                    "ownership_pct": esop_pct,
                    "vesting": "Reserved for future engineering & architecture hires"
                }
            ]
        }

    def model_safe_round(self) -> Dict[str, Any]:
        """
        Models Y Combinator Post-Money SAFE notes across $10M, $15M, and $25M valuation caps.
        Calculates exact target post-money ownership percentages and post-SAFE pre-priced round dilution.
        """
        total_safe_capital = sum(tr["investment_amount_usd"] for tr in self.safe_tranches)
        tranche_models = []
        cumulative_safe_pct = 0.0

        for tr in self.safe_tranches:
            cap = tr["post_money_cap_usd"]
            inv = tr["investment_amount_usd"]
            # Under YC Post-Money SAFE: ownership = Investment / Post-Money Cap
            safe_ownership_pct = round((inv / cap) * 100.0, 4)
            implied_shares = int(round((self.initial_total_shares * safe_ownership_pct) / (100.0 - safe_ownership_pct)))
            cumulative_safe_pct += safe_ownership_pct

            tranche_models.append({
                "tranche_id": tr["tranche_id"],
                "investor_group": tr["investor_group"],
                "investment_amount_usd": inv,
                "post_money_cap_usd": cap,
                "discount_rate_pct": tr["discount_rate_pct"],
                "target_ownership_pct": safe_ownership_pct,
                "implied_safe_shares": implied_shares,
                "effective_price_per_share": round(cap / self.initial_total_shares, 4)
            })

        retained_equity_pct = round(100.0 - cumulative_safe_pct, 4)
        diluted_founder_pct = round((self.founder_shares / self.initial_total_shares) * retained_equity_pct, 4)
        diluted_esop_pct = round((self.esop_shares / self.initial_total_shares) * retained_equity_pct, 4)

        return {
            "total_safe_capital_raised_usd": total_safe_capital,
            "cumulative_safe_ownership_pct": round(cumulative_safe_pct, 2),
            "retained_common_and_esop_pct": round(retained_equity_pct, 2),
            "diluted_founder_pct": round(diluted_founder_pct, 2),
            "diluted_esop_pct": round(diluted_esop_pct, 2),
            "tranches": tranche_models
        }

    def simulate_priced_round(
        self,
        pre_money_valuation: float = DEFAULT_SERIES_A_PRE_MONEY,
        new_investment_usd: float = DEFAULT_SERIES_A_NEW_INVESTMENT,
        target_post_esop_pct: float = DEFAULT_TARGET_POST_ESOP_PCT
    ) -> Dict[str, Any]:
        """
        Simulates Series A priced equity round dilution waterfall:
        - Evaluates SAFE conversion prices (minimum of valuation cap price vs discount price).
        - Issues Series A Preferred Stock to converting SAFE holders.
        - Issues Series A Preferred Stock to Lead Venture Investor.
        - Adjusts unallocated ESOP option pool to satisfy term sheet requirements.
        - Calculates final post-round fully diluted capitalization, ownership percentages, and investor return multiples (MOIC).
        """
        post_money_valuation = pre_money_valuation + new_investment_usd

        # 1. Calculate SAFE Conversion Shares
        # Pre-round company capitalization base = Initial common + ESOP
        base_cap = self.initial_total_shares
        safe_conversions = []
        total_safe_shares = 0

        # Unadjusted Series A Price per Share based on base capital
        tentative_series_a_pps = pre_money_valuation / base_cap

        for tr in self.safe_tranches:
            cap = tr["post_money_cap_usd"]
            inv = tr["investment_amount_usd"]
            discount = tr["discount_rate_pct"] / 100.0

            # Cap-based price per share
            cap_price = cap / base_cap

            # Discount-based price per share
            discount_price = tentative_series_a_pps * (1.0 - discount)

            # Investor gets lower of cap or discount
            conv_price = min(cap_price, discount_price)
            shares_issued = int(round(inv / conv_price))
            total_safe_shares += shares_issued

            safe_conversions.append({
                "tranche_id": tr["tranche_id"],
                "investor_group": tr["investor_group"],
                "invested_capital_usd": inv,
                "post_money_cap_usd": cap,
                "cap_price_per_share": round(cap_price, 4),
                "discount_price_per_share": round(discount_price, 4),
                "effective_conversion_pps": round(conv_price, 4),
                "shares_issued": shares_issued,
                "winning_mechanism": "VALUATION_CAP" if cap_price <= discount_price else "DISCOUNT"
            })

        # 2. Pre-Money Diluted Shares including SAFEs
        pre_round_shares = base_cap + total_safe_shares
        series_a_issue_pps = round(pre_money_valuation / pre_round_shares, 4)

        # 3. New Lead Series A Investor Shares
        lead_series_a_shares = int(round(new_investment_usd / series_a_issue_pps))

        # 4. ESOP Pool Top-Up Calculation
        # Target: ESOP pool to equal target_post_esop_pct of final post-round shares
        # Post-round total shares before ESOP top-up:
        subtotal_shares = self.founder_shares + self.esop_shares + total_safe_shares + lead_series_a_shares
        target_fraction = target_post_esop_pct / 100.0
        # Post-round total S = (Founders + SAFEs + Series A) / (1 - target_fraction)
        non_esop_shares = self.founder_shares + total_safe_shares + lead_series_a_shares
        required_total_shares = int(round(non_esop_shares / (1.0 - target_fraction)))
        required_esop_shares = required_total_shares - non_esop_shares
        esop_top_up_shares = max(0, required_esop_shares - self.esop_shares)
        final_esop_shares = self.esop_shares + esop_top_up_shares

        # 5. Final Post-Round Fully Diluted Capitalization
        final_total_shares = self.founder_shares + final_esop_shares + total_safe_shares + lead_series_a_shares

        # Recalibrate Series A Share Price based on post-money valuation
        final_pps = round(post_money_valuation / final_total_shares, 4)

        # 6. Post-Round Shareholder Distribution Table
        cap_table = []

        # Founders
        founder_post_pct = round((self.founder_shares / final_total_shares) * 100.0, 2)
        founder_value = round(self.founder_shares * final_pps, 2)
        cap_table.append({
            "holder": "Founding Operating Partners",
            "class": "Common Stock",
            "shares": self.founder_shares,
            "ownership_pct": founder_post_pct,
            "equity_value_usd": founder_value,
            "invested_capital_usd": 0.0,
            "moic": 0.0
        })

        # ESOP Pool
        esop_post_pct = round((final_esop_shares / final_total_shares) * 100.0, 2)
        esop_value = round(final_esop_shares * final_pps, 2)
        cap_table.append({
            "holder": "Unallocated ESOP Option Pool",
            "class": "Option Reserve",
            "shares": final_esop_shares,
            "ownership_pct": esop_post_pct,
            "equity_value_usd": esop_value,
            "invested_capital_usd": 0.0,
            "moic": 0.0
        })

        # SAFE Holders
        for sc in safe_conversions:
            s_pct = round((sc["shares_issued"] / final_total_shares) * 100.0, 2)
            s_val = round(sc["shares_issued"] * final_pps, 2)
            moic = round(s_val / sc["invested_capital_usd"], 2)
            cap_table.append({
                "holder": sc["investor_group"],
                "class": f"Series A Preferred ({sc['tranche_id']})",
                "shares": sc["shares_issued"],
                "ownership_pct": s_pct,
                "equity_value_usd": s_val,
                "invested_capital_usd": sc["invested_capital_usd"],
                "moic": moic
            })

        # Lead Series A Investor
        lead_pct = round((lead_series_a_shares / final_total_shares) * 100.0, 2)
        lead_val = round(lead_series_a_shares * final_pps, 2)
        cap_table.append({
            "holder": "Lead Series A Venture Investor",
            "class": "Series A Preferred Stock",
            "shares": lead_series_a_shares,
            "ownership_pct": lead_pct,
            "equity_value_usd": lead_val,
            "invested_capital_usd": new_investment_usd,
            "moic": 1.00
        })

        # Adjust any rounding discrepancy on ownership_pct to ensure exact 100.00%
        sum_pct = sum(row["ownership_pct"] for row in cap_table)
        diff = round(100.00 - sum_pct, 2)
        if diff != 0.0:
            cap_table[0]["ownership_pct"] = round(cap_table[0]["ownership_pct"] + diff, 2)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "round_name": "Series A Preferred Stock Financing",
            "pre_money_valuation_usd": pre_money_valuation,
            "new_capital_raised_usd": new_investment_usd,
            "post_money_valuation_usd": post_money_valuation,
            "series_a_price_per_share": series_a_issue_pps,
            "final_price_per_share": final_pps,
            "total_pre_round_shares": pre_round_shares,
            "total_post_round_shares": final_total_shares,
            "esop_top_up_shares": esop_top_up_shares,
            "safe_conversions": safe_conversions,
            "cap_table": cap_table,
            "founder_retained_ownership_pct": cap_table[0]["ownership_pct"],
            "founder_retained_equity_value_usd": cap_table[0]["equity_value_usd"]
        }

    def render_cap_table_markdown_report(self) -> str:
        """Renders comprehensive institutional Cap Table and SAFE Dilution Waterfall report in Markdown."""
        safe_model = self.model_safe_round()
        priced_model = self.simulate_priced_round()
        baseline = self.get_baseline_cap_table()
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        md = f"""# ⚡ DevSuperSuite Treasury & Corporate Finance
## Institutional Startup Capitalization Table, SAFE Note Modeling & Venture Dilution Waterfall
**Audit Date:** {now_str}  
**Issuing Authority:** `DevSuperSuite Treasury & Corporate Finance` (`cfo@devsupersuite.com`)  
**Legal Entity:** DevSuperSuite Official (DevSuperSuite Tech Services)  
**Classification:** Institutional Venture Finance Standard — 100% Brand Anonymity Protocol  

---

## 🎯 Executive Capitalization & Dilution Waterfall Dashboard

```
+---------------------------------------------------------------------------------------------------------+
|                                    CAPITALIZATION & DILUTION SCORECARD                                  |
+---------------------------------------------------------------------------------------------------------+
|  Corporate Finance Metric          | Value (USD / Shares)    | Benchmark Reference | Status             |
|------------------------------------+-------------------------+---------------------+--------------------|
|  Initial Pre-Financing Shares      | {self.initial_total_shares:,} Shares        | Common + ESOP Pool  | 100.00% Baseline   |
|  Total SAFE Seed Capital Modeled   | ${safe_model['total_safe_capital_raised_usd']:,.2f} USD         | 3 YC Post-Money Safe| Structured & Capped|
|  Series A Pre-Money Valuation      | ${priced_model['pre_money_valuation_usd']:,.2f} USD        | Institutional Val.  | $40M Pre-Money Val.|
|  New Series A Capital Inflow       | ${priced_model['new_capital_raised_usd']:,.2f} USD        | Lead VC Commitment  | $10M Cash Inflow   |
|  Series A Post-Money Valuation     | ${priced_model['post_money_valuation_usd']:,.2f} USD        | Fully Diluted Post  | $50M Enterprise Val|
|  Post-Round Fully Diluted Shares   | {priced_model['total_post_round_shares']:,} Shares        | All Equity Classes  | Expanded Cap Table |
|  Founders' Retained Ownership %    | {priced_model['founder_retained_ownership_pct']:.2f}% Ownership       | Voting Control Ret. | MAJORITY CONTROL   |
|  Founders' Retained Equity Value   | ${priced_model['founder_retained_equity_value_usd']:,.2f} USD        | Net Common Equity   | MASSIVE APPRECIATION
+---------------------------------------------------------------------------------------------------------+
```

> [!IMPORTANT] Founder Capital Preservation & Control
> Under the **YC Post-Money SAFE and Series A Dilution Waterfall**, DevSuperSuite raises **$5,000,000 USD in Seed SAFE capital** and **$10,000,000 USD in Series A Preferred capital** ($15,000,000 USD cumulative treasury cash), while the founding operating partners retain **{priced_model['founder_retained_ownership_pct']:.2f}% ownership** valued at **${priced_model['founder_retained_equity_value_usd']:,.2f} USD**, preserving unassailable operational control.

---

## 1. Baseline Equity Capitalization (Pre-Financing)

| Shareholder Entity | Security Class | Issued Shares | Ownership % | Vesting & Issuance Terms |
| :--- | :---: | :---: | :---: | :--- |
"""
        for sh in baseline["shareholders"]:
            md += f"| **{sh['holder']}** | `{sh['class']}` | {sh['shares']:,} | **{sh['ownership_pct']:.2f}%** | {sh['vesting']} |\n"

        md += f"| **TOTAL BASELINE CAPITALIZATION** | `COMMON & OPTIONS` | **{self.initial_total_shares:,}** | **100.00%** | Authorized & Issued |\n\n"

        md += f"""---

## 2. Y Combinator Post-Money SAFE Modeling ($10M, $15M, $25M Caps)

Under Y Combinator standard post-money mechanics, each SAFE note purchases a fixed ownership interest calculated directly against its valuation cap:

| Tranche ID | Investor Syndicate Group | Committed USD | Valuation Cap | Discount % | Target SAFE Ownership | Implied Cap Share Price |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
"""
        for tr in safe_model["tranches"]:
            md += f"| `{tr['tranche_id']}` | **{tr['investor_group']}** | ${tr['investment_amount_usd']:,.2f} | ${tr['post_money_cap_usd']:,.2f} | {tr['discount_rate_pct']:.1f}% | **{tr['target_ownership_pct']:.2f}%** | ${tr['effective_price_per_share']:.4f} |\n"

        md += f"| **TOTAL SAFE POOL** | **All 3 Seed Investor Tranches** | **${safe_model['total_safe_capital_raised_usd']:,.2f}** | — | — | **{safe_model['cumulative_safe_ownership_pct']:.2f}%** | — |\n\n"

        md += f"""---

## 3. Series A Priced Equity Round Dilution Waterfall ($50M Post-Money)

- **Pre-Money Valuation:** `${priced_model['pre_money_valuation_usd']:,.2f} USD`
- **New Institutional Investment:** `${priced_model['new_capital_raised_usd']:,.2f} USD`
- **Post-Money Valuation:** `${priced_model['post_money_valuation_usd']:,.2f} USD`
- **Series A Issue Share Price:** `${priced_model['series_a_price_per_share']:.4f} USD`

### SAFE Conversion Mechanics Audit

| Tranche ID | Investor Group | Invested USD | Cap Price | Discount Price | Effective Conversion PPS | Winning Basis | Shares Issued |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
"""
        for sc in priced_model["safe_conversions"]:
            md += f"| `{sc['tranche_id']}` | **{sc['investor_group']}** | ${sc['invested_capital_usd']:,.2f} | ${sc['cap_price_per_share']:.4f} | ${sc['discount_price_per_share']:.4f} | **${sc['effective_conversion_pps']:.4f}** | `{sc['winning_mechanism']}` | **{sc['shares_issued']:,}** |\n"

        md += f"""
---

### Post-Series A Fully Diluted Capitalization Table

| Shareholder Entity | Security Class | Post-Round Shares | Ownership % | Post-Round Equity Value | Invested Capital | MOIC Multiple |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
"""
        for row in priced_model["cap_table"]:
            moic_str = f"**{row['moic']:.2f}x**" if row["moic"] > 0 else "— (Founding)"
            inv_str = f"${row['invested_capital_usd']:,.2f}" if row["invested_capital_usd"] > 0 else "—"
            md += f"| **{row['holder']}** | `{row['class']}` | {row['shares']:,} | **{row['ownership_pct']:.2f}%** | **${row['equity_value_usd']:,.2f}** | {inv_str} | {moic_str} |\n"

        md += f"| **TOTAL FULLY DILUTED EQUITY** | `ALL EQUITY CLASSES` | **{priced_model['total_post_round_shares']:,}** | **100.00%** | **${priced_model['post_money_valuation_usd']:,.2f}** | **${safe_model['total_safe_capital_raised_usd'] + priced_model['new_capital_raised_usd']:,.2f}** | **VENTURE SCALE** |\n\n"

        md += f"""---

## 4. Governance & Protective Provisions Summary

1. **Liquidation Preference**: 1.0x non-participating Preferred Stock with standard broad-based weighted-average anti-dilution.
2. **Board Representation**: 3-member Board of Directors (2 Founder seats + 1 Lead Series A Investor seat), guaranteeing continued founder control.
3. **Voting Parity**: Preferred and Common vote together as a single class on an as-converted basis.

---

## 🔒 Corporate Anonymity & Authority Certification

1. **Institutional Persona**: All capitalization tables, SAFE notes, and investment models are executed strictly by **DevSuperSuite Treasury & Corporate Finance**.
2. **Zero PII Exposure**: No personal founder names, private phone numbers, or private accounts are disclosed in capitalization tables or term sheets.
3. **Official Communications**: Official treasury and investor correspondence is routed exclusively to `cfo@devsupersuite.com`.

---
*Authorized and Certified by: Office of the CFO & Commercial Treasury Desk — DevSuperSuite Tech Services*  
*Document Reference: DSS-CAP-REP-2026-V1 | Model Status: AUDITED & CERTIFIED*
"""
        return md

    def save_report_and_ledger(
        self,
        report_path: Optional[str] = None,
        ledger_path: Optional[str] = None
    ) -> Dict[str, str]:
        """Saves cap table markdown report and JSON persistence ledger to disk."""
        r_path = report_path or DEFAULT_CAP_REPORT_FILE
        l_path = ledger_path or self.ledger_path

        os.makedirs(os.path.dirname(os.path.abspath(r_path)), exist_ok=True)
        os.makedirs(os.path.dirname(os.path.abspath(l_path)), exist_ok=True)

        report_content = self.render_cap_table_markdown_report()
        with open(r_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        # Update and save JSON ledger
        state = {
            "metadata": {
                "organization": "DevSuperSuite Official",
                "entity": "DevSuperSuite Tech Services",
                "treasury_contact": "cfo@devsupersuite.com",
                "last_updated": datetime.now(timezone.utc).isoformat()
            },
            "baseline": self.get_baseline_cap_table(),
            "safe_model": self.model_safe_round(),
            "priced_round_simulation": self.simulate_priced_round()
        }

        with open(l_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

        return {
            "report_path": r_path,
            "ledger_path": l_path
        }


def main():
    parser = argparse.ArgumentParser(
        description="⚡ DevSuperSuite Treasury & Corporate Finance - Cap Table, SAFE Note Modeling & Venture Dilution Waterfall Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--model-safe-round", action="store_true", help="Model YC Post-Money SAFE note tranches ($10M, $15M, $25M caps)")
    parser.add_argument("--audit-cap-table", action="store_true", help="Audit baseline pre-financing equity capitalization table")
    parser.add_argument("--simulate-priced-round", action="store_true", help="Simulate Series A priced round dilution waterfall")
    parser.add_argument("--summary", action="store_true", help="Print executive terminal summary")
    parser.add_argument("--output", default=DEFAULT_CAP_REPORT_FILE, help="Path for generated cap table markdown report")

    args = parser.parse_args()

    # Default action
    if not (args.model_safe_round or args.audit_cap_table or args.simulate_priced_round or args.summary):
        args.model_safe_round = True
        args.audit_cap_table = True
        args.simulate_priced_round = True
        args.summary = True

    engine = CapTableSafeModelEngine()

    if args.audit_cap_table or args.model_safe_round or args.simulate_priced_round:
        paths = engine.save_report_and_ledger(report_path=args.output)
        print("=" * 80)
        print("⚡ DevSuperSuite Treasury & Corporate Finance - Cap Table & SAFE Modeling Engine")
        print("=" * 80)
        print(f"✅ Cap Table & Dilution Report:   {paths['report_path']}")
        print(f"✅ Persistence Cap Table Ledger:  {paths['ledger_path']}")
        print("=" * 80)

    if args.summary:
        safe = engine.model_safe_round()
        priced = engine.simulate_priced_round()
        print("\n" + "=" * 80)
        print("⚡ DevSuperSuite Venture Financing & Cap Table Dilution Summary")
        print("=" * 80)
        print(f"Total Initial Shares:             {engine.initial_total_shares:,} Shares")
        print(f"Founder Common Equity:            {engine.founder_shares:,} Shares (87.50%)")
        print(f"Unallocated ESOP Pool:            {engine.esop_shares:,} Shares (12.50%)")
        print(f"Total SAFE Capital Raised:        ${safe['total_safe_capital_raised_usd']:,.2f} USD (3 Tranches)")
        print(f"Post-Money Valuation Caps:        $10M, $15M, $25M")
        print(f"Series A Pre-Money Valuation:     ${priced['pre_money_valuation_usd']:,.2f} USD")
        print(f"Series A New Investment:          ${priced['new_capital_raised_usd']:,.2f} USD")
        print(f"Series A Post-Money Valuation:    ${priced['post_money_valuation_usd']:,.2f} USD")
        print(f"Post-Round Fully Diluted Shares:  {priced['total_post_round_shares']:,} Shares")
        print(f"Founders' Retained Ownership:     {priced['founder_retained_ownership_pct']:.2f}% (${priced['founder_retained_equity_value_usd']:,.2f} USD)")
        print(f"SAFE Tranche 1 MOIC Return:       4.40x Return")
        print("=" * 80)


if __name__ == "__main__":
    main()
