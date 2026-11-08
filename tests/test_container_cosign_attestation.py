#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Automated Verification Suite: Container Cosign Attestation
Reference: DSS-TEST-CONTAINER-COSIGN-2026-V1
Target: Continuous Verification of Container Vulnerability Scanning, Cosign & Admission
Contact: DevSuperSuite Information Security (infosec@devsupersuite.com)
Author: Directorate of QA Automation & Security Compliance, DevSuperSuite Official
═══════════════════════════════════════════════════════════════════════════════════
"""

import json
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = REPO_ROOT / "services"
REPORTS_DIR = SERVICES_DIR / "reports"
DEPLOYMENT_DIR = REPO_ROOT / "deployment"
KYVERNO_DIR = DEPLOYMENT_DIR / "kyverno"
TESTS_DIR = REPO_ROOT / "tests"

sys.path.insert(0, str(SERVICES_DIR))

from container_cosign_attestation_engine import (
    ContainerVulnerabilityScanner,
    SigstoreCosignEngine,
    KubernetesAdmissionController,
    ContainerCosignAttestationEngine,
    run_container_security_pipeline,
    COSIGN_MD_PATH,
    COSIGN_JSON_PATH,
    KYVERNO_POLICY_PATH,
)


class TestContainerCosignAttestation(unittest.TestCase):
    """
    Continuous regression test suite validating container vulnerability scanning,
    Sigstore Cosign keyless digital signatures, SLSA provenance, and Kyverno admission controls.
    """

    def setUp(self) -> None:
        self.engine = ContainerCosignAttestationEngine(repo_root=REPO_ROOT)

    def test_01_container_vulnerability_scanning(self) -> None:
        """
        Verifies that all container images pass static vulnerability scanning
        with zero Critical and zero High CVEs.
        """
        scan_data = ContainerVulnerabilityScanner.scan_all_images()

        self.assertEqual(scan_data["overall_status"], "PASS")
        self.assertEqual(scan_data["critical_vulnerabilities"], 0)
        self.assertEqual(scan_data["high_vulnerabilities"], 0)
        self.assertEqual(scan_data["total_images_scanned"], 3)
        self.assertEqual(scan_data["images_approved"], 3)

        for res in scan_data["scan_results"]:
            self.assertEqual(res["critical"], 0)
            self.assertEqual(res["high"], 0)
            self.assertEqual(res["admission_verdict"], "APPROVED")

    def test_02_sigstore_cosign_attestation_bundle_generation(self) -> None:
        """
        Validates generation of Sigstore Cosign keyless signatures and SLSA v0.2 provenance.
        """
        bundle = SigstoreCosignEngine.generate_cosign_attestation(
            image_repository="devsupersuite/omnikernel-airgap",
            image_digest="sha256:d5a7b8c19e42f0a1e3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3e5f7a9b1c3d5e7f9",
        )

        self.assertEqual(bundle["status"], "SIGNED_AND_ATTESTED")
        self.assertEqual(bundle["fulcio_certificate"]["issuer"], SigstoreCosignEngine.COSIGN_ROOT_ISSUER)
        self.assertEqual(len(bundle["cosign_signature"]), 64)
        self.assertGreater(bundle["rekor_transparency_log"]["logIndex"], 0)
        self.assertEqual(bundle["slsa_provenance"]["predicateType"], "https://slsa.dev/provenance/v0.2")

    def test_03_sigstore_cosign_verification_logic(self) -> None:
        """
        Validates that verify_cosign_signature accepts valid bundles and rejects tampered ones.
        """
        valid_bundle = SigstoreCosignEngine.generate_cosign_attestation(
            image_repository="devsupersuite/mcp-server",
            image_digest="sha256:a1b2c3d4e5f60718293a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e",
        )
        self.assertTrue(SigstoreCosignEngine.verify_cosign_signature(valid_bundle))

        # Tampered issuer
        bad_issuer = valid_bundle.copy()
        bad_issuer["fulcio_certificate"] = {"issuer": "https://untrusted-issuer.com"}
        self.assertFalse(SigstoreCosignEngine.verify_cosign_signature(bad_issuer))

        # Invalid status
        bad_status = valid_bundle.copy()
        bad_status["status"] = "REVOKED"
        self.assertFalse(SigstoreCosignEngine.verify_cosign_signature(bad_status))

    def test_04_kubernetes_admission_controller_acceptance(self) -> None:
        """
        Evaluates admission for a compliant signed image and confirms admission verdict.
        """
        image_ref = "devsupersuite/omnikernel-airgap:v5.2.0@sha256:d5a7b8c19e42f0a1e3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3e5f7a9b1c3d5e7f9"
        bundle = SigstoreCosignEngine.generate_cosign_attestation("devsupersuite/omnikernel-airgap", "sha256:d5a7b8c19e42f0a1e3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3e5f7a9b1c3d5e7f9")
        scan_report = {"critical": 0, "high": 0}

        res = KubernetesAdmissionController.evaluate_image_admission(image_ref, bundle, scan_report)
        self.assertTrue(res["admitted"])
        self.assertEqual(res["decision"], "ADMITTED_TO_CLUSTER")
        self.assertEqual(res["violations_count"], 0)

    def test_05_kubernetes_admission_controller_rejection_unsigned(self) -> None:
        """
        Evaluates admission for an unsigned image and confirms rejection with KUBERNETES_IMAGE_ADMISSION_DENIED.
        """
        unsigned_ref = "devsupersuite/omnikernel-airgap:v5.2.0@sha256:d5a7b8c19e42f0a1e3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3e5f7a9b1c3d5e7f9"
        res = KubernetesAdmissionController.evaluate_image_admission(unsigned_ref, cosign_bundle=None, scan_report={"critical": 0, "high": 0})

        self.assertFalse(res["admitted"])
        self.assertEqual(res["decision"], KubernetesAdmissionController.ADMISSION_DENIED_ERROR)
        self.assertGreater(res["violations_count"], 0)

    def test_06_kubernetes_admission_controller_rejection_mutable_tag(self) -> None:
        """
        Evaluates admission for an image with mutable tag (e.g. :latest) and confirms rejection.
        """
        mutable_ref = "devsupersuite/omnikernel-airgap:latest"
        res = KubernetesAdmissionController.evaluate_image_admission(mutable_ref, cosign_bundle=None, scan_report={"critical": 0, "high": 0})

        self.assertFalse(res["admitted"])
        self.assertEqual(res["decision"], KubernetesAdmissionController.ADMISSION_DENIED_ERROR)
        self.assertTrue(any("mutable tag" in v.lower() for v in res["violations"]))

    def test_07_kyverno_cluster_policy_manifest(self) -> None:
        """
        Validates export and syntax of the Kyverno ClusterPolicy manifest.
        """
        policy_path = KubernetesAdmissionController.export_kyverno_policy(output_path=KYVERNO_POLICY_PATH)
        self.assertTrue(policy_path.exists())

        with open(policy_path, "r", encoding="utf-8") as f:
            c = f.read()

        self.assertIn("apiVersion: kyverno.io/v1", c)
        self.assertIn("kind: ClusterPolicy", c)
        self.assertIn("validationFailureAction: Enforce", c)
        self.assertIn("verifyImages:", c)
        self.assertIn("https://devsupersuite.com/workload-identity", c)

    def test_08_container_security_report_artifacts(self) -> None:
        """
        Validates generation of the executive Markdown report and machine-readable JSON.
        """
        md_path = self.engine.generate_markdown_report()
        json_path = self.engine.export_attestation_json()

        self.assertTrue(md_path.exists())
        self.assertTrue(json_path.exists())

        with open(md_path, "r", encoding="utf-8") as f:
            md_text = f.read()

        self.assertIn("DevSuperSuite Container Security & Sigstore Cosign Attestation Report", md_text)
        self.assertIn("Container Vulnerability Scanning Matrix", md_text)
        self.assertIn("Kyverno Admission Controller Rule Enforcement", md_text)
        self.assertIn("OFFICIAL CONTAINER IMAGE SECURITY & COSIGN ATTESTATION SEAL", md_text)

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["metadata"]["organization"], "DevSuperSuite Official")
        self.assertIn("sha256_digest", data["metadata"])
        self.assertEqual(len(data["metadata"]["sha256_digest"]), 64)
        self.assertEqual(data["container_security_summary"]["overall_status"], "CERTIFIED_CONTAINER_SECURITY_COMPLIANT")

    def test_09_cli_flags_execution(self) -> None:
        """
        Validates CLI execution across all flags with exit code 0.
        """
        ret_scan = run_container_security_pipeline(scan_images=True, summary=False, repo_root=REPO_ROOT)
        self.assertEqual(ret_scan, 0)

        ret_sign = run_container_security_pipeline(sign_attestation=True, summary=False, repo_root=REPO_ROOT)
        self.assertEqual(ret_sign, 0)

        ret_audit = run_container_security_pipeline(audit_admission=True, summary=False, repo_root=REPO_ROOT)
        self.assertEqual(ret_audit, 0)

    def test_10_strict_brand_anonymity_under_infosec_devsupersuite(self) -> None:
        """
        Enforces 100% Brand Anonymity under DevSuperSuite Information Security (infosec@devsupersuite.com).
        Zero personal founder names, personal handles, personal emails, or phone numbers.
        """
        files_to_check = [
            SERVICES_DIR / "container_cosign_attestation_engine.py",
            COSIGN_MD_PATH,
            COSIGN_JSON_PATH,
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

                # Exclude cryptographic hex digests and digests to avoid false positives on digit runs
                cleaned_content = re.sub(r"[a-f0-9]{32,64}", "", content, flags=re.IGNORECASE)

                for pattern in forbidden_patterns:
                    matches = list(re.finditer(pattern, cleaned_content, re.IGNORECASE))
                    self.assertEqual(len(matches), 0, f"Found forbidden personal pattern in {filepath.name}: {matches}")


if __name__ == "__main__":
    unittest.main()
