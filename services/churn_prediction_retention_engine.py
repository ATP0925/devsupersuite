#!/usr/bin/env python3
"""
⚡ DevSuperSuite Official: Developer Churn Prediction & Retention Interception Engine
File: churn_prediction_retention_engine.py
Version: 1.0.0
Governing Authority: DevSuperSuite Customer Success Directorate (success@devsupersuite.com)
Strict Protocol: 100% Brand Anonymity - DevSuperSuite Official Only - Zero Founder Personal Identifiers

Features:
- Predictive telemetry scanner measuring usage frequency, AST slicing volumes, and pre-commit hook execution drops.
- Composite Churn Risk Index (0 to 100) scoring developers into LOW, MEDIUM, HIGH, and CRITICAL bands.
- Dynamic retention workflows (Language optimization guides, 50% Team upgrade coupon 'RETAIN50', 1-on-1 architectural triage).
- Cooldown safety guards to prevent repetitive message fatigue.
- Full CLI interfaces: --audit-churn-risk, --trigger-retention-flow, --export-risk-registry, --summary.
"""

import os
import sys
import json
import uuid
import hashlib
import argparse
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Base Paths Setup
SERVICES_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(SERVICES_DIR)
DATA_DIR = os.path.join(SCRATCH_DIR, "data")
MARKETING_DIR = os.path.join(SCRATCH_DIR, "marketing")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MARKETING_DIR, exist_ok=True)

USAGE_TELEMETRY_PATH = os.path.join(DATA_DIR, "developer_usage_telemetry.json")
CHURN_REGISTRY_PATH = os.path.join(DATA_DIR, "churn_risk_registry.json")
RETENTION_QUEUE_PATH = os.path.join(DATA_DIR, "retention_interventions_queue.json")
MARKDOWN_RETENTION_REPORT_PATH = os.path.join(MARKETING_DIR, "retention_intervention_manifest.md")

DEFAULT_GUMROAD_UPGRADE_URL = "https://gumroad.com/l/tlzdco?discount=RETAIN50&upgrade=team"
DEFAULT_TRIAGE_CALENDAR_URL = "https://devsupersuite.web.app/schedule-architect-triage"


class ChurnRiskScorer:
    """Calculates composite developer churn risk index based on telemetry vectors."""

    # Risk Weights
    RECENCY_WEIGHT = 0.40          # Inactivity / dwell drop (max 40 pts)
    AST_VOLUME_DROP_WEIGHT = 0.30  # AST compression volume reduction (max 30 pts)
    PRECOMMIT_DROP_WEIGHT = 0.20   # Git pre-commit hook invocations (max 20 pts)
    ERROR_RATE_WEIGHT = 0.10       # Client error / crash spikes (max 10 pts)

    @classmethod
    def calculate_score(
        cls,
        days_inactive: float,
        ast_volume_drop_pct: float,
        precommit_drop_pct: float,
        crash_rate_pct: float
    ) -> Dict[str, Any]:
        """
        Computes 0 to 100 risk score and categorizes into LOW, MEDIUM, HIGH, or CRITICAL.
        """
        # 1. Recency Penalty (0 to 40)
        # 0-2 days: 0 pts, 3-7 days: linear scaling, >14 days: 40 pts
        if days_inactive <= 2:
            recency_pts = 0.0
        elif days_inactive >= 14:
            recency_pts = 40.0
        else:
            recency_pts = ((days_inactive - 2) / 12.0) * 40.0

        # 2. AST Volume Drop Penalty (0 to 30)
        # ast_volume_drop_pct: 0% to 100%
        ast_drop_clamped = max(0.0, min(100.0, ast_volume_drop_pct))
        ast_pts = (ast_drop_clamped / 100.0) * 30.0

        # 3. Precommit Drop Penalty (0 to 20)
        precommit_drop_clamped = max(0.0, min(100.0, precommit_drop_pct))
        precommit_pts = (precommit_drop_clamped / 100.0) * 20.0

        # 4. Crash Rate Penalty (0 to 10)
        crash_rate_clamped = max(0.0, min(10.0, crash_rate_pct))
        crash_pts = (crash_rate_clamped / 10.0) * 10.0

        total_score = round(recency_pts + ast_pts + precommit_pts + crash_pts, 1)
        total_score = min(100.0, max(0.0, total_score))

        # Categorize
        if total_score <= 30.0:
            tier = "LOW"
            recommended_action = "MONITOR_HEALTHY"
        elif total_score <= 65.0:
            tier = "MEDIUM"
            recommended_action = "LANGUAGE_OPTIMIZATION_NURTURE"
        elif total_score <= 85.0:
            tier = "HIGH"
            recommended_action = "OFFER_50_PCT_TEAM_UPGRADE"
        else:
            tier = "CRITICAL"
            recommended_action = "DEDICATED_ARCHITECT_TRIAGE_CALL"

        return {
            "churn_risk_score": total_score,
            "risk_tier": tier,
            "recommended_action": recommended_action,
            "breakdown": {
                "recency_penalty": round(recency_pts, 1),
                "ast_volume_drop_penalty": round(ast_pts, 1),
                "precommit_drop_penalty": round(precommit_pts, 1),
                "crash_rate_penalty": round(crash_pts, 1)
            }
        }


