"""
═══════════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - SOC 2 Type II Evidence Collector Test Suite
Document Ref: DSS-TEST-SOC2-COLLECTOR-2026-V1
Compliance Standards: AICPA SOC 2 Type II (Trust Services Criteria), ISO 27001:2022

Verifies:
1. Evidence collection coverage across Security, Availability, Confidentiality,
   Processing Integrity, and Common Criteria principles.
2. Granular Trust Services Criteria validation (CC6.1, CC6.3, A1.2, C1.1, CC8.1).
3. Cryptographic SHA-256 hash binding on all evidence records.
4. Observation window freshness verification (< 24h daily threshold).
5. Vanta / Drata / Secureframe normalized JSON schema export.
6. Auditor Zip bundle generation with structured directories & evidence_manifest.json.
7. Executive Markdown audit dossier generation.
8. Negative test on missing or simulated files ensuring graceful fallback.
9. CLI commands execution (--summary, --collect-soc2-evidence, etc.).
10. Strict 100% Brand Anonymity under DevSuperSuite Information Security.
═══════════════════════════════════════════════════════════════════════════════════
"""

import json
import os
import re
import subprocess
import sys
import unittest
import zipfile
from pathlib import Path

# Add services and repo root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = REPO_ROOT / "services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from automated_soc2_evidence_collector import (
    EvidenceArtifact,
    SOC2EvidenceCollector,
    TSCPrinciple,
    MAX_FRESHNESS_HOURS_DAILY,
)


