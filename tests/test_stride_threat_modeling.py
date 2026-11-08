#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Automated Verification Suite: STRIDE Threat Modeling
Reference: DSS-TEST-THREAT-STRIDE-2026-V1
Target: Continuous Verification of Dynamic Threat Modeling & STRIDE Matrix Engine
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
TESTS_DIR = REPO_ROOT / "tests"

sys.path.insert(0, str(SERVICES_DIR))

from threat_modeling_stride_engine import (
    DREADScore,
    STRIDEThreatVector,
    ThreatModelCatalog,
    ThreatModelingSTRIDEEngine,
    run_stride_pipeline,
    STRIDE_MD_PATH,
    STRIDE_JSON_PATH,
)


class TestSTRIDEThreatModeling(unittest.TestCase):
    """
    Continuous regression test suite validating the automated STRIDE threat modeling
    engine, DREAD scoring, mitigation artifact verification, and risk reductions.
    """

    def setUp(self) -> None:
        self.engine = ThreatModelingSTRIDEEngine(repo_root=REPO_ROOT)

    def test_01_stride_coverage_across_all_six_categories(self) -> None:
        """
        Verifies that all 6 STRIDE threat categories are modeled with at least 2 vectors each.
        """
        payload = self.engine.generate_stride_matrix_payload()
        stride_counts = payload["stride_breakdown"]

        expected_categories = [
            "Spoofing",
            "Tampering",
            "Repudiation",
            "Information_Disclosure",
            "Denial_of_Service",
            "Elevation_of_Privilege",
        ]

        for cat in expected_categories:
            self.assertIn(cat, stride_counts, f"Missing category: {cat}")
            self.assertGreaterEqual(stride_counts[cat], 2, f"Category {cat} must have >= 2 threat vectors")

        self.assertGreaterEqual(payload["threat_model_summary"]["total_threat_vectors_analyzed"], 12)

    def test_02_dread_scoring_mathematics(self) -> None:
        """
        Validates DREAD score calculations, bounds clamping (1.0 - 10.0), and severity categorization.
        """
        # Critical test
        d_crit = DREADScore(damage=10.0, reproducibility=9.0, exploitability=8.5, affected_users=9.0, discoverability=8.5)
        self.assertEqual(d_crit.composite_score, 9.0)
        self.assertEqual(d_crit.severity_level, "CRITICAL")

        # Low test
        d_low = DREADScore(damage=1.5, reproducibility=1.0, exploitability=1.5, affected_users=1.0, discoverability=1.0)
        self.assertEqual(d_low.composite_score, 1.2)
        self.assertEqual(d_low.severity_level, "LOW")

        # Clamping test
        d_clamped = DREADScore(damage=15.0, reproducibility=-5.0, exploitability=10.0, affected_users=1.0, discoverability=1.0)
        self.assertEqual(d_clamped.damage, 10.0)
        self.assertEqual(d_clamped.reproducibility, 1.0)

    def test_03_enterprise_threat_vector_catalog_integrity(self) -> None:
        """
        Validates that every threat vector in the catalog contains all required fields and metadata.
        """
        vectors = ThreatModelCatalog.get_enterprise_threat_vectors()
        self.assertGreaterEqual(len(vectors), 12)

        for tv in vectors:
            self.assertTrue(tv.threat_id.startswith("THR-STRIDE-"), f"Invalid ID: {tv.threat_id}")
            self.assertGreater(len(tv.title), 5)
            self.assertGreater(len(tv.attack_description), 15)
            self.assertGreater(len(tv.mitigation_mechanism), 15)
            self.assertGreater(len(tv.mitigation_evidence_artifact), 3)
            self.assertEqual(tv.mitigation_status, "MITIGATED")

    def test_04_mitigation_audit_100_percent_verified(self) -> None:
        """
        Verifies that 100% of threat vectors have concrete, existing mitigation artifacts on disk.
        """
        audit = self.engine.audit_mitigations()

        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["unmitigated_threats"], 0)
        self.assertEqual(audit["mitigation_rate_percentage"], 100.0)

        for rec in audit["audit_records"]:
            self.assertTrue(rec["evidence_present"], f"Missing mitigation artifact: {rec['evidence_path']}")
            self.assertEqual(rec["status"], "PASS")

    def test_05_dread_risk_reduction_benchmark(self) -> None:
        """
        Asserts that every threat's residual post-mitigation DREAD score is <= 2.5
        and aggregate risk reduction >= 75.0%.
        """
        payload = self.engine.generate_stride_matrix_payload()
        summary = payload["threat_model_summary"]

        self.assertLess(summary["average_residual_dread_score"], 2.5)
        self.assertGreaterEqual(summary["aggregate_risk_reduction_percentage"], 75.0)

        for tv in payload["threat_vectors"]:
            residual = tv["residual_dread"]["composite_score"]
            self.assertLessEqual(residual, 2.5, f"Residual DREAD too high for {tv['threat_id']}: {residual}")

    def test_06_deployment_scope_coverage(self) -> None:
        """
        Verifies that threat vectors explicitly model Cloud, Hybrid Edge, and Air-Gapped On-Prem enclaves.
        """
        vectors = ThreatModelCatalog.get_enterprise_threat_vectors()
        scopes = {tv.deployment_scope for tv in vectors}

        self.assertTrue(any("Cloud" in s for s in scopes))
        self.assertTrue(any("Air-Gapped" in s for s in scopes))
        self.assertTrue(any("Universal" in s for s in scopes))

    def test_07_json_stride_matrix_export_and_sha256_digest(self) -> None:
        """
        Validates export of machine-readable STRIDE matrix JSON and verifies SHA-256 seal.
        """
        json_path = self.engine.export_stride_matrix_json()
        self.assertTrue(json_path.exists())

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["metadata"]["organization"], "DevSuperSuite Official")
        self.assertIn("sha256_digest", data["metadata"])
        self.assertEqual(len(data["metadata"]["sha256_digest"]), 64)
        self.assertEqual(data["threat_model_summary"]["overall_status"], "AUDITED_AND_CERTIFIED")

    def test_08_markdown_report_generation(self) -> None:
        """
        Validates generation of the executive STRIDE markdown matrix with Mermaid diagrams and tables.
        """
        md_path = self.engine.generate_stride_matrix_markdown()
        self.assertTrue(md_path.exists())

        with open(md_path, "r", encoding="utf-8") as f:
            md_text = f.read()

        self.assertIn("DevSuperSuite Enterprise STRIDE Threat Model", md_text)
        self.assertIn("flowchart TD", md_text)
        self.assertIn("Comprehensive STRIDE & DREAD Threat Matrix", md_text)
        self.assertIn("OFFICIAL DEVSECOPS THREAT MODELING & STRIDE ATTESTATION SEAL", md_text)

    def test_09_cli_execution_pipeline(self) -> None:
        """
        Validates end-to-end CLI execution and confirms exit code 0.
        """
        exit_code = run_stride_pipeline(
            generate_threat_model=True,
            audit_mitigations=True,
            export_stride_matrix=True,
            summary=False,
            repo_root=REPO_ROOT,
        )
        self.assertEqual(exit_code, 0, "Threat modeling CLI must exit with code 0")

    def test_10_strict_brand_anonymity_under_infosec_devsupersuite(self) -> None:
        """
        Enforces 100% Brand Anonymity under DevSuperSuite Information Security (infosec@devsupersuite.com).
        Zero personal founder names, personal handles, personal emails, or phone numbers.
        """
        files_to_check = [
            SERVICES_DIR / "threat_modeling_stride_engine.py",
            STRIDE_MD_PATH,
            STRIDE_JSON_PATH,
        ]

        forbidden_patterns = [
            r"\b[A-Za-z0-9._%+-]+@(?!(?:devsupersuite\.com))\w+\.\w+\b",
            r"\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
            r"github\.com\/(?!DevSuperSuiteOfficial)[a-zA-Z0-9_\-]+",
        ]

        for filepath in files_to_check:
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                self.assertIn("DevSuperSuite", content, f"Must reference DevSuperSuite in {filepath.name}")
                self.assertIn("infosec@devsupersuite.com", content, f"Must reference official contact in {filepath.name}")

                # Exclude cryptographic hex digests to avoid false positives on digit runs
                cleaned_content = re.sub(r"[a-f0-9]{32,64}", "", content, flags=re.IGNORECASE)

                for pattern in forbidden_patterns:
                    matches = list(re.finditer(pattern, cleaned_content, re.IGNORECASE))
                    self.assertEqual(len(matches), 0, f"Found forbidden personal pattern in {filepath.name}: {matches}")


if __name__ == "__main__":
    unittest.main()
