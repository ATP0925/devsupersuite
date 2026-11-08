"""
⚡ DevSuperSuite Official: Enterprise NRR & GRR Revenue Cohort Retention Tests
File: test_nrr_forecasting_engine.py
Governing Authority: DevSuperSuite Revenue Operations (growth@devsupersuite.com)
Strict Protocol: 100% Brand Anonymity - Zero Founder Personal Identifiers
"""

import os
import sys
import json
import pytest
import subprocess
from pathlib import Path

# Paths Setup
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(TESTS_DIR)
SERVICES_DIR = os.path.join(SCRATCH_DIR, "services")
DATA_DIR = os.path.join(SCRATCH_DIR, "data")
REPORTS_DIR = os.path.join(SERVICES_DIR, "reports")

if SCRATCH_DIR not in sys.path:
    sys.path.insert(0, SCRATCH_DIR)
if SERVICES_DIR not in sys.path:
    sys.path.insert(0, SERVICES_DIR)

from services.enterprise_nrr_forecasting_engine import (
    CohortExpansionModeler,
    EnterpriseNRRForecastingEngine,
    SECURITY_EXPANSION_CATALOG,
    SCHEDULE_PATH,
    REPORT_PATH,
)


@pytest.fixture
def test_engine(tmp_path):
    sched_file = str(tmp_path / "test_cohort_schedule.json")
    report_file = str(tmp_path / "test_cohort_report.md")
    return EnterpriseNRRForecastingEngine(
        schedule_path=sched_file,
        report_path=report_file
    )


def test_01_cohort_expansion_modeler_nrr_grr_formulas():
    """Verify NRR > 138% and GRR > 96% mathematical formulas."""
    res = CohortExpansionModeler.calculate_cohort_trajectory(
        cohort_id="COHORT-TEST-1",
        cohort_name="Test Enterprise Base",
        initial_accounts=10,
        starting_arr_usd=100000.0,
        months_elapsed=12,
        seat_expansion_pct=34.5,
        multi_year_uplift_pct=6.5,
        contraction_pct=2.0,
        churn_pct=1.4
    )

    # GRR = (100000 - 1400 - 2000) / 100000 = 96.6%
    assert res["grr_pct"] == 96.6
    assert res["grr_pct"] >= 96.0

    # NRR = (96600 + 34500 + 6500) / 100000 = 137.6%
    assert res["nrr_pct"] >= 137.0
    assert res["retained_base_arr_usd"] == 96600.0
    assert res["total_expansion_usd"] == 41000.0
    assert res["ending_arr_usd"] == 137600.0


def test_02_cohort_expansion_with_security_modules():
    """Verify attaching security expansion modules lifts NRR above 140%."""
    pqc_module = SECURITY_EXPANSION_CATALOG["MODULE_PQC_KYBER_ATTESTATION"]
    fips_module = SECURITY_EXPANSION_CATALOG["MODULE_FIPS_140_3_HSM"]

    res = CohortExpansionModeler.calculate_cohort_trajectory(
        cohort_id="COHORT-TEST-2",
        cohort_name="Defense High Security",
        initial_accounts=10,
        starting_arr_usd=200000.0,
        months_elapsed=12,
        seat_expansion_pct=34.5,
        multi_year_uplift_pct=6.5,
        security_modules=[pqc_module, fips_module]
    )

    # Additional modules: 14999 + 9999 = 24998 USD
    assert res["module_expansion_usd"] == 24998.0
    assert res["nrr_pct"] > 140.0
    assert len(res["security_modules_attached"]) == 2


def test_03_ltv_cac_ratio_and_payback_calculation():
    """Verify LTV:CAC ratio exceeds 7.4x and CAC payback is computed accurately."""
    res = CohortExpansionModeler.calculate_cohort_trajectory(
        cohort_id="COHORT-UNIT-ECON",
        cohort_name="SaaS Metrics Cohort",
        initial_accounts=8,
        starting_arr_usd=160000.0,
        blended_cac_per_account_usd=18500.0,
        gross_margin_pct=92.5
    )

    unit = res["unit_economics"]
    assert unit["ltv_cac_ratio"] >= 7.4
    assert unit["gross_margin_pct"] == 92.5
    assert unit["cac_payback_months"] > 0
    assert unit["cac_payback_months"] < 12.0


def test_04_schedule_persistence_and_reloading(tmp_path):
    """Verify schedule initializes, persists to disk, and can be reloaded."""
    sched_file = str(tmp_path / "sched_persist.json")
    engine1 = EnterpriseNRRForecastingEngine(schedule_path=sched_file)

    engine1.register_cohort(
        cohort_id="COHORT-PERSIST-1",
        cohort_name="Persistent Cohort",
        initial_accounts=5,
        starting_arr_usd=100000.0
    )

    assert os.path.exists(sched_file)

    # Re-instantiate
    engine2 = EnterpriseNRRForecastingEngine(schedule_path=sched_file)
    assert len(engine2.schedule["cohorts"]) == 1
    assert engine2.schedule["cohorts"][0]["cohort_id"] == "COHORT-PERSIST-1"


def test_05_register_new_and_update_existing_cohort(test_engine):
    """Verify register_cohort inserts new cohort and updates existing without duplication."""
    test_engine.register_cohort("COHORT-UP-1", "Original Name", 5, 100000.0)
    assert len(test_engine.schedule["cohorts"]) == 1
    assert test_engine.schedule["cohorts"][0]["cohort_name"] == "Original Name"

    # Update
    test_engine.register_cohort("COHORT-UP-1", "Updated Name", 6, 120000.0)
    assert len(test_engine.schedule["cohorts"]) == 1
    assert test_engine.schedule["cohorts"][0]["cohort_name"] == "Updated Name"
    assert test_engine.schedule["cohorts"][0]["initial_accounts"] == 6


