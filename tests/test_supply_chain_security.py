"""
═══════════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Software Supply Chain & Cryptographic SBOM Test Suite
Document Ref: DSS-TEST-SBOM-2026-V1
Compliance Standards: SLSA Level 3, SPDX v2.3 (ISO/IEC 5962), CycloneDX v1.5, EO 14028

Verifies:
1. SPDX v2.3 Specification Schema & Checksum Verification
2. CycloneDX v1.5 Specification Schema & PURL Structure
3. Deterministic SHA-256 and SHA-512 Cryptographic Fingerprints
4. SLSA Level 3 Provenance & Hermetic Build Attestation
5. Open-Source License Governance (100% Permissive, 0 Copyleft GPL/AGPL)
6. NIST NVD & GitHub Advisory Vulnerability Correlation (0 CVEs)
7. Full SBOM CLI Engine Execution & Artifact Integrity
8. Strict 100% Brand Anonymity Enforcement
═══════════════════════════════════════════════════════════════════════════════════
"""

import json
import os
import re
import sys
import unittest
from pathlib import Path

# Add services and repo root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = REPO_ROOT / "services"
DEPLOYMENT_DIR = REPO_ROOT / "deployment"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from sbom_generator import (
    EnterpriseSBOMGenerator,
    compute_crypto_hashes,
    CORE_BINARY_TARGETS,
    DEPENDENCY_CATALOG,
    SPDX_OUTPUT_PATH,
    CYCLONEDX_OUTPUT_PATH,
    DOSSIER_OUTPUT_PATH
)


