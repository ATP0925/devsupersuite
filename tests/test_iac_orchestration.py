#!/usr/bin/env python3
"""
Unit and Integration Tests for Enterprise IaC Orchestrator
Reference: tests/test_iac_orchestration.py
Classification: Multi-Cloud Automated Assurance Quality Gate (100% Pass)
Contact: cloud@devsupersuite.com
"""

import json
import shutil
import tempfile
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.enterprise_iac_orchestrator import (
    IaCModuleInspector,
    IaCStructuralValidator,
    SecurityRulesAuditor,
    DeploymentManifestGenerator,
    run_cli,
    DEFAULT_TERRAFORM_DIR
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Module Inspector Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_module_inspector_file_discovery():
    inspector = IaCModuleInspector(DEFAULT_TERRAFORM_DIR)
    
    for provider in ["aws", "gcp", "azure"]:
        files = inspector.get_module_files(provider)
        assert len(files) >= 4, f"Provider {provider} should have at least 4 .tf files"
        filenames = {f.name for f in files}
        assert "main.tf" in filenames
        assert "variables.tf" in filenames
        assert "outputs.tf" in filenames


def test_module_inspector_deterministic_checksums():
    inspector = IaCModuleInspector(DEFAULT_TERRAFORM_DIR)
    c1 = inspector.calculate_module_checksums("aws")
    c2 = inspector.calculate_module_checksums("aws")

    assert c1["module_checksum"] == c2["module_checksum"]
    assert len(c1["module_checksum"]) == 64
    assert c1["file_count"] >= 4


# ─────────────────────────────────────────────────────────────────────────────
# 2. Structural Validator Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_structural_validator_aws_pass():
    inspector = IaCModuleInspector(DEFAULT_TERRAFORM_DIR)
    validator = IaCStructuralValidator(inspector)
    res = validator.validate_aws_module()

    assert res["is_valid"] is True
    assert len(res["violations"]) == 0
    assert len(res["checks_passed"]) >= 4


def test_structural_validator_gcp_pass():
    inspector = IaCModuleInspector(DEFAULT_TERRAFORM_DIR)
    validator = IaCStructuralValidator(inspector)
    res = validator.validate_gcp_module()

    assert res["is_valid"] is True
    assert len(res["violations"]) == 0
    assert len(res["checks_passed"]) >= 4


def test_structural_validator_azure_pass():
    inspector = IaCModuleInspector(DEFAULT_TERRAFORM_DIR)
    validator = IaCStructuralValidator(inspector)
    res = validator.validate_azure_module()

    assert res["is_valid"] is True
    assert len(res["violations"]) == 0
    assert len(res["checks_passed"]) >= 4


def test_structural_validator_validate_all():
    inspector = IaCModuleInspector(DEFAULT_TERRAFORM_DIR)
    validator = IaCStructuralValidator(inspector)
    res = validator.validate_all("all")

    assert res["status"] == "VALID"
    assert res["all_valid"] is True
    assert "aws" in res["provider_results"]
    assert "gcp" in res["provider_results"]
    assert "azure" in res["provider_results"]


def test_structural_validator_detects_violations_on_empty_dir():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_empty_tf_"))
    try:
        empty_inspector = IaCModuleInspector(temp_dir)
        validator = IaCStructuralValidator(empty_inspector)
        res = validator.validate_aws_module()
        assert res["is_valid"] is False
        assert len(res["violations"]) > 0
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Security Rules & Egress Auditor Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_security_rules_auditor_aws_zero_egress_pass():
    inspector = IaCModuleInspector(DEFAULT_TERRAFORM_DIR)
    auditor = SecurityRulesAuditor(inspector)
    res = auditor.audit_aws_security_groups()

    assert res["zero_egress_enforced"] is True
    assert len(res["violations"]) == 0
    assert res["egress_rules_audited"] >= 2


def test_security_rules_auditor_gcp_zero_egress_pass():
    inspector = IaCModuleInspector(DEFAULT_TERRAFORM_DIR)
    auditor = SecurityRulesAuditor(inspector)
    res = auditor.audit_gcp_firewall_rules()

    assert res["zero_egress_enforced"] is True
    assert len(res["violations"]) == 0
    assert res["firewall_resources_audited"] >= 2


def test_security_rules_auditor_azure_zero_egress_pass():
    inspector = IaCModuleInspector(DEFAULT_TERRAFORM_DIR)
    auditor = SecurityRulesAuditor(inspector)
    res = auditor.audit_azure_nsg_rules()

    assert res["zero_egress_enforced"] is True
    assert len(res["violations"]) == 0
    assert res["nsg_rules_audited"] >= 2


def test_security_rules_auditor_audit_all():
    inspector = IaCModuleInspector(DEFAULT_TERRAFORM_DIR)
    auditor = SecurityRulesAuditor(inspector)
    res = auditor.audit_all("all")

    assert res["status"] == "COMPLIANT"
    assert res["zero_egress_certified"] is True


def test_security_rules_auditor_detects_insecure_aws_egress():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_bad_aws_"))
    try:
        aws_dir = temp_dir / "aws"
        aws_dir.mkdir(parents=True)
        bad_sg = """
        resource "aws_security_group" "bad_sg" {
          egress {
            from_port = 0
            to_port = 0
            protocol = "-1"
            cidr_blocks = ["0.0.0.0/0"]
          }
        }
        """
        (aws_dir / "bad_sg.tf").write_text(bad_sg, encoding="utf-8")
        auditor = SecurityRulesAuditor(IaCModuleInspector(temp_dir))
        res = auditor.audit_aws_security_groups()

        assert res["zero_egress_enforced"] is False
        assert any("0.0.0.0/0" in v for v in res["violations"])
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Deployment Manifest Generator Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_deployment_manifest_generator():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_manifest_"))
    try:
        out_manifest = temp_dir / "manifest.json"
        generator = DeploymentManifestGenerator(IaCModuleInspector(DEFAULT_TERRAFORM_DIR))
        manifest = generator.generate_manifest(
            customer_name="Northrop Grumman Mission Systems",
            output_path=out_manifest
        )

        assert out_manifest.exists()
        assert manifest["customer_organization"] == "Northrop Grumman Mission Systems"
        assert manifest["manifest_id"].startswith("IAC-PLAN-2026-")
        assert len(manifest["master_plan_checksum"]) == 64
        assert manifest["security_invariants"]["zero_public_egress"] == "ENFORCED"
        assert manifest["arb_approval_state"] == "PRE_APPROVED_AIRGAP_CERTIFIED"
        assert "aws" in manifest["modules"]
        assert "gcp" in manifest["modules"]
        assert "azure" in manifest["modules"]
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# 5. CLI Gateway Integration Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_cli_execution_all_flags():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_cli_iac_"))
    try:
        out_manifest = temp_dir / "cli_manifest.json"
        ret = run_cli([
            "--validate-iac",
            "--audit-security-rules",
            "--generate-deployment-manifest",
            "--summary",
            "--customer", "Lockheed Space Technologies",
            "--output", str(out_manifest)
        ])

        assert ret == 0
        assert out_manifest.exists()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
