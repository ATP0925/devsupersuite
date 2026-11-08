"""
DevSuperSuite Tech Services - Post-Quantum Cryptography (PQC) ML-KEM & CNSA 2.0 Test Suite
File: tests/test_pqc_mlkem.py
Governing Authority: DevSuperSuite Security & Compliance Desk
Contact: security@devsupersuite.com
Regulatory Baseline: NIST FIPS 203 / NIST FIPS 204 / NSA CNSA 2.0 / CNSSP-15
"""

import json
from pathlib import Path
import re
import subprocess
import sys
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from services.enterprise_pqc_mlkem_engine import (
    MLKEMEngine,
    MLDSAEngine,
    HybridTLSKeyExchangeSimulator,
    CNSA2AttestationEngine,
    PQCParameterSet,
    PQC_SPECIFICATIONS,
    export_pqc_mlkem_cnsa2_artifacts,
)


class TestEnterprisePQCMLKEM:
    """Comprehensive test suite for NIST FIPS 203, FIPS 204, and NSA CNSA 2.0 SCIF attestation."""

    def test_01_ml_kem_768_exact_fips203_dimensions_and_roundtrip(self):
        """Verifies ML-KEM-768 exact byte dimensions and reciprocal shared secret derivation."""
        kem = MLKEMEngine("ML-KEM-768")
        kp = kem.generate_keypair()

        assert len(kp.public_key) == 1184, f"ML-KEM-768 PK expected 1184B, got {len(kp.public_key)}"
        assert len(kp.private_key) == 2400, f"ML-KEM-768 SK expected 2400B, got {len(kp.private_key)}"
        assert kp.fingerprint.startswith("MLKEM-")

        ct, ss_bob = kem.encapsulate(kp.public_key)
        assert len(ct) == 1088, f"ML-KEM-768 CT expected 1088B, got {len(ct)}"
        assert len(ss_bob) == 32, "Shared secret must be 32 bytes (256 bits)"

        ss_alice = kem.decapsulate(kp.private_key, ct)
        assert ss_alice == ss_bob, "Alice and Bob must derive identical shared secret"

    def test_02_ml_kem_1024_exact_fips203_dimensions_and_roundtrip(self):
        """Verifies ML-KEM-1024 (Level 5) exact dimensions and decapsulation match."""
        kem = MLKEMEngine("ML-KEM-1024")
        kp = kem.generate_keypair()

        assert len(kp.public_key) == 1568, f"ML-KEM-1024 PK expected 1568B, got {len(kp.public_key)}"
        assert len(kp.private_key) == 3168, f"ML-KEM-1024 SK expected 3168B, got {len(kp.private_key)}"

        ct, ss_bob = kem.encapsulate(kp.public_key)
        assert len(ct) == 1568, f"ML-KEM-1024 CT expected 1568B, got {len(ct)}"
        assert len(ss_bob) == 32

        ss_alice = kem.decapsulate(kp.private_key, ct)
        assert ss_alice == ss_bob, "ML-KEM-1024 Alice and Bob must derive identical shared secret"

    def test_03_ml_kem_fo_transform_implicit_rejection(self):
        """Verifies Fujisaki-Okamoto constant-time implicit rejection on corrupted ciphertext."""
        kem = MLKEMEngine("ML-KEM-768")
        kp = kem.generate_keypair()
        ct, ss_bob = kem.encapsulate(kp.public_key)

        tampered_ct = bytearray(ct)
        tampered_ct[42] ^= 0xFF
        tampered_ct = bytes(tampered_ct)

        ss_rejected = kem.decapsulate(kp.private_key, tampered_ct)
        assert len(ss_rejected) == 32, "Implicit rejection must output 32-byte pseudo-random secret"
        assert ss_rejected != ss_bob, "Corrupted ciphertext must not yield legitimate shared secret"

    def test_04_ml_dsa_65_dilithium3_signing_and_verification(self):
        """Verifies ML-DSA-65 (Dilithium-3) keypair generation, signing, and verification."""
        dsa = MLDSAEngine("ML-DSA-65")
        kp = dsa.generate_keypair()

        assert len(kp.public_key) == 1952, f"ML-DSA-65 PK expected 1952B, got {len(kp.public_key)}"
        assert len(kp.private_key) == 4032, f"ML-DSA-65 SK expected 4032B, got {len(kp.private_key)}"

        message = b"DevSuperSuite Sovereign SCIF Enclave Policy Authorization"
        sig = dsa.sign(kp.private_key, message, ctx=b"SCIF-AUTH-V1")
        assert len(sig) == 3309, f"ML-DSA-65 Sig expected 3309B, got {len(sig)}"

        assert dsa.verify(kp.public_key, message, sig, ctx=b"SCIF-AUTH-V1") is True
        assert dsa.verify(kp.public_key, b"Corrupted Message Payload", sig, ctx=b"SCIF-AUTH-V1") is False
        assert dsa.verify(kp.public_key, message, sig, ctx=b"Wrong-Context") is False

    def test_05_ml_dsa_87_dilithium5_cnsa2_mandatory_dimensions_and_verification(self):
        """Verifies ML-DSA-87 (Category 5) mandatory CNSA 2.0 digital signature scheme."""
        dsa = MLDSAEngine("ML-DSA-87")
        kp = dsa.generate_keypair()

        assert len(kp.public_key) == 2592, f"ML-DSA-87 PK expected 2592B, got {len(kp.public_key)}"
        assert len(kp.private_key) == 4896, f"ML-DSA-87 SK expected 4896B, got {len(kp.private_key)}"

        message = b"NSA CNSA 2.0 Air-Gapped Firmware Cryptographic Verification"
        sig = dsa.sign(kp.private_key, message, ctx=b"CNSA2-FIRMWARE-V1")
        assert len(sig) == 4627, f"ML-DSA-87 Sig expected 4627B, got {len(sig)}"

        assert dsa.verify(kp.public_key, message, sig, ctx=b"CNSA2-FIRMWARE-V1") is True
        assert dsa.verify(kp.public_key, message, sig, ctx=b"Mismatched-Ctx") is False

    def test_06_ml_dsa_signature_tamper_rejection(self):
        """Verifies ML-DSA robustly rejects tampered signatures and malformed keys."""
        dsa = MLDSAEngine("ML-DSA-87")
        kp = dsa.generate_keypair()
        message = b"Critical Sovereign Command"
        sig = dsa.sign(kp.private_key, message)

        tampered_sig = bytearray(sig)
        tampered_sig[10] ^= 0x01
        tampered_sig = bytes(tampered_sig)

        assert dsa.verify(kp.public_key, message, tampered_sig) is False
        assert dsa.verify(kp.public_key[:100], message, sig) is False
        assert dsa.verify(kp.public_key, message, sig[:100]) is False

    def test_07_hybrid_tls_handshake_simulation_agreement(self):
        """Verifies simulated hybrid TLS 1.3 key exchange derives matching master secrets."""
        simulator = HybridTLSKeyExchangeSimulator(scif_enclave_id="SCIF-USA-TEST-ENCLAVE-07")
        session = simulator.simulate_full_handshake()

        assert session.secrets_match is True
        assert session.initiator_public_key_bytes == 1216  # 32 (X25519) + 1184 (ML-KEM-768)
        assert session.responder_ciphertext_bytes == 1120  # 32 (X25519) + 1088 (ML-KEM-768)
        assert session.cnsa2_attested is True
        assert session.sovereign_airgap_verified is True
        assert len(session.client_shared_secret) == 64  # Hex encoded 32 bytes
        assert session.client_shared_secret == session.server_shared_secret

    def test_08_hybrid_tls_handshake_tamper_rejection(self):
        """Verifies tampering with hybrid ciphertext prevents secret derivation match."""
        simulator = HybridTLSKeyExchangeSimulator()
        client_pk, client_sk = simulator.generate_initiator_keyshare()
        server_ct, server_ss = simulator.respond_and_encapsulate(client_pk)

        # Tamper with server ciphertext
        tampered_raw = bytearray(server_ct.serialize())
        tampered_raw[50] ^= 0x55
        tampered_ct = type(server_ct).deserialize(bytes(tampered_raw))

        client_ss = simulator.decapsulate_initiator(client_sk, tampered_ct)
        assert client_ss != server_ss, "Tampered hybrid ciphertext must not produce matching secret"

    def test_09_cnsa2_scif_attestation_engine_audit(self):
        """Verifies NSA CNSA 2.0 SCIF readiness audit scorecard and dual signature sealing."""
        audit = CNSA2AttestationEngine.run_cnsa2_audit()

        assert audit["total_scif_workloads"] >= 5
        assert audit["cnsa_2_0_compliant_workloads"] == audit["total_scif_workloads"]
        assert audit["cnsa_compliance_ratio_pct"] == 100.0
        assert audit["aggregate_resilience_score"] >= 95.0
        assert "NEUTRALIZED" in audit["hndl_adversary_threat_status"]

        # Verify cryptographic attestation sealing block
        attestation = audit["cryptographic_attestation"]
        assert attestation["attestation_status"] == "VALID_SEALED"
        assert len(bytes.fromhex(attestation["classical_ed25519_pk"])) == 32
        assert len(bytes.fromhex(attestation["classical_ed25519_sig"])) == 64
        assert attestation["quantum_mldsa87_sig_bytes"] == 4627

    def test_10_manifest_and_report_file_generation_and_schema(self):
        """Verifies manifest and audit report generation, structure, and schema compliance."""
        audit = CNSA2AttestationEngine.run_cnsa2_audit()
        simulator = HybridTLSKeyExchangeSimulator()
        session = simulator.simulate_full_handshake()

        manifest_path, report_path = export_pqc_mlkem_cnsa2_artifacts(audit, session)
        assert manifest_path.exists(), f"Manifest file missing: {manifest_path}"
        assert report_path.exists(), f"Report file missing: {report_path}"

        # Verify JSON manifest
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        assert manifest_data["audit_reference"] == "AUDIT-CNSA2-MLKEM-2026-V1"
        assert manifest_data["cnsa_compliance_ratio_pct"] == 100.0
        assert "simulated_hybrid_handshake" in manifest_data
        assert manifest_data["simulated_hybrid_handshake"]["secrets_match"] is True

        # Verify Markdown report
        report_text = report_path.read_text(encoding="utf-8")
        assert "NIST FIPS 203" in report_text
        assert "NIST FIPS 204" in report_text
        assert "NSA CNSA 2.0" in report_text
        assert "SCIF-USA-EAST-SECURE-ENCLAVE-01" in report_text

    def test_11_cli_interface_all_flags_execution(self):
        """Verifies all CLI flags execute with zero exit code and DevSuperSuite branding."""
        engine_script = REPO_ROOT / "services" / "enterprise_pqc_mlkem_engine.py"
        assert engine_script.exists()

        flags = [
            ["--simulate-handshake"],
            ["--verify-vectors"],
            ["--audit"],
            ["--manifest"],
            ["--report"],
        ]

        for flag_set in flags:
            proc = subprocess.run(
                [sys.executable, str(engine_script)] + flag_set,
                capture_output=True,
                text=True,
                timeout=25,
            )
            assert proc.returncode == 0, f"CLI command failed with {flag_set}: {proc.stderr}"
            assert "DevSuperSuite" in proc.stdout

    def test_12_strict_brand_anonymity_under_devsupersuite(self):
        """Enforces strict 100% brand anonymity under DevSuperSuite Security & Compliance Desk."""
        target_files = [
            REPO_ROOT / "services" / "enterprise_pqc_mlkem_engine.py",
            REPO_ROOT / "services" / "reports" / "pqc_mlkem_cnsa2_manifest.json",
            REPO_ROOT / "services" / "reports" / "pqc_mlkem_cnsa2_readiness_report.md",
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

            # Scrub safe timestamps, ISO dates, GUIDs, and specific audit IDs before phone check
            scrubbed = re.sub(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}", "", content)
            scrubbed = re.sub(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", "", scrubbed)
            scrubbed = re.sub(r"AUDIT-CNSA2-MLKEM-\d{4}-V\d", "", scrubbed)

            phone_matches = phone_pattern.findall(scrubbed)
            assert not phone_matches, (
                f"Brand anonymity violation: Found phone pattern in {file_path.name}: {phone_matches}"
            )

            # Confirm corporate identity
            assert "DevSuperSuite" in content, (
                f"Missing corporate brand DevSuperSuite in {file_path.name}"
            )
            assert "security@devsupersuite.com" in content, (
                f"Missing corporate email in {file_path.name}"
            )
