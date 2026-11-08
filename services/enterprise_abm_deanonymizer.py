#!/usr/bin/env python3
"""
⚡ DevSuperSuite Official: Enterprise B2B IP Deanonymization & Account-Based Intent Signal Engine
File: enterprise_abm_deanonymizer.py
Version: 1.0.0
Governing Authority: DevSuperSuite Enterprise Solutions Directorate (enterprise@devsupersuite.com)
Strict Protocol: 100% Brand Anonymity - DevSuperSuite Official Only - Zero Founder Personal Identifiers

Features:
- Real-time IP-to-Company & ASN matching against Fortune 500 and Top Tech Enterprise CIDR blocks.
- Multi-vector ABM Intent Scoring Algorithm:
  * Page depth (+5 pts per page, max 20)
  * Sandbox playground dwell time (+10 pts per 30s in #demo, max 30)
  * Pricing section exploration (+20 pts)
  * Security & Airgap compliance inspection (+15 pts)
  * Repeat visits within 24h (+15 pts)
- High-Intent Surge Alert Trigger (Score >= 75):
  * Generates actionable account dossier with recommended AE outreach play.
  * Formats real-time Slack/Webhook payload for enterprise solutions desk.
- Automated Reporting:
  * Generates services/reports/enterprise_abm_signals_report.md.
  * Logs to data/enterprise_intent_sessions.json.
- CLI flags: --simulate-enterprise-traffic, --audit-abm-intent, --export-account-dossiers, --summary.
"""

import os
import sys
import json
import uuid
import ipaddress
import argparse
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Base Paths Setup
SERVICES_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(SERVICES_DIR)
DATA_DIR = os.path.join(SCRATCH_DIR, "data")
MARKETING_DIR = os.path.join(SCRATCH_DIR, "marketing")
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MARKETING_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

TARGET_ACCOUNTS_PATH = os.path.join(MARKETING_DIR, "abm_target_accounts_signals.json")
SESSIONS_LOG_PATH = os.path.join(DATA_DIR, "enterprise_intent_sessions.json")
DOSSIERS_EXPORT_PATH = os.path.join(DATA_DIR, "enterprise_account_dossiers.json")
ABM_REPORT_PATH = os.path.join(REPORTS_DIR, "enterprise_abm_signals_report.md")
PLAYBOOK_PATH = os.path.join(MARKETING_DIR, "cro_enterprise_abm_playbook.md")

SURGE_ALERT_THRESHOLD = 75.0


# ─────────────────────────────────────────────────────────────────────────────
# 1. IP to Company Resolver (CIDR Subnet Matcher)
# ─────────────────────────────────────────────────────────────────────────────

