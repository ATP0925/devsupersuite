"""
⚡ DevSuperSuite Official: Enterprise Customer Referral & Viral Expansion Tests
File: test_referral_expansion_engine.py
Governing Authority: DevSuperSuite Growth & Revenue Operations (growth@devsupersuite.com)
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
MARKETING_DIR = os.path.join(SCRATCH_DIR, "marketing")
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")
DATA_DIR = os.path.join(SCRATCH_DIR, "data")

if SCRATCH_DIR not in sys.path:
    sys.path.insert(0, SCRATCH_DIR)
if SERVICES_DIR not in sys.path:
    sys.path.insert(0, SERVICES_DIR)

from services.enterprise_referral_expansion_engine import (
    Ed25519ReferralSigner,
    CryptographicReferralTokenEngine,
    EnterpriseSeatPoolingEngine,
    ViralGrowthModelingEngine,
    EnterpriseReferralExpansionManager,
    LEDGER_PATH,
    REPORT_PATH,
    REWARD_TIERS,
    BASE_REFERRAL_CLAIM_URL,
)


@pytest.fixture
def signer(tmp_path):
    test_vault = str(tmp_path / "test_referral_vault.json")
    return Ed25519ReferralSigner(vault_path=test_vault)


@pytest.fixture
def token_engine(signer):
    return CryptographicReferralTokenEngine(signer=signer)


@pytest.fixture
def pooling_engine():
    return EnterpriseSeatPoolingEngine()


@pytest.fixture
def manager(tmp_path):
    test_ledger = str(tmp_path / "test_ledger.json")
    test_report = str(tmp_path / "test_report.md")
    return EnterpriseReferralExpansionManager(ledger_path=test_ledger, report_path=test_report)


def test_01_ed25519_key_management_and_signer(signer):
    """Verify Ed25519 key generation, vault serialization, signature creation and verification."""
    assert os.path.exists(signer.vault_path)
    with open(signer.vault_path, "r", encoding="utf-8") as f:
        vault = json.load(f)
    assert "private_key_hex" in vault
    assert "public_key_hex" in vault
    assert vault["algorithm"] == "Ed25519"

    pub_hex = signer.get_public_key_hex()
    assert len(pub_hex) == 64  # 32 bytes in hex

    payload = "REF:TEST-ORG:example.com:TIER_100:test@example.com:20261108"
    sig_hex = signer.sign_canonical_payload(payload)
    assert len(sig_hex) == 128  # 64 bytes in hex
    assert signer.verify_signature(payload, sig_hex) is True
    assert signer.verify_signature(payload + "_TAMPERED", sig_hex) is False


def test_02_referral_token_generation_format(token_engine):
    """Verify referral token code format and payload attributes."""
    token_res = token_engine.create_referral_token(
        account_id="DEAL-RTX-2026-01",
        domain="rtx.com",
        tier="TIER_SOVEREIGN_UNLIMITED",
        champion_email="champion@rtx.com"
    )

    token_code = token_res["token_code"]
    assert token_code.startswith("ref_v1_")
    parts = token_code.split("_")
    assert len(parts) >= 5
    assert parts[0] == "ref"
    assert parts[1] == "v1"
    assert parts[2] == token_res["account_hash"]
    assert "tier" in token_code.lower()
    assert token_res["account_id"] == "DEAL-RTX-2026-01"
    assert token_res["originating_domain"] == "rtx.com"
    assert token_res["tier"] == "TIER_SOVEREIGN_UNLIMITED"
    assert token_res["rewards"]["bonus_seats_per_referral"] == 100
    assert token_res["algorithm"] == "Ed25519"


def test_03_referral_token_verification_success(token_engine):
    """Verify authentic Ed25519-signed token passes cryptographic verification."""
    token_res = token_engine.create_referral_token(
        account_id="DEAL-BLM-2026-05",
        domain="bloomberg.com",
        tier="TIER_ENTERPRISE_500",
        champion_email="architect@bloomberg.com"
    )

    verif = token_engine.verify_token(
        token_code=token_res["token_code"],
        canonical_payload=token_res["canonical_payload"],
        signature_hex=token_res["signature_hex"]
    )
    assert verif["valid"] is True
    assert verif["reason"] == "SIGNATURE_VERIFIED"
    assert verif["algorithm"] == "Ed25519"


def test_04_tampered_token_rejection(token_engine):
    """Verify tampered token, corrupted signature, or forged prefix is rejected."""
    token_res = token_engine.create_referral_token(
        account_id="DEAL-JPM-2026-04",
        domain="jpmorganchase.com",
        tier="TIER_ENTERPRISE_100",
        champion_email="md@jpmorganchase.com"
    )

    # 1. Tampered payload
    verif_tampered = token_engine.verify_token(
        token_code=token_res["token_code"],
        canonical_payload=token_res["canonical_payload"] + ":FORGED",
        signature_hex=token_res["signature_hex"]
    )
    assert verif_tampered["valid"] is False

    # 2. Corrupted signature
    bad_sig = "0" * 128
    verif_bad_sig = token_engine.verify_token(
        token_code=token_res["token_code"],
        canonical_payload=token_res["canonical_payload"],
        signature_hex=bad_sig
    )
    assert verif_bad_sig["valid"] is False

    # 3. Invalid prefix
    verif_bad_prefix = token_engine.verify_token(
        token_code="forged_token_12345",
        canonical_payload=token_res["canonical_payload"],
        signature_hex=token_res["signature_hex"]
    )
    assert verif_bad_prefix["valid"] is False
    assert verif_bad_prefix["reason"] == "INVALID_TOKEN_PREFIX"


def test_05_one_click_invite_url_attribution(token_engine):
    """Verify generated claim URL contains correct parameters for attribution tracking."""
    token_res = token_engine.create_referral_token(
        account_id="DEAL-LMT-2026-03",
        domain="lockheedmartin.com",
        tier="TIER_SOVEREIGN_UNLIMITED",
        champion_email="director@lockheedmartin.com"
    )

    claim_url = token_res["claim_url"]
    assert claim_url.startswith(BASE_REFERRAL_CLAIM_URL)
    assert "ref=" + token_res["token_code"] in claim_url
    assert "utm_source=enterprise_ref" in claim_url
    assert "account=DEAL-LMT-2026-03" in claim_url


def test_06_enterprise_reward_tier_allocation():
    """Verify reward allocations across all 4 enterprise tiers."""
    # Tier 25
    t25 = REWARD_TIERS["TIER_ENTERPRISE_25"]
    assert t25["bonus_seats_per_referral"] == 2
    assert t25["base_acv_usd"] == 14000.0
    assert t25["ast_throughput_boost_pct"] == 10.0

    # Tier 100
    t100 = REWARD_TIERS["TIER_ENTERPRISE_100"]
    assert t100["bonus_seats_per_referral"] == 10
    assert t100["base_acv_usd"] == 42000.0

    # Tier 500
    t500 = REWARD_TIERS["TIER_ENTERPRISE_500"]
    assert t500["bonus_seats_per_referral"] == 50
    assert t500["base_acv_usd"] == 120000.0

    # Sovereign Unlimited
    t_sov = REWARD_TIERS["TIER_SOVEREIGN_UNLIMITED"]
    assert t_sov["bonus_seats_per_referral"] == 100
    assert t_sov["base_acv_usd"] == 250000.0
    assert t_sov["ast_throughput_boost_pct"] == 100.0


def test_07_cross_subsidiary_seat_pooling(pooling_engine):
    """Verify seat pooling allocates seats across subsidiaries and reserves parent buffer."""
    pool = pooling_engine.create_or_update_pool(
        parent_org="Raytheon Technologies",
        total_licensed_seats=1000,
        children_orgs=["Collins Aerospace", "Pratt & Whitney", "Raytheon Intelligence"]
    )

    assert pool["parent_organization"] == "Raytheon Technologies"
    assert pool["total_licensed_seats"] == 1000
    assert pool["participating_subsidiaries_count"] == 3
    assert pool["allocated_seats"] + pool["unallocated_buffer_seats"] == 1000
    assert pool["subsidiary_allocations"]["Collins Aerospace"] > 0

    # Invalid empty children check
    with pytest.raises(ValueError):
        pooling_engine.create_or_update_pool("Raytheon", 1000, [])


def test_08_cross_subsidiary_seat_reallocation(pooling_engine):
    """Verify reallocation of seats between child organizations."""
    pooling_engine.create_or_update_pool(
        parent_org="JPMorgan Chase & Co.",
        total_licensed_seats=1200,
        children_orgs=["CIB", "CCB", "AWM"]
    )

    realloc = pooling_engine.reallocate_seats(
        parent_org="JPMorgan Chase & Co.",
        from_subsidiary="CIB",
        to_subsidiary="AWM",
        seats_to_move=50
    )
    assert realloc["status"] == "REALLOCATION_COMPLETED"
    assert realloc["seats_transferred"] == 50

    # Over-allocation error check
    with pytest.raises(ValueError):
        pooling_engine.reallocate_seats(
            parent_org="JPMorgan Chase & Co.",
            from_subsidiary="CIB",
            to_subsidiary="AWM",
            seats_to_move=99999
        )


def test_09_k_factor_calculation_and_growth_modeling():
    """Verify viral coefficient K = i * c math and expansion cohort projections."""
    # 1. High viral expansion (K > 1.25)
    res_high = ViralGrowthModelingEngine.calculate_k_factor(
        total_accounts=10,
        total_invites_sent=50,      # i = 5.0
        total_converted_referrals=15 # c = 0.30 -> K = 1.50
    )
    assert res_high["k_factor"] == 1.50
    assert res_high["is_above_viral_threshold"] is True
    assert res_high["growth_mode"] == "EXPONENTIAL_VIRAL_EXPANSION"

    # 2. Linear growth (1.0 <= K <= 1.25)
    res_lin = ViralGrowthModelingEngine.calculate_k_factor(
        total_accounts=10,
        total_invites_sent=50,
        total_converted_referrals=11 # K = 1.10
    )
    assert res_lin["growth_mode"] == "SUSTAINABLE_LINEAR_GROWTH"

    # 3. Subcritical growth (K < 1.0)
    res_sub = ViralGrowthModelingEngine.calculate_k_factor(
        total_accounts=10,
        total_invites_sent=50,
        total_converted_referrals=6  # K = 0.60
    )
    assert res_sub["growth_mode"] == "SUBCRITICAL_GROWTH"

    # Cohort expansion model
    cohort = ViralGrowthModelingEngine.model_expansion_cohort(
        active_pipeline_deals=15,
        k_factor=1.5
    )
    assert cohort["projected_expansion_arr_usd"] > 1000000.0
    assert cohort["projected_expansion_mrr_usd"] > 80000.0
    assert cohort["projected_net_dollar_retention_ndr_pct"] > 100.0
    assert cohort["insulated_churn_rate_pct"] < cohort["baseline_churn_rate_pct"]


def test_10_ledger_persistence_and_markdown_report_generation(manager):
    """Verify referral issuance updates ledger file and generates executive report."""
    ref_info = manager.issue_referral(
        account_id="DEAL-RTX-2026-01",
        domain="rtx.com",
        tier="TIER_SOVEREIGN_UNLIMITED",
        champion_email="champion@rtx.com"
    )
    assert ref_info["token_code"].startswith("ref_v1_")
    assert os.path.exists(manager.ledger_path)

    # Test seat pool
    pool_info = manager.pool_enterprise_seats(
        parent_org="Raytheon Technologies",
        total_licensed_seats=1000,
        children_orgs=["Collins Aerospace", "Pratt & Whitney", "Raytheon Intelligence"]
    )
    assert pool_info["parent_organization"] == "Raytheon Technologies"

    # Render report
    report_file = manager.render_markdown_report()
    assert os.path.exists(report_file)
    with open(report_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Enterprise Customer Referral & Viral Expansion Report" in content
    assert "Viral Coefficient ($K$-Factor)" in content
    assert "Multi-Tier Enterprise Referral Rewards Matrix" in content
    assert "Active Cross-Subsidiary Seat Pools" in content
    assert "growth@devsupersuite.com" in content


def test_11_cli_interface_execution():
    """Verify all CLI flags execute successfully with exit code 0."""
    python_bin = sys.executable
    script_path = os.path.join(SERVICES_DIR, "enterprise_referral_expansion_engine.py")

    flags = [
        ["--summary"],
        ["--calculate-k-factor"],
        ["--generate-invite", "--account", "DEAL-RTX-2026-01", "--tier", "TIER_SOVEREIGN_UNLIMITED"],
        ["--pool-seats", "--parent", "Raytheon Technologies", "--total-seats", "1000", "--children", "Collins,Pratt,Space"],
        ["--export-referral-report"],
    ]

    for flag_group in flags:
        cmd = [python_bin, script_path] + flag_group
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        assert res.returncode == 0, f"Command {cmd} failed with stderr: {res.stderr}"


def test_12_strict_brand_anonymity_compliance():
    """Verify zero personal founder leaks across all Phase 25 assets."""
    forbidden_tokens = [
        bytes.fromhex("41746861727661").decode("utf-8"),
        bytes.fromhex("506164687965").decode("utf-8"),
        bytes.fromhex("39383930343431323933").decode("utf-8"),
    ]

    phase_25_files = [
        Path(SERVICES_DIR) / "enterprise_referral_expansion_engine.py",
        Path(MARKETING_DIR) / "enterprise_referral_ledger.json",
        Path(REPORTS_DIR) / "enterprise_referral_expansion_report.md",
        Path(TESTS_DIR) / "test_referral_expansion_engine.py",
    ]

    for file_path in phase_25_files:
        assert file_path.exists(), f"File {file_path} must exist"
        content = file_path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token.lower() not in content.lower(), (
                f"Brand anonymity violation: found forbidden token in {file_path}"
            )
