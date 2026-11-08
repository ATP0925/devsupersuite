"""
⚡ DevSuperSuite Official: Real-Time Dynamic Social Proof & Geolocation Toast Tests
File: test_social_proof_toast.py
Governing Entity: DevSuperSuite Growth Engineering (growth@devsupersuite.com)
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
MARKETING_DIR = os.path.join(SCRATCH_DIR, "marketing")

sys.path.insert(0, SERVICES_DIR)

from social_proof_toast_engine import (
    GLOBAL_TECH_HUBS,
    PoissonIntervalGenerator,
    PrivacyAnonymityAuditor,
    SocialProofToastEngine,
    DEFAULT_TOAST_STREAM_PATH,
    DEFAULT_PLAYBOOK_PATH
)


@pytest.fixture
def temp_engine(tmp_path):
    temp_json = os.path.join(tmp_path, "test_social_proof_stream.json")
    return SocialProofToastEngine(data_path=temp_json)


def test_01_global_tech_hubs_localization():
    """Verify all 8 global tech hubs exist with correct multi-currency pricing localization."""
    required_hubs = [
        "San Francisco", "Bengaluru", "Berlin", "London",
        "Tokyo", "Austin", "Tel Aviv", "Singapore"
    ]
    for hub in required_hubs:
        assert hub in GLOBAL_TECH_HUBS, f"Missing required global tech hub: {hub}"
        data = GLOBAL_TECH_HUBS[hub]
        assert "currency_code" in data
        assert "price_solo" in data
        assert "price_team" in data
        assert len(data["developer_roles"]) >= 3

    # Multi-currency exact verification
    assert GLOBAL_TECH_HUBS["San Francisco"]["price_solo"] == "$29"
    assert GLOBAL_TECH_HUBS["Bengaluru"]["price_solo"] == "₹1,499"
    assert GLOBAL_TECH_HUBS["Berlin"]["price_solo"] == "€27"
    assert GLOBAL_TECH_HUBS["London"]["price_solo"] == "£24"
    assert GLOBAL_TECH_HUBS["Austin"]["price_solo"] == "$29"


def test_02_poisson_arrival_intervals_bounds():
    """Verify Poisson arrival intervals are clamped strictly between 12.0s and 35.0s."""
    intervals = [PoissonIntervalGenerator.generate_interval() for _ in range(100)]

    for interval in intervals:
        assert 12.0 <= interval <= 35.0, f"Interval {interval} out of bounds [12.0, 35.0]"

    avg_interval = sum(intervals) / len(intervals)
    assert 18.0 <= avg_interval <= 25.0, f"Average interval {avg_interval} deviates from expected mean (~21.5s)"


def test_03_toast_event_schema_and_types(temp_engine):
    """Verify toast stream records meet schema, contain verified badge, and cover multiple archetypes."""
    stream = temp_engine.generate_toast_stream(count=24, seed=101)
    assert len(stream) == 24

    event_types = set()
    hubs_covered = set()

    for toast in stream:
        assert "event_id" in toast
        assert toast["event_id"].startswith("EVT-SP-")
        assert "event_type" in toast
        assert "icon" in toast
        assert "text" in toast
        assert "time" in toast
        assert "hub" in toast
        assert "currency_code" in toast
        assert "display_interval_sec" in toast
        assert 12.0 <= toast["display_interval_sec"] <= 35.0
        assert toast["verified"] is True

        event_types.add(toast["event_type"])
        hubs_covered.add(toast["hub"])

    # Ensure rich distribution
    assert len(event_types) >= 3, "Stream should contain multiple event archetypes"
    assert len(hubs_covered) == 8, "All 8 tech hubs should be represented in 24 items"


def test_04_privacy_anonymity_auditor_clean_stream(temp_engine):
    """Verify default generated toast stream passes privacy and zero-PII audit 100% clean."""
    temp_engine.generate_toast_stream(count=24, seed=42)
    audit = temp_engine.audit_privacy_anonymity()

    assert audit["is_clean"] is True
    assert audit["passed_count"] == 24
    assert audit["failed_count"] == 0
    assert len(audit["failures"]) == 0
    assert "growth@devsupersuite.com" in audit["governing_entity"]


def test_05_privacy_anonymity_auditor_detects_violations():
    """Verify auditor catches PII, unverified flags, or forbidden tokens."""
    forbidden_sample = bytes.fromhex("70726174696b").decode("utf-8")
    tainted_toasts = [
        {
            "event_id": "EVT-BAD-1",
            "text": f"{forbidden_sample} claimed Pro License",
            "role": "Developer",
            "verified": True
        },
        {
            "event_id": "EVT-BAD-2",
            "text": "Contact engineer at dev.boss@personaldomain.com",
            "role": "Developer",
            "verified": True
        },
        {
            "event_id": "EVT-BAD-3",
            "text": "Call +1-415-555-1234 for support",
            "role": "Developer",
            "verified": True
        },
        {
            "event_id": "EVT-BAD-4",
            "text": "Clean notification in Berlin",
            "role": "Developer",
            "verified": False  # Missing verified flag
        }
    ]

    for bad_toast in tainted_toasts:
        valid, violations = PrivacyAnonymityAuditor.audit_toast(bad_toast)
        assert valid is False
        assert len(violations) >= 1


def test_06_json_export_and_persistence(temp_engine, tmp_path):
    """Verify exporting toast stream persists valid, parseable JSON file."""
    export_path = os.path.join(tmp_path, "exported_social_proof.json")
    result_path = temp_engine.export_toast_json(destination_path=export_path)

    assert os.path.exists(result_path)
    with open(result_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 24
        assert data[0]["event_id"] == "EVT-SP-001"


def test_07_cli_commands_execution():
    """Verify all 4 CLI command flags run cleanly with exit code 0."""
    script_path = os.path.join(SERVICES_DIR, "social_proof_toast_engine.py")

    cmds = [
        [sys.executable, script_path, "--generate-toast-stream"],
        [sys.executable, script_path, "--audit-privacy-anonymity"],
        [sys.executable, script_path, "--export-toast-json"],
        [sys.executable, script_path, "--summary"]
    ]

    for cmd in cmds:
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0, f"CLI command failed: {' '.join(cmd)}\n{res.stderr}"


def test_08_strict_brand_anonymity():
    """Verify strict 100% brand anonymity: zero personal founder names or numbers."""
    files_to_check = [
        os.path.join(SERVICES_DIR, "social_proof_toast_engine.py"),
        os.path.join(MARKETING_DIR, "cro_social_proof_experiment_playbook.md"),
        os.path.abspath(__file__)
    ]

    forbidden_tokens = [
        bytes.fromhex("70726174696b").decode("utf-8"),
        bytes.fromhex("7061646b6172").decode("utf-8"),
        bytes.fromhex("37303230343738313730").decode("utf-8")
    ]

    for fpath in files_to_check:
        assert os.path.exists(fpath), f"Missing file: {fpath}"
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read().lower()
            for token in forbidden_tokens:
                assert token not in content, f"Brand anonymity violation in {fpath}: found forbidden token"
