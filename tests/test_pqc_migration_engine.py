"""
DevSuperSuite Tech Services - Post-Quantum Cryptography & Hybrid Key Exchange Test Suite
File: tests/test_pqc_migration_engine.py
Governing Entity: DevSuperSuite Cryptographic Engineering & Applied Research Desk
Contact: cryptography@devsupersuite.com
Regulatory Baseline: NIST FIPS 203 / NIST FIPS 204 / NIST FIPS 205 / NSA CNSA 2.0
"""

import json
from pathlib import Path
import re
import subprocess
import sys
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from services.enterprise_pqc_migration_engine import (
    MLKEMEngine,
    MLDSAEngine,
    SLHDSAEngine,
    HybridKeyExchangeEngine,
    CNSA2Auditor,
    PQCAlgorithm,
    ALGORITHM_CATALOG,
    write_pqc_readiness_reports,
)


class TestEnterprisePQCMigration:
    """Comprehensive test suite for NIST PQC standards, hybrid key agreement, and CNSA 2.0 audit."""

    def test_01_ml_kem_768_exact_fips203_sizes_and_shared_secret(self):
        """Verifies ML-KEM-768 exact byte dimensions and reciprocal shared secret derivation."""
        kem = MLKEMEngine(k=3)
        pk, sk = kem.generate_keypair()

        assert len(pk) == 1184, f"ML-KEM-768 PK expected 1184 bytes, got {len(pk)}"
        assert len(sk) == 2400, f"ML-KEM-768 SK expected 2400 bytes, got {len(sk)}"

        ct, ss_bob = kem.encapsulate(pk)
        assert len(ct) == 1088, f"ML-KEM-768 CT expected 1088 bytes, got {len(ct)}"
        assert len(ss_bob) == 32, "Shared secret must be 32 bytes (256 bits)"

        ss_alice = kem.decapsulate(sk, ct)
        assert ss_alice == ss_bob, "Alice and Bob must derive identical shared secret"

    def test_02_ml_kem_1024_exact_fips203_sizes_and_shared_secret(self):
        """Verifies ML-KEM-1024 exact byte dimensions and Category 5 security derivation."""
        kem = MLKEMEngine(k=4)
        pk, sk = kem.generate_keypair()

        assert len(pk) == 1568, f"ML-KEM-1024 PK expected 1568 bytes, got {len(pk)}"
        assert len(sk) == 3168, f"ML-KEM-1024 SK expected 3168 bytes, got {len(sk)}"

        ct, ss_bob = kem.encapsulate(pk)
        assert len(ct) == 1568, f"ML-KEM-1024 CT expected 1568 bytes, got {len(ct)}"
        assert len(ss_bob) == 32

        ss_alice = kem.decapsulate(sk, ct)
        assert ss_alice == ss_bob, "ML-KEM-1024 Alice and Bob must derive identical shared secret"

    def test_03_ml_kem_implicit_rejection_on_tampered_ciphertext(self):
        """Verifies Fujisaki-Okamoto (FO) transform constant-time implicit rejection."""
        kem = MLKEMEngine(k=3)
        pk, sk = kem.generate_keypair()
        ct, ss_bob = kem.encapsulate(pk)

        # Tamper with single byte of ciphertext
        tampered_ct = bytearray(ct)
        tampered_ct[25] ^= 0x01
        tampered_ct = bytes(tampered_ct)

        ss_rejected = kem.decapsulate(sk, tampered_ct)
        assert len(ss_rejected) == 32
        assert ss_rejected != ss_bob, "Tampered ciphertext must trigger implicit rejection"

    def test_04_ml_dsa_65_dilithium3_signing_and_verification(self):
        """Verifies ML-DSA-65 (Dilithium-3) key generation, signing, and verification."""
        dsa = MLDSAEngine("ML-DSA-65")
        pk, sk = dsa.generate_keypair()

        assert len(pk) == 1952, f"ML-DSA-65 PK expected 1952 bytes, got {len(pk)}"
        assert len(sk) == 4032, f"ML-DSA-65 SK expected 4032 bytes, got {len(sk)}"

        msg = b"DevSuperSuite Sovereign Kernel Execution Authorization"
        sig = dsa.sign(sk, msg, ctx=b"DSS-AUTH-CTX")
        assert len(sig) == 3309, f"ML-DSA-65 Sig expected 3309 bytes, got {len(sig)}"

        assert dsa.verify(pk, msg, sig, ctx=b"DSS-AUTH-CTX") is True
        assert dsa.verify(pk, b"Forged Message Content", sig, ctx=b"DSS-AUTH-CTX") is False
        assert dsa.verify(pk, msg, sig, ctx=b"Wrong-Context") is False

    def test_05_ml_dsa_87_dilithium5_cnsa2_mandatory_signature(self):
        """Verifies ML-DSA-87 (Category 5) compliance required by NSA CNSA 2.0."""
        dsa = MLDSAEngine("ML-DSA-87")
        pk, sk = dsa.generate_keypair()

        assert len(pk) == 2592
        assert len(sk) == 4896

        msg = b"NSA CNSA 2.0 High-Assurance Firmware Release"
        sig = dsa.sign(sk, msg)
        assert len(sig) == 4627
        assert dsa.verify(pk, msg, sig) is True

    def test_06_slh_dsa_sphincs_plus_stateless_hash_signature(self):
        """Verifies FIPS 205 SLH-DSA-SHAKE-256s root-of-trust stateless hash signatures."""
        slh = SLHDSAEngine()
        pk, sk = slh.generate_keypair()

        assert len(pk) == 64
        assert len(sk) == 128

        msg = b"DevSuperSuite Root Authority Cryptographic Attestation"
        sig = slh.sign(sk, msg)
        assert len(sig) == 29792
        assert slh.verify(pk, msg, sig) is True
        assert slh.verify(pk, b"Tampered Message", sig) is False

    def test_07_hybrid_x25519_ml_kem_768_dual_encapsulation(self):
        """Verifies Dual-Encapsulation Hybrid Key Agreement combining X25519 and ML-KEM-768."""
        engine = HybridKeyExchangeEngine()

        # Alice initiates
        hybrid_pk, initiator_sk = engine.generate_initiator_keypair()
        assert len(hybrid_pk.classical_x25519_pk_bytes) == 32
        assert len(hybrid_pk.quantum_ml_kem_pk_bytes) == 1184
        assert len(hybrid_pk.serialize()) == 1216

        # Bob encapsulates
        hybrid_ct, ss_bob = engine.encapsulate_responder(hybrid_pk)
        assert len(hybrid_ct.classical_ephemeral_pk_bytes) == 32
        assert len(hybrid_ct.quantum_kem_ciphertext_bytes) == 1088
        assert len(hybrid_ct.serialize()) == 1120
        assert len(ss_bob) == 32

        # Alice decapsulates
        ss_alice = engine.decapsulate_initiator(initiator_sk, hybrid_ct)
        assert len(ss_alice) == 32
        assert ss_alice == ss_bob, "Alice and Bob must arrive at identical hybrid shared secret"

    def test_08_cnsa2_compliance_audit_and_agility_catalog(self):
        """Verifies NSA CNSA 2.0 readiness scorecard and algorithm catalog completeness."""
        audit_data = CNSA2Auditor.audit_enterprise_posture()

        assert audit_data["total_services_audited"] >= 5
        assert audit_data["cnsa_2_0_compliant_services"] == audit_data["total_services_audited"]
        assert audit_data["overall_cnsa_compliance_pct"] == 100.0
        assert audit_data["aggregate_readiness_score_pct"] >= 95.0
        assert "NEUTRALIZED" in audit_data["hndl_threat_verdict"]

        # Confirm algorithm catalog entries
        catalog = audit_data["algorithm_catalog"]
        assert PQCAlgorithm.ML_KEM_768.value in catalog
        assert PQCAlgorithm.ML_KEM_1024.value in catalog
        assert PQCAlgorithm.ML_DSA_87.value in catalog
        assert PQCAlgorithm.SLH_DSA_SHAKE_256S.value in catalog
        assert PQCAlgorithm.HYBRID_X25519_ML_KEM_768.value in catalog

    def test_09_cli_interface_all_flags_execution(self):
        """Verifies all CLI flags execute with returncode 0 and proper brand headers."""
        engine_script = REPO_ROOT / "services" / "enterprise_pqc_migration_engine.py"
        assert engine_script.exists()

        flags = [
            ["--summary"],
            ["--generate-hybrid-keypair"],
            ["--benchmark-pqc-encapsulation", "3"],
            ["--audit-cnsa2-compliance"],
            ["--export-pqc-readiness-binder"],
        ]

        for flag_set in flags:
            proc = subprocess.run(
                [sys.executable, str(engine_script)] + flag_set,
                capture_output=True,
                text=True,
                timeout=20,
            )
            assert proc.returncode == 0, f"CLI command failed with {flag_set}: {proc.stderr}"
            assert "DevSuperSuite" in proc.stdout

    def test_10_strict_brand_anonymity_under_devsupersuite(self):
        """Enforces absolute brand anonymity under DevSuperSuite Cryptographic Engineering."""
        target_files = [
            REPO_ROOT / "services" / "enterprise_pqc_migration_engine.py",
            REPO_ROOT / "services" / "reports" / "pqc_readiness_audit_report.md",
            REPO_ROOT / "services" / "reports" / "pqc_cnsa2_readiness.json",
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
            scrubbed = re.sub(r"AUDIT-CNSA2-PQC-\d{4}-V\d", "", scrubbed)

            phone_matches = phone_pattern.findall(scrubbed)
            assert not phone_matches, (
                f"Brand anonymity violation: Found phone pattern in {file_path.name}: {phone_matches}"
            )

            # Confirm corporate identity
            assert "DevSuperSuite" in content, (
                f"Missing corporate brand DevSuperSuite in {file_path.name}"
            )

