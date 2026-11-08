#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Enterprise Service Mesh Test Suite
Reference: DSS-TEST-MESH-CONTROLLER-2026
Classification: Zero-Trust Multi-Cluster Federation & Resiliency Verification
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
K8S_MESH_DIR = DEPLOYMENT_DIR / "k8s" / "mesh"

VS_FILE = K8S_MESH_DIR / "istio_virtualservice.yaml"
DR_FILE = K8S_MESH_DIR / "istio_destinationrule.yaml"
GW_FILE = K8S_MESH_DIR / "istio_gateway.yaml"
GUIDE_FILE = SERVICES_DIR / "enterprise_service_mesh_guide.md"
REPORT_FILE = REPORTS_DIR / "service_mesh_architecture_report.md"

sys.path.insert(0, str(SERVICES_DIR))
from enterprise_service_mesh_traffic_controller import (
    ServiceMeshManifestGenerator,
    CanaryRolloutController,
    CircuitBreakerAuditor,
    MultiClusterFederationTopology,
    run_canary_simulation,
    export_service_mesh_guide,
    export_service_mesh_report,
    MAX_5XX_ERROR_RATE_THRESHOLD,
    MAX_P99_LATENCY_MS_THRESHOLD
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Mesh Manifest Schema & Routing Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_virtualservice_manifest_schema_and_routes():
    """Validates Istio VirtualService syntax, header override match, and weighted routes."""
    vs_dict = ServiceMeshManifestGenerator.get_virtual_service_dict(stable_weight=95, canary_weight=5)
    assert vs_dict["apiVersion"] == "networking.istio.io/v1beta1"
    assert vs_dict["kind"] == "VirtualService"
    assert vs_dict["metadata"]["name"] == "devsupersuite-ast-proxy"

    http_rules = vs_dict["spec"]["http"]
    assert len(http_rules) == 2

    # Rule 1: Header Override
    override_rule = http_rules[0]
    assert override_rule["name"] == "internal-canary-override"
    assert override_rule["match"][0]["headers"]["x-canary-override"]["exact"] == "canary"
    assert override_rule["route"][0]["destination"]["subset"] == "canary"
    assert override_rule["route"][0]["weight"] == 100

    # Rule 2: Weighted Split
    weighted_rule = http_rules[1]
    assert weighted_rule["name"] == "weighted-canary-split"
    routes = weighted_rule["route"]
    assert len(routes) == 2

    stable_route = next(r for r in routes if r["destination"]["subset"] == "stable")
    canary_route = next(r for r in routes if r["destination"]["subset"] == "canary")
    assert stable_route["weight"] == 95
    assert canary_route["weight"] == 5
    assert stable_route["weight"] + canary_route["weight"] == 100

    # Retries and Timeout
    assert weighted_rule["timeout"] == "10s"
    assert weighted_rule["retries"]["attempts"] == 3


def test_destinationrule_mtls_and_circuit_breaker():
    """Verifies DestinationRule mutual TLS 1.3 and outlier detection thresholds."""
    dr_dict = ServiceMeshManifestGenerator.get_destination_rule_dict()
    assert dr_dict["apiVersion"] == "networking.istio.io/v1beta1"
    assert dr_dict["kind"] == "DestinationRule"

    tp = dr_dict["spec"]["trafficPolicy"]
    # Mutual TLS
    assert tp["tls"]["mode"] == "ISTIO_MUTUAL"
    assert tp["tls"]["minProtocolVersion"] == "TLSV1_3"

    # Outlier Detection (<500ms ejection upon 3 consecutive 5xx errors)
    outlier = tp["outlierDetection"]
    assert outlier["consecutive5xxErrors"] == 3
    assert outlier["baseEjectionTime"] == "30s"
    assert outlier["maxEjectionPercent"] == 50

    # Subsets
    subsets = dr_dict["spec"]["subsets"]
    subset_names = [s["name"] for s in subsets]
    assert "stable" in subset_names
    assert "canary" in subset_names


def test_gateway_tls13_and_federation_port():
    """Verifies Gateway TLS 1.3 edge termination and multi-cluster east-west port 15443."""
    gw_dict = ServiceMeshManifestGenerator.get_gateway_dict()
    assert gw_dict["apiVersion"] == "networking.istio.io/v1beta1"
    assert gw_dict["kind"] == "Gateway"

    servers = gw_dict["spec"]["servers"]
    assert len(servers) == 2

    # Port 443 Ingress
    s443 = next(s for s in servers if s["port"]["number"] == 443)
    assert s443["tls"]["mode"] == "MUTUAL"
    assert s443["tls"]["minProtocolVersion"] == "TLSV1_3"

    # Port 15443 Multi-Cluster Federation
    s15443 = next(s for s in servers if s["port"]["number"] == 15443)
    assert s15443["port"]["name"] == "tls-federation-eastwest"
    assert s15443["tls"]["mode"] == "AUTO_PASSTHROUGH"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Circuit Breaker Auditor Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_circuit_breaker_auditor_compliance_pass():
    """Tests that a standard production DestinationRule passes all circuit breaking checks."""
    dr_dict = ServiceMeshManifestGenerator.get_destination_rule_dict()
    res = CircuitBreakerAuditor.audit_destination_rule(dr_dict)
    assert res["is_compliant"] is True
    assert res["total_findings"] == 4
    for f in res["findings"]:
        assert f["status"] == "PASS"


def test_circuit_breaker_auditor_compliance_fail():
    """Tests that deficient outlier parameters fail the audit."""
    dr_dict = ServiceMeshManifestGenerator.get_destination_rule_dict()
    # Tamper parameters: 10 consecutive errors, 10s ejection, 90% ejection limit, non-mTLS
    dr_dict["spec"]["trafficPolicy"]["outlierDetection"]["consecutive5xxErrors"] = 10
    dr_dict["spec"]["trafficPolicy"]["outlierDetection"]["baseEjectionTime"] = "10s"
    dr_dict["spec"]["trafficPolicy"]["outlierDetection"]["maxEjectionPercent"] = 90
    dr_dict["spec"]["trafficPolicy"]["tls"]["mode"] = "DISABLE"

    res = CircuitBreakerAuditor.audit_destination_rule(dr_dict)
    assert res["is_compliant"] is False
    assert any(f["status"] == "FAIL" and "Consecutive" in f["invariant"] for f in res["findings"])
    assert any(f["status"] == "FAIL" and "Base Ejection" in f["invariant"] for f in res["findings"])
    assert any(f["status"] == "FAIL" and "Max Ejection" in f["invariant"] for f in res["findings"])
    assert any(f["status"] == "FAIL" and "Zero-Trust" in f["invariant"] for f in res["findings"])


# ─────────────────────────────────────────────────────────────────────────────
# 3. Canary Progression & Automated Rollback Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_canary_state_machine_ideal_progression():
    """Tests full progressive promotion through 95/5 -> 80/20 -> 50/50 -> 0/100."""
    controller = CanaryRolloutController()
    t0 = datetime(2026, 11, 8, 12, 0, 0, tzinfo=timezone.utc)

    # Stage 1: 95/5
    r1 = controller.evaluate_and_advance(0.00001, 15.0, t0 + timedelta(minutes=5))
    assert r1["stage_index"] == 1
    assert r1["stable_weight"] == 95
    assert r1["canary_weight"] == 5
    assert r1["status"] == "InCanaryProgress"

    # Stage 2: 80/20
    r2 = controller.evaluate_and_advance(0.00002, 16.0, t0 + timedelta(minutes=15))
    assert r2["stage_index"] == 2
    assert r2["stable_weight"] == 80
    assert r2["canary_weight"] == 20

    # Stage 3: 50/50
    r3 = controller.evaluate_and_advance(0.00003, 18.0, t0 + timedelta(minutes=30))
    assert r3["stage_index"] == 3
    assert r3["stable_weight"] == 50
    assert r3["canary_weight"] == 50

    # Stage 4: 0/100 Promotion
    r4 = controller.evaluate_and_advance(0.00001, 14.0, t0 + timedelta(minutes=45))
    assert r4["stage_index"] == 4
    assert r4["stable_weight"] == 0
    assert r4["canary_weight"] == 100
    assert r4["action"] == "PROMOTED_TO_STABLE"
    assert r4["status"] == "Completed"
    assert controller.stable_version == "v2026.3.0"


def test_canary_automated_rollback_on_5xx_spike():
    """Tests emergency rollback when 5xx error rate exceeds 0.01% threshold."""
    controller = CanaryRolloutController()
    t0 = datetime(2026, 11, 8, 12, 0, 0, tzinfo=timezone.utc)

    # Stage 1: Normal 95/5
    controller.evaluate_and_advance(0.00001, 15.0, t0 + timedelta(minutes=5))

    # Stage 2: Spike to 0.05% (0.0005 > 0.0001)
    res = controller.evaluate_and_advance(0.0005, 18.0, t0 + timedelta(minutes=15))
    assert controller.is_rolled_back is True
    assert res["action"] == "EMERGENCY_ROLLBACK"
    assert res["status"] == "RolledBack"
    assert res["stable_weight"] == 100
    assert res["canary_weight"] == 0
    assert "5xx error rate" in controller.rollback_reason


def test_canary_automated_rollback_on_p99_latency_spike():
    """Tests emergency rollback when p99 latency exceeds 250ms threshold."""
    controller = CanaryRolloutController()
    t0 = datetime(2026, 11, 8, 12, 0, 0, tzinfo=timezone.utc)

    # Stage 1: Normal 95/5
    controller.evaluate_and_advance(0.00001, 20.0, t0 + timedelta(minutes=5))

    # Stage 2: Latency spike to 285ms (> 250ms)
    res = controller.evaluate_and_advance(0.00001, 285.0, t0 + timedelta(minutes=15))
    assert controller.is_rolled_back is True
    assert res["action"] == "EMERGENCY_ROLLBACK"
    assert res["status"] == "RolledBack"
    assert res["stable_weight"] == 100
    assert res["canary_weight"] == 0
    assert "p99 latency" in controller.rollback_reason


# ─────────────────────────────────────────────────────────────────────────────
# 4. Multi-Cluster Federation & Exporters Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_multi_cluster_federation_topology():
    """Verifies multi-cluster federation topology across AWS, GCP, and On-Prem SCIF."""
    topo = MultiClusterFederationTopology.get_federation_topology()
    assert topo["mesh_federation_id"] == "dss-global-federation-2026"
    assert topo["gateway_port"] == 15443

    clusters = topo["clusters"]
    assert len(clusters) == 3

    providers = [c["provider"] for c in clusters]
    assert any("AWS" in p for p in providers)
    assert any("Google" in p or "GCP" in p for p in providers)
    assert any("OpenShift" in p or "SCIF" in p for p in providers)

    for c in clusters:
        assert c["east_west_gateway_port"] == 15443
        assert len(c["workload_identities"]) > 0
        assert c["workload_identities"][0].startswith("spiffe://")


def test_simulation_runner_and_exporters():
    """Tests full canary simulation runner and documentation generation."""
    sim_res = run_canary_simulation()
    assert sim_res["healthy_run"]["final_status"] == "Completed"
    assert sim_res["anomaly_run"]["final_status"] == "RolledBack"

    # Export guide and report
    guide_path = export_service_mesh_guide()
    dr_dict = ServiceMeshManifestGenerator.get_destination_rule_dict()
    audit_res = CircuitBreakerAuditor.audit_destination_rule(dr_dict)
    fed_topo = MultiClusterFederationTopology.get_federation_topology()
    report_path = export_service_mesh_report(sim_res, audit_res, fed_topo)

    assert guide_path.exists()
    assert report_path.exists()
    assert "DSS-SERVICE-MESH-RUNBOOK-2026" in guide_path.read_text(encoding="utf-8")
    assert "DSS-MESH-REPORT-2026-V1" in report_path.read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Brand Anonymity Invariants Test
# ─────────────────────────────────────────────────────────────────────────────

def test_brand_anonymity_invariants():
    """Asserts 100% Brand Anonymity across all newly authored service mesh artifacts."""
    files_to_check = [
        SERVICES_DIR / "enterprise_service_mesh_traffic_controller.py",
        GUIDE_FILE,
        REPORT_FILE,
        VS_FILE,
        DR_FILE,
        GW_FILE
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
    """Tests execution of the service mesh traffic controller CLI across all mandatory flags."""
    flags_to_test = [
        ["--generate-mesh-manifests"],
        ["--simulate-canary-rollout"],
        ["--audit-circuit-breakers"],
        ["--export-mesh-bundle"],
        ["--summary"]
    ]

    engine_script = SERVICES_DIR / "enterprise_service_mesh_traffic_controller.py"

    for flag_list in flags_to_test:
        cmd = [sys.executable, str(engine_script)] + flag_list
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, f"CLI command failed with code {proc.returncode}: {proc.stderr}"
        assert "DevSuperSuite" in proc.stdout
