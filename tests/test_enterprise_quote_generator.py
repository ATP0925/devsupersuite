"""
⚡ DevSuperSuite Official: Enterprise Tiered Pricing Matrix & Quote Generator Integration Tests
File: test_enterprise_quote_generator.py
Governing Entity: DevSuperSuite Official (sales@devsupersuite.com)
Strict Protocol: 100% Brand Anonymity - Zero Founder Personal Identifiers
"""

import os
import sys
import json
import pytest
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Paths Setup
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(SCRATCH_DIR, "services")
DATA_DIR = os.path.join(SCRATCH_DIR, "data")
MARKETING_DIR = os.path.join(SCRATCH_DIR, "marketing")

sys.path.insert(0, SERVICES_DIR)

from custom_enterprise_quote_generator import (
    EnterpriseTierCatalog,
    Ed25519QuoteSealer,
    EnterpriseRoiCalculator,
    EnterpriseQuoteGeneratorEngine,
    ENTERPRISE_LEDGER_PATH,
    QUOTES_DIR
)


@pytest.fixture
def quote_engine(tmp_path):
    test_ledger = os.path.join(tmp_path, "test_enterprise_quotes.json")
    return EnterpriseQuoteGeneratorEngine(ledger_path=test_ledger)


def test_01_catalog_tier_specifications():
    """Verify master catalog seat tiers and base annual pricing."""
    tiers = EnterpriseTierCatalog.TIERS
    assert "tier_25" in tiers
    assert "tier_100" in tiers
    assert "tier_500" in tiers
    assert "tier_scif_unlimited" in tiers

    assert tiers["tier_25"]["base_annual_usd"] == 14000.00
    assert tiers["tier_25"]["seats"] == 25

    assert tiers["tier_100"]["base_annual_usd"] == 42000.00
    assert tiers["tier_100"]["seats"] == 100

    assert tiers["tier_500"]["base_annual_usd"] == 120000.00
    assert tiers["tier_500"]["seats"] == 500

    assert tiers["tier_scif_unlimited"]["base_annual_usd"] == 250000.00
    assert tiers["tier_scif_unlimited"].get("is_unlimited", False) is True


def test_02_base_pricing_calculation(quote_engine):
    """Verify standard single-year quote pricing without add-ons."""
    res = quote_engine.calculate_pricing("tier_100", sla_level="standard", has_dedicated_tam=False, term_years=1)
    assert res["base_annual_usd"] == 42000.00
    assert res["sla_addon_annual_usd"] == 0.00
    assert res["tam_addon_annual_usd"] == 0.00
    assert res["net_annual_billed_usd"] == 42000.00
    assert res["total_contract_value_usd"] == 42000.00
    assert res["monthly_effective_per_dev_usd"] == 35.00


def test_03_sla_multipliers(quote_engine):
    """Verify mission_critical 1.25x SLA multiplier is applied correctly."""
    res_std = quote_engine.calculate_pricing("tier_100", sla_level="standard")
    res_crit = quote_engine.calculate_pricing("tier_100", sla_level="mission_critical")

    # 42000 * 1.25 = 52500
    assert res_crit["sla_multiplier"] == 1.25
    assert res_crit["sla_addon_annual_usd"] == 10500.00
    assert res_crit["net_annual_billed_usd"] == 52500.00


def test_04_dedicated_tam_support_addon(quote_engine):
    """Verify dedicated TAM add-on (+$18,000/yr) applies accurately."""
    res = quote_engine.calculate_pricing("tier_100", sla_level="standard", has_dedicated_tam=True, term_years=1)
    # 42000 base + 18000 TAM = 60000
    assert res["tam_addon_annual_usd"] == 18000.00
    assert res["net_annual_billed_usd"] == 60000.00


def test_05_multi_year_commitment_discounts(quote_engine):
    """Verify 1-year (0%), 2-year (10%), and 3-year (18%) term discounts."""
    # 1 Year: 0%
    p1 = quote_engine.calculate_pricing("tier_100", term_years=1)
    assert p1["term_discount_percentage"] == 0.0
    assert p1["net_annual_billed_usd"] == 42000.00

    # 2 Year: 10% discount on $42k = $37,800/yr (TCV: $75,600)
    p2 = quote_engine.calculate_pricing("tier_100", term_years=2)
    assert p2["term_discount_percentage"] == 10.0
    assert p2["net_annual_billed_usd"] == 37800.00
    assert p2["total_contract_value_usd"] == 75600.00

    # 3 Year: 18% discount on $42k = $34,440/yr (TCV: $103,320)
    p3 = quote_engine.calculate_pricing("tier_100", term_years=3)
    assert p3["term_discount_percentage"] == 18.0
    assert p3["net_annual_billed_usd"] == 34440.00
    assert p3["total_contract_value_usd"] == 103320.00


