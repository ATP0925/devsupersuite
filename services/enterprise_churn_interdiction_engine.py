#!/usr/bin/env python3
"""
⚡ DevSuperSuite Official: Enterprise Customer Health Scoring & Churn Interdiction Engine
File: enterprise_churn_interdiction_engine.py
Version: 1.0.0
Governing Authority: DevSuperSuite Revenue Operations (growth@devsupersuite.com)
Strict Protocol: 100% Brand Anonymity - Zero Founder Personal Identifiers

Key Capabilities:
1. Real-Time Customer Health Scoring Across 5 Behavioral Signals:
   - AST queries volume trend (30-day moving average, 25% weight).
   - Secret scan frequency (20% weight).
   - Active CLI developer sessions (20% weight).
   - Seat utilization ratio (active vs licensed seats, 20% weight).
   - Support ticket sentiment & CSAT (15% weight).
2. Dynamic Health Classification:
   - HEALTHY (Score >= 80.0): Expansion / module upsell readiness.
   - AT_RISK (50.0 <= Score < 80.0): Proactive TAM check-in and feature enablement.
   - CRITICAL_INTERDICTION (Score < 50.0): Immediate executive outreach, SA office hours, and 14-day license extension.
3. Automated Interdiction Playbook Execution:
   - Generates and logs intervention payloads and license extension tokens.
4. Persistent Schedule & Publication Reporting:
   - Stored in data/customer_health_scores.json.
   - Executive scorecard in services/reports/customer_churn_interdiction_report.md.
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

# Base Directories Setup
SERVICES_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(SERVICES_DIR)
DATA_DIR = os.path.join(SCRATCH_DIR, "data")
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

HEALTH_SCORES_PATH = os.path.join(DATA_DIR, "customer_health_scores.json")
REPORT_PATH = os.path.join(REPORTS_DIR, "customer_churn_interdiction_report.md")

# Signal Weights
SIGNAL_WEIGHTS = {
    "ast_volume_trend": 0.25,
    "secret_scan_frequency": 0.20,
    "active_cli_sessions": 0.20,
    "seat_utilization": 0.20,
    "support_sentiment": 0.15
}


# ─────────────────────────────────────────────────────────────────────────────
# 1. Behavioral Signal Normalizer & Health Calculator
# ─────────────────────────────────────────────────────────────────────────────

class CustomerHealthCalculator:
    """Computes normalized subscores and aggregate health index (0-100)."""

    @classmethod
    def calculate_health_score(
        cls,
        ast_volume_trend_pct: float,        # e.g., +20% or -40% 30-day trend
        weekly_secret_scans: int,           # e.g., 500 scans/week
        daily_active_cli_users: int,        # e.g., 40 active CLI developers
        licensed_seats: int,                # e.g., 50 seats
        active_seats: int,                  # e.g., 42 active seats
        support_csat_score: float,          # 1.0 to 5.0 scale
        open_critical_tickets: int = 0
    ) -> Dict[str, Any]:
        """Calculates normalized subscores and weighted composite customer health score."""
        licensed = max(1, licensed_seats)
        active = max(0, active_seats)

        # 1. AST Volume Trend Score (25% weight)
        # +30% or more -> 100, 0% -> 70, -50% -> 20, -100% -> 0
        if ast_volume_trend_pct >= 30.0:
            ast_score = 100.0
        elif ast_volume_trend_pct >= 0.0:
            ast_score = round(70.0 + (ast_volume_trend_pct / 30.0) * 30.0, 1)
        elif ast_volume_trend_pct >= -50.0:
            ast_score = round(70.0 - (abs(ast_volume_trend_pct) / 50.0) * 50.0, 1)
        else:
            ast_score = max(0.0, round(20.0 - ((abs(ast_volume_trend_pct) - 50.0) / 50.0) * 20.0, 1))

        # 2. Secret Scan Frequency Score (20% weight)
        # Benchmark: >100 scans/week -> 100, 50-100 -> 80, 10-50 -> 50, <10 -> 20
        if weekly_secret_scans >= 100:
            scan_score = 100.0
        elif weekly_secret_scans >= 50:
            scan_score = round(80.0 + ((weekly_secret_scans - 50) / 50.0) * 20.0, 1)
        elif weekly_secret_scans >= 10:
            scan_score = round(50.0 + ((weekly_secret_scans - 10) / 40.0) * 30.0, 1)
        else:
            scan_score = round(max(0.0, (weekly_secret_scans / 10.0) * 50.0), 1)

        # 3. Active CLI Sessions Score (20% weight)
        # Ratio of daily active users to active seats
        cli_ratio = min(1.5, daily_active_cli_users / max(1, active))
        cli_score = min(100.0, round(cli_ratio * 100.0, 1))

        # 4. Seat Utilization Score (20% weight)
        # Utilization = active / licensed
        util_ratio = min(1.2, active / licensed)
        if util_ratio >= 0.90:
            util_score = 100.0
        elif util_ratio >= 0.70:
            util_score = round(80.0 + ((util_ratio - 0.70) / 0.20) * 20.0, 1)
        elif util_ratio >= 0.40:
            util_score = round(50.0 + ((util_ratio - 0.40) / 0.30) * 30.0, 1)
        else:
            util_score = max(0.0, round((util_ratio / 0.40) * 50.0, 1))

        # 5. Support Sentiment Score (15% weight)
        # CSAT 1.0 to 5.0 normalized to 0-100, penalty for open critical tickets
        csat_normalized = min(100.0, max(0.0, (support_csat_score / 5.0) * 100.0))
        penalty = open_critical_tickets * 25.0
        sentiment_score = max(0.0, round(csat_normalized - penalty, 1))

        # Weighted Composite Score
        composite_score = round(
            (ast_score * SIGNAL_WEIGHTS["ast_volume_trend"]) +
            (scan_score * SIGNAL_WEIGHTS["secret_scan_frequency"]) +
            (cli_score * SIGNAL_WEIGHTS["active_cli_sessions"]) +
            (util_score * SIGNAL_WEIGHTS["seat_utilization"]) +
            (sentiment_score * SIGNAL_WEIGHTS["support_sentiment"]),
            1
        )

        # Health Classification
        if composite_score >= 80.0:
            status = "HEALTHY"
            interdiction_action = "EXPANSION_UPSELL_OPPORTUNITY"
        elif composite_score >= 50.0:
            status = "AT_RISK"
            interdiction_action = "PROACTIVE_TAM_OPTIMIZATION_TOUCHPOINT"
        else:
            status = "CRITICAL_INTERDICTION"
            interdiction_action = "EMERGENCY_SOLUTIONS_ARCHITECT_OFFICE_HOURS_AND_EXTENSION"

        return {
            "health_score": composite_score,
            "status": status,
            "recommended_action": interdiction_action,
            "subscores": {
                "ast_volume_trend_score": ast_score,
                "secret_scan_score": scan_score,
                "active_cli_score": cli_score,
                "seat_utilization_score": util_score,
                "support_sentiment_score": sentiment_score
            },
            "raw_metrics": {
                "ast_volume_trend_pct": ast_volume_trend_pct,
                "weekly_secret_scans": weekly_secret_scans,
                "daily_active_cli_users": daily_active_cli_users,
                "licensed_seats": licensed_seats,
                "active_seats": active_seats,
                "seat_utilization_pct": round((active / licensed) * 100.0, 1),
                "support_csat_score": support_csat_score,
                "open_critical_tickets": open_critical_tickets
            }
        }


# ─────────────────────────────────────────────────────────────────────────────
# 2. Enterprise Churn Interdiction Engine
# ─────────────────────────────────────────────────────────────────────────────

class EnterpriseChurnInterdictionEngine:
    """Manages customer health tracking, automated playbooks, and intervention dispatches."""

    def __init__(
        self,
        ledger_path: str = HEALTH_SCORES_PATH,
        report_path: str = REPORT_PATH
    ):
        self.ledger_path = ledger_path
        self.report_path = report_path
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
            "governing_entity": "DevSuperSuite Revenue Operations (growth@devsupersuite.com)",
            "compliance_protocol": "100% Brand Anonymity - Zero Founder Personal Identifiers",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "customer_accounts": [],
            "interdiction_events": []
        }

    def save_ledger(self) -> None:
        self.ledger["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            json.dump(self.ledger, f, indent=2)

    def assess_and_record_customer_health(
        self,
        account_id: str,
        company_name: str,
        domain: str,
        contract_arr_usd: float,
        ast_volume_trend_pct: float,
        weekly_secret_scans: int,
        daily_active_cli_users: int,
        licensed_seats: int,
        active_seats: int,
        support_csat_score: float = 4.8,
        open_critical_tickets: int = 0
    ) -> Dict[str, Any]:
        """Calculates health score and records evaluation in persistent ledger."""
        account_id = account_id.strip().upper()
        health = CustomerHealthCalculator.calculate_health_score(
            ast_volume_trend_pct=ast_volume_trend_pct,
            weekly_secret_scans=weekly_secret_scans,
            daily_active_cli_users=daily_active_cli_users,
            licensed_seats=licensed_seats,
            active_seats=active_seats,
            support_csat_score=support_csat_score,
            open_critical_tickets=open_critical_tickets
        )

        now_dt = datetime.now(timezone.utc).isoformat()

        record = {
            "account_id": account_id,
            "company_name": company_name.strip(),
            "domain": domain.strip().lower(),
            "contract_arr_usd": round(contract_arr_usd, 2),
            "health_score": health["health_score"],
            "status": health["status"],
            "recommended_action": health["recommended_action"],
            "subscores": health["subscores"],
            "raw_metrics": health["raw_metrics"],
            "last_evaluated_at": now_dt,
            "interdiction_active": health["status"] in ["AT_RISK", "CRITICAL_INTERDICTION"],
            "active_interventions": []
        }

        # Update if exists or append
        existing_idx = next((i for i, c in enumerate(self.ledger.get("customer_accounts", [])) if c["account_id"] == account_id), None)
        if existing_idx is not None:
            self.ledger["customer_accounts"][existing_idx] = record
        else:
            self.ledger["customer_accounts"].append(record)

        self.save_ledger()
        return record

    def trigger_interdiction_playbook(
        self,
        account_id: str,
        target_executive_email: str = "engineering-leadership@company.com"
    ) -> Dict[str, Any]:
        """Executes automated interdiction playbook according to customer health classification."""
        account_id = account_id.strip().upper()
        matched = next((c for c in self.ledger.get("customer_accounts", []) if c["account_id"] == account_id), None)
        if not matched:
            raise KeyError(f"Customer account '{account_id}' not found in health ledger.")

        now_dt = datetime.now(timezone.utc)
        status = matched["status"]
        event_id = f"INT-{uuid.uuid4().hex[:8].upper()}"

        if status == "CRITICAL_INTERDICTION":
            # 14-day license extension token + SA office hours
            ext_token = f"DSS-EXT-14D-{hashlib.sha256((account_id + str(now_dt.timestamp())).encode('utf-8')).hexdigest()[:12].upper()}"
            intervention = {
                "event_id": event_id,
                "account_id": account_id,
                "severity": "CRITICAL",
                "triggered_at": now_dt.isoformat(),
                "executive_email": target_executive_email.strip().lower(),
                "actions_executed": [
                    "Automated high-priority escalation logged to solutions@devsupersuite.com",
                    f"Generated 14-day zero-cost license grace extension token: {ext_token}",
                    "Dispatched dedicated Solutions Architect 1-on-1 office hours invitation",
                    "Activated AST tuning and secret false-positive remediation desk"
                ],
                "extension_token": ext_token,
                "status": "DISPATCHED_ACTIVE"
            }
        elif status == "AT_RISK":
            intervention = {
                "event_id": event_id,
                "account_id": account_id,
                "severity": "WARNING",
                "triggered_at": now_dt.isoformat(),
                "executive_email": target_executive_email.strip().lower(),
                "actions_executed": [
                    "Dispatched proactive Technical Account Manager (TAM) optimization review email",
                    "Attached Enterprise AST CLI adoption & IDE integration playbook",
                    "Scheduled quarterly business review (QBR) check-in"
                ],
                "extension_token": None,
                "status": "DISPATCHED_ACTIVE"
            }
        else:
            intervention = {
                "event_id": event_id,
                "account_id": account_id,
                "severity": "OPPORTUNITY",
                "triggered_at": now_dt.isoformat(),
                "executive_email": target_executive_email.strip().lower(),
                "actions_executed": [
                    "Logged customer as high-health reference candidate",
                    "Prepared expansion proposal for additional seats & FIPS 140-3 HSM module"
                ],
                "extension_token": None,
                "status": "COMPLETED"
            }

        matched["active_interventions"].append(intervention)
        self.ledger["interdiction_events"].append(intervention)
        self.save_ledger()

        return intervention

    def audit_customer_health_portfolio(self) -> Dict[str, Any]:
        """Runs audit of overall customer health portfolio, ARR at risk, and intervention metrics."""
        accounts = self.ledger.get("customer_accounts", [])
        total_accounts = len(accounts)

        healthy_accounts = [a for a in accounts if a["status"] == "HEALTHY"]
        at_risk_accounts = [a for a in accounts if a["status"] == "AT_RISK"]
        critical_accounts = [a for a in accounts if a["status"] == "CRITICAL_INTERDICTION"]

        total_portfolio_arr = sum(float(a.get("contract_arr_usd", 0.0)) for a in accounts)
        healthy_arr = sum(float(a.get("contract_arr_usd", 0.0)) for a in healthy_accounts)
        at_risk_arr = sum(float(a.get("contract_arr_usd", 0.0)) for a in at_risk_accounts)
        critical_arr = sum(float(a.get("contract_arr_usd", 0.0)) for a in critical_accounts)

        avg_health_score = round(
            sum(float(a.get("health_score", 0.0)) for a in accounts) / max(1, total_accounts), 1
        ) if total_accounts > 0 else 0.0

        interventions = self.ledger.get("interdiction_events", [])

        return {
            "total_accounts": total_accounts,
            "average_portfolio_health_score": avg_health_score,
            "total_portfolio_arr_usd": round(total_portfolio_arr, 2),
            "healthy_accounts_count": len(healthy_accounts),
            "healthy_arr_usd": round(healthy_arr, 2),
            "at_risk_accounts_count": len(at_risk_accounts),
            "at_risk_arr_usd": round(at_risk_arr, 2),
            "critical_accounts_count": len(critical_accounts),
            "critical_arr_usd": round(critical_arr, 2),
            "total_arr_at_risk_usd": round(at_risk_arr + critical_arr, 2),
            "total_interventions_dispatched": len(interventions),
            "governing_entity": "DevSuperSuite Revenue Operations (growth@devsupersuite.com)"
        }

    def render_markdown_report(self) -> str:
        """Renders comprehensive executive customer health and churn interdiction scorecard in markdown."""
        audit = self.audit_customer_health_portfolio()
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        lines = [
            "# ⚡ DevSuperSuite Official: Customer Health Scoring & Churn Interdiction Scorecard",
            f"**Audit Timestamp:** {now_str}  ",
            "**Governing Authority:** DevSuperSuite Revenue Operations (`growth@devsupersuite.com`)  ",
            "**Strict Compliance:** 100% Brand Anonymity • Zero Founder Personal Identifiers  ",
            "",
            "---",
            "",
            "## 1. Executive Health & Retention Telemetry",
            "",
            f"- **Average Customer Health Score:** **{audit['average_portfolio_health_score']} / 100**",
            f"- **Total Governed Enterprise ARR:** **${audit['total_portfolio_arr_usd']:,.2f} USD** ({audit['total_accounts']} Accounts)",
            f"- **Healthy Accounts (>80 Score):** **{audit['healthy_accounts_count']} Accounts** (${audit['healthy_arr_usd']:,.2f} ARR)",
            f"- **At-Risk Accounts (50-80 Score):** **{audit['at_risk_accounts_count']} Accounts** (${audit['at_risk_arr_usd']:,.2f} ARR)",
            f"- **Critical Interdiction Accounts (<50 Score):** **{audit['critical_accounts_count']} Accounts** (${audit['critical_arr_usd']:,.2f} ARR)",
            f"- **Total ARR At-Risk:** **${audit['total_arr_at_risk_usd']:,.2f} USD**",
            f"- **Automated Interventions Dispatched:** **{audit['total_interventions_dispatched']} Playbook Executions**",
            "",
            "---",
            "",
            "## 2. Customer Health Scoring Model & Signal Weights",
            "",
            "| Behavioral Signal | Weight | Target Benchmark | Scoring Logic |",
            "| :--- | :---: | :--- | :--- |",
            "| **AST Queries Volume Trend** | 25% | >0% (30-day expansion) | Normalized 0-100 (+30% $\\to$ 100, -50% $\\to$ 20) |",
            "| **Secret Scan Frequency** | 20% | >100 scans / week | Benchmark curve: >100 $\\to$ 100, <10 $\\to$ <50 |",
            "| **Active CLI Developer Sessions** | 20% | >80% active engineer ratio | Daily active CLI instances / active seats |",
            "| **Seat Utilization Ratio** | 20% | >75% seat activation | Active developer seats / total licensed seats |",
            "| **Support Ticket Sentiment** | 15% | CSAT > 4.5 • 0 Critical P1s | 5.0 CSAT normalized with -25 pt per open P1 |",
            "",
            "---",
            "",
            "## 3. Enterprise Customer Accounts Scorecard",
            "",
            "| Account ID | Organization | ARR | Health Score | Status | AST Trend | Seat Util | Recommended Action |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |"
        ]

        for a in self.ledger.get("customer_accounts", []):
            raw = a.get("raw_metrics", {})
            lines.append(
                f"| `{a['account_id']}` | **{a['company_name']}** | ${a['contract_arr_usd']:,.2f} | "
                f"**{a['health_score']}** | `{a['status']}` | {raw.get('ast_volume_trend_pct', 0.0):+.1f}% | "
                f"{raw.get('seat_utilization_pct', 0.0)}% | `{a['recommended_action']}` |"
            )

        if not self.ledger.get("customer_accounts"):
            lines.append("| *No active customer health evaluations* | — | — | — | — | — | — | — |")

        lines.extend([
            "",
            "---",
            "",
            "## 4. Churn Interdiction Protocol & Brand Anonymity",
            "- **Critical Accounts (<50):** Automated dispatch of 14-day zero-cost license extension tokens and 1-on-1 solutions architect office hours (`solutions@devsupersuite.com`).",
            "- **At-Risk Accounts (50-80):** Technical account manager review and CLI adoption enablement.",
            "- **Zero Founder Identifiers:** 100% brand anonymity strictly enforced across all customer-facing playbooks.",
            "",
            "*End of customer health scoring & churn interdiction scorecard.*"
        ])

        report_content = "\n".join(lines) + "\n"
        with open(self.report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        return self.report_path

    def print_summary(self) -> None:
        """Renders ASCII terminal dashboard for customer health and churn interdiction."""
        audit = self.audit_customer_health_portfolio()
        print("=" * 80)
        print("⚡ DEVSUPERSUITE OFFICIAL — CUSTOMER HEALTH & CHURN INTERDICTION DESK")
        print("=" * 80)
        print(f"Total Governed Accounts:        {audit['total_accounts']} (${audit['total_portfolio_arr_usd']:,.2f} ARR)")
        print(f"Average Health Score:           {audit['average_portfolio_health_score']} / 100")
        print(f"Healthy Accounts (>80):         {audit['healthy_accounts_count']} (${audit['healthy_arr_usd']:,.2f} ARR)")
        print(f"At-Risk Accounts (50-80):       {audit['at_risk_accounts_count']} (${audit['at_risk_arr_usd']:,.2f} ARR)")
        print(f"Critical Interdiction (<50):    {audit['critical_accounts_count']} (${audit['critical_arr_usd']:,.2f} ARR)")
        print(f"Total ARR at Risk:              ${audit['total_arr_at_risk_usd']:,.2f} USD")
        print(f"Automated Interventions:        {audit['total_interventions_dispatched']} Dispatches")
        print("-" * 80)
        print(f"Health Scores File: {self.ledger_path}")
        print(f"Executive Report:   {self.report_path}")
        print("Governing Authority: DevSuperSuite Revenue Operations (growth@devsupersuite.com)")
        print("=" * 80)


# ─────────────────────────────────────────────────────────────────────────────
# 3. CLI Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="DevSuperSuite Official Customer Health & Churn Interdiction Engine")
    parser.add_argument("--calculate-health", action="store_true", help="Calculate and record customer health score")
    parser.add_argument("--account-id", type=str, default="ACC-LMT-01", help="Target account ID")
    parser.add_argument("--company", type=str, default="Lockheed Martin Corporation", help="Company name")
    parser.add_argument("--domain", type=str, default="lockheedmartin.com", help="Corporate domain")
    parser.add_argument("--arr", type=float, default=24999.0, help="Contract annual recurring revenue in USD")
    parser.add_argument("--ast-trend", type=float, default=25.0, help="AST volume 30-day percentage trend")
    parser.add_argument("--scans", type=int, default=150, help="Weekly secret scans executed")
    parser.add_argument("--cli-users", type=int, default=45, help="Daily active CLI developer instances")
    parser.add_argument("--licensed-seats", type=int, default=50, help="Total licensed seats")
    parser.add_argument("--active-seats", type=int, default=48, help="Active seats consumed")
    parser.add_argument("--csat", type=float, default=4.9, help="Support CSAT rating (1.0 to 5.0)")
    parser.add_argument("--open-p1", type=int, default=0, help="Number of open critical P1 tickets")
    parser.add_argument("--trigger-interdiction", action="store_true", help="Trigger automated interdiction playbook")
    parser.add_argument("--email", type=str, default="leadership@company.com", help="Target executive email")
    parser.add_argument("--audit-health", action="store_true", help="Run audit on customer health portfolio")
    parser.add_argument("--export-churn-report", action="store_true", help="Render markdown scorecard")
    parser.add_argument("--summary", action="store_true", help="Display ASCII dashboard summary")

    args = parser.parse_args()
    engine = EnterpriseChurnInterdictionEngine()

    if args.calculate_health:
        rec = engine.assess_and_record_customer_health(
            account_id=args.account_id,
            company_name=args.company,
            domain=args.domain,
            contract_arr_usd=args.arr,
            ast_volume_trend_pct=args.ast_trend,
            weekly_secret_scans=args.scans,
            daily_active_cli_users=args.cli_users,
            licensed_seats=args.licensed_seats,
            active_seats=args.active_seats,
            support_csat_score=args.csat,
            open_critical_tickets=args.open_p1
        )
        print(f"[✓] Customer Health Assessed & Recorded:")
        print(f"    - Account:       {rec['company_name']} ({rec['account_id']})")
        print(f"    - Health Score:  {rec['health_score']} / 100")
        print(f"    - Classification:{rec['status']}")
        print(f"    - Action:        {rec['recommended_action']}")

    if args.trigger_interdiction:
        a_id = args.account_id
        if not a_id and engine.ledger.get("customer_accounts"):
            a_id = engine.ledger["customer_accounts"][-1]["account_id"]
        res = engine.trigger_interdiction_playbook(a_id, args.email)
        print(f"[✓] Interdiction Playbook Executed:")
        print(f"    - Event ID:      {res['event_id']}")
        print(f"    - Severity:      {res['severity']}")
        print(f"    - Actions Taken: {len(res['actions_executed'])} steps executed")
        if res.get("extension_token"):
            print(f"    - License Token: {res['extension_token']}")

    if args.audit_health:
        audit = engine.audit_customer_health_portfolio()
        print(f"[✓] Customer Health Portfolio Audit Completed:")
        print(f"    - Accounts:      {audit['total_accounts']}")
        print(f"    - Avg Score:     {audit['average_portfolio_health_score']}")
        print(f"    - ARR At Risk:   ${audit['total_arr_at_risk_usd']:,.2f} USD")

    if args.export_churn_report:
        report_file = engine.render_markdown_report()
        print(f"[✓] Rendered Churn Report: {report_file}")

    if args.summary or (not args.calculate_health and not args.trigger_interdiction and not args.audit_health and not args.export_churn_report):
        engine.render_markdown_report()
        engine.print_summary()


if __name__ == "__main__":
    main()
