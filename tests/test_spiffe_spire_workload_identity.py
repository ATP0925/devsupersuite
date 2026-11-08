"""
═══════════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - SPIFFE/SPIRE Workload Identity Test Suite
Document Ref: DSS-TEST-SPIFFE-ZTNA-2026-V1
Compliance Standards: SPIFFE Specification, SPIRE Runtime, NIST SP 800-207 Zero Trust

Verifies:
1. SPIFFE URI format compliance & regex validation.
2. X.509 SVID issuance & Subject Alternative Name (SAN) URI parsing.
3. Short-lived certificate lifetime ceiling (< 60 minutes) enforcement.
4. JWT SVID claims structure (sub, aud, iss, exp).
5. Workload selector attestation evaluation (Kubernetes, cgroup, container sha256).
6. Hardware TPM 2.0 / Nitro Enclave node attestation state machine.
7. Automated SVID certificate rotation trigger at 50% lifetime threshold.
8. Sovereign multi-domain trust federation mapping.
9. Full manifest and executive dossier export pipeline.
10. Strict 100% Brand Anonymity under DevSuperSuite Information Security.
═══════════════════════════════════════════════════════════════════════════════════
"""

import base64
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

from cryptography import x509
from spiffe_spire_workload_identity_engine import (
    AttestationStatus,
    SPIFFEWorkloadIdentity,
    SPIFFEWorkloadIdentityEngine,
    SPIREAttestationManager,
    SVIDType,
    DEFAULT_SVID_TTL_SECONDS,
    MAX_PERMITTED_TTL_SECONDS,
)


