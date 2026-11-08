"""
═══════════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - FedRAMP High & DoD IL4/IL5 SSP Test Suite
Document Ref: DSS-TEST-FEDRAMP-DOD-2026-V1
Compliance Standards: NIST SP 800-53 Rev. 5, FedRAMP High, DoD CC SRG (IL4/IL5),
                      NIST OSCAL v1.1.0 JSON Schema

Verifies:
1. NIST SP 800-53 Rev 5 control family completeness (AC, AU, CM, IA, MP, SC, SI, CP, SR).
2. FedRAMP High baseline compliance & FIPS 199 High-Water Mark categorization.
3. DoD CC SRG Impact Level 5 (IL5) technical invariant validation.
4. NIST OSCAL v1.1.0 JSON schema validity & component implementation hierarchy.
5. Parameter validation on mission-critical security controls.
6. Executive Markdown System Security Plan dossier generation.
7. Negative tests for non-compliant control injection.
8. Machine-readable manifest export integrity.
9. CLI commands execution (--summary, --audit-fedramp-high, --verify-dod-il5-readiness, etc.).
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

from fedramp_high_dod_il5_ssp_engine import (
    ControlFamily,
    FedRAMPHighDoDIL5SSPEngine,
    NISTControlImplementation,
    SecurityControlStatus,
    FEDRAMP_DOD_CONTROLS_CATALOG,
)


class TestFedRAMPHighDoDSSP(unittest.TestCase):
    """
    Test suite verifying FedRAMP High and DoD IL4/IL5 System Security Plan Engine.
    """

    def setUp(self):
        self.engine = FedRAMPHighDoDIL5SSPEngine()

    def test_01_control_family_completeness(self):
        """
        Verify presence of mandatory NIST SP 800-53 Rev 5 control families:
        - Access Control (AC)
        - Audit and Accountability (AU)
        - Configuration Management (CM)
        - Identification and Authentication (IA)
        - Media Protection (MP)
        - System and Communications Protection (SC)
        - System and Information Integrity (SI)
        - Contingency Planning (CP)
        - Supply Chain Risk Management (SR)
        """
        families = {c.family for c in self.engine.controls}
        self.assertIn(ControlFamily.AC, families)
        self.assertIn(ControlFamily.AU, families)
        self.assertIn(ControlFamily.CM, families)
        self.assertIn(ControlFamily.IA, families)
        self.assertIn(ControlFamily.MP, families)
        self.assertIn(ControlFamily.SC, families)
        self.assertIn(ControlFamily.SI, families)
        self.assertIn(ControlFamily.CP, families)
        self.assertIn(ControlFamily.SR, families)
        self.assertGreaterEqual(len(self.engine.controls), 18)

    def test_02_fedramp_high_baseline_audit(self):
        """
        Verify FedRAMP High baseline audit evaluates to COMPLIANT_HIGH:
        - All controls implemented or automated continuously.
        - FIPS 199 High-Water Mark (Confidentiality: HIGH, Integrity: HIGH, Availability: HIGH).
        """
        audit = self.engine.audit_fedramp_high()
        self.assertEqual(audit["fedramp_high_audit_status"], "COMPLIANT_HIGH")
        self.assertEqual(audit["implemented_count"], audit["total_controls_audited"])

        watermark = audit["fips_199_watermark"]
        self.assertEqual(watermark["confidentiality"], "HIGH")
        self.assertEqual(watermark["integrity"], "HIGH")
        self.assertEqual(watermark["availability"], "HIGH")

    def test_03_dod_il5_readiness_invariants(self):
        """
        Verify DoD CC SRG Impact Level 5 (IL5) technical invariants:
        - Airgap SCIF support.
        - FIPS 140-3 cryptography.
        - Hardware PIV/CAC smartcard MFA.
        - SLSA Level 3 build provenance.
        - Sub-second RPO failover.
        """
        il5 = self.engine.verify_dod_il5_readiness()
        self.assertEqual(il5["dod_il5_decision"], "CERTIFIED_IL5_READY")
        self.assertTrue(il5["airgap_scif_support"])
        self.assertTrue(il5["fips_140_3_cryptography"])
        self.assertTrue(il5["hardware_piv_cac_mfa"])
        self.assertTrue(il5["slsa_level_3_provenance"])
        self.assertTrue(il5["subsecond_rpo_failover"])

    def test_04_oscal_v1_1_0_schema_validity(self):
        """
        Verify NIST OSCAL v1.1.0 JSON format compliance:
        - root element: system-security-plan
        - oscal-version: 1.1.0
        - valid UUIDs in document metadata and implemented-requirements
        - by-components mapping present
        """
        oscal = self.engine.generate_oscal_ssp_json()
        ssp = oscal.get("system-security-plan", {})

        self.assertEqual(ssp.get("metadata", {}).get("oscal-version"), "1.1.0")
        self.assertIn("metadata", ssp)
        self.assertIn("system-characteristics", ssp)
        self.assertIn("control-implementation", ssp)

        # Verify UUID format
        doc_id = ssp.get("id", "")
        uuid_pattern = re.compile(r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$")
        self.assertTrue(bool(uuid_pattern.match(doc_id)), f"Invalid UUID: {doc_id}")

        # Check implemented requirements
        reqs = ssp.get("control-implementation", {}).get("implemented-requirements", [])
        self.assertGreaterEqual(len(reqs), 18)
        for req in reqs:
            self.assertTrue(bool(req.get("control-id")))
            self.assertTrue(bool(req.get("description")))
            self.assertGreater(len(req.get("statements", [])), 0)

    def test_05_critical_control_parameter_bindings(self):
        """
        Verify parameter bindings on mission-critical controls:
        - AC-2: session max age 15 mins.
        - IA-2: FIDO2_PIV_CAC authenticator.
        - SC-8: TLS 1.3 only.
        - SR-3: SLSA Level 3.
        """
        controls_map = {c.control_id: c for c in self.engine.controls}

        self.assertEqual(controls_map["AC-2"].parameters.get("session_max_age_min"), 15)
        self.assertEqual(controls_map["IA-2"].parameters.get("authenticator_type"), "FIDO2_PIV_CAC")
        self.assertEqual(controls_map["SC-8"].parameters.get("min_tls_version"), "1.3")
        self.assertEqual(controls_map["SR-3"].parameters.get("slsa_level"), 3)

    def test_06_executive_markdown_dossier_generation(self):
        """
        Verify executive Markdown dossier generation:
        - File exists and has required sections.
        - Attestation from DevSuperSuite Official & infosec@devsupersuite.com.
        """
        md_p, oscal_p = self.engine.export_ssp_dossier()
        self.assertTrue(md_p.exists())
        self.assertTrue(oscal_p.exists())

        content = md_p.read_text(encoding="utf-8")
        self.assertIn("FedRAMP High & DoD IL5 System Security Plan", content)
        self.assertIn("FIPS 199 High-Water Mark", content)
        self.assertIn("NIST SP 800-53 Rev. 5 Control Implementation Ledger", content)
        self.assertIn("infosec@devsupersuite.com", content)

    def test_07_negative_control_failure_detection(self):
        """
        Negative test: injecting a non-compliant or planned control into the catalog
        must immediately degrade the audit status from COMPLIANT_HIGH to NON_COMPLIANT.
        """
        # Save original controls
        original_controls = list(self.engine.controls)

        # Inject a planned / non-implemented control
        failed_control = NISTControlImplementation(
            control_id="AC-99",
            family=ControlFamily.AC,
            title="Simulated Failed Control",
            fedramp_high_baseline=True,
            dod_il4_requirement=True,
            dod_il5_requirement=True,
            status=SecurityControlStatus.PLANNED,
            implementation_summary="Not yet implemented",
            responsible_role="N/A",
            parameters={},
            verification_artifacts=[]
        )
        self.engine.controls.append(failed_control)

        degraded_audit = self.engine.audit_fedramp_high()
        self.assertEqual(degraded_audit["fedramp_high_audit_status"], "NON_COMPLIANT")

        # Restore original controls
        self.engine.controls = original_controls

    def test_08_machine_readable_oscal_file_integrity(self):
        """
        Verify saved oscal_ssp_manifest.json parses as valid JSON with expected metadata.
        """
        oscal_path = SERVICES_DIR / "reports" / "oscal_ssp_manifest.json"
        self.assertTrue(oscal_path.exists())

        data = json.loads(oscal_path.read_text(encoding="utf-8"))
        ssp = data.get("system-security-plan", {})
        self.assertEqual(ssp.get("metadata", {}).get("oscal-version"), "1.1.0")
        self.assertEqual(
            ssp.get("system-characteristics", {}).get("security-sensitivity-level"),
            "High"
        )

    def test_09_cli_interface_execution(self):
        """
        Verify CLI invocation for --summary, --audit-fedramp-high,
        --verify-dod-il5-readiness, and --export-ssp-dossier.
        """
        cli_script = SERVICES_DIR / "fedramp_high_dod_il5_ssp_engine.py"

        # Test --summary
        res1 = subprocess.run([sys.executable, str(cli_script), "--summary"], capture_output=True, text=True, check=True)
        self.assertEqual(res1.returncode, 0)
        self.assertIn("DevSuperSuite FedRAMP High", res1.stdout)

        # Test --audit-fedramp-high
        res2 = subprocess.run([sys.executable, str(cli_script), "--audit-fedramp-high"], capture_output=True, text=True, check=True)
        self.assertEqual(res2.returncode, 0)
        self.assertIn("FedRAMP High Baseline Audit: COMPLIANT_HIGH", res2.stdout)

        # Test --verify-dod-il5-readiness
        res3 = subprocess.run([sys.executable, str(cli_script), "--verify-dod-il5-readiness"], capture_output=True, text=True, check=True)
        self.assertEqual(res3.returncode, 0)
        self.assertIn("DoD CC SRG Impact Level 5 (IL5) Verification: CERTIFIED_IL5_READY", res3.stdout)

        # Test --export-ssp-dossier
        res4 = subprocess.run([sys.executable, str(cli_script), "--export-ssp-dossier"], capture_output=True, text=True, check=True)
        self.assertEqual(res4.returncode, 0)
        self.assertIn("FedRAMP High & DoD IL5 Dossier Exported", res4.stdout)

    def test_10_strict_brand_anonymity_under_devsupersuite(self):
        """
        Strict Brand Anonymity Enforcement:
        - Inspects fedramp_high_dod_il5_ssp_engine.py, fedramp_high_dod_il5_compliance_architecture.md,
          and generated report artifacts.
        - Asserts ZERO personal names, ZERO personal emails (gmail/yahoo/etc), ZERO personal phone numbers.
        - Confirms all attributions point to DevSuperSuite Official & infosec@devsupersuite.com.
        """
        files_to_check = [
            SERVICES_DIR / "fedramp_high_dod_il5_ssp_engine.py",
            SERVICES_DIR / "fedramp_high_dod_il5_compliance_architecture.md",
            SERVICES_DIR / "reports" / "fedramp_high_ssp_executive_dossier.md",
            SERVICES_DIR / "reports" / "oscal_ssp_manifest.json",
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
            clean_content = re.sub(r"SP\s+800-\d+", "", clean_content)

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

