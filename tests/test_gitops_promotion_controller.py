#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - GitOps Promotion Controller Test Suite
Reference: DSS-GITOPS-PROMOTION-TESTS-2026-V1
Classification: Automated Quality Gate & Invariant Validation (Restricted)
Contact: DevSuperSuite Solutions Architecture (solutions@devsupersuite.com)
Author: OmniKernel Labs / DevSuperSuite Quality Assurance & Test Engineering
═══════════════════════════════════════════════════════════════════════════════
"""

import copy
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = REPO_ROOT / "services"
REPORTS_DIR = SERVICES_DIR / "reports"
DEPLOYMENT_DIR = REPO_ROOT / "deployment"
GITOPS_DIR = DEPLOYMENT_DIR / "gitops"

if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from enterprise_gitops_promotion_controller import (
    ORGANIZATION_NAME,
    PRIMARY_CONTACT,
    GITOPS_CONTACT,
    REFERENCE_CODE,
    MAX_ROLLBACK_LATENCY_SECONDS,
    COSIGN_OIDC_ISSUER,
    COSIGN_PUBKEY_FINGERPRINT,
    ENVIRONMENTS_PROGRESSION,
    SLSAGateVerificationError,
    SLSAGateVerifier,
    OpticalDataDiodeStager,
    CanaryRollbackEngine,
    EnterpriseGitOpsPromotionController
)


class TestEnterpriseGitOpsPromotionController:
    """Enterprise verification suite for GitOps Continuous Verification & Promotion Controller."""

    def test_pipeline_environments_initialization(self):
        """Validate 4-stage promotion progression (Dev -> Staging -> Prod -> Airgap SCIF) and golden states."""
        controller = EnterpriseGitOpsPromotionController()
        expected_stages = ["DEV", "STAGING", "PROD", "AIRGAP_SCIF"]
        assert ENVIRONMENTS_PROGRESSION == expected_stages

        # Verify golden states are pre-seeded for all environments
        for env in expected_stages:
            golden = controller.rollback_engine.get_golden_state(env)
            assert golden is not None
            assert golden["version"] == "v2.4.0"
            assert "sha256:" in golden["digest"]

    def test_slsa_reproducible_digest_verification(self):
        """Verify SLSA Level 3 bit-for-bit reproducible binary hash check."""
        digest_a = "sha256:7mP4kX8qW2vL9zR1tN3yE6uI0oA5sD8fG2hJ1kL4xM="
        digest_b = "sha256:7mP4kX8qW2vL9zR1tN3yE6uI0oA5sD8fG2hJ1kL4xM="
        digest_tampered = "sha256:00000000000000000000000000000000000000000000"

        ok, msg = SLSAGateVerifier.verify_reproducible_digest(digest_a, digest_b)
        assert ok is True
        assert "bit-for-bit reproducible" in msg.lower()

        fail_ok, fail_msg = SLSAGateVerifier.verify_reproducible_digest(digest_a, digest_tampered)
        assert fail_ok is False
        assert "failure" in fail_msg.lower()

    def test_cosign_attestation_verification(self):
        """Verify Cosign container attestation, OIDC issuer, and key fingerprint."""
        valid_attestation = {
            "issuer": COSIGN_OIDC_ISSUER,
            "status": "VERIFIED",
            "fingerprint": COSIGN_PUBKEY_FINGERPRINT
        }
        ok, msg = SLSAGateVerifier.verify_cosign_signature("devsupersuite/app:v1", valid_attestation)
        assert ok is True
        assert "verified" in msg.lower()

        # Untrusted issuer
        invalid_issuer = copy.deepcopy(valid_attestation)
        invalid_issuer["issuer"] = "https://untrusted-token-issuer.com"
        fail_ok, fail_msg = SLSAGateVerifier.verify_cosign_signature("devsupersuite/app:v1", invalid_issuer)
        assert fail_ok is False
        assert "untrusted" in fail_msg.lower()

    def test_cyclonedx_sbom_vulnerability_gating(self):
        """Verify SBOM gate blocks Critical/High CVEs and permits clean/low-risk packages."""
        # Clean SBOM
        clean_sbom = {"vulnerabilities": [{"severity": "LOW"}, {"severity": "MEDIUM"}]}
        ok, msg, counts = SLSAGateVerifier.verify_cyclonedx_sbom(clean_sbom)
        assert ok is True
        assert counts["CRITICAL"] == 0
        assert counts["HIGH"] == 0

        # Vulnerable SBOM with Critical CVE
        crit_sbom = {"vulnerabilities": [{"severity": "CRITICAL"}]}
        fail_crit, msg_crit, counts_crit = SLSAGateVerifier.verify_cyclonedx_sbom(crit_sbom)
        assert fail_crit is False
        assert counts_crit["CRITICAL"] == 1
        assert "blocked" in msg_crit.lower()

        # Vulnerable SBOM with High CVE
        high_sbom = {"vulnerabilities": [{"severity": "HIGH"}]}
        fail_high, msg_high, counts_high = SLSAGateVerifier.verify_cyclonedx_sbom(high_sbom)
        assert fail_high is False
        assert counts_high["HIGH"] == 1

    def test_successful_release_promotion_progression(self):
        """Test complete promotion of verified artifact to PROD."""
        controller = EnterpriseGitOpsPromotionController()
        digest = "sha256:7mP4kX8qW2vL9zR1tN3yE6uI0oA5sD8fG2hJ1kL4xM="
        cosign_sample = {"issuer": COSIGN_OIDC_ISSUER, "status": "VERIFIED", "fingerprint": COSIGN_PUBKEY_FINGERPRINT}
        clean_sbom = {"vulnerabilities": []}

        res = controller.promote_release(
            release_id="REL-2026-V1",
            version="v2.5.0",
            target_env="PROD",
            artifact_digest=digest,
            reproducible_digest=digest,
            cosign_attestation=cosign_sample,
            sbom_data=clean_sbom
        )

        assert res["status"] == "PROMOTED_SUCCESS"
        assert res["canary_health_verified"] is True
        assert res["rollback_event"] is None

        # Verify golden state updated
        golden = controller.rollback_engine.get_golden_state("PROD")
        assert golden["release_id"] == "REL-2026-V1"
        assert golden["version"] == "v2.5.0"

    def test_promotion_failure_on_gate_rejection(self):
        """Verify pipeline halts and raises SLSAGateVerificationError when gates fail."""
        controller = EnterpriseGitOpsPromotionController()
        digest = "sha256:valid-digest"
        tampered = "sha256:tampered-digest"
        cosign = {"issuer": COSIGN_OIDC_ISSUER, "status": "VERIFIED", "fingerprint": COSIGN_PUBKEY_FINGERPRINT}
        clean_sbom = {"vulnerabilities": []}

        # Gate 1 Failure: Hash mismatch
        with pytest.raises(SLSAGateVerificationError, match="SLSA L3 Reproducibility"):
            controller.promote_release("REL-F1", "v1", "STAGING", digest, tampered, cosign, clean_sbom)

        # Gate 3 Failure: Critical CVE in SBOM
        vuln_sbom = {"vulnerabilities": [{"severity": "CRITICAL"}]}
        with pytest.raises(SLSAGateVerificationError, match="SBOM Vulnerability Scan"):
            controller.promote_release("REL-F2", "v1", "STAGING", digest, digest, cosign, vuln_sbom)

    def test_optical_data_diode_bundle_staging_and_verification(self):
        """Validate optical data-diode bundle packaging, SHA-256 manifest, and Ed25519 signature."""
        stager = OpticalDataDiodeStager()
        payloads = {
            "image.tar": "binary-container-layer-001",
            "chart.tgz": "helm-chart-values-prod",
            "parsers.bin": "ast-tree-sitter-grammars"
        }

        bundle = stager.stage_airgap_bundle("REL-SCIF-01", "v2.5.0", payloads)
        assert "DIODE-REL-SCIF-01" in bundle["bundle_id"]
        assert len(bundle["manifest_sha256"]) == 64
        assert len(bundle["detached_signature_hex"]) == 64
        assert len(bundle["packaged_components"]) == 3

        # Verify destination receipt
        ok, msg = stager.verify_airgap_bundle(bundle)
        assert ok is True
        assert "verified" in msg.lower()

    def test_optical_data_diode_tampering_detection(self):
        """Verify destination-side check detects payload bit corruption across the optical diode."""
        stager = OpticalDataDiodeStager()
        payloads = {"component.bin": "original-unmodified-content"}
        bundle = stager.stage_airgap_bundle("REL-CORRUPT", "v1", payloads)

        # Corrupt payload
        bundle["raw_payloads"]["component.bin"] = "corrupted-bit-flip-content"
        ok, msg = stager.verify_airgap_bundle(bundle)
        assert ok is False
        assert "corruption" in msg.lower() or "mismatch" in msg.lower()

    def test_canary_health_anomaly_detection(self):
        """Validate canary SLO thresholds for error rate, latency, and crash loops."""
        engine = CanaryRollbackEngine()

        # Healthy
        ok, _ = engine.evaluate_canary_health({"error_rate_percentage": 0.01, "p99_latency_ms": 120.0})
        assert ok is True

        # Error rate violation (> 0.05%)
        fail_err, reason_err = engine.evaluate_canary_health({"error_rate_percentage": 0.12})
        assert fail_err is False
        assert "Error rate" in reason_err

        # Latency violation (> 200ms)
        fail_lat, reason_lat = engine.evaluate_canary_health({"p99_latency_ms": 320.0})
        assert fail_lat is False
        assert "p99 latency" in reason_lat

        # CrashLoop violation (> 0 pods)
        fail_crash, reason_crash = engine.evaluate_canary_health({"crash_loop_pod_count": 2})
        assert fail_crash is False
        assert "CrashLoopBackOff" in reason_crash

    def test_sub_3_second_automated_rollback(self):
        """Verify automated rollback to previous golden state executes in <= 3.0 seconds."""
        engine = CanaryRollbackEngine()
        engine.record_golden_state("PROD", "REL-GOLDEN-OLD", "v2.0.0", "sha256:old-digest")

        rb = engine.execute_automated_rollback("PROD", "Canary error rate spike")
        assert rb["action"] == "ROLLBACK_SUCCESSFUL"
        assert rb["restored_release_id"] == "REL-GOLDEN-OLD"
        assert rb["restored_version"] == "v2.0.0"
        assert rb["rollback_duration_seconds"] <= MAX_ROLLBACK_LATENCY_SECONDS
        assert rb["sub_3s_sla_met"] is True

    def test_pipeline_manifest_export_and_json_validity(self, tmp_path):
        """Verify declarative pipeline manifest export and valid JSON schema."""
        controller = EnterpriseGitOpsPromotionController()
        target_file = tmp_path / "promotion_pipeline_manifest.json"
        controller.export_pipeline_manifest(target_file)

        assert target_file.exists()
        with open(target_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["metadata"]["organization"] == ORGANIZATION_NAME
        assert manifest["metadata"]["contact"] == PRIMARY_CONTACT
        assert manifest["slsa_level_3_gates"]["cosign_attestation"]["oidc_issuer"] == COSIGN_OIDC_ISSUER
        assert manifest["optical_data_diode_configuration"]["detached_signature_algorithm"] == "Ed25519-Detached-Signature"
        assert manifest["canary_and_rollback_policy"]["max_rollback_latency_seconds"] == 3.0

    def test_architecture_report_generation(self, tmp_path):
        """Verify whitepaper generation and technical report content completeness."""
        controller = EnterpriseGitOpsPromotionController()
        report_file = tmp_path / "gitops_airgap_promotion_report.md"
        controller.export_architecture_report(report_file)

        assert report_file.exists()
        content = report_file.read_text(encoding="utf-8")
        assert "GitOps Continuous Verification & Air-Gap Promotion Architecture" in content
        assert "SLSA Level 3" in content
        assert "Cosign" in content
        assert "CycloneDX" in content
        assert "Optical Data-Diode" in content
        assert "solutions@devsupersuite.com" in content

    def test_brand_anonymity_invariants(self):
        """
        Enforce strict institutional brand anonymity:
        Must NOT contain personal names or unauthorized personal email domains.
        Must strictly represent DevSuperSuite Solutions Architecture / OmniKernel Labs.
        """
        forbidden_terms = ["github.com/", "gitlab.com/", "@gmail.com", "@yahoo.com", "@hotmail.com"]
        files_to_check = [
            SERVICES_DIR / "enterprise_gitops_promotion_controller.py",
            GITOPS_DIR / "promotion_pipeline_manifest.json",
            REPORTS_DIR / "gitops_airgap_promotion_report.md"
        ]

        for filepath in files_to_check:
            assert filepath.exists(), f"Expected file {filepath} to exist."
            content = filepath.read_text(encoding="utf-8")

            for term in forbidden_terms:
                assert term not in content.lower(), f"Forbidden term '{term}' found in {filepath.name}"

            assert "DevSuperSuite" in content or "OmniKernel Labs" in content, (
                f"Missing institutional brand in {filepath.name}"
            )
            assert "solutions@devsupersuite.com" in content, (
                f"Missing official contact in {filepath.name}"
            )

    def test_cli_flags_execution(self):
        """Ensure all CLI interface flags execute cleanly with exit code 0."""
        python_exe = sys.executable
        script = str(SERVICES_DIR / "enterprise_gitops_promotion_controller.py")

        commands = [
            [python_exe, script, "--summary"],
            [python_exe, script, "--verify-slsa-gate"],
            [python_exe, script, "--stage-optical-diode-bundle", "REL-TEST-01"],
            [python_exe, script, "--simulate-canary-rollback", "REL-TEST-01"],
            [python_exe, script, "--export-promotion-bundle"]
        ]

        for cmd in commands:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            assert res.returncode == 0, f"Command failed: {' '.join(cmd)}\nStderr: {res.stderr}"
            assert len(res.stdout) > 0
