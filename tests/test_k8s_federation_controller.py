#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Kubernetes Multi-Cluster Federation Test Suite
Reference: DSS-TEST-FEDERATION-CONTROLLER-2026
Classification: Cross-Cloud Sovereign Service Mesh Ingress & Multi-Cluster Routing
Contact: DevSuperSuite Solutions Architecture (solutions@devsupersuite.com)
═══════════════════════════════════════════════════════════════════════════════
"""

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = REPO_ROOT / "services"
REPORTS_DIR = SERVICES_DIR / "reports"
DEPLOYMENT_DIR = REPO_ROOT / "deployment"
K8S_FEDERATION_DIR = DEPLOYMENT_DIR / "k8s" / "federation"

MCI_FILE = K8S_FEDERATION_DIR / "multi_cluster_ingress_spec.yaml"
EXPORT_FILE = K8S_FEDERATION_DIR / "federation_service_export.yaml"
GUIDE_FILE = SERVICES_DIR / "enterprise_multi_cluster_federation_guide.md"
REPORT_FILE = REPORTS_DIR / "multi_cluster_federation_architecture_report.md"

sys.path.insert(0, str(SERVICES_DIR))
from enterprise_k8s_federation_controller import (
    MultiClusterFederationController,
    ClusterEndpoint,
    FederationManifestGenerator,
    run_federation_simulation,
    export_federation_guide,
    export_federation_report,
    PUBLIC_INGRESS_HOST,
    GLOBAL_FQDN
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Endpoint Discovery & Model Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_endpoint_discovery_multi_cloud():
    """Validates endpoint discovery across AWS EKS, GCP GKE, and Azure AKS."""
    controller = MultiClusterFederationController()
    eps = controller.discover_endpoints()
    assert len(eps) == 3

    providers = [ep["cloud_provider"] for ep in eps]
    assert any("AWS" in p for p in providers)
    assert any("Google" in p for p in providers)
    assert any("Azure" in p for p in providers)

    for ep in eps:
        assert ep["healthy"] is True
        assert ep["observed_latency_ms"] > 0
        assert ep["spiffe_id"].startswith("spiffe://devsupersuite.io/")


def test_dynamic_latency_weight_calculation():
    """Verifies that lowest latency clusters receive the largest traffic allocation."""
    controller = MultiClusterFederationController()
    weights = controller.recalculate_latency_weights()

    assert sum(weights.values()) == 100
    # EKS has lowest latency (14.5ms) -> highest weight
    assert weights["eks-us-east-1"] > weights["gke-us-central1"]
    # GKE (28.2ms) -> higher weight than AKS (75ms)
    assert weights["gke-us-central1"] > weights["aks-westeurope-1"]


# ─────────────────────────────────────────────────────────────────────────────
# 2. Health Probing & Sub-Second Failover Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_sub_second_probe_failure_and_failover():
    """Tests that 3 consecutive failed probes triggers sub-second failover."""
    controller = MultiClusterFederationController()

    # Failures 1 and 2
    r1 = controller.record_probe_result("eks-us-east-1", success=False)
    assert r1["healthy"] is True
    assert r1["consecutive_failures"] == 1

    r2 = controller.record_probe_result("eks-us-east-1", success=False)
    assert r2["healthy"] is True
    assert r2["consecutive_failures"] == 2

    # Failure 3 -> Triggers failover
    r3 = controller.record_probe_result("eks-us-east-1", success=False)
    assert r3["healthy"] is False
    assert r3["consecutive_failures"] == 3
    assert r3["current_weight"] == 0

    # Remaining clusters absorb 100% of traffic
    active_weights = {k: ep.weight for k, ep in controller.endpoints.items() if ep.healthy}
    assert sum(active_weights.values()) == 100
    assert "eks-us-east-1" not in active_weights


def test_endpoint_recovery_and_traffic_rebalance():
    """Tests that recovered endpoints re-enter routing pool smoothly."""
    controller = MultiClusterFederationController()
    # Mark EKS as down
    controller.record_probe_result("eks-us-east-1", success=False)
    controller.record_probe_result("eks-us-east-1", success=False)
    controller.record_probe_result("eks-us-east-1", success=False)
    assert controller.endpoints["eks-us-east-1"].healthy is False

    # Recover
    rec = controller.record_probe_result("eks-us-east-1", success=True, latency_ms=15.0)
    assert rec["healthy"] is True
    assert rec["consecutive_failures"] == 0

    weights = controller.recalculate_latency_weights()
    assert sum(weights.values()) == 100
    assert weights["eks-us-east-1"] > 50


def test_zero_downtime_cluster_maintenance_drain():
    """Verifies graceful maintenance draining drops weight to 0 while maintaining health."""
    controller = MultiClusterFederationController()
    res = controller.initiate_zero_downtime_drain("gke-us-central1")

    assert res["draining"] is True
    assert controller.endpoints["gke-us-central1"].weight == 0

    # Remaining clusters sum to 100
    eligible_weights = [ep.weight for ep in controller.endpoints.values() if not ep.draining and ep.healthy]
    assert sum(eligible_weights) == 100


# ─────────────────────────────────────────────────────────────────────────────
# 3. Declarative Manifest Schema Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_gateway_api_multi_cluster_ingress_schema():
    """Validates Gateway API multi-cluster ingress specification."""
    mci_dict = FederationManifestGenerator.get_multi_cluster_ingress_dict()
    assert mci_dict["apiVersion"] == "gateway.networking.k8s.io/v1"
    assert mci_dict["kind"] == "Gateway"
    assert mci_dict["metadata"]["name"] == "devsupersuite-cross-cloud-gateway"

    listeners = mci_dict["spec"]["listeners"]
    assert len(listeners) == 2

    # Port 443 Ingress
    l443 = next(l for l in listeners if l["port"] == 443)
    assert l443["hostname"] == PUBLIC_INGRESS_HOST
    assert l443["tls"]["mode"] == "Terminate"

    # Port 8443 Cross-cluster mTLS
    l8443 = next(l for l in listeners if l["port"] == 8443)
    assert l8443["tls"]["mode"] == "Passthrough"


def test_multicluster_service_export_import_schema():
    """Validates Multi-Cluster Services ServiceExport and ServiceImport definitions."""
    mcs_docs = FederationManifestGenerator.get_service_export_import_dict()
    assert len(mcs_docs) == 2

    export_doc = mcs_docs[0]
    import_doc = mcs_docs[1]

    assert export_doc["kind"] == "ServiceExport"
    assert export_doc["metadata"]["name"] == "devsupersuite-ast-proxy"

    assert import_doc["kind"] == "ServiceImport"
    assert import_doc["spec"]["type"] == "ClusterSetIP"
    ports = [p["port"] for p in import_doc["spec"]["ports"]]
    assert 443 in ports
    assert 8443 in ports


# ─────────────────────────────────────────────────────────────────────────────
# 4. Simulation Runner & Exporters Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_simulation_runner_and_exporters():
    """Runs full federation simulation and verifies guide and report file exports."""
    sim_res = run_federation_simulation()
    assert sim_res["sub_second_failover_verified"] is True
    assert len(sim_res["events"]) >= 3

    # Export guide and report
    guide_path = export_federation_guide()
    report_path = export_federation_report(sim_res)

    assert guide_path.exists()
    assert report_path.exists()
    assert "DSS-FEDERATION-RUNBOOK-2026" in guide_path.read_text(encoding="utf-8")
    assert "DSS-FEDERATION-REPORT-2026-V1" in report_path.read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Brand Anonymity Invariants Test
# ─────────────────────────────────────────────────────────────────────────────

def test_brand_anonymity_invariants():
    """Asserts 100% Brand Anonymity across all newly authored federation artifacts."""
    files_to_check = [
        SERVICES_DIR / "enterprise_k8s_federation_controller.py",
        GUIDE_FILE,
        REPORT_FILE,
        MCI_FILE,
        EXPORT_FILE
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
# 6. CLI Execution Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_cli_execution_all_flags():
    """Tests execution of the federation controller CLI across all mandatory flags."""
    flags_to_test = [
        ["--discover-endpoints"],
        ["--benchmark-latency-routing"],
        ["--simulate-failover"],
        ["--export-federation-bundle"],
        ["--summary"]
    ]

    engine_script = SERVICES_DIR / "enterprise_k8s_federation_controller.py"

    for flag_list in flags_to_test:
        cmd = [sys.executable, str(engine_script)] + flag_list
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, f"CLI command failed with code {proc.returncode}: {proc.stderr}"
        assert "DevSuperSuite" in proc.stdout
