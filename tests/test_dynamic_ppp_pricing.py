"""
⚡ DevSuperSuite Official: Purchasing Power Parity (PPP) Pricing Engine Tests
File: test_dynamic_ppp_pricing.py
Governing Entity: DevSuperSuite Growth Engineering (growth@devsupersuite.com)
Strict Protocol: 100% Brand Anonymity - Zero Founder Personal Identifiers
"""

import os
import sys
import json
import pytest
import subprocess
from pathlib import Path

# Paths Setup
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(SCRATCH_DIR, "services")
DATA_DIR = os.path.join(SCRATCH_DIR, "data")
MARKETING_DIR = os.path.join(SCRATCH_DIR, "marketing")

sys.path.insert(0, SERVICES_DIR)

from dynamic_ppp_pricing_engine import (
    TIER_CONFIG,
    PPP_COUNTRIES_DATABASE,
    CountryHeaderResolver,
    DynamicPPPPricingEngine,
    DEFAULT_PPP_MATRIX_PATH,
    DEFAULT_PLAYBOOK_PATH,
    BASE_PRICE_USD
)


@pytest.fixture
def temp_ppp_engine(tmp_path):
    matrix_file = os.path.join(tmp_path, "test_ppp_matrix.json")
    return DynamicPPPPricingEngine(matrix_path=matrix_file)


def test_01_tier_configuration_and_discounts():
    """Verify tier matrix defines 4 distinct purchasing power tiers with accurate pricing & coupons."""
    assert "TIER_A" in TIER_CONFIG
    assert "TIER_B" in TIER_CONFIG
    assert "TIER_C" in TIER_CONFIG
    assert "TIER_D" in TIER_CONFIG

    # Tier A (Developed)
    assert TIER_CONFIG["TIER_A"]["discount_pct"] == 0
    assert TIER_CONFIG["TIER_A"]["price_usd"] == 29.00
    assert TIER_CONFIG["TIER_A"]["coupon_code"] is None

    # Tier B (High-Growth)
    assert TIER_CONFIG["TIER_B"]["discount_pct"] == 30
    assert TIER_CONFIG["TIER_B"]["price_usd"] == 20.00
    assert TIER_CONFIG["TIER_B"]["coupon_code"] == "DSS-PPP-30"

    # Tier C (Emerging Hubs)
    assert TIER_CONFIG["TIER_C"]["discount_pct"] == 50
    assert TIER_CONFIG["TIER_C"]["price_usd"] == 14.00
    assert TIER_CONFIG["TIER_C"]["coupon_code"] == "DSS-PPP-50"

    # Tier D (Developing Economies)
    assert TIER_CONFIG["TIER_D"]["discount_pct"] == 70
    assert TIER_CONFIG["TIER_D"]["price_usd"] == 9.00
    assert TIER_CONFIG["TIER_D"]["coupon_code"] == "DSS-PPP-70"


def test_02_database_completeness_and_audit(temp_ppp_engine):
    """Verify 80+ sovereign countries are mapped without missing currencies or invalid pricing."""
    audit = temp_ppp_engine.audit_ppp_matrix()

    assert audit["total_countries_mapped"] >= 80, f"Expected at least 80 countries, got {audit['total_countries_mapped']}"
    assert audit["is_valid"] is True
    assert len(audit["invalid_records"]) == 0

    dist = audit["tier_distribution"]
    assert dist["TIER_A"] >= 20
    assert dist["TIER_B"] >= 18
    assert dist["TIER_C"] >= 18
    assert dist["TIER_D"] >= 18


def test_03_country_header_resolver():
    """Verify CountryHeaderResolver normalizes Cloudflare, CloudFront, and custom proxy headers."""
    # Cloudflare header
    assert CountryHeaderResolver.resolve_from_headers({"CF-IPCountry": "in"}) == "IN"
    assert CountryHeaderResolver.resolve_from_headers({"cf-ipcountry": "DE"}) == "DE"

    # CloudFront header
    assert CountryHeaderResolver.resolve_from_headers({"X-Country-Code": "br"}) == "BR"
    assert CountryHeaderResolver.resolve_from_headers({"Cloudfront-Viewer-Country": "NG"}) == "NG"

    # Fallback to US
    assert CountryHeaderResolver.resolve_from_headers({}) == "US"
    assert CountryHeaderResolver.resolve_from_headers({"User-Agent": "Mozilla/5.0"}) == "US"