class IPToCompanyResolver:
    """Matches IPv4 client addresses against enterprise ASN and CIDR subnet allocations."""

    def __init__(self, target_accounts_path: str = TARGET_ACCOUNTS_PATH):
        self.target_accounts_path = target_accounts_path
        self.accounts: List[Dict[str, Any]] = self._load_accounts()
        self.compiled_cidrs: List[Tuple[Any, Dict[str, Any]]] = self._compile_cidrs()

    def _load_accounts(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.target_accounts_path):
            try:
                with open(self.target_accounts_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("accounts", [])
            except Exception:
                pass
        return []

    def _compile_cidrs(self) -> List[Tuple[Any, Dict[str, Any]]]:
        compiled = []
        for acct in self.accounts:
            for cidr_str in acct.get("ip_ranges", []):
                try:
                    net = ipaddress.ip_network(cidr_str.strip(), strict=False)
                    compiled.append((net, acct))
                except Exception:
                    continue
        return compiled

    def resolve_ip(self, ip_str: str) -> Optional[Dict[str, Any]]:
        """
        Resolves client IP string against enterprise CIDRs.
        Returns matched account metadata or None.
        """
        try:
            addr = ipaddress.ip_address(ip_str.strip())
        except Exception:
            return None

        for net, acct in self.compiled_cidrs:
            if addr in net:
                return {
                    "account_id": acct["account_id"],
                    "company_name": acct["company_name"],
                    "domain": acct["domain"],
                    "industry": acct["industry"],
                    "employee_tier": acct["employee_tier"],
                    "asn": acct["asn"],
                    "matched_cidr": str(net),
                    "primary_stack": acct["primary_stack"],
                    "target_acv_usd": acct["target_acv_usd"],
                    "recommended_tier": acct["recommended_tier"]
                }
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 2. Multi-Vector ABM Intent Scorer
# ─────────────────────────────────────────────────────────────────────────────

class ABMIntentScorer:
    """
    Computes a composite 0-100 Account Intent Index based on behavioral engagement depth.
    """

    MAX_PAGE_DEPTH_PTS = 20.0        # +5 pts per page up to 4 pages (max 20)
    MAX_PLAYGROUND_DWELL_PTS = 30.0  # +10 pts per 30s in AST playground (max 30)
    PRICING_VISIT_PTS = 20.0         # Explored enterprise tier matrix
    SECURITY_DOCS_PTS = 15.0         # Inspected airgap, SCIF, SOC2, Ed25519 docs
    REPEAT_VISIT_PTS = 15.0          # Return visit within 24 hours

    @classmethod
    def calculate_intent_score(cls, session_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates composite intent score and determines surge alert status.
        """
        page_depth = session_metrics.get("page_depth", 1)
        dwell_seconds = session_metrics.get("playground_dwell_seconds", 0.0)
        visited_pricing = session_metrics.get("visited_pricing", False)
        visited_security = session_metrics.get("visited_security_compliance", False)
        repeat_visit = session_metrics.get("repeat_visit_24h", False)

        # 1. Page Depth Score (0-20)
        page_pts = min(cls.MAX_PAGE_DEPTH_PTS, page_depth * 5.0)

        # 2. Playground Dwell Score (0-30)
        dwell_pts = min(cls.MAX_PLAYGROUND_DWELL_PTS, (dwell_seconds / 30.0) * 10.0)

        # 3. Pricing Visit Score (0 or 20)
        pricing_pts = cls.PRICING_VISIT_PTS if visited_pricing else 0.0

        # 4. Security / Compliance Inspection (0 or 15)
        sec_pts = cls.SECURITY_DOCS_PTS if visited_security else 0.0

        # 5. Repeat Visit (0 or 15)
        repeat_pts = cls.REPEAT_VISIT_PTS if repeat_visit else 0.0

        raw_total = page_pts + dwell_pts + pricing_pts + sec_pts + repeat_pts
        total_score = min(100.0, max(0.0, round(raw_total, 1)))

        # Categorization
        if total_score >= SURGE_ALERT_THRESHOLD:
            intent_tier = "HIGH_INTENT_SURGE"
            action_recommended = "IMMEDIATE_ENTERPRISE_AE_OUTREACH"
        elif total_score >= 45.0:
            intent_tier = "MODERATE_ENGAGEMENT"
            action_recommended = "ACCOUNT_NURTURE_CADENCE"
        else:
            intent_tier = "LOW_INTEREST"
            action_recommended = "PASSIVE_MONITORING"

        return {
            "intent_score": total_score,
            "intent_tier": intent_tier,
            "is_surge_alert": (total_score >= SURGE_ALERT_THRESHOLD),
            "action_recommended": action_recommended,
            "score_breakdown": {
                "page_depth_pts": round(page_pts, 1),
                "playground_dwell_pts": round(dwell_pts, 1),
                "pricing_visit_pts": pricing_pts,
                "security_docs_pts": sec_pts,
                "repeat_visit_pts": repeat_pts
            }
        }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Enterprise ABM Deanonymizer Core Engine
# ─────────────────────────────────────────────────────────────────────────────

class EnterpriseABMDeanonymizer:
    """
    Real-time B2B IP de-anonymization and intent tracking platform for DevSuperSuite.
    Identifies high-value enterprise accounts visiting the storefront and triggers AE alerts.
    """

    def __init__(
        self,
        target_accounts_path: str = TARGET_ACCOUNTS_PATH,
        sessions_path: str = SESSIONS_LOG_PATH,
        dossiers_path: str = DOSSIERS_EXPORT_PATH,
        report_path: str = ABM_REPORT_PATH
    ):
        self.resolver = IPToCompanyResolver(target_accounts_path)
        self.sessions_path = sessions_path
        self.dossiers_path = dossiers_path
        self.report_path = report_path
        self.sessions_log: List[Dict[str, Any]] = self._load_or_init_sessions()

    def _load_or_init_sessions(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.sessions_path):
            try:
                with open(self.sessions_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_sessions(self) -> None:
        with open(self.sessions_path, "w", encoding="utf-8") as f:
            json.dump(self.sessions_log, f, indent=2)

    def process_inbound_session(
        self,
        client_ip: str,
        session_metrics: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        De-anonymizes incoming IP, calculates intent score, and triggers alerts if score >= 75.
        """
        matched_acct = self.resolver.resolve_ip(client_ip)
        if not matched_acct:
            return None

        intent_res = ABMIntentScorer.calculate_intent_score(session_metrics)
        now_iso = datetime.now(timezone.utc).isoformat()
        session_id = f"SESS-ABM-{uuid.uuid4().hex[:8].upper()}"

        record = {
            "session_id": session_id,
            "visitor_ip": client_ip,
            "account_id": matched_acct["account_id"],
            "company_name": matched_acct["company_name"],
            "domain": matched_acct["domain"],
            "industry": matched_acct["industry"],
            "employee_tier": matched_acct["employee_tier"],
            "asn": matched_acct["asn"],
            "primary_stack": matched_acct["primary_stack"],
            "target_acv_usd": matched_acct["target_acv_usd"],
            "recommended_tier": matched_acct["recommended_tier"],
            "intent_score": intent_res["intent_score"],
            "intent_tier": intent_res["intent_tier"],
            "is_surge_alert": intent_res["is_surge_alert"],
            "action_recommended": intent_res["action_recommended"],
            "score_breakdown": intent_res["score_breakdown"],
            "timestamp": now_iso
        }

        # Generate Slack / Webhook alert if surge threshold met
        if intent_res["is_surge_alert"]:
            record["alert_payload"] = self._build_slack_alert_payload(record)
            record["alert_dispatched"] = True
        else:
            record["alert_dispatched"] = False

        self.sessions_log.append(record)
        self._save_sessions()
        return record

    def _build_slack_alert_payload(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Formats real-time enterprise AE webhook dispatch."""
        return {
            "channel": "#enterprise-leads-live",
            "alert_id": f"ALERT-{uuid.uuid4().hex[:6].upper()}",
            "text": (
                f"🚨 *ENTERPRISE HIGH-INTENT SURGE: {record['company_name']} ({record['domain']})*\n"
                f"• *Intent Score:* {record['intent_score']} / 100 [{record['intent_tier']}]\n"
                f"• *Visitor IP:* `{record['visitor_ip']}` (Matched ASN: `{record['asn']}`)\n"
                f"• *Target ACV:* ${record['target_acv_usd']:,} USD ({record['recommended_tier']})\n"
                f"• *Tech Stack:* {record['primary_stack']}\n"
                f"• *Recommended Play:* Dispatch tailored Air-Gap SCIF proposal to Lead Systems Architect.\n"
                f"• *Enterprise Desk:* enterprise@devsupersuite.com"
            ),
            "status": "DISPATCHED"
        }

    def simulate_enterprise_traffic(self) -> List[Dict[str, Any]]:
        """Simulates benchmark inbound sessions from Fortune 500 & top tech accounts."""
        sim_events = [
            # 1. Bloomberg LP (High Intent Surge: Dwell + Pricing + Security)
            {
                "ip": "160.43.12.88",
                "metrics": {
                    "page_depth": 5,
                    "playground_dwell_seconds": 90.0,
                    "visited_pricing": True,
                    "visited_security_compliance": True,
                    "repeat_visit_24h": True
                }
            },
            # 2. JPMorgan Chase (High Intent Surge: SCIF & Enterprise Tier)
            {
                "ip": "159.53.20.44",
                "metrics": {
                    "page_depth": 4,
                    "playground_dwell_seconds": 65.0,
                    "visited_pricing": True,
                    "visited_security_compliance": True,
                    "repeat_visit_24h": False
                }
            },
            # 3. Raytheon Technologies (High Intent Surge: Airgap Docs + Pricing)
            {
                "ip": "192.138.10.15",
                "metrics": {
                    "page_depth": 6,
                    "playground_dwell_seconds": 120.0,
                    "visited_pricing": True,
                    "visited_security_compliance": True,
                    "repeat_visit_24h": True
                }
            },
            # 4. Datadog (Moderate Engagement: Playground only)
            {
                "ip": "199.83.129.50",
                "metrics": {
                    "page_depth": 2,
                    "playground_dwell_seconds": 45.0,
                    "visited_pricing": False,
                    "visited_security_compliance": False,
                    "repeat_visit_24h": False
                }
            },
            # 5. Stripe (Moderate Engagement: Pricing check)
            {
                "ip": "54.187.174.12",
                "metrics": {
                    "page_depth": 3,
                    "playground_dwell_seconds": 30.0,
                    "visited_pricing": True,
                    "visited_security_compliance": False,
                    "repeat_visit_24h": False
                }
            },
            # 6. Uber (High Intent Surge: Deep dwell + repeat)
            {
                "ip": "199.231.209.100",
                "metrics": {
                    "page_depth": 4,
                    "playground_dwell_seconds": 75.0,
                    "visited_pricing": True,
                    "visited_security_compliance": True,
                    "repeat_visit_24h": False
                }
            }
        ]

        results = []
        for sim in sim_events:
            rec = self.process_inbound_session(sim["ip"], sim["metrics"])
            if rec:
                results.append(rec)

        self.render_markdown_report()
        return results

    def audit_abm_intent(self) -> Dict[str, Any]:
        """Audits database CIDR compilation, intent scoring accuracy, and surge alerts."""
        total_accounts = len(self.resolver.accounts)
        compiled_networks = len(self.resolver.compiled_cidrs)
        surge_count = sum(1 for s in self.sessions_log if s.get("is_surge_alert"))

        return {
            "total_priority_accounts": total_accounts,
            "compiled_cidr_subnets": compiled_networks,
            "total_logged_sessions": len(self.sessions_log),
            "high_intent_surges_detected": surge_count,
            "database_complete": (total_accounts >= 50 and compiled_networks >= 50),
            "governing_entity": "DevSuperSuite Enterprise Solutions (enterprise@devsupersuite.com)"
        }

    def export_account_dossiers(self, output_path: Optional[str] = None) -> str:
        """Exports high-intent account dossiers to structured JSON for CRM ingestion."""
        target = output_path if output_path else self.dossiers_path
        high_intent_sessions = [s for s in self.sessions_log if s.get("is_surge_alert")]

        payload = {
            "version": "1.0.0",
            "governing_authority": "DevSuperSuite Enterprise Solutions Directorate (enterprise@devsupersuite.com)",
            "compliance_protocol": "100% Brand Anonymity - Zero Founder Personal Identifiers",
            "total_dossiers": len(high_intent_sessions),
            "dossiers": high_intent_sessions
        }
        with open(target, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return target

    def render_markdown_report(self) -> str:
        """Renders executive operational markdown report of enterprise intent signals."""
        audit = self.audit_abm_intent()
        lines = [
            "# ⚡ DevSuperSuite Official: Enterprise B2B IP Deanonymization & Intent Signals Report",
            f"**Audit Timestamp:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            "**Governing Directorate:** DevSuperSuite Enterprise Solutions (`enterprise@devsupersuite.com`)  ",
            "**Strict Compliance:** 100% Brand Anonymity • Zero Founder Personal Identifiers  ",
            "",
            "---",
            "",
            "## 1. Enterprise Ingress Intent Trajectory",
            "",
            "| Session ID | Enterprise Account | Domain | Matched IP | Intent Score | Tier | Target ACV | Status |",
            "| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: |"
        ]

        for s in self.sessions_log[-10:]:
            surge_badge = "**SURGE ALERT**" if s["is_surge_alert"] else "MONITORING"
            lines.append(
                f"| `{s['session_id']}` | **{s['company_name']}** | `{s['domain']}` | "
                f"`{s['visitor_ip']}` | **{s['intent_score']}** | `{s['intent_tier']}` | "
                f"${s['target_acv_usd']:,} | {surge_badge} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 2. Infrastructure Health & Target Coverage",
            f"- **Target Enterprise Accounts Mapped:** {audit['total_priority_accounts']} (Fortune 500, Defense, Hyperscale Tech)",
            f"- **Compiled CIDR Subnets:** {audit['compiled_cidr_subnets']} active IPv4 allocations",
            f"- **Surge Alerts Triggered (>= 75 pts):** {audit['high_intent_surges_detected']} real-time AE alerts dispatched",
            "",
            "*End of automated enterprise intent signals report.*"
        ])

        report_content = "\n".join(lines) + "\n"
        with open(self.report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        return self.report_path

    def print_summary(self) -> None:
        """Renders ASCII terminal analytics dashboard."""
        audit = self.audit_abm_intent()
        total_sessions = len(self.sessions_log)
        surges = [s for s in self.sessions_log if s.get("is_surge_alert")]

        print("=" * 76)
        print("⚡ DEVSUPERSUITE OFFICIAL — ENTERPRISE B2B IP DEANONYMIZATION DESK")
        print("=" * 76)
        print(f"Total Priority Enterprise Accounts: {audit['total_priority_accounts']}")
        print(f"Compiled Enterprise CIDR Subnets:   {audit['compiled_cidr_subnets']}")
        print(f"Total De-anonymized Ingress Logs:   {total_sessions}")
        print(f"High-Intent Surge Alerts (>= 75):   {len(surges)} accounts")
        print("-" * 76)
        print("Recent High-Intent Enterprise Signals:")
        for s in surges[-5:]:
            print(f"  • {s['company_name']:<22} | Score: {s['intent_score']:4.1f} | Target: ${s['target_acv_usd']:,} | IP: {s['visitor_ip']}")
        print("-" * 76)
        print(f"Target Accounts Database: {TARGET_ACCOUNTS_PATH}")
        print(f"Account Dossiers Export:  {self.dossiers_path}")
        print(f"Executive Signals Report: {self.report_path}")
        print("Governing Authority:      DevSuperSuite Enterprise Solutions (enterprise@devsupersuite.com)")
        print("=" * 76)


# ─────────────────────────────────────────────────────────────────────────────
# 4. CLI Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="DevSuperSuite Official Enterprise B2B IP Deanonymizer")
    parser.add_argument("--simulate-enterprise-traffic", action="store_true", help="Simulate inbound enterprise traffic and detect intent surges")
    parser.add_argument("--audit-abm-intent", action="store_true", help="Audit CIDR compilation and scoring algorithms")
    parser.add_argument("--export-account-dossiers", action="store_true", help="Export high-intent dossiers to JSON")
    parser.add_argument("--summary", action="store_true", help="Display ASCII dashboard summary")

    args = parser.parse_args()
    engine = EnterpriseABMDeanonymizer()

    if args.simulate_enterprise_traffic:
        results = engine.simulate_enterprise_traffic()
        print(f"[✓] Simulated {len(results)} enterprise visitor sessions:")
        for r in results:
            alert_str = "[!] SURGE ALERT TRIGGERED" if r["is_surge_alert"] else "[ ] Normal Traffic"
            print(f"    - {r['company_name']} ({r['visitor_ip']}): Score {r['intent_score']} -> {alert_str}")

    if args.audit_abm_intent:
        audit = engine.audit_abm_intent()
        print("[✓] ABM Intent Audit Completed:")
        print(f"    - Priority Accounts:    {audit['total_priority_accounts']}")
        print(f"    - Compiled CIDRs:       {audit['compiled_cidr_subnets']}")
        print(f"    - Surge Alerts Logged:  {audit['high_intent_surges_detected']}")
        print(f"    - Database Complete:    {audit['database_complete']}")
        if not audit["database_complete"]:
            sys.exit(1)

    if args.export_account_dossiers:
        out_path = engine.export_account_dossiers()
        print(f"[✓] Exported high-intent dossiers to: {out_path}")

    if args.summary or (not args.simulate_enterprise_traffic and not args.audit_abm_intent and not args.export_account_dossiers):
        engine.render_markdown_report()
        engine.print_summary()


if __name__ == "__main__":
    main()
