#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Enterprise GitOps Delivery Controller Test Suite
Reference: DSS-TEST-GITOPS-CONTROLLER-2026
Classification: Sovereign Air-Gap Declarative CD & Self-Heal Governance
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
K8S_GITOPS_DIR = DEPLOYMENT_DIR / "k8s" / "gitops"

ARGOCD_APP_FILE = K8S_GITOPS_DIR / "argocd_application.yaml"
ARGOCD_APPSET_FILE = K8S_GITOPS_DIR / "argocd_applicationset.yaml"
FLUX_HR_FILE = K8S_GITOPS_DIR / "flux_helm_release.yaml"
GUIDE_FILE = SERVICES_DIR / "enterprise_gitops_guide.md"
REPORT_FILE = REPORTS_DIR / "gitops_delivery_architecture_report.md"

sys.path.insert(0, str(SERVICES_DIR))
from enterprise_gitops_delivery_controller import (
    GitOpsManifestGenerator,
    ClusterDriftDetector,
    AirgapRegistrySynchronizer,
    run_gitops_simulation,
    export_gitops_guide,
    export_gitops_report,
    NON_ROOT_UID,
    MAX_SELF_HEAL_LATENCY_SECONDS
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. ArgoCD & Flux Manifest Schema Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_argocd_application_manifest_schema():
    """Validates ArgoCD Application structure, automated prune, and self-heal policies."""
    app_dict = GitOpsManifestGenerator.get_argocd_application_dict()
    assert app_dict["apiVersion"] == "argoproj.io/v1alpha1"
    assert app_dict["kind"] == "Application"
    assert app_dict["metadata"]["name"] == "devsupersuite-core"

    spec = app_dict["spec"]
    assert spec["project"] == "default"
    assert spec["destination"]["namespace"] == "devsupersuite-system"

    # Automated Sync Policy
    sync_policy = spec["syncPolicy"]
    assert sync_policy["automated"]["prune"] is True
    assert sync_policy["automated"]["selfHeal"] is True
    assert "PruneLast=true" in sync_policy["syncOptions"]
    assert "ApplyOutOfSyncOnly=true" in sync_policy["syncOptions"]

    # Retry backoff
    assert sync_policy["retry"]["limit"] == 5
    assert sync_policy["retry"]["backoff"]["factor"] == 2

    # Helm Parameters (UID 10001, Zero-Egress)
    helm_params = spec["source"]["helm"]["parameters"]
    assert any(p["name"] == "security.runAsUser" and p["value"] == str(NON_ROOT_UID) for p in helm_params)
    assert any(p["name"] == "security.zeroEgress" and p["value"] == "true" for p in helm_params)


def test_argocd_applicationset_matrix_generator():
    """Validates ArgoCD ApplicationSet multi-cluster matrix configuration."""
    appset_dict = GitOpsManifestGenerator.get_argocd_applicationset_dict()
    assert appset_dict["apiVersion"] == "argoproj.io/v1alpha1"
    assert appset_dict["kind"] == "ApplicationSet"

    spec = appset_dict["spec"]
    elements = spec["generators"][0]["list"]["elements"]
    assert len(elements) == 4

    cluster_names = [e["cluster"] for e in elements]
    assert "staging-us-west" in cluster_names
    assert "prod-eu-central-1" in cluster_names
    assert "prod-us-east-1" in cluster_names
    assert "scif-isolated-dc01" in cluster_names

    # Check compliance editions
    editions = [e["edition"] for e in elements]
    assert "Enterprise" in editions
    assert "FedRAMP" in editions
    assert "SCIF-AirGap" in editions


def test_flux_manifests_schema():
    """Verifies Flux v2 GitRepository and HelmRelease multi-document manifests."""
    flux_docs = GitOpsManifestGenerator.get_flux_manifests_dict()
    assert len(flux_docs) == 2

    git_repo = flux_docs[0]
    helm_release = flux_docs[1]

    assert git_repo["kind"] == "GitRepository"
    assert git_repo["spec"]["interval"] == "1m"
    assert git_repo["spec"]["ref"]["branch"] == "master"

    assert helm_release["kind"] == "HelmRelease"
    assert helm_release["spec"]["chart"]["spec"]["sourceRef"]["name"] == "devsupersuite-repo"
    assert helm_release["spec"]["install"]["remediation"]["retries"] == 3
    assert helm_release["spec"]["values"]["securityContext"]["runAsUser"] == NON_ROOT_UID
    assert helm_release["spec"]["values"]["networkPolicy"]["zeroEgress"] is True


# ─────────────────────────────────────────────────────────────────────────────
# 2. Configuration Drift Detection & Self-Heal Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_drift_detector_tampering_identification():
    """Verifies drift detection catches replica drift, image changes, and root escalation."""
    git_manifests = {
        "Deployment": {
            "metadata": {"name": "ast-proxy"},
            "spec": {
                "replicas": 4,
                "template": {
                    "spec": {
                        "securityContext": {"runAsUser": NON_ROOT_UID},
                        "containers": [{"image": "registry.devsupersuite.io/enterprise/ast-proxy:v2026.3.0"}]
                    }
                }
            }
        },
        "NetworkPolicy": {"metadata": {"name": "zero-egress-policy"}}
    }

    # Tampered live state
    tampered_live = {
        "Deployment": {
            "metadata": {"name": "ast-proxy"},
            "spec": {
                "replicas": 1,
                "template": {
                    "spec": {
                        "securityContext": {"runAsUser": 0},  # Root escalation!
                        "containers": [{"image": "docker.io/unverified/rogue:latest"}]
                    }
                }
            }
        }
        # NetworkPolicy deleted
    }

    drifts = ClusterDriftDetector.compare_states(git_manifests, tampered_live)
    assert len(drifts) == 4

    severities = [d.severity for d in drifts]
    assert "CRITICAL" in severities  # Root escalation and rogue image
    assert "MEDIUM" in severities    # Replica modification
    assert "HIGH" in severities      # Missing NetworkPolicy


def test_self_heal_remediation_within_sla():
    """Tests automated self-healing reconciliation latency and restoration to Synced/Healthy."""
    git_manifests = {
        "Deployment": {
            "metadata": {"name": "ast-proxy"},
            "spec": {
                "replicas": 4,
                "template": {
                    "spec": {
                        "securityContext": {"runAsUser": NON_ROOT_UID},
                        "containers": [{"image": "registry.devsupersuite.io/enterprise/ast-proxy:v2026.3.0"}]
                    }
                }
            }
        }
    }
    tampered_live = {
        "Deployment": {
            "metadata": {"name": "ast-proxy"},
            "spec": {
                "replicas": 2,
                "template": {
                    "spec": {
                        "securityContext": {"runAsUser": NON_ROOT_UID},
                        "containers": [{"image": "registry.devsupersuite.io/enterprise/ast-proxy:v2026.3.0"}]
                    }
                }
            }
        }
    }

    drifts = ClusterDriftDetector.compare_states(git_manifests, tampered_live)
    heal_res = ClusterDriftDetector.execute_self_heal_remediation(drifts, self_heal_enabled=True)

    assert heal_res["sync_status"] == "Synced"
    assert heal_res["health_status"] == "Healthy"
    assert heal_res["within_sla"] is True
    assert heal_res["elapsed_seconds"] <= MAX_SELF_HEAL_LATENCY_SECONDS
    assert len(heal_res["remediation_actions"]) == 1


def test_self_heal_disabled_reports_out_of_sync():
    """Tests that disabled self-heal leaves cluster in OutOfSync/Degraded state."""
    git_manifests = {
        "Deployment": {
            "metadata": {"name": "ast-proxy"},
            "spec": {"replicas": 4}
        }
    }
    tampered_live = {
        "Deployment": {
            "metadata": {"name": "ast-proxy"},
            "spec": {"replicas": 1}
        }
    }

    drifts = ClusterDriftDetector.compare_states(git_manifests, tampered_live)
    heal_res = ClusterDriftDetector.execute_self_heal_remediation(drifts, self_heal_enabled=False)

    assert heal_res["sync_status"] == "OutOfSync"
    assert heal_res["health_status"] == "Degraded"


# ─────────────────────────────────────────────────────────────────────────────
# 3. Air-Gapped OCI Registry Synchronizer Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_airgap_registry_manifest_generation():
    """Validates air-gap OCI artifacts, SHA256 checksums, and skopeo copy commands."""
    manifest = AirgapRegistrySynchronizer.generate_airgap_manifest()
    assert manifest["bundle_name"].endswith(".tar.gz")
    assert len(manifest["bundle_sha256"]) == 64
    assert manifest["total_artifacts"] == 4
    assert manifest["total_size_mb"] > 200

    commands = manifest["sync_runbook_commands"]
    assert any("skopeo copy" in c for c in commands)
    assert any("helm push" in c for c in commands)


# ─────────────────────────────────────────────────────────────────────────────
# 4. GitOps Simulation Runner & Exporters Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_gitops_simulation_runner_and_exporters():
    """Runs full GitOps simulation and verifies guide and report file exports."""
    sim_res = run_gitops_simulation()
    assert len(sim_res["detected_drifts"]) == 3
    assert sim_res["self_heal_result"]["sync_status"] == "Synced"

    # Export guide and report
    guide_path = export_gitops_guide()
    airgap_manifest = AirgapRegistrySynchronizer.generate_airgap_manifest()
    report_path = export_gitops_report(sim_res, airgap_manifest)

    assert guide_path.exists()
    assert report_path.exists()
    assert "DSS-GITOPS-RUNBOOK-2026" in guide_path.read_text(encoding="utf-8")
    assert "DSS-GITOPS-REPORT-2026-V1" in report_path.read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Brand Anonymity Invariants Test
# ─────────────────────────────────────────────────────────────────────────────

def test_brand_anonymity_invariants():
    """Asserts 100% Brand Anonymity across all newly authored GitOps artifacts."""
    files_to_check = [
        SERVICES_DIR / "enterprise_gitops_delivery_controller.py",
        GUIDE_FILE,
        REPORT_FILE,
        ARGOCD_APP_FILE,
        ARGOCD_APPSET_FILE,
        FLUX_HR_FILE
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
    """Tests execution of the GitOps delivery controller CLI across all mandatory flags."""
    flags_to_test = [
        ["--generate-gitops-manifests"],
        ["--simulate-drift-reconciliation"],
        ["--audit-sync-health"],
        ["--export-gitops-bundle"],
        ["--summary"]
    ]

    engine_script = SERVICES_DIR / "enterprise_gitops_delivery_controller.py"

    for flag_list in flags_to_test:
        cmd = [sys.executable, str(engine_script)] + flag_list
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, f"CLI command failed with code {proc.returncode}: {proc.stderr}"
        assert "DevSuperSuite" in proc.stdout
