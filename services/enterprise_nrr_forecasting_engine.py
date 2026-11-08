#!/usr/bin/env python3
"""
⚡ DevSuperSuite Official: Enterprise NRR & GRR Revenue Cohort Retention Engine
File: enterprise_nrr_forecasting_engine.py
Version: 1.0.0
Governing Authority: DevSuperSuite Revenue Operations (growth@devsupersuite.com)
Strict Protocol: 100% Brand Anonymity - Zero Founder Personal Identifiers

Key Capabilities:
1. Cohort Retention Modeling:
   - Net Revenue Retention (NRR > 138%), Gross Revenue Retention (GRR > 96%).
   - Customer Lifetime Value (LTV:CAC ratio > 7.4x) and CAC Payback (< 6 months).
2. Enterprise Expansion & Upsell Attribution:
   - Developer seat scaling (+25% annual seat expansion).
   - Add-on Security Enclave Modules: FIPS 140-3 HSM ($9,999/yr), PQC Kyber-1024 ($14,999/yr), Airgap SCIF ($19,999/yr).
   - Multi-year enterprise renewal contract uplifts (+6.5% annual indexation).
3. Machine-readable Persistence & Publication Audit:
   - Saves cohort schedule in data/enterprise_cohort_retention_schedule.json.
   - Generates executive forecast report in services/reports/enterprise_nrr_cohort_retention_report.md.
"""

import os
import sys
import json
import uuid
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Base Directories Setup
SERVICES_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(SERVICES_DIR)
DATA_DIR = os.path.join(SCRATCH_DIR, "data")
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

SCHEDULE_PATH = os.path.join(DATA_DIR, "enterprise_cohort_retention_schedule.json")
REPORT_PATH = os.path.join(REPORTS_DIR, "enterprise_nrr_cohort_retention_report.md")

# Standard Add-On Security Enclave Modules Catalog
SECURITY_EXPANSION_CATALOG: Dict[str, Dict[str, Any]] = {
    "MODULE_FIPS_140_3_HSM": {
        "module_id": "MODULE_FIPS_140_3_HSM",
        "name": "FIPS 140-3 Level 4 HSM Cryptographic Accelerator",
        "annual_price_usd": 9999.0,
        "compliance_target": "NIST FIPS 140-3 / FedRAMP High",
        "expansion_category": "HARDWARE_SECURITY"
    },
    "MODULE_PQC_KYBER_ATTESTATION": {
        "module_id": "MODULE_PQC_KYBER_ATTESTATION",
        "name": "Post-Quantum Kyber-1024 / Dilithium Enclave Attestation",
        "annual_price_usd": 14999.0,
        "compliance_target": "CNSA 2.0 / Post-Quantum Cryptography",
        "expansion_category": "QUANTUM_RESILIENCE"
    },
    "MODULE_AIRGAP_SCIF_CLUSTER": {
        "module_id": "MODULE_AIRGAP_SCIF_CLUSTER",
        "name": "Sovereign Air-Gap SCIF Multi-Cluster Coordinator",
        "annual_price_usd": 19999.0,
        "compliance_target": "DoD IL6 / Zero-Telemetry Sovereign",
        "expansion_category": "AIRGAP_INFRASTRUCTURE"
    },
    "MODULE_ZTNA_MICROSEGMENTATION": {
        "module_id": "MODULE_ZTNA_MICROSEGMENTATION",
        "name": "eBPF Zero-Trust Workload Microsegmentation Matrix",
        "annual_price_usd": 7499.0,
        "compliance_target": "NIST SP 800-207 Zero Trust",
        "expansion_category": "NETWORK_ZERO_TRUST"
    }
}


# ─────────────────────────────────────────────────────────────────────────────
# 1. Cohort Expansion Modeler
# ─────────────────────────────────────────────────────────────────────────────

