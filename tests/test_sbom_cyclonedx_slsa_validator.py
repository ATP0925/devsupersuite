"""
═══════════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Software Supply Chain & SLSA Level 3 Test Suite
Document Ref: DSS-TEST-SBOM-SLSA-2026-V1
Compliance Standards: SLSA Level 3, SPDX 2.3, CycloneDX 1.5, OpenVEX 0.2.0

Verifies:
1. CycloneDX 1.5 schema validation & NTIA minimum elements.
2. SPDX 2.3 schema compliance & package relationship hierarchy.
3. OpenVEX 0.2.0 vulnerability exploitability justification taxonomy.
4. SLSA Level 3 in-toto envelope attestation & cryptographic signature.
5. NTIA minimum elements verification across direct/transitive dependencies.
6. Negative tests for malformed CycloneDX and unverified SLSA configurations.
7. Negative tests for invalid OpenVEX statuses and justifications.
8. Artifact export pipeline (JSON manifests, deployment mirrors, Markdown report).
9. CLI commands execution (--summary, --generate-cyclonedx-sbom, --audit-slsa-provenance, etc.).
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

from sbom_cyclonedx_slsa_validator import (
    CycloneDXValidator,
    MasterSBOMValidatorEngine,
    OpenVEXValidator,
    SLSAProvenanceValidator,
    SPDXValidator,
    CORE_SOFTWARE_COMPONENTS,
    OPENVEX_STATEMENTS,
)


class TestSBOMCycloneDXSLSAValidator(unittest.TestCase):
    """
    Test suite verifying CycloneDX 1.5, SPDX 2.3, OpenVEX, and SLSA Level 3 Engine.
    """

    def setUp(self):
        self.engine = MasterSBOMValidatorEngine()

    def test_01_cyclonedx_schema_and_ntia_elements(self):
        """
        Verify CycloneDX 1.5 generation adheres strictly to schema specifications:
        - bomFormat == 'CycloneDX', specVersion == '1.5'
        - Valid URN UUID serial number
        - Mandatory NTIA fields (name, version, purl, sha256 hash) present on all components
        """
        doc = CycloneDXValidator.generate_sbom("agent-commerce", "2.4.0")
        is_valid, errors = CycloneDXValidator.validate_schema(doc)

        self.assertTrue(is_valid, f"CycloneDX validation failed: {errors}")
        self.assertEqual(len(errors), 0)
        self.assertEqual(doc["bomFormat"], "CycloneDX")
        self.assertEqual(doc["specVersion"], "1.5")
        self.assertTrue(doc["serialNumber"].startswith("urn:uuid:"))
        self.assertGreaterEqual(len(doc["components"]), 7)

        for comp in doc["components"]:
            self.assertIn("name", comp)
            self.assertIn("version", comp)
            self.assertTrue(comp["purl"].startswith("pkg:pypi/"))
            self.assertEqual(comp["hashes"][0]["alg"], "SHA-256")
            self.assertEqual(len(comp["hashes"][0]["content"]), 64)

    def test_02_spdx_schema_compliance_and_relationships(self):
        """
        Verify SPDX 2.3 generation complies with ISO/IEC 5962:2021:
        - spdxVersion == 'SPDX-2.3', dataLicense == 'CC0-1.0'
        - Root document describes application
        - Packages have SPDXID, licenses, and SHA-256 checksums
        """
        doc = SPDXValidator.generate_sbom("agent-commerce", "2.4.0")
        is_valid, errors = SPDXValidator.validate_schema(doc)

        self.assertTrue(is_valid, f"SPDX validation failed: {errors}")
        self.assertEqual(len(errors), 0)
        self.assertEqual(doc["spdxVersion"], "SPDX-2.3")
        self.assertEqual(doc["dataLicense"], "CC0-1.0")
        self.assertEqual(doc["SPDXID"], "SPDXRef-DOCUMENT")
        self.assertGreaterEqual(len(doc["packages"]), 8)  # 1 root + 7 dependencies

        # Verify root DESCRIBES relationship
        root_rel = next(r for r in doc["relationships"] if r["relationshipType"] == "DESCRIBES")
        self.assertEqual(root_rel["spdxElementId"], "SPDXRef-DOCUMENT")
        self.assertEqual(root_rel["relatedSpdxElement"], "SPDXRef-Application-Root")

    def test_03_openvex_attestation_and_justifications(self):
        """
        Verify OpenVEX 0.2.0 schema and zero-exploitability justification codes.
        """
        vex_doc = OpenVEXValidator.generate_attestation("agent-commerce", "2.4.0")
        is_valid, errors = OpenVEXValidator.validate_schema(vex_doc)

        self.assertTrue(is_valid, f"OpenVEX validation failed: {errors}")
        self.assertEqual(len(errors), 0)
        self.assertEqual(vex_doc["@context"], "https://openvex.dev/ns/v0.2.0")
        self.assertGreaterEqual(len(vex_doc["statements"]), 3)

        for stmt in vex_doc["statements"]:
            self.assertEqual(stmt["status"], "not_affected")
            self.assertIn(stmt["justification"], [
                "component_not_present",
                "inline_mitigations_exist",
                "vulnerable_code_cannot_be_controlled_by_adversary"
            ])
            self.assertGreater(len(stmt["impact_statement"]), 10)

    def test_04_slsa_level_3_in_toto_envelope_attestation(self):
        """
        Verify SLSA Level 3 provenance builder:
        - Envelope payloadType == 'application/vnd.in-toto+json'
        - Predicate type == 'https://slsa.dev/provenance/v0.2'
        - Hermetic build, ephemeral sandbox, network isolation verified
        - Ed25519 cryptographic signature present
        """
        envelope = SLSAProvenanceValidator.generate_slsa_envelope()
        audit = SLSAProvenanceValidator.audit_slsa_level_3(envelope)

        self.assertEqual(audit["status"], "CERTIFIED_SLSA_LEVEL_3")
        self.assertEqual(audit["slsa_level_achieved"], 3)
        self.assertTrue(all(audit["checks"].values()))

        # Verify envelope structure
        self.assertEqual(envelope["payloadType"], "application/vnd.in-toto+json")
        self.assertIn("signatures", envelope)
        self.assertEqual(len(envelope["signatures"]), 1)
        self.assertEqual(envelope["signatures"][0]["keyid"], "KID-ED25519-DEVSS-SLSA-ROOT-01")

    def test_05_ntia_minimum_elements_catalog_integrity(self):
        """
        Verify that all core components cataloged satisfy the 7 NTIA minimum elements.
        """
        self.assertGreaterEqual(len(CORE_SOFTWARE_COMPONENTS), 7)
        for comp in CORE_SOFTWARE_COMPONENTS:
            self.assertTrue(bool(comp.get("name")))
            self.assertTrue(bool(comp.get("version")))
            self.assertTrue(bool(comp.get("supplier")))
            self.assertTrue(bool(comp.get("license")))
            self.assertTrue(comp.get("purl", "").startswith("pkg:pypi/"))
            self.assertTrue(comp.get("cpe", "").startswith("cpe:2.3:a:"))
            self.assertEqual(len(comp.get("sha256", "")), 64)

    def test_06_negative_malformed_cyclonedx_and_spdx(self):
        """
        Verify negative test: malformed CycloneDX and SPDX documents fail schema validation.
        """
        # Corrupt CycloneDX
        bad_cdx = {"bomFormat": "UnknownFormat", "specVersion": "1.0", "components": []}
        valid_cdx, errors_cdx = CycloneDXValidator.validate_schema(bad_cdx)
        self.assertFalse(valid_cdx)
        self.assertGreater(len(errors_cdx), 0)

        # Corrupt SPDX
        bad_spdx = {"spdxVersion": "SPDX-1.0", "dataLicense": "GPL-3.0", "packages": []}
        valid_spdx, errors_spdx = SPDXValidator.validate_schema(bad_spdx)
        self.assertFalse(valid_spdx)
        self.assertGreater(len(errors_spdx), 0)

    def test_07_negative_invalid_openvex_and_slsa(self):
        """
        Verify negative test: invalid OpenVEX justification and non-hermetic SLSA configuration are rejected.
        """
        # Corrupt OpenVEX
        bad_vex = {
            "@context": "https://openvex.dev/ns/v0.2.0",
            "statements": [
                {
                    "vulnerability": {"name": "CVE-2024-0001"},
                    "products": ["pkg:pypi/test@1.0.0"],
                    "status": "not_affected",
                    "justification": "invalid_unsupported_justification"
                }
            ]
        }
        valid_vex, errors_vex = OpenVEXValidator.validate_schema(bad_vex)
        self.assertFalse(valid_vex)
        self.assertIn("invalid justification", errors_vex[0])

        # Non-hermetic SLSA
        envelope = SLSAProvenanceValidator.generate_slsa_envelope()
        envelope["_decoded_statement"]["predicate"]["buildConfig"]["hermetic_build"] = False
        audit = SLSAProvenanceValidator.audit_slsa_level_3(envelope)
        self.assertEqual(audit["status"], "NON_COMPLIANT")
        self.assertEqual(audit["slsa_level_achieved"], 0)

    def test_08_artifact_export_pipeline(self):
        """
        Verify full export pipeline generates all JSON manifests and executive Markdown dossier.
        """
        paths = self.engine.export_all_files()
        self.assertEqual(len(paths), 5)

        for p in paths:
            self.assertTrue(p.exists(), f"Expected file {p} does not exist")
            self.assertGreater(p.stat().st_size, 0)

        # Check Markdown content
        report_md = paths[4]
        content = report_md.read_text(encoding="utf-8")
        self.assertIn("SLSA LEVEL 3 CERTIFIED", content)
        self.assertIn("CycloneDX 1.5", content)
        self.assertIn("SPDX 2.3", content)
        self.assertIn("OpenVEX", content)
        self.assertIn("infosec@devsupersuite.com", content)

    def test_09_cli_interface_execution(self):
        """
        Verify CLI invocation for --summary, --generate-cyclonedx-sbom, --generate-spdx-sbom,
        --audit-slsa-provenance, and --export-openvex-attestation.
        """
        cli_script = SERVICES_DIR / "sbom_cyclonedx_slsa_validator.py"

        # Test --summary
        res1 = subprocess.run([sys.executable, str(cli_script), "--summary"], capture_output=True, text=True, check=True)
        self.assertEqual(res1.returncode, 0)
        self.assertIn("DevSuperSuite Software Bill of Materials", res1.stdout)

        # Test --generate-cyclonedx-sbom
        res2 = subprocess.run([sys.executable, str(cli_script), "--generate-cyclonedx-sbom"], capture_output=True, text=True, check=True)
        self.assertEqual(res2.returncode, 0)
        self.assertIn("CycloneDX 1.5 SBOM Generated", res2.stdout)

        # Test --generate-spdx-sbom
        res3 = subprocess.run([sys.executable, str(cli_script), "--generate-spdx-sbom"], capture_output=True, text=True, check=True)
        self.assertEqual(res3.returncode, 0)
        self.assertIn("SPDX 2.3 SBOM Generated", res3.stdout)

        # Test --audit-slsa-provenance
        res4 = subprocess.run([sys.executable, str(cli_script), "--audit-slsa-provenance"], capture_output=True, text=True, check=True)
        self.assertEqual(res4.returncode, 0)
        self.assertIn("SLSA Level 3 Provenance Audit: CERTIFIED_SLSA_LEVEL_3", res4.stdout)

        # Test --export-openvex-attestation
        res5 = subprocess.run([sys.executable, str(cli_script), "--export-openvex-attestation"], capture_output=True, text=True, check=True)
        self.assertEqual(res5.returncode, 0)
        self.assertIn("OpenVEX 0.2.0 Attestation Exported", res5.stdout)

    def test_10_strict_brand_anonymity_under_devsupersuite(self):
        """
        Strict Brand Anonymity Enforcement:
        - Inspects sbom_cyclonedx_slsa_validator.py, software_supply_chain_slsa_policy.md,
          and generated report artifacts.
        - Asserts ZERO personal names, ZERO personal emails (gmail/yahoo/etc), ZERO personal phone numbers.
        - Confirms all attributions point to DevSuperSuite Official & infosec@devsupersuite.com.
        """
        files_to_check = [
            SERVICES_DIR / "sbom_cyclonedx_slsa_validator.py",
            SERVICES_DIR / "software_supply_chain_slsa_policy.md",
            SERVICES_DIR / "reports" / "sbom_supply_chain_audit_report.md",
            SERVICES_DIR / "reports" / "sbom_cyclonedx_manifest.json",
            SERVICES_DIR / "reports" / "sbom_spdx_manifest.json",
            SERVICES_DIR / "reports" / "openvex_attestation.json",
            SERVICES_DIR / "reports" / "slsa_provenance_attestation.json",
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
            clean_content = re.sub(r"GHSA-[a-z0-9-]+", "", clean_content)

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
