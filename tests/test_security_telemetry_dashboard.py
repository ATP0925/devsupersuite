#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Automated Verification Suite: Security Telemetry Dashboard
Reference: DSS-TEST-SEC-TELEMETRY-2026-V1
Target: Continuous Verification of DevSecOps Security Telemetry & Trust Index Engine
Author: Directorate of QA Automation & Security Compliance, DevSuperSuite Official
═══════════════════════════════════════════════════════════════════════════════════
"""

import json
import math
import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = REPO_ROOT / "services"
REPORTS_DIR = SERVICES_DIR / "reports"
DEPLOYMENT_DIR = REPO_ROOT / "deployment"
TESTS_DIR = REPO_ROOT / "tests"

sys.path.insert(0, str(SERVICES_DIR))

from security_telemetry_dashboard import (
    TestTelemetryCollector,
    SecretScreeningTelemetry,
    AirgapIsolationTelemetry,
    FuzzingAndResilienceTelemetry,
    SupplyChainTelemetry,
    ComplianceEvidenceTelemetry,
    EnterpriseTrustIndexEngine,
    run_telemetry_pipeline,
    DASHBOARD_MD_PATH,
    DASHBOARD_JSON_PATH,
)


class TestSecurityTelemetryDashboard(unittest.TestCase):
    """
    Automated verification of the DevSecOps Real-Time Security Telemetry Dashboard
    and the quantitative Enterprise Trust Index (ETI) Engine.
    """

    def setUp(self) -> None:
        self.engine = EnterpriseTrustIndexEngine(repo_root=REPO_ROOT)

    def test_01_test_telemetry_collector_ingestion(self) -> None:
        """
        Verifies test telemetry collector scans >= 13 test suites and >= 104 tests
        with a 100.0% pass rate.
        """
        collector = TestTelemetryCollector(tests_dir=TESTS_DIR)
        metrics = collector.collect_test_suite_metrics()

        self.assertGreaterEqual(metrics["total_suites"], 13, "Must scan at least 13 test suites")
        self.assertGreaterEqual(metrics["total_tests"], 104, "Must collect at least 104 unit/integration tests")
        self.assertEqual(metrics["pass_rate_percentage"], 100.0)
        self.assertEqual(metrics["fail_count"], 0)
        self.assertEqual(metrics["skipped_count"], 0)

        # Verify suite breakdown contains core suites
        modules = [item["module"] for item in metrics["suite_breakdown"]]
        self.assertIn("test_airgap_deployment.py", modules)
        self.assertIn("test_compliance_audit_engine.py", modules)
        self.assertIn("test_enterprise_compliance.py", modules)
        self.assertIn("test_security_fuzzing.py", modules)
        self.assertIn("test_supply_chain_security.py", modules)

    def test_02_secret_screening_entropy_mathematics(self) -> None:
        """
        Verifies Shannon entropy detection and pre-commit secret screening tripwire metrics.
        """
        telemetry = SecretScreeningTelemetry()
        metrics = telemetry.evaluate_screening_metrics()

        self.assertEqual(metrics["entropy_threshold"], 4.5)
        self.assertEqual(metrics["interception_rate_percentage"], 100.0)
        self.assertEqual(metrics["false_positive_rate_percentage"], 0.0)
        self.assertEqual(metrics["status"], "PASS")

        # Direct mathematical verification of Shannon entropy
        h_low = telemetry.calculate_entropy("hello world")
        h_high = telemetry.calculate_entropy("dummy_high_entropy_secret_token_9x8b7c6v5a4z3y2w1q")
        self.assertLess(h_low, 3.5, "Natural language string must have low entropy")
        self.assertGreater(h_high, 4.5, "High-entropy API key must have entropy > 4.5")

    def test_03_airgap_network_isolation_telemetry(self) -> None:
        """
        Verifies air-gapped zero-egress network policies across Docker and Kubernetes manifests.
        """
        airgap = AirgapIsolationTelemetry(deployment_dir=DEPLOYMENT_DIR)
        posture = airgap.evaluate_isolation_posture()

        self.assertEqual(posture["docker_internal_network"], "PASS")
        self.assertEqual(posture["read_only_root_filesystem"], "PASS")
        self.assertEqual(posture["non_root_uid_10001"], "PASS")
        self.assertEqual(posture["cap_drop_all"], "PASS")
        self.assertEqual(posture["k8s_egress_drop_policy"], "PASS")
        self.assertEqual(posture["isolation_score_percentage"], 100.0)
        self.assertFalse(posture["wan_egress_allowed"])
        self.assertEqual(posture["status"], "PASS")

    def test_04_fuzzing_and_redos_resilience_telemetry(self) -> None:
        """
        Verifies parser fuzzing, AST recursion depth safeguards, and ReDoS immunity (< 1.0ms).
        """
        resilience = FuzzingAndResilienceTelemetry()
        metrics = resilience.evaluate_resilience()

        self.assertLess(metrics["redos_execution_time_ms"], 1.0, "Regex evaluation must complete in < 1.0ms")
        self.assertEqual(metrics["redos_immunity"], "PASS")
        self.assertEqual(metrics["ast_max_recursion_depth"], 30)
        self.assertEqual(metrics["ast_recursion_bomb_protection"], "PASS")
        self.assertEqual(metrics["resilience_score_percentage"], 100.0)
        self.assertEqual(metrics["status"], "PASS")

    def test_05_supply_chain_and_sbom_integrity_telemetry(self) -> None:
        """
        Verifies SLSA Level 3 provenance, SPDX v2.3 / CycloneDX v1.5 SBOM presence, and zero CVEs.
        """
        supply = SupplyChainTelemetry(deployment_dir=DEPLOYMENT_DIR)
        metrics = supply.evaluate_supply_chain()

        self.assertTrue(metrics["spdx_v23_present"], "SPDX v2.3 SBOM must be present")
        self.assertTrue(metrics["cyclonedx_v15_present"], "CycloneDX v1.5 SBOM must be present")
        self.assertGreater(metrics["tracked_dependency_packages"], 0)
        self.assertEqual(metrics["known_cve_count"], 0)
        self.assertEqual(metrics["copyleft_license_risks"], 0)
        self.assertEqual(metrics["supply_chain_score_percentage"], 100.0)
        self.assertEqual(metrics["status"], "PASS")

    def test_06_compliance_readiness_telemetry(self) -> None:
        """
        Verifies SOC 2 Type II and ISO 27001 readiness posture and SHA-256 sealed evidence binder.
        """
        comp = ComplianceEvidenceTelemetry(reports_dir=REPORTS_DIR)
        metrics = comp.evaluate_compliance_readiness()

        self.assertEqual(metrics["soc2_type2_readiness_percentage"], 100.0)
        self.assertEqual(metrics["iso27001_readiness_percentage"], 100.0)
        self.assertTrue(metrics["evidence_binder_present"])
        self.assertTrue(metrics["cryptographic_seal_verified"])
        self.assertEqual(metrics["compliance_score_percentage"], 100.0)
        self.assertEqual(metrics["status"], "PASS")

    def test_07_enterprise_trust_index_quantitative_benchmark(self) -> None:
        """
        Computes the Enterprise Trust Index and asserts ETI >= 99.5 (Target: Tier-1 Sovereign Grade).
        """
        payload = self.engine.aggregate_full_telemetry()
        eti = payload["enterprise_trust_index"]

        self.assertGreaterEqual(eti["composite_score"], 99.5, "Enterprise Trust Index must be >= 99.5")
        self.assertEqual(eti["status"], "CERTIFIED_PASS")
        self.assertIn("Tier-1 Sovereign", eti["tier_classification"])
        self.assertIn("sha256_digest", payload["metadata"])
        self.assertEqual(len(payload["metadata"]["sha256_digest"]), 64)

    def test_08_cli_execution_and_report_artifacts(self) -> None:
        """
        Tests the CLI pipeline execution and verifies generated Markdown and JSON reports.
        """
        ret = run_telemetry_pipeline(
            generate_dashboard=True,
            verify_telemetry=True,
            export_json=True,
            summary=False,
            repo_root=REPO_ROOT,
        )
        self.assertEqual(ret, 0, "CLI execution pipeline must return 0")

        # Verify disk artifacts
        self.assertTrue(DASHBOARD_MD_PATH.exists(), f"Missing {DASHBOARD_MD_PATH}")
        self.assertTrue(DASHBOARD_JSON_PATH.exists(), f"Missing {DASHBOARD_JSON_PATH}")

        # Validate Markdown content
        with open(DASHBOARD_MD_PATH, "r", encoding="utf-8") as f:
            md_text = f.read()
        self.assertIn("DevSuperSuite DevSecOps Real-Time Security Telemetry", md_text)
        self.assertIn("Enterprise Trust Index (ETI)", md_text)
        self.assertIn("OFFICIAL SEAL OF DEVSEC-OPS ATTESTATION", md_text)

        # Validate JSON content
        with open(DASHBOARD_JSON_PATH, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        self.assertEqual(json_data["metadata"]["organization"], "DevSuperSuite Official")
        self.assertGreaterEqual(json_data["enterprise_trust_index"]["composite_score"], 99.5)

    def test_09_strict_brand_anonymity_enforcement(self) -> None:
        """
        Enforces 100% Brand Anonymity across dashboard code, generated reports, and JSON payloads.
        Strictly attributed to DevSuperSuite Official. Zero personal identity leaks.
        """
        files_to_check = [
            SERVICES_DIR / "security_telemetry_dashboard.py",
            DASHBOARD_MD_PATH,
            DASHBOARD_JSON_PATH,
        ]

        forbidden_patterns = [
            r"\b[A-Za-z0-9._%+-]+@(?:gmail|yahoo|hotmail|outlook)\.com\b",
            r"(?<![a-f0-9])\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?![a-f0-9])",
            r"github\.com\/(?!DevSuperSuiteOfficial)[a-zA-Z0-9_\-]+",
        ]

        for filepath in files_to_check:
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                # Must contain DevSuperSuite Official
                self.assertIn("DevSuperSuite", content, f"Must reference DevSuperSuite in {filepath.name}")

                for pattern in forbidden_patterns:
                    matches = list(re.finditer(pattern, content, re.IGNORECASE))
                    self.assertEqual(len(matches), 0, f"Found forbidden personal pattern in {filepath.name}: {matches}")


if __name__ == "__main__":
    unittest.main()