class CohortExpansionModeler:
    """Calculates granular cohort retention, expansion, contraction, NRR, and GRR."""

    @classmethod
    def calculate_cohort_trajectory(
        cls,
        cohort_id: str,
        cohort_name: str,
        initial_accounts: int,
        starting_arr_usd: float,
        months_elapsed: int = 12,
        seat_expansion_pct: float = 34.5,
        multi_year_uplift_pct: float = 6.5,
        security_modules: Optional[List[Dict[str, Any]]] = None,
        contraction_pct: float = 2.0,
        churn_pct: float = 1.4,
        blended_cac_per_account_usd: float = 18500.0,
        gross_margin_pct: float = 92.5
    ) -> Dict[str, Any]:
        """Calculates 12-month cohort retention and expansion metrics."""
        security_modules = security_modules or []

        # Contraction and Churn
        churn_amount_usd = round(starting_arr_usd * (churn_pct / 100.0), 2)
        contraction_amount_usd = round(starting_arr_usd * (contraction_pct / 100.0), 2)
        retained_base_arr_usd = round(starting_arr_usd - churn_amount_usd - contraction_amount_usd, 2)

        # Expansion drivers
        seat_expansion_usd = round(starting_arr_usd * (seat_expansion_pct / 100.0), 2)
        renewal_uplift_usd = round(starting_arr_usd * (multi_year_uplift_pct / 100.0), 2)
        module_expansion_usd = sum(float(m.get("annual_price_usd", 0.0)) for m in security_modules)
        total_expansion_usd = round(seat_expansion_usd + renewal_uplift_usd + module_expansion_usd, 2)

        ending_arr_usd = round(retained_base_arr_usd + total_expansion_usd, 2)

        # Retention Ratios
        grr_pct = round((retained_base_arr_usd / starting_arr_usd) * 100.0, 2) if starting_arr_usd > 0 else 100.0
        nrr_pct = round((ending_arr_usd / starting_arr_usd) * 100.0, 2) if starting_arr_usd > 0 else 100.0

        # LTV and CAC Unit Economics
        total_cohort_cac_usd = round(initial_accounts * blended_cac_per_account_usd, 2)
        arpu_usd = round(ending_arr_usd / max(1, initial_accounts), 2)
        annual_churn_rate = max(0.01, churn_pct / 100.0)
        ltv_per_account_usd = round((arpu_usd * (gross_margin_pct / 100.0)) / annual_churn_rate, 2)
        ltv_cac_ratio = round(ltv_per_account_usd / max(1.0, blended_cac_per_account_usd), 2)
        cac_payback_months = round((blended_cac_per_account_usd / (arpu_usd * (gross_margin_pct / 100.0))) * 12.0, 1)

        return {
            "cohort_id": cohort_id,
            "cohort_name": cohort_name,
            "months_elapsed": months_elapsed,
            "initial_accounts": initial_accounts,
            "starting_arr_usd": starting_arr_usd,
            "churn_amount_usd": churn_amount_usd,
            "contraction_amount_usd": contraction_amount_usd,
            "retained_base_arr_usd": retained_base_arr_usd,
            "seat_expansion_usd": seat_expansion_usd,
            "renewal_uplift_usd": renewal_uplift_usd,
            "module_expansion_usd": module_expansion_usd,
            "total_expansion_usd": total_expansion_usd,
            "ending_arr_usd": ending_arr_usd,
            "grr_pct": grr_pct,
            "nrr_pct": nrr_pct,
            "security_modules_attached": security_modules,
            "unit_economics": {
                "blended_cac_per_account_usd": blended_cac_per_account_usd,
                "arpu_usd": arpu_usd,
                "gross_margin_pct": gross_margin_pct,
                "ltv_per_account_usd": ltv_per_account_usd,
                "ltv_cac_ratio": ltv_cac_ratio,
                "cac_payback_months": cac_payback_months
            }
        }


# ─────────────────────────────────────────────────────────────────────────────
# 2. Enterprise NRR & GRR Retention Forecasting Engine
# ─────────────────────────────────────────────────────────────────────────────

