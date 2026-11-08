#!/usr/bin/env python3
"""
Test Suite for Sovereign SCIF Optical Diode Ingestion Gateway & Unidirectional Sanitization Engine.
Part of DevSuperSuite Infrastructure Solutions & OmniKernel Labs.

Validates:
- Physical simplex optical diode isolation and zero reverse egress (DiodeEgressViolationError).
- Cauchy Systematic Reed-Solomon Forward Error Correction (FEC) over GF(2^8) with packet loss recovery.
- Content Disarm and Reconstruction (CDR) Engine (Tar Slip, embedded PE/ELF/Mach-O magic, AST normalization).
- Cryptographic verification via BLAKE3 Merkle tree and SHA3-512 with SLSA Level 3 Provenance.
- SCIF Quarantine Staging Ledger persistence.
- Multi-action CLI operations.
- 100% Brand Anonymity Protocol.
"""

import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
import pytest

# Ensure repo root is on sys.path
PROJECT_DIR = str(Path(__file__).resolve().parent.parent)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from services.enterprise_optical_diode_gateway import (
    ORGANIZATION_NAME,
    PRIMARY_CONTACT,
    SCIF_CONTACT,
    GF256,
    ReedSolomonFEC,
    Blake3Sha3DigestEngine,
    SimplexOpticalDiodeTransceiver,
    ContentDisarmReconstructionEngine,
    SCIFQuarantineLedger,
    EnterpriseOpticalDiodeGateway,
    DiodeEgressViolationError,
    CDRSanitizationError,
    DigestIntegrityError
)


def test_physical_transceiver_initialization_and_specs():
    """Verify hardware parameters of the simplex optical diode transceiver."""
    transceiver = SimplexOpticalDiodeTransceiver(
        serial_number="TEST-DIODE-10G-001",
        wavelength_nm=1310,
        tx_power_dbm=2.0,
        rx_sensitivity_dbm=-18.0
    )
    assert transceiver.serial_number == "TEST-DIODE-10G-001"
    assert transceiver.wavelength_nm == 1310
    assert transceiver.tx_power_dbm == 2.0
    assert transceiver.rx_sensitivity_dbm == -18.0
    assert transceiver.return_fiber_cores == 0
    assert transceiver.reverse_optical_channel_active is False


def test_simplex_reverse_egress_violation_error():
    """Verify that attempting reverse transmission from the RX node raises DiodeEgressViolationError."""
    transceiver = SimplexOpticalDiodeTransceiver()
    with pytest.raises(DiodeEgressViolationError) as exc_info:
        transceiver.attempt_reverse_egress(destination_ip="192.168.10.5", data=b"UNAUTHORIZED_ACK")
    
    assert "Physical Layer Egress Violation" in str(exc_info.value)
    assert transceiver.egress_violations_blocked == 1


def test_gf256_math_primitives():
    """Verify GF(2^8) Galois field arithmetic properties."""
    gf = GF256()
    # Identity and multiplicative inverse
    for val in [1, 2, 7, 19, 45, 128, 254]:
        inv_val = gf.inv(val)
        assert gf.mul(val, inv_val) == 1
    
    # Multiplication by zero
    assert gf.mul(0, 15) == 0
    assert gf.mul(15, 0) == 0

    with pytest.raises(ZeroDivisionError):
        gf.inv(0)


def test_reed_solomon_fec_packet_loss_recovery():
    """Verify systematic Reed-Solomon FEC recovers original payload with 20% dropped packets."""
    fec = ReedSolomonFEC()
    # 2048-byte sample test data
    test_data = (b"DevSuperSuite_SCIF_Airgap_Payload_" * 64)[:2048]
    chunk_size = 256
    
    # Encode with 25% parity ratio
    chunks, k, m, original_length = fec.encode(test_data, chunk_size=chunk_size, parity_ratio=0.25)
    assert original_length == len(test_data)
    assert k == 8
    assert m == 2
    assert len(chunks) == k + m

    # Simulate packet loss: drop 2 primary data chunks (chunk 0 and chunk 3)
    surviving_chunks = [c for c in chunks if c["chunk_index"] not in (0, 3)]
    assert len(surviving_chunks) >= k  # Still have 8 surviving chunks

    # Decode and verify bit-for-bit reconstruction
    recovered = fec.decode(surviving_chunks, k=k, m=m, original_length=original_length, chunk_size=chunk_size)
    assert recovered == test_data


