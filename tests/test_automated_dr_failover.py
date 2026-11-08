"""
═══════════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Automated Disaster Recovery Failover Gate Test Suite
Document Ref: DSS-TEST-DR-FAILOVER-2026-V1
Compliance Standards: SOC 2 Type II (CC7.3, CC7.4), ISO 27001:2022 (A.12.3, A.17.1, A.17.2)

Verifies:
1. Multi-region sovereign topology initialization (Primary, Warm Standby, Air-Gap SCIF).
2. RPO replication lag boundary enforcement (< 1.0 second ceiling).
3. RTO automated failover sequence execution bounds (< 60.0 seconds ceiling).
4. Chaos Fault 1: Primary Region Network Partition & STONITH split-brain prevention.
5. Chaos Fault 2: KMS Key Rotation Outage & Local Enclave DEK Fallback.
6. Chaos Fault 3: Primary Database Crash & Zero-Loss Read Replica Promotion.
7. Chaos Fault 4: Route53 / GeoDNS Latency Routing Blackhole & Weight Flip.
8. Evidence binder generation (Markdown & JSON telemetry).
9. CLI flags and end-to-end execution.
10. Strict 100% Brand Anonymity Enforcement under DevSuperSuite Information Security.
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

from automated_dr_failover_gate import (
    AutomatedDRFailoverGate,
    ChaosFaultResult,
    ChaosFaultType,
    QuorumValidator,
    RegionHealth,
    RegionNode,
    RegionRole,
    RPO_SLA_CEILING_MS,
    RTO_SLA_CEILING_SEC,
)


class TestAutomatedDRFailoverGate(unittest.TestCase):
    """
    Test suite verifying DevSuperSuite Automated Disaster Recovery & RPO/RTO Failover Gate.
    """

    def setUp(self):
        self.engine = AutomatedDRFailoverGate()

    def test_01_multi_region_topology_initialization(self):
        """
        Verify multi-region topology boots with 3 sovereign nodes:
        - Primary Active: us-east-1 (100% DNS weight, 0ms lag)
        - Secondary Warm Standby: us-west-2 (0% DNS weight, ~120ms lag)
        - Tertiary Cold Standby: eu-central-1 (0% DNS weight, ~450ms lag)
        """
        self.assertEqual(len(self.engine.regions), 3)

        primary = next(r for r in self.engine.regions if r.region_id == "us-east-1")
        secondary = next(r for r in self.engine.regions if r.region_id == "us-west-2")
        tertiary = next(r for r in self.engine.regions if r.region_id == "eu-central-1")

        self.assertEqual(primary.role, RegionRole.PRIMARY_ACTIVE)
        self.assertEqual(primary.health, RegionHealth.HEALTHY)
        self.assertEqual(primary.dns_weight, 100)
        self.assertEqual(primary.replication_lag_ms, 0.0)
        self.assertEqual(primary.db_status, "READ_WRITE_MASTER")

        self.assertEqual(secondary.role, RegionRole.SECONDARY_WARM_STANDBY)
        self.assertEqual(secondary.health, RegionHealth.HEALTHY)
        self.assertEqual(secondary.dns_weight, 0)
        self.assertLess(secondary.replication_lag_ms, RPO_SLA_CEILING_MS)
        self.assertEqual(secondary.db_status, "READ_REPLICA")

        self.assertEqual(tertiary.role, RegionRole.TERTIARY_COLD_STANDBY)
        self.assertTrue(tertiary.quorum_vote)

    def test_02_rpo_replication_lag_boundary_audit(self):
        """
        Verify RPO SLA compliance (< 1000ms):
        - Nominal state: 120ms lag -> COMPLIANT / PASS
        - Degraded state: 1500ms lag -> NON_COMPLIANT_BREACH / FAIL
        """
        # Nominal audit
        audit = self.engine.audit_rpo_rto_sla()
        self.assertEqual(audit["gate_decision"], "PASS")
        self.assertEqual(audit["rpo_metric"]["status"], "COMPLIANT")
        self.assertLess(audit["rpo_metric"]["measured_secondary_lag_ms"], RPO_SLA_CEILING_MS)

        # Breach condition: inject 1500ms lag into us-west-2
        secondary = next(r for r in self.engine.regions if r.region_id == "us-west-2")
        secondary.replication_lag_ms = 1500.0

        breach_audit = self.engine.audit_rpo_rto_sla()
        self.assertEqual(breach_audit["gate_decision"], "FAIL")
        self.assertEqual(breach_audit["rpo_metric"]["status"], "NON_COMPLIANT_BREACH")
        self.assertFalse(breach_audit["rpo_metric"]["compliant"])

    def test_03_rto_automated_failover_execution_bounds(self):
        """
        Verify that executing the 7-step automated failover completes within RTO SLA (< 60.0s).
        """
        failover_run = self.engine.execute_automated_failover_sequence("PRIMARY_DATACENTER_FIRE")

        self.assertEqual(failover_run["gate_decision"], "PASS")
        self.assertLess(failover_run["total_rto_sec"], RTO_SLA_CEILING_SEC)
        self.assertLess(failover_run["total_rto_sec"], 15.0)  # Measured baseline is ~11.45s
        self.assertEqual(failover_run["data_loss_records"], 0)
        self.assertTrue(failover_run["split_brain_prevented"])
        self.assertEqual(failover_run["active_primary_region"], "us-west-2")

        # Verify all 7 steps executed successfully
        self.assertEqual(len(failover_run["steps"]), 7)
        for step in failover_run["steps"]:
            self.assertEqual(step["status"], "SUCCESS")
            self.assertGreater(step["duration_ms"], 0.0)

    def test_04_chaos_fault_primary_network_partition(self):
        """
        Verify Fault 1: Primary Region Network Partition.
        - Raft quorum isolates us-east-1.
        - STONITH fencing enforced.
        - Split-brain strictly prevented.
        """
        result = self.engine.simulate_chaos_fault(ChaosFaultType.PRIMARY_NETWORK_PARTITION)

        self.assertEqual(result.status, "PASS")
        self.assertTrue(result.split_brain_prevented)
        self.assertEqual(result.data_loss_records, 0)
        self.assertLess(result.rto_measured_ms, RTO_SLA_CEILING_SEC * 1000.0)

        # Check post-fault state of isolated primary node
        fenced_node = next(r for r in self.engine.regions if r.region_id == "us-east-1")
        self.assertEqual(fenced_node.health, RegionHealth.FENCED)
        self.assertEqual(fenced_node.role, RegionRole.FENCED_OFFLINE)
        self.assertFalse(fenced_node.quorum_vote)

        # Check promoted secondary
        promoted_node = next(r for r in self.engine.regions if r.region_id == "us-west-2")
        self.assertEqual(promoted_node.role, RegionRole.PRIMARY_ACTIVE)
        self.assertEqual(promoted_node.dns_weight, 100)

    def test_05_chaos_fault_kms_rotation_outage(self):
        """
        Verify Fault 2: KMS HSM Key Rotation Outage.
        - Graceful fallback to cached envelope DEK in Hardware Enclave.
        - RPO = 0.0ms, zero transaction disruption.
        """
        result = self.engine.simulate_chaos_fault(ChaosFaultType.KMS_ROTATION_OUTAGE)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.rpo_measured_ms, 0.0)
        self.assertLess(result.rto_measured_ms, 2000.0)  # Near instantaneous fallback (< 2.0s)
        self.assertEqual(result.data_loss_records, 0)

        primary = next(r for r in self.engine.regions if r.region_id == "us-east-1")
        self.assertEqual(primary.kms_enclave_status, "FALLBACK_CACHED_DEK")

    def test_06_chaos_fault_database_crash_and_promotion(self):
        """
        Verify Fault 3: Primary Database Crash.
        - Primary database crashes.
        - Standby read replica in us-west-2 promoted to read-write master.
        - Zero record loss, RPO measured well below SLA ceiling (< 1000ms).
        """
        result = self.engine.simulate_chaos_fault(ChaosFaultType.PRIMARY_DATABASE_CRASH)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.data_loss_records, 0)
        self.assertLess(result.rpo_measured_ms, RPO_SLA_CEILING_MS)
        self.assertLess(result.rto_measured_ms, RTO_SLA_CEILING_SEC * 1000.0)

        secondary = next(r for r in self.engine.regions if r.region_id == "us-west-2")
        self.assertEqual(secondary.db_status, "READ_WRITE_MASTER")
        self.assertEqual(secondary.role, RegionRole.PRIMARY_ACTIVE)

    def test_07_chaos_fault_dns_routing_blackhole(self):
        """
        Verify Fault 4: Route53 / GeoDNS Latency Routing Blackhole.
        - Automated health check failure trips DNS weight flip: us-east-1=0, us-west-2=100.
        - Traffic rerouted with zero data loss.
        """
        result = self.engine.simulate_chaos_fault(ChaosFaultType.DNS_ROUTING_BLACKHOLE)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.data_loss_records, 0)
        self.assertLess(result.rto_measured_ms, 10000.0)  # Rerouted in < 10.0s

        primary = next(r for r in self.engine.regions if r.region_id == "us-east-1")
        secondary = next(r for r in self.engine.regions if r.region_id == "us-west-2")
        self.assertEqual(primary.dns_weight, 0)
        self.assertEqual(secondary.dns_weight, 100)

    def test_08_evidence_binder_and_json_generation(self):
        """
        Verify automated generation of Markdown evidence binder and JSON telemetry.
        """
        md_path, json_path = self.engine.generate_dr_evidence()

        self.assertTrue(md_path.exists())
        self.assertTrue(json_path.exists())

        # Inspect Markdown contents
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        self.assertIn("DevSuperSuite Tech Services", md_content)
        self.assertIn("SOC 2 Type II", md_content)
        self.assertIn("ISO 27001:2022", md_content)
        self.assertIn("RPO", md_content)
        self.assertIn("RTO", md_content)
        self.assertIn("infosec@devsupersuite.com", md_content)

        # Inspect JSON contents
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["organization"], "DevSuperSuite Tech Services")
        self.assertEqual(data["contact"], "DevSuperSuite Information Security (infosec@devsupersuite.com)")
        self.assertIn("sla_audit", data)
        self.assertIn("failover_simulation", data)
        self.assertEqual(len(data["chaos_engineering_matrix"]), 4)

    def test_09_cli_interface_execution(self):
        """
        Verify CLI invocation for `--summary`, `--audit-rpo-rto-sla`, and `--simulate-chaos-failover`.
        """
        cli_script = SERVICES_DIR / "automated_dr_failover_gate.py"

        # Test --summary
        res = subprocess.run(
            [sys.executable, str(cli_script), "--summary"],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("DevSuperSuite Automated Disaster Recovery", res.stdout)
        self.assertIn("Gate Decision", res.stdout)

        # Test --audit-rpo-rto-sla
        res2 = subprocess.run(
            [sys.executable, str(cli_script), "--audit-rpo-rto-sla"],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertEqual(res2.returncode, 0)
        self.assertIn("RPO/RTO SLA Audit Decision: PASS", res2.stdout)

        # Test --simulate-chaos-failover
        res3 = subprocess.run(
            [sys.executable, str(cli_script), "--simulate-chaos-failover"],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertEqual(res3.returncode, 0)
        self.assertIn("All 4 Chaos Scenarios Passed Invariant Checks.", res3.stdout)

    def test_10_strict_brand_anonymity_under_devsupersuite(self):
        """
        Strict Brand Anonymity Enforcement:
        - Inspects automated_dr_failover_gate.py, disaster_recovery_runbook.md, and generated reports.
        - Asserts ZERO personal names, ZERO personal emails (gmail/yahoo/outlook/hotmail), and ZERO personal phone numbers.
        - Confirms all attributions point to DevSuperSuite Official & infosec@devsupersuite.com.
        """
        files_to_check = [
            SERVICES_DIR / "automated_dr_failover_gate.py",
            SERVICES_DIR / "disaster_recovery_runbook.md",
            SERVICES_DIR / "reports" / "disaster_recovery_audit_report.md",
            SERVICES_DIR / "reports" / "disaster_recovery_audit.json",
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

            # Clean out hex digests and key IDs to avoid false phone matches
            clean_content = re.sub(r"[a-f0-9]{32,64}", "", content)
            clean_content = re.sub(r"KID-[A-Za-z0-9-]+", "", clean_content)

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
