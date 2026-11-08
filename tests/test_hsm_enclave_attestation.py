#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Automated Verification Suite: HSM & FIPS 140-3 Enclave
Reference: DSS-TEST-CRYPTO-HSM-2026-V1
Target: Continuous Verification of Hardware Enclaves, Ed25519 Keys & Memory Zeroization
Contact: DevSuperSuite Information Security (infosec@devsupersuite.com)
Author: Directorate of QA Automation & Security Compliance, DevSuperSuite Official
═══════════════════════════════════════════════════════════════════════════════════
"""

import json
import os
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = REPO_ROOT / "services"
REPORTS_DIR = SERVICES_DIR / "reports"
DEPLOYMENT_DIR = REPO_ROOT / "deployment"
TESTS_DIR = REPO_ROOT / "tests"

sys.path.insert(0, str(SERVICES_DIR))

from hsm_enclave_attestation_engine import (
    CryptographicMemoryZeroizer,
    HardwareEnclaveProfile,
    HardwareEnclaveAttestationEngine,
    Ed25519RootAuthorityKeyManager,
    HSMEnclaveAttestationEngine,
    run_hsm_pipeline,
    ATTESTATION_MD_PATH,
    ATTESTATION_JSON_PATH,
    KEYS_VAULT_PATH,
)


class TestHSMEnclaveAttestation(unittest.TestCase):
    """
    Continuous regression test suite validating hardware security module (HSM) attestation,
    FIPS 140-3 cryptographic key rotation, and DoD 5220.22-M memory zeroization.
    """

    def setUp(self) -> None:
        self.engine = HSMEnclaveAttestationEngine(repo_root=REPO_ROOT)
        self.enclave_verifier = HardwareEnclaveAttestationEngine(repo_root=REPO_ROOT)
        self.key_manager = Ed25519RootAuthorityKeyManager(vault_path=KEYS_VAULT_PATH)

    def test_01_hardware_enclave_quote_verification(self) -> None:
        """
        Verifies hardware attestation quotes across TPM 2.0, AWS Nitro, GCP Confidential VM,
        and Apple Secure Enclave.
        """
        expected_platforms = ["TPM_2_0", "AWS_NITRO", "GCP_CONFIDENTIAL_VM", "APPLE_SECURE_ENCLAVE"]

        for plat_id in expected_platforms:
            quote = self.enclave_verifier.verify_enclave_quote(plat_id)
            self.assertEqual(quote["platform_id"], plat_id)
            self.assertTrue(quote["nonce_verified"])
            self.assertGreater(quote["pcr_count"], 0)
            self.assertEqual(len(quote["quote_signature_sha256"]), 64)
            self.assertEqual(quote["attestation_status"], "VERIFIED_AUTHENTIC")

        all_res = self.enclave_verifier.verify_all_enclave_platforms()
        self.assertEqual(all_res["overall_status"], "PASS")
        self.assertEqual(all_res["platforms_verified"], 4)

    def test_02_ed25519_keypair_generation_and_signatures(self) -> None:
        """
        Validates FIPS 140-3 compliant Ed25519 key generation, 256-bit key length,
        SHA-256 fingerprinting, and digital signature verification.
        """
        priv_key, pub_key, meta = self.key_manager.generate_new_root_keypair()

        self.assertEqual(meta["algorithm"], "Ed25519 (FIPS 186-5 & RFC 8032)")
        self.assertEqual(meta["key_length_bits"], 256)
        self.assertTrue(meta["key_id"].startswith("KID-ED25519-"))
        self.assertEqual(len(meta["sha256_fingerprint"]), 64)
        self.assertEqual(meta["state"], "ACTIVE")

        # Test signature and verification
        test_payload = b"Commerce-Attestation-Signature-Test"
        sig = priv_key.sign(test_payload)
        self.assertEqual(len(sig), 64)
        # Verify must not raise
        pub_key.verify(sig, test_payload)

    def test_03_ed25519_root_key_rotation(self) -> None:
        """
        Validates automated cryptographic root authority key rotation:
        prior key archived, new key active, and raw private key zeroized in memory.
        """
        rot_res = self.key_manager.rotate_root_keys()

        self.assertEqual(rot_res["action"], "KEY_ROTATION_SUCCESSFUL")
        self.assertEqual(rot_res["signature_verification"], "VERIFIED_PASS")
        self.assertEqual(rot_res["memory_zeroization"]["status"], "ZEROIZED")

        active_meta = self.key_manager.load_active_key_metadata()
        self.assertIsNotNone(active_meta)
        self.assertEqual(active_meta["state"], "ACTIVE")
        self.assertEqual(active_meta["key_id"], rot_res["new_active_key"]["key_id"])

    def test_04_dod_5220_22_m_memory_zeroization(self) -> None:
        """
        Tests DoD 5220.22-M / NIST SP 800-88 Rev 1 compliant 3-pass memory sanitization.
        """
        test_data = bytearray(os.urandom(128))
        self.assertTrue(any(b != 0 for b in test_data))

        res = CryptographicMemoryZeroizer.zeroize(test_data)

        self.assertEqual(res["bytes_zeroized"], 128)
        self.assertEqual(res["passes_completed"], 3)
        self.assertTrue(res["final_state_verified_zero"])
        self.assertEqual(res["status"], "ZEROIZED")
        self.assertTrue(all(b == 0 for b in test_data))

        # Enforce TypeError on immutable bytes
        with self.assertRaises(TypeError):
            CryptographicMemoryZeroizer.zeroize(b"immutable_bytes")  # type: ignore

    def test_05_fips_140_3_cryptographic_posture_audit(self) -> None:
        """
        Audits cryptographic posture across algorithms, enclaves, and container RAM isolation.
        """
        posture = self.engine.audit_cryptographic_posture()

        self.assertEqual(posture["overall_status"], "PASS")
        self.assertIn("FIPS 140-3 Level 3", posture["fips_140_compliance_level"])
        self.assertEqual(posture["hardware_enclaves"]["platforms_verified"], 4)
        self.assertEqual(posture["memory_zeroization_protocol"]["status"], "ZEROIZED")

    def test_06_enclave_attestation_report_artifacts(self) -> None:
        """
        Validates generation of the executive Markdown report and machine-readable JSON.
        """
        md_path = self.engine.generate_markdown_report()
        json_path = self.engine.export_attestation_json()

        self.assertTrue(md_path.exists())
        self.assertTrue(json_path.exists())

        with open(md_path, "r", encoding="utf-8") as f:
            md_text = f.read()

        self.assertIn("DevSuperSuite HSM & FIPS 140-3 Enclave Hardware Attestation Report", md_text)
        self.assertIn("Hardware Enclave Attestation Matrix", md_text)
        self.assertIn("DoD 5220.22-M Cryptographic Memory Sanitization Protocol", md_text)
        self.assertIn("OFFICIAL HARDWARE SECURITY MODULE & FIPS 140-3 ATTESTATION SEAL", md_text)

        with open(json_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        self.assertEqual(json_data["metadata"]["organization"], "DevSuperSuite Official")
        self.assertIn("sha256_digest", json_data["metadata"])
        self.assertEqual(len(json_data["metadata"]["sha256_digest"]), 64)
        self.assertEqual(json_data["cryptographic_attestation_summary"]["overall_status"], "CERTIFIED_FIPS_140_3_COMPLIANT")

    def test_07_cli_flags_execution(self) -> None:
        """
        Validates CLI execution across all flags with exit code 0.
        """
        ret_verify = run_hsm_pipeline(verify_enclave=True, summary=False, repo_root=REPO_ROOT)
        self.assertEqual(ret_verify, 0)

        ret_rotate = run_hsm_pipeline(rotate_keys=True, summary=False, repo_root=REPO_ROOT)
        self.assertEqual(ret_rotate, 0)

        ret_audit = run_hsm_pipeline(audit_posture=True, summary=False, repo_root=REPO_ROOT)
        self.assertEqual(ret_audit, 0)

    def test_08_strict_brand_anonymity_under_infosec_devsupersuite(self) -> None:
        """
        Enforces 100% Brand Anonymity under DevSuperSuite Information Security (infosec@devsupersuite.com).
        Zero personal founder names, personal handles, personal emails, or phone numbers.
        """
        files_to_check = [
            SERVICES_DIR / "hsm_enclave_attestation_engine.py",
            ATTESTATION_MD_PATH,
            ATTESTATION_JSON_PATH,
        ]

        forbidden_patterns = [
            r"\b[A-Za-z0-9._%+-]+@(?!(?:devsupersuite\.com))\w+\.\w+\b",
            r"(?<![a-zA-Z0-9])(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}(?![a-zA-Z0-9])",
            r"github\.com\/(?!DevSuperSuiteOfficial)[a-zA-Z0-9_\-]+",
        ]

        for filepath in files_to_check:
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                self.assertIn("DevSuperSuite", content, f"Must reference DevSuperSuite in {filepath.name}")
                self.assertIn("infosec@devsupersuite.com", content, f"Must reference official contact in {filepath.name}")

                # Exclude cryptographic hex digests and key IDs to avoid false positives on digit runs
                cleaned_content = re.sub(r"[a-f0-9]{32,64}", "", content, flags=re.IGNORECASE)
                cleaned_content = re.sub(r"KID-ED25519-[A-Za-z0-9]+", "", cleaned_content)

                for pattern in forbidden_patterns:
                    matches = list(re.finditer(pattern, cleaned_content, re.IGNORECASE))
                    self.assertEqual(len(matches), 0, f"Found forbidden personal pattern in {filepath.name}: {matches}")


if __name__ == "__main__":
    unittest.main()
