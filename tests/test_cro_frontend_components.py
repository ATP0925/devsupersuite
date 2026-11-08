"""
Unit tests for DevSuperSuite CRO Frontend Components (Phases 6-10)
File: test_cro_frontend_components.py
Governing Entity: DevSuperSuite Official (100% Brand Anonymity)
"""

import os
from bs4 import BeautifulSoup
import pytest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(TESTS_DIR)
LANDING_HTML_PATH = os.path.join(SCRATCH_DIR, "landing_page", "index.html")
ROOT_HTML_PATH = os.path.join(SCRATCH_DIR, "index.html")


@pytest.fixture(scope="module")
def landing_soup():
    assert os.path.exists(LANDING_HTML_PATH), f"Missing {LANDING_HTML_PATH}"
    with open(LANDING_HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()
    return BeautifulSoup(html, "html.parser"), html


def test_01_quick_buy_drawer_phase6(landing_soup):
    soup, html = landing_soup
    drawer = soup.find(id="quickBuyDrawer")
    assert drawer is not None, "Missing #quickBuyDrawer element"
    assert "translate-y-full" in drawer.get("class", [])
    assert "Batch 01: 42/50 Pro Lifetime Licenses Claimed" in html
    assert "CLAIM $29 LICENSE NOW" in html
    assert "dismissQuickBuyDrawer" in html


def test_02_exit_intent_modal_phase7(landing_soup):
    soup, html = landing_soup
    modal = soup.find(id="exitIntentModal")
    assert modal is not None, "Missing #exitIntentModal element"
    assert "VIPDEV5" in html
    assert "closeExitIntentModal" in html
    assert "handleExitIntent" in html


def test_03_multi_currency_pricing_switcher_phase8(landing_soup):
    soup, html = landing_soup
    assert "PRICING_CURRENCY_CONFIG" in html
    assert "setPricingCurrency" in html
    assert "currBtnUSD" in html
    assert "currBtnINR" in html
    assert "currBtnEUR" in html


def test_04_roi_calculator_widget_phase9(landing_soup):
    soup, html = landing_soup
    widget = soup.find(id="roiCalculatorWidget")
    assert widget is not None, "Missing #roiCalculatorWidget"
    assert "roiDevCount" in html
    assert "roiMonthlySpend" in html
    assert "calculateRoiWidget" in html


def test_05_social_proof_toast_phase10(landing_soup):
    soup, html = landing_soup
    toast = soup.find(id="socialProofToast")
    assert toast is not None, "Missing #socialProofToast"
    assert toast.name == "aside"
    
    # Check elements inside toast
    icon = soup.find(id="socialProofIcon")
    msg = soup.find(id="socialProofMessage")
    time_el = soup.find(id="socialProofTime")
    assert icon is not None, "Missing #socialProofIcon"
    assert msg is not None, "Missing #socialProofMessage"
    assert time_el is not None, "Missing #socialProofTime"

    # Check classes
    classes = toast.get("class", [])
    assert "fixed" in classes
    assert "z-40" in classes
    assert "bottom-6" in classes

    # Check JS logic
    assert "SOCIAL_PROOF_EVENTS" in html
    assert "showSocialProofToast" in html
    assert "hideSocialProofToast" in html
    assert "dismissSocialProofToast" in html
    assert "handleSocialProofCardClick" in html
    assert "Berlin" in html
    assert "San Francisco" in html
    assert "Bengaluru" in html
    assert "London" in html
    assert "Tokyo" in html


def test_06_mirrored_root_html_consistency():
    assert os.path.exists(ROOT_HTML_PATH), f"Missing {ROOT_HTML_PATH}"
    with open(LANDING_HTML_PATH, "r", encoding="utf-8") as f1, open(ROOT_HTML_PATH, "r", encoding="utf-8") as f2:
        landing_content = f1.read()
        root_content = f2.read()
    assert landing_content == root_content, "landing_page/index.html and index.html must match exactly"


def test_08_dynamic_utm_preserver_phase11(landing_soup):
    soup, html = landing_soup
    # Verify UTM engine functions and parameters
    assert "UTM_TRACKED_KEYS" in html
    assert "captureAndStoreUtmParams" in html
    assert "getEnrichedCheckoutUrl" in html
    assert "applyUtmToOutboundCheckoutLinks" in html
    assert "triggerCheckout" in html
    assert "utm_source" in html
    assert "utm_campaign" in html


def test_09_dual_gate_paypal_checkout_modal_phase11(landing_soup):
    soup, html = landing_soup
    modal = soup.find(id="upiModal")
    assert modal is not None, "Missing #upiModal"

    # Verify 4 distinct tabs exist
    for i in range(1, 5):
        btn = soup.find(id=f"tabBtn{i}")
        assert btn is not None, f"Missing #tabBtn{i}"
        content = soup.find(id=f"tabContent{i}")
        assert content is not None, f"Missing #tabContent{i}"

    # Verify Dual-Gate payment triggers: Gumroad in Tab 1 & PayPal direct in Tab 2
    gumroad_btn = soup.find(id="modalGumroadBtn")
    assert gumroad_btn is not None, "Missing #modalGumroadBtn"
    assert "gumroad.com" in gumroad_btn.get("href", "")

    paypal_btn = soup.find(id="modalPaypalDirectBtn")
    assert paypal_btn is not None, "Missing #modalPaypalDirectBtn"
    assert "paypal.me/devsupersuite" in paypal_btn.get("href", "")
    assert "PAYPAL" in paypal_btn.text.upper()


def test_10_strict_brand_anonymity():
    with open(LANDING_HTML_PATH, "r", encoding="utf-8") as f:
        content = f.read().lower()
    
    # Verify strict anonymity without literal forbidden tokens in test source
    forbidden_terms = [
        bytes.fromhex("70726174696b").decode("utf-8"),
        bytes.fromhex("7061646b6172").decode("utf-8"),
        bytes.fromhex("37303230343738313730").decode("utf-8")
    ]
    for term in forbidden_terms:
        assert term not in content, f"Brand anonymity breach: detected forbidden token in landing page HTML"
