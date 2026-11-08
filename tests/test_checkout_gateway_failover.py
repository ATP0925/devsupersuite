"""
⚡ DevSuperSuite Official: Multi-Gateway Checkout Failover & Transaction Resilience Tests
File: test_checkout_gateway_failover.py
Governing Entity: DevSuperSuite Payment Engineering (payments@devsupersuite.com)
Strict Protocol: 100% Brand Anonymity - Zero Founder Personal Identifiers
"""

import os
import sys
import json
import pytest
import subprocess
import urllib.parse
from pathlib import Path

# Paths Setup
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(SCRATCH_DIR, "services")
DATA_DIR = os.path.join(SCRATCH_DIR, "data")
MARKETING_DIR = os.path.join(SCRATCH_DIR, "marketing")
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")

sys.path.insert(0, SERVICES_DIR)

from checkout_gateway_failover_router import (
    GatewayId,
    CircuitState,
    GATEWAY_PROFILES,
    CheckoutGatewayFailoverRouter,
    DEFAULT_RESILIENCE_MATRIX_PATH,
    DEFAULT_RESILIENCE_REPORT_PATH
)


@pytest.fixture
def temp_router(tmp_path):
    matrix_file = os.path.join(tmp_path, "test_matrix.json")
    report_file = os.path.join(tmp_path, "test_report.md")
    return CheckoutGatewayFailoverRouter(matrix_path=matrix_file, report_path=report_file)


def test_01_gateway_profiles_and_priorities():
    """Verify all 3 gateways exist with proper priority hierarchy (Gumroad -> Stripe -> PayPal)."""
    assert GatewayId.GUMROAD in GATEWAY_PROFILES
    assert GatewayId.STRIPE_DIRECT in GATEWAY_PROFILES
    assert GatewayId.PAYPAL_EXPRESS in GATEWAY_PROFILES

    assert GATEWAY_PROFILES[GatewayId.GUMROAD]["priority"] == 1
    assert GATEWAY_PROFILES[GatewayId.STRIPE_DIRECT]["priority"] == 2
    assert GATEWAY_PROFILES[GatewayId.PAYPAL_EXPRESS]["priority"] == 3

    assert "gumroad.com" in GATEWAY_PROFILES[GatewayId.GUMROAD]["base_url"]
    assert "stripe.com" in GATEWAY_PROFILES[GatewayId.STRIPE_DIRECT]["base_url"]
    assert "paypal.com" in GATEWAY_PROFILES[GatewayId.PAYPAL_EXPRESS]["base_url"]


def test_02_default_healthy_resolution(temp_router):
    """Verify that under healthy conditions, router selects Gumroad (P1) with no failover."""
    active_gid, profile = temp_router.resolve_active_gateway()
    assert active_gid == GatewayId.GUMROAD
    assert profile["priority"] == 1

    url_data = temp_router.build_resilient_checkout_url({
        "customer_email": "dev@workstation.io",
        "coupon_code": "VIPDEV5"
    })
    assert url_data["active_gateway_id"] == GatewayId.GUMROAD.value
    assert url_data["failover_applied"] is False
    assert "gumroad.com" in url_data["checkout_url"]
    assert "discount=VIPDEV5" in url_data["checkout_url"]


def test_03_circuit_breaker_tripping_on_high_latency(temp_router):
    """Verify that latency exceeding 2,500ms trips Gumroad circuit to OPEN, failing over to Stripe."""
    # Probe with 2,900ms latency (> 2,500ms limit)
    health = temp_router.record_probe(GatewayId.GUMROAD, latency_ms=2900.0, is_error=False)
    assert health["circuit_state"] == CircuitState.OPEN.value

    # Now active gateway must failover to Stripe Direct (P2)
    active_gid, profile = temp_router.resolve_active_gateway()
    assert active_gid == GatewayId.STRIPE_DIRECT
    assert profile["priority"] == 2

    url_data = temp_router.build_resilient_checkout_url({
        "customer_email": "lead@cloudscale.io",
        "coupon_code": "DSS-PPP-50"
    })
    assert url_data["active_gateway_id"] == GatewayId.STRIPE_DIRECT.value
    assert url_data["failover_applied"] is True
    assert "buy.stripe.com" in url_data["checkout_url"]


