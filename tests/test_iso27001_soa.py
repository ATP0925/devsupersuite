#!/usr/bin/env python3
"""
Pytest Test Suite for DevSuperSuite ISO/IEC 27001:2022 Statement of Applicability (SoA) & Annex A Controls Engine

Governing Authority: DevSuperSuite Information Security Office (iso27001@devsupersuite.com)
Corporate Entity: DevSuperSuite Official (DevSuperSuite Tech Services)
Classification: Automated Compliance Testing & Invariant Gate Verification
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from services.enterprise_iso27001_soa_engine import (
    ALL_93_CONTROLS_DATA,
    AnnexAControl,
    ControlApplicability,
    ImplementationStatus,
    ISO27001SoAEngine,
    ISOTheme,
)


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def soa_engine(repo_root: Path) -> ISO27001SoAEngine:
    return ISO27001SoAEngine(repo_root=repo_root)


class TestEnterpriseISO27001SoA:
    """Comprehensive high-assurance verification for ISO/IEC 27001:2022 Annex A Controls & SoA Engine."""

    def test_01_all_93_annex_a_controls_represented(self, soa_engine: ISO27001SoAEngine):
        """Verifies exactly 93 Annex A controls exist across the 4 standard ISO 27001:2022 themes."""
        assert len(soa_engine.controls) == 93, f"Expected 93 controls, found {len(soa_engine.controls)}"

        theme_5 = soa_engine.get_controls_by_theme(5)
        theme_6 = soa_engine.get_controls_by_theme(6)
        theme_7 = soa_engine.get_controls_by_theme(7)
        theme_8 = soa_engine.get_controls_by_theme(8)

        assert len(theme_5) == 37, f"Theme 5 (Organizational) must have 37 controls, got {len(theme_5)}"
        assert len(theme_6) == 8, f"Theme 6 (People) must have 8 controls, got {len(theme_6)}"
        assert len(theme_7) == 14, f"Theme 7 (Physical) must have 14 controls, got {len(theme_7)}"
        assert len(theme_8) == 34, f"Theme 8 (Technological) must have 34 controls, got {len(theme_8)}"
        assert len(theme_5) + len(theme_6) + len(theme_7) + len(theme_8) == 93

    def test_02_all_controls_applicable_and_justified(self, soa_engine: ISO27001SoAEngine):
        """Verifies 100% of controls are Applicable and possess rigorous business justifications."""
        for cid, ctrl in soa_engine.controls.items():
            assert ctrl.applicability == ControlApplicability.APPLICABLE.value, (
                f"Control {cid} must be Applicable under DevSuperSuite high-assurance profile"
            )
            assert len(ctrl.justification.strip()) >= 20, (
                f"Control {cid} justification too short: '{ctrl.justification}'"
            )
            assert ctrl.title.strip() != "", f"Control {cid} missing title"
            assert ctrl.description.strip() != "", f"Control {cid} missing description"
            assert len(ctrl.control_types) > 0, f"Control {cid} missing control types"
            assert len(ctrl.info_sec_properties) > 0, f"Control {cid} missing info sec properties"

    def test_03_technological_controls_evidence_bindings(self, soa_engine: ISO27001SoAEngine):
        """Verifies key technological controls are programmatically bound to codebase implementations."""
        # A.8.20 Network Security
        ctrl_8_20 = soa_engine.get_control("A.8.20")
        assert ctrl_8_20 is not None
        assert "services/enterprise_ebpf_socket_interlock.py" in ctrl_8_20.evidence_bindings

        # A.8.24 Use of Cryptography
        ctrl_8_24 = soa_engine.get_control("A.8.24")
        assert ctrl_8_24 is not None
        assert any("pqc" in b for b in ctrl_8_24.evidence_bindings)
        assert any("pkcs11" in b for b in ctrl_8_24.evidence_bindings)

        # A.8.8 Management of Technical Vulnerabilities
        ctrl_8_8 = soa_engine.get_control("A.8.8")
        assert ctrl_8_8 is not None
        assert any("security_scanner" in b for b in ctrl_8_8.evidence_bindings)
        assert any("stride" in b for b in ctrl_8_8.evidence_bindings)

        # A.5.30 ICT Readiness for Business Continuity
        ctrl_5_30 = soa_engine.get_control("A.5.30")
        assert ctrl_5_30 is not None
        assert any("failover" in b or "dr" in b or "chaos" in b for b in ctrl_5_30.evidence_bindings)

        # A.8.10 Information Deletion
        ctrl_8_10 = soa_engine.get_control("A.8.10")
        assert ctrl_8_10 is not None
        assert "services/enterprise_fips_memory_sanitization_engine.py" in ctrl_8_10.evidence_bindings

    def test_04_evidence_files_exist_and_verified(self, soa_engine: ISO27001SoAEngine):
        """Verifies all bound evidence artifacts exist on disk and have valid SHA-256 hashes."""
        ev = soa_engine.verify_evidence_bindings()

        assert ev["total_bound_files"] >= 20, f"Expected at least 20 bound files, got {ev['total_bound_files']}"
        assert ev["missing_files"] == 0, f"Missing files found: {ev['missing_files']}"
        assert ev["verified_files"] == ev["total_bound_files"]
        assert ev["verification_rate_pct"] == 100.0

        for cid, records in ev["details"].items():
            for rec in records:
                assert rec["status"] == "VERIFIED", f"File {rec['relative_path']} for control {cid} failed verification"
                assert len(rec["sha256"]) == 64, f"Invalid SHA-256 length for {rec['relative_path']}"
                assert rec["size_bytes"] > 0, f"File {rec['relative_path']} is empty"

    def test_05_risk_treatment_plan_scoring(self, soa_engine: ISO27001SoAEngine):
        """Verifies Risk Treatment Plan (RTP) scoring reflects CMMI Level 5 and maturity >= 4.8/5.0."""
        rtp = soa_engine.calculate_risk_treatment_scores()

        assert rtp["total_controls_evaluated"] == 93
        assert rtp["overall_mean_baseline_risk"] >= 7.5, "Baseline risk should represent realistic inherent threat level"
        assert rtp["overall_mean_residual_risk"] <= 2.0, "Post-treatment residual risk must be low"
        assert rtp["overall_risk_deflection_pct"] >= 75.0, "Risk deflection must exceed 75%"
        assert rtp["overall_compliance_maturity"] >= 4.8, f"Maturity {rtp['overall_compliance_maturity']} must be >= 4.8"
        assert "Level 5" in rtp["cmmi_level"]

    def test_06_theme_breakdown_scoring(self, soa_engine: ISO27001SoAEngine):
        """Verifies each individual theme maintains maturity >= 4.8 and substantial risk deflection."""
        rtp = soa_engine.calculate_risk_treatment_scores()
        themes = rtp["themes"]

        assert len(themes) == 4
        for theme_name, t_info in themes.items():
            assert t_info["mean_maturity_level"] >= 4.8, f"{theme_name} maturity below 4.8"
            assert t_info["risk_reduction_pct"] >= 70.0, f"{theme_name} risk reduction below 70%"
            assert t_info["mean_residual_risk"] < 2.0, f"{theme_name} residual risk too high"

    def test_07_manifest_generation_and_schema(self, soa_engine: ISO27001SoAEngine, tmp_path: Path):
        """Verifies SoA JSON manifest generation, schema compliance, and cryptographic hash."""
        manifest_path = tmp_path / "iso27001_soa_matrix.json"
        manifest = soa_engine.generate_soa_manifest(output_path=manifest_path)

        assert manifest_path.exists()
        assert manifest["document_id"] == "DSS-ISO27001-SOA-2022-V1"
        assert manifest["authority"] == soa_engine.AUTHORITY
        assert manifest["total_controls"] == 93
        assert manifest["applicable_controls"] == 93
        assert len(manifest["soa_matrix_sha256"]) == 64
        assert len(manifest["controls"]) == 93

        # Validate that disk JSON matches return object
        disk_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert disk_data["soa_matrix_sha256"] == manifest["soa_matrix_sha256"]

    def test_08_executive_report_generation(self, soa_engine: ISO27001SoAEngine, tmp_path: Path):
        """Verifies formal executive markdown report generation with all required sections."""
        report_path = tmp_path / "iso27001_2022_soa_report.md"
        content = soa_engine.export_soa_binder(output_path=report_path)

        assert report_path.exists()
        assert "# 🛡️ DevSuperSuite Tech Services: ISO/IEC 27001:2022 Statement of Applicability (SoA)" in content
        assert "## 1. Executive Summary & Statement of Applicability Scorecard" in content
        assert "## 2. Annex A Four-Theme Breakdown & Risk Treatment Scoring" in content
        assert "## 3. Concrete Technological Evidence Bindings" in content
        assert "## 4. Complete Annex A 93-Control Statement of Applicability Matrix" in content
        assert "### Formal Auditor Attestation & Sign-off" in content
        assert "APPROVED FOR ISO/IEC 27001:2022 ACCREDITATION" in content

    def test_09_annex_a_audit_method(self, soa_engine: ISO27001SoAEngine):
        """Verifies the audit method issues CERTIFIED_COMPLIANT with zero unmitigated high risks."""
        audit_res = soa_engine.audit_annex_a_controls()

        assert audit_res["audit_status"] == "CERTIFIED_COMPLIANT"
        assert audit_res["total_annex_a_controls"] == 93
        assert audit_res["applicable_controls"] == 93
        assert audit_res["excluded_controls"] == 0
        assert audit_res["applicability_coverage_pct"] == 100.0
        assert audit_res["unmitigated_high_risks"] == []
        assert audit_res["evidence_verification"]["missing_files"] == 0

    def test_10_missing_evidence_tamper_detection(self, tmp_path: Path):
        """Verifies that missing or unresolvable evidence files trigger ACTION_REQUIRED status."""
        empty_root = tmp_path / "empty_repo"
        empty_root.mkdir()

        # Engine pointing to empty repo should detect missing bound files
        engine_missing = ISO27001SoAEngine(repo_root=empty_root)
        audit_res = engine_missing.audit_annex_a_controls()

        assert audit_res["evidence_verification"]["missing_files"] > 0
        assert audit_res["audit_status"] == "ACTION_REQUIRED"

    def test_11_cli_interface_all_flags(self, repo_root: Path):
        """Verifies the multi-action CLI interface executes cleanly across all flags."""
        script_path = repo_root / "services" / "enterprise_iso27001_soa_engine.py"

        flags = [
            ["--audit-annex-a-controls"],
            ["--evaluate-soa-justifications"],
            ["--generate-soa-manifest"],
            ["--export-soa-binder"],
            ["--summary"],
        ]

        for flag in flags:
            cmd = [sys.executable, str(script_path)] + flag
            proc = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True)
            assert proc.returncode == 0, f"CLI command {' '.join(cmd)} failed: {proc.stderr}"
            assert len(proc.stdout) > 0

    def test_12_strict_brand_anonymity_under_devsupersuite(self, repo_root: Path, soa_engine: ISO27001SoAEngine):
        """Enforces 100% Brand Anonymity: zero personal identities, strictly DevSuperSuite."""
        # Forbidden personal strings
        forbidden_terms = [
            "atpad",
            "atpadhyay",
            "kartik",
            "aditya",
            "singh",
            "sharma",
            "verma",
            "gupta",
            "gmail.com",
            "yahoo.com",
            "hotmail.com",
            "+91",
            "+1-",
        ]

        manifest_file = repo_root / "data" / "iso27001_soa_matrix.json"
        report_file = repo_root / "services" / "reports" / "iso27001_2022_soa_report.md"
        script_file = repo_root / "services" / "enterprise_iso27001_soa_engine.py"

        files_to_check = [manifest_file, report_file, script_file]

        for file_path in files_to_check:
            assert file_path.exists(), f"File {file_path} does not exist"
            text = file_path.read_text(encoding="utf-8").lower()
            for term in forbidden_terms:
                assert term not in text, f"Forbidden term '{term}' found in {file_path}"

        # Verify authority attributes explicitly brand DevSuperSuite
        assert "DevSuperSuite" in soa_engine.AUTHORITY
        assert "iso27001@devsupersuite.com" in soa_engine.AUTHORITY
        assert "DevSuperSuite" in soa_engine.ORGANIZATION

