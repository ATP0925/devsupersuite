#!/usr/bin/env python3
"""
Test Suite for Sovereign SCIF HSM PKCS#11 Level 4 Physical Tamper Enclave & Custody Controller.
Part of DevSuperSuite Infrastructure Solutions & OmniKernel Labs.

Validates:
- Cryptoki PKCS#11 v3.0 Token Store & non-extractable key enforcement (CKA_EXTRACTABLE=CK_FALSE).
- Active multi-sensor tamper envelope & sub-50ns atomic zeroization (HSMTamperZeroizedError).
- M-of-N Shamir's Secret Sharing threshold cryptography over prime field GF(2^256 - 189).
- Continuous Known Answer Tests (KAT) & Power-On Self-Tests (POST) for FIPS 140-3 Level 4.
- Hardware signing within the silicon boundary.
- Immutable custody audit ledger with SHA3-512 hash-chain integrity.
- Multi-action CLI operations.
- 100% Brand Anonymity Protocol.
"""

import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path
import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519

from services.enterprise_pkcs11_hsm_custody_controller import (
    ORGANIZATION_NAME,
    PRIMARY_CONTACT,
    HSM_CONTACT,
    SHAMIR_FIELD_PRIME,
    ShamirThresholdSecretSharing,
    FipsContinuousSelfTestEngine,
    ActiveTamperEnvelope,
    PKCS11TokenStore,
    HSMCustodyAuditLedger,
    EnterprisePKCS11HSMController,
    HSMError,
    HSMTamperZeroizedError,
    PKCS11ExtractableViolationError,
    FipsSelfTestFailureError,
    InsufficientQuorumError
)


def test_hsm_initialization_and_specs():
    """Verify default initialization parameters of the PKCS#11 Token Store."""
    token = PKCS11TokenStore(serial_number="TEST-HSM-L4-001")
    assert token.serial_number == "TEST-HSM-L4-001"
    assert token.state == PKCS11TokenStore.STATE_INITIALIZING
    assert token._mkek is None


def test_fips_continuous_kats_all_pass():
    """Verify that all FIPS 140-3 Power-On Self-Tests (POST) pass with official NIST vectors."""
    engine = FipsContinuousSelfTestEngine()
    res = engine.execute_all_kats()
    assert res["overall_status"] == "ALL_KATS_PASSED"
    assert res["algorithms_verified"]["AES-256-GCM"]["status"] == "PASS"
    assert res["algorithms_verified"]["SHA3-512"]["status"] == "PASS"
    assert res["algorithms_verified"]["Ed25519"]["status"] == "PASS"
    assert res["algorithms_verified"]["ML-KEM-1024"]["status"] == "PASS"


def test_fips_kat_failure_halts_with_exception():
    """Verify that a corrupted Known Answer Test vector raises FipsSelfTestFailureError."""
    engine = FipsContinuousSelfTestEngine()
    # Intentionally corrupt expected tag
    engine.AES_KAT_EXPECTED_TAG = "00000000000000000000000000000000"
    with pytest.raises(FipsSelfTestFailureError) as exc_info:
        engine.execute_all_kats()
    assert "FIPS 140-3 POST Failure" in str(exc_info.value)


def test_shamir_secret_sharing_reconstruction_3_of_5():
    """Verify 3-of-5 Shamir Secret Sharing reconstruction over GF(2^256 - 189)."""
    shamir = ShamirThresholdSecretSharing()
    master_secret = secrets.token_bytes(32)

    shares = shamir.split_secret(master_secret, threshold_m=3, total_n=5)
    assert len(shares) == 5

    # Reconstruct with first 3 shares
    reconstructed = shamir.reconstruct_secret(shares[:3], threshold_m=3)
    assert reconstructed == master_secret


def test_shamir_insufficient_quorum_failure():
    """Verify that fewer shares than threshold M raises InsufficientQuorumError."""
    shamir = ShamirThresholdSecretSharing()
    master_secret = secrets.token_bytes(32)

    shares = shamir.split_secret(master_secret, threshold_m=3, total_n=5)
    with pytest.raises(InsufficientQuorumError) as exc_info:
        shamir.reconstruct_secret(shares[:2], threshold_m=3)
    assert "Quorum check failed" in str(exc_info.value)


def test_shamir_different_subsets_reconstruct_identical_secret():
    """Verify that any combination of 3 shares out of 5 reconstructs the identical secret."""
    shamir = ShamirThresholdSecretSharing()
    secret = secrets.token_bytes(32)
    shares = shamir.split_secret(secret, threshold_m=3, total_n=5)

    subsets = [
        [shares[0], shares[1], shares[2]],
        [shares[0], shares[2], shares[4]],
        [shares[1], shares[3], shares[4]],
        [shares[2], shares[3], shares[4]]
    ]
    for sub in subsets:
        rec = shamir.reconstruct_secret(sub, threshold_m=3)
        assert rec == secret