def test_cdr_tar_slip_and_path_traversal_prevention():
    """Verify CDR prevents Tar Slip / path traversal directory jumping."""
    cdr = ContentDisarmReconstructionEngine()
    
    malicious_paths = [
        "../../etc/shadow",
        "....//....//windows/system32/cmd.exe",
        "/usr/local/bin/malicious_node",
        "C:\\Users\\Administrator\\ntuser.dat"
    ]
    for path in malicious_paths:
        res = cdr.sanitize_payload(path, b"print('Hello Secure SCIF')\n")
        assert "DIRECTORY_TRAVERSAL_DETECTED" in " ".join(res["threats_detected"])
        assert ".." not in res["filename"]
        assert "/" not in res["filename"]
        assert "\\" not in res["filename"]
        assert res["status"] == "SANITIZED"


def test_cdr_embedded_magic_header_stripping():
    """Verify CDR neutralizes embedded executable headers (MZ, ELF, Mach-O)."""
    cdr = ContentDisarmReconstructionEngine()
    # Polyglot text file with embedded DOS PE header and ELF header
    dirty_script = (
        b"# Normal header\n"
        b"MZ\x90\x00\x03\x00Some DOS binary blob\n"
        b"\x7fELF\x02\x01\x01\x00Linux payload\n"
        b"def execute_task():\n    return 42\n"
    )
    res = cdr.sanitize_payload("worker.py", dirty_script)
    sanitized_bytes = res["sanitized_content"]

    # Verify magic bytes were neutralized
    assert b"MZ" not in sanitized_bytes
    assert b"\x7fELF" not in sanitized_bytes
    assert any("EMBEDDED_EXECUTABLE_HEADER_FOUND" in t for t in res["threats_detected"])
    assert res["status"] == "SANITIZED"


def test_cdr_json_normalization():
    """Verify CDR normalizes JSON and strips control characters."""
    cdr = ContentDisarmReconstructionEngine()
    dirty_json = b'{\x00\x01"app": "devsupersuite", "scif_id": 109, "active": true}\x07'
    res = cdr.sanitize_payload("config.json", dirty_json)
    
    parsed = json.loads(res["sanitized_content"].decode("utf-8"))
    assert parsed["app"] == "devsupersuite"
    assert parsed["scif_id"] == 109
    assert parsed["active"] is True
    assert "CONTROL_CHARS_IN_JSON" in res["threats_detected"]


def test_cdr_yaml_unsafe_tag_stripping():
    """Verify CDR strips unsafe YAML deserialization tags like !python/object."""
    cdr = ContentDisarmReconstructionEngine()
    dangerous_yaml = b"""
enclave: SCIF-01
exploit: !python/object/apply:os.system ["touch /tmp/pwned"]
settings:
  timeout: 30
"""
    res = cdr.sanitize_payload("policy.yaml", dangerous_yaml)
    sanitized_text = res["sanitized_content"].decode("utf-8")
    assert "!python/object" not in sanitized_text
    assert "!sanitized_tag" in sanitized_text
    assert "UNSAFE_YAML_DESERIALIZATION_TAG_DETECTED" in res["threats_detected"]


def test_cdr_python_ast_validation_and_null_byte_disarm():
    """Verify CDR handles Python source cleansing, null-byte injection, and syntax check."""
    cdr = ContentDisarmReconstructionEngine()
    code_with_null = b"def calculate():\x00\n    return 100 * 2\n"
    res = cdr.sanitize_payload("calc.py", code_with_null)
    
    assert b"\x00" not in res["sanitized_content"]
    assert "NULL_BYTE_OR_CONTROL_CHAR_INJECTION_IN_PYTHON" in res["threats_detected"]
    assert "AST_SYNTAX_PARSED_AND_VALIDATED" in res["actions_taken"]


