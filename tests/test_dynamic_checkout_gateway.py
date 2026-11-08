"""
⚡ DevSuperSuite Official: Enterprise Multi-Variant Dynamic Checkout Gateway Tests
File: test_dynamic_checkout_gateway.py
Governing Authority: DevSuperSuite Revenue Operations (growth@devsupersuite.com)
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
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")

if SCRATCH_DIR not in sys.path:
    sys.path.insert(0, SCRATCH_DIR)
if SERVICES_DIR not in sys.path:
    sys.path.insert(0, SERVICES_DIR)

from services.enterprise_dynamic_checkout_gateway import (
    DynamicCurrencyResolver,
    DualRailCheckoutGenerator,
    EnterpriseDynamicCheckoutGateway,
    COUNTRY_CURRENCY_MAP,
    VALID_COUPONS,
    UPI_INSTITUTIONAL_VPA,
    CONFIG_PATH,
    REPORT_PATH,
)


@pytest.fixture
def test_gateway(tmp_path):
    cfg_file = str(tmp_path / "test_gateway_config.json")
    report_file = str(tmp_path / "test_gateway_report.md")
    return EnterpriseDynamicCheckoutGateway(
        config_path=cfg_file,
        report_path=report_file
    )


def test_01_currency_resolver_standard_currencies():
    """Verify currency resolution, symbols, and PPP adjustments across major regions."""
    # US
    us = DynamicCurrencyResolver.resolve_pricing_for_country("US")
    assert us["currency"] == "USD"
    assert us["final_checkout_price"] == 29.0
    assert us["primary_rail"] == "GUMROAD"

    # UK
    gb = DynamicCurrencyResolver.resolve_pricing_for_country("GB")
    assert gb["currency"] == "GBP"
    assert gb["final_checkout_price"] == 23.0

    # Germany / EU
    de = DynamicCurrencyResolver.resolve_pricing_for_country("DE")
    assert de["currency"] == "EUR"
    assert de["final_checkout_price"] == 27.0

    # India
    in_res = DynamicCurrencyResolver.resolve_pricing_for_country("IN")
    assert in_res["currency"] == "INR"
    assert in_res["final_checkout_price"] == 1499.0
    assert in_res["ppp_discount_pct"] == 40.0
    assert in_res["primary_rail"] == "UPI_DOMESTIC"


def test_02_currency_resolver_percentage_coupons():
    """Verify percentage coupons DSS-DEVREL-X (15%), DSS-COMMUNITY (20%), and RECOVER20 (20%)."""
    # 15% discount on $29 = $4.35 discount -> $24.65
    res15 = DynamicCurrencyResolver.resolve_pricing_for_country("US", coupon_code="DSS-DEVREL-X")
    assert res15["applied_coupon"] == "DSS-DEVREL-X"
    assert res15["discount_amount"] == 4.35
    assert res15["final_checkout_price"] == 24.65

    # 20% discount on $29 = $5.80 discount -> $23.20
    res20 = DynamicCurrencyResolver.resolve_pricing_for_country("US", coupon_code="DSS-COMMUNITY")
    assert res20["applied_coupon"] == "DSS-COMMUNITY"
    assert res20["discount_amount"] == 5.80
    assert res20["final_checkout_price"] == 23.20

    # RECOVER20
    res_rec = DynamicCurrencyResolver.resolve_pricing_for_country("US", coupon_code="RECOVER20")
    assert res_rec["applied_coupon"] == "RECOVER20"
    assert res_rec["final_checkout_price"] == 23.20


def test_03_currency_resolver_fixed_coupon():
    """Verify VIPDEV5 ($5 USD off) applies correctly across US and international FX."""
    us_fixed = DynamicCurrencyResolver.resolve_pricing_for_country("US", coupon_code="VIPDEV5")
    assert us_fixed["applied_coupon"] == "VIPDEV5"
    assert us_fixed["discount_amount"] == 5.0
    assert us_fixed["final_checkout_price"] == 24.0

    # Germany EUR ($5 * 0.93 = €4.65 off €27 = €22.35)
    de_fixed = DynamicCurrencyResolver.resolve_pricing_for_country("DE", coupon_code="VIPDEV5")
    assert de_fixed["applied_coupon"] == "VIPDEV5"
    assert de_fixed["discount_amount"] == 4.65
    assert de_fixed["final_checkout_price"] == 22.35


def test_04_dual_rail_upi_payload_generation():
    """Verify domestic India UPI intent payload contains valid VPA, amount, and tracking token."""
    upi = DualRailCheckoutGenerator.generate_upi_payload(
        customer_email="developer@company.in",
        amount_inr=1499.0
    )

    assert upi["rail"] == "UPI_DOMESTIC"
    assert upi["vpa"] == "devsupersuite@icici"
    assert upi["amount_inr"] == 1499.0
    assert "upi://pay?pa=devsupersuite@icici" in upi["upi_intent_uri"]
    assert "DevSuperSuite%20Official" in upi["upi_intent_uri"]
    assert "am=1499.00" in upi["upi_intent_uri"]
    assert upi["transaction_ref"].startswith("DSS-UPI-")


def test_05_dual_rail_gumroad_url_generation():
    """Verify Gumroad checkout URLs are dynamically enriched with discount codes and currency."""
    gum = DualRailCheckoutGenerator.generate_gumroad_url(
        customer_email="ciso@defense.com",
        coupon_code="DSS-DEVREL-X",
        currency="USD"
    )

    assert gum["rail"] == "GUMROAD_INTERNATIONAL"
    assert "https://devsupersuite.gumroad.com/l/pro" in gum["checkout_url"]
    assert "discount_code=DSS-DEVREL-X" in gum["checkout_url"]
    assert "email=ciso@defense.com" in gum["checkout_url"]
    assert gum["applied_coupon"] == "DSS-DEVREL-X"


def test_06_resolve_checkout_session_dual_rail(test_gateway):
    """Verify session resolution generates both UPI and Gumroad rails for India and Gumroad for US."""
    # India Session
    sess_in = test_gateway.resolve_checkout_session("IN", "dev@tcs.in")
    assert sess_in["session_id"].startswith("CHK-")
    assert sess_in["country_code"] == "IN"
    assert sess_in["primary_rail"] == "UPI_DOMESTIC"
    assert sess_in["upi_payload"] is not None
    assert sess_in["gumroad_payload"] is not None

    # US Session
    sess_us = test_gateway.resolve_checkout_session("US", "dev@rtx.com")
    assert sess_us["country_code"] == "US"
    assert sess_us["primary_rail"] == "GUMROAD"
    assert sess_us["upi_payload"] is None
    assert sess_us["gumroad_payload"] is not None


def test_07_cart_abandonment_simulation(test_gateway):
    """Verify abandoned carts trigger recovery payloads with RECOVER20 incentives."""
    rec = test_gateway.simulate_cart_abandonment(
        customer_email="abandoned@startup.co",
        country_code="US",
        minutes_ago=15
    )

    assert rec["abandonment_id"].startswith("ABN-")
    assert rec["customer_email"] == "abandoned@startup.co"
    assert rec["recovered_offer"]["recovery_coupon"] == "RECOVER20"
    assert "discount_code=RECOVER20" in rec["recovered_offer"]["recovery_url"]
    assert rec["status"] == "DISPATCHED_PENDING_CLICK"

    # Verify telemetry increment
    audit = test_gateway.audit_gateway_operations()
    assert audit["cart_abandonments_detected"] == 1
    assert audit["recovery_dispatches_sent"] == 1


def test_08_utr_verification_and_license_unlock(test_gateway):
    """Verify valid UTR payment reconciliation issues instant Ed25519 unlock token and handles duplicates."""
    res = test_gateway.verify_and_settle_utr(
        utr_number="123456789012",
        customer_email="dev.settled@india.in",
        amount_inr=1499.0
    )

    assert res["status"] == "VERIFIED_UNLOCKED"
    assert res["utr_number"] == "123456789012"
    assert res["license_unlock_token"].startswith("DSS-PRO-ED25519-")

    # Duplicate verification attempt
    res_dup = test_gateway.verify_and_settle_utr(
        utr_number="123456789012",
        customer_email="dev.settled@india.in"
    )
    assert res_dup["status"] == "ALREADY_VERIFIED"


def test_09_invalid_utr_validation(test_gateway):
    """Verify ValueError is raised when submitting invalid/short UTR numbers."""
    with pytest.raises(ValueError, match="Minimum 8 digits required"):
        test_gateway.verify_and_settle_utr(
            utr_number="1234",
            customer_email="test@fail.com"
        )


def test_10_gateway_operations_audit_and_report(test_gateway):
    """Verify comprehensive gateway audit aggregation and publication report rendering."""
    test_gateway.resolve_checkout_session("US", "usr1@co.com")
    test_gateway.resolve_checkout_session("IN", "usr2@co.in")
    test_gateway.simulate_cart_abandonment("drop@co.com")
    test_gateway.verify_and_settle_utr("998811223344", "usr2@co.in")

    audit = test_gateway.audit_gateway_operations()
    assert audit["total_checkout_sessions"] == 2
    assert audit["upi_domestic_sessions"] == 1
    assert audit["gumroad_international_sessions"] == 2
    assert audit["cart_abandonments_detected"] == 1
    assert audit["utr_verifications_settled"] == 1

    report_path = test_gateway.render_markdown_report()
    assert os.path.exists(report_path)
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "# ⚡ DevSuperSuite Official: Dynamic Checkout Gateway Operations Report" in content
    assert "devsupersuite@icici" in content
    assert "DSS-DEVREL-X" in content
    assert "growth@devsupersuite.com" in content


def test_11_cli_interface_execution():
    """Verify all CLI subcommands execute with exit code 0."""
    python_bin = sys.executable
    script_path = os.path.join(SERVICES_DIR, "enterprise_dynamic_checkout_gateway.py")

    commands = [
        ["--summary"],
        ["--resolve-checkout", "--country", "CA", "--email", "cli.dev@co.ca", "--coupon", "DSS-DEVREL-X"],
        ["--generate-upi-qr", "--email", "cli.upi@co.in"],
        ["--enrich-gumroad-link", "--coupon", "VIPDEV5"],
        ["--simulate-cart-abandonment", "--email", "cli.drop@co.com"],
        ["--verify-utr", "--utr", "99001122334455", "--email", "cli.upi@co.in"],
        ["--audit-gateway"],
        ["--export-gateway-report"]
    ]

    for args in commands:
        cmd = [python_bin, script_path] + args
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        assert res.returncode == 0, f"CLI command {cmd} failed with stderr: {res.stderr}"


def test_12_strict_brand_anonymity_compliance():
    """Verify zero personal founder leaks across all Phase 30 assets."""
    forbidden_tokens = [
        bytes.fromhex("41746861727661").decode("utf-8"),
        bytes.fromhex("506164687965").decode("utf-8"),
        bytes.fromhex("39383930343431323933").decode("utf-8"),
    ]

    phase_30_files = [
        Path(SERVICES_DIR) / "enterprise_dynamic_checkout_gateway.py",
        Path(DATA_DIR) / "checkout_gateway_config.json",
        Path(REPORTS_DIR) / "dynamic_checkout_gateway_report.md",
        Path(TESTS_DIR) / "test_dynamic_checkout_gateway.py",
    ]

    for file_path in phase_30_files:
        assert file_path.exists(), f"File {file_path} must exist"
        content = file_path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token.lower() not in content.lower(), (
                f"Brand anonymity violation: found forbidden token in {file_path}"
            )