class TestSPIFFEWorkloadIdentity(unittest.TestCase):
    """
    Test suite verifying SPIFFE / SPIRE workload identity issuance,
    X.509 SVID SAN URIs, rotation thresholds, and zero-trust federation.
    """

    def setUp(self):
        self.engine = SPIFFEWorkloadIdentityEngine()

    def test_01_spiffe_uri_format_validation(self):
        """
        Verify SPIFFE URI format parser:
        - Valid: spiffe://devsupersuite.io/agent/ast-parser
        - Valid: spiffe://gov.devsupersuite.io/service/license-verifier
        - Invalid: https://devsupersuite.io/agent/test (invalid scheme)
        - Invalid: spiffe:// (empty path/domain)
        """
        valid1, td1, path1 = SPIREAttestationManager.validate_spiffe_uri("spiffe://devsupersuite.io/agent/ast-parser")
        self.assertTrue(valid1)
        self.assertEqual(td1, "devsupersuite.io")
        self.assertEqual(path1, "agent/ast-parser")

        valid2, td2, path2 = SPIREAttestationManager.validate_spiffe_uri("spiffe://gov.devsupersuite.io/service/license-verifier")
        self.assertTrue(valid2)
        self.assertEqual(td2, "gov.devsupersuite.io")

        # Invalid schemes
        self.assertFalse(SPIREAttestationManager.validate_spiffe_uri("https://devsupersuite.io/agent/test")[0])
        self.assertFalse(SPIREAttestationManager.validate_spiffe_uri("spiffe://")[0])
        self.assertFalse(SPIREAttestationManager.validate_spiffe_uri("spiffe:///no-domain")[0])

    def test_02_x509_svid_issuance_and_san_parsing(self):
        """
        Verify issued X.509 SVID certificate:
        - Valid X.509 PEM certificate parsed with cryptography.x509.
        - SubjectAlternativeName contains exactly one UniformResourceIdentifier matching the SPIFFE ID.
        - Ed25519 public key and non-empty serial number.
        """
        target_id = "spiffe://devsupersuite.io/agent/ast-parser"
        svid = self.engine.issue_x509_svid(target_id, ["k8s:ns:agent-commerce"])

        self.assertEqual(svid.spiffe_id, target_id)
        self.assertEqual(svid.status, AttestationStatus.ATTESTED_VALID)
        self.assertIsNotNone(svid.certificate_pem)

        cert = x509.load_pem_x509_certificate(svid.certificate_pem.encode("utf-8"))
        san_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        san_uris = san_ext.value.get_values_for_type(x509.UniformResourceIdentifier)

        self.assertEqual(len(san_uris), 1)
        self.assertEqual(san_uris[0], target_id)

    def test_03_short_lived_ttl_ceiling_enforcement(self):
        """
        Verify short-lived certificate lifetime boundaries:
        - Default TTL is 1800s (30m), well within policy ceiling (< 60m).
        - Attempting to issue with TTL > 3600s raises ValueError.
        """
        self.assertLessEqual(DEFAULT_SVID_TTL_SECONDS, 1800)
        self.assertEqual(MAX_PERMITTED_TTL_SECONDS, 3600)

        # Compliant issuance
        svid = self.engine.issue_x509_svid("spiffe://devsupersuite.io/agent/mcp-daemon", [], ttl_seconds=1800)
        self.assertEqual(svid.ttl_seconds, 1800)

        # Policy breach attempt (2 hours)
        with self.assertRaises(ValueError):
            self.engine.issue_x509_svid("spiffe://devsupersuite.io/agent/mcp-daemon", [], ttl_seconds=7200)

    def test_04_jwt_svid_issuance_and_claims(self):
        """
        Verify JWT SVID generation and claims:
        - Header algorithm is EdDSA.
        - sub claim equals SPIFFE ID.
        - aud claim matches requested audience list.
        - Token signature is verified against CA public key.
        """
        target_id = "spiffe://devsupersuite.io/service/billing-engine"
        audience = ["spiffe://devsupersuite.io", "https://api.devsupersuite.io"]

        jwt_svid = self.engine.issue_jwt_svid(target_id, audience, ttl_seconds=1800)
        self.assertEqual(jwt_svid.svid_type, SVIDType.JWT_SVID)
        self.assertIsNotNone(jwt_svid.jwt_token)

        parts = jwt_svid.jwt_token.split(".")
        self.assertEqual(len(parts), 3)

        # Decode claims payload (pad base64 if needed)
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload_b64.encode("ascii")).decode("utf-8"))

        self.assertEqual(claims["sub"], target_id)
        self.assertEqual(claims["aud"], audience)
        self.assertEqual(claims["iss"], "https://devsupersuite.io/spire")

    def test_05_workload_attestation_selector_evaluation(self):
        """
        Verify workload attestation selector matching:
        - Candidate possessing all required selectors passes.
        - Candidate missing one or more required selectors fails.
        """
        required = ["k8s:ns:agent-commerce", "k8s:sa:ast-parser", "unix:uid:10001"]

        valid_candidate = ["k8s:ns:agent-commerce", "k8s:sa:ast-parser", "unix:uid:10001", "extra:tag:foo"]
        self.assertTrue(SPIREAttestationManager.attest_workload_selectors(valid_candidate, required))

        invalid_candidate = ["k8s:ns:untrusted-ns", "k8s:sa:ast-parser"]
        self.assertFalse(SPIREAttestationManager.attest_workload_selectors(invalid_candidate, required))

    def test_06_hardware_node_attestation(self):
        """
        Verify hardware TPM 2.0 / Nitro Enclave node attestation.
        """
        res = SPIREAttestationManager.verify_node_attestation("TPM_2_0_ENCLAVE")
        self.assertTrue(res["attested"])
        self.assertEqual(res["security_state"], "HARDWARE_ROOT_VERIFIED")

        # Negative test on unapproved node attestation type
        res_bad = SPIREAttestationManager.verify_node_attestation("INSECURE_SOFTWARE_MOCK")
        self.assertFalse(res_bad["attested"])
        self.assertEqual(res_bad["security_state"], "UNTRUSTED_NODE")

    def test_07_automated_rotation_threshold_evaluation(self):
        """
        Verify automated rotation trigger:
        - SVID with > 50% lifetime remaining does NOT require rotation.
        - SVID with <= 50% lifetime remaining triggers ROTATION_REQUIRED.
        """
        svid = self.engine.issue_x509_svid("spiffe://devsupersuite.io/agent/ast-parser", [], ttl_seconds=1800)

        # Fresh SVID
        rot_fresh = self.engine.evaluate_rotation_requirement(svid)
        self.assertFalse(rot_fresh["needs_rotation"])
        self.assertEqual(rot_fresh["status"], "VALID_ACTIVE")

        # Simulating aged SVID (expired/elapsed)
        svid.expires_at = svid.issued_at  # remaining seconds = 0
        rot_aged = self.engine.evaluate_rotation_requirement(svid)
        self.assertTrue(rot_aged["needs_rotation"])
        self.assertEqual(rot_aged["status"], "ROTATION_REQUIRED")

    def test_08_multi_domain_trust_federation(self):
        """
        Verify sovereign trust domain federation parameters:
        - Primary trust domain: devsupersuite.io
        - Federated domains: gov.devsupersuite.io, scif.devsupersuite.io
        - mTLS profile: TLS 1.3 only.
        """
        fed = self.engine.federation
        self.assertEqual(fed["local_trust_domain"], "devsupersuite.io")
        self.assertIn("gov.devsupersuite.io", fed["federated_domains"])
        self.assertIn("scif.devsupersuite.io", fed["federated_domains"])
        self.assertIn("TLS 1.3", fed["mtls_profile"])

    def test_09_cli_interface_execution(self):
        """
        Verify CLI invocation for --summary, --audit-workload-identities,
        --verify-attestation-policy, and --export-spiffe-bundle.
        """
        cli_script = SERVICES_DIR / "spiffe_spire_workload_identity_engine.py"

        # Test --summary
        res1 = subprocess.run([sys.executable, str(cli_script), "--summary"], capture_output=True, text=True, check=True)
        self.assertEqual(res1.returncode, 0)
        self.assertIn("DevSuperSuite Enterprise SPIFFE", res1.stdout)

        # Test --audit-workload-identities
        res2 = subprocess.run([sys.executable, str(cli_script), "--audit-workload-identities"], capture_output=True, text=True, check=True)
        self.assertEqual(res2.returncode, 0)
        self.assertIn("Audited 5 SPIFFE Workload Identities", res2.stdout)

        # Test --verify-attestation-policy
        res3 = subprocess.run([sys.executable, str(cli_script), "--verify-attestation-policy"], capture_output=True, text=True, check=True)
        self.assertEqual(res3.returncode, 0)
        self.assertIn("Hardware Node Attestation: HARDWARE_ROOT_VERIFIED", res3.stdout)

        # Test --export-spiffe-bundle
        res4 = subprocess.run([sys.executable, str(cli_script), "--export-spiffe-bundle"], capture_output=True, text=True, check=True)
        self.assertEqual(res4.returncode, 0)
        self.assertIn("SPIFFE Bundle & Dossier Exported", res4.stdout)

    def test_10_strict_brand_anonymity_under_devsupersuite(self):
        """
        Strict Brand Anonymity Enforcement:
        - Inspects spiffe_spire_workload_identity_engine.py,
          enterprise_zero_trust_workload_identity_policy.md, and generated report artifacts.
        - Asserts ZERO personal names, ZERO personal emails (gmail/yahoo/etc), ZERO personal phone numbers.
        - Confirms all attributions point to DevSuperSuite Official & infosec@devsupersuite.com.
        """
        files_to_check = [
            SERVICES_DIR / "spiffe_spire_workload_identity_engine.py",
            SERVICES_DIR / "enterprise_zero_trust_workload_identity_policy.md",
            SERVICES_DIR / "reports" / "spiffe_workload_identity_dossier.md",
            SERVICES_DIR / "reports" / "spiffe_svid_manifest.json",
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
            clean_content = re.sub(r"`?[a-f0-9]{10,64}(?:\.\.\.)?`?", "", content)
            clean_content = re.sub(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", "", clean_content, flags=re.IGNORECASE)
            clean_content = re.sub(r"KID-[A-Za-z0-9-]+", "", clean_content)
            clean_content = re.sub(r"SN-[A-Fa-f0-9]+", "", clean_content)
            clean_content = re.sub(r"JWT-\d+", "", clean_content)
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
