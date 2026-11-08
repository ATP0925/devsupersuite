"""
⚡ DevSuperSuite Official: Enterprise ABM Hardware Token & Executive Dispatch Tests
File: test_abm_hardware_dispatch.py
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

from services.enterprise_abm_hardware_dispatch_engine import (
    EnterpriseABMHardwareDispatchEngine,
    HARDWARE_KIT_SPECS,
    BENCHMARK_METRICS,
    DISPATCH_LEDGER_PATH,
    REPORT_PATH,
)


@pytest.fixture
def test_engine(tmp_path):
    ledger_file = str(tmp_path / "test_abm_dispatches.json")
    report_file = str(tmp_path / "test_abm_report.md")
    return EnterpriseABMHardwareDispatchEngine(
        ledger_path=ledger_file,
        report_path=report_file
    )


def test_01_hardware_specs_and_unit_economics():
    """Verify hardware kit specifications, FIPS 140-3 HSM standard, and cost breakdown."""
    assert "FIPS 140-3 Level 3" in HARDWARE_KIT_SPECS["hsm_standard"]
    assert "devsupersuite_airgap_v1.0.0.wasm" in HARDWARE_KIT_SPECS["preloaded_runtime"]
    assert "DevSuperSuite Official" in HARDWARE_KIT_SPECS["laser_engraving"]
    assert HARDWARE_KIT_SPECS["unit_hardware_cost_usd"] == 85.0
    assert HARDWARE_KIT_SPECS["laser_engraving_cost_usd"] == 18.50
    assert HARDWARE_KIT_SPECS["priority_white_glove_courier_usd"] == 45.0
    assert HARDWARE_KIT_SPECS["total_unit_dispatch_cost_usd"] == 148.50


def test_02_register_and_dispatch_kit_generation(test_engine):
    """Verify dispatching kit creates structured record with unique ID, MIL seal, and tracking."""
    rec = test_engine.register_and_dispatch_kit(
        company_name="Raytheon Technologies",
        domain="rtx.com",
        recipient_title="Chief Information Security Officer",
        recipient_code="EXEC-RTX-99",
        shipping_city="Arlington, VA",
        target_deal_acv_usd=200000.0
    )

    assert rec["dispatch_id"].startswith("ABM-HW-")
    assert rec["company_name"] == "Raytheon Technologies"
    assert rec["recipient_title"] == "Chief Information Security Officer"
    assert rec["status"] == "DISPATCHED"
    assert rec["tamper_seal_serial"].startswith("SEAL-MIL-")
    assert rec["tracking_number"].startswith("FDX-PRI-")
    assert rec["target_deal_acv_usd"] == 200000.0
    assert rec["unit_cost_usd"] == 148.50


def test_03_record_delivery_event(test_engine):
    """Verify recording delivery transitions status to DELIVERED_SIGNED with timestamp."""
    rec = test_engine.register_and_dispatch_kit(
        company_name="Lockheed Martin",
        domain="lockheedmartin.com",
        recipient_title="VP Engineering",
        recipient_code="EXEC-LMT-01",
        shipping_city="Bethesda, MD"
    )
    d_id = rec["dispatch_id"]

    delivered = test_engine.record_delivery_event(d_id, signed_by="Security Enclave Desk")
    assert delivered["status"] == "DELIVERED_SIGNED"
    assert delivered["delivered_at"] is not None
    assert delivered["signed_by"] == "Security Enclave Desk"


def test_04_record_dongle_activation(test_engine):
    """Verify dongle activation records challenge hash and updates pipeline weighting to 60%."""
    rec = test_engine.register_and_dispatch_kit(
        company_name="Northrop Grumman",
        domain="northropgrumman.com",
        recipient_title="Head of Cyber Architecture",
        recipient_code="EXEC-NOC-02",
        shipping_city="Falls Church, VA",
        target_deal_acv_usd=100000.0
    )
    d_id = rec["dispatch_id"]
    test_engine.record_delivery_event(d_id)

    activated = test_engine.record_dongle_activation(d_id)
    assert activated["status"] == "DONGLE_PLUGGED_ACTIVATED"
    assert activated["activated_at"] is not None
    assert "activation_hash" in activated
    assert activated["opportunity_weighted_value_usd"] == 60000.0  # 60% of 100k


def test_05_book_discovery_meeting(test_engine):
    """Verify booking discovery meeting updates status to DISCOVERY_CALL_BOOKED with 80% weighting."""
    rec = test_engine.register_and_dispatch_kit(
        company_name="General Dynamics",
        domain="gd.com",
        recipient_title="VP Cyber Systems",
        recipient_code="EXEC-GD-03",
        shipping_city="Reston, VA",
        target_deal_acv_usd=250000.0
    )
    d_id = rec["dispatch_id"]
    test_engine.record_delivery_event(d_id)
    test_engine.record_dongle_activation(d_id)

    booked = test_engine.book_discovery_meeting(d_id, meeting_date="2026-11-28")
    assert booked["status"] == "DISCOVERY_CALL_BOOKED"
    assert booked["meeting_booked_at"] is not None
    assert booked["scheduled_meeting_date"] == "2026-11-28"
    assert booked["opportunity_weighted_value_usd"] == 200000.0  # 80% of 250k


def test_06_state_machine_invalid_dispatch_id(test_engine):
    """Verify KeyError is raised when referencing invalid dispatch ID."""
    with pytest.raises(KeyError, match="Dispatch ID 'ABM-UNKNOWN' not found"):
        test_engine.record_delivery_event("ABM-UNKNOWN")

    with pytest.raises(KeyError, match="Dispatch ID 'ABM-UNKNOWN' not found"):
        test_engine.record_dongle_activation("ABM-UNKNOWN")

    with pytest.raises(KeyError, match="Dispatch ID 'ABM-UNKNOWN' not found"):
        test_engine.book_discovery_meeting("ABM-UNKNOWN")


def test_07_audit_abm_campaign_metrics(test_engine):
    """Verify campaign conversion metrics, booking rates, and ROI multiples."""
    # 10 accounts: 10 dispatched, 8 delivered, 6 activated, 4 booked meetings
    for i in range(10):
        rec = test_engine.register_and_dispatch_kit(
            company_name=f"Enterprise {i}",
            domain=f"corp{i}.com",
            recipient_title="CISO",
            recipient_code=f"EXEC-{i}",
            shipping_city="New York, NY",
            target_deal_acv_usd=100000.0
        )
        d_id = rec["dispatch_id"]
        if i < 8:
            test_engine.record_delivery_event(d_id)
        if i < 6:
            test_engine.record_dongle_activation(d_id)
        if i < 4:
            test_engine.book_discovery_meeting(d_id)

    audit = test_engine.audit_abm_campaign()
    assert audit["total_kits_dispatched"] == 10
    assert audit["kits_delivered"] == 8
    assert audit["dongles_activated"] == 6
    assert audit["discovery_calls_booked"] == 4
    assert audit["delivery_rate_pct"] == 80.0
    # Booking rate = 4 / 8 = 50.0%
    assert audit["meeting_booking_rate_pct"] == 50.0
    assert audit["conversion_lift_multiple"] > 20.0
    assert audit["total_campaign_spend_usd"] == 1485.0
    assert audit["weighted_pipeline_generated_usd"] > 0
    assert audit["campaign_pipeline_roi_multiple"] > 100.0


def test_08_ledger_persistence_and_reloading(tmp_path):
    """Verify ledger persistence to disk and state re-instantiation."""
    ledger_file = str(tmp_path / "persist_ledger.json")
    eng1 = EnterpriseABMHardwareDispatchEngine(ledger_path=ledger_file)

    rec = eng1.register_and_dispatch_kit(
        company_name="Palantir",
        domain="palantir.com",
        recipient_title="Head of Infosec",
        recipient_code="EXEC-PLTR",
        shipping_city="Denver, CO"
    )
    assert os.path.exists(ledger_file)

    eng2 = EnterpriseABMHardwareDispatchEngine(ledger_path=ledger_file)
    assert len(eng2.ledger["dispatches"]) == 1
    assert eng2.ledger["dispatches"][0]["dispatch_id"] == rec["dispatch_id"]


def test_09_markdown_report_generation(test_engine):
    """Verify executive markdown report generation with all required tables and brand headers."""
    rec = test_engine.register_and_dispatch_kit(
        company_name="Datadog",
        domain="datadoghq.com",
        recipient_title="VP Infrastructure",
        recipient_code="EXEC-DDOG",
        shipping_city="Boston, MA"
    )
    test_engine.record_delivery_event(rec["dispatch_id"])
    test_engine.book_discovery_meeting(rec["dispatch_id"])

    report_path = test_engine.render_markdown_report()
    assert os.path.exists(report_path)

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "# ⚡ DevSuperSuite Official: Enterprise ABM Hardware Token & Executive Dispatch Report" in content
    assert "Meeting Booking Rate" in content
    assert "Datadog" in content
    assert "growth@devsupersuite.com" in content


def test_10_cli_interface_execution():
    """Verify all CLI subcommands execute with exit code 0."""
    python_bin = sys.executable
    script_path = os.path.join(SERVICES_DIR, "enterprise_abm_hardware_dispatch_engine.py")

    commands = [
        ["--summary"],
        ["--dispatch-kit", "--company", "Snowflake", "--domain", "snowflake.com", "--title", "VP Security", "--code", "EXEC-SNOW-99", "--city", "San Mateo, CA", "--acv", "150000.0"],
        ["--record-delivery"],
        ["--record-activation"],
        ["--book-meeting", "--meeting-date", "2026-12-01"],
        ["--audit-abm"],
        ["--export-abm-report"]
    ]

    for args in commands:
        cmd = [python_bin, script_path] + args
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        assert res.returncode == 0, f"CLI command {cmd} failed with stderr: {res.stderr}"


def test_11_strict_brand_anonymity_compliance():
    """Verify zero personal founder leaks across all Phase 31 assets."""
    forbidden_tokens = [
        bytes.fromhex("41746861727661").decode("utf-8"),
        bytes.fromhex("506164687965").decode("utf-8"),
        bytes.fromhex("39383930343431323933").decode("utf-8"),
    ]

    phase_31_files = [
        Path(SERVICES_DIR) / "enterprise_abm_hardware_dispatch_engine.py",
        Path(DATA_DIR) / "enterprise_abm_hardware_dispatches.json",
        Path(REPORTS_DIR) / "abm_hardware_dispatch_report.md",
        Path(TESTS_DIR) / "test_abm_hardware_dispatch.py",
    ]

    for file_path in phase_31_files:
        assert file_path.exists(), f"File {file_path} must exist"
        content = file_path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token.lower() not in content.lower(), (
                f"Brand anonymity violation: found forbidden token in {file_path}"
            )