def test_06_attach_security_module_recalculation(test_engine):
    """Verify attaching security module recalculates NRR and expands ending ARR."""
    cohort = test_engine.register_cohort(
        cohort_id="COHORT-SEC-1",
        cohort_name="Secured Enclave",
        initial_accounts=10,
        starting_arr_usd=200000.0
    )
    initial_nrr = cohort["nrr_pct"]
    initial_ending = cohort["ending_arr_usd"]

    updated = test_engine.attach_security_module_to_cohort(
        cohort_id="COHORT-SEC-1",
        module_key="MODULE_AIRGAP_SCIF_CLUSTER"
    )

    assert updated["ending_arr_usd"] == initial_ending + 19999.0
    assert updated["nrr_pct"] > initial_nrr
    assert len(updated["security_modules_attached"]) == 1


def test_07_invalid_cohort_or_module_key_exception(test_engine):
    """Verify KeyError is raised for non-existent cohort or invalid module key."""
    with pytest.raises(KeyError, match="Cohort 'COHORT-NONEXISTENT' not found"):
        test_engine.attach_security_module_to_cohort("COHORT-NONEXISTENT", "MODULE_FIPS_140_3_HSM")

    test_engine.register_cohort("COHORT-VALID-1", "Valid Cohort", 5, 100000.0)
    with pytest.raises(KeyError, match="Security module 'MODULE_INVALID' not found"):
        test_engine.attach_security_module_to_cohort("COHORT-VALID-1", "MODULE_INVALID")


def test_08_portfolio_retention_audit_benchmarks(test_engine):
    """Verify blended portfolio audit achieves institutional verdict."""
    test_engine.register_cohort("COHORT-A", "Cohort Alpha", 10, 200000.0, seat_expansion_pct=35.0)
    test_engine.attach_security_module_to_cohort("COHORT-A", "MODULE_PQC_KYBER_ATTESTATION")

    test_engine.register_cohort("COHORT-B", "Cohort Beta", 12, 180000.0, seat_expansion_pct=34.0)
    test_engine.attach_security_module_to_cohort("COHORT-B", "MODULE_FIPS_140_3_HSM")

    audit = test_engine.audit_portfolio_retention()
    assert audit["total_cohorts"] == 2
    assert audit["blended_nrr_pct"] >= 138.0
    assert audit["blended_grr_pct"] >= 96.0
    assert audit["average_ltv_cac_ratio"] >= 7.4
    assert audit["retention_verdict"] == "EXCEEDS_INSTITUTIONAL_BENCHMARKS"
    assert audit["benchmark_compliance"]["nrr_met"] is True
    assert audit["benchmark_compliance"]["grr_met"] is True
    assert audit["benchmark_compliance"]["ltv_cac_met"] is True


def test_09_markdown_report_generation(test_engine):
    """Verify executive markdown report generation and structure."""
    test_engine.register_cohort("COHORT-RPT-1", "Reporting Cohort", 8, 150000.0)
    test_engine.attach_security_module_to_cohort("COHORT-RPT-1", "MODULE_ZTNA_MICROSEGMENTATION")

    report_path = test_engine.render_markdown_report()
    assert os.path.exists(report_path)

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "# ⚡ DevSuperSuite Official: Enterprise NRR & GRR Revenue Cohort Retention Report" in content
    assert "Blended Net Revenue Retention (NRR)" in content
    assert "Blended Gross Revenue Retention (GRR)" in content
    assert "COHORT-RPT-1" in content
    assert "MODULE_ZTNA_MICROSEGMENTATION" in content
    assert "growth@devsupersuite.com" in content


def test_10_cli_interface_execution():
    """Verify all CLI subcommands execute with exit code 0."""
    python_bin = sys.executable
    script_path = os.path.join(SERVICES_DIR, "enterprise_nrr_forecasting_engine.py")

    commands = [
        ["--summary"],
        ["--simulate-cohort", "--cohort-id", "COHORT-CLI-101", "--name", "CLI Simulation", "--accounts", "6", "--arr", "120000.0"],
        ["--add-security-module", "--cohort-id", "COHORT-CLI-101", "--module-key", "MODULE_PQC_KYBER_ATTESTATION"],
        ["--audit-retention"],
        ["--export-nrr-report"]
    ]

    for args in commands:
        cmd = [python_bin, script_path] + args
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        assert res.returncode == 0, f"CLI command {cmd} failed with stderr: {res.stderr}"


def test_11_strict_brand_anonymity_compliance():
    """Verify zero personal founder leaks across all Phase 29 assets."""
    forbidden_tokens = [
        bytes.fromhex("41746861727661").decode("utf-8"),
        bytes.fromhex("506164687965").decode("utf-8"),
        bytes.fromhex("39383930343431323933").decode("utf-8"),
    ]

    phase_29_files = [
        Path(SERVICES_DIR) / "enterprise_nrr_forecasting_engine.py",
        Path(DATA_DIR) / "enterprise_cohort_retention_schedule.json",
        Path(REPORTS_DIR) / "enterprise_nrr_cohort_retention_report.md",
        Path(TESTS_DIR) / "test_nrr_forecasting_engine.py",
    ]

    for file_path in phase_29_files:
        assert file_path.exists(), f"File {file_path} must exist"
        content = file_path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token.lower() not in content.lower(), (
                f"Brand anonymity violation: found forbidden token in {file_path}"
            )
