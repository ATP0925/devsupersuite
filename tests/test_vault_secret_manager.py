#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Enterprise Secret Management Test Suite
Reference: DSS-TEST-VAULT-SECRETS-2026
Classification: Defense SCIF & Sovereign HSM Secret Protection
Contact: DevSuperSuite Solutions Architecture (solutions@devsupersuite.com)
═══════════════════════════════════════════════════════════════════════════════
"""

import base64
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
import yaml
from cryptography.exceptions import InvalidTag

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = REPO_ROOT / "services"
REPORTS_DIR = SERVICES_DIR / "reports"
DEPLOYMENT_DIR = REPO_ROOT / "deployment"
K8S_SECRETS_DIR = DEPLOYMENT_DIR / "k8s" / "secrets"

SPC_FILE = K8S_SECRETS_DIR / "secret_provider_class.yaml"
SIDECAR_FILE = K8S_SECRETS_DIR / "vault_agent_sidecar.yaml"
GUIDE_FILE = SERVICES_DIR / "enterprise_secret_management_guide.md"
REPORT_FILE = REPORTS_DIR / "secret_management_architecture_report.md"

sys.path.insert(0, str(SERVICES_DIR))
from enterprise_vault_secret_manager import (
    SecretManifestGenerator,
    EnvelopeEncryptionEngine,
    SecureMemoryBuffer,
    run_secrets_simulation,
    export_secrets_guide,
    export_secrets_report,
    NON_ROOT_UID
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Secret Provider Class & Sidecar Manifest Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_secret_provider_class_manifest_schema():
    """Validates Secrets Store CSI Driver SecretProviderClass syntax and rotation objects."""
    spc_dict = SecretManifestGenerator.get_secret_provider_class_dict()
    assert spc_dict["apiVersion"] == "secrets-store.csi.x-k8s.io/v1"
    assert spc_dict["kind"] == "SecretProviderClass"
    assert spc_dict["metadata"]["name"] == "devsupersuite-vault-secrets"

    spec = spc_dict["spec"]
    assert spec["provider"] == "vault"
    assert "vault.internal.devsupersuite.io" in spec["parameters"]["vaultAddress"]
    assert spec["parameters"]["roleName"] == "devsupersuite-ast-proxy-role"

    # SecretObjects rotation mappings
    sec_objs = spec["secretObjects"]
    assert len(sec_objs) == 1
    assert sec_objs[0]["secretName"] == "devsupersuite-runtime-secrets"
    data_mappings = sec_objs[0]["data"]
    assert len(data_mappings) == 3
    keys = [d["key"] for d in data_mappings]
    assert "SIGNING_KEY" in keys
    assert "ENTROPY_SALT" in keys
    assert "DB_PASSWORD" in keys


def test_vault_agent_sidecar_and_tmpfs_mount():
    """Verifies Vault Agent injector sidecar and zero-disk tmpfs volume mount."""
    deploy = SecretManifestGenerator.get_vault_agent_sidecar_dict()
    assert deploy["apiVersion"] == "apps/v1"
    assert deploy["kind"] == "Deployment"

    annotations = deploy["spec"]["template"]["metadata"]["annotations"]
    assert annotations["vault.hashicorp.com/agent-inject"] == "true"
    assert annotations["vault.hashicorp.com/role"] == "devsupersuite-ast-proxy-role"

    # Verify tmpfs RAM-only volume (zero disk persistence)
    volumes = deploy["spec"]["template"]["spec"]["volumes"]
    tmpfs_vol = next((v for v in volumes if v["name"] == "vault-secrets-tmpfs"), None)
    assert tmpfs_vol is not None
    assert tmpfs_vol["emptyDir"]["medium"] == "Memory"

    # Verify CSI driver volume
    csi_vol = next((v for v in volumes if v["name"] == "csi-secrets-store"), None)
    assert csi_vol is not None
    assert csi_vol["csi"]["driver"] == "secrets-store.csi.k8s.io"

    # Rootless security context
    pod_sec = deploy["spec"]["template"]["spec"]["securityContext"]
    assert pod_sec["runAsUser"] == 10001
    assert pod_sec["runAsNonRoot"] is True


# ─────────────────────────────────────────────────────────────────────────────
# 2. Envelope Encryption Engine Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_envelope_encryption_cycle():
    """Tests two-tier envelope encryption: DEK generation, CMK wrapping, and decryption."""
    engine = EnvelopeEncryptionEngine()
    original_secret = b"dss-scif-ed25519-private-signing-key-production"
    context = {"cluster": "scif-isolated-dc01", "service": "ast-proxy"}

    envelope = engine.encrypt_secret(original_secret, context)
    assert envelope["algorithm"] == "AES-256-GCM"
    assert "wrapped_dek_b64" in envelope
    assert "ciphertext_b64" in envelope

    # Decrypt and assert equality
    decrypted = engine.decrypt_secret(envelope)
    assert decrypted == original_secret


def test_envelope_encryption_tamper_detection():
    """Ensures AES-GCM authentication fails if ciphertext or metadata is tampered with."""
    engine = EnvelopeEncryptionEngine()
    original_secret = b"dss-shannon-entropy-salt-987654321"
    context = {"cluster": "scif-isolated-dc01", "service": "ast-proxy"}

    envelope = engine.encrypt_secret(original_secret, context)

    # Tamper with context metadata (AAD modification)
    tampered_envelope = dict(envelope)
    tampered_envelope["context_metadata"] = {"cluster": "rogue-unauthorized-cluster", "service": "ast-proxy"}

    with pytest.raises(InvalidTag):
        engine.decrypt_secret(tampered_envelope)

    # Tamper with ciphertext bytes
    tampered_envelope2 = dict(envelope)
    raw_ct = bytearray(base64.b64decode(envelope["ciphertext_b64"]))
    raw_ct[0] ^= 0xFF  # Flip bit
    tampered_envelope2["ciphertext_b64"] = base64.b64encode(raw_ct).decode("ascii")

    with pytest.raises(InvalidTag):
        engine.decrypt_secret(tampered_envelope2)


# ─────────────────────────────────────────────────────────────────────────────
# 3. DoD 5220.22-M Memory Zeroization Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_dod_5220_22_m_memory_zeroization():
    """Verifies DoD 5220.22-M 4-pass in-memory scrubbing and post-zeroization access denial."""
    secret = b"dss-database-master-password-sensitive"
    buf = SecureMemoryBuffer(secret)

    assert buf.read_secret() == secret
    assert buf.is_zeroized is False

    # Execute zeroization
    report = buf.zeroize()
    assert report["status"] == "ZEROIZED"
    assert report["passes_executed"] == 4
    assert report["standard"] == "DoD 5220.22-M NISPOM"
    assert report["verified_zeroes"] is True
    assert buf.is_zeroized is True

    # Assert subsequent access is denied
    with pytest.raises(ValueError, match="Access Denied"):
        buf.read_secret()


# ─────────────────────────────────────────────────────────────────────────────
# 4. Secrets Simulation Runner & Exporters Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_secrets_simulation_runner_and_exporters():
    """Runs full secrets simulation and verifies guide and report file exports."""
    sim_res = run_secrets_simulation()
    assert sim_res["envelope_encryption_pass"] is True
    assert sim_res["zeroization_report"]["verified_zeroes"] is True

    # Export guide and report
    guide_path = export_secrets_guide()
    report_path = export_secrets_report(sim_res)

    assert guide_path.exists()
    assert report_path.exists()
    assert "DSS-VAULT-SECRETS-RUNBOOK-2026" in guide_path.read_text(encoding="utf-8")
    assert "DSS-SECRETS-REPORT-2026-V1" in report_path.read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Brand Anonymity Invariants Test
# ─────────────────────────────────────────────────────────────────────────────

def test_brand_anonymity_invariants():
    """Asserts 100% Brand Anonymity across all newly authored secret management artifacts."""
    files_to_check = [
        SERVICES_DIR / "enterprise_vault_secret_manager.py",
        GUIDE_FILE,
        REPORT_FILE,
        SPC_FILE,
        SIDECAR_FILE
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
    """Tests execution of the vault secret manager CLI across all mandatory flags."""
    flags_to_test = [
        ["--generate-csi-manifests"],
        ["--simulate-envelope-encryption"],
        ["--audit-memory-zeroization"],
        ["--export-secrets-bundle"],
        ["--summary"]
    ]

    engine_script = SERVICES_DIR / "enterprise_vault_secret_manager.py"

    for flag_list in flags_to_test:
        cmd = [sys.executable, str(engine_script)] + flag_list
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, f"CLI command failed with code {proc.returncode}: {proc.stderr}"
        assert "DevSuperSuite" in proc.stdout
