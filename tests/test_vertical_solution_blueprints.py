#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Vertical Solution Blueprints Test Suite
Reference: DSS-VERTICAL-BLUEPRINTS-TESTS-2026-V1
Classification: Automated Quality Gate & Invariant Validation (Restricted)
Contact: DevSuperSuite Solutions Architecture (solutions@devsupersuite.com)
Author: OmniKernel Labs / DevSuperSuite Quality Assurance & Test Engineering
═══════════════════════════════════════════════════════════════════════════════
"""

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
BLUEPRINTS_DIR = DEPLOYMENT_DIR / "blueprints"

if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from enterprise_vertical_solution_blueprints import (
    ORGANIZATION_NAME,
    PRIMARY_CONTACT,
    COMPLIANCE_CONTACT,
    REFERENCE_CODE,
    SECComplianceViolationError,
    SEC17a4WORMLogger,
    PaymentCardRedactor,
    HSMCommitSigner,
    SafeHarborPHIScrubber,
    BAALifecycleManager,
    EnterpriseVerticalSolutionBlueprints
)


class TestEnterpriseVerticalSolutionBlueprints:
    """Enterprise verification suite for Regulated Vertical Blueprints (Finance & Healthcare)."""

    def test_sec_worm_logger_immutability(self):
        """Verify SEC Rule 17a-4 Write-Once-Read-Many (WORM) audit ledger and immutability guard."""
        logger = SEC17a4WORMLogger(retention_years=7)

        # Append record 0
        entry0 = logger.append_log("TRADE_EXECUTION_AUDIT", {"trade_id": "T-1001", "shares": 500}, "trader-01")
        assert entry0["record_index"] == 0
        assert entry0["retention_years"] == 7
        assert entry0["worm_status"] == "LOCKED_IMMUTABLE"
        assert len(entry0["record_sha256"]) == 64
        assert entry0["previous_record_hash"] == "0" * 64

        # Append record 1 (chained hash)
        entry1 = logger.append_log("CODE_REVIEW_APPROVAL", {"pr_id": 42, "approved_by": "compliance_bot"}, "bot-02")
        assert entry1["record_index"] == 1
        assert entry1["previous_record_hash"] == entry0["record_sha256"]

        # Attempting to mutate or delete throws SECComplianceViolationError
        with pytest.raises(SECComplianceViolationError):
            logger.attempt_modify_or_delete(0)
        with pytest.raises(SECComplianceViolationError):
            logger.attempt_modify_or_delete(1)

    def test_payment_card_luhn_algorithm_and_pan_redaction(self):
        """Validate Luhn checksum evaluation and PCI-DSS 4.0 PAN masking."""
        # Valid test card numbers satisfying Luhn MOD-10
        valid_pan = "4532015000000007"
        assert PaymentCardRedactor.luhn_checksum_valid(valid_pan) is True

        # Invalid card number
        invalid_pan = "4532015000000008"
        assert PaymentCardRedactor.luhn_checksum_valid(invalid_pan) is False

        # Redact valid card from text
        text_with_card = f"Customer payment charged to account {valid_pan} via gateway."
        redacted, count = PaymentCardRedactor.redact_pan(text_with_card)
        assert count == 1
        assert valid_pan not in redacted
        assert "[REDACTED_PAN_PCI_DSS-*0007]" in redacted

        # Ensure text without valid card is unredacted
        clean_text = "Transaction ID 9876543210123 confirmed."
        clean_res, c = PaymentCardRedactor.redact_pan(clean_text)
        assert c == 0
        assert clean_res == clean_text

    def test_hsm_commit_signing(self):
        """Verify Hardware Security Module (HSM) Ed25519 commit signing attestation."""
        commit_hash = "9f83c605d4c601882467b5a0a3d61a"
        author = "solutions@devsupersuite.com"
        key_id = "hsm://slot0/key-fin-sign-01"

        sig = HSMCommitSigner.sign_commit(commit_hash, author, key_id)
        assert sig["commit_hash"] == commit_hash
        assert sig["author_email"] == author
        assert sig["hsm_key_id"] == key_id
        assert sig["signature_algorithm"] == "Ed25519-FIPS-140-3"
        assert sig["attestation_status"] == "HARDWARE_VERIFIED"
        assert len(sig["signature_hex"]) == 64

    def test_hipaa_safe_harbor_phi_scrubber(self):
        """Verify Safe Harbor 18-identifier scrubber across clinical test payloads."""
        clinical_sample = (
            "Patient John Doe (SSN: 987-65-4321, MRN-7654321) visited clinic on DOB: 03/15/1975. "
            "Follow-up contact at patient@medical.org or +1-555-123-4567. "
            "Connected from IP 192.168.1.50 with HPID-AB98765432."
        )

        sanitized, stats = SafeHarborPHIScrubber.scrub_text(clinical_sample)
        assert "987-65-4321" not in sanitized
        assert "MRN-7654321" not in sanitized
        assert "patient@medical.org" not in sanitized
        assert "192.168.1.50" not in sanitized

        assert "[REDACTED_PHI_SSN]" in sanitized
        assert "[REDACTED_PHI_MRN]" in sanitized
        assert "[REDACTED_PHI_EMAIL]" in sanitized
        assert "[REDACTED_PHI_IPV4_ADDR]" in sanitized
        assert stats["SSN"] == 1
        assert stats["MRN"] == 1

    def test_shannon_entropy_calculation(self):
        """Verify Shannon entropy calculation for secret and token detection."""
        # Empty text
        assert SafeHarborPHIScrubber.calculate_shannon_entropy("") == 0.0

        # Low entropy (monotonous)
        low_ent = SafeHarborPHIScrubber.calculate_shannon_entropy("aaaaaaaaaaaaaaaa")
        assert low_ent == 0.0

        # High entropy (random base64/token)
        high_ent = SafeHarborPHIScrubber.calculate_shannon_entropy("k9#mP$7vL2!xQ8@wZ1*rT4")
        assert high_ent > 3.8

    def test_baa_lifecycle_manager_execution(self):
        """Verify automated Business Associate Agreement (BAA) execution and statutory covenants."""
        baa = BAALifecycleManager.execute_baa(
            covered_entity_name="Hospital Health System",
            covered_entity_ein="12-3456789",
            authorized_officer_title="Chief Information Security Officer"
        )

        assert baa["status"] == "EXECUTED_ACTIVE"
        assert baa["breach_notification_sla_hours"] == 24
        assert baa["business_associate"]["organization"] == ORGANIZATION_NAME
        assert baa["covered_entity"]["name"] == "Hospital Health System"
        assert len(baa["statutory_covenants"]) >= 5
        assert len(baa["cryptographic_signature"]) == 64

    def test_financial_services_blueprint_schema(self):
        """Validate financial services blueprint compliance mappings and architecture."""
        engine = EnterpriseVerticalSolutionBlueprints()
        blueprint = engine.generate_financial_services_blueprint()

        assert blueprint["metadata"]["organization"] == ORGANIZATION_NAME
        assert blueprint["metadata"]["contact"] == PRIMARY_CONTACT
        assert len(blueprint["regulatory_frameworks"]) >= 3

        arch = blueprint["architecture_components"]
        assert arch["worm_audit_storage"]["retention_period_years"] == 7
        assert arch["worm_audit_storage"]["hash_algorithm"] == "SHA-256 Chained Hash Tree"
        assert "FIPS 140-3" in arch["hardware_cryptography"]["hsm_model"]
        assert arch["disaster_recovery"]["rpo_seconds"] == 0

    def test_healthcare_scif_blueprint_schema(self):
        """Validate healthcare SCIF blueprint compliance mappings and microsegmentation."""
        engine = EnterpriseVerticalSolutionBlueprints()
        blueprint = engine.generate_healthcare_blueprint()

        assert blueprint["metadata"]["organization"] == ORGANIZATION_NAME
        assert len(blueprint["regulatory_frameworks"]) >= 3

        phi_prot = blueprint["phi_protection_mechanisms"]
        assert phi_prot["ephemeral_workloads"]["storage"] == "tmpfs (RAM-only mounts, zero disk persistence)"
        assert "Cilium eBPF" in phi_prot["network_microsegmentation"]["cni"]
        assert "executed_baa_template" in blueprint

    def test_json_manifest_exports_validity(self, tmp_path):
        """Verify export of both blueprints to JSON and check schema validity."""
        engine = EnterpriseVerticalSolutionBlueprints()
        f_file = tmp_path / "financial_services_blueprint.json"
        h_file = tmp_path / "hipaa_healthcare_blueprint.json"

        engine.export_financial_blueprint(f_file)
        engine.export_healthcare_blueprint(h_file)

        assert f_file.exists()
        with open(f_file, "r", encoding="utf-8") as f:
            f_json = json.load(f)
        assert f_json["metadata"]["contact"] == PRIMARY_CONTACT
        assert "regulatory_frameworks" in f_json

        assert h_file.exists()
        with open(h_file, "r", encoding="utf-8") as f:
            h_json = json.load(f)
        assert h_json["metadata"]["contact"] == PRIMARY_CONTACT
        assert "phi_protection_mechanisms" in h_json

    def test_whitepaper_report_generation(self, tmp_path):
        """Verify technical whitepaper generation and content completeness."""
        engine = EnterpriseVerticalSolutionBlueprints()
        rep_file = tmp_path / "enterprise_vertical_solution_blueprints.md"
        engine.export_whitepaper(rep_file)

        assert rep_file.exists()
        content = rep_file.read_text(encoding="utf-8")
        assert "DevSuperSuite Enterprise Regulated Vertical Solution Blueprints" in content
        assert "PCI-DSS v4.0" in content
        assert "SEC Rule 17a-4" in content
        assert "HIPAA Healthcare SCIF Architecture" in content
        assert "solutions@devsupersuite.com" in content

    def test_brand_anonymity_invariants(self):
        """
        Enforce strict institutional brand anonymity:
        Must NOT contain personal names or unauthorized personal email providers.
        Must strictly represent DevSuperSuite Solutions Architecture / OmniKernel Labs.
        """
        forbidden_terms = ["github.com/", "gitlab.com/", "@gmail.com", "@yahoo.com", "@hotmail.com"]
        files_to_check = [
            SERVICES_DIR / "enterprise_vertical_solution_blueprints.py",
            BLUEPRINTS_DIR / "financial_services_blueprint.json",
            BLUEPRINTS_DIR / "hipaa_healthcare_blueprint.json",
            REPORTS_DIR / "enterprise_vertical_solution_blueprints.md"
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
        script = str(SERVICES_DIR / "enterprise_vertical_solution_blueprints.py")

        commands = [
            [python_exe, script, "--summary"],
            [python_exe, script, "--scan-phi-deid", "Patient SSN 000-11-2222 with MRN-998877 visited clinic."],
            [python_exe, script, "--simulate-sec-worm-log", "PAYLOAD_VERIFICATION_PASS"],
            [python_exe, script, "--export-blueprints"]
        ]

        for cmd in commands:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            assert res.returncode == 0, f"Command failed: {' '.join(cmd)}\nStderr: {res.stderr}"
            assert len(res.stdout) > 0
