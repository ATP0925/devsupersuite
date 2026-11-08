"""
DevSuperSuite Tech Services - Automated Continuous Chaos Engineering & Resilience Test Suite
File: tests/test_chaos_resilience.py
Governing Entity: DevSuperSuite Security & Compliance Desk
Contact: security@devsupersuite.com
Regulatory Baseline: Chaos Community Principles / ISO 27001:2022 A.8.14 / SOC 2 Type II
"""

import json
from pathlib import Path
import re
import subprocess
import sys
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from services.enterprise_chaos_resilience_engine import (
    EnterpriseChaosResilienceEngine,
    ChaosExperimentType,
    ExperimentStatus,
    write_chaos_reports,
)


class TestEnterpriseChaosResilience:
    """Rigorous verification suite for distributed chaos experiments, MTTR SLAs, and steady-state recovery."""

    @pytest.fixture
    def engine(self):
        return EnterpriseChaosResilienceEngine(cluster_id="test-resilience-mesh-01")

    def test_01_packet_loss_injection_steady_state_recovery(self, engine):
        """Verifies packet loss injection self-heals in < 3.2s via retry circuit breaker."""
        res = engine.execute_packet_loss_injection(drop_rate_pct=30.0)

        assert res.experiment_type == ChaosExperimentType.PACKET_LOSS_INJECTION
        assert res.status == ExperimentStatus.PASSED_STEADY_STATE_RECOVERED
        assert res.steady_state_hypothesis_verified is True
        assert 0.0 < res.mttr_seconds < 3.2, f"MTTR {res.mttr_seconds}s exceeded 3.2s SLA ceiling"
        assert res.post_fault_metrics.error_rate_pct < 0.1

    def test_02_dns_blackholing_instant_cache_fallback(self, engine):
        """Verifies downstream DNS blackholing triggers sub-second cache fallback."""
        res = engine.execute_dns_blackholing(target_domain="auth.devsupersuite.io")

        assert res.experiment_type == ChaosExperimentType.DNS_BLACKHOLING
        assert res.status == ExperimentStatus.PASSED_STEADY_STATE_RECOVERED
        assert res.mttr_seconds < 1.0, f"DNS failover MTTR {res.mttr_seconds}s took longer than expected"
        assert res.post_fault_metrics.error_rate_pct == 0.0

    def test_03_raft_split_brain_quorum_linearizability(self, engine):
        """Verifies Raft network partition preserves linearizability and elects valid leader."""
        res = engine.execute_raft_split_brain_quorum(cluster_nodes=5)

        assert res.experiment_type == ChaosExperimentType.RAFT_SPLIT_BRAIN_QUORUM
        assert res.status == ExperimentStatus.PASSED_STEADY_STATE_RECOVERED
        assert res.post_fault_metrics.consensus_linearizable is True
        assert res.mttr_seconds < 3.2

    def test_04_memory_pressure_cgroup_eviction(self, engine):
        """Verifies cgroup v2 proactive memory eviction prevents OOM crashes."""
        res = engine.execute_memory_pressure_oom(simulated_utilization_pct=94.0)

        assert res.experiment_type == ChaosExperimentType.MEMORY_PRESSURE_OOM
        assert res.status == ExperimentStatus.PASSED_STEADY_STATE_RECOVERED
        assert res.steady_state_hypothesis_verified is True
        assert res.post_fault_metrics.error_rate_pct == 0.0
        assert res.mttr_seconds < 3.2

    def test_05_cold_node_crash_replica_promotion(self, engine):
        """Verifies cold node crash triggers automated distributed replica promotion."""
        res = engine.execute_cold_node_crash(node_id="worker-node-03")

        assert res.experiment_type == ChaosExperimentType.COLD_NODE_CRASH
        assert res.status == ExperimentStatus.PASSED_STEADY_STATE_RECOVERED
        assert res.post_fault_metrics.healthy_node_ratio == 1.0
        assert res.mttr_seconds < 3.2

    def test_06_run_all_experiments_100pct_resilience_rate(self, engine):
        """Executes full 5-stage chaos suite and confirms 100% resilience rate."""
        suite_data = engine.run_all_experiments()

        assert suite_data["total_experiments"] == 5
        assert suite_data["experiments_passed"] == 5
        assert suite_data["experiments_failed"] == 0
        assert suite_data["overall_resilience_rate_pct"] == 100.0
        assert suite_data["mttr_sla_satisfied"] is True

    def test_07_mttr_calculation_strict_sla_compliance(self, engine):
        """Guarantees both average MTTR and worst-case MTTR strictly satisfy < 3.2s ceiling."""
        suite_data = engine.run_all_experiments()

        avg_mttr = suite_data["average_mttr_seconds"]
        max_mttr = suite_data["max_mttr_seconds"]
        ceiling = suite_data["mttr_sla_ceiling_seconds"]

        assert 0.0 < avg_mttr < ceiling, f"Average MTTR {avg_mttr}s >= {ceiling}s"
        assert 0.0 < max_mttr < ceiling, f"Max MTTR {max_mttr}s >= {ceiling}s"

    def test_08_steady_state_hypothesis_pre_post_metrics(self, engine):
        """Verifies pre-fault and post-fault steady-state metric consistency."""
        suite_data = engine.run_all_experiments()

        for exp in suite_data["experiments"]:
            pre = exp["pre_fault_metrics"]
            post = exp["post_fault_metrics"]

            # Latency delta must be < 10ms post-recovery
            latency_delta = abs(post["latency_p99_ms"] - pre["latency_p99_ms"])
            assert latency_delta < 10.0, f"Latency delta {latency_delta}ms excessive"

            # Post-fault error rate must be < 0.1%
            assert post["error_rate_pct"] <= 0.1

    def test_09_chaos_report_and_manifest_generation(self, engine):
        """Verifies JSON manifest and Markdown executive scorecard generation."""
        suite_data = engine.run_all_experiments()
        scorecard_md, manifest_json = write_chaos_reports(suite_data)

        assert scorecard_md.exists()
        assert manifest_json.exists()

        with open(manifest_json, "r", encoding="utf-8") as f:
            manifest_content = json.load(f)
        assert manifest_content["suite_id"] == "CHAOS-SUITE-2026-V1"
        assert len(manifest_content["experiments"]) == 5

        with open(scorecard_md, "r", encoding="utf-8") as f:
            md_text = f.read()
        assert "DevSuperSuite" in md_text
        assert "ENTERPRISE CHAOS RESILIENCE SCORECARD" in md_text
        assert "99.999%" in md_text

    def test_10_cli_interface_all_flags_execution(self):
        """Verifies all CLI flags execute with exit code 0 and proper brand headers."""
        engine_script = REPO_ROOT / "services" / "enterprise_chaos_resilience_engine.py"
        assert engine_script.exists()

        flags = [
            ["--summary"],
            ["--run-all-chaos-experiments"],
            ["--inject-fault", "PACKET_LOSS"],
            ["--inject-fault", "DNS_BLACKHOLE"],
            ["--inject-fault", "RAFT_SPLIT"],
            ["--inject-fault", "MEMORY_PRESSURE"],
            ["--inject-fault", "COLD_CRASH"],
            ["--audit-steady-state"],
            ["--export-chaos-scorecard"],
        ]

        for flag_set in flags:
            proc = subprocess.run(
                [sys.executable, str(engine_script)] + flag_set,
                capture_output=True,
                text=True,
                timeout=15,
            )
            assert proc.returncode == 0, f"CLI command failed with {flag_set}: {proc.stderr}"
            assert "DevSuperSuite" in proc.stdout

    def test_11_strict_brand_anonymity_under_devsupersuite(self):
        """Enforces absolute brand anonymity under DevSuperSuite Security & Compliance."""
        target_files = [
            REPO_ROOT / "services" / "enterprise_chaos_resilience_engine.py",
            REPO_ROOT / "services" / "reports" / "chaos_engineering_resilience_scorecard.md",
            REPO_ROOT / "services" / "reports" / "chaos_experiment_suite.json",
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

            # Scrub safe timestamps, ISO dates, and GUIDs before phone regex
            scrubbed = re.sub(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}", "", content)
            scrubbed = re.sub(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", "", scrubbed)
            scrubbed = re.sub(r"\b1\d{9}\b", "", scrubbed)

            phone_matches = phone_pattern.findall(scrubbed)
            assert not phone_matches, (
                f"Brand anonymity violation: Found phone pattern in {file_path.name}: {phone_matches}"
            )

            # Confirm corporate identity
            assert "DevSuperSuite" in content, (
                f"Missing corporate brand DevSuperSuite in {file_path.name}"
            )
