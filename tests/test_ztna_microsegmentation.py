#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Automated Verification Suite: ZTNA & eBPF Microsegmentation
Reference: DSS-TEST-ZTNA-EBPF-2026-V1
Target: Continuous Verification of Zero-Trust Network Architecture, SPIFFE & Cilium eBPF
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
CILIUM_DIR = DEPLOYMENT_DIR / "cilium"
TESTS_DIR = REPO_ROOT / "tests"

sys.path.insert(0, str(SERVICES_DIR))

from ztna_microsegmentation_engine import (
    SPIFFEWorkloadIdentity,
    MicrosegmentationNamespaceBoundary,
    CiliumNetworkPolicyGenerator,
    ZTNAMicrosegmentationEngine,
    run_ztna_pipeline,
    ZTNA_MD_PATH,
    ZTNA_JSON_PATH,
)


class TestZTNAMicrosegmentation(unittest.TestCase):
    """
    Continuous regression test suite validating Zero-Trust network architecture (ZTNA),
    SPIFFE/SPIRE workload identity attestation, Cilium eBPF policies, and lateral blast radius.
    """

    def setUp(self) -> None:
        self.engine = ZTNAMicrosegmentationEngine(repo_root=REPO_ROOT)

    def test_01_spiffe_workload_identity_attestation(self) -> None:
        """
        Verifies dynamic SPIFFE/SPIRE X.509 SVID credential issuance across all 5 workload tiers.
        """
        res = self.engine.verify_spiffe_workload_attestation()

        self.assertEqual(res["overall_status"], "PASS")
        self.assertEqual(res["trust_domain"], "devsupersuite.internal")
        self.assertEqual(res["total_workloads_attested"], 5)
        self.assertEqual(res["valid_attestation_count"], 5)

        for w in res["workload_attestations"]:
            self.assertTrue(w["spiffe_id"].startswith("spiffe://devsupersuite.internal/ns/"))
            self.assertEqual(w["status"], "VERIFIED_VALID")
            self.assertEqual(len(w["cert_fingerprint"]), 64)

    def test_02_spiffe_svid_validation_rules(self) -> None:
        """
        Validates that malformed, expired, or foreign trust domain SVIDs are rejected.
        """
        ident = SPIFFEWorkloadIdentity("test-ns", "test-sa", "Test Workload")
        valid_svid = ident.issue_x509_svid()
        self.assertTrue(ident.verify_svid(valid_svid))

        # Foreign trust domain
        bad_domain = valid_svid.copy()
        bad_domain["spiffe_id"] = "spiffe://rogue-domain.internal/ns/test/sa/test"
        self.assertFalse(ident.verify_svid(bad_domain))

        # Expired TTL
        expired_svid = valid_svid.copy()
        expired_svid["ttl_seconds"] = 0
        self.assertFalse(ident.verify_svid(expired_svid))

        # Invalid State
        invalid_state = valid_svid.copy()
        invalid_state["state"] = "REVOKED"
        self.assertFalse(ident.verify_svid(invalid_state))

    def test_03_lateral_movement_blast_radius_evaluation(self) -> None:
        """
        Verifies that lateral movement from compute workers to financial/license stores
        is strictly blocked, while legitimate mTLS flows are permitted.
        """
        # Legitimate flows
        f_ingress = MicrosegmentationNamespaceBoundary.evaluate_traffic_flow("ingress-gateway", "omnikernel-compute")
        self.assertTrue(f_ingress["allowed"])
        self.assertEqual(f_ingress["verdict"], "ALLOWED_MUTUAL_TLS_FLOW")

        f_compute_to_mesh = MicrosegmentationNamespaceBoundary.evaluate_traffic_flow("omnikernel-compute", "mcp-service-mesh")
        self.assertTrue(f_compute_to_mesh["allowed"])

        # Adversarial lateral movement blocked
        f_pivot_billing = MicrosegmentationNamespaceBoundary.evaluate_traffic_flow("omnikernel-compute", "billing-reconciliation")
        self.assertFalse(f_pivot_billing["allowed"])
        self.assertEqual(f_pivot_billing["verdict"], "BLOCKED_BY_LATERAL_SEGMENTATION")

        f_pivot_license = MicrosegmentationNamespaceBoundary.evaluate_traffic_flow("omnikernel-compute", "licensing-auth")
        self.assertFalse(f_pivot_license["allowed"])
        self.assertEqual(f_pivot_license["verdict"], "BLOCKED_BY_LATERAL_SEGMENTATION")

        # Zero-egress WAN drop
        f_wan = MicrosegmentationNamespaceBoundary.evaluate_traffic_flow("omnikernel-compute", "internet-wan")
        self.assertFalse(f_wan["allowed"])
        self.assertEqual(f_wan["verdict"], "BLOCKED_BY_ZERO_EGRESS_AIRGAP")

    def test_04_blast_radius_containment_audit(self) -> None:
        """
        Simulates adversarial lateral movement attempts across all namespace permutations
        and asserts >= 80.0% containment rate.
        """
        audit = MicrosegmentationNamespaceBoundary.audit_blast_radius_containment()

        self.assertEqual(audit["status"], "PASS")
        self.assertGreaterEqual(audit["blast_radius_containment_percentage"], 80.0)
        self.assertEqual(audit["airgap_wan_egress_drop"], "100.0% BLOCKED")
        self.assertGreater(audit["unauthorized_flows_blocked"], 0)

    def test_05_cilium_ebpf_policy_generation_and_validity(self) -> None:
        """
        Validates generation of Cilium eBPF L3/L4/L7 NetworkPolicy manifests on disk.
        """
        files = CiliumNetworkPolicyGenerator.export_all_cilium_policies(output_dir=CILIUM_DIR)
        self.assertEqual(len(files), 3)

        expected_names = [
            "cilium-omnikernel-policy.yaml",
            "cilium-licensing-policy.yaml",
            "cilium-billing-policy.yaml",
        ]

        for p_name in expected_names:
            p_path = CILIUM_DIR / p_name
            self.assertTrue(p_path.exists())
            with open(p_path, "r", encoding="utf-8") as f:
                c = f.read()
            self.assertIn("apiVersion: \"cilium.io/v2\"", c)
            self.assertIn("kind: CiliumNetworkPolicy", c)
            self.assertIn("enableDefaultDeny:", c)

    def test_06_ztna_posture_audit_end_to_end(self) -> None:
        """
        Audits end-to-end Zero-Trust posture across SPIFFE, blast radius, and network enforcement.
        """
        audit = self.engine.audit_ztna_posture()

        self.assertEqual(audit["overall_status"], "CERTIFIED_ZTNA_COMPLIANT")
        self.assertEqual(audit["spiffe_spire_attestation"]["overall_status"], "PASS")
        self.assertEqual(audit["lateral_movement_blast_radius"]["status"], "PASS")
        self.assertEqual(audit["infrastructure_enforcement"]["kubernetes_default_deny_networkpolicy"], "PASS")
        self.assertEqual(audit["infrastructure_enforcement"]["docker_internal_zero_egress_bridge"], "PASS")

    def test_07_ztna_report_and_json_artifacts(self) -> None:
        """
        Validates generation of executive Markdown report and machine-readable JSON.
        """
        md_path = self.engine.generate_markdown_report()
        json_path = self.engine.export_ztna_json()

        self.assertTrue(md_path.exists())
        self.assertTrue(json_path.exists())

        with open(md_path, "r", encoding="utf-8") as f:
            md_text = f.read()

        self.assertIn("Zero-Trust Network Architecture (ZTNA)", md_text)
        self.assertIn("flowchart TD", md_text)
        self.assertIn("OFFICIAL ZERO-TRUST NETWORK ARCHITECTURE & eBPF ATTESTATION SEAL", md_text)

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["metadata"]["organization"], "DevSuperSuite Official")
        self.assertIn("sha256_digest", data["metadata"])
        self.assertEqual(len(data["metadata"]["sha256_digest"]), 64)
        self.assertEqual(data["ztna_executive_summary"]["posture_status"], "CERTIFIED_ZTNA_COMPLIANT")

    def test_08_cli_flags_execution(self) -> None:
        """
        Validates CLI execution pipeline across all flags with exit code 0.
        """
        ret_audit = run_ztna_pipeline(audit_posture=True, summary=False, repo_root=REPO_ROOT)
        self.assertEqual(ret_audit, 0)

        ret_cilium = run_ztna_pipeline(generate_cilium=True, summary=False, repo_root=REPO_ROOT)
        self.assertEqual(ret_cilium, 0)

        ret_spiffe = run_ztna_pipeline(verify_spiffe=True, summary=False, repo_root=REPO_ROOT)
        self.assertEqual(ret_spiffe, 0)

    def test_09_strict_brand_anonymity_under_infosec_devsupersuite(self) -> None:
        """
        Enforces 100% Brand Anonymity under DevSuperSuite Information Security (infosec@devsupersuite.com).
        Zero personal founder names, personal handles, personal emails, or phone numbers.
        """
        files_to_check = [
            SERVICES_DIR / "ztna_microsegmentation_engine.py",
            ZTNA_MD_PATH,
            ZTNA_JSON_PATH,
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

                # Exclude cryptographic hex digests and serial numbers to avoid false positives on digit runs
                cleaned_content = re.sub(r"[a-f0-9]{32,64}", "", content, flags=re.IGNORECASE)

                for pattern in forbidden_patterns:
                    matches = list(re.finditer(pattern, cleaned_content, re.IGNORECASE))
                    self.assertEqual(len(matches), 0, f"Found forbidden personal pattern in {filepath.name}: {matches}")


if __name__ == "__main__":
    unittest.main()

