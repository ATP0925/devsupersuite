#!/usr/bin/env python3
"""
Unit and integration tests for DevSuperSuite Discord & Telegram Developer Community Bot Engine (Phase 47).
Validates cryptographic license verification, slash commands (/verify-license, /benchmark-ast, /simulate-voice, /docs),
auto-role assignment, anti-spam phishing filters, and 100% Brand Anonymity Protocol.
"""

import json
import os
import sys
import tempfile
import pytest

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from marketing.community_onboarding_bot_engine import (
    CommunityOnboardingBotEngine,
    CryptographicLicenseValidator,
    LicenseVerificationResult,
    AntiSpamResult,
    BRAND_ENTITY,
    BRAND_EMAIL,
    WEB_APP_BASE,
    GUMROAD_BASE,
    PROMO_CODE,
    PROMO_PRICE,
)


@pytest.fixture
def bot() -> CommunityOnboardingBotEngine:
    return CommunityOnboardingBotEngine()


# TEST 1: Bot Manifest Schema and Command Specifications
def test_bot_manifest_schema(bot: CommunityOnboardingBotEngine):
    manifest = bot.generate_bot_manifest()

    assert manifest["bot_name"] == "DevSuperSuite Community Onboarding & Verification Bot"
    assert manifest["brand"] == BRAND_ENTITY
    assert manifest["contact_email"] == BRAND_EMAIL
    assert "Discord" in manifest["platforms"]
    assert "Telegram" in manifest["platforms"]

    cmd_names = [c["name"] for c in manifest["slash_commands"]]
    assert "verify-license" in cmd_names
    assert "benchmark-ast" in cmd_names
    assert "simulate-voice" in cmd_names
    assert "docs" in cmd_names

    roles = manifest["auto_roles"]
    assert "VIP Lifetime Member" in roles
    assert "Enterprise SCIF Architect" in roles
    assert "Verified Contributor" in roles


# TEST 2: Valid Pro Lifetime License Verification & Auto-Role Assignment
def test_verify_license_valid_pro(bot: CommunityOnboardingBotEngine):
    res = bot.verify_license_command("DSS-PRO-2026-A1B2C3D4")

    assert res.valid is True
    assert res.tier == "Pro Lifetime"
    assert res.assigned_role == "VIP Lifetime Member"
    assert res.seats == 1
    assert "assigned role: **vip lifetime member**" in res.status_message.lower()
    assert res.signature_verified is True


# TEST 3: Valid Enterprise SCIF License Verification & Auto-Role Assignment
def test_verify_license_enterprise(bot: CommunityOnboardingBotEngine):
    res = bot.verify_license_command("DSS-ENT-2026-F9E8D7C6")

    assert res.valid is True
    assert res.tier == "Enterprise SCIF"
    assert res.assigned_role == "Enterprise SCIF Architect"
    assert res.seats == 50
    assert "Enterprise SCIF Architect" in res.status_message


# TEST 4: Valid Contributor License Verification & Auto-Role Assignment
def test_verify_license_contributor(bot: CommunityOnboardingBotEngine):
    res = bot.verify_license_command("DSS-CONTRIB-2026-0042")

    assert res.valid is True
    assert res.tier == "Open-Source Contributor"
    assert res.assigned_role == "Verified Contributor"
    assert res.seats == 1


# TEST 5: Invalid or Forged License Key Rejection
def test_verify_license_invalid_or_corrupted(bot: CommunityOnboardingBotEngine):
    # Bad format
    bad_res = bot.verify_license_command("INVALID-KEY-TOKEN-1234")
    assert bad_res.valid is False
    assert bad_res.assigned_role == "Unverified Member"
    assert bad_res.error == "FORMAT_INVALID"

    # Forged signature check
    forged_res = bot.verify_license_command("DSS-PRO-2026-9999", signature_hex="deadbeef00001111")
    assert forged_res.valid is False
    assert forged_res.error == "SIGNATURE_FORGED"


