#!/usr/bin/env python3
"""
Unit and Integration Tests for Enterprise Solution Sizing & Hardware Calculator
Reference: tests/test_solution_sizing_calculator.py
Classification: Automated Quality Gate (100% Pass Required)
Contact: solutions@devsupersuite.com
"""

import re
import shutil
import tempfile
from pathlib import Path
import pytest

from services.enterprise_solution_sizing_calculator import (
    EnterpriseSizingEngine,
    SizingReportExporter,
    run_cli,
    DEFAULT_TOKEN_COST_PER_M,
    TOKEN_COMPRESSION_RATIO,
    MIN_REPLICAS
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Tier Categorization Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_tier_categorization():
    engine = EnterpriseSizingEngine
    assert "Tier 1" in engine.determine_tier_name(50)
    assert "Tier 1" in engine.determine_tier_name(250)
    assert "Tier 2" in engine.determine_tier_name(251)
    assert "Tier 2" in engine.determine_tier_name(1000)
    assert "Tier 3" in engine.determine_tier_name(1001)
    assert "Tier 3" in engine.determine_tier_name(10000)
    assert "Tier 4" in engine.determine_tier_name(10001)
    assert "Tier 4" in engine.determine_tier_name(50000)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Workload Metrics & Dimensioning Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_workload_metrics_calculation():
    engine = EnterpriseSizingEngine
    w = engine.calculate_workload_metrics(1000)

    assert w["active_developers"] == 1000
    assert w["peak_concurrent_developers"] == 350
    assert w["peak_qps"] > 0
    assert w["burst_qps"] > w["peak_qps"]

    k8s = w["kubernetes_sizing"]
    assert k8s["min_replicas"] == MIN_REPLICAS
    assert k8s["recommended_replicas"] >= MIN_REPLICAS
    assert k8s["max_replicas"] > k8s["recommended_replicas"]
    assert k8s["cpu_cores_limit"] >= k8s["cpu_cores_requested"]
    assert k8s["ram_gb_limit"] >= k8s["ram_gb_requested"]

    storage = w["storage_sizing"]
    assert storage["recommended_pv_storage_gb"] >= 50
    assert storage["daily_telemetry_mb"] > 0

    net = w["network_sizing"]
    assert net["peak_bandwidth_mbps"] > 0
    assert net["burst_bandwidth_mbps"] > net["peak_bandwidth_mbps"]


# ─────────────────────────────────────────────────────────────────────────────
# 3. Cloud Hardware Mapping Tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("dev_count", [150, 500, 5000, 25000])
def test_cloud_hardware_mapping(dev_count):
    engine = EnterpriseSizingEngine
    w = engine.calculate_workload_metrics(dev_count)
    hw = engine.calculate_cloud_hardware_mapping(w)

    assert "on_premise_scif" in hw
    assert "aws_govcloud_eks" in hw
    assert "azure_sovereign_aks" in hw
    assert "gcp_private_gke" in hw

    # Check on-premise SCIF fields
    scif = hw["on_premise_scif"]
    assert "servers" in scif
    assert "cpu" in scif
    assert "ram" in scif
    assert "storage" in scif
    assert "gpu_inference" in scif

    # Check AWS fields
    aws = hw["aws_govcloud_eks"]
    assert aws["nodes_count"] >= 2
    assert aws["vcpus_total"] >= 16
    assert aws["ram_gb_total"] >= 64


# ─────────────────────────────────────────────────────────────────────────────
# 4. Token Cost-Benefit & ROI Analysis Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_token_roi_math_accuracy():
    engine = EnterpriseSizingEngine
    devs = 1000
    rate = 10.00
    roi = engine.calculate_token_roi(devs=devs, token_cost_per_m=rate)

    vols = roi["volumes"]
    fin = roi["financials"]

    # 1,000 devs * 2,500,000 tokens = 2.5 Billion tokens/month
    assert vols["monthly_uncompressed_tokens"] == 2_500_000_000

    # 72% pruning
    expected_saved = int(2_500_000_000 * 0.720)
    assert vols["monthly_tokens_saved"] == expected_saved

    # Cost uncompressed: 2.5B / 1M * $10 = $25,000/month
    assert fin["monthly_uncompressed_token_cost_usd"] == 25000.00
    # Cost compressed: 700M / 1M * $10 = $7,000/month
    assert fin["monthly_compressed_token_cost_usd"] == 7000.00
    # Monthly savings: $18,000/month
    assert fin["monthly_direct_token_savings_usd"] == 18000.00
    # Annual savings: $18,000 * 12 = $216,000/year
    assert fin["annual_direct_token_savings_usd"] == 216000.00

    # Productivity recovery: 1,000 * 15 * $100 = $1,500,000/year
    assert fin["annual_productivity_recovery_usd"] == 1500000.00
    # Gross annual benefit: $216,000 + $1,500,000 = $1,716,000/year
    assert fin["gross_annual_economic_benefit_usd"] == 1716000.00

    assert fin["net_roi_percentage"] > 0.0
    assert fin["payback_period_months"] < 12.0


# ─────────────────────────────────────────────────────────────────────────────
# 5. Brand Anonymity Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_brand_anonymity_invariants():
    script_path = Path(r"C:\Users\atpad\.gemini\antigravity\scratch\agent-commerce\services\enterprise_solution_sizing_calculator.py")
    matrix_path = Path(r"C:\Users\atpad\.gemini\antigravity\scratch\agent-commerce\services\enterprise_hardware_dimensioning_matrix.md")

    for p in [script_path, matrix_path]:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        
        # Verify mandatory corporate brand entities
        assert "DevSuperSuite" in text
        assert "OmniKernel Labs" in text

        # Verify no personal phone numbers (e.g. +1-xxx, 555-xxxx)
        assert not re.search(r"\+1[- ]?\d{3}[- ]?\d{3}[- ]?\d{4}", text)
        assert not re.search(r"\b\d{3}[-.]\d{3}[-.]\d{4}\b", text)

        # Verify no individual personal names or email domains other than official
        assert "solutions@devsupersuite.com" in text or "cloud@devsupersuite.com" in text
        assert "gmail.com" not in text
        assert "yahoo.com" not in text
        assert "hotmail.com" not in text


# ─────────────────────────────────────────────────────────────────────────────
# 6. Report Exporting Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_export_markdown_reports():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_sizing_test_"))
    try:
        mat_path = temp_dir / "test_matrix.md"
        spec_path = temp_dir / "test_spec.md"

        SizingReportExporter.export_hardware_dimensioning_matrix(mat_path)
        assert mat_path.exists()
        mat_text = mat_path.read_text(encoding="utf-8")
        assert "Enterprise Hardware Dimensioning" in mat_text
        assert "Tier 1: Team / BU" in mat_text
        assert "AWS GovCloud / EKS" in mat_text

        SizingReportExporter.export_cluster_sizing_spec(
            devs=2500,
            output_path=spec_path,
            customer_name="Raytheon Space Systems"
        )
        assert spec_path.exists()
        spec_text = spec_path.read_text(encoding="utf-8")
        assert "Raytheon Space Systems" in spec_text
        assert "2,500 Active Engineers" in spec_text
        assert "Kubernetes Enclave Resource Requirements" in spec_text
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# 7. CLI Execution Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_cli_execution_all_flags():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_cli_sizing_"))
    try:
        mat_file = temp_dir / "cli_matrix.md"
        spec_file = temp_dir / "cli_spec.md"

        ret = run_cli([
            "--calculate-sizing",
            "--export-hardware-matrix",
            "--generate-roi-sheet",
            "--summary",
            "--developers", "800",
            "--token-cost", "12.50",
            "--customer", "General Dynamics Land Systems",
            "--output-matrix", str(mat_file),
            "--output-spec", str(spec_file)
        ])

        assert ret == 0
        assert mat_file.exists()
        assert spec_file.exists()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