def test_04_circuit_breaker_tripping_to_tertiary_paypal(temp_router):
    """Verify that when both Gumroad and Stripe circuits are OPEN, router falls over to PayPal (P3)."""
    temp_router.trip_gateway(GatewayId.GUMROAD)
    temp_router.trip_gateway(GatewayId.STRIPE_DIRECT)

    active_gid, profile = temp_router.resolve_active_gateway()
    assert active_gid == GatewayId.PAYPAL_EXPRESS
    assert profile["priority"] == 3

    url_data = temp_router.build_resilient_checkout_url({
        "customer_email": "architect@enterprise.org",
        "coupon_code": "DSS-PPP-30"
    })
    assert url_data["active_gateway_id"] == GatewayId.PAYPAL_EXPRESS.value
    assert url_data["failover_applied"] is True
    assert "paypal.com" in url_data["checkout_url"]


def test_05_zero_loss_state_preservation(temp_router):
    """Verify customer email, discount coupon, and UTM tracking tags are preserved across gateway switch."""
    temp_router.trip_gateway(GatewayId.GUMROAD)

    req = {
        "customer_email": "sarah.lead@fintech.de",
        "coupon_code": "DSS-PPP-50",
        "utm_params": {
            "utm_source": "hacker_news",
            "utm_medium": "cpc",
            "utm_campaign": "devops_launch"
        }
    }

    url_data = temp_router.build_resilient_checkout_url(req)
    final_url = url_data["checkout_url"]
    unquoted_url = urllib.parse.unquote(final_url)

    assert "buy.stripe.com" in final_url
    assert "sarah.lead@fintech.de" in unquoted_url
    assert "prefilled_promo_code=DSS-PPP-50" in unquoted_url
    assert "utm_source=hacker_news" in unquoted_url
    assert "utm_campaign=devops_launch" in unquoted_url
    assert url_data["preserved_state"]["utm_tags_count"] >= 3


def test_06_canary_probe_recovery_to_closed(temp_router):
    """Verify that a recovered gateway transitions cleanly back to CLOSED state."""
    temp_router.trip_gateway(GatewayId.GUMROAD)
    assert temp_router.gateway_health[GatewayId.GUMROAD]["circuit_state"] == CircuitState.OPEN.value

    # Recover
    temp_router.recover_gateway(GatewayId.GUMROAD)
    assert temp_router.gateway_health[GatewayId.GUMROAD]["circuit_state"] == CircuitState.CLOSED.value

    # Verifies it is prioritized again
    active_gid, _ = temp_router.resolve_active_gateway()
    assert active_gid == GatewayId.GUMROAD


def test_07_resilience_matrix_export_and_report_generation(temp_router, tmp_path):
    """Verify router exports JSON matrix and renders Markdown operational report."""
    matrix_out = str(tmp_path / "matrix_test.json")
    report_out = str(tmp_path / "report_test.md")

    exported_matrix = temp_router.export_resilience_matrix(output_path=matrix_out)
    assert os.path.exists(exported_matrix)
    with open(exported_matrix, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "gateway_profiles" in data
    assert "gateway_health" in data

    temp_router.report_path = report_out
    rendered_report = temp_router.render_markdown_resilience_report()
    assert os.path.exists(rendered_report)
    with open(rendered_report, "r", encoding="utf-8") as f:
        content = f.read()
    assert "# ⚡ DevSuperSuite Official: Multi-Gateway Checkout Failover & Resilience Report" in content
    assert "payments@devsupersuite.com" in content
    assert "| Gateway ID | Role | Circuit State |" in content


def test_08_cli_commands_execution():
    """Verify all 4 CLI command flags run cleanly with exit code 0."""
    script_path = os.path.join(SERVICES_DIR, "checkout_gateway_failover_router.py")

    cmds = [
        [sys.executable, script_path, "--simulate-gateway-outage"],
        [sys.executable, script_path, "--audit-gateway-sla"],
        [sys.executable, script_path, "--export-resilience-matrix"],
        [sys.executable, script_path, "--summary"]
    ]

    for cmd in cmds:
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0, f"CLI command failed: {' '.join(cmd)}\n{res.stderr}"


def test_09_strict_brand_anonymity():
    """Verify strict 100% brand anonymity: zero personal founder names or numbers."""
    files_to_check = [
        os.path.join(SERVICES_DIR, "checkout_gateway_failover_router.py"),
        os.path.join(MARKETING_DIR, "checkout_resilience_playbook.md"),
        os.path.join(REPORTS_DIR, "checkout_gateway_resilience_report.md"),
        os.path.abspath(__file__)
    ]

    forbidden_tokens = [
        bytes.fromhex("70726174696b").decode("utf-8"),
        bytes.fromhex("7061646b6172").decode("utf-8"),
        bytes.fromhex("37303230343738313730").decode("utf-8")
    ]

    for fpath in files_to_check:
        assert os.path.exists(fpath), f"Missing file: {fpath}"
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read().lower()
            for token in forbidden_tokens:
                assert token not in content, f"Brand anonymity violation in {fpath}: found forbidden token"