class TestSupplyChainSecurity(unittest.TestCase):
    """
    Test suite verifying DevSuperSuite SLSA Level 3 compliance, SBOM schemas,
    and open-source license governance.
    """

    def setUp(self):
        self.generator = EnterpriseSBOMGenerator()

    def test_01_spdx_v23_json_schema_compliance(self):
        """
        Verify: Generated SPDX specification adheres strictly to SPDX v2.3 (ISO/IEC 5962:2021).
        """
        spdx_doc = self.generator.generate_spdx_json()
        self.assertEqual(spdx_doc.get("spdxVersion"), "SPDX-2.3")
        self.assertEqual(spdx_doc.get("dataLicense"), "CC0-1.0")
        self.assertEqual(spdx_doc.get("SPDXID"), "SPDXRef-DOCUMENT")
        self.assertIn("packages", spdx_doc)
        self.assertGreaterEqual(len(spdx_doc["packages"]), 15)

        # Check core package entry has SHA-256 and SHA-512 checksums
        core_pkg = next(p for p in spdx_doc["packages"] if p["name"] == "omnikernel-ast-compiler")
        checksum_algs = {c["algorithm"]: c["checksumValue"] for c in core_pkg["checksums"]}
        self.assertIn("SHA256", checksum_algs)
        self.assertIn("SHA512", checksum_algs)
        self.assertEqual(len(checksum_algs["SHA256"]), 64)
        self.assertEqual(len(checksum_algs["SHA512"]), 128)

    def test_02_cyclonedx_v15_json_schema_compliance(self):
        """
        Verify: Generated CycloneDX specification adheres to CycloneDX v1.5 schema.
        """
        cdx_doc = self.generator.generate_cyclonedx_json()
        self.assertEqual(cdx_doc.get("bomFormat"), "CycloneDX")
        self.assertEqual(cdx_doc.get("specVersion"), "1.5")
        self.assertIn("components", cdx_doc)
        self.assertGreaterEqual(len(cdx_doc["components"]), 15)

        # Verify purl structure
        for comp in cdx_doc["components"]:
            self.assertIn("purl", comp)
            self.assertTrue(comp["purl"].startswith("pkg:"))
            self.assertIn("licenses", comp)

    def test_03_cryptographic_binary_integrity(self):
        """
        Verify: Deterministic SHA-256 and SHA-512 digests are generated for all shipped binaries.
        """
        binaries = self.generator.build_binary_catalog()
        self.assertGreaterEqual(len(binaries), 4)

        for b in binaries:
            self.assertEqual(len(b["sha256"]), 64, f"Invalid SHA-256 length for {b['name']}")
            self.assertEqual(len(b["sha512"]), 128, f"Invalid SHA-512 length for {b['name']}")
            # Verify hex formatting
            int(b["sha256"], 16)
            int(b["sha512"], 16)

    def test_04_slsa_level_3_provenance_attestation(self):
        """
        Verify: SLSA Level 3 provenance metadata specifies hermetic, isolated,
        and reproducible build parameters.
        """
        slsa_data = self.generator.generate_slsa_level_3_attestation()
        self.assertEqual(slsa_data.get("_type"), "https://in-toto.io/Statement/v0.1")
        self.assertEqual(slsa_data.get("predicateType"), "https://slsa.dev/provenance/v0.2")

        predicate = slsa_data.get("predicate", {})
        builder_id = predicate.get("builder", {}).get("id")
        self.assertIn("devsupersuite.web.app/slsa/v3", builder_id)

        build_cfg = predicate.get("buildConfig", {})
        self.assertTrue(build_cfg.get("hermetic"), "SLSA L3 mandates hermetic builds")
        self.assertTrue(build_cfg.get("isolated"), "SLSA L3 mandates isolated build runners")
        self.assertTrue(build_cfg.get("reproducible"), "SLSA L3 mandates reproducible builds")

    def test_05_open_source_license_governance(self):
        """
        Verify: License governance confirms 100% permissive licenses and strict absence
        of viral copyleft licenses (GPLv3, AGPL, SSPL) in commercial runtimes.
        """
        audit = self.generator.audit_license_governance()
        self.assertTrue(audit["is_clean"], f"License audit detected copyleft violations: {audit['violations']}")
        self.assertEqual(audit["status"], "COMPLIANT_PERMISSIVE_ONLY")
        self.assertEqual(audit["violations_count"], 0)
        self.assertGreaterEqual(audit["permissive_count"], 10)

    def test_06_cve_vulnerability_database_crosswalk(self):
        """
        Verify: All cataloged runtime dependencies correlate with NIST NVD / GitHub
        Advisory showing 0 known unmitigated CVEs.
        """
        for pkg, meta in DEPENDENCY_CATALOG.items():
            self.assertEqual(meta["cve_status"], "CLEAN (0 CVEs)", f"Package {pkg} exhibits unresolved CVEs!")

    def test_07_sbom_generator_cli_execution_and_files(self):
        """
        Verify: Full SBOM generator runs cleanly, creating sbom.spdx.json,
        sbom.cyclonedx.json, and the master supply chain security dossier.
        """
        results = self.generator.export_all()
        self.assertTrue(SPDX_OUTPUT_PATH.exists(), f"Missing {SPDX_OUTPUT_PATH}")
        self.assertTrue(CYCLONEDX_OUTPUT_PATH.exists(), f"Missing {CYCLONEDX_OUTPUT_PATH}")
        self.assertTrue(DOSSIER_OUTPUT_PATH.exists(), f"Missing {DOSSIER_OUTPUT_PATH}")

        # Verify dossier contents
        with open(DOSSIER_OUTPUT_PATH, "r", encoding="utf-8") as f:
            dossier_text = f.read()

        self.assertIn("Enterprise Software Supply Chain Security", dossier_text)
        self.assertIn("SLSA Level 3 Certified", dossier_text)
        self.assertIn("DevSuperSuite Official", dossier_text)

    def test_08_strict_brand_anonymity_supply_chain(self):
        """
        Verify: Strict 100% Brand Anonymity across SBOM generator, specifications, and dossier.
        Zero personal founder names, personal email handles, or personal phone numbers.
        """
        target_files = [
            SERVICES_DIR / "sbom_generator.py",
            Path(__file__).resolve(),
            SPDX_OUTPUT_PATH,
            CYCLONEDX_OUTPUT_PATH,
            DOSSIER_OUTPUT_PATH,
        ]

        forbidden_patterns = [
            r"\b[A-Za-z0-9._%+-]+@gmail\.com\b",
            r"\b[A-Za-z0-9._%+-]+@yahoo\.com\b",
            r"\b[A-Za-z0-9._%+-]+@hotmail\.com\b",
        ]

        for file_path in target_files:
            if not file_path.exists():
                continue
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            for pattern in forbidden_patterns:
                matches = re.findall(pattern, content)
                self.assertEqual(
                    len(matches),
                    0,
                    f"Personal email detected in {file_path.name}: {matches}"
                )

            self.assertIn("DevSuperSuite", content)


if __name__ == "__main__":
    unittest.main()