class TestSOC2EvidenceCollector(unittest.TestCase):
    """
    Test suite verifying continuous SOC 2 Type II evidence collection,
    cryptographic digest binding, freshness audits, and Big-4 exporter formats.
    """

    def setUp(self):
        self.collector = SOC2EvidenceCollector()

    def test_01_evidence_collection_coverage(self):
        """
        Verify collection covers all key Trust Services Criteria principles:
        - Security (CC6)
        - Availability (A1)
        - Confidentiality (C1)
        - Processing Integrity (PI1, CC8)
        - Common Criteria (CC2, CC3, CC7)
        """
        artifacts = self.collector.collect_all_evidence()
        self.assertGreaterEqual(len(artifacts), 15)

        principles = {a.tsc_principle for a in artifacts}
        self.assertIn(TSCPrinciple.SECURITY, principles)
        self.assertIn(TSCPrinciple.AVAILABILITY, principles)
        self.assertIn(TSCPrinciple.CONFIDENTIALITY, principles)
        self.assertIn(TSCPrinciple.PROCESSING_INTEGRITY, principles)
        self.assertIn(TSCPrinciple.COMMON_CRITERIA, principles)

        for a in artifacts:
            self.assertEqual(a.status, "COMPLIANT_VERIFIED")
            self.assertTrue(len(a.criterion_id) >= 4)
            self.assertTrue(len(a.title) > 5)

    def test_02_granular_tsc_criteria_presence(self):
        """
        Verify core foundational SOC 2 criteria are evaluated:
        - CC6.1 (FIPS 140-3 cryptography & TLS 1.3)
        - CC6.3 (Zero-Trust & Cilium eBPF)
        - A1.2 (Disaster Recovery RPO/RTO)
        - C1.1 (Memory Zeroization)
        - CC8.1 (SLSA Level 3 Provenance)
        """
        artifacts = self.collector.collect_all_evidence()
        criteria_map = {a.criterion_id: a for a in artifacts}

        self.assertIn("CC6.1", criteria_map)
        self.assertIn("CC6.3", criteria_map)
        self.assertIn("A1.2", criteria_map)
        self.assertIn("C1.1", criteria_map)
        self.assertIn("CC8.1", criteria_map)

        cc61 = criteria_map["CC6.1"]
        self.assertIn("FIPS", cc61.title)
        self.assertEqual(cc61.verification_metadata.get("fips_status"), "PASS")

        a12 = criteria_map["A1.2"]
        self.assertIn("RPO/RTO", a12.title)
        self.assertLessEqual(a12.verification_metadata.get("measured_rpo_ms"), 1000.0)

    def test_03_cryptographic_sha256_hash_binding(self):
        """
        Verify every evidence record has an immutable 64-hex SHA-256 cryptographic binding.
        """
        artifacts = self.collector.collect_all_evidence()
        sha256_regex = re.compile(r"^[a-f0-9]{64}$")

        for a in artifacts:
            self.assertTrue(
                bool(sha256_regex.match(a.evidence_sha256)),
                f"Invalid SHA-256 digest on {a.criterion_id}: {a.evidence_sha256}"
            )

    def test_04_observation_window_freshness_audit(self):
        """
        Verify observation window freshness audit:
        - Validates that newly collected evidence is fresh (< 24h).
        - Simulates stale evidence and verifies freshness warning detection.
        """
        freshness = self.collector.audit_evidence_freshness()
        self.assertEqual(freshness["status"], "PASS")
        self.assertTrue(freshness["all_evidence_fresh"])
        self.assertEqual(freshness["stale_count"], 0)

        # Negative test: inject simulated stale record (48h old)
        stale_artifact = EvidenceArtifact(
            criterion_id="CC9.9",
            tsc_principle=TSCPrinciple.COMMON_CRITERIA,
            title="Simulated Stale Artifact",
            description="Testing freshness ceiling",
            source_artifact_path="services/reports/simulated_stale.json",
            evidence_sha256="0" * 64,
            collected_at="2026-01-01T00:00:00Z",
            status="COMPLIANT_VERIFIED",
            verification_metadata={},
            freshness_hours=48.0
        )
        self.collector.collected_artifacts.append(stale_artifact)

        stale_audit = self.collector.audit_evidence_freshness()
        self.assertEqual(stale_audit["status"], "FRESHNESS_WARNING")
        self.assertFalse(stale_audit["all_evidence_fresh"])
        self.assertIn("CC9.9", stale_audit["stale_artifacts"])

        # Clean up injected artifact
        self.collector.collected_artifacts.pop()

    def test_05_vanta_drata_normalized_json_export(self):
        """
        Verify JSON export format matches Big-4 portal standards:
        - Schema version, organization, contact, 12-month lookback window.
        - Unqualified clean opinion.
        """
        json_path = self.collector.export_evidence_json()
        self.assertTrue(json_path.exists())

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("vanta.drata.secureframe", data["schema_version"])
        self.assertEqual(data["organization"], "DevSuperSuite Tech Services")
        self.assertEqual(data["contact"], "DevSuperSuite Information Security (infosec@devsupersuite.com)")
        self.assertEqual(data["trust_services_criteria_coverage"]["overall_opinion"], "UNQUALIFIED_CLEAN_OPINION")
        self.assertGreaterEqual(len(data["evidence_inventory"]), 15)

    def test_06_auditor_zip_bundle_structure_and_manifest(self):
        """
        Verify auditor Zip bundle generation:
        - Zip file exists and is valid.
        - Contains structured subdirectories (/evidence/security/, /evidence/availability/, etc.).
        - Contains evidence_manifest.json with SHA-256 digests.
        """
        zip_path = self.collector.export_auditor_zip_bundle()
        self.assertTrue(zip_path.exists())
        self.assertGreater(zip_path.stat().st_size, 1000)

        with zipfile.ZipFile(zip_path, "r") as zf:
            file_names = zf.namelist()
            self.assertIn("evidence_manifest.json", file_names)

            # Check for subdirectories
            has_security = any("evidence/security/" in f for f in file_names)
            has_availability = any("evidence/availability/" in f for f in file_names)
            self.assertTrue(has_security, "Missing evidence/security/ in zip bundle")
            self.assertTrue(has_availability, "Missing evidence/availability/ in zip bundle")

            # Check manifest contents
            manifest_data = json.loads(zf.read("evidence_manifest.json").decode("utf-8"))
            self.assertEqual(manifest_data["audit_entity"], "DevSuperSuite Tech Services")
            self.assertIn("manifest_entries", manifest_data)
            self.assertGreaterEqual(len(manifest_data["manifest_entries"]), 15)

    def test_07_executive_markdown_report_generation(self):
        """
        Verify executive Markdown report generation:
        - Contains document reference, clean opinion, criteria table.
        - Official contact infosec@devsupersuite.com.
        """
        md_path = self.collector.export_evidence_markdown()
        self.assertTrue(md_path.exists())

        content = md_path.read_text(encoding="utf-8")
        self.assertIn("SOC 2 Type II Continuous Evidence Report", content)
        self.assertIn("UNQUALIFIED CLEAN OPINION", content)
        self.assertIn("Trust Services Criteria (TSC) Evidence Ledger", content)
        self.assertIn("infosec@devsupersuite.com", content)

    def test_08_missing_file_graceful_handling(self):
        """
        Negative test: ensure collector handles nonexistent source files gracefully
        without raising uncaught exceptions, utilizing deterministic fallback hashes.
        """
        fake_path = REPO_ROOT / "services" / "reports" / "nonexistent_evidence_file.json"
        h, age = self.collector.get_file_metadata_and_hash(fake_path)

        self.assertEqual(len(h), 64)
        self.assertGreater(age, 0.0)

    def test_09_cli_interface_execution(self):
        """
        Verify CLI invocation for --summary, --collect-soc2-evidence,
        --audit-evidence-freshness, and --export-auditor-zip-bundle.
        """
        cli_script = SERVICES_DIR / "automated_soc2_evidence_collector.py"

        # Test --summary
        res1 = subprocess.run([sys.executable, str(cli_script), "--summary"], capture_output=True, text=True, check=True)
        self.assertEqual(res1.returncode, 0)
        self.assertIn("DevSuperSuite SOC 2 Type II Continuous Evidence", res1.stdout)

        # Test --collect-soc2-evidence
        res2 = subprocess.run([sys.executable, str(cli_script), "--collect-soc2-evidence"], capture_output=True, text=True, check=True)
        self.assertEqual(res2.returncode, 0)
        self.assertIn("Collected 15 SOC 2 Type II Evidence Artifacts", res2.stdout)

        # Test --audit-evidence-freshness
        res3 = subprocess.run([sys.executable, str(cli_script), "--audit-evidence-freshness"], capture_output=True, text=True, check=True)
        self.assertEqual(res3.returncode, 0)
        self.assertIn("Evidence Freshness Audit: PASS", res3.stdout)

        # Test --export-auditor-zip-bundle
        res4 = subprocess.run([sys.executable, str(cli_script), "--export-auditor-zip-bundle"], capture_output=True, text=True, check=True)
        self.assertEqual(res4.returncode, 0)
        self.assertIn("Auditor Zip Bundle Exported Successfully", res4.stdout)

    def test_10_strict_brand_anonymity_under_devsupersuite(self):
        """
        Strict Brand Anonymity Enforcement:
        - Inspects automated_soc2_evidence_collector.py, continuous_compliance_monitoring_policy.md,
          and generated report artifacts.
        - Asserts ZERO personal names, ZERO personal emails (gmail/yahoo/etc), ZERO personal phone numbers.
        - Confirms all attributions point to DevSuperSuite Official & infosec@devsupersuite.com.
        """
        files_to_check = [
            SERVICES_DIR / "automated_soc2_evidence_collector.py",
            SERVICES_DIR / "continuous_compliance_monitoring_policy.md",
            SERVICES_DIR / "reports" / "soc2_type2_continuous_evidence_report.md",
            SERVICES_DIR / "reports" / "soc2_type2_continuous_evidence.json",
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
