"""
⚡ DevSuperSuite Official: Enterprise Contract Lifecycle Automation (CLM) Tests
File: test_contract_lifecycle_engine.py
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

from services.enterprise_contract_lifecycle_engine import (
    ContractSigningAuthority,
    DynamicQuoteCalculator,
    EnterpriseContractLifecycleEngine,
    CLM_PRICING_TIERS,
    CONTRACTS_LEDGER_PATH,
    REPORT_PATH,
    KEY_VAULT_PATH,
)


@pytest.fixture
def test_authority(tmp_path):
    vault_file = str(tmp_path / "test_clm_vault.json")
    return ContractSigningAuthority(vault_path=vault_file)


@pytest.fixture
def test_engine(tmp_path, test_authority):
    ledger_file = str(tmp_path / "test_contracts_ledger.json")
    report_file = str(tmp_path / "test_clm_report.md")
    return EnterpriseContractLifecycleEngine(
        ledger_path=ledger_file,
        report_path=report_file,
        authority=test_authority
    )


def test_01_ed25519_contract_signing_authority(test_authority):
    """Verify Ed25519 key generation, vault persistence, digest signing, and verification."""
    assert os.path.exists(test_authority.vault_path)
    pub_hex = test_authority.get_public_key_hex()
    assert len(pub_hex) == 64

    test_digest = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    sig_hex = test_authority.sign_document_digest(test_digest)
    assert len(sig_hex) == 128

    # Signature verification
    is_valid = ContractSigningAuthority.verify_document_signature(
        test_digest,
        sig_hex,
        pub_hex
    )
    assert is_valid is True

    # Tampered digest verification must fail
    tampered_digest = "0000000000000000000000000000000000000000000000000000000000000000"
    is_tampered_valid = ContractSigningAuthority.verify_document_signature(
        tampered_digest,
        sig_hex,
        pub_hex
    )
    assert is_tampered_valid is False


def test_02_dynamic_quote_calculator_standard_tiers():
    """Verify standard quoting parameters across Solo, Team, Enterprise 1, and Sovereign SCIF."""
    # Solo
    solo_quote = DynamicQuoteCalculator.calculate_quote(
        tier_key="TIER_SOLO",
        company_name="Independent Dev",
        domain="dev.local"
    )
    assert solo_quote["tier_id"] == "TIER_SOLO"
    assert solo_quote["base_annual_price_usd"] == 29.0
    assert solo_quote["licensed_seats"] == 1
    assert solo_quote["sla_uptime_pct"] == 99.0
    assert solo_quote["support_response_p1_hrs"] == 24

    # Team
    team_quote = DynamicQuoteCalculator.calculate_quote(
        tier_key="TIER_TEAM",
        company_name="Team Startup",
        domain="startup.io"
    )
    assert team_quote["tier_id"] == "TIER_TEAM"
    assert team_quote["base_annual_price_usd"] == 299.0
    assert team_quote["licensed_seats"] == 10
    assert team_quote["sla_uptime_pct"] == 99.5
    assert team_quote["support_response_p1_hrs"] == 12

    # Enterprise Tier 1
    ent_quote = DynamicQuoteCalculator.calculate_quote(
        tier_key="TIER_ENTERPRISE_1",
        company_name="Fintech Corp",
        domain="fintech.com"
    )
    assert ent_quote["tier_id"] == "TIER_ENTERPRISE_1"
    assert ent_quote["base_annual_price_usd"] == 4999.0
    assert ent_quote["licensed_seats"] == 100
    assert ent_quote["sla_uptime_pct"] == 99.9
    assert ent_quote["support_response_p1_hrs"] == 4
    assert ent_quote["airgap_support"] is True

    # Sovereign SCIF
    scif_quote = DynamicQuoteCalculator.calculate_quote(
        tier_key="TIER_SOVEREIGN_SCIF",
        company_name="Defense Advanced Enclave",
        domain="defense.gov"
    )
    assert scif_quote["tier_id"] == "TIER_SOVEREIGN_SCIF"
    assert scif_quote["base_annual_price_usd"] == 24999.0
    assert scif_quote["licensed_seats"] == 999999
    assert scif_quote["sla_uptime_pct"] == 99.95
    assert scif_quote["support_response_p1_hrs"] == 1
    assert scif_quote["ip_indemnity_cap_usd"] == 10000000.0
    assert scif_quote["dedicated_tam"] is True


def test_03_custom_seat_and_multi_year_discounts():
    """Verify custom seats volume discounting and multi-year commitment discounts."""
    # 2-Year Multi-Year: 10% Discount
    quote_2yr = DynamicQuoteCalculator.calculate_quote(
        tier_key="TIER_ENTERPRISE_1",
        company_name="Cloudscale",
        domain="cloudscale.net",
        multi_year_commitment=2
    )
    assert quote_2yr["multi_year_discount_pct"] == 10.0
    assert quote_2yr["net_annual_price_usd"] == 4499.10
    assert quote_2yr["total_contract_value_usd"] == 8998.20

    # 3-Year Multi-Year: 20% Discount
    quote_3yr = DynamicQuoteCalculator.calculate_quote(
        tier_key="TIER_SOVEREIGN_SCIF",
        company_name="Lockheed Martin Enterprise",
        domain="lockheedmartin.com",
        multi_year_commitment=3
    )
    assert quote_3yr["multi_year_discount_pct"] == 20.0
    assert quote_3yr["net_annual_price_usd"] == 19999.20
    assert quote_3yr["total_contract_value_usd"] == 59997.60

    # Custom Seats volume calculation (150 seats on 100-seat base)
    quote_custom_seats = DynamicQuoteCalculator.calculate_quote(
        tier_key="TIER_ENTERPRISE_1",
        company_name="BigTeam Inc",
        domain="bigteam.com",
        custom_seats=150,
        multi_year_commitment=1
    )
    assert quote_custom_seats["licensed_seats"] == 150
    # Extra 50 seats with 15% discount: 50 * (4999/100) * 0.85 = 50 * 49.99 * 0.85 = 2124.58
    assert quote_custom_seats["base_annual_price_usd"] > 4999.0


def test_04_msa_contract_generation_structure(test_engine):
    """Verify MSA contract generation contains all required institutional clauses and SLA terms."""
    quote = test_engine.generate_and_record_quote(
        tier_key="TIER_SOVEREIGN_SCIF",
        company_name="Raytheon Space Systems",
        domain="rtx.com",
        multi_year_commitment=3
    )

    contract = test_engine.generate_enterprise_msa(quote["quote_id"])

    assert contract["contract_id"].startswith("MSA-")
    assert contract["company_name"] == "Raytheon Space Systems"
    assert contract["domain"] == "rtx.com"
    assert contract["status"] == "PENDING_SIGNATURE"
    assert len(contract["digest_sha256"]) == 64
    assert len(contract["provider_signature_hex"]) == 128
    assert contract["total_contract_value_usd"] == 59997.60

    body = contract["contract_body"]
    assert "MASTER SOFTWARE LICENSE AND SERVICES AGREEMENT (MSA)" in body
    assert "Grant of Software License & Air-Gap Enclaves" in body
    assert "99.95% availability" in body
    assert "Initial response within **1 hour(s)**" in body
    assert "$10,000,000.00 USD" in body
    assert "Zero-Telemetry & Sovereign Confidentiality" in body
    assert "growth@devsupersuite.com" in body


def test_05_bilateral_countersignature_workflow(test_engine):
    """Verify counterparty signing updates status to EXECUTED_ACTIVE with tamper-evident nonce."""
    quote = test_engine.generate_and_record_quote(
        tier_key="TIER_ENTERPRISE_1",
        company_name="Datadog Global",
        domain="datadoghq.com"
    )
    contract = test_engine.generate_enterprise_msa(quote["quote_id"])
    cid = contract["contract_id"]

    res = test_engine.execute_counterparty_signature(
        contract_id=cid,
        signatory_email="ciso@datadoghq.com",
        signatory_title="Chief Information Security Officer"
    )

    assert res["status"] == "EXECUTED_ACTIVE"
    assert res["contract_id"] == cid
    assert res["signatory_email"] == "ciso@datadoghq.com"
    assert res["provider_signature_verified"] is True

    # Check ledger state
    updated_contract = next(c for c in test_engine.ledger["contracts"] if c["contract_id"] == cid)
    assert updated_contract["status"] == "EXECUTED_ACTIVE"
    assert len(updated_contract["counterparty_signatures"]) == 1
    sig = updated_contract["counterparty_signatures"][0]
    assert sig["signatory_email"] == "ciso@datadoghq.com"
    assert sig["signatory_title"] == "Chief Information Security Officer"
    assert len(sig["nonce"]) == 16
    assert len(sig["counterparty_signature_token"]) == 64


def test_06_tampered_contract_signature_rejection(test_engine):
    """Verify audit flags tampered signatures and modified contract digests."""
    quote = test_engine.generate_and_record_quote(
        tier_key="TIER_TEAM",
        company_name="Agile Devs",
        domain="agiledevs.org"
    )
    contract = test_engine.generate_enterprise_msa(quote["quote_id"])
    cid = contract["contract_id"]

    # Tamper with the provider signature in the ledger
    for c in test_engine.ledger["contracts"]:
        if c["contract_id"] == cid:
            c["provider_signature_hex"] = "a" * 128

    audit = test_engine.audit_contracts()
    assert audit["total_contracts"] == 1
    assert audit["verified_provider_signatures"] == 0
    assert audit["cryptographic_audit_verdict"] == "AUDIT_WARNING"


def test_07_missing_quote_or_contract_handling(test_engine):
    """Verify KeyError is raised when referencing non-existent quote or contract ID."""
    with pytest.raises(KeyError, match="Quote 'QTE-NONEXISTENT' not found"):
        test_engine.generate_enterprise_msa("QTE-NONEXISTENT")

    with pytest.raises(KeyError, match="Contract 'MSA-NONEXISTENT' not found"):
        test_engine.execute_counterparty_signature("MSA-NONEXISTENT", "legal@unknown.com")


def test_08_audit_and_markdown_report_generation(test_engine):
    """Verify executive CLM audit aggregation and markdown report generation."""
    # Create two executed contracts
    q1 = test_engine.generate_and_record_quote("TIER_SOVEREIGN_SCIF", "Boeing Defense", "boeing.com")
    c1 = test_engine.generate_enterprise_msa(q1["quote_id"])
    test_engine.execute_counterparty_signature(c1["contract_id"], "procurement@boeing.com")

    q2 = test_engine.generate_and_record_quote("TIER_ENTERPRISE_1", "Stripe Platform", "stripe.com")
    c2 = test_engine.generate_enterprise_msa(q2["quote_id"])
    test_engine.execute_counterparty_signature(c2["contract_id"], "legal@stripe.com")

    # One pending contract
    q3 = test_engine.generate_and_record_quote("TIER_TEAM", "Gitlab Partner", "partner.io")
    test_engine.generate_enterprise_msa(q3["quote_id"])

    audit = test_engine.audit_contracts()
    assert audit["total_contracts"] == 3
    assert audit["status_distribution"]["EXECUTED_ACTIVE"] == 2
    assert audit["status_distribution"]["PENDING_SIGNATURE"] == 1
    assert audit["total_active_arr_usd"] == 24999.0 + 4999.0
    assert audit["cryptographic_audit_verdict"] == "ALL_SIGNATURES_VALID"

    report_path = test_engine.render_markdown_report()
    assert os.path.exists(report_path)
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "# ⚡ DevSuperSuite Official: Enterprise Contract Lifecycle Automation (CLM) Report" in content
    assert "Boeing Defense" in content
    assert "Stripe Platform" in content
    assert "Gitlab Partner" in content
    assert "EXECUTED_ACTIVE" in content
    assert "ALL_SIGNATURES_VALID" in content
    assert "growth@devsupersuite.com" in content


def test_09_cli_interface_execution():
    """Verify CLI subcommands execute with exit code 0."""
    python_bin = sys.executable
    script_path = os.path.join(SERVICES_DIR, "enterprise_contract_lifecycle_engine.py")

    commands = [
        ["--summary"],
        ["--generate-quote", "--tier", "TIER_ENTERPRISE_1", "--company", "Palantir Tech", "--domain", "palantir.com"],
        ["--generate-msa"],
        ["--sign-contract", "--signatory", "legal@palantir.com"],
        ["--audit-contracts"],
        ["--export-clm-report"]
    ]

    for args in commands:
        cmd = [python_bin, script_path] + args
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        assert res.returncode == 0, f"CLI command {cmd} failed with stderr: {res.stderr}"


def test_10_strict_brand_anonymity_compliance():
    """Verify zero personal founder leaks across all Phase 27 assets."""
    forbidden_tokens = [
        bytes.fromhex("41746861727661").decode("utf-8"),
        bytes.fromhex("506164687965").decode("utf-8"),
        bytes.fromhex("39383930343431323933").decode("utf-8"),
    ]

    phase_27_files = [
        Path(SERVICES_DIR) / "enterprise_contract_lifecycle_engine.py",
        Path(DATA_DIR) / "enterprise_contracts_ledger.json",
        Path(REPORTS_DIR) / "enterprise_contract_lifecycle_report.md",
        Path(TESTS_DIR) / "test_contract_lifecycle_engine.py",
    ]

    for file_path in phase_27_files:
        assert file_path.exists(), f"File {file_path} must exist"
        content = file_path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token.lower() not in content.lower(), (
                f"Brand anonymity violation: found forbidden token in {file_path}"
            )


def test_11_custom_vault_and_persistence(tmp_path):
    """Verify initialization and key reloading from existing vault file."""
    vault_file = str(tmp_path / "custom_vault.json")
    auth1 = ContractSigningAuthority(vault_path=vault_file)
    pub_key_1 = auth1.get_public_key_hex()

    # Re-instantiate with same vault file; public key should match
    auth2 = ContractSigningAuthority(vault_path=vault_file)
    pub_key_2 = auth2.get_public_key_hex()
    assert pub_key_1 == pub_key_2

    # Sign with auth1 and verify with auth2's public key
    digest = "c2e42f44764f72e6129983b614022d7fb663c0ce5ce285b93668106050f6002d"
    sig = auth1.sign_document_digest(digest)
    assert ContractSigningAuthority.verify_document_signature(digest, sig, pub_key_2) is True
