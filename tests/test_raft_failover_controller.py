#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Multi-Region Raft Consensus & Failover Test Suite
Reference: DSS-TEST-RAFT-FAILOVER-2026
Classification: Sovereign Multi-Region Active-Active Consensus & Failover
Contact: DevSuperSuite Solutions Architecture (solutions@devsupersuite.com)
═══════════════════════════════════════════════════════════════════════════════
"""

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = REPO_ROOT / "services"
REPORTS_DIR = SERVICES_DIR / "reports"
DEPLOYMENT_DIR = REPO_ROOT / "deployment"
K8S_DB_DIR = DEPLOYMENT_DIR / "k8s" / "database"

TOPOLOGY_FILE = K8S_DB_DIR / "multi_region_cluster_topology.json"
GUIDE_FILE = SERVICES_DIR / "enterprise_database_replication_guide.md"
REPORT_FILE = REPORTS_DIR / "raft_failover_architecture_report.md"

sys.path.insert(0, str(SERVICES_DIR))
from enterprise_raft_failover_controller import (
    RaftConsensusCluster,
    RaftRole,
    WALEntry,
    export_cluster_topology,
    export_replication_guide,
    export_failover_report
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Cluster Quorum & Topology Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_cluster_initialization_and_quorum_calculation():
    """Validates cluster node initialization and quorum threshold floor(N/2) + 1."""
    # 3-node cluster -> Quorum 2
    c3 = RaftConsensusCluster(node_count=3)
    assert len(c3.nodes) == 3
    assert c3.quorum_size == 2
    for node in c3.nodes.values():
        assert node.role == RaftRole.FOLLOWER
        assert node.current_term == 0

    # 5-node cluster -> Quorum 3
    c5 = RaftConsensusCluster(node_count=5)
    assert len(c5.nodes) == 5
    assert c5.quorum_size == 3


def test_raft_leader_election_success():
    """Tests standard election where candidate gains quorum votes and becomes leader."""
    cluster = RaftConsensusCluster(node_count=3)
    candidate_id = "dss-db-us-east-01"

    success, votes = cluster.start_election(candidate_id)
    assert success is True
    assert votes == 3  # All reachable nodes voted
    assert cluster.current_leader_id == candidate_id

    leader = cluster.nodes[candidate_id]
    assert leader.role == RaftRole.LEADER
    assert leader.current_term == 1
    assert leader.fencing_token == 1001


# ─────────────────────────────────────────────────────────────────────────────
# 2. Monotonic Fencing Token & Split-Brain Defense Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_fencing_token_monotonic_increments():
    """Verifies that consecutive term transitions strictly increment the fencing token."""
    cluster = RaftConsensusCluster(node_count=3)
    c1 = "dss-db-us-east-01"
    c2 = "dss-db-eu-central-01"
    c3 = "dss-db-ap-south-01"

    # Election 1
    cluster.start_election(c1)
    tok1 = cluster.global_fencing_token
    assert tok1 == 1001

    # Election 2
    cluster.start_election(c2)
    tok2 = cluster.global_fencing_token
    assert tok2 == 1002
    assert tok2 > tok1

    # Election 3
    cluster.start_election(c3)
    tok3 = cluster.global_fencing_token
    assert tok3 == 1003
    assert tok3 > tok2


def test_split_brain_stale_fencing_token_rejection():
    """Guarantees stale fencing token writes from a zombie leader are rejected."""
    cluster = RaftConsensusCluster(node_count=3)
    cluster.start_election("dss-db-us-east-01")  # Token 1001
    cluster.start_election("dss-db-eu-central-01")  # Token 1002

    # Attempt write with stale token 1001
    success, entry, msg = cluster.replicate_wal_entry(
        key="customer_balance",
        value={"account_id": "ACC-99", "balance": 500000},
        fencing_token=1001  # Stale!
    )
    assert success is False
    assert entry is None
    assert "Stale fencing token" in msg


# ─────────────────────────────────────────────────────────────────────────────
# 3. WAL Replication & Vector Clock Conflict Resolution Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_cross_region_wal_replication_and_commit():
    """Tests synchronous WAL streaming to majority quorum with valid fencing token."""
    cluster = RaftConsensusCluster(node_count=3)
    cluster.start_election("dss-db-us-east-01")
    active_token = cluster.global_fencing_token

    success, entry, msg = cluster.replicate_wal_entry(
        key="session_auth_token",
        value={"session_id": "SESS-10294", "status": "ACTIVE"},
        fencing_token=active_token
    )
    assert success is True
    assert entry is not None
    assert entry.lsn == 1
    assert "Committed" in msg

    leader = cluster.nodes["dss-db-us-east-01"]
    assert leader.commit_index == 1
    assert len(leader.wal_log) == 1

    # Verify followers received the entry
    follower = cluster.nodes["dss-db-eu-central-01"]
    assert follower.commit_index == 1
    assert len(follower.wal_log) == 1
    assert follower.wal_log[0].key == "session_auth_token"


def test_vector_clock_causality_and_conflict_resolution():
    """Validates vector clock partial order dominance and deterministic tie-breaking."""
    # Case 1: Dominance (Entry A is strictly causally newer than Entry B)
    entry_a = WALEntry(
        lsn=5, term=2, key="item_count", value=100,
        vector_clock={"us-east": 3, "eu-central": 2, "ap-south": 1}
    )
    entry_b = WALEntry(
        lsn=4, term=2, key="item_count", value=95,
        vector_clock={"us-east": 2, "eu-central": 2, "ap-south": 1}
    )
    resolved_1 = RaftConsensusCluster.resolve_vector_clock_conflict(entry_a, entry_b)
    assert resolved_1 == entry_a

    # Case 2: Concurrent/Divergent updates -> tie-break on higher term/LSN
    entry_c1 = WALEntry(
        lsn=6, term=3, key="pricing_rule", value="ENTERPRISE",
        vector_clock={"us-east": 4, "eu-central": 1, "ap-south": 0}
    )
    entry_c2 = WALEntry(
        lsn=6, term=2, key="pricing_rule", value="STANDARD",
        vector_clock={"us-east": 1, "eu-central": 3, "ap-south": 0}
    )
    resolved_2 = RaftConsensusCluster.resolve_vector_clock_conflict(entry_c1, entry_c2)
    assert resolved_2 == entry_c1  # Higher term wins


# ─────────────────────────────────────────────────────────────────────────────
# 4. Network Partition Chaos & Sub-Second Failover Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_network_partition_and_subsecond_failover():
    """Tests network partition of leader triggering sub-second failover in majority."""
    cluster = RaftConsensusCluster(node_count=3)
    cluster.start_election("dss-db-us-east-01")
    old_leader_id = "dss-db-us-east-01"

    # Inject partition isolating current leader
    res = cluster.inject_network_partition(old_leader_id)
    assert res["status"] == "FAILOVER_EXECUTED"
    assert res["isolated_leader"] == old_leader_id
    assert res["new_leader"] != old_leader_id
    assert res["sub_second_failover"] is True
    assert res["failover_latency_ms"] <= 500
    assert res["new_fencing_token"] == 1002

    new_leader = cluster.nodes[res["new_leader"]]
    assert new_leader.role == RaftRole.LEADER


def test_partition_reconciliation_and_zombie_stepdown():
    """Tests partition healing where old leader steps down and resyncs WAL."""
    cluster = RaftConsensusCluster(node_count=3)
    cluster.start_election("dss-db-us-east-01")

    # Isolate us-east-01 -> eu-central-01 elected
    cluster.inject_network_partition("dss-db-us-east-01")
    new_leader_id = cluster.current_leader_id
    assert new_leader_id == "dss-db-eu-central-01"

    # Commit a write on new leader
    cluster.replicate_wal_entry("status", "ACTIVE", cluster.global_fencing_token)

    # Heal network partition
    heal_res = cluster.reconcile_network_partition()
    assert heal_res["status"] == "PARTITION_HEALED"
    assert heal_res["reintegrated_node"] == "dss-db-us-east-01"

    # Old leader has stepped down to FOLLOWER and caught up on WAL
    old_node = cluster.nodes["dss-db-us-east-01"]
    assert old_node.role == RaftRole.FOLLOWER
    assert old_node.commit_index == 1
    assert len(old_node.wal_log) == 1


# ─────────────────────────────────────────────────────────────────────────────
# 5. Client Routing & Topology Artifact Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_dynamic_client_routing_table_updates():
    """Verifies client routing table dynamically reflects active leader and read replicas."""
    cluster = RaftConsensusCluster(node_count=3)
    cluster.start_election("dss-db-us-east-01")

    rt = cluster.get_dynamic_routing_table()
    assert rt["active_leader_id"] == "dss-db-us-east-01"
    assert "db.us-east.internal.devsupersuite.io" in rt["active_primary_endpoint"]
    assert rt["fencing_token"] == 1001
    assert len(rt["read_replicas"]) == 2
    for rep in rt["read_replicas"]:
        assert rep["status"] == "UP"


def test_topology_and_guide_export_integrity():
    """Tests JSON topology export, replication operations guide, and failover report."""
    cluster = RaftConsensusCluster(node_count=3)
    cluster.start_election("dss-db-us-east-01")

    topo_path = export_cluster_topology(cluster)
    guide_path = export_replication_guide()
    report_path = export_failover_report(cluster)

    assert topo_path.exists()
    assert guide_path.exists()
    assert report_path.exists()

    topo_data = json.loads(topo_path.read_text(encoding="utf-8"))
    assert topo_data["cluster_name"] == "dss-multi-region-database-fabric"
    assert len(topo_data["nodes"]) == 3

    assert "DSS-RAFT-REPLICATION-RUNBOOK-2026" in guide_path.read_text(encoding="utf-8")
    assert "DSS-RAFT-REPORT-2026-V1" in report_path.read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# 6. Brand Anonymity Invariants Test
# ─────────────────────────────────────────────────────────────────────────────

def test_brand_anonymity_invariants():
    """Asserts 100% Brand Anonymity across all newly authored database replication artifacts."""
    files_to_check = [
        SERVICES_DIR / "enterprise_raft_failover_controller.py",
        GUIDE_FILE,
        REPORT_FILE,
        TOPOLOGY_FILE
    ]

    for f in files_to_check:
        if not f.exists():
            continue
        content = f.read_text(encoding="utf-8")

        # Must mention authorized entities
        assert "DevSuperSuite" in content or "devsupersuite" in content
        assert "solutions@devsupersuite.com" in content

        # Must NOT contain forbidden personal identities or personal domains
        forbidden_terms = [
            "atpad", "Padhy", "Amrut", "amrut",
            "@gmail.com", "@yahoo.com", "@hotmail.com"
        ]
        for term in forbidden_terms:
            assert term not in content, f"Forbidden personal identity '{term}' found in {f.name}"


# ─────────────────────────────────────────────────────────────────────────────
# 7. CLI Execution Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_cli_execution_all_flags():
    """Tests execution of the Raft failover controller CLI across all mandatory flags."""
    flags_to_test = [
        ["--simulate-election", "--nodes", "3"],
        ["--inject-partition", "--isolated-node", "dss-db-us-east-01"],
        ["--trigger-failover", "--target-region", "eu-central"],
        ["--reconcile-partition"],
        ["--export-cluster-topology"],
        ["--summary"]
    ]

    engine_script = SERVICES_DIR / "enterprise_raft_failover_controller.py"

    for flag_list in flags_to_test:
        cmd = [sys.executable, str(engine_script)] + flag_list
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, f"CLI command failed with code {proc.returncode}: {proc.stderr}"
        assert "DevSuperSuite" in proc.stdout
