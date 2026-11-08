"""
DevSuperSuite Tech Services - Continuous STRIDE Threat Modeling Test Suite
File: tests/test_continuous_stride.py
Governing Authority: DevSuperSuite Security & Compliance Desk
Contact: security@devsupersuite.com
Regulatory Baseline: Microsoft STRIDE / DREAD Model / NIST SP 800-154 / MITRE ATT&CK v14
"""

import json
from pathlib import Path
import re
import subprocess
import sys
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from services.enterprise_continuous_stride_engine import (
    ContinuousSTRIDEEngine,
    STRIDECategory,
    RiskSeverity,
    MitigationControl,
    DREADScore,
    ThreatVector,
    export_stride_threat_manifest,
    export_stride_threat_report,
)


class TestEnterpriseContinuousSTRIDE:
    """Comprehensive test suite for Continuous STRIDE Threat Modeling & Attack Graph Engine."""

    @pytest.fixture
    def engine(self):
        return ContinuousSTRIDEEngine()

    def test_01_stride_taxonomy_full_coverage(self, engine):
        """Verifies all 6 STRIDE threat categories are actively modeled."""
        categories_found = {t.category for t in engine.threats}
        expected_categories = {
            STRIDECategory.SPOOFING,
            STRIDECategory.TAMPERING,
            STRIDECategory.REPUDIATION,
            STRIDECategory.INFORMATION_DISCLOSURE,
            STRIDECategory.DENIAL_OF_SERVICE,
            STRIDECategory.ELEVATION_OF_PRIVILEGE,
        }
        assert expected_categories.issubset(categories_found), "Missing STRIDE category coverage"

    def test_02_service_nodes_and_scif_enclave_topology(self, engine):
        """Verifies complete topology modeling across microservices and sovereign SCIF enclaves."""
        node_ids = set(engine.nodes.keys())
        expected_nodes = {
            "NODE-EXT-UNTRUSTED",
            "NODE-EDGE-GW",
            "NODE-AST-ENGINE",
            "NODE-SPIRE-CA",
            "NODE-FIN-VAULT",
            "ENCLAVE-SCIF-HSM",
        }
        assert expected_nodes.issubset(node_ids)
        assert engine.nodes["ENCLAVE-SCIF-HSM"].is_airgapped is True
        assert engine.nodes["NODE-FIN-VAULT"].is_airgapped is True
        assert engine.nodes["NODE-EXT-UNTRUSTED"].is_airgapped is False

    def test_03_dread_score_calculation_and_severity(self):
        """Verifies DREAD mathematical formula and severity tier classifications."""
        score_crit = DREADScore(damage=10.0, reproducibility=9.5, exploitability=9.0, affected_users=9.5, discoverability=9.0)
        assert score_crit.total_score == 9.4
        assert score_crit.severity == RiskSeverity.CRITICAL

        score_high = DREADScore(damage=8.0, reproducibility=7.0, exploitability=7.5, affected_users=8.0, discoverability=7.0)
        assert score_high.total_score == 7.5
        assert score_high.severity == RiskSeverity.HIGH

        score_med = DREADScore(damage=5.0, reproducibility=5.0, exploitability=5.0, affected_users=5.0, discoverability=5.0)
        assert score_med.total_score == 5.0
        assert score_med.severity == RiskSeverity.MEDIUM

        score_low = DREADScore(damage=2.0, reproducibility=2.0, exploitability=2.0, affected_users=2.0, discoverability=2.0)
        assert score_low.total_score == 2.0
        assert score_low.severity == RiskSeverity.LOW

    def test_04_dynamic_dread_mitigation_deflection(self, engine):
        """Verifies active enterprise controls deflect aggregate DREAD risk by >= 70%."""
        summary = engine.generate_threat_model_summary()
        assert summary["aggregate_raw_dread_score"] >= 7.0
        assert summary["aggregate_residual_dread_score"] <= 2.5
        assert summary["overall_risk_deflection_pct"] >= 70.0
        assert summary["threat_status"] == "CONTROLLED_FAIL_CLOSED"

    def test_05_multi_hop_attack_graph_path_generation(self, engine):
        """Verifies multi-hop path probabilities and significant risk deflection ratios."""
        paths = engine.compute_attack_paths()
        assert len(paths) >= 3

        # Path 1: Internet -> Edge GW -> AST Engine -> Financial Vault
        path1 = paths[0]
        assert path1.path_id == "AP-CRITICAL-MULTI-HOP-01"
        assert path1.nodes[0] == "NODE-EXT-UNTRUSTED"
        assert path1.nodes[-1] == "NODE-FIN-VAULT"
        assert path1.cumulative_raw_probability > path1.cumulative_residual_probability
        assert path1.risk_deflection_ratio > 1000.0

        # Path 2: Internet -> Edge GW -> AST Engine -> Enclave HSM
        path2 = paths[1]
        assert path2.nodes[-1] == "ENCLAVE-SCIF-HSM"
        assert path2.risk_deflection_ratio > 1000.0

    def test_06_ebpf_socket_interlock_mitigation_binding(self, engine):
        """Verifies eBPF socket interlock mitigations for SSRF and DoS attacks."""
        ssrf_threat = next(t for t in engine.threats if t.threat_id == "THR-STRIDE-07")
        assert ssrf_threat.mitigation_control == MitigationControl.EBPF_SOCKET_INTERLOCK
        assert ssrf_threat.control_efficiency_pct >= 99.0
        assert ssrf_threat.residual_exploit_probability < 0.001

        dos_threat = next(t for t in engine.threats if t.threat_id == "THR-STRIDE-05")
        assert dos_threat.mitigation_control == MitigationControl.EBPF_SOCKET_INTERLOCK
        assert dos_threat.control_efficiency_pct >= 99.0

    def test_07_fips_140_3_hsm_mitigation_binding(self, engine):
        """Verifies FIPS 140-3 PKCS#11 HSM mitigates repudiation and balance tampering."""
        repud_threat = next(t for t in engine.threats if t.threat_id == "THR-STRIDE-03")
        assert repud_threat.mitigation_control == MitigationControl.FIPS_140_3_HSM
        assert repud_threat.control_efficiency_pct >= 99.5
        assert repud_threat.residual_exploit_probability <= 0.0005

    def test_08_ml_kem_768_pqc_mitigation_binding(self, engine):
        """Verifies ML-KEM-768 lattice encryption neutralizes quantum HNDL threats."""
        hndl_threat = next(t for t in engine.threats if t.threat_id == "THR-STRIDE-04")
        assert hndl_threat.category == STRIDECategory.INFORMATION_DISCLOSURE
        assert hndl_threat.mitigation_control == MitigationControl.ML_KEM_768_ENCRYPTION
        assert hndl_threat.control_efficiency_pct >= 99.9
        assert hndl_threat.residual_dread.total_score <= 2.5

    def test_09_unverified_mitigation_fallback(self):
        """Verifies that an unverified mitigation causes residual risk to revert to raw exposure."""
        threat = ThreatVector(
            threat_id="THR-TEST-UNVERIFIED",
            source_node="NODE-A",
            target_node="NODE-B",
            category=STRIDECategory.TAMPERING,
            title="Unmitigated Test Threat",
            attack_description="Attack vector with unverified mitigation control",
            base_exploit_probability=0.80,
            raw_dread=DREADScore(damage=9.0, reproducibility=9.0, exploitability=9.0, affected_users=9.0, discoverability=9.0),
            mitigation_control=MitigationControl.EBPF_SOCKET_INTERLOCK,
            control_efficiency_pct=99.0,
            mitigation_verified=False,  # Unverified!
        )

        assert threat.residual_exploit_probability == threat.base_exploit_probability
        assert threat.residual_dread.total_score == threat.raw_dread.total_score

    def test_10_manifest_and_report_file_generation_and_schema(self, engine):
        """Verifies threat manifest and executive report files are properly generated."""
        manifest_path = export_stride_threat_manifest(engine)
        report_path = export_stride_threat_report(engine)

        assert manifest_path.exists()
        assert report_path.exists()

        # Validate JSON schema
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        assert manifest_data["model_reference"] == "STRIDE-DSS-CONTINUOUS-2026-V1"
        assert manifest_data["total_microservice_nodes"] == 6
        assert manifest_data["overall_risk_deflection_pct"] >= 70.0
        assert "threats" in manifest_data and len(manifest_data["threats"]) >= 7
        assert "attack_paths" in manifest_data and len(manifest_data["attack_paths"]) >= 3

        # Validate Markdown report
        report_text = report_path.read_text(encoding="utf-8")
        assert "Microsoft STRIDE" in report_text
        assert "DREAD" in report_text
        assert "ENCLAVE-SCIF-HSM" in report_text
        assert "eBPF Socket Interlock" in report_text
        assert "security@devsupersuite.com" in report_text

    def test_11_cli_interface_all_flags(self):
        """Verifies CLI flags execute with zero exit code and DevSuperSuite branding."""
        script_path = REPO_ROOT / "services" / "enterprise_continuous_stride_engine.py"
        assert script_path.exists()

        flags = [
            ["--analyze-threats"],
            ["--calc-paths"],
            ["--verify-mitigations"],
            ["--export-graph"],
            ["--export-report"],
        ]

        for flag_set in flags:
            proc = subprocess.run(
                [sys.executable, str(script_path)] + flag_set,
                capture_output=True,
                text=True,
                timeout=25,
            )
            assert proc.returncode == 0, f"CLI execution failed with {flag_set}: {proc.stderr}"
            assert "DevSuperSuite" in proc.stdout

    def test_12_strict_brand_anonymity_under_devsupersuite(self, engine):
        """Enforces 100% brand anonymity under DevSuperSuite Security & Compliance Desk."""
        manifest_path = export_stride_threat_manifest(engine)
        report_path = export_stride_threat_report(engine)

        target_files = [
            REPO_ROOT / "services" / "enterprise_continuous_stride_engine.py",
            manifest_path,
            report_path,
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
            scrubbed = re.sub(r"STRIDE-DSS-CONTINUOUS-\d{4}-V\d", "", scrubbed)

            phone_matches = phone_pattern.findall(scrubbed)
            assert not phone_matches, (
                f"Brand anonymity violation: Found phone pattern in {file_path.name}: {phone_matches}"
            )

            # Confirm corporate branding
            assert "DevSuperSuite" in content, (
                f"Missing corporate brand DevSuperSuite in {file_path.name}"
            )
            assert "security@devsupersuite.com" in content, (
                f"Missing corporate email in {file_path.name}"
            )

