#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Zero-Trust Bastion Test Suite
Reference: DSS-ZERO-TRUST-BASTION-TESTS-2026-V1
Classification: Automated Quality Gate & Invariant Validation (Restricted)
Contact: DevSuperSuite Solutions Architecture (solutions@devsupersuite.com)
Author: OmniKernel Labs / DevSuperSuite Quality Assurance & Test Engineering
═══════════════════════════════════════════════════════════════════════════════
"""

import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = REPO_ROOT / "services"
REPORTS_DIR = SERVICES_DIR / "reports"
DEPLOYMENT_DIR = REPO_ROOT / "deployment"
BASTION_DIR = DEPLOYMENT_DIR / "bastion"

if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from enterprise_zero_trust_bastion_engine import (
    ORGANIZATION_NAME,
    PRIMARY_CONTACT,
    BASTION_CONTACT,
    REFERENCE_CODE,
    MAX_CERT_VALIDITY_SECONDS,
    REQUIRED_QUORUM_APPROVALS,
    CA_KEY_ALGORITHM,
    CA_FINGERPRINT,
    CollusionProtectionError,
    QuorumNotMetError,
    DualControlQuorumManager,
    EphemeralCertificateAuthority,
    BastionSessionAuditor,
    EnterpriseZeroTrustBastionEngine
)


class TestEnterpriseZeroTrustBastion:
    """Enterprise verification suite for Zero-Trust Ephemeral Bastion & Quorum Engine."""

    def test_access_request_creation(self):
        """Validate creation of a Just-In-Time (JIT) access request with 30-min max TTL."""
        manager = DualControlQuorumManager()
        req = manager.create_access_request(
            requestor_id="engineer@devsupersuite.internal",
            target_resource="prod-banking-core-cluster",
            reason="Hotfix deployment for payment settlement",
            duration_seconds=1800
        )

        assert "JIT-" in req["request_id"]
        assert req["status"] == "PENDING"
        assert req["required_approvals"] == 2
        assert req["duration_seconds"] == 1800
        assert req["current_approvals_count"] == 0

        # Duration exceeding 30 minutes must be rejected
        with pytest.raises(ValueError):
            manager.create_access_request("eng@devsupersuite.internal", "res", "reason", duration_seconds=3600)

        # Zero or negative duration must be rejected
        with pytest.raises(ValueError):
            manager.create_access_request("eng@devsupersuite.internal", "res", "reason", duration_seconds=0)

    def test_dual_control_quorum_approval_success(self):
        """Verify M-of-N dual-control consensus: 2 distinct approvals transition status to APPROVED."""
        manager = DualControlQuorumManager()
        req = manager.create_access_request("devops@devsupersuite.internal", "prod-scif-node", "audit check")

        # Approval 1: Security Lead
        req1 = manager.approve_request(req["request_id"], "sec-lead@devsupersuite.internal", "Security Lead")
        assert req1["current_approvals_count"] == 1
        assert req1["status"] == "PENDING"  # Quorum not met yet

        # Approval 2: Infrastructure Lead
        req2 = manager.approve_request(req["request_id"], "infra-lead@devsupersuite.internal", "Infrastructure Lead")
        assert req2["current_approvals_count"] == 2
        assert req2["status"] == "APPROVED"  # Quorum satisfied!

    def test_anti_collusion_self_approval_blocked(self):
        """Enforce anti-collusion rule: Requestor cannot approve their own JIT request."""
        manager = DualControlQuorumManager()
        req = manager.create_access_request("rogue-actor@devsupersuite.internal", "scif-cluster", "test")

        with pytest.raises(CollusionProtectionError):
            manager.approve_request(req["request_id"], "rogue-actor@devsupersuite.internal", "Security Lead")

    def test_duplicate_approver_and_role_rejection(self):
        """Reject duplicate votes from same approver or multiple votes under identical role."""
        manager = DualControlQuorumManager()
        req = manager.create_access_request("dev@devsupersuite.internal", "res", "maintenance")

        # First vote
        manager.approve_request(req["request_id"], "approver-1@devsupersuite.internal", "Security Lead")

        # Same approver voting again
        with pytest.raises(ValueError, match="already voted"):
            manager.approve_request(req["request_id"], "approver-1@devsupersuite.internal", "Infrastructure Lead")

        # Different approver voting under same role
        with pytest.raises(ValueError, match="already provided an approval"):
            manager.approve_request(req["request_id"], "approver-2@devsupersuite.internal", "Security Lead")

        # Unauthorized role
        with pytest.raises(ValueError, match="not authorized"):
            manager.approve_request(req["request_id"], "approver-3@devsupersuite.internal", "Junior Developer")

    def test_request_rejection(self):
        """Validate explicit rejection transitions request status to REJECTED."""
        manager = DualControlQuorumManager()
        req = manager.create_access_request("dev@devsupersuite.internal", "res", "maintenance")
        rejected = manager.reject_request(req["request_id"], "ciso@devsupersuite.internal", "Insufficient justification")

        assert rejected["status"] == "REJECTED"
        assert len(rejected["rejections"]) == 1
        assert rejected["rejections"][0]["rejector_id"] == "ciso@devsupersuite.internal"

    def test_ephemeral_cert_issuance_approved(self):
        """Validate Ed25519 certificate issuance with short-lived <= 30-min validity."""
        engine = EnterpriseZeroTrustBastionEngine()
        req = engine.request_and_approve_access(
            requestor_id="operator-01@devsupersuite.internal",
            target_resource="prod-financial-cluster",
            reason="Emergency failover validation",
            approvers=[
                ("sec-lead@devsupersuite.internal", "Security Lead"),
                ("vp-eng@devsupersuite.internal", "VP Engineering")
            ],
            duration_seconds=1800
        )

        cert = engine.ca.issue_certificate(req)
        assert cert["certificate_type"] == "SSH_USER_CERTIFICATE"
        assert cert["format"] == CA_KEY_ALGORITHM
        assert cert["validity_duration_seconds"] <= MAX_CERT_VALIDITY_SECONDS
        assert cert["max_validity_sla_met"] is True
        assert cert["ca_fingerprint"] == CA_FINGERPRINT
        assert len(cert["ed25519_cert_signature"]) == 64
        assert EphemeralCertificateAuthority.is_certificate_valid(cert) is True
        assert req["status"] == "ACTIVE"

    def test_cert_issuance_unapproved_raises_error(self):
        """Attempting to issue certificate for unapproved request raises QuorumNotMetError."""
        ca = EphemeralCertificateAuthority()
        unapproved_req = {
            "request_id": "JIT-TEST-001",
            "requestor_id": "unauthorized@devsupersuite.internal",
            "status": "PENDING"
        }
        with pytest.raises(QuorumNotMetError):
            ca.issue_certificate(unapproved_req)

    def test_keystroke_auditor_hash_chaining(self):
        """Validate session audit log captures commands in an immutable SHA-256 hash chain."""
        auditor = BastionSessionAuditor("SESS-001", "JIT-001", "operator-01")

        f0 = auditor.record_command("kubectl get namespaces", exit_code=0)
        assert f0["frame_index"] == 0
        assert f0["previous_hash"] == "0" * 64

        f1 = auditor.record_command("kubectl get pods -n kube-system", exit_code=0)
        assert f1["frame_index"] == 1
        assert f1["previous_hash"] == f0["frame_hash"]

        f2 = auditor.record_command("uptime", exit_code=0)
        assert f2["frame_index"] == 2
        assert f2["previous_hash"] == f1["frame_hash"]

        assert auditor.session_status == "ACTIVE"
        assert len(auditor.get_audit_trail()) == 3

    def test_dangerous_command_detection_and_kill(self):
        """Verify high-risk dangerous commands trigger immediate session termination (KILL)."""
        auditor = BastionSessionAuditor("SESS-002", "JIT-002", "operator-02")

        # Normal command
        auditor.record_command("ls -la", exit_code=0)
        assert auditor.session_status == "ACTIVE"

        # Dangerous command: catastrophic delete
        f_kill = auditor.record_command("rm -rf / --no-preserve-root")
        assert auditor.session_status == "KILLED_SECURITY_VIOLATION"
        assert f_kill["security_violation"] is not None
        assert "purge attempt" in f_kill["security_violation"]
        assert f_kill["exit_code"] == -1

    def test_dangerous_command_patterns_coverage(self):
        """Verify detection of various threat signatures: shadow cat, iptables flush, dd."""
        test_threats = [
            ("cat /etc/shadow", "Password hash"),
            ("iptables -F", "Firewall flush"),
            ("dd if=/dev/zero of=/dev/sda", "block device write")
        ]

        for cmd, expected_phrase in test_threats:
            auditor = BastionSessionAuditor("SESS-THREAT", "JIT-THREAT", "attacker")
            f = auditor.record_command(cmd)
            assert auditor.session_status == "KILLED_SECURITY_VIOLATION"
            assert expected_phrase.lower() in f["security_violation"].lower()

    def test_siem_event_export(self):
        """Verify export of session audit trail into enterprise SIEM event format."""
        auditor = BastionSessionAuditor("SESS-003", "JIT-003", "audit-user")
        auditor.record_command("kubectl get svc", exit_code=0)
        auditor.record_command("chmod 777 /var/data")  # Triggers threat alert

        events = auditor.export_siem_events()
        assert len(events) == 2
        assert events[0]["security_alert"] is False
        assert events[1]["security_alert"] is True
        assert events[1]["violation_reason"] is not None
        assert "chain_hash" in events[0]
        assert events[0]["event_source"] == "devsupersuite_bastion"

    def test_policy_manifest_export_and_json_validity(self, tmp_path):
        """Verify generation and valid JSON schema of bastion policy manifest."""
        engine = EnterpriseZeroTrustBastionEngine()
        target_file = tmp_path / "bastion_policy_manifest.json"
        engine.export_policy_manifest(target_file)

        assert target_file.exists()
        with open(target_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["metadata"]["organization"] == ORGANIZATION_NAME
        assert manifest["metadata"]["contact"] == PRIMARY_CONTACT
        assert manifest["quorum_authorization_policy"]["required_approvals"] == REQUIRED_QUORUM_APPROVALS
        assert manifest["certificate_authority_policy"]["max_certificate_ttl_seconds"] == MAX_CERT_VALIDITY_SECONDS
        assert "rm -rf /" in manifest["session_auditing_policy"]["dangerous_command_blacklist"]

    def test_architecture_report_generation(self, tmp_path):
        """Verify technical whitepaper and security architecture report export."""
        engine = EnterpriseZeroTrustBastionEngine()
        report_file = tmp_path / "zero_trust_bastion_report.md"
        engine.export_architecture_report(report_file)

        assert report_file.exists()
        text = report_file.read_text(encoding="utf-8")
        assert "Zero-Trust Ephemeral Bastion & Dual-Control Quorum Architecture" in text
        assert "Zero Standing Privileges (ZSP)" in text
        assert "Dual-Control Quorum" in text
        assert "Ed25519" in text
        assert "solutions@devsupersuite.com" in text

    def test_brand_anonymity_invariants(self):
        """
        Enforce strict institutional brand anonymity:
        Must NOT contain personal names or unauthorized personal email domains.
        Must strictly represent DevSuperSuite Solutions Architecture / OmniKernel Labs.
        """
        forbidden_terms = ["github.com/", "gitlab.com/", "@gmail.com", "@yahoo.com", "@hotmail.com"]
        files_to_check = [
            SERVICES_DIR / "enterprise_zero_trust_bastion_engine.py",
            BASTION_DIR / "bastion_policy_manifest.json",
            REPORTS_DIR / "zero_trust_bastion_report.md"
        ]

        for filepath in files_to_check:
            assert filepath.exists(), f"Expected file {filepath} to exist."
            content = filepath.read_text(encoding="utf-8")

            for term in forbidden_terms:
                assert term not in content.lower(), f"Forbidden term '{term}' found in {filepath.name}"

            assert "DevSuperSuite" in content or "OmniKernel Labs" in content, (
                f"Missing institutional brand in {filepath.name}"
            )
            assert "solutions@devsupersuite.com" in content, (
                f"Missing official contact in {filepath.name}"
            )

    def test_cli_flags_execution(self):
        """Ensure all CLI interface flags execute cleanly with exit code 0."""
        python_exe = sys.executable
        script = str(SERVICES_DIR / "enterprise_zero_trust_bastion_engine.py")

        commands = [
            [python_exe, script, "--summary"],
            [python_exe, script, "--request-access", "k8s-prod-cluster", "Emergency schema check"],
            [python_exe, script, "--simulate-bastion-session", "JIT-CLI-01"],
            [python_exe, script, "--export-bastion-bundle"]
        ]

        for cmd in commands:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            assert res.returncode == 0, f"Command failed: {' '.join(cmd)}\nStderr: {res.stderr}"
            assert len(res.stdout) > 0