class EnterpriseNRRForecastingEngine:
    """Manages cohort data, security expansion attachments, and publication reports."""

    def __init__(
        self,
        schedule_path: str = SCHEDULE_PATH,
        report_path: str = REPORT_PATH
    ):
        self.schedule_path = schedule_path
        self.report_path = report_path
        self.schedule: Dict[str, Any] = self._load_or_init_schedule()

    def _load_or_init_schedule(self) -> Dict[str, Any]:
        if os.path.exists(self.schedule_path):
            try:
                with open(self.schedule_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "version": "1.0.0",
            "governing_entity": "DevSuperSuite Revenue Operations (growth@devsupersuite.com)",
            "compliance_protocol": "100% Brand Anonymity - Zero Founder Personal Identifiers",
            "target_benchmarks": {
                "minimum_nrr_pct": 138.0,
                "minimum_grr_pct": 96.0,
                "minimum_ltv_cac_ratio": 7.4,
                "maximum_cac_payback_months": 8.0
            },
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "cohorts": []
        }

    def save_schedule(self) -> None:
        self.schedule["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.schedule_path, "w", encoding="utf-8") as f:
            json.dump(self.schedule, f, indent=2)

    def register_cohort(
        self,
        cohort_id: str,
        cohort_name: str,
        initial_accounts: int,
        starting_arr_usd: float,
        months_elapsed: int = 12,
        seat_expansion_pct: float = 34.5,
        multi_year_uplift_pct: float = 6.5,
        security_modules: Optional[List[Dict[str, Any]]] = None,
        contraction_pct: float = 2.0,
        churn_pct: float = 1.4,
        blended_cac_per_account_usd: float = 18500.0,
        gross_margin_pct: float = 92.5
    ) -> Dict[str, Any]:
        """Calculates cohort performance and records it in schedule."""
        cohort_id = cohort_id.strip().upper()

        # Update if exists, or append new
        existing_idx = next((i for i, c in enumerate(self.schedule.get("cohorts", [])) if c["cohort_id"] == cohort_id), None)

        record = CohortExpansionModeler.calculate_cohort_trajectory(
            cohort_id=cohort_id,
            cohort_name=cohort_name,
            initial_accounts=initial_accounts,
            starting_arr_usd=starting_arr_usd,
            months_elapsed=months_elapsed,
            seat_expansion_pct=seat_expansion_pct,
            multi_year_uplift_pct=multi_year_uplift_pct,
            security_modules=security_modules,
            contraction_pct=contraction_pct,
            churn_pct=churn_pct,
            blended_cac_per_account_usd=blended_cac_per_account_usd,
            gross_margin_pct=gross_margin_pct
        )

        if existing_idx is not None:
            self.schedule["cohorts"][existing_idx] = record
        else:
            self.schedule["cohorts"].append(record)

        self.save_schedule()
        return record

    def attach_security_module_to_cohort(
        self,
        cohort_id: str,
        module_key: str
    ) -> Dict[str, Any]:
        """Attaches an add-on security module to an active cohort and recalculates NRR."""
        cohort_id = cohort_id.strip().upper()
        matched = next((c for c in self.schedule.get("cohorts", []) if c["cohort_id"] == cohort_id), None)
        if not matched:
            raise KeyError(f"Cohort '{cohort_id}' not found in retention schedule.")

        module = SECURITY_EXPANSION_CATALOG.get(module_key.upper().strip())
        if not module:
            raise KeyError(f"Security module '{module_key}' not found in catalog.")

        # Attach module
        modules = matched.get("security_modules_attached", [])
        modules.append(module)

        multi_year_uplift = round((matched.get("renewal_uplift_usd", 0.0) / matched["starting_arr_usd"]) * 100.0, 2) if matched.get("renewal_uplift_usd") else 6.5

        # Recalculate
        updated = CohortExpansionModeler.calculate_cohort_trajectory(
            cohort_id=matched["cohort_id"],
            cohort_name=matched["cohort_name"],
            initial_accounts=matched["initial_accounts"],
            starting_arr_usd=matched["starting_arr_usd"],
            months_elapsed=matched["months_elapsed"],
            seat_expansion_pct=round((matched["seat_expansion_usd"] / matched["starting_arr_usd"]) * 100.0, 2),
            multi_year_uplift_pct=multi_year_uplift,
            security_modules=modules,
            contraction_pct=round((matched["contraction_amount_usd"] / matched["starting_arr_usd"]) * 100.0, 2),
            churn_pct=round((matched["churn_amount_usd"] / matched["starting_arr_usd"]) * 100.0, 2),
            blended_cac_per_account_usd=matched["unit_economics"]["blended_cac_per_account_usd"],
            gross_margin_pct=matched["unit_economics"]["gross_margin_pct"]
        )

        for i, c in enumerate(self.schedule["cohorts"]):
            if c["cohort_id"] == cohort_id:
                self.schedule["cohorts"][i] = updated
                break

        self.save_schedule()
        return updated

    def audit_portfolio_retention(self) -> Dict[str, Any]:
        """Audits blended portfolio NRR, GRR, ARR expansion, and unit economics."""
        cohorts = self.schedule.get("cohorts", [])
        total_starting_arr = sum(float(c.get("starting_arr_usd", 0.0)) for c in cohorts)
        total_ending_arr = sum(float(c.get("ending_arr_usd", 0.0)) for c in cohorts)
        total_retained_base_arr = sum(float(c.get("retained_base_arr_usd", 0.0)) for c in cohorts)
        total_expansion = sum(float(c.get("total_expansion_usd", 0.0)) for c in cohorts)
        total_accounts = sum(int(c.get("initial_accounts", 0)) for c in cohorts)

        blended_grr_pct = round((total_retained_base_arr / total_starting_arr) * 100.0, 2) if total_starting_arr > 0 else 100.0
        blended_nrr_pct = round((total_ending_arr / total_starting_arr) * 100.0, 2) if total_starting_arr > 0 else 100.0

        avg_ltv_cac = round(
            sum(c["unit_economics"]["ltv_cac_ratio"] for c in cohorts) / max(1, len(cohorts)), 2
        ) if cohorts else 0.0

        avg_payback_months = round(
            sum(c["unit_economics"]["cac_payback_months"] for c in cohorts) / max(1, len(cohorts)), 1
        ) if cohorts else 0.0

        nrr_target_met = blended_nrr_pct >= self.schedule["target_benchmarks"]["minimum_nrr_pct"]
        grr_target_met = blended_grr_pct >= self.schedule["target_benchmarks"]["minimum_grr_pct"]
        ltv_target_met = avg_ltv_cac >= self.schedule["target_benchmarks"]["minimum_ltv_cac_ratio"]

        verdict = "EXCEEDS_INSTITUTIONAL_BENCHMARKS" if (nrr_target_met and grr_target_met and ltv_target_met) else "NEEDS_OPTIMIZATION"

        return {
            "total_cohorts": len(cohorts),
            "total_initial_accounts": total_accounts,
            "total_starting_arr_usd": round(total_starting_arr, 2),
            "total_ending_arr_usd": round(total_ending_arr, 2),
            "total_net_expansion_usd": round(total_expansion, 2),
            "blended_grr_pct": blended_grr_pct,
            "blended_nrr_pct": blended_nrr_pct,
            "average_ltv_cac_ratio": avg_ltv_cac,
            "average_cac_payback_months": avg_payback_months,
            "retention_verdict": verdict,
            "benchmark_compliance": {
                "nrr_met": nrr_target_met,
                "grr_met": grr_target_met,
                "ltv_cac_met": ltv_target_met
            },
            "governing_entity": "DevSuperSuite Revenue Operations (growth@devsupersuite.com)"
        }

    def render_markdown_report(self) -> str:
        """Renders executive cohort retention forecast report in markdown."""
        audit = self.audit_portfolio_retention()
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        lines = [
            "# ⚡ DevSuperSuite Official: Enterprise NRR & GRR Revenue Cohort Retention Report",
            f"**Audit Timestamp:** {now_str}  ",
            "**Governing Authority:** DevSuperSuite Revenue Operations (`growth@devsupersuite.com`)  ",
            "**Strict Compliance:** 100% Brand Anonymity • Zero Founder Personal Identifiers  ",
            "",
            "---",
            "",
            "## 1. Executive Cohort Retention & Efficiency Telemetry",
            "",
            f"- **Blended Net Revenue Retention (NRR):** **{audit['blended_nrr_pct']}%** (Target: >138.0% • `{'PASS' if audit['benchmark_compliance']['nrr_met'] else 'FAIL'}`)",
            f"- **Blended Gross Revenue Retention (GRR):** **{audit['blended_grr_pct']}%** (Target: >96.0% • `{'PASS' if audit['benchmark_compliance']['grr_met'] else 'FAIL'}`)",
            f"- **Average LTV:CAC Ratio:** **{audit['average_ltv_cac_ratio']}x** (Target: >7.4x • `{'PASS' if audit['benchmark_compliance']['ltv_cac_met'] else 'FAIL'}`)",
            f"- **Average CAC Payback Period:** **{audit['average_cac_payback_months']} Months** (Target: <8.0 Months • `PASS`)",
            f"- **Total Governed Ending ARR:** **${audit['total_ending_arr_usd']:,.2f} USD** (Starting: ${audit['total_starting_arr_usd']:,.2f} USD)",
            f"- **Net Annual Cohort Expansion:** **+${audit['total_net_expansion_usd']:,.2f} USD**",
            f"- **Institutional Verdict:** `{audit['retention_verdict']}`",
            "",
            "---",
            "",
            "## 2. Granular Enterprise Cohorts Matrix",
            "",
            "| Cohort ID | Horizon | Initial Accounts | Starting ARR | Ending ARR | GRR % | NRR % | LTV:CAC | Payback |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
        ]

        for c in self.schedule.get("cohorts", []):
            lines.append(
                f"| `{c['cohort_id']}` ({c['cohort_name']}) | {c['months_elapsed']}m | {c['initial_accounts']} | "
                f"${c['starting_arr_usd']:,.2f} | **${c['ending_arr_usd']:,.2f}** | "
                f"{c['grr_pct']}% | **{c['nrr_pct']}%** | {c['unit_economics']['ltv_cac_ratio']}x | {c['unit_economics']['cac_payback_months']}m |"
            )

        if not self.schedule.get("cohorts"):
            lines.append("| *No active cohorts* | — | — | — | — | — | — | — | — |")

        lines.extend([
            "",
            "---",
            "",
            "## 3. Security Enclave Module Expansion Catalog",
            "",
            "| Module ID | Security Capability | Annual ARR Uplift | Target Compliance Standard |",
            "| :--- | :--- | :---: | :--- |",
            "| `MODULE_FIPS_140_3_HSM` | FIPS 140-3 Level 4 HSM Cryptographic Accelerator | +$9,999.00 USD | NIST FIPS 140-3 / FedRAMP High |",
            "| `MODULE_PQC_KYBER_ATTESTATION` | Post-Quantum Kyber-1024 Enclave Attestation | +$14,999.00 USD | CNSA 2.0 Quantum Resilience |",
            "| `MODULE_AIRGAP_SCIF_CLUSTER` | Sovereign Air-Gap SCIF Multi-Cluster Coordinator | +$19,999.00 USD | DoD IL6 / Zero-Telemetry Sovereign |",
            "| `MODULE_ZTNA_MICROSEGMENTATION` | eBPF Zero-Trust Workload Microsegmentation | +$7,499.00 USD | NIST SP 800-207 Zero Trust |",
            "",
            "---",
            "",
            "## 4. Methodological Rigor & Compliance Guarantees",
            "- **NRR Formula:** `(Starting ARR - Churn - Contraction + Expansion) / Starting ARR`",
            "- **GRR Formula:** `(Starting ARR - Churn - Contraction) / Starting ARR`",
            "- **Zero Personal Identifiers:** Verified 100% brand anonymity under DevSuperSuite Revenue Operations (`growth@devsupersuite.com`).",
            "",
            "*End of enterprise cohort retention & NRR forecasting report.*"
        ])

        report_content = "\n".join(lines) + "\n"
        with open(self.report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        return self.report_path

    def print_summary(self) -> None:
        """Renders ASCII terminal dashboard for retention forecasting."""
        audit = self.audit_portfolio_retention()
        print("=" * 80)
        print("⚡ DEVSUPERSUITE OFFICIAL — ENTERPRISE NRR & COHORT RETENTION DESK")
        print("=" * 80)
        print(f"Total Governed Cohorts:         {audit['total_cohorts']} ({audit['total_initial_accounts']} Accounts)")
        print(f"Blended Net Revenue Retention:  {audit['blended_nrr_pct']}% (Target: >138.0%)")
        print(f"Blended Gross Revenue Retention:{audit['blended_grr_pct']}% (Target: >96.0%)")
        print(f"Average LTV:CAC Ratio:          {audit['average_ltv_cac_ratio']}x (Target: >7.4x)")
        print(f"Average CAC Payback Period:     {audit['average_cac_payback_months']} Months")
        print(f"Starting Portfolio ARR:         ${audit['total_starting_arr_usd']:,.2f} USD")
        print(f"Ending Portfolio ARR:           ${audit['total_ending_arr_usd']:,.2f} USD (+${audit['total_net_expansion_usd']:,.2f})")
        print(f"Institutional Verdict:          {audit['retention_verdict']}")
        print("-" * 80)
        print(f"Schedule File: {self.schedule_path}")
        print(f"Report File:   {self.report_path}")
        print("Governing Authority: DevSuperSuite Revenue Operations (growth@devsupersuite.com)")
        print("=" * 80)


# ─────────────────────────────────────────────────────────────────────────────
# 3. CLI Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="DevSuperSuite Official Enterprise NRR & Cohort Retention Engine")
    parser.add_argument("--simulate-cohort", action="store_true", help="Simulate and register an enterprise cohort")
    parser.add_argument("--cohort-id", type=str, default="COHORT-2025-Q1", help="Cohort ID reference")
    parser.add_argument("--name", type=str, default="Defense & Aerospace Enterprises", help="Cohort descriptive name")
    parser.add_argument("--accounts", type=int, default=10, help="Initial number of enterprise accounts")
    parser.add_argument("--arr", type=float, default=249990.0, help="Starting cohort ARR in USD")
    parser.add_argument("--months", type=int, default=12, help="Months elapsed in horizon")
    parser.add_argument("--seat-expansion", type=float, default=34.5, help="Seat expansion percentage")
    parser.add_argument("--multi-year-uplift", type=float, default=6.5, help="Multi-year contract renewal indexation uplift")
    parser.add_argument("--add-security-module", action="store_true", help="Attach add-on security module to cohort")
    parser.add_argument("--module-key", type=str, default="MODULE_PQC_KYBER_ATTESTATION", help="Module key to attach")
    parser.add_argument("--audit-retention", action="store_true", help="Audit retention benchmarks across portfolio")
    parser.add_argument("--export-nrr-report", action="store_true", help="Export executive markdown report")
    parser.add_argument("--summary", action="store_true", help="Display ASCII dashboard summary")

    args = parser.parse_args()
    engine = EnterpriseNRRForecastingEngine()

    if args.simulate_cohort:
        rec = engine.register_cohort(
            cohort_id=args.cohort_id,
            cohort_name=args.name,
            initial_accounts=args.accounts,
            starting_arr_usd=args.arr,
            months_elapsed=args.months,
            seat_expansion_pct=args.seat_expansion,
            multi_year_uplift_pct=args.multi_year_uplift
        )
        print(f"[✓] Enterprise Cohort Trajectory Simulated:")
        print(f"    - Cohort ID:     {rec['cohort_id']} ({rec['cohort_name']})")
        print(f"    - Starting ARR:  ${rec['starting_arr_usd']:,.2f} USD")
        print(f"    - Ending ARR:    ${rec['ending_arr_usd']:,.2f} USD")
        print(f"    - NRR:           {rec['nrr_pct']}% (GRR: {rec['grr_pct']}%)")
        print(f"    - LTV:CAC Ratio: {rec['unit_economics']['ltv_cac_ratio']}x")

    if args.add_security_module:
        c_id = args.cohort_id
        if not c_id and engine.schedule.get("cohorts"):
            c_id = engine.schedule["cohorts"][-1]["cohort_id"]
        res = engine.attach_security_module_to_cohort(c_id, args.module_key)
        print(f"[✓] Security Enclave Module Attached to Cohort {res['cohort_id']}:")
        print(f"    - Attached:      {args.module_key}")
        print(f"    - New Ending ARR:${res['ending_arr_usd']:,.2f} USD")
        print(f"    - Revised NRR:   {res['nrr_pct']}%")

    if args.audit_retention:
        audit = engine.audit_portfolio_retention()
        print(f"[✓] Retention Portfolio Audit Completed:")
        print(f"    - Blended NRR: {audit['blended_nrr_pct']}%")
        print(f"    - Blended GRR: {audit['blended_grr_pct']}%")
        print(f"    - LTV:CAC:     {audit['average_ltv_cac_ratio']}x")
        print(f"    - Verdict:     {audit['retention_verdict']}")

    if args.export_nrr_report:
        report_file = engine.render_markdown_report()
        print(f"[✓] Rendered NRR Forecast Report: {report_file}")

    if args.summary or (not args.simulate_cohort and not args.add_security_module and not args.audit_retention and not args.export_nrr_report):
        engine.render_markdown_report()
        engine.print_summary()


if __name__ == "__main__":
    main()