# TEST 6: /benchmark-ast Command Output
def test_benchmark_ast_command(bot: CommunityOnboardingBotEngine):
    bench = bot.benchmark_ast_command()

    assert "-83.6%" in bench["summary"] or bench["metrics"]["token_reduction_percent"] == 83.6
    assert bench["metrics"]["execution_latency_ms"] < 5.0
    assert bench["metrics"]["parse_speed_loc_per_sec"] >= 600000
    assert WEB_APP_BASE in bench["interactive_sandbox_url"]


# TEST 7: /simulate-voice Command Output & NLMS Latency Budget
def test_simulate_voice_command(bot: CommunityOnboardingBotEngine):
    voice = bot.simulate_voice_command()

    assert voice["total_turnaround_ms"] <= 110.0
    assert "Acoustic Echo Cancellation" in voice["architecture"]
    assert len(voice["latency_budget"]) == 5
    assert voice["privacy"] == "100% Air-Gapped Local Execution (Zero Cloud Audio Uploads)"


# TEST 8: /docs Command Output & Quickstart Installers
def test_docs_command(bot: CommunityOnboardingBotEngine):
    docs = bot.docs_command()

    assert "curl -fsSL https://devsupersuite.web.app/install.sh" in docs["install_linux_macos"]
    assert "irm https://devsupersuite.web.app/install.ps1" in docs["install_windows"]
    assert WEB_APP_BASE in docs["interactive_browser_sandbox"]
    assert PROMO_CODE in docs["community_pass"]
    assert BRAND_EMAIL in docs["support_desk"]


# TEST 9: Anti-Spam & Rogue Crypto Phishing Protection
def test_antispam_crypto_phishing_filter(bot: CommunityOnboardingBotEngine):
    # Malicious phishing messages
    phishing_msgs = [
        "Hey everyone claim-airdrop of free solana at bit.ly/claim-crypto now!",
        "Connect your wallet at metamask-connect.io to validate tokens",
        "Free discord-nitro-free gift card here: tinyurl.com/freegift"
    ]
    for msg in phishing_msgs:
        res = bot.check_anti_spam(msg)
        assert res.flagged is True, f"Failed to flag malicious message: {msg}"
        assert res.action == "DELETE_AND_QUARANTINE"

    # Benign technical message
    clean_msg = "How does Tree-sitter incremental re-parsing handle multiple cursors in Neovim?"
    clean_res = bot.check_anti_spam(clean_msg)
    assert clean_res.flagged is False
    assert clean_res.action == "ALLOW"


# TEST 10: Strict 100% Brand Anonymity Protocol Enforcement
def test_brand_anonymity_enforcement(bot: CommunityOnboardingBotEngine):
    ok, violations = bot.audit_brand_anonymity()
    assert ok is True, f"Brand Anonymity violations: {violations}"
    assert len(violations) == 0

    # Test rejection of leaked personal names/phones
    leaked_corpus = "Written by boss personal cell phone +1-555-820-1928 at residential address"
    leak_ok, leak_violations = bot.audit_brand_anonymity(text=leaked_corpus)
    assert leak_ok is False
    assert len(leak_violations) >= 2


# TEST 11: Multi-Platform Payload Formatting (Discord & Telegram)
def test_discord_and_telegram_payload_formatting(bot: CommunityOnboardingBotEngine):
    # Discord Interaction
    d_res = bot.format_discord_interaction_response("verify-license", key="DSS-PRO-2026-ABCD")
    assert d_res["type"] == 4
    assert len(d_res["data"]["embeds"]) == 1
    assert "VIP Lifetime Member" in d_res["data"]["embeds"][0]["fields"][1]["value"]

    # Telegram Webhook
    t_res = bot.format_telegram_webhook_response("benchmark-ast")
    assert t_res["method"] == "sendMessage"
    assert t_res["parse_mode"] == "Markdown"
    assert "-83.6%" in t_res["text"]
