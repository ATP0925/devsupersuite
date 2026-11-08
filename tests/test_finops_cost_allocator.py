#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Multi-Tenant FinOps Cost Allocator Test Suite
Reference: DSS-TEST-FINOPS-ALLOCATOR-2026
Classification: Multi-Tenant Cloud & Sovereign GPU Cost Attribution
Contact: DevSuperSuite Solutions Architecture (solutions@devsupersuite.com)
═══════════════════════════════════════════════════════════════════════════════
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = REPO_ROOT / "services"
REPORTS_DIR = SERVICES_DIR / "reports"
DEPLOYMENT_DIR = REPO_ROOT / "deployment"
FINOPS_DIR = DEPLOYMENT_DIR / "finops"

MATRIX_FILE = FINOPS_DIR / "departmental_chargeback_matrix.json"
GUIDE_FILE = SERVICES_DIR / "enterprise_finops_governance_guide.md"
REPORT_FILE = REPORTS_DIR / "finops_cost_allocation_report.md"

sys.path.insert(0, str(SERVICES_DIR))
from enterprise_finops_cost_allocator import (
    FinOpsCostAllocator,
    TenantWorkloadProfile,
    TokenSiliconTCOModeler,
    CLOUD_RATE_CARDS,
    MIG_SLICE_FRACTIONS,
    export_chargeback_matrix,
    export_finops_governance_guide,
    export_finops_report,
    BILLING_HOURS_PER_MONTH,
    AST_TOKEN_REDUCTION_RATIO
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Rate Card & MIG Slicing Math Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_cloud_rate_card_pricing_integrity():
    """Validates rate cards across AWS, GCP, and Azure."""
    for cloud in ["AWS", "GCP", "Azure"]:
        assert cloud in CLOUD_RATE_CARDS
        rc = CLOUD_RATE_CARDS[cloud]
        assert rc["vcpu_hourly"] > 0.03
        assert rc["ram_gib_hourly"] > 0.003
        assert "NVIDIA_A100_80GB" in rc["gpus"]
        assert rc["gpus"]["NVIDIA_A100_80GB"] > 2.0
        assert "NVIDIA_H100_SXM5" in rc["gpus"]
        assert rc["gpus"]["NVIDIA_H100_SXM5"] > 3.0


def test_gpu_mig_slice_fractions():
    """Verifies that MIG slicing multipliers match hardware partitions."""
    assert MIG_SLICE_FRACTIONS["1g.10gb"] == pytest.approx(1.0 / 7.0, rel=1e-3)
    assert MIG_SLICE_FRACTIONS["2g.20gb"] == pytest.approx(2.0 / 7.0, rel=1e-3)
    assert MIG_SLICE_FRACTIONS["3g.40gb"] == pytest.approx(3.0 / 7.0, rel=1e-3)
    assert MIG_SLICE_FRACTIONS["4g.40gb"] == pytest.approx(4.0 / 7.0, rel=1e-3)
    assert MIG_SLICE_FRACTIONS["7g.80gb"] == 1.0
    assert MIG_SLICE_FRACTIONS["full"] == 1.0


# ─────────────────────────────────────────────────────────────────────────────
# 2. Multi-Tenant Departmental Cost Attribution Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_tenant_workload_cost_calculation():
    """Tests cost calculation math for an individual departmental workload."""
    allocator = FinOpsCostAllocator()
    profile = TenantWorkloadProfile(
        tenant_id="TENANT-TEST",
        department_name="Test Engineering",
        namespace="tenant-test",
        cloud_provider="AWS",
        cluster_id="eks-test",
        allocated_vcpu=10,
        allocated_ram_gib=40,
        gpu_model="NVIDIA_A100_80GB",
        gpu_count=1,
        gpu_mig_slice="2g.20gb",
        p95_utilized_vcpu=8.0,
        p95_utilized_ram_gib=30.0,
        p95_utilized_gpu_pct=80.0
    )

    cost = allocator.calculate_tenant_cost(profile)

    expected_vcpu = 10 * CLOUD_RATE_CARDS["AWS"]["vcpu_hourly"] * BILLING_HOURS_PER_MONTH
    expected_ram = 40 * CLOUD_RATE_CARDS["AWS"]["ram_gib_hourly"] * BILLING_HOURS_PER_MONTH
    expected_gpu = (1 * CLOUD_RATE_CARDS["AWS"]["gpus"]["NVIDIA_A100_80GB"] * (2.0 / 7.0)) * BILLING_HOURS_PER_MONTH

    assert cost["vcpu_cost"] == pytest.approx(expected_vcpu, rel=1e-2)
    assert cost["ram_cost"] == pytest.approx(expected_ram, rel=1e-2)
    assert cost["gpu_cost"] == pytest.approx(expected_gpu, rel=1e-2)
    assert cost["total_monthly_cost"] == pytest.approx(expected_vcpu + expected_ram + expected_gpu, rel=1e-2)


def test_idle_waste_detection_and_right_sizing():
    """Tests that low utilization triggers right-sizing recommendations and calculates savings."""
    allocator = FinOpsCostAllocator()
    # Heavily over-provisioned tenant: 64 vCPU allocated, only 10 used
    profile = TenantWorkloadProfile(
        tenant_id="TENANT-OVERPROVISIONED",
        department_name="Legacy Apps",
        namespace="tenant-legacy",
        cloud_provider="AWS",
        cluster_id="eks-test",
        allocated_vcpu=64,
        allocated_ram_gib=256,
        gpu_model=None,
        gpu_count=0,
        gpu_mig_slice="full",
        p95_utilized_vcpu=10.0,
        p95_utilized_ram_gib=32.0,
        p95_utilized_gpu_pct=0.0
    )

    cost = allocator.calculate_tenant_cost(profile)
    assert cost["potential_monthly_savings"] > 1000.0
    assert cost["idle_waste_percentage"] > 50.0

    rec = cost["recommendation"]
    # 10.0 * 1.25 = 13 vCPU
    assert rec["target_vcpu"] == 13
    # 32.0 * 1.25 = 40 GiB
    assert rec["target_ram_gib"] == 40


def test_enterprise_chargeback_matrix_aggregation():
    """Validates full enterprise departmental aggregation across all active tenants."""
    allocator = FinOpsCostAllocator()
    res = allocator.generate_all_allocations()

    assert res["tenant_count"] == 4
    assert res["total_enterprise_monthly_spend"] > 15000.0
    assert res["total_potential_monthly_savings"] > 2000.0
    assert 0.0 < res["average_idle_waste_pct"] < 50.0

    # Ensure sum of breakdowns equals total
    breakdowns = res["departmental_breakdowns"]
    sum_total = sum(b["total_monthly_cost"] for b in breakdowns)
    assert res["total_enterprise_monthly_spend"] == pytest.approx(sum_total, rel=1e-2)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Token-to-Silicon TCO & Hardware ROI Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_token_deflection_roi_calculation():
    """Verifies 72% AST token reduction calculations and annual deflection savings."""
    roi = TokenSiliconTCOModeler.calculate_token_deflection_roi(
        developer_count=500,
        baseline_cloud_api_cost_per_dev_monthly=750.0,
        token_reduction_rate=0.72
    )

    assert roi["developer_count"] == 500
    assert roi["monthly_spend_before"] == 375000.0  # 500 * $750
    assert roi["monthly_savings"] == 270000.0       # $375,000 * 0.72
    assert roi["monthly_spend_after"] == 105000.0   # $375,000 - $270,000
    assert roi["annual_savings"] == 3240000.0       # $270,000 * 12


def test_workstation_amortization_tco_and_payback():
    """Verifies 36-month workstation TCO amortization and sub-14-month ROI payback."""
    tco = TokenSiliconTCOModeler.calculate_workstation_amortization_tco(
        hardware_type="Apple_Silicon_M3_Max",
        acquisition_cost=4800.0,
        monthly_power_cooling_cost=12.0,
        amortization_months=36,
        cloud_gpu_alternative_monthly=392.0
    )

    # 4800 / 36 = 133.33
    assert tco["monthly_depreciation"] == pytest.approx(133.33, rel=1e-2)
    # 133.33 + 12 = 145.33
    assert tco["total_monthly_tco"] == pytest.approx(145.33, rel=1e-2)
    # 392 - 145.33 = 246.67
    assert tco["monthly_net_savings_per_seat"] == pytest.approx(246.67, rel=1e-2)
    # Payback: 4800 / (392 - 12) = 12.63 months
    assert tco["payback_period_months"] == pytest.approx(12.6, rel=1e-1)
    assert tco["payback_period_months"] <= 14.0


# ─────────────────────────────────────────────────────────────────────────────
# 4. JSON Chargeback Matrix & Exporter Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_chargeback_matrix_json_export():
    """Verifies JSON matrix structure, organization header, and tenant mappings."""
    allocator = FinOpsCostAllocator()
    allocations = allocator.generate_all_allocations()
    matrix_path = export_chargeback_matrix(allocations)

    assert matrix_path.exists()
    data = json.loads(matrix_path.read_text(encoding="utf-8"))
    assert data["organization"] == "DevSuperSuite Solutions Architecture / OmniKernel Labs"
    assert data["contact"] == "solutions@devsupersuite.com"
    assert data["currency"] == "USD"
    assert len(data["tenants"]) == 4


def test_finops_guide_and_report_export():
    """Tests platform guide and report export integrity."""
    allocator = FinOpsCostAllocator()
    allocations = allocator.generate_all_allocations()
    token_roi = TokenSiliconTCOModeler.calculate_token_deflection_roi()
    workstation_tco = TokenSiliconTCOModeler.calculate_workstation_amortization_tco()

    guide_path = export_finops_governance_guide()
    report_path = export_finops_report(allocations, token_roi, workstation_tco)

    assert guide_path.exists()
    assert report_path.exists()
    assert "DSS-FINOPS-GOVERNANCE-RUNBOOK-2026" in guide_path.read_text(encoding="utf-8")
    assert "DSS-FINOPS-REPORT-2026-V1" in report_path.read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Brand Anonymity Invariants Test
# ─────────────────────────────────────────────────────────────────────────────

def test_brand_anonymity_invariants():
    """Asserts 100% Brand Anonymity across all newly authored FinOps artifacts."""
    files_to_check = [
        SERVICES_DIR / "enterprise_finops_cost_allocator.py",
        GUIDE_FILE,
        REPORT_FILE,
        MATRIX_FILE
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
    """Tests execution of the FinOps cost allocator CLI across all mandatory flags."""
    flags_to_test = [
        ["--calculate-allocations"],
        ["--model-silicon-roi"],
        ["--generate-chargeback-invoice"],
        ["--audit-idle-waste"],
        ["--export-finops-bundle"],
        ["--summary"]
    ]

    engine_script = SERVICES_DIR / "enterprise_finops_cost_allocator.py"

    for flag_list in flags_to_test:
        cmd = [sys.executable, str(engine_script)] + flag_list
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, f"CLI command failed with code {proc.returncode}: {proc.stderr}"
        assert "DevSuperSuite" in proc.stdout
