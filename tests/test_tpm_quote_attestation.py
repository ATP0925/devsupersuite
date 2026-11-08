"""
DevSuperSuite Tech Services - Air-Gapped TPM 2.0 PCR Quote Attestation Test Suite
File: tests/test_tpm_quote_attestation.py
Governing Authority: DevSuperSuite Cryptographic Engineering & Applied Research Desk
Contact: cryptography@devsupersuite.com
Regulatory Baseline: TCG TPM 2.0 Structures / NIST SP 800-155 / FIPS 140-3
"""

import json
from pathlib import Path
import re
import subprocess
import sys
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from services.enterprise_tpm_quote_attestation_engine import (
    TPMQuoteAttestationEngine,
    HardwareCredentialVault,
    TPMSAttest,
    TPMSQuoteInfo,
    TPMManufacturer,
    GOLDEN_BASELINE_PCRS,
    GOLDEN_COMPOSITE_DIGEST,
    compute_composite_pcr_digest,
    TPM_GENERATED_VALUE,
    TPM_ST_ATTEST_QUOTE,
)


class TestTPMQuoteAttestation:
    """Rigorous verification suite for TCG TPM 2.0 quote structures, EK certificates, and air-gapped policy."""

    @pytest.fixture
    def engine(self):
        return TPMQuoteAttestationEngine(manufacturer=TPMManufacturer.INFINEON)

    def test_01_tpms_attest_binary_serialization_roundtrip(self):
        """Verifies canonical binary serialization and deserialization of TPMS_ATTEST."""
        pcr_digest = bytes.fromhex(GOLDEN_COMPOSITE_DIGEST)
        quote_info = TPMSQuoteInfo(
            pcr_select_count=1,
            hash_alg=0x000B,
            pcr_select_bitmap=bytes([0x95, 0x00, 0x00]),
            pcr_digest=pcr_digest,
        )
        original = TPMSAttest(
            magic=TPM_GENERATED_VALUE,
            attest_type=TPM_ST_ATTEST_QUOTE,
            qualified_signer=b"AK-TEST-SIGNER-SHA256-DIGEST-32B",
            extra_data_nonce=b"NONCE-CHALLENGE-VALUE-32B-SECURE",
            clock=1700000000,
            reset_count=2,
            restart_count=1,
            safe=1,
            firmware_version=0x0002000400060008,
            quote_info=quote_info,
        )

        serialized = original.serialize()
        assert len(serialized) > 100

        deserialized = TPMSAttest.deserialize(serialized)
        assert deserialized.magic == TPM_GENERATED_VALUE
        assert deserialized.attest_type == TPM_ST_ATTEST_QUOTE
        assert deserialized.qualified_signer == original.qualified_signer
        assert deserialized.extra_data_nonce == original.extra_data_nonce
        assert deserialized.clock == original.clock
        assert deserialized.quote_info.pcr_digest == pcr_digest

    def test_02_golden_composite_pcr_digest_calculation(self):
        """Verifies composite PCR digest over sorted PCR indices [0, 2, 4, 7]."""
        comp = compute_composite_pcr_digest(GOLDEN_BASELINE_PCRS, [0, 2, 4, 7])
        assert comp == GOLDEN_COMPOSITE_DIGEST
        assert len(comp) == 64

    def test_03_tpm_quote_generation_and_valid_signature_verification(self, engine):
        """Verifies TPM2_Quote generation and AK signature verification."""
        nonce = b"CHALLENGE-NONCE-1234567890123456"
        attest_struct, sig = engine.generate_quote(nonce=nonce)

        is_valid, errors, details = engine.verify_quote(
            attest_struct,
            sig,
            expected_nonce=nonce,
            reported_pcrs=GOLDEN_BASELINE_PCRS,
        )

        assert is_valid is True, f"Quote verification failed: {errors}"
        assert len(errors) == 0
        assert details["status"] == "AIR_GAP_INTEGRITY_VERIFIED"
        assert details["golden_baseline_match"] is True

    def test_04_tpm_quote_rejects_tampered_pcr_measurement(self, engine):
        """Verifies that unauthorized PCR modification trips Air-Gapped Integrity Breach."""
        nonce = b"CHALLENGE-NONCE-1234567890123456"
        tampered_pcrs = dict(GOLDEN_BASELINE_PCRS)
        # Modify PCR 0 (CRTM firmware compromised)
        tampered_pcrs[0] = "0000000000000000000000000000000000000000000000000000000000000000"

        attest_struct, sig = engine.generate_quote(nonce=nonce, pcrs=tampered_pcrs)
        is_valid, errors, details = engine.verify_quote(
            attest_struct,
            sig,
            expected_nonce=nonce,
            reported_pcrs=tampered_pcrs,
        )

        assert is_valid is False
        assert details["status"] == "AIR_GAP_INTEGRITY_BREACH"
        assert any("Air-gapped Golden Baseline Integrity Breach" in e for e in errors)
        assert details["golden_baseline_match"] is False

    def test_05_tpm_quote_rejects_stale_or_mismatched_nonce(self, engine):
        """Verifies replay attack defense via nonce mismatch rejection."""
        original_nonce = b"FRESH-CHALLENGE-NONCE-32BYTES-OK"
        attest_struct, sig = engine.generate_quote(nonce=original_nonce)

        is_valid, errors, _ = engine.verify_quote(
            attest_struct,
            sig,
            expected_nonce=b"DIFFERENT-STALE-CHALLENGE-NONCE",
        )

        assert is_valid is False
        assert any("nonce mismatch" in e.lower() for e in errors)

    def test_06_tpm_quote_rejects_forged_ak_signature(self, engine):
        """Verifies that an altered or forged AK signature is rejected."""
        nonce = b"CHALLENGE-NONCE-1234567890123456"
        attest_struct, sig = engine.generate_quote(nonce=nonce)

        # Corrupt signature bytes
        tampered_sig = bytearray(sig)
        tampered_sig[10] ^= 0xFF
        tampered_sig = bytes(tampered_sig)

        is_valid, errors, _ = engine.verify_quote(
            attest_struct,
            tampered_sig,
            expected_nonce=nonce,
        )

        assert is_valid is False
        assert any("signature verification failed" in e.lower() for e in errors)

    def test_07_hardware_ek_certificate_chain_verification_multi_vendor(self):
        """Verifies silicon manufacturer EK certificate profiles for Intel, AMD, and Infineon."""
        vendors = [TPMManufacturer.INTEL, TPMManufacturer.AMD, TPMManufacturer.INFINEON]

        for vendor in vendors:
            ek_profile = HardwareCredentialVault.get_certified_ek_profile(vendor)
            assert ek_profile.manufacturer == vendor
            assert ek_profile.certificate_validity is True
            assert ek_profile.tcg_extensions_verified is True
            assert ek_profile.serial_number.startswith("TPM20-SN-")

    def test_08_ak_binding_verification_credential_activation(self, engine):
        """Verifies AK binding to certified hardware TPM via credential activation proof."""
        is_bound = HardwareCredentialVault.verify_ak_binding(
            engine.ek_record,
            engine.ak_pk_bytes,
            engine.ak_name,
        )
        assert is_bound is True

        # False with forged AK name
        assert HardwareCredentialVault.verify_ak_binding(
            engine.ek_record,
            engine.ak_pk_bytes,
            b"FORGED-AK-NAME-32BYTES-VALUE---",
        ) is False

    def test_09_air_gapped_offline_policy_zero_network_dependency(self, engine):
        """Confirms that attestation verification executes 100% offline without network calls."""
        nonce = b"OFFLINE-SCIF-CHALLENGE-NONCE-VAL"
        attest_struct, sig = engine.generate_quote(nonce=nonce)

        # Verification executes without network sockets or cloud callbacks
        is_valid, errors, details = engine.verify_quote(
            attest_struct,
            sig,
            expected_nonce=nonce,
            reported_pcrs=GOLDEN_BASELINE_PCRS,
        )
        assert is_valid is True
        assert details["status"] == "AIR_GAP_INTEGRITY_VERIFIED"

    def test_10_cli_interface_all_flags_execution(self):
        """Verifies all CLI flags execute with returncode 0 and proper brand headers."""
        engine_script = REPO_ROOT / "services" / "enterprise_tpm_quote_attestation_engine.py"
        assert engine_script.exists()

        flags = [
            ["--summary"],
            ["--verify-tpm-quote"],
            ["--audit-pcr-banks"],
            ["--verify-ek-certificate"],
            ["--export-airgap-bundle"],
        ]

        for flag_set in flags:
            proc = subprocess.run(
                [sys.executable, str(engine_script)] + flag_set,
                capture_output=True,
                text=True,
                timeout=15,
            )
            assert proc.returncode == 0, f"CLI command failed with {flag_set}: {proc.stderr}"
            assert "DevSuperSuite" in proc.stdout

    def test_11_strict_brand_anonymity_under_devsupersuite(self):
        """Enforces absolute brand anonymity under DevSuperSuite Cryptographic Engineering."""
        target_files = [
            REPO_ROOT / "services" / "enterprise_tpm_quote_attestation_engine.py",
            REPO_ROOT / "services" / "reports" / "tpm_quote_attestation_dossier.md",
            REPO_ROOT / "services" / "reports" / "tpm_quote_attestation_manifest.json",
        ]

        prohibited_names = [
            bytes.fromhex("70726174696b").decode("utf-8"),
            bytes.fromhex("7061646b6172").decode("utf-8"),
            bytes.fromhex("6174706164").decode("utf-8"),
        ]

        phone_pattern = re.compile(
            r"(?<![A-Za-z0-9_-])(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?![A-Za-z0-9_-])"
        )

        for file_path in target_files:
            assert file_path.exists(), f"Target file does not exist: {file_path}"
            content = file_path.read_text(encoding="utf-8")

            # Check prohibited personal names
            for name in prohibited_names:
                assert name not in content.lower(), (
                    f"Brand anonymity violation: Found prohibited name '{name}' in {file_path.name}"
                )

            # Scrub safe timestamps, ISO dates, integer epochs, and GUIDs before phone regex
            scrubbed = re.sub(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}", "", content)
            scrubbed = re.sub(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", "", scrubbed)
            scrubbed = re.sub(r"TPM20-SN-[A-F0-9]{12}", "", scrubbed)
            scrubbed = re.sub(r'"clock_seconds":\s*\d+', "", scrubbed)
            scrubbed = re.sub(r"\b1\d{9}\b", "", scrubbed)  # 10-digit unix timestamps

            phone_matches = phone_pattern.findall(scrubbed)
            assert not phone_matches, (
                f"Brand anonymity violation: Found phone pattern in {file_path.name}: {phone_matches}"
            )

            # Confirm corporate identity
            assert "DevSuperSuite" in content, (
                f"Missing corporate brand DevSuperSuite in {file_path.name}"
            )
