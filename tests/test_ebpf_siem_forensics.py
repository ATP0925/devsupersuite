"""
DevSuperSuite Tech Services - Real-Time eBPF Forensics & SIEM Engine Test Suite
File: tests/test_ebpf_siem_forensics.py
Governing Authority: DevSuperSuite Official / Office of the CSCO
Contact: infosec@devsupersuite.com
Regulatory Baseline: NIST SP 800-86 / NIST SP 800-137 / RFC 5424 / ArcSight CEF
"""

import json
from pathlib import Path
import re
import subprocess
import sys
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from services.enterprise_ebpf_siem_forensics_engine import (
    EBPFForensicsEngine,
    EBPFForensicEvent,
    SyscallProbeType,
    EgressVerdict,
    SIEMFormat,
    EnterpriseSIEMExporter,
    run_threat_neutralization_simulation,
    write_siem_reports,
)


class TestEBPFSIEMForensics:
    """Rigorous verification suite for kernel eBPF probes, SIEM streaming, and kill-switch latency."""

    @pytest.fixture
    def engine(self):
        return EBPFForensicsEngine(
            node_id="dss-test-node-01",
            cluster_id="devsupersuite-test-cluster",
        )

    def test_01_socket_egress_whitelist_allow_and_block(self, engine):
        """Verifies whitelisted egress connections are permitted and unapproved connections are killed."""
        # Allowed internal connection
        evt_allowed = engine.intercept_connect(
            pid=1001,
            ppid=1,
            comm="ast-parser",
            uid=10001,
            gid=10001,
            dest_ip="10.244.0.15",
            dest_port=8080,
        )
        assert evt_allowed.verdict == EgressVerdict.ALLOW
        assert evt_allowed.probe_type == SyscallProbeType.SYS_ENTER_CONNECT
        assert evt_allowed.details["whitelisted"] is True
        assert evt_allowed.details["action_taken"] == "SOCKET_PERMITTED"

        # Blocked rogue external connection
        evt_blocked = engine.intercept_connect(
            pid=9999,
            ppid=1001,
            comm="rogue-exfil",
            uid=10001,
            gid=10001,
            dest_ip="203.0.113.55",
            dest_port=1337,
        )
        assert evt_blocked.verdict == EgressVerdict.BLOCK_SIGKILL
        assert evt_blocked.details["whitelisted"] is False
        assert evt_blocked.details["action_taken"] == "SIGKILL_TRANSMITTED"

    def test_02_killswitch_latency_ceiling_invariant(self, engine):
        """Guarantees the outbound egress kill-switch latency strictly conforms to < 10.0 microseconds."""
        for _ in range(25):
            evt = engine.intercept_connect(
                pid=4000,
                ppid=1,
                comm="test-runner",
                uid=10002,
                gid=10002,
                dest_ip="198.51.100.99",
                dest_port=8443,
            )
            assert evt.verdict == EgressVerdict.BLOCK_SIGKILL
            assert 0.0 < evt.killswitch_latency_us < 10.0, (
                f"Killswitch latency {evt.killswitch_latency_us}us exceeded 10.0us ceiling"
            )

    def test_03_execve_restricted_binary_interception(self, engine):
        """Verifies restricted shell and sniffer tools trigger instant SIGKILL."""
        # Safe execution
        evt_safe = engine.intercept_execve(
            pid=2001,
            ppid=1,
            comm="python",
            uid=10001,
            gid=10001,
            binary_path="/usr/bin/python3",
            argv=["python3", "services/app.py"],
        )
        assert evt_safe.verdict == EgressVerdict.ALLOW

        # Malicious netcat execution
        evt_nc = engine.intercept_execve(
            pid=2002,
            ppid=2001,
            comm="sh",
            uid=10001,
            gid=10001,
            binary_path="/usr/bin/nc",
            argv=["nc", "-lvnp", "4444"],
        )
        assert evt_nc.verdict == EgressVerdict.BLOCK_SIGKILL
        assert evt_nc.details["restricted_tool"] is True

    def test_04_lsm_file_open_credential_protection(self, engine):
        """Verifies unprivileged attempts to access sensitive files (/etc/shadow) trigger SIGKILL."""
        # Privileged root access allowed
        evt_root = engine.intercept_file_open(
            pid=100,
            ppid=1,
            comm="systemd",
            uid=0,
            gid=0,
            file_path="/etc/shadow",
        )
        assert evt_root.verdict == EgressVerdict.ALLOW

        # Unprivileged non-root access blocked
        evt_unprivileged = engine.intercept_file_open(
            pid=3005,
            ppid=1001,
            comm="ast-parser",
            uid=10001,
            gid=10001,
            file_path="/etc/shadow",
        )
        assert evt_unprivileged.verdict == EgressVerdict.BLOCK_SIGKILL
        assert evt_unprivileged.details["sensitive_target"] is True

    def test_05_cef_serialization_format_compliance(self, engine):
        """Validates Common Event Format (CEF) header and extension attributes."""
        evt = engine.intercept_connect(
            pid=5555,
            ppid=1,
            comm="test-comm",
            uid=10001,
            gid=10001,
            dest_ip="198.51.100.12",
            dest_port=9000,
        )
        cef_line = EnterpriseSIEMExporter.format_cef(evt)

        # Must conform to CEF:Version|Device Vendor|Device Product|Device Version|Device Event Class ID|Name|Severity|Extension
        parts = cef_line.split("|")
        assert len(parts) >= 8
        assert parts[0] == "CEF:0"
        assert parts[1] == "DevSuperSuite"
        assert parts[2] == "eBPF-Forensics-Engine"
        assert parts[4] == "sys_enter_connect"
        assert parts[6] == "10"  # High severity for block
        assert "dst=198.51.100.12:9000" in parts[7]
        assert "cs1Label=ForensicHash" in parts[7]
        assert "cn1Label=LatencyMicros" in parts[7]

    def test_06_rfc5424_syslog_serialization(self, engine):
        """Validates RFC 5424 Syslog structure, PRI code, structured-data, and message."""
        evt = engine.intercept_connect(
            pid=6666,
            ppid=1,
            comm="worker-thread",
            uid=10002,
            gid=10002,
            dest_ip="auth.devsupersuite.io",
            dest_port=443,
        )
        syslog_msg = EnterpriseSIEMExporter.format_rfc5424_syslog(evt)

        # RFC 5424 format: <PRI>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID [STRUCTURED-DATA] MSG
        pattern = r"^<\d+>1 \S+ \S+ ebpf-forensics 6666 EVT-EBPF-\d+ \[forensics@48577 .+\] .+"
        assert re.match(pattern, syslog_msg), f"Syslog message failed regex: {syslog_msg}"
        assert 'verdict="ALLOW"' in syslog_msg
        assert 'comm="worker-thread"' in syslog_msg

    def test_07_ndjson_exporter_and_parsing(self, engine):
        """Validates NDJSON streaming output is valid JSON and contains required forensic fields."""
        engine.intercept_connect(101, 1, "test", 10001, 10001, "127.0.0.1", 80)
        engine.intercept_connect(102, 1, "test", 10001, 10001, "198.51.100.1", 80)

        ndjson_stream = EnterpriseSIEMExporter.export_stream(engine.chain_of_custody, SIEMFormat.NDJSON)
        lines = ndjson_stream.strip().split("\n")
        assert len(lines) == 2

        for line in lines:
            data = json.loads(line)
            assert "event_id" in data
            assert "probe_type" in data
            assert "verdict" in data
            assert "killswitch_latency_us" in data
            assert "event_hash" in data
            assert data["vendor"] == "DevSuperSuite"

    def test_08_immutable_merkle_chain_of_custody(self, engine):
        """Verifies SHA-256 chain of custody and confirms tampering is detected."""
        engine.intercept_connect(101, 1, "test1", 10001, 10001, "127.0.0.1", 80)
        engine.intercept_connect(102, 1, "test2", 10001, 10001, "10.0.0.1", 443)
        engine.intercept_connect(103, 1, "test3", 10001, 10001, "198.51.100.1", 9999)

        is_valid, count, err = engine.verify_chain_of_custody()
        assert is_valid is True
        assert count == 3
        assert err is None

        # Simulate tampering with event at index 1
        tampered_event = engine.chain_of_custody[1]
        original_hash = tampered_event.event_hash
        tampered_event.event_hash = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"

        is_valid_tampered, failed_idx, err_tampered = engine.verify_chain_of_custody()
        assert is_valid_tampered is False
        assert failed_idx == 1
        assert "Event integrity violation" in err_tampered

        # Restore
        tampered_event.event_hash = original_hash

    def test_09_cli_interface_execution(self):
        """Verifies that all CLI flags execute with returncode 0."""
        engine_script = REPO_ROOT / "services" / "enterprise_ebpf_siem_forensics_engine.py"
        assert engine_script.exists()

        flags = [
            ["--summary"],
            ["--audit-ebpf-probes"],
            ["--simulate-threat-neutralization"],
            ["--verify-killswitch-latency"],
            ["--export-siem-stream", "CEF"],
            ["--export-siem-stream", "RFC5424"],
            ["--export-siem-stream", "NDJSON"],
        ]

        for flag_set in flags:
            proc = subprocess.run(
                [sys.executable, str(engine_script)] + flag_set,
                capture_output=True,
                text=True,
                timeout=15,
            )
            assert proc.returncode == 0, f"CLI command failed with {flag_set}: {proc.stderr}"
            assert "DevSuperSuite" in proc.stdout

    def test_10_strict_brand_anonymity_under_devsupersuite(self):
        """Enforces absolute brand anonymity under DevSuperSuite Official."""
        target_files = [
            REPO_ROOT / "services" / "enterprise_ebpf_siem_forensics_engine.py",
            REPO_ROOT / "services" / "enterprise_ebpf_forensics_policy.md",
            REPO_ROOT / "services" / "reports" / "ebpf_forensics_dossier.md",
            REPO_ROOT / "services" / "reports" / "siem_event_stream.ndjson",
        ]

        prohibited_names = [
            bytes.fromhex("70726174696b").decode("utf-8"),
            bytes.fromhex("7061646b6172").decode("utf-8"),
            bytes.fromhex("6174706164").decode("utf-8"),
        ]

        phone_pattern = re.compile(r"(?<![A-Za-z0-9_-])(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?![A-Za-z0-9_-])")

        for file_path in target_files:
            assert file_path.exists(), f"Target file does not exist: {file_path}"
            content = file_path.read_text(encoding="utf-8")

            # Check prohibited personal names
            for name in prohibited_names:
                assert name not in content.lower(), (
                    f"Brand anonymity violation: Found prohibited name '{name}' in {file_path.name}"
                )

            # Scrub safe timestamps and GUIDs before phone regex
            scrubbed = re.sub(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}", "", content)
            scrubbed = re.sub(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", "", scrubbed)
            scrubbed = re.sub(r"EVT-EBPF-\d+", "", scrubbed)
            scrubbed = re.sub(r"timestamp_mono_ns\":\d+", "", scrubbed)

            phone_matches = phone_pattern.findall(scrubbed)
            assert not phone_matches, (
                f"Brand anonymity violation: Found phone pattern in {file_path.name}: {phone_matches}"
            )

            # Confirm authorized corporate identity
            assert "DevSuperSuite" in content, (
                f"Missing corporate brand DevSuperSuite in {file_path.name}"
            )
