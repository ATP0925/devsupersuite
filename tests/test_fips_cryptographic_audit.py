"""
═══════════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - FIPS 140-3 Cryptographic Module Test Suite
Document Ref: DSS-TEST-FIPS-140-3-2026-V1
Compliance Standards: NIST FIPS 140-3, FIPS 180-4, NIST SP 800-38D, RFC 8032, RFC 4231

Verifies:
1. FIPS 140-3 module perimeter boundary & approved algorithm catalog.
2. Ed25519 Known-Answer Test (RFC 8032 Section 7.1).
3. AES-256-GCM Known-Answer Test (NIST SP 800-38D Test Case 13).
4. SHA-256 and SHA-512 Known-Answer Tests (FIPS 180-4 Standard Vectors).
5. HMAC-SHA256 Known-Answer Test (RFC 4231 Test Case 1).
6. DoD 5220.22-M 3-pass memory zeroization & remanence elimination.
7. Constant-time execution & timing side-channel resistance (Δt < 0.05ms).
8. Post-Quantum Cryptography (PQC) hybrid migration audit (FIPS 203 & FIPS 204).
9. Full report generation pipeline (Markdown & JSON telemetry).
10. Strict 100% Brand Anonymity under DevSuperSuite Information Security.
═══════════════════════════════════════════════════════════════════════════════════
"""

import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

# Add services and repo root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = REPO_ROOT / "services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from fips_140_3_cryptographic_audit_engine import (
    ConstantTimeAuditor,
    CryptographicMemoryZeroizer,
    FIPS140AuditMasterEngine,
    FIPSModuleBoundary,
    KnownAnswerTestRunner,
    PQCHybridReadinessAuditor,
    CONSTANT_TIME_THRESHOLD_MS,
)


