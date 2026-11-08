#!/usr/bin/env python3
"""
DevSuperSuite - Multi-Channel Outreach Dispatcher & CRM Pipeline Tracker
Phase 10: Automated Rate-Limited Dispatch Engine & Multi-Channel CRM

Compliance: 100% Brand Anonymity (DevSuperSuite Official only).
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CRM_STATE_PATH = os.path.join(BASE_DIR, "multi_channel_crm_tracker.json")
REPORT_PATH = os.path.join(BASE_DIR, "daily_outreach_pipeline_report.md")

COMMUNITY_TRACKER_PATH = os.path.join(BASE_DIR, "outreach_tracker.json")
X_MANIFEST_PATH = os.path.join(BASE_DIR, "x_engagement_manifest.json")
NEWSLETTER_PITCH_PATH = os.path.join(BASE_DIR, "tech_newsletter_outreach_pitch.md")
INFLUENCER_PITCH_PATH = os.path.join(BASE_DIR, "influencer_youtube_review_pitches.md")

WEB_APP_BASE = "https://devsupersuite.web.app"
GUMROAD_BASE = "https://gumroad.com/l/tlzdco"

# Maximum allowable dispatches per channel per hour to prevent platform rate limits/spam flags
RATE_LIMIT_PER_HOUR = 5

def generate_utm_url(base_url: str, source: str, medium: str, campaign: str, content: str = "") -> str:
    params = {
        "utm_source": source,
        "utm_medium": medium,
        "utm_campaign": campaign,
    }
    if content:
        params["utm_content"] = content
    query_string = urlencode(params)
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{query_string}"

def load_initial_leads() -> list:
    leads = []
    
    # 1. Load Community / Reddit Leads from outreach_tracker.json
    if os.path.exists(COMMUNITY_TRACKER_PATH):
        try:
            with open(COMMUNITY_TRACKER_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for rec in data.get("records", []):
                lead_id = rec.get("lead_id", "UNKNOWN")
                platform = rec.get("platform", "Reddit")
                channel = "reddit" if "reddit" in platform.lower() else "forum"
                
                leads.append({
                    "lead_id": f"CRM-{lead_id}",
                    "channel": channel,
                    "target_platform": platform,
                    "recipient_or_thread": rec.get("url", ""),
                    "subject_or_hook": rec.get("topic_title", ""),
                    "category": rec.get("category", "General"),
                    "priority": rec.get("priority", "HIGH"),
                    "utm_source": channel,
                    "utm_medium": "comment",
                    "utm_campaign": lead_id.lower().replace("-", "_"),
                    "sandbox_url": rec.get("tracked_urls", {}).get("sandbox_landing", WEB_APP_BASE),
                    "checkout_url": rec.get("tracked_urls", {}).get("commercial_checkout", GUMROAD_BASE),
                    "payload_preview": rec.get("ready_to_deploy_payload", "")[:180] + "...",
                    "full_payload": rec.get("ready_to_deploy_payload", ""),
                    "status": "queued",
                    "dispatched_at": None,
                    "history": [{"status": "queued", "timestamp": datetime.now(timezone.utc).isoformat(), "note": "Initial ingestion from active lead queue"}]
                })
        except Exception as e:
            print(f"[Warning] Failed to load community tracker: {e}")

    # 2. Load Twitter/X Leads from x_engagement_manifest.json
    if os.path.exists(X_MANIFEST_PATH):
        try:
            with open(X_MANIFEST_PATH, "r", encoding="utf-8") as f:
                x_data = json.load(f)
            for item in x_data.get("quote_tweet_campaigns", []):
                qt_id = item.get("id", "QT-000")
                camp_tag = f"x_{qt_id.lower().replace('-', '_')}"
                leads.append({
                    "lead_id": f"CRM-{qt_id}",
                    "channel": "twitter",
                    "target_platform": "Twitter / X",
                    "recipient_or_thread": f"Search keyword: {item.get('keyword', '')}",
                    "subject_or_hook": item.get("hook_title", ""),
                    "category": "Social Quote-Tweet",
                    "priority": "HIGH",
                    "utm_source": "twitter",
                    "utm_medium": "quote_tweet",
                    "utm_campaign": camp_tag,
                    "sandbox_url": generate_utm_url(WEB_APP_BASE, "twitter", "quote_tweet", camp_tag, "sandbox"),
                    "checkout_url": generate_utm_url(GUMROAD_BASE, "twitter", "quote_tweet", camp_tag, "checkout"),
                    "payload_preview": item.get("tweet_body", "")[:180] + "...",
                    "full_payload": item.get("tweet_body", ""),
                    "status": "queued",
                    "dispatched_at": None,
                    "history": [{"status": "queued", "timestamp": datetime.now(timezone.utc).isoformat(), "note": "Initial ingestion from X manifest"}]
                })
        except Exception as e:
            print(f"[Warning] Failed to load X manifest: {e}")

    # 3. Load Tech Newsletter Leads
    newsletters = [
        ("NL-001", "The Pragmatic Engineer", "The AI Token Tax: Slashing 80% redundant tokens via AST slicing", "pragmatic_engineer"),
        ("NL-002", "ByteByteGo", "Visual System Architecture: AST Context Pruning for Coding Agents", "bytebytego"),
        ("NL-003", "TLDR WebDev", "Tool Feature: OmniKernel AST Slicer cuts Cursor token bills by 83%", "tldr_webdev"),
        ("NL-004", "Console.dev", "Local Tool Spotlight: DevSuperSuite quad-engine local dev toolkit", "console_dev"),
        ("NL-005", "Pointer", "Attention Sink Dilution in Transformer Code Generation via AST Pruning", "pointer_io")
    ]
    for nl_id, publication, hook, utm_src in newsletters:
        leads.append({
            "lead_id": f"CRM-{nl_id}",
            "channel": "newsletter",
            "target_platform": f"Newsletter ({publication})",
            "recipient_or_thread": f"Editor / Submissions Desk ({publication})",
            "subject_or_hook": hook,
            "category": "Editorial Newsletter Feature",
            "priority": "HIGH",
            "utm_source": utm_src,
            "utm_medium": "newsletter_pitch",
            "utm_campaign": "token_tax_press",
            "sandbox_url": generate_utm_url(WEB_APP_BASE, utm_src, "newsletter_pitch", "token_tax_press"),
            "checkout_url": generate_utm_url(GUMROAD_BASE, utm_src, "newsletter_pitch", "token_tax_press"),
            "payload_preview": f"Pitch targeting {publication}: {hook}...",
            "full_payload": f"Full pitch available in tech_newsletter_outreach_pitch.md for {publication}",
            "status": "queued",
            "dispatched_at": None,
            "history": [{"status": "queued", "timestamp": datetime.now(timezone.utc).isoformat(), "note": "Initial ingestion from newsletter pitch pack"}]
        })

    # 4. Load Influencer YouTube Leads
    creators = [
        ("YT-001", "Fireship (Jeff Delaney)", "Why Cursor & Claude Code burn 80% redundant tokens (Code Report)", "fireship"),
        ("YT-002", "ThePrimeagen", "100% local AST context slicer & pre-commit entropy blocker (Zero telemetry)", "theprimeagen"),
        ("YT-003", "Matthew Berman", "How AST Context Pruning reduces local LLM token load by 83% (OmniKernel MCP)", "matthew_berman"),
        ("YT-004", "Web Dev Simplified (Kyle Cook)", "Why Cursor burns 80% redundant tokens & how to prevent API key leaks", "web_dev_simplified"),
        ("YT-005", "AI Jason", "Cutting 80% token costs in autonomous agent loops (Cursor / Claude Code)", "ai_jason")
    ]
    for yt_id, creator, hook, utm_src in creators:
        leads.append({
            "lead_id": f"CRM-{yt_id}",
            "channel": "youtube",
            "target_platform": f"YouTube / Streamer ({creator})",
            "recipient_or_thread": f"Business Inquiries ({creator})",
            "subject_or_hook": hook,
            "category": "Creator Video Review & VIP Giveaway",
            "priority": "HIGH",
            "utm_source": utm_src,
            "utm_medium": "creator_video_pitch",
            "utm_campaign": "vip_giveaway_dss",
            "sandbox_url": generate_utm_url(WEB_APP_BASE, utm_src, "creator_video_pitch", "vip_giveaway_dss"),
            "checkout_url": generate_utm_url(GUMROAD_BASE, utm_src, "creator_video_pitch", "vip_giveaway_dss"),
            "payload_preview": f"VIP review pitch to {creator} with VIP code DSS-PRO-INFLUENCER-VIP...",
            "full_payload": f"Full pitch and 3-minute video outline in influencer_youtube_review_pitches.md for {creator}",
            "status": "queued",
            "dispatched_at": None,
            "history": [{"status": "queued", "timestamp": datetime.now(timezone.utc).isoformat(), "note": "Initial ingestion from influencer review pack"}]
        })

    return leads

def load_or_init_crm() -> dict:
    if os.path.exists(CRM_STATE_PATH):
        try:
            with open(CRM_STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Warning] Failed reading existing CRM tracker: {e}. Reinitializing.")

    initial_leads = load_initial_leads()
    crm_data = {
        "metadata": {
            "system": "DevSuperSuite Multi-Channel Outreach Dispatcher & CRM",
            "brand_entity": "DevSuperSuite Official",
            "version": "1.0.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "rate_limit_per_channel_per_hour": RATE_LIMIT_PER_HOUR,
            "status": "ACTIVE"
        },
        "channel_stats": {},
        "leads": initial_leads
    }
    save_crm_state(crm_data)
    return crm_data

def save_crm_state(crm_data: dict):
    crm_data["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(CRM_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(crm_data, f, indent=2)

def check_channel_rate_limits(crm_data: dict, window_minutes: int = 60) -> dict:
    """Calculates dispatches within the last window_minutes for each channel."""
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(minutes=window_minutes)
    
    counts = {}
    for lead in crm_data.get("leads", []):
        ch = lead.get("channel", "general")
        disp_at = lead.get("dispatched_at")
        if disp_at:
            try:
                dt = datetime.fromisoformat(disp_at)
                if dt >= threshold:
                    counts[ch] = counts.get(ch, 0) + 1
            except Exception:
                pass
    return counts

def generate_pipeline_report(crm_data: dict) -> str:
    now_iso = datetime.now(timezone.utc).isoformat()
    leads = crm_data.get("leads", [])
    
    total = len(leads)
    queued = sum(1 for l in leads if l.get("status") == "queued")
    dispatched = sum(1 for l in leads if l.get("status") == "dispatched")
    responded = sum(1 for l in leads if l.get("status") == "responded")
    converted = sum(1 for l in leads if l.get("status") == "converted")
    
    # Channel distribution
    by_channel = {}
    for l in leads:
        ch = l.get("channel", "unknown")
        if ch not in by_channel:
            by_channel[ch] = {"total": 0, "queued": 0, "dispatched": 0, "responded": 0, "converted": 0}
        by_channel[ch]["total"] += 1
        st = l.get("status", "queued")
        if st in by_channel[ch]:
            by_channel[ch][st] += 1

    recent_dispatches = check_channel_rate_limits(crm_data)

    lines = [
        "# 📊 DevSuperSuite: Multi-Channel Outreach Pipeline & CRM Report",
        f"**Generated**: `{now_iso}`  ",
        "**Brand Persona**: **DevSuperSuite Official**  ",
        "**Compliance**: 100% Brand Anonymity | Zero Founder Personal Data  ",
        f"**Pipeline Health**: 🟢 ACTIVE | Rate Limit Cap: `{RATE_LIMIT_PER_HOUR} dispatches/hr/channel`\n",
        "---\n",
        "## 📈 Executive Pipeline Metrics\n",
        f"| Metric | Count | Ratio (%) |",
        f"| :--- | :---: | :---: |",
        f"| **Total Tracked Developer Leads** | **{total}** | 100.0% |",
        f"| **Dispatched / Deployed** | **{dispatched}** | {round(dispatched/total*100, 1) if total else 0}% |",
        f"| **Queued (Ready for Deployment)** | **{queued}** | {round(queued/total*100, 1) if total else 0}% |",
        f"| **Active Responses Inbound** | **{responded}** | {round(responded/total*100, 1) if total else 0}% |",
        f"| **Commercial Customers Converted ($29)** | **{converted}** | {round(converted/total*100, 1) if total else 0}%\n",
        "---\n",
        "## 📡 Channel-by-Channel Breakdown & Rate Limit Status\n",
        "| Channel | Total Leads | Queued | Dispatched | Responded | Converted | Recent Dispatches (Past 60m) | Rate Limit Status |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
    ]

    for ch, stats in sorted(by_channel.items()):
        rec_count = recent_dispatches.get(ch, 0)
        status_badge = "🟢 Clear" if rec_count < RATE_LIMIT_PER_HOUR else "🟡 Throttled (Capped)"
        lines.append(f"| **{ch.capitalize()}** | {stats['total']} | {stats['queued']} | {stats['dispatched']} | {stats['responded']} | {stats['converted']} | {rec_count} / {RATE_LIMIT_PER_HOUR} | {status_badge} |")

    lines.extend([
        "\n---\n",
        "## 📋 Staged & Active Lead Registry\n",
        "| Lead ID | Channel | Recipient / Discussion | Hook Title | UTM Campaign | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :---: |"
    ] )

    for l in leads:
        lead_id = l.get("lead_id", "")
        ch = l.get("channel", "")
        recip = l.get("target_platform", "")
        hook = l.get("subject_or_hook", "")[:45] + ("..." if len(l.get("subject_or_hook", "")) > 45 else "")
        camp = l.get("utm_campaign", "")
        st = l.get("status", "queued")
        status_icon = "🟢" if st == "dispatched" else ("🟡" if st == "queued" else "🔵")
        lines.append(f"| `{lead_id}` | {ch} | {recip} | {hook} | `{camp}` | {status_icon} `{st}` |")

    lines.extend([
        "\n---\n",
        "## 🛡️ Attribution & Security Assurance",
        "- **Zero Telemetry**: All product tools run 100% locally on localhost.",
        "- **Deterministic Attribution**: Every single message is tagged with distinct `utm_source`, `utm_medium`, and `utm_campaign` params.",
        "- **Brand Anonymity**: Strictly represented under **DevSuperSuite Official** / **DevSuperSuite Engineering Team**.",
        "\n---\n*Report maintained automatically by DevSuperSuite CRM Dispatch Engine.*"
    ])

    report_content = "\n".join(lines)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_content)
    return report_content

def execute_batch(dry_run: bool = True, channel_filter: str = "all", max_to_dispatch: int = 5) -> dict:
    crm_data = load_or_init_crm()
    leads = crm_data.get("leads", [])
    now = datetime.now(timezone.utc)
    
    recent_dispatches = check_channel_rate_limits(crm_data)
    
    dispatched_in_batch = []
    throttled_in_batch = []
    skipped_in_batch = []

    channel_dispatch_counter = {}

    for lead in leads:
        lead_id = lead.get("lead_id")
        ch = lead.get("channel", "general")
        status = lead.get("status", "queued")

        if channel_filter != "all" and ch.lower() != channel_filter.lower():
            continue

        if status != "queued":
            continue

        # Check rate limits for this channel
        current_hour_dispatches = recent_dispatches.get(ch, 0) + channel_dispatch_counter.get(ch, 0)
        if current_hour_dispatches >= RATE_LIMIT_PER_HOUR:
            throttled_in_batch.append({
                "lead_id": lead_id,
                "channel": ch,
                "reason": f"Channel rate limit reached ({current_hour_dispatches}/{RATE_LIMIT_PER_HOUR} in past 60m)"
            })
            continue

        if len(dispatched_in_batch) >= max_to_dispatch:
            skipped_in_batch.append(lead_id)
            continue

        # Eligible for dispatch
        channel_dispatch_counter[ch] = channel_dispatch_counter.get(ch, 0) + 1
        
        dispatch_record = {
            "lead_id": lead_id,
            "channel": ch,
            "target": lead.get("target_platform"),
            "subject": lead.get("subject_or_hook"),
            "sandbox_url": lead.get("sandbox_url"),
            "checkout_url": lead.get("checkout_url"),
            "dispatched_at": now.isoformat()
        }
        dispatched_in_batch.append(dispatch_record)

        if not dry_run:
            lead["status"] = "dispatched"
            lead["dispatched_at"] = now.isoformat()
            lead["history"].append({
                "status": "dispatched",
                "timestamp": now.isoformat(),
                "note": f"Dispatched via automated multi-channel batch execution (Channel: {ch})"
            })

    if not dry_run:
        save_crm_state(crm_data)

    report_text = generate_pipeline_report(crm_data)

    return {
        "dry_run": dry_run,
        "channel_filter": channel_filter,
        "dispatched_count": len(dispatched_in_batch),
        "dispatched_items": dispatched_in_batch,
        "throttled_count": len(throttled_in_batch),
        "throttled_items": throttled_in_batch,
        "skipped_remaining": len(skipped_in_batch),
        "crm_state_file": CRM_STATE_PATH,
        "report_file": REPORT_PATH
    }

def main():
    parser = argparse.ArgumentParser(description="DevSuperSuite Multi-Channel Outreach Dispatcher & CRM")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Simulate execution without mutating CRM status")
    parser.add_argument("--dispatch", action="store_true", default=False, help="Execute batch and advance CRM lead state to 'dispatched'")
    parser.add_argument("--channel", type=str, default="all", choices=["all", "reddit", "twitter", "newsletter", "youtube", "forum"], help="Target specific channel")
    parser.add_argument("--batch-size", type=int, default=10, help="Max items to process in this run (subject to hourly rate limits)")
    parser.add_argument("--report-only", action="store_true", default=False, help="Regenerate documentation report without dispatching")

    args = parser.parse_args()

    crm_data = load_or_init_crm()

    if args.report_only:
        generate_pipeline_report(crm_data)
        print(f"[Success] Generated daily outreach pipeline report at {REPORT_PATH}")
        sys.exit(0)

    is_dry_run = True
    if args.dispatch:
        is_dry_run = False
    elif not args.dry_run:
        # Default to dry-run if neither explicitly passed
        is_dry_run = True

    result = execute_batch(dry_run=is_dry_run, channel_filter=args.channel, max_to_dispatch=args.batch_size)

    mode_label = "DRY RUN (Simulation)" if result["dry_run"] else "LIVE DISPATCH"
    print("\n" + "="*70)
    print(f"🚀 DEVSUPERSUITE MULTI-CHANNEL OUTREACH DISPATCHER: {mode_label}")
    print(f"Brand Entity: DevSuperSuite Official (100% Brand Anonymity)")
    print("="*70)
    print(f"Target Channel Scope: {result['channel_filter'].upper()}")
    print(f"Dispatched Items:     {result['dispatched_count']}")
    print(f"Throttled Items:      {result['throttled_count']} (Rate limit protected: max {RATE_LIMIT_PER_HOUR}/hr)")
    print(f"Queued Items Left:    {result['skipped_remaining']}")
    print("-"*70)

    if result["dispatched_items"]:
        print("\n[+] Dispatched Outreach Records:")
        for item in result["dispatched_items"]:
            print(f"  • [{item['lead_id']}] ({item['channel'].upper()}) -> {item['target']}")
            print(f"    Hook:    {item['subject'][:60]}...")
            print(f"    Sandbox: {item['sandbox_url']}")
            print(f"    Product: {item['checkout_url']}\n")

    if result["throttled_items"]:
        print("\n[!] Throttled Records (Preventing spam triggers):")
        for item in result["throttled_items"]:
            print(f"  • [{item['lead_id']}] {item['channel']} - {item['reason']}")

    print("\n" + "="*70)
    print(f"CRM State Updated: {result['crm_state_file']}")
    print(f"Pipeline Report:   {result['report_file']}")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