def test_cdr_zip_archive_disarming():
    """Verify CDR inspects and reconstructs clean ZIP archives disarming nested threats."""
    cdr = ContentDisarmReconstructionEngine()
    
    # Create in-memory zip with malicious traversal entry and normal entry
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("../../etc/passwd", b"root:x:0:0:root:/root:/bin/bash\n")
        z.writestr("safe_module.py", b"def run():\n    return 'safe'\n")
    
    zip_bytes = zip_buf.getvalue()
    res = cdr.sanitize_payload("bundle.zip", zip_bytes)
    
    # Inspect reconstructed zip
    out_buf = io.BytesIO(res["sanitized_content"])
    with zipfile.ZipFile(out_buf, "r") as z_out:
        namelist = z_out.namelist()
        assert not any(".." in name for name in namelist)
        assert "passwd" in namelist or any("sanitized" in name for name in namelist)
        assert "safe_module.py" in namelist


def test_cdr_tar_archive_disarming():
    """Verify CDR sanitizes TAR archives and strips unauthorized symlinks."""
    cdr = ContentDisarmReconstructionEngine()

    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w:gz") as t:
        # Add normal file
        data = b"def task(): pass\n"
        info = tarfile.TarInfo(name="app.py")
        info.size = len(data)
        t.addfile(info, io.BytesIO(data))

        # Add symlink
        symlink_info = tarfile.TarInfo(name="link_to_shadow")
        symlink_info.type = tarfile.SYMTYPE
        symlink_info.linkname = "/etc/shadow"
        t.addfile(symlink_info)

    tar_bytes = tar_buf.getvalue()
    res = cdr.sanitize_payload("codebase.tar.gz", tar_bytes)

    # Inspect sanitized tar
    out_buf = io.BytesIO(res["sanitized_content"])
    with tarfile.open(fileobj=out_buf, mode="r:gz") as t_out:
        names = t_out.getnames()
        assert "app.py" in names
        assert "link_to_shadow" not in names  # Symlink stripped
    assert any("STRIPPED_SYMLINK_MEMBER" in a for a in res["actions_taken"])


def test_blake3_and_sha3_512_merkle_digests():
    """Verify cryptographic digest generation and Merkle tree hashing."""
    engine = Blake3Sha3DigestEngine()
    test_bytes = b"DevSuperSuite_SCIF_Cryptographic_Attestation_Block" * 50

    sha3 = engine.calculate_sha3_512(test_bytes)
    assert len(sha3) == 128  # 512 bits = 64 bytes = 128 hex chars
    assert sha3 == hashlib.sha3_512(test_bytes).hexdigest()

    blake3_root = engine.calculate_blake3_merkle_root(test_bytes, chunk_size=256)
    assert len(blake3_root) == 64  # 256-bit Merkle root = 64 hex chars
    
    # Determinism check
    assert blake3_root == engine.calculate_blake3_merkle_root(test_bytes, chunk_size=256)


def test_slsa_level3_provenance_generation():
    """Verify SLSA Level 3 In-Toto attestation format."""
    engine = Blake3Sha3DigestEngine()
    slsa = engine.generate_slsa_provenance(
        artifact_name="kernel_patch.rs",
        transfer_id="DIODE-TX-2026-TEST01",
        sha3_512="a" * 128,
        blake3_digest="b" * 64,
        diode_serial="DSS-DIODE-10G-OPT-8839",
        classification="TOP SECRET//SCI"
    )
    assert slsa["_type"] == "https://in-toto.io/Statement/v1"
    assert slsa["predicateType"] == "https://slsa.dev/provenance/v1"
    assert slsa["subject"][0]["name"] == "kernel_patch.rs"
    assert slsa["subject"][0]["digest"]["sha3_512"] == "a" * 128
    assert slsa["subject"][0]["digest"]["blake3"] == "b" * 64
    assert slsa["predicate"]["buildDefinition"]["externalParameters"]["security_classification"] == "TOP SECRET//SCI"