class ChurnPredictionRetentionEngine:
    """Institutional developer retention and churn interception engine for DevSuperSuite."""

    def __init__(
        self,
        telemetry_path: str = USAGE_TELEMETRY_PATH,
        registry_path: str = CHURN_REGISTRY_PATH,
        queue_path: str = RETENTION_QUEUE_PATH
    ):
        self.telemetry_path = telemetry_path
        self.registry_path = registry_path
        self.queue_path = queue_path

        self.telemetry_data: List[Dict[str, Any]] = self._load_or_init_telemetry()
        self.risk_registry: List[Dict[str, Any]] = self._load_or_init_registry()
        self.interventions_queue: List[Dict[str, Any]] = self._load_or_init_queue()

    def _load_or_init_telemetry(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.telemetry_path):
            try:
                with open(self.telemetry_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        now = datetime.now(timezone.utc)
        seeds = [
            {
                "customer_email": "dev.marcus@quantumcloud.de",
                "customer_name": "Marcus Vance",
                "plan_name": "Hacker Solo",
                "primary_language": "Python",
                "ide_environment": "Cursor",
                "days_inactive": 1.5,
                "ast_volume_drop_pct": 5.0,
                "precommit_drop_pct": 0.0,
                "crash_rate_pct": 0.0,
                "last_active_at": (now - timedelta(days=1.5)).isoformat()
            },
            {
                "customer_email": "techlead.priya@fintechscale.in",
                "customer_name": "Priya Sharma",
                "plan_name": "Team 5-Seat",
                "primary_language": "TypeScript",
                "ide_environment": "Claude Code",
                "days_inactive": 5.0,
                "ast_volume_drop_pct": 45.0,
                "precommit_drop_pct": 40.0,
                "crash_rate_pct": 1.2,
                "last_active_at": (now - timedelta(days=5)).isoformat()
            },
            {
                "customer_email": "kenji.sato@systems-tokyo.jp",
                "customer_name": "Kenji Sato",
                "plan_name": "Hacker Solo",
                "primary_language": "Rust",
                "ide_environment": "Windsurf",
                "days_inactive": 11.0,
                "ast_volume_drop_pct": 85.0,
                "precommit_drop_pct": 75.0,
                "crash_rate_pct": 2.5,
                "last_active_at": (now - timedelta(days=11)).isoformat()
            },
            {
                "customer_email": "alex.vance@legacycorp.org",
                "customer_name": "Alex Vance",
                "plan_name": "Hacker Solo",
                "primary_language": "C++",
                "ide_environment": "VS Code",
                "days_inactive": 18.0,
                "ast_volume_drop_pct": 100.0,
                "precommit_drop_pct": 100.0,
                "crash_rate_pct": 8.0,
                "last_active_at": (now - timedelta(days=18)).isoformat()
            }
        ]
        self._save_json(self.telemetry_path, seeds)
        return seeds

    def _load_or_init_registry(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _load_or_init_queue(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.queue_path):
            try:
                with open(self.queue_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_json(self, path: str, data: Any) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def audit_churn_risk(self) -> List[Dict[str, Any]]:
        """
        Scans all developer accounts, computes composite churn risk score,
        and saves updated risk registry.
        """
        now = datetime.now(timezone.utc)
        results = []

        for dev in self.telemetry_data:
            score_data = ChurnRiskScorer.calculate_score(
                days_inactive=dev.get("days_inactive", 0.0),
                ast_volume_drop_pct=dev.get("ast_volume_drop_pct", 0.0),
                precommit_drop_pct=dev.get("precommit_drop_pct", 0.0),
                crash_rate_pct=dev.get("crash_rate_pct", 0.0)
            )

            record = {
                "customer_email": dev["customer_email"],
                "customer_name": dev.get("customer_name", "Developer"),
                "plan_name": dev.get("plan_name", "Hacker Solo"),
                "primary_language": dev.get("primary_language", "Python"),
                "ide_environment": dev.get("ide_environment", "Cursor"),
                "days_inactive": dev.get("days_inactive", 0.0),
                "ast_volume_drop_pct": dev.get("ast_volume_drop_pct", 0.0),
                "churn_risk_score": score_data["churn_risk_score"],
                "risk_tier": score_data["risk_tier"],
                "recommended_action": score_data["recommended_action"],
                "breakdown": score_data["breakdown"],
                "audited_at": now.isoformat()
            }
            results.append(record)

        self.risk_registry = results
        self._save_json(self.registry_path, self.risk_registry)
        return results

    def trigger_retention_flow(self) -> List[Dict[str, Any]]:
        """
        Synthesizes personalized re-engagement workflows and retention offers
        for MEDIUM, HIGH, and CRITICAL risk developer accounts.
        """
        if not self.risk_registry:
            self.audit_churn_risk()

        now = datetime.now(timezone.utc)
        new_interventions = []

        for record in self.risk_registry:
            tier = record["risk_tier"]
            if tier == "LOW":
                continue

            email = record["customer_email"]
            name = record["customer_name"]
            lang = record["primary_language"]
            ide = record["ide_environment"]

            # Deduplication cooldown: don't create multiple interventions for same email within 14 days
            already_queued = any(
                q["customer_email"] == email and 
                (now - datetime.fromisoformat(q["created_at"].replace("Z", "+00:00"))).days < 14
                for q in self.interventions_queue
            )
            if already_queued:
                continue

            intervention_id = f"RET-{uuid.uuid4().hex[:6].upper()}"

            if tier == "MEDIUM":
                # Tier 1: Nurture & Performance Optimization Tips
                subject = f"Optimizing your {lang} AST Context Slicing in {ide}"
                body = f"""Hi {name},

We noticed your AST context compression volume dropped over the past week in {ide}.

Here is a 60-second optimization guide tailored for your {lang} monorepo:
1. Enable aggressive tree-sitter node pruning: `omnikernel config --language {lang.lower()} --prune-depth aggressive`
2. Auto-repair your Git pre-commit hook: `omnikernel hook install --git`
3. Check zero-day secret defense status: `omnikernel doctor`

Need help tuning AST grammars or custom test invariants? Reply to this note and our Customer Success team will assist directly.

Best regards,
DevSuperSuite Customer Success Directorate
success@devsupersuite.com • https://devsupersuite.web.app
"""
                action_payload = {
                    "action_type": "NURTURE_OPTIMIZATION_TIPS",
                    "resource_url": f"https://devsupersuite.web.app/docs/{lang.lower()}-optimization"
                }

            elif tier == "HIGH":
                # Tier 2: 50% Team License Upgrade Incentive (RETAIN50)
                subject = f"⚡ Exclusive 50% Upgrade to Team 5-Seat Pack (Coupon: RETAIN50)"
                body = f"""Hi {name},

As an early adopter of DevSuperSuite, we want to ensure your entire engineering pod benefits from zero-rot context slicing and leak protection.

For the next 7 days, you can upgrade your account to the full Team 5-Seat Commercial Pack for 50% OFF ($74.50 instead of $149):

Claim Your 50% Upgrade Now:
{DEFAULT_GUMROAD_UPGRADE_URL}&email={email}

Includes:
✓ 5 Commercial Developer Deployments
✓ Team Centralized Shannon Entropy Rule Configs
✓ Priority Engineering Bridge & Telegram Support
✓ 100% Offline Standalone Ed25519 Keys

Best regards,
DevSuperSuite Customer Success Desk
success@devsupersuite.com
"""
                action_payload = {
                    "action_type": "OFFER_50_PCT_UPGRADE",
                    "coupon_code": "RETAIN50",
                    "offer_price_usd": 74.50,
                    "upgrade_url": f"{DEFAULT_GUMROAD_UPGRADE_URL}&email={email}"
                }

            else:  # CRITICAL
                # Tier 3: Dedicated 1-on-1 Architect Triage Call
                subject = f"🚨 Priority Triage Request: DevSuperSuite Performance Check for {name}"
                body = f"""Hi {name},

Our telemetry flagged that your OmniKernel daemon hasn't run in {int(record['days_inactive'])} days. If you experienced compilation delays, IDE crashes in {ide}, or configuration friction, we want to fix it immediately.

We have reserved a complimentary 30-minute 1-on-1 session with a Principal Systems Architect to debug your environment and calibrate your AST parsers:

Schedule Your Dedicated Architect Session:
{DEFAULT_TRIAGE_CALENDAR_URL}?email={email}

Your satisfaction is guaranteed by our 30-Day Money Back Guarantee. If DevSuperSuite isn't delivering immediate value, we will issue a full refund upon request.

Sincerely,
DevSuperSuite Customer Success Directorate
success@devsupersuite.com
"""
                action_payload = {
                    "action_type": "DEDICATED_ARCHITECT_TRIAGE",
                    "calendar_url": f"{DEFAULT_TRIAGE_CALENDAR_URL}?email={email}",
                    "refund_guarantee_highlighted": True
                }

            intervention_record = {
                "intervention_id": intervention_id,
                "customer_email": email,
                "customer_name": name,
                "risk_tier": tier,
                "churn_risk_score": record["churn_risk_score"],
                "subject": subject,
                "body": body,
                "payload": action_payload,
                "status": "QUEUED_FOR_DISPATCH",
                "created_at": now.isoformat()
            }
            new_interventions.append(intervention_record)
            self.interventions_queue.append(intervention_record)

        self._save_json(self.queue_path, self.interventions_queue)
        self._write_markdown_manifest()
        return new_interventions

    def _write_markdown_manifest(self) -> None:
        """Writes operational markdown runbook of retention dispatches."""
        md_lines = [
            "# ⚡ DevSuperSuite Official: Developer Retention & Churn Interception Manifest",
            f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            "**Governing Authority:** DevSuperSuite Customer Success (success@devsupersuite.com)  ",
            "**Strict Compliance:** 100% Brand Anonymous • Zero Founder Personal Identifiers  ",
            "",
            "---",
            "",
            "## 1. Active Retention Interventions Queue",
            "",
            "| Intervention ID | Recipient Email | Risk Score | Risk Tier | Retention Action Strategy | Status |",
            "| :--- | :--- | :---: | :---: | :--- | :---: |"
        ]

        for item in self.interventions_queue:
            md_lines.append(
                f"| `{item['intervention_id']}` | `{item['customer_email']}` | "
                f"**{item['churn_risk_score']}** | `{item['risk_tier']}` | "
                f"`{item['payload']['action_type']}` | **{item['status']}** |"
            )

        md_lines.extend([
            "",
            "---",
            "",
            "## 2. Retention Tier Protocol Reference",
            "- **MEDIUM (31-65):** AST optimization tips and pre-commit hook repair.",
            "- **HIGH (66-85):** 50% discount on team license upgrade (`RETAIN50`).",
            "- **CRITICAL (86-100):** Complimentary 1-on-1 Principal Architect triage session.",
            "",
            "*End of automated churn retention manifest.*"
        ])

        with open(MARKDOWN_RETENTION_REPORT_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines) + "\n")

    def print_summary(self) -> None:
        """Renders comprehensive ASCII terminal dashboard."""
        if not self.risk_registry:
            self.audit_churn_risk()

        total_devs = len(self.risk_registry)
        low_count = sum(1 for r in self.risk_registry if r["risk_tier"] == "LOW")
        med_count = sum(1 for r in self.risk_registry if r["risk_tier"] == "MEDIUM")
        high_count = sum(1 for r in self.risk_registry if r["risk_tier"] == "HIGH")
        crit_count = sum(1 for r in self.risk_registry if r["risk_tier"] == "CRITICAL")
        avg_score = round(sum(r["churn_risk_score"] for r in self.risk_registry) / total_devs, 1) if total_devs > 0 else 0.0

        print("=" * 76)
        print("⚡ DEVSUPERSUITE OFFICIAL — DEVELOPER CHURN PREDICTION & RETENTION DESK")
        print("=" * 76)
        print(f"Total Monitored Developer Accounts: {total_devs}")
        print(f"Average Account Churn Risk Score:   {avg_score} / 100")
        print("-" * 76)
        print(f"Risk Tier Breakdown:")
        print(f"  • LOW RISK      (Score 0-30)   : {low_count} developers [HEALTHY]")
        print(f"  • MEDIUM RISK   (Score 31-65)  : {med_count} developers [NURTURE REQUIRED]")
        print(f"  • HIGH RISK     (Score 66-85)  : {high_count} developers [50% UPGRADE INTERVENTION]")
        print(f"  • CRITICAL RISK (Score 86-100) : {crit_count} developers [1-ON-1 TRIAGE ESCALATION]")
        print("-" * 76)
        print(f"Active Retention Queue Items:       {len(self.interventions_queue)}")
        print(f"Registry File: {self.registry_path}")
        print(f"Queue File:    {self.queue_path}")
        print(f"Manifest Runbook: {MARKDOWN_RETENTION_REPORT_PATH}")
        print("=" * 76)


def main():
    parser = argparse.ArgumentParser(description="DevSuperSuite Official Developer Churn Prediction & Retention Engine")
    parser.add_argument("--audit-churn-risk", action="store_true", help="Audit developer churn risk and update registry")
    parser.add_argument("--trigger-retention-flow", action="store_true", help="Trigger automated dynamic retention workflows")
    parser.add_argument("--export-risk-registry", action="store_true", help="Export churn risk registry and generate manifest")
    parser.add_argument("--summary", action="store_true", help="Print summary dashboard")

    args = parser.parse_args()
    engine = ChurnPredictionRetentionEngine()

    if args.audit_churn_risk:
        audited = engine.audit_churn_risk()
        print(f"[✓] Audited {len(audited)} developer accounts for churn risk:")
        for a in audited:
            print(f"    - {a['customer_email']}: Score {a['churn_risk_score']} [{a['risk_tier']}] -> {a['recommended_action']}")

    if args.trigger_retention_flow:
        interventions = engine.trigger_retention_flow()
        print(f"[✓] Generated {len(interventions)} new retention interventions in queue:")
        for i in interventions:
            print(f"    - [{i['risk_tier']}] {i['customer_email']} -> {i['payload']['action_type']}")

    if args.export_risk_registry:
        engine.audit_churn_risk()
        engine._write_markdown_manifest()
        print(f"[✓] Exported Churn Risk Registry to: {CHURN_REGISTRY_PATH}")
        print(f"[✓] Exported Retention Manifest to: {MARKDOWN_RETENTION_REPORT_PATH}")

    if args.summary or (not args.audit_churn_risk and not args.trigger_retention_flow and not args.export_risk_registry):
        engine.print_summary()


if __name__ == "__main__":
    main()