def test_active_tamper_envelope_sensor_thresholds():
    """Verify physical tamper envelope detection across thermal, voltage, and chassis sensors."""
    envelope = ActiveTamperEnvelope()
    
    # Baseline: nominal conditions
    base_eval = envelope.evaluate_sensors()
    assert base_eval["is_tampered"] is False
    assert len(base_eval["violations"]) == 0

    # 1. Cryogenic freezing attack (-45C)
    envelope.temperature_c = -45.0
    cryo_eval = envelope.evaluate_sensors()
    assert cryo_eval["is_tampered"] is True
    assert any("Cryogenic freezing" in v for v in cryo_eval["violations"])

    # 2. Thermal heat probe attack (+90C)
    envelope.temperature_c = 90.0
    heat_eval = envelope.evaluate_sensors()
    assert heat_eval["is_tampered"] is True
    assert any("Thermal heat probe" in v for v in heat_eval["violations"])
    envelope.temperature_c = 25.0

    # 3. Voltage fault injection (4.0V)
    envelope.voltage_v = 4.00
    volt_eval = envelope.evaluate_sensors()
    assert volt_eval["is_tampered"] is True
    assert any("Overvoltage fault injection" in v for v in volt_eval["violations"])
    envelope.voltage_v = 3.30

    # 4. Chassis micro-switch lid opening
    envelope.lid_switch_closed = False
    lid_eval = envelope.evaluate_sensors()
    assert lid_eval["is_tampered"] is True
    assert any("Chassis enclosure micro-switch opened" in v for v in lid_eval["violations"])

    # 5. Serpentine drill detection wire mesh
    envelope.chassis_mesh_intact = False
    mesh_eval = envelope.evaluate_sensors()
    assert mesh_eval["is_tampered"] is True
    assert any("wire mesh optical barrier breached" in v for v in mesh_eval["violations"])


def test_atomic_zeroization_within_50ns_sla():
    """Verify that atomic zeroization executes in <50ns and wipes MKEK and private key buffers."""
    token = PKCS11TokenStore()
    token.initialize_mkek(secrets.token_bytes(32))
    key_meta = token.generate_ed25519_keypair(label="CEREMONY_KEY_01")

    assert token.state == PKCS11TokenStore.STATE_OPERATIONAL
    assert token._mkek is not None

    zero_res = token.execute_atomic_zeroization(trigger_cause="ACTIVE_TAMPER_CHASSIS_BREACH")

    assert zero_res["status"] == "ATOMIC_ZEROIZATION_COMPLETE"
    assert zero_res["state"] == PKCS11TokenStore.STATE_TAMPER_ZEROIZED
    assert zero_res["zeroization_time_nanoseconds"] < 50.0
    assert zero_res["within_50ns_sla"] is True
    assert token._mkek is None
    assert token._objects[key_meta["key_id"]]["private_bytes"] is None
    assert token._objects[key_meta["key_id"]]["zeroized"] is True


def test_crypto_operations_blocked_after_zeroization():
    """Verify that zeroized token rejects all subsequent cryptographic operations."""
    token = PKCS11TokenStore()
    token.initialize_mkek(secrets.token_bytes(32))
    key_meta = token.generate_ed25519_keypair(label="CEREMONY_KEY_02")
    token.execute_atomic_zeroization(trigger_cause="SIMULATED_TEST_TAMPER")

    # 1. Sign attempt
    with pytest.raises(HSMTamperZeroizedError) as exc_info:
        token.sign_with_key(key_meta["key_id"], b"SAMPLE_TRANSACTION")
    assert "zeroized" in str(exc_info.value).lower() or "device_removed" in str(exc_info.value).lower()

    # 2. Key generation attempt
    with pytest.raises(HSMTamperZeroizedError):
        token.generate_ed25519_keypair(label="NEW_KEY_AFTER_TAMPER")

    # 3. MKEK load attempt
    with pytest.raises(HSMTamperZeroizedError):
        token.initialize_mkek(secrets.token_bytes(32))


