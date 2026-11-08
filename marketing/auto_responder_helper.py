#!/usr/bin/env python3
"""
DevSuperSuite - Social Infiltration & Lead Outreach Helper
Phase 3: Automated UTM tracking injection & Outreach Tracker generation.

Compliance: 100% Brand Anonymity (DevSuperSuite Official only).
"""

import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import urlencode

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEAD_QUEUE_PATH = os.path.join(BASE_DIR, "active_lead_queue.json")
TRACKER_PATH = os.path.join(BASE_DIR, "outreach_tracker.json")
MARKDOWN_DISPATCH_PATH = os.path.join(BASE_DIR, "outreach_dispatch_queue.md")

WEB_APP_BASE = "https://devsupersuite.web.app"
GUMROAD_BASE = "https://gumroad.com/l/tlzdco"

def determine_utm_source(platform: str) -> str:
    plat_lower = platform.lower()
    if "reddit" in plat_lower:
        return "reddit"
    elif "forum.cursor" in plat_lower or "cursor community" in plat_lower:
        return "cursor_forum"
    elif "github" in plat_lower:
        return "github"
    elif "hacker news" in plat_lower or "hn" in plat_lower:
        return "hackernews"
    elif "twitter" in plat_lower or "x.com" in plat_lower:
        return "twitter"
    return "social_community"

def generate_utm_url(base_url: str, source: str, medium: str, campaign: str, content: str) -> str:
    params = {
        "utm_source": source,
        "utm_medium": medium,
        "utm_campaign": campaign,
        "utm_content": content,
    }
    query_string = urlencode(params)
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{query_string}"

def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "_", slug)

def main():
    if not os.path.exists(LEAD_QUEUE_PATH):
        raise FileNotFoundError(f"Lead queue not found at {LEAD_QUEUE_PATH}")

    with open(LEAD_QUEUE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    leads = data.get("leads", [])
    staged_records = []
    now_iso = datetime.now(timezone.utc).isoformat()
    markdown_lines = [
        "# 🚀 DevSuperSuite Outreach Dispatch & Infiltration Queue",
        f"**Generated**: {now_iso}  ",
        "**Compliance**: 100% Brand Anonymity | DevSuperSuite Official  ",
        f"**Total Staged Leads**: {len(leads)}\n",
        "---\n"
    ]

    for lead in leads:
        lead_id = lead.get("id", "UNKNOWN")
        platform = lead.get("platform", "Unknown")
        category = lead.get("category", "dev_tooling")
        
        source = determine_utm_source(platform)
        medium = "comment" if "reddit" in source else "forum_reply"
        campaign = lead_id.lower().replace("-", "_")
        content_slug = slugify(category)[:24]

        # Generate UTM URLs
        utm_web_app = generate_utm_url(WEB_APP_BASE, source, medium, campaign, content_slug)
        utm_gumroad = generate_utm_url(GUMROAD_BASE, source, medium, campaign, content_slug)

        raw_response = lead.get("tailored_response", "")

        # Inject UTM URLs accurately into response
        injected_response = raw_response.replace(
            "https://devsupersuite.web.app", utm_web_app
        ).replace(
            "https://gumroad.com/l/tlzdco", utm_gumroad
        )

        staged_record = {
            "tracking_id": f"DSS-OUTREACH-{lead_id}",
            "lead_id": lead_id,
            "platform": platform,
            "url": lead.get("url", ""),
            "topic_title": lead.get("topic_title", ""),
            "category": category,
            "pain_point_summary": lead.get("pain_point_summary", ""),
            "priority": lead.get("priority", "NORMAL"),
            "utm_parameters": {
                "utm_source": source,
                "utm_medium": medium,
                "utm_campaign": campaign,
                "utm_content": content_slug
            },
            "tracked_urls": {
                "sandbox_landing": utm_web_app,
                "commercial_checkout": utm_gumroad
            },
            "deployment_status": "STAGED",
            "ready_to_deploy_payload": injected_response,
            "staged_at": now_iso
        }
        staged_records.append(staged_record)

        markdown_lines.extend([
            f"## [{lead_id}] {platform} — {lead.get('topic_title')}",
            f"- **Target Discussion**: {lead.get('url')}",
            f"- **Category / Pain Point**: `{category}` ({lead.get('priority')} Priority)",
            f"- **Tracked Sandbox Link**: `{utm_web_app}`",
            f"- **Tracked Gumroad Link**: `{utm_gumroad}`",
            "",
            "### 📋 Ready-to-Paste Response Payload:",
            "```markdown",
            injected_response,
            "```",
            "",
            "---",
            ""
        ])

    tracker_payload = {
        "metadata": {
            "project": "DevSuperSuite Commercial Distribution",
            "campaign": "Initial 5 Paying Customers ($29 Pro Lifetime)",
            "brand_entity": "DevSuperSuite Official",
            "generated_at": now_iso,
            "total_staged": len(staged_records),
            "status": "READY_FOR_DEPLOYMENT"
        },
        "records": staged_records
    }

    with open(TRACKER_PATH, "w", encoding="utf-8") as f:
        json.dump(tracker_payload, f, indent=2)

    with open(MARKDOWN_DISPATCH_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(markdown_lines))

    print(f"Successfully processed {len(staged_records)} leads.")
    print(f"Tracker JSON saved to: {TRACKER_PATH}")
    print(f"Dispatch Markdown saved to: {MARKDOWN_DISPATCH_PATH}")

if __name__ == "__main__":
    main()
