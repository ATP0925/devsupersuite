#!/usr/bin/env python3
"""
Unit and Integration Tests for Enterprise VPC Migration Engine
Reference: tests/test_enterprise_vpc_migration.py
Classification: Automated Quality Gate (100% Pass Required)
Contact: cloud@devsupersuite.com
"""

import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.enterprise_vpc_migration_engine import (
    ArchitecturalModelEvaluator,
    TenantBoundaryValidator,
    VpcMigrationPlanner,
    VpcMigrationReportExporter,
    run_cli
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Architectural Model Evaluator Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_architectural_model_evaluation():
    eval_res = ArchitecturalModelEvaluator.evaluate_models()

    assert "models_evaluated" in eval_res
    models = eval_res["models_evaluated"]

    assert "multi_tenant_saas" in models
    assert "dedicated_customer_vpc" in models
    assert "on_premise_scif" in models

    # Dedicated VPC must exceed Multi-Tenant SaaS in composite security score
    assert models["dedicated_customer_vpc"]["composite_score"] > models["multi_tenant_saas"]["composite_score"]
    assert models["on_premise_scif"]["composite_score"] > models["multi_tenant_saas"]["composite_score"]

    # Check compliance ceilings
    assert "FedRAMP High" in models["dedicated_customer_vpc"]["compliance_ceiling"]
    assert "DoD Impact Level 6" in models["on_premise_scif"]["compliance_ceiling"]
    assert "SOC 2" in models["multi_tenant_saas"]["compliance_ceiling"]


# ─────────────────────────────────────────────────────────────────────────────
# 2. Tenant Boundary Validator Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_tenant_boundary_validator_compliant():
    valid_config = {
        "kms_key_arn": "arn:aws-us-gov:kms:us-gov-west-1:123456789012:key/cmk-sovereign-01",
        "subnet_cidr": "10.100.1.0/24",
        "zero_egress_enforced": True,
        "run_as_user": 10001,
        "private_endpoint_enabled": True
    }
    res = TenantBoundaryValidator.audit_tenant_configuration(valid_config)

    assert res["is_isolated"] is True
    assert res["status"] == "STRICT_SOVEREIGN_ISOLATION_VERIFIED"
    assert len(res["violations"]) == 0
    assert len(res["checks_passed"]) == 5


def test_tenant_boundary_validator_detects_violations():
    # Insecure configuration: missing KMS, public CIDR, permissive egress, root UID, public endpoint
    bad_config = {
        "kms_key_arn": "", # Missing KMS
        "subnet_cidr": "8.8.8.0/24", # Public IP space
        "zero_egress_enforced": False, # Permissive egress
        "run_as_user": 0, # Root execution
        "private_endpoint_enabled": False # Public endpoint
    }
    res = TenantBoundaryValidator.audit_tenant_configuration(bad_config)

    assert res["is_isolated"] is False
    assert res["status"] == "NON_COMPLIANT"
    assert len(res["violations"]) == 5

    violation_texts = " ".join(res["violations"])
    assert "KMS" in violation_texts
    assert "RFC1918" in violation_texts
    assert "Zero-egress" in violation_texts
    assert "10001" in violation_texts
    assert "PrivateLink" in violation_texts


# ─────────────────────────────────────────────────────────────────────────────
# 3. VPC Migration Planner Tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("cloud", ["aws", "azure", "gcp", "scif"])
def test_migration_plan_generation(cloud):
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_mig_test_"))
    try:
        out_plan = temp_dir / f"plan_{cloud}.json"
        plan = VpcMigrationPlanner.generate_migration_plan(
            customer_name="BAE Defense Systems",
            target_cloud=cloud,
            licensed_seats=300,
            output_path=out_plan
        )

        assert out_plan.exists()
        assert plan["plan_id"].startswith("VPC-MIG-")
        assert plan["estimated_total_days"] == 14
        assert plan["guaranteed_downtime_minutes"] == 0
        assert len(plan["phases"]) == 4

        # Verify Manifest Overrides
        manifests = plan["manifest_overrides"]
        assert "helm_values" in manifests
        assert "terraform_snippet" in manifests

        hv = manifests["helm_values"]
        assert hv["securityContext"]["runAsUser"] == 10001
        assert hv["global"]["zeroEgressEnforced"] is True
        assert hv["networkPolicy"]["enforceZeroEgress"] is True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Brand Anonymity Verification
# ─────────────────────────────────────────────────────────────────────────────

def test_brand_anonymity_invariants():
    script_path = Path(r"C:\Users\atpad\.gemini\antigravity\scratch\agent-commerce\services\enterprise_vpc_migration_engine.py")
    runbook_path = Path(r"C:\Users\atpad\.gemini\antigravity\scratch\agent-commerce\services\enterprise_vpc_migration_runbook.md")

    for p in [script_path, runbook_path]:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")

        # Must contain institutional brands
        assert "DevSuperSuite" in text
        assert "OmniKernel Labs" in text

        # Must not contain personal phone numbers or external emails
        assert not re.search(r"\+1[- ]?\d{3}[- ]?\d{3}[- ]?\d{4}", text)
        assert not re.search(r"\b\d{3}[-.]\d{3}[-.]\d{4}\b", text)
        assert "gmail.com" not in text
        assert "yahoo.com" not in text
        assert "hotmail.com" not in text


# ─────────────────────────────────────────────────────────────────────────────
# 5. Report & Runbook Exporter Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_report_and_runbook_exporters():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_rep_mig_"))
    try:
        runbook_out = temp_dir / "runbook.md"
        report_out = temp_dir / "report.md"

        plan = VpcMigrationPlanner.generate_migration_plan("L3Harris Tech", "aws", 200)
        valid_config = {
            "kms_key_arn": "arn:aws-us-gov:kms:us-gov-west-1:123456789012:key/cmk-l3harris",
            "subnet_cidr": "10.200.1.0/24",
            "zero_egress_enforced": True,
            "run_as_user": 10001,
            "private_endpoint_enabled": True
        }
        validation = TenantBoundaryValidator.audit_tenant_configuration(valid_config)

        VpcMigrationReportExporter.export_migration_runbook(runbook_out)
        assert runbook_out.exists()
        rb_text = runbook_out.read_text(encoding="utf-8")
        assert "Enterprise Multi-Tenant vs Dedicated VPC" in rb_text
        assert "Model B: Dedicated Customer VPC" in rb_text

        VpcMigrationReportExporter.export_migration_report(plan, validation, report_out)
        assert report_out.exists()
        rep_text = report_out.read_text(encoding="utf-8")
        assert "DevSuperSuite Enterprise VPC Migration & Isolation Audit Report" in rep_text
        assert "STRICT_SOVEREIGN_ISOLATION_VERIFIED" in rep_text
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# 6. CLI Execution Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_cli_execution_all_flags():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_cli_mig_"))
    try:
        plan_out = temp_dir / "cli_plan.json"
        runbook_out = temp_dir / "cli_runbook.md"
        report_out = temp_dir / "cli_report.md"

        ret = run_cli([
            "--evaluate-isolation-model",
            "--audit-tenant-boundaries",
            "--generate-vpc-migration-plan",
            "--summary",
            "--customer", "Lockheed Titan Aerospace",
            "--target-cloud", "azure",
            "--seats", "400",
            "--output-plan", str(plan_out),
            "--output-runbook", str(runbook_out),
            "--output-report", str(report_out)
        ])

        assert ret == 0
        assert plan_out.exists()
        assert runbook_out.exists()
        assert report_out.exists()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