def test_pkcs11_cka_extractable_false_enforcement():
    """Verify that CKA_EXTRACTABLE=CK_FALSE prevents plaintext private key extraction."""
    token = PKCS11TokenStore()
    token.initialize_mkek(secrets.token_bytes(32))
    key_meta = token.generate_ed25519_keypair(label="DEFENSE_TOP_SECRET_SIGNER")

    assert key_meta["CKA_EXTRACTABLE"] is False
    assert key_meta["CKA_SENSITIVE"] is True

    with pytest.raises(PKCS11ExtractableViolationError) as exc_info:
        token.export_private_key_attempt(key_meta["key_id"])
    assert "CKR_ACTION_PROHIBITED" in str(exc_info.value)
    assert "CKA_EXTRACTABLE=CK_FALSE" in str(exc_info.value)


def test_hardware_signing_and_verification():
    """Verify hardware enclave signature generation and external public key verification."""
    token = PKCS11TokenStore()
    token.initialize_mkek(secrets.token_bytes(32))
    key_meta = token.generate_ed25519_keypair(label="FEDRAMP_AUDIT_SIGNER")

    test_payload = b"NIST_SP_800_53_SCIF_COMMAND_LOG_VERIFICATION"
    signature = token.sign_with_key(key_meta["key_id"], test_payload)
    assert len(signature) == 64

    # Verify signature externally using the public key hex
    pub_key_bytes = bytes.fromhex(key_meta["public_key_hex"])
    pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_key_bytes)
    pub_key.verify(signature, test_payload)  # Raises if invalid


def test_immutable_audit_ledger_hash_chain(tmp_path):
    """Verify that the custody audit ledger maintains an unbroken SHA3-512 hash chain."""
    ledger_file = tmp_path / "test_hsm_ledger.json"
    ledger = HSMCustodyAuditLedger(ledger_file)

    entry1 = ledger.log_event("TEST_EVENT_1", "SECURITY_OFFICER", "STATE_OPERATIONAL", {"test": 1})
    entry2 = ledger.log_event("TEST_EVENT_2", "CUSTODIAN_1", "STATE_OPERATIONAL", {"test": 2})
    entry3 = ledger.log_event("TEST_EVENT_3", "ACTIVE_TAMPER_CIRCUIT", "STATE_TAMPER_ZEROIZED", {"test": 3})

    ledger_data = ledger.read_ledger()
    events = ledger_data["events"]
    assert len(events) == 3

    # Check hash links
    assert events[0]["previous_hash"] == ledger_data["genesis_hash"]
    assert events[1]["previous_hash"] == events[0]["entry_hash"]
    assert events[2]["previous_hash"] == events[1]["entry_hash"]

    # Verify SHA3-512 integrity of entry 2
    record_content = {
        "entry_id": events[1]["entry_id"],
        "timestamp": events[1]["timestamp"],
        "event_type": events[1]["event_type"],
        "operator_role": events[1]["operator_role"],
        "hsm_state": events[1]["hsm_state"],
        "previous_hash": events[1]["previous_hash"],
        "details": events[1]["details"]
    }
    recomputed_hash = hashlib.sha3_512(json.dumps(record_content, sort_keys=True).encode("utf-8")).hexdigest()
    assert recomputed_hash == events[1]["entry_hash"]


def test_cli_execution_modes():
    """Verify that all CLI subcommands run successfully without errors."""
    cli_script = Path(__file__).resolve().parent.parent / "services" / "enterprise_pkcs11_hsm_custody_controller.py"

    flags = [
        ["--summary"],
        ["--execute-power-on-kat"],
        ["--split-shamir-keys"],
        ["--simulate-tamper-zeroization"],
        ["--generate-hsm-manifest"]
    ]
    for flag_group in flags:
        res = subprocess.run(
            [sys.executable, str(cli_script)] + flag_group,
            capture_output=True,
            text=True
        )
        assert res.returncode == 0, f"CLI command {flag_group} failed: {res.stderr}"


def test_brand_anonymity_hsm_custody():
    """Enforce strict 100% Brand Anonymity: zero personal names, private numbers, or unofficial domains."""
    repo_root = Path(__file__).resolve().parent.parent
    files_to_check = [
        repo_root / "services" / "enterprise_pkcs11_hsm_custody_controller.py",
        repo_root / "deployment" / "hardware" / "hsm_custody_manifest.json",
        repo_root / "services" / "reports" / "hsm_pkcs11_custody_report.md"
    ]

    forbidden_tokens = [
        "".join(["at", "pad"]),
        "".join(["kar", "tik"]),
        "".join(["Kar", "tik"]),
        "".join(["Pad", "manabhan"])
    ]

    for file_path in files_to_check:
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            # Verify unauthorized emails
            emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", content)
            for email in emails:
                assert email.endswith("@devsupersuite.com"), f"Unauthorized email found in {file_path}: {email}"
            
            # Verify forbidden founder tokens
            for token in forbidden_tokens:
                assert token not in content, f"Personal identity leak '{token}' detected in {file_path}"