def test_end_to_end_gateway_pipeline(tmp_path):
    """Verify complete end-to-end diode ingestion pipeline and ledger persistence."""
    ledger_file = tmp_path / "test_ledger.json"
    manifest_file = tmp_path / "test_manifest.json"
    report_file = tmp_path / "test_report.md"

    gateway = EnterpriseOpticalDiodeGateway(
        ledger_path=ledger_file,
        manifest_path=manifest_file,
        report_path=report_file
    )

    sample_content = b"""
import math

def calculate_orbital_path(radius: float) -> float:
    return 2.0 * math.pi * radius
"""
    result = gateway.process_and_transfer_payload(
        filename="orbital_nav.py",
        content=sample_content,
        classification="TOP SECRET//SCI",
        simulated_loss_rate=0.0
    )

    assert result["status"] == "SUCCESS_VERIFIED"
    assert result["sanitized_payload"].decode("utf-8").strip() == sample_content.decode("utf-8").strip()
    assert result["record"]["cryptographic_verification"]["digests_match"] is True

    # Check ledger persistence
    ledger_data = gateway.ledger.read_ledger()
    assert len(ledger_data["transfers"]) == 1
    assert ledger_data["transfers"][0]["transfer_id"] == result["transfer_id"]
    assert ledger_data["transfers"][0]["sanitized_filename"] == "orbital_nav.py"


def test_audit_unidirectional_airgap(tmp_path):
    """Verify formal physical layer airgap audit output."""
    gateway = EnterpriseOpticalDiodeGateway(
        ledger_path=tmp_path / "ledger.json",
        manifest_path=tmp_path / "manifest.json",
        report_path=tmp_path / "report.md"
    )
    audit = gateway.audit_unidirectional_airgap()
    assert audit["audit_status"] == "COMPLIANT_ZERO_EGRESS_VERIFIED"
    assert audit["egress_penetration_test"]["blocked_by_hardware_law"] is True
    assert audit["physical_specifications"]["physical_egress_path_exists"] is False
    assert "NIST SP 800-53 Rev 5" in " ".join(audit["compliance_standards"])


def test_cli_execution_modes():
    """Verify all CLI subcommands run successfully via subprocess."""
    cli_script = Path(__file__).resolve().parent.parent / "services" / "enterprise_optical_diode_gateway.py"
    
    flags = [
        ["--summary"],
        ["--audit-unidirectional-airgap"],
        ["--sanitize-payload"],
        ["--simulate-diode-transfer"],
        ["--generate-diode-manifest"]
    ]
    for flag_group in flags:
        res = subprocess.run(
            [sys.executable, str(cli_script)] + flag_group,
            capture_output=True,
            text=True
        )
        assert res.returncode == 0, f"CLI command {flag_group} failed: {res.stderr}"


def test_brand_anonymity_optical_diode():
    """Enforce 100% Brand Anonymity Protocol: zero personal names, private phone numbers, or unofficial domains."""
    repo_root = Path(__file__).resolve().parent.parent
    files_to_check = [
        repo_root / "services" / "enterprise_optical_diode_gateway.py",
        repo_root / "deployment" / "hardware" / "optical_diode_manifest.json",
        repo_root / "services" / "reports" / "optical_diode_airgap_report.md"
    ]
    for file_path in files_to_check:
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            # Scan for unauthorized emails
            emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", content)
            for email in emails:
                assert email.endswith("@devsupersuite.com"), f"Unauthorized email found in {file_path}: {email}"
            
            # Scan for personal founder names
            forbidden_tokens = [
                "".join(["at", "pad"]),
                "".join(["kar", "tik"]),
                "".join(["Kar", "tik"]),
                "".join(["Pad", "manabhan"])
            ]
            for token in forbidden_tokens:
                assert token not in content, f"Personal identity leak '{token}' detected in {file_path}"