def test_06_quantitative_roi_economics():
    """Verify token waste elimination economics and payback window."""
    # 100 seats, $42,000 annual cost
    # Baseline spend: 100 * 120 * 12 = $144,000
    # Gross token savings: $144,000 * 0.784 = $112,896
    # Net annual savings: $112,896 - $42,000 = $70,896
    econ = EnterpriseRoiCalculator.compute_economics(seats=100, annual_quote_cost=42000.00, term_years=1)
    assert econ["total_baseline_annual_api_spend"] == 144000.00
    assert econ["annual_gross_token_savings"] == 112896.00
    assert econ["annual_net_savings"] == 70896.00
    assert econ["payback_window_months"] == 4.5
    assert econ["term_net_roi_percentage"] == 168.8


def test_07_cryptographic_ed25519_sealing():
    """Verify Ed25519 digital signature creation and non-repudiable verification."""
    sealer = Ed25519QuoteSealer()
    sample_payload = '{"quote_id": "TEST-Q01", "total_contract_value_usd": 120000.00}'
    
    seal = sealer.seal_quote(sample_payload)
    assert "sha256_fingerprint" in seal
    assert "ed25519_signature_hex" in seal
    assert "ed25519_signer_public_key" in seal

    # Verify signature passes
    valid = sealer.verify_seal(sample_payload, seal["ed25519_signature_hex"])
    assert valid is True

    # Tampered payload fails verification
    tampered_payload = '{"quote_id": "TEST-Q01", "total_contract_value_usd": 1000.00}'
    tampered_valid = sealer.verify_seal(tampered_payload, seal["ed25519_signature_hex"])
    assert tampered_valid is False


def test_08_formal_quote_generation_and_persistence(quote_engine):
    """Verify end-to-end formal quote generation, markdown SOW export, and ledger update."""
    quote = quote_engine.generate_formal_quote(
        client_organization="General Dynamics Mission Systems",
        tier_id="tier_500",
        contact_name="Chief Information Security Officer",
        contact_email="procurement@gd-ms.com",
        sla_level="mission_critical",
        has_dedicated_tam=True,
        term_years=3
    )

    assert quote["quote_id"].startswith("DSS-ENT-Q2026-")
    assert quote["client_organization"] == "General Dynamics Mission Systems"
    assert quote["pricing"]["seats"] == 500
    assert "quote_file_path" in quote
    assert os.path.exists(quote["quote_file_path"])

    with open(quote["quote_file_path"], "r", encoding="utf-8") as f:
        md = f.read()

    assert "DevSuperSuite Official" in md
    assert "General Dynamics Mission Systems" in md
    assert "Ed25519" in md
    assert "OmniKernel 5.0" in md
    assert "sales@devsupersuite.com" in md


def test_09_all_tiers_roi_matrix(quote_engine):
    """Verify all standard tiers return structured economic comparisons."""
    matrix = quote_engine.calculate_all_tiers_roi()
    assert len(matrix) == 4
    for tid in ["tier_25", "tier_100", "tier_500", "tier_scif_unlimited"]:
        assert tid in matrix
        assert matrix[tid]["gross_token_savings_usd"] > matrix[tid]["annual_cost_usd"]
        assert matrix[tid]["payback_months"] <= 6.5


def test_10_cli_commands_execution():
    """Verify all 4 required CLI commands execute with exit code 0."""
    script_path = os.path.join(SERVICES_DIR, "custom_enterprise_quote_generator.py")

    cmds = [
        [sys.executable, script_path, "--generate-quote", "--tier", "tier_25", "--client", "Test Defense Corp"],
        [sys.executable, script_path, "--audit-quotes"],
        [sys.executable, script_path, "--calculate-tier-roi"],
        [sys.executable, script_path, "--summary"]
    ]

    for cmd in cmds:
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0, f"CLI command failed: {' '.join(cmd)}\n{res.stderr}"


def test_11_strict_brand_anonymity_enterprise_quote():
    """Verify strict 100% brand anonymity: zero personal founder names or numbers."""
    files_to_check = [
        os.path.join(SERVICES_DIR, "custom_enterprise_quote_generator.py"),
        os.path.join(MARKETING_DIR, "enterprise_pricing_tier_comparator.md"),
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
