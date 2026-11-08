#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Enterprise Kubernetes Operator Test Suite
Reference: DSS-TEST-K8S-OPERATOR-2026
Classification: Enterprise GitOps & Sovereign Air-Gap Kubernetes Automation
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
K8S_OPERATOR_DIR = DEPLOYMENT_DIR / "k8s" / "operator"

CRD_FILE = K8S_OPERATOR_DIR / "crd_devsupersuite_cluster.yaml"
RBAC_FILE = K8S_OPERATOR_DIR / "operator_rbac.yaml"
DEPLOY_FILE = K8S_OPERATOR_DIR / "operator_deployment.yaml"
GUIDE_FILE = SERVICES_DIR / "enterprise_k8s_operator_guide.md"
REPORT_FILE = REPORTS_DIR / "k8s_operator_architecture_report.md"

sys.path.insert(0, str(SERVICES_DIR))
from enterprise_k8s_operator_engine import (
    CRDManifestGenerator,
    RBACManifestGenerator,
    OperatorDeploymentGenerator,
    ReconciliationController,
    OperatorSimulationHarness,
    export_k8s_operator_guide,
    export_k8s_operator_report,
    NON_ROOT_UID,
    CRD_GROUP,
    CRD_KIND
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. CRD Schema & Version Validation Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_crd_schema_structure_and_versions():
    """Validates OpenAPI v3 CRD schema, multi-version declarations, and required properties."""
    crd_dict = CRDManifestGenerator.get_crd_dict()
    assert crd_dict["apiVersion"] == "apiextensions.k8s.io/v1"
    assert crd_dict["kind"] == "CustomResourceDefinition"
    assert crd_dict["metadata"]["name"] == f"devsupersuiteclusters.{CRD_GROUP}"

    spec = crd_dict["spec"]
    assert spec["group"] == CRD_GROUP
    assert spec["names"]["kind"] == CRD_KIND
    assert spec["scope"] == "Namespaced"

    version_names = [v["name"] for v in spec["versions"]]
    assert "v1alpha1" in version_names
    assert "v1beta1" in version_names

    v1beta1 = next(v for v in spec["versions"] if v["name"] == "v1beta1")
    assert v1beta1["storage"] is True
    assert v1beta1["served"] is True

    # Validate OpenAPI Schema tree
    schema = v1beta1["schema"]["openAPIV3Schema"]["properties"]["spec"]["properties"]
    assert "replicas" in schema
    assert "edition" in schema
    assert "version" in schema
    assert "astEngine" in schema
    assert "security" in schema
    assert "deploymentStrategy" in schema

    # Status schema
    status_schema = v1beta1["schema"]["openAPIV3Schema"]["properties"]["status"]["properties"]
    assert "phase" in status_schema
    assert "currentReplicas" in status_schema
    assert "astQueueDepth" in status_schema


def test_crd_yaml_rendering_integrity():
    """Verifies exported CRD YAML file is valid and re-parsable."""
    crd_yaml = CRDManifestGenerator.render_yaml()
    parsed = yaml.safe_load(crd_yaml)
    assert parsed["kind"] == "CustomResourceDefinition"
    assert parsed["spec"]["names"]["singular"] == "devsupersuitecluster"


# ─────────────────────────────────────────────────────────────────────────────
# 2. RBAC Least-Privilege Conformance Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_rbac_least_privilege_conformance():
    """Ensures RBAC manifests contain no wildcard '*' verbs or resources."""
    manifests = RBACManifestGenerator.get_rbac_manifests()
    assert len(manifests) == 3

    sa = manifests[0]
    cluster_role = manifests[1]
    crb = manifests[2]

    assert sa["kind"] == "ServiceAccount"
    assert sa["metadata"]["name"] == "devsupersuite-operator-controller-manager"

    assert cluster_role["kind"] == "ClusterRole"
    rules = cluster_role["rules"]
    assert len(rules) >= 5

    for rule in rules:
        # Strict zero wildcard rule
        assert "*" not in rule["verbs"], f"Wildcard verb detected in rule: {rule}"
        assert "*" not in rule["resources"], f"Wildcard resource detected in rule: {rule}"

    assert crb["kind"] == "ClusterRoleBinding"
    assert crb["roleRef"]["name"] == cluster_role["metadata"]["name"]
    assert crb["subjects"][0]["name"] == sa["metadata"]["name"]


# ─────────────────────────────────────────────────────────────────────────────
# 3. Controller Manager Deployment Hardening Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_deployment_security_context_and_ha():
    """Verifies HA replicas, non-root UID 10001, and read-only filesystem."""
    deploy = OperatorDeploymentGenerator.get_deployment_dict()
    assert deploy["kind"] == "Deployment"
    assert deploy["spec"]["replicas"] == 2  # HA leader election

    pod_sec = deploy["spec"]["template"]["spec"]["securityContext"]
    assert pod_sec["runAsNonRoot"] is True
    assert pod_sec["runAsUser"] == NON_ROOT_UID
    assert pod_sec["runAsGroup"] == NON_ROOT_UID

    container = deploy["spec"]["template"]["spec"]["containers"][0]
    container_sec = container["securityContext"]
    assert container_sec["allowPrivilegeEscalation"] is False
    assert container_sec["readOnlyRootFilesystem"] is True
    assert "ALL" in container_sec["capabilities"]["drop"]

    # Probes
    assert container["livenessProbe"]["httpGet"]["path"] == "/healthz"
    assert container["readinessProbe"]["httpGet"]["path"] == "/readyz"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Reconciliation Engine State Machine Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_reconciliation_ast_queue_autoscaling():
    """Tests dynamic replica scaling tied to Tree-sitter AST queue depth."""
    controller = ReconciliationController()
    spec = {
        "replicas": 3,
        "edition": "Enterprise",
        "version": "2026.3.0",
        "astEngine": {
            "minReplicas": 2,
            "maxReplicas": 50,
            "maxQueueDepth": 500
        }
    }
    status = {
        "phase": "Healthy",
        "currentReplicas": 3,
        "readyReplicas": 3,
        "activeVersion": "2026.3.0",
        "lastSecretRotationTimestamp": datetime.now(timezone.utc).isoformat()
    }

    # Queue depth 850 -> math.ceil(850 / 100) = 9 replicas
    telemetry_spike = {"astQueueDepth": 850, "canaryHealthHealthy": True}
    updated_status, events = controller.reconcile("test-cluster", spec, status, telemetry_spike)

    assert updated_status["currentReplicas"] == 9
    assert updated_status["readyReplicas"] == 9
    assert updated_status["phase"] == "Scaling"
    assert any(e.action_type == "SCALE_UP" for e in events)

    # Queue drain: 150 items -> max(2, min(50, 2)) = 3 (base spec replica floor)
    telemetry_drain = {"astQueueDepth": 150, "canaryHealthHealthy": True}
    updated_status_drain, events_drain = controller.reconcile("test-cluster", spec, updated_status, telemetry_drain)
    assert updated_status_drain["currentReplicas"] == 3
    assert any(e.action_type == "SCALE_DOWN" for e in events_drain)


def test_reconciliation_secret_rotation_trigger():
    """Verifies automated secret & TLS rotation occurs upon 24h threshold expiration."""
    controller = ReconciliationController()
    spec = {
        "replicas": 2,
        "version": "2026.3.0",
        "security": {
            "secretRotation": {
                "enabled": True,
                "intervalHours": 24
            }
        }
    }
    t0 = datetime(2026, 11, 8, 0, 0, 0, tzinfo=timezone.utc)
    status = {
        "phase": "Healthy",
        "activeVersion": "2026.3.0",
        "lastSecretRotationTimestamp": t0.isoformat()
    }

    # Case 1: Only 10 hours elapsed -> NO rotation
    t_fresh = t0 + timedelta(hours=10)
    res_fresh, ev_fresh = controller.reconcile("test-cluster", spec, status, {}, simulated_now=t_fresh)
    assert not any(e.action_type == "ROTATE_SECRETS" for e in ev_fresh)

    # Case 2: 25 hours elapsed -> triggers ROTATE_SECRETS
    t_expired = t0 + timedelta(hours=25)
    res_expired, ev_expired = controller.reconcile("test-cluster", spec, status, {}, simulated_now=t_expired)
    assert any(e.action_type == "ROTATE_SECRETS" for e in ev_expired)
    assert res_expired["lastSecretRotationTimestamp"] == t_expired.isoformat()


def test_reconciliation_canary_rollout_lifecycle():
    """Tests zero-downtime rolling canary progression: 20% -> 50% -> 100% promotion."""
    controller = ReconciliationController()
    spec_v1 = {"replicas": 2, "version": "2026.2.0", "deploymentStrategy": {"type": "Canary", "canaryStepPercent": 20}}
    status = {"phase": "Healthy", "activeVersion": "2026.2.0", "currentReplicas": 2}

    # Upgrade spec to v2026.3.0
    spec_v2 = dict(spec_v1)
    spec_v2["version"] = "2026.3.0"

    # Step 1: Canary Initiation (20%)
    status_1, ev1 = controller.reconcile("test-cluster", spec_v2, status, {"canaryHealthHealthy": True})
    assert status_1["phase"] == "CanaryActive"
    assert status_1["canaryWeight"] == 20
    assert any(e.action_type == "CANARY_INITIATE" for e in ev1)

    # Step 2: Canary Advance (50%)
    status_2, ev2 = controller.reconcile("test-cluster", spec_v2, status_1, {"canaryHealthHealthy": True})
    assert status_2["phase"] == "CanaryActive"
    assert status_2["canaryWeight"] == 50
    assert any(e.action_type == "CANARY_ADVANCE" for e in ev2)

    # Step 3: Canary Promotion (100% promotion)
    status_3, ev3 = controller.reconcile("test-cluster", spec_v2, status_2, {"canaryHealthHealthy": True})
    assert status_3["phase"] == "Healthy"
    assert status_3["canaryWeight"] == 0
    assert status_3["activeVersion"] == "2026.3.0"
    assert any(e.action_type == "CANARY_PROMOTED" for e in ev3)


def test_reconciliation_canary_rollback_on_health_failure():
    """Tests automated canary rollback to stable version if canary metrics degrade."""
    controller = ReconciliationController()
    spec_v2 = {"replicas": 2, "version": "2026.3.0", "deploymentStrategy": {"type": "Canary"}}
    status_active_canary = {
        "phase": "CanaryActive",
        "activeVersion": "2026.2.0",
        "canaryWeight": 20,
        "currentReplicas": 2
    }

    # Canary fails health check (e.g. latency spike or error ceiling breach)
    status_rolled_back, ev = controller.reconcile(
        "test-cluster",
        spec_v2,
        status_active_canary,
        {"canaryHealthHealthy": False}
    )
    assert status_rolled_back["phase"] == "Degraded"
    assert status_rolled_back["canaryWeight"] == 0
    assert status_rolled_back["activeVersion"] == "2026.2.0"
    assert any(e.action_type == "CANARY_ROLLBACK" for e in ev)


def test_reconciliation_mtls_sidecar_injection():
    """Ensures sidecar injection is triggered when mesh sidecar is missing."""
    controller = ReconciliationController()
    spec = {"replicas": 2, "version": "2026.3.0", "security": {"mtlsSidecar": {"enabled": True, "tlsMinVersion": "TLSv1.3"}}}
    status = {"phase": "Healthy", "activeVersion": "2026.3.0"}

    _, events = controller.reconcile("test-cluster", spec, status, {"mtlsSidecarVerified": False})
    assert any(e.action_type == "INJECT_MTLS_SIDECAR" for e in events)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Simulation Harness & Exporters Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_full_simulation_harness_execution():
    """Runs the 4-stage operator simulation harness and verifies end-state invariants."""
    sim_results = OperatorSimulationHarness.run_simulation()
    assert sim_results["stages_executed"] == 4
    assert sim_results["total_reconciliation_events"] >= 8
    assert sim_results["final_status"]["phase"] == "Healthy"
    assert sim_results["final_status"]["activeVersion"] == "2026.3.0"

    # Export guide and report
    guide_path = export_k8s_operator_guide()
    report_path = export_k8s_operator_report(sim_results)
    assert guide_path.exists()
    assert report_path.exists()
    assert "DSS-K8S-OPERATOR-RUNBOOK-2026" in guide_path.read_text(encoding="utf-8")
    assert "DSS-K8S-REPORT-2026-V1" in report_path.read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# 6. Brand Anonymity Invariants Test
# ─────────────────────────────────────────────────────────────────────────────

def test_brand_anonymity_invariants():
    """Asserts 100% Brand Anonymity across all newly authored operator manifests and documentation."""
    files_to_check = [
        SERVICES_DIR / "enterprise_k8s_operator_engine.py",
        GUIDE_FILE,
        REPORT_FILE,
        CRD_FILE,
        RBAC_FILE,
        DEPLOY_FILE
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
    """Tests execution of the operator engine CLI across all mandatory flags."""
    flags_to_test = [
        ["--generate-crd-manifests"],
        ["--generate-operator-rbac"],
        ["--simulate-reconcile-loop"],
        ["--export-operator-bundle"],
        ["--summary"]
    ]

    engine_script = SERVICES_DIR / "enterprise_k8s_operator_engine.py"

    for flag_list in flags_to_test:
        cmd = [sys.executable, str(engine_script)] + flag_list
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, f"CLI command failed with code {proc.returncode}: {proc.stderr}"
        assert "DevSuperSuite" in proc.stdout