def test_04_resolve_country_tier_c_india(temp_ppp_engine):
    """Verify resolving India (IN) produces Tier C, 50% discount, ₹749 INR, and DSS-PPP-50 coupon."""
    res = temp_ppp_engine.resolve_country("IN")

    assert res["country_code"] == "IN"
    assert res["country_name"] == "India"
    assert res["tier"] == "TIER_C"
    assert res["discount_percentage"] == 50
    assert res["discounted_price_usd"] == 14.00
    assert res["coupon_code"] == "DSS-PPP-50"
    assert res["currency_code"] == "INR"
    assert res["currency_symbol"] == "₹"
    assert "₹749 INR" in res["localized_price_display"]
    assert "discount=DSS-PPP-50" in res["checkout_url"]
    assert res["ppp_parity_applied"] is True

    # HTML Banner check
    assert "pppDiscountBanner" in res["banner_html"]
    assert "DSS-PPP-50" in res["banner_html"]
    assert "50% OFF" in res["banner_html"]


def test_05_resolve_country_tier_d_nigeria(temp_ppp_engine):
    """Verify resolving Nigeria (NG) produces Tier D, 70% discount, $9 USD, and DSS-PPP-70 coupon."""
    res = temp_ppp_engine.resolve_country("NG")

    assert res["country_code"] == "NG"
    assert res["country_name"] == "Nigeria"
    assert res["tier"] == "TIER_D"
    assert res["discount_percentage"] == 70
    assert res["discounted_price_usd"] == 9.00
    assert res["coupon_code"] == "DSS-PPP-70"
    assert "discount=DSS-PPP-70" in res["checkout_url"]
    assert res["ppp_parity_applied"] is True
    assert "70% Parity Deal" in res["banner_html"]


def test_06_resolve_country_tier_a_developed(temp_ppp_engine):
    """Verify resolving United States (US) produces Tier A, 0% discount, base $29 USD, and empty banner."""
    res = temp_ppp_engine.resolve_country("US")

    assert res["country_code"] == "US"
    assert res["tier"] == "TIER_A"
    assert res["discount_percentage"] == 0
    assert res["discounted_price_usd"] == 29.00
    assert res["coupon_code"] is None
    assert "discount=" not in res["checkout_url"]
    assert res["ppp_parity_applied"] is False
    assert res["banner_html"] == ""


def test_07_export_matrix_json_file(temp_ppp_engine, tmp_path):
    """Verify exporting matrix writes valid JSON with tier definitions and 80+ countries."""
    export_file = str(tmp_path / "matrix_export.json")
    exported = temp_ppp_engine.export_matrix_json(output_path=export_file)

    assert os.path.exists(exported)
    with open(exported, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "tier_definitions" in data
    assert "countries" in data
    assert len(data["countries"]) >= 80
    assert data["base_price_usd"] == BASE_PRICE_USD
    assert "growth@devsupersuite.com" in data["governing_authority"]


def test_08_cli_commands_execution():
    """Verify all 4 CLI command flags run cleanly with exit code 0."""
    script_path = os.path.join(SERVICES_DIR, "dynamic_ppp_pricing_engine.py")

    cmds = [
        [sys.executable, script_path, "--resolve-country", "IN"],
        [sys.executable, script_path, "--audit-ppp-matrix"],
        [sys.executable, script_path, "--export-localized-pricing-json"],
        [sys.executable, script_path, "--summary"]
    ]

    for cmd in cmds:
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0, f"CLI command failed: {' '.join(cmd)}\n{res.stderr}"


def test_09_strict_brand_anonymity():
    """Verify strict 100% brand anonymity: zero personal founder names or numbers."""
    files_to_check = [
        os.path.join(SERVICES_DIR, "dynamic_ppp_pricing_engine.py"),
        os.path.join(MARKETING_DIR, "cro_ppp_pricing_experiment_playbook.md"),
        os.path.join(MARKETING_DIR, "ppp_localized_discount_matrix.json"),
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