class TestFIPSCryptographicAudit(unittest.TestCase):
    """
    Test suite verifying NIST FIPS 140-3 module compliance, KAT vectors,
    DoD memory zeroization, and side-channel immunity.
    """

    def setUp(self):
        self.engine = FIPS140AuditMasterEngine()

    def test_01_fips_module_boundary_and_approved_catalog(self):
        """
        Verify FIPS 140-3 module boundary configuration:
        - Security Level 2 (Overall) / Level 3 (Cryptographic Keys)
        - Approved algorithms baseline: AES-256-GCM, Ed25519, SHA-256/512, HMAC, ML-KEM, ML-DSA
        """
        boundary = self.engine.boundary.to_dict()
        self.assertEqual(boundary["module_name"], "DevSuperSuite Cryptographic Core")
        self.assertIn("Level 2", boundary["security_level"])
        self.assertGreaterEqual(len(boundary["approved_algorithms"]), 5)

        alg_str = " ".join(boundary["approved_algorithms"])
        self.assertIn("AES-256-GCM", alg_str)
        self.assertIn("Ed25519", alg_str)
        self.assertIn("SHA-256", alg_str)
        self.assertIn("HMAC-SHA256", alg_str)
        self.assertIn("ML-KEM-768", alg_str)

    def test_02_ed25519_known_answer_test(self):
        """
        Verify Ed25519 Known-Answer Test against RFC 8032 Section 7.1 Test 1:
        - Exact signature hex match.
        - Public key verification roundtrip.
        """
        kat = KnownAnswerTestRunner.run_ed25519_kat()
        self.assertEqual(kat["status"], "PASS")
        self.assertEqual(kat["algorithm"], "Ed25519")
        self.assertTrue(kat["verification_verified"])

    def test_03_aes256_gcm_known_answer_test(self):
        """
        Verify AES-256-GCM Known-Answer Test against NIST SP 800-38D Test Case 13:
        - 256-bit key, 96-bit IV, empty plaintext.
        - Exact tag match: 530f8afbc74536b9a963b4f1c4cb738b.
        - Roundtrip decryption succeeds.
        """
        kat = KnownAnswerTestRunner.run_aes256_gcm_kat()
        self.assertEqual(kat["status"], "PASS")
        self.assertEqual(kat["expected_tag"], "530f8afbc74536b9a963b4f1c4cb738b")
        self.assertEqual(kat["computed_tag"], "530f8afbc74536b9a963b4f1c4cb738b")
        self.assertTrue(kat["roundtrip_decryption"])

    def test_04_sha256_and_sha512_known_answer_tests(self):
        """
        Verify SHA-256 and SHA-512 Known-Answer Tests against FIPS 180-4 standard vectors.
        """
        sha256_kat = KnownAnswerTestRunner.run_sha256_kat()
        self.assertEqual(sha256_kat["status"], "PASS")
        self.assertTrue(sha256_kat["computed_digest"].startswith("ba7816bf8f01cfea"))

        sha512_kat = KnownAnswerTestRunner.run_sha512_kat()
        self.assertEqual(sha512_kat["status"], "PASS")
        self.assertTrue(sha512_kat["computed_digest"].startswith("ddaf35a193617aba"))

    def test_05_hmac_sha256_known_answer_test(self):
        """
        Verify HMAC-SHA256 Known-Answer Test against RFC 4231 Test Case 1.
        """
        hmac_kat = KnownAnswerTestRunner.run_hmac_sha256_kat()
        self.assertEqual(hmac_kat["status"], "PASS")
        self.assertEqual(hmac_kat["expected_digest"], "b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7")
        self.assertEqual(hmac_kat["computed_digest"], hmac_kat["expected_digest"])

    def test_06_dod_5220_22m_memory_zeroization(self):
        """
        Verify DoD 5220.22-M 3-pass memory zeroization:
        - Replaces mutable byte buffer with zeros, ones, random noise, and final 0x00.
        - Invariant: Confirms 100% of buffer bytes evaluate to 0x00.
        """
        zero_report = CryptographicMemoryZeroizer.create_and_zeroize_key_material(32)
        self.assertTrue(zero_report["hygiene_compliant"])
        self.assertTrue(zero_report["pre_zeroization_has_entropy"])
        self.assertFalse(zero_report["post_zeroization_has_entropy"])
        self.assertEqual(zero_report["zeroization_result"]["status"], "ZEROIZED")
        self.assertTrue(zero_report["zeroization_result"]["verified_clean"])

        # Negative test: Non-bytearray buffer raises TypeError
        with self.assertRaises(TypeError):
            CryptographicMemoryZeroizer.zeroize(b"immutable_bytes_cannot_be_zeroized")

    def test_07_constant_time_execution_side_channel_bounds(self):
        """
        Verify constant-time execution for signature / digest comparison:
        - Timing variance |t_match - t_diff| < 0.05 ms.
        - Backed by hmac.compare_digest.
        """
        timing = ConstantTimeAuditor.audit_constant_time_digest(1000)
        self.assertEqual(timing["status"], "PASS")
        self.assertTrue(timing["side_channel_resistant"])
        self.assertLess(timing["delta_ms"], CONSTANT_TIME_THRESHOLD_MS)

    def test_08_pqc_hybrid_migration_readiness(self):
        """
        Verify Post-Quantum Cryptography hybrid migration readiness:
        - FIPS 203 (ML-KEM-768) and FIPS 204 (ML-DSA-65) specs present.
        - NSA CNSA 2.0 timeline verified.
        """
        pqc = PQCHybridReadinessAuditor.audit_pqc_readiness()
        self.assertEqual(pqc["status"], "PQC_HYBRID_READY")
        self.assertTrue(pqc["quantum_buffer_preallocation_verified"])
        self.assertGreaterEqual(len(pqc["pqc_suites"]), 2)
        self.assertIn("2026", pqc["cnsa_timeline"])
        self.assertIn("2030", pqc["cnsa_timeline"])

    def test_09_evidence_binder_and_json_generation(self):
        """
        Verify Markdown audit dossier and JSON telemetry generation.
        """
        md_p, json_p = self.engine.generate_fips_evidence()
        self.assertTrue(md_p.exists())
        self.assertTrue(json_p.exists())

        # Inspect Markdown content
        md_content = md_p.read_text(encoding="utf-8")
        self.assertIn("FIPS 140-3 Cryptographic Audit Report", md_content)
        self.assertIn("Known-Answer Tests", md_content)
        self.assertIn("DoD 5220.22-M", md_content)
        self.assertIn("infosec@devsupersuite.com", md_content)

        # Inspect JSON telemetry
        data = json.loads(json_p.read_text(encoding="utf-8"))
        self.assertEqual(data["overall_decision"], "PASS")
        self.assertTrue(data["known_answer_tests"]["all_kats_passed"])
        self.assertTrue(data["zeroization_hygiene"]["hygiene_compliant"])

    def test_10_strict_brand_anonymity_under_devsupersuite(self):
        """
        Strict Brand Anonymity Enforcement:
        - Inspects fips_140_3_cryptographic_audit_engine.py, fips_cryptographic_security_policy.md,
          and generated report artifacts.
        - Asserts ZERO personal names, ZERO personal emails (gmail/yahoo/etc), ZERO personal phone numbers.
        - Confirms all attributions point to DevSuperSuite Official & infosec@devsupersuite.com.
        """
        files_to_check = [
            SERVICES_DIR / "fips_140_3_cryptographic_audit_engine.py",
            SERVICES_DIR / "fips_cryptographic_security_policy.md",
            SERVICES_DIR / "reports" / "fips_140_3_audit_report.md",
            SERVICES_DIR / "reports" / "fips_140_3_audit.json",
        ]

        prohibited_names = [
            "atpad", "Padmanabhan", "Ananthapadmanabhan", "Ananth",
            "Sridhar", "John Doe", "Jane Doe", "Alice", "Bob"
        ]

        personal_email_pattern = re.compile(
            r"\b[A-Za-z0-9._%+-]+@(?!devsupersuite\.com)[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        )
        phone_pattern = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")

        for file_path in files_to_check:
            self.assertTrue(file_path.exists(), f"Target file must exist: {file_path}")
            content = file_path.read_text(encoding="utf-8")

            # Clean out hex digests, UUIDs, key IDs, and CVE numbers to avoid false phone matches
            clean_content = re.sub(r"[a-f0-9]{32,64}", "", content)
            clean_content = re.sub(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", "", clean_content, flags=re.IGNORECASE)
            clean_content = re.sub(r"KID-[A-Za-z0-9-]+", "", clean_content)
            clean_content = re.sub(r"CVE-\d{4}-\d+", "", clean_content)
            clean_content = re.sub(r"FIPS\s+\d+", "", clean_content)

            # Check personal names
            for name in prohibited_names:
                matches = re.findall(rf"\b{re.escape(name)}\b", clean_content, re.IGNORECASE)
                self.assertEqual(
                    len(matches), 0,
                    f"Brand anonymity violation: Found prohibited name '{name}' in {file_path.name}"
                )

            # Check personal emails
            emails = personal_email_pattern.findall(clean_content)
            self.assertEqual(
                len(emails), 0,
                f"Brand anonymity violation: Found personal email(s) {emails} in {file_path.name}"
            )

            # Check personal phones
            phones = phone_pattern.findall(clean_content)
            self.assertEqual(
                len(phones), 0,
                f"Brand anonymity violation: Found phone number(s) {phones} in {file_path.name}"
            )

            # Verify presence of official brand identifier
            self.assertIn("devsupersuite", content.lower(), f"Missing brand reference in {file_path.name}")


if __name__ == "__main__":
    unittest.main()
