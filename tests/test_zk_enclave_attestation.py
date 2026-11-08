"""
DevSuperSuite Tech Services - Zero-Knowledge Attestation & Enclave Remote Attestation Test Suite
File: tests/test_zk_enclave_attestation.py
Governing Authority: DevSuperSuite Cryptographic Engineering & Applied Research Desk
Contact: cryptography@devsupersuite.com
Regulatory Baseline: NIST SP 800-193 / AWS Nitro COSE Sign1 / AMD SEV-SNP / RFC 3526 NIZKP / NIST FIPS 204
"""

import json
from pathlib import Path
import re
import subprocess
import sys
import time
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from services.enterprise_zk_enclave_attestation_engine import (
    EnclaveAttestationVerifier,
    ZKCodeComplianceProver,
    AttestationTokenSealer,
    GOLDEN_BASELINE_PCRS,
    GOLDEN_BASELINE_AMD_MEASUREMENT,
    ZKComplianceProof,
    EnclavePlatform,
)


class TestZKEnclaveAttestation:
    """Comprehensive test suite for confidential enclaves, zero-knowledge proofs, and dual-signature sealing."""

    @pytest.fixture
    def verifier(self):
        return EnclaveAttestationVerifier()

    @pytest.fixture
    def prover(self):
        return ZKCodeComplianceProver()

    @pytest.fixture
    def sealer(self):
        return AttestationTokenSealer()

    def test_01_nitro_enclave_cose_sign1_golden_pcr_verification(self, verifier):
        """Verifies AWS Nitro Enclave attestation document matches golden PCRs."""
        doc = verifier.generate_synthetic_nitro_attestation(nonce="nonce-test-1234")
        is_valid, errors, details = verifier.verify_nitro_attestation(doc, expected_nonce="nonce-test-1234")

        assert is_valid is True, f"Verification failed with errors: {errors}"
        assert len(errors) == 0
        assert details["platform"] == EnclavePlatform.AWS_NITRO_ENCLAVE.value
        assert details["pcr0_verified"] is True
        assert details["pcr1_verified"] is True
        assert details["pcr2_verified"] is True
        assert details["pcr8_verified"] is True

    def test_02_nitro_enclave_rejects_tampered_pcr0(self, verifier):
        """Ensures that any discrepancy in PCR0 (kernel/ramdisk) causes verification failure."""
        tampered_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        doc = verifier.generate_synthetic_nitro_attestation(tampered_pcr=tampered_hash)
        is_valid, errors, details = verifier.verify_nitro_attestation(doc)

        assert is_valid is False
        assert any("PCR PCR0 measurement discrepancy" in e for e in errors)
        assert details["pcr0_verified"] is False

    def test_03_nitro_enclave_nonce_freshness_and_replay_defense(self, verifier):
        """Verifies that mismatched nonce triggers immediate attestation rejection."""
        doc = verifier.generate_synthetic_nitro_attestation(nonce="original-fresh-nonce")
        is_valid, errors, _ = verifier.verify_nitro_attestation(doc, expected_nonce="different-challenge-nonce")

        assert is_valid is False
        assert any("Nonce mismatch" in e for e in errors)

    def test_04_nitro_enclave_timestamp_expiration_window(self, verifier):
        """Guarantees that expired attestation documents (>300s old) are rejected."""
        doc = verifier.generate_synthetic_nitro_attestation()
        # Artificially age the timestamp by 400 seconds
        doc["payload"]["timestamp"] -= 400 * 1000

        is_valid, errors, _ = verifier.verify_nitro_attestation(doc, max_age_seconds=300)
        assert is_valid is False
        assert any("expired" in e for e in errors)

    def test_05_amd_sev_snp_launch_measurement_verification(self, verifier):
        """Verifies AMD SEV-SNP hardware attestation report against Golden Measurement."""
        snp_report = verifier.generate_synthetic_amd_sev_snp_report()
        is_valid, errors, details = verifier.verify_amd_sev_snp_report(snp_report)

        assert is_valid is True, f"SEV-SNP verification failed: {errors}"
        assert details["platform"] == EnclavePlatform.AMD_SEV_SNP.value
        assert details["measurement_verified"] is True
        assert details["vmpl"] == 0

    def test_06_amd_sev_snp_rejects_altered_measurement(self, verifier):
        """Ensures modified launch measurement is rejected."""
        tampered_measurement = "111122223333444455556666777788889999aaaabbbbccccddddeeeeffff000011112222333344445555666677778888"
        snp_report = verifier.generate_synthetic_amd_sev_snp_report(measurement=tampered_measurement)
        is_valid, errors, details = verifier.verify_amd_sev_snp_report(
            snp_report, expected_measurement=GOLDEN_BASELINE_AMD_MEASUREMENT
        )

        assert is_valid is False
        assert any("launch measurement mismatch" in e for e in errors)
        assert details["measurement_verified"] is False

    def test_07_pedersen_commitment_hiding_and_binding(self, prover):
        """Verifies Pedersen Commitment hiding (different random blinds produce different C for same value)."""
        v = 0
        r1 = 123456789
        r2 = 987654321
        c1 = prover.commit(v, r1)
        c2 = prover.commit(v, r2)

        assert c1 != c2, "Different blinding factors must yield different commitments"
        # Deterministic with same blind
        assert prover.commit(v, r1) == c1

    def test_08_fiat_shamir_nizkp_zero_defects_proof_verification(self, prover):
        """Proves in Zero-Knowledge that critical vulnerability count equals zero."""
        proof = prover.prove_zero_defects(vulnerability_count=0)
        assert proof.proof_id.startswith("ZK-PRF-")
        assert proof.verified_property == "CRITICAL_VULNERABILITY_COUNT_EQUALS_ZERO"

        # Verifier checks proof without learning secrets
        is_valid = prover.verify_proof(proof)
        assert is_valid is True

    def test_09_nizkp_rejects_tampered_proof_or_statement(self, prover):
        """Ensures that modified challenges or responses cause mathematical proof rejection."""
        proof = prover.prove_zero_defects(vulnerability_count=0)

        # 1. Statement mismatch
        assert prover.verify_proof(proof, statement="Forged-Statement-Name") is False

        # 2. Tampered response z1
        tampered_dict = proof.to_dict()
        original_z1 = int(tampered_dict["response_z1"], 16)
        tampered_dict["response_z1"] = hex(original_z1 + 1)
        tampered_proof = ZKComplianceProof(**tampered_dict)
        assert prover.verify_proof(tampered_proof) is False

    def test_10_dual_signature_attestation_token_sealing(self, verifier, prover, sealer):
        """Verifies dual classical Ed25519 and post-quantum ML-DSA-87 signature sealing."""
        doc = verifier.generate_synthetic_nitro_attestation()
        _, _, details = verifier.verify_nitro_attestation(doc)
        proof = prover.prove_zero_defects()

        sealed_token = sealer.seal_attestation(details, proof)
        assert sealed_token.token_id.startswith("ATTEST-TOKEN-DSS-")
        assert len(sealed_token.classical_signature_ed25519) == 128  # 64 bytes hex
        assert len(sealed_token.post_quantum_signature_ml_dsa_87) == 9254  # 4627 bytes hex

        # Signature verification pass
        assert sealer.verify_sealed_token(sealed_token) is True

        # Tampered token fails
        tampered_token = sealed_token
        tampered_token.pcr_verification_status = "COMPROMISED"
        assert sealer.verify_sealed_token(tampered_token) is False

    def test_11_cli_interface_all_flags_execution(self):
        """Verifies all CLI flags execute with exit code 0 and proper brand headers."""
        engine_script = REPO_ROOT / "services" / "enterprise_zk_enclave_attestation_engine.py"
        assert engine_script.exists()

        flags = [
            ["--summary"],
            ["--verify-nitro-enclave"],
            ["--verify-amd-sev-snp"],
            ["--generate-zk-compliance-proof"],
            ["--verify-zk-proof"],
            ["--seal-attestation-token"],
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

    def test_12_strict_brand_anonymity_under_devsupersuite(self):
        """Enforces absolute brand anonymity under DevSuperSuite Cryptographic Engineering."""
        target_files = [
            REPO_ROOT / "services" / "enterprise_zk_enclave_attestation_engine.py",
            REPO_ROOT / "services" / "reports" / "zk_enclave_attestation_dossier.md",
            REPO_ROOT / "services" / "reports" / "zk_attestation_proof.json",
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

            # Scrub safe timestamps, ISO dates, and GUIDs before phone regex
            scrubbed = re.sub(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}", "", content)
            scrubbed = re.sub(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", "", scrubbed)
            scrubbed = re.sub(r"ATTEST-TOKEN-DSS-\d{8}-[A-F0-9]{8}", "", scrubbed)

            phone_matches = phone_pattern.findall(scrubbed)
            assert not phone_matches, (
                f"Brand anonymity violation: Found phone pattern in {file_path.name}: {phone_matches}"
            )

            # Confirm corporate identity
            assert "DevSuperSuite" in content, (
                f"Missing corporate brand DevSuperSuite in {file_path.name}"
            )
