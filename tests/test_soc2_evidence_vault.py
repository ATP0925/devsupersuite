"""
DevSuperSuite Tech Services - Continuous SOC 2 Type II Evidence Vault Test Suite
File: tests/test_soc2_evidence_vault.py
Governing Authority: DevSuperSuite Security & Compliance Desk
Contact: compliance@devsupersuite.com
Regulatory Baseline: AICPA Trust Services Criteria (TSC 2022) / SOC 2 Type II / RFC 6962
"""

import base64
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import re
import subprocess
import sys
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from services.enterprise_soc2_evidence_vault_engine import (
    EnterpriseSOC2EvidenceVaultEngine,
    MerkleTreeEngine,
    TSCCriterionID,
    TSCEvidenceItem,
    export_soc2_live_audit_artifacts,
)


class TestEnterpriseSOC2EvidenceVault:
    """Comprehensive test suite for Continuous SOC 2 Type II Evidence Vault & Merkle Integrity."""

    @pytest.fixture
    def engine(self):
        return EnterpriseSOC2EvidenceVaultEngine()

    def test_01_tsc_control_sampling_coverage(self, engine):
        """Verifies live evidence sampling covers all 5 core AICPA TSC criteria."""
        samples = engine.sample_all_tsc_evidence()
        assert len(samples) == 5
        control_ids = {s.control_id for s in samples}
        expected_controls = {
            TSCCriterionID.CC6_1_6_6.value,
            TSCCriterionID.CC6_7.value,
            TSCCriterionID.CC7_2.value,
            TSCCriterionID.CC8_1.value,
            TSCCriterionID.A1_2.value,
        }
        assert expected_controls == control_ids

    def test_02_all_controls_pass_compliant(self, engine):
        """Verifies every sampled evidence item has PASS_COMPLIANT status and non-empty hash."""
        samples = engine.sample_all_tsc_evidence()
        for item in samples:
            assert item.control_status == "PASS_COMPLIANT"
            assert len(item.verification_hash) == 64
            assert item.verification_hash == item.compute_hash()

    def test_03_merkle_tree_construction_and_root(self):
        """Verifies deterministic Merkle tree root calculation."""
        leaves = [
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        ]
        root1 = MerkleTreeEngine.compute_merkle_root(leaves)
        root2 = MerkleTreeEngine.compute_merkle_root(leaves)
        assert len(root1) == 64
        assert root1 == root2, "Merkle root calculation must be deterministic"

    def test_04_merkle_root_tamper_detection(self, engine):
        """Verifies modifying any evidence payload alters the computed Merkle root."""
        dossier = engine.construct_vault_dossier()
        original_root = dossier["merkle_integrity_proof"]["merkle_root"]

        # Tamper with evidence sample 0
        tampered_dossier = json.loads(json.dumps(dossier))
        tampered_dossier["evidence_samples"][0]["live_metric_value"] = "TAMPERED_ADVERSARY_METRIC"

        is_valid, err_msg = EnterpriseSOC2EvidenceVaultEngine.verify_merkle_evidence_integrity(tampered_dossier)
        assert is_valid is False
        assert "mismatch" in err_msg.lower()

    def test_05_ed25519_merkle_root_signature_verification(self, engine):
        """Verifies Ed25519 compliance signature over Merkle root passes verification."""
        dossier = engine.construct_vault_dossier()
        is_valid, msg = EnterpriseSOC2EvidenceVaultEngine.verify_merkle_evidence_integrity(dossier)
        assert is_valid is True
        assert "verified intact" in msg

    def test_06_tampered_signature_rejection(self, engine):
        """Verifies bit-flipping the compliance signature triggers verification failure."""
        dossier = engine.construct_vault_dossier()
        tampered = json.loads(json.dumps(dossier))

        sig_bytes = bytearray(bytes.fromhex(tampered["merkle_integrity_proof"]["ed25519_signature_hex"]))
        sig_bytes[5] ^= 0xFF
        tampered["merkle_integrity_proof"]["ed25519_signature_hex"] = sig_bytes.hex()

        is_valid, err = EnterpriseSOC2EvidenceVaultEngine.verify_merkle_evidence_integrity(tampered)
        assert is_valid is False
        assert "failed" in err.lower()

    def test_07_auditor_token_generation_and_verification(self, engine):
        """Verifies time-bounded auditor token creation, structure, and signature validation."""
        token = engine.generate_auditor_token(auditor_id="PWC-AUDIT-ENGAGEMENT-2026", validity_hours=48)
        assert token.startswith("DSS-AUDIT-SOC2-")
        assert len(token.split(".")) == 3

        is_valid, msg, payload = EnterpriseSOC2EvidenceVaultEngine.verify_auditor_token(token)
        assert is_valid is True
        assert "verified valid" in msg
        assert payload is not None
        assert payload["auditor_id"] == "PWC-AUDIT-ENGAGEMENT-2026"
        assert payload["authorized_scope"] == "SOC_2_TYPE_II_READ_ONLY_AUDIT_ACCESS"

    def test_08_expired_auditor_token_rejection(self, engine):
        """Verifies expired auditor token is rejected by the verification engine."""
        # Forge an expired token with valid signature
        token_id = "EXPIRED-TEST"
        now = datetime.now(timezone.utc)
        expired_dt = now - timedelta(hours=10)

        payload = {
            "token_id": token_id,
            "auditor_id": "TEST-EXPIRED",
            "issued_at_utc": (now - timedelta(hours=20)).isoformat(),
            "expires_at_utc": expired_dt.isoformat(),
            "authorized_scope": "SOC_2_TYPE_II_READ_ONLY_AUDIT_ACCESS",
            "issuer": "DevSuperSuite Security & Compliance (compliance@devsupersuite.com)",
            "signer_public_key_hex": engine.public_key_hex,
        }
        raw_p = json.dumps(payload, sort_keys=True).encode("utf-8")
        sig = engine._compliance_private_key.sign(raw_p)

        b64_p = base64.urlsafe_b64encode(raw_p).decode("utf-8")
        b64_s = base64.urlsafe_b64encode(sig).decode("utf-8")
        expired_token = f"DSS-AUDIT-SOC2-{token_id}.{b64_p}.{b64_s}"

        is_valid, err_msg, _ = EnterpriseSOC2EvidenceVaultEngine.verify_auditor_token(expired_token)
        assert is_valid is False
        assert "expired" in err_msg.lower()

    def test_09_forged_auditor_token_rejection(self, engine):
        """Verifies forged or tampered token payload fails signature verification."""
        token = engine.generate_auditor_token()
        parts = token.split(".")

        # Modify payload
        raw_p = base64.urlsafe_b64decode(parts[1].encode("utf-8")).decode("utf-8")
        tampered_p = raw_p.replace("AUDITOR-BIG4-VERIFY-01", "ROGUE-ACTOR-INTRUDER")
        forged_b64_p = base64.urlsafe_b64encode(tampered_p.encode("utf-8")).decode("utf-8")
        forged_token = f"{parts[0]}.{forged_b64_p}.{parts[2]}"

        is_valid, err_msg, _ = EnterpriseSOC2EvidenceVaultEngine.verify_auditor_token(forged_token)
        assert is_valid is False
        assert "failed" in err_msg.lower()

    def test_10_manifest_and_report_file_generation_and_schema(self, engine):
        """Verifies export of live manifest and publication-grade markdown binder."""
        manifest_p, report_p, token = export_soc2_live_audit_artifacts(engine)
        assert manifest_p.exists()
        assert report_p.exists()
        assert token.startswith("DSS-AUDIT-SOC2-")

        # Validate JSON manifest
        with open(manifest_p, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["vault_id"] == "VAULT-SOC2-TYPE2-2026-LIVE"
        assert data["overall_compliance_verdict"] == "SOC_2_TYPE_2_FULLY_CERTIFIED"
        assert data["compliance_score_pct"] == 100.0
        assert len(data["evidence_samples"]) == 5
        assert "merkle_integrity_proof" in data

        # Validate Markdown report
        text = report_p.read_text(encoding="utf-8")
        assert "AICPA Trust Services Criteria" in text
        assert "CC6.1/CC6.6" in text
        assert "CC6.7" in text
        assert "CC7.2" in text
        assert "CC8.1" in text
        assert "A1.2" in text
        assert "compliance@devsupersuite.com" in text

    def test_11_cli_interface_all_flags(self):
        """Verifies CLI execution across all flags with exit code 0 and DevSuperSuite branding."""
        script_path = REPO_ROOT / "services" / "enterprise_soc2_evidence_vault_engine.py"
        assert script_path.exists()

        flags = [
            ["--sample-tsc-evidence"],
            ["--verify-merkle-integrity"],
            ["--generate-auditor-token"],
            ["--export-soc2-binder"],
            ["--summary"],
        ]

        for flag_set in flags:
            proc = subprocess.run(
                [sys.executable, str(script_path)] + flag_set,
                capture_output=True,
                text=True,
                timeout=25,
            )
            assert proc.returncode == 0, f"CLI command failed with {flag_set}: {proc.stderr}"
            assert "DevSuperSuite" in proc.stdout

    def test_12_strict_brand_anonymity_under_devsupersuite(self, engine):
        """Enforces 100% brand anonymity under DevSuperSuite Security & Compliance Desk."""
        manifest_p, report_p, _ = export_soc2_live_audit_artifacts(engine)

        target_files = [
            REPO_ROOT / "services" / "enterprise_soc2_evidence_vault_engine.py",
            manifest_p,
            report_p,
        ]

        prohibited_names = [
            bytes.fromhex("70726174696b").decode("utf-8"),
            bytes.fromhex("7061646b6172").decode("utf-8"),
            bytes.fromhex("6174706164").decode("utf-8"),
        ]

        phone_pattern = re.compile(
            r"(?<![A-Za-z0-9_-])(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?![A-Za-z0-9_-])"
        )

        for file_path in target_files:
            assert file_path.exists(), f"Target file does not exist: {file_path}"
            content = file_path.read_text(encoding="utf-8")

            # Check prohibited personal names
            for name in prohibited_names:
                assert name not in content.lower(), (
                    f"Brand anonymity violation: Found prohibited name '{name}' in {file_path.name}"
                )

            # Scrub safe timestamps, ISO dates, GUIDs before phone regex
            scrubbed = re.sub(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}", "", content)
            scrubbed = re.sub(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", "", scrubbed)

            phone_matches = phone_pattern.findall(scrubbed)
            assert not phone_matches, (
                f"Brand anonymity violation: Found phone pattern in {file_path.name}: {phone_matches}"
            )

            # Confirm corporate branding
            assert "DevSuperSuite" in content, (
                f"Missing corporate brand DevSuperSuite in {file_path.name}"
            )
            assert "compliance@devsupersuite.com" in content, (
                f"Missing corporate email in {file_path.name}"
            )

