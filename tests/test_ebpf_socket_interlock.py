"""
DevSuperSuite Tech Services - eBPF Zero-Trust Socket Interlock & Air-Gap Test Suite
File: tests/test_ebpf_socket_interlock.py
Governing Authority: DevSuperSuite Security & Compliance Desk
Contact: security@devsupersuite.com
Regulatory Standards: CNSSP-15 / NIST SP 800-53 (AC-4, SC-7) / SOC 2 CC6.6
"""

import json
from pathlib import Path
import re
import subprocess
import sys
import time
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from services.enterprise_ebpf_socket_interlock import (
    EBPFSocketInterlockEngine,
    EBPFAuditLogger,
    SIEMAlertFormatter,
    SocketConnectionRequest,
    SocketFamily,
    TransportProtocol,
    InterlockVerdict,
    export_ebpf_airgap_whitepaper,
)


class TestEnterpriseEBPFSocketInterlock:
    """Comprehensive test suite for Linux eBPF LSM and sock_ops air-gap enforcement."""

    @pytest.fixture
    def engine(self):
        return EBPFSocketInterlockEngine()

    def test_01_loopback_ipv4_and_ipv6_authorized(self, engine):
        """Verifies SCIF loopback addresses (127.0.0.1 and ::1) are strictly authorized."""
        req_v4 = SocketConnectionRequest(
            request_id="REQ-TEST-LB4",
            timestamp_ns=time.perf_counter_ns(),
            pid=1001,
            comm="auth-service",
            uid=1000,
            family=SocketFamily.AF_INET,
            protocol=TransportProtocol.TCP,
            src_addr="127.0.0.1",
            src_port=45000,
            dst_addr="127.0.0.1",
            dst_port=8080,
        )
        dec_v4 = engine.evaluate_socket_connection(req_v4)
        assert dec_v4.verdict == InterlockVerdict.ALLOW_SCIF_LOOPBACK
        assert dec_v4.allowed is True
        assert dec_v4.latency_us < 5.0

        req_v6 = SocketConnectionRequest(
            request_id="REQ-TEST-LB6",
            timestamp_ns=time.perf_counter_ns(),
            pid=1002,
            comm="auth-service-v6",
            uid=1000,
            family=SocketFamily.AF_INET6,
            protocol=TransportProtocol.TCP,
            src_addr="::1",
            src_port=45002,
            dst_addr="::1",
            dst_port=8080,
        )
        dec_v6 = engine.evaluate_socket_connection(req_v6)
        assert dec_v6.verdict == InterlockVerdict.ALLOW_SCIF_LOOPBACK
        assert dec_v6.allowed is True

    def test_02_unix_domain_sockets_authorized(self, engine):
        """Verifies authorized local unix domain sockets are allowed for IPC."""
        req_unix = SocketConnectionRequest(
            request_id="REQ-TEST-UNIX-01",
            timestamp_ns=time.perf_counter_ns(),
            pid=2001,
            comm="db-connector",
            uid=1000,
            family=SocketFamily.AF_UNIX,
            protocol=TransportProtocol.UNIX_STREAM,
            src_addr="",
            src_port=0,
            dst_addr="/var/run/devsupersuite/database.sock",
            dst_port=0,
        )
        dec = engine.evaluate_socket_connection(req_unix)
        assert dec.verdict == InterlockVerdict.ALLOW_UNIX_SOCKET
        assert dec.allowed is True

    def test_03_external_public_ipv4_blocked(self, engine):
        """Verifies public IPv4 destinations are mechanically dropped at kernel level."""
        public_ips = ["8.8.8.8", "93.184.216.34", "1.1.1.1", "142.250.190.46"]
        for ip in public_ips:
            req = SocketConnectionRequest(
                request_id=f"REQ-TEST-PUB4-{ip.replace('.', '-')}",
                timestamp_ns=time.perf_counter_ns(),
                pid=3001,
                comm="rogue-curl",
                uid=1001,
                family=SocketFamily.AF_INET,
                protocol=TransportProtocol.TCP,
                src_addr="10.240.1.10",
                src_port=52000,
                dst_addr=ip,
                dst_port=443,
            )
            dec = engine.evaluate_socket_connection(req)
            assert dec.verdict == InterlockVerdict.DROP_AIRGAP_VIOLATION
            assert dec.allowed is False
            assert "blocked egress attempt" in dec.reason

    def test_04_external_public_ipv6_blocked(self, engine):
        """Verifies public IPv6 destinations are mechanically dropped."""
        public_v6 = ["2001:4860:4860::8888", "2606:4700:4700::1111"]
        for ip in public_v6:
            req = SocketConnectionRequest(
                request_id="REQ-TEST-PUB6",
                timestamp_ns=time.perf_counter_ns(),
                pid=3005,
                comm="rogue-downloader",
                uid=1001,
                family=SocketFamily.AF_INET6,
                protocol=TransportProtocol.TCP,
                src_addr="::1",
                src_port=52010,
                dst_addr=ip,
                dst_port=443,
            )
            dec = engine.evaluate_socket_connection(req)
            assert dec.verdict == InterlockVerdict.DROP_AIRGAP_VIOLATION
            assert dec.allowed is False

    def test_05_internal_scif_cidr_authorized(self, engine):
        """Verifies authorized internal SCIF enclave subnets (10.240.0.0/16) are permitted."""
        internal_ips = ["10.240.1.5", "10.240.250.199", "172.16.50.25"]
        for ip in internal_ips:
            req = SocketConnectionRequest(
                request_id=f"REQ-TEST-ENCLAVE-{ip.replace('.', '-')}",
                timestamp_ns=time.perf_counter_ns(),
                pid=4001,
                comm="scif-sync-agent",
                uid=1000,
                family=SocketFamily.AF_INET,
                protocol=TransportProtocol.TCP,
                src_addr="10.240.1.2",
                src_port=49000,
                dst_addr=ip,
                dst_port=8443,
            )
            dec = engine.evaluate_socket_connection(req)
            assert dec.verdict == InterlockVerdict.ALLOW_INTERNAL_ENCLAVE
            assert dec.allowed is True

    def test_06_fail_closed_on_invalid_or_unknown_destination(self, engine):
        """Verifies fail-closed behavior on malformed addresses or unauthorized unix paths."""
        # Malformed IP
        req_bad_ip = SocketConnectionRequest(
            request_id="REQ-TEST-MALFORMED",
            timestamp_ns=time.perf_counter_ns(),
            pid=5001,
            comm="fuzzer",
            uid=1001,
            family=SocketFamily.AF_INET,
            protocol=TransportProtocol.TCP,
            src_addr="127.0.0.1",
            src_port=50000,
            dst_addr="999.999.999.999",
            dst_port=80,
        )
        dec_bad_ip = engine.evaluate_socket_connection(req_bad_ip)
        assert dec_bad_ip.verdict == InterlockVerdict.DROP_FAIL_CLOSED
        assert dec_bad_ip.allowed is False

        # Unauthorized Unix Socket path
        req_bad_unix = SocketConnectionRequest(
            request_id="REQ-TEST-UNAUTH-UNIX",
            timestamp_ns=time.perf_counter_ns(),
            pid=5002,
            comm="exploit",
            uid=1001,
            family=SocketFamily.AF_UNIX,
            protocol=TransportProtocol.UNIX_STREAM,
            src_addr="",
            src_port=0,
            dst_addr="/etc/systemd/private.raw",
            dst_port=0,
        )
        dec_bad_unix = engine.evaluate_socket_connection(req_bad_unix)
        assert dec_bad_unix.verdict == InterlockVerdict.DROP_FAIL_CLOSED
        assert dec_bad_unix.allowed is False

    def test_07_kernel_interception_latency_under_5us(self, engine):
        """Verifies all decisions execute strictly within the sub-5.0-microsecond kernel ceiling."""
        for i in range(100):
            req = SocketConnectionRequest(
                request_id=f"REQ-PERF-{i}",
                timestamp_ns=time.perf_counter_ns(),
                pid=6000 + i,
                comm="test-perf",
                uid=1000,
                family=SocketFamily.AF_INET,
                protocol=TransportProtocol.TCP,
                src_addr="127.0.0.1",
                src_port=40000 + i,
                dst_addr="127.0.0.1",
                dst_port=9000,
            )
            dec = engine.evaluate_socket_connection(req)
            assert dec.latency_us < 5.0, f"Latency breached: {dec.latency_us} µs >= 5.0 µs"

        assert engine.average_latency_us < 5.0
        assert engine.average_latency_us > 0.0

    def test_08_tamper_resistant_audit_log_hash_chain(self, tmp_path):
        """Verifies cryptographic SHA-256 hash chaining and tamper detection in audit log."""
        test_log_file = tmp_path / "test_ebpf_audit.json"
        logger = EBPFAuditLogger(log_path=test_log_file)
        engine = EBPFSocketInterlockEngine()

        # Log 5 decisions
        for idx in range(5):
            req = SocketConnectionRequest(
                request_id=f"REQ-CHAIN-{idx}",
                timestamp_ns=time.perf_counter_ns(),
                pid=7000 + idx,
                comm="agent",
                uid=1000,
                family=SocketFamily.AF_INET,
                protocol=TransportProtocol.TCP,
                src_addr="127.0.0.1",
                src_port=41000 + idx,
                dst_addr="127.0.0.1" if idx % 2 == 0 else "8.8.8.8",
                dst_port=80,
            )
            dec = engine.evaluate_socket_connection(req)
            logger.log_decision(dec)

        # Verify pristine chain
        is_valid, count, msg = EBPFAuditLogger.verify_audit_log_chain(test_log_file)
        assert is_valid is True
        assert count == 5
        assert "Chain intact" in msg

        # Tamper with an entry
        with open(test_log_file, "r", encoding="utf-8") as f:
            tampered_data = json.load(f)

        tampered_data[2]["decision"]["reason"] = "FORGED_REASON_BY_ADVERSARY"
        with open(test_log_file, "w", encoding="utf-8") as f:
            json.dump(tampered_data, f, indent=2)

        # Verify tamper is flagged
        is_valid_after, bad_idx, err_msg = EBPFAuditLogger.verify_audit_log_chain(test_log_file)
        assert is_valid_after is False
        assert bad_idx == 2
        assert "Hash tamper detected" in err_msg

    def test_09_siem_event_formatting_cef_and_rfc5424(self, engine):
        """Verifies SIEM alert formatting into ArcSight CEF v25 and RFC 5424 Syslog."""
        req = SocketConnectionRequest(
            request_id="REQ-SIEM-TEST",
            timestamp_ns=time.perf_counter_ns(),
            pid=8080,
            comm="exfil-process",
            uid=1002,
            family=SocketFamily.AF_INET,
            protocol=TransportProtocol.TCP,
            src_addr="10.240.1.99",
            src_port=60001,
            dst_addr="198.51.100.1",
            dst_port=443,
        )
        dec = engine.evaluate_socket_connection(req)

        # Test CEF
        cef = SIEMAlertFormatter.format_cef(dec)
        assert cef.startswith("CEF:0|DevSuperSuite|KernelEBPFInterlock|1.0|DROP_AIRGAP_VIOLATION|")
        assert "dst=198.51.100.1" in cef
        assert "act=DROP" in cef
        assert "cn1=" in cef

        # Test RFC 5424
        rfc = SIEMAlertFormatter.format_rfc5424(dec)
        assert rfc.startswith("<11>1")
        assert "devsupersuite-scif" in rfc
        assert "ebpf-interlock" in rfc
        assert "verdict=\"DROP_AIRGAP_VIOLATION\"" in rfc

    def test_10_attestation_report_generation_and_content(self, engine):
        """Verifies generation of executive whitepaper and checks governing compliance frameworks."""
        audit_logger = EBPFAuditLogger()
        req = SocketConnectionRequest(
            request_id="REQ-SAMPLE-RPT",
            timestamp_ns=time.perf_counter_ns(),
            pid=9001,
            comm="sample-app",
            uid=1000,
            family=SocketFamily.AF_INET,
            protocol=TransportProtocol.TCP,
            src_addr="127.0.0.1",
            src_port=30000,
            dst_addr="127.0.0.1",
            dst_port=8080,
        )
        sample_dec = engine.evaluate_socket_connection(req)
        report_path = export_ebpf_airgap_whitepaper(engine, audit_logger, [sample_dec])

        assert report_path.exists()
        text = report_path.read_text(encoding="utf-8")
        assert "CNSSP-15" in text
        assert "NIST SP 800-53 Rev 5" in text
        assert "AC-4" in text
        assert "SC-7" in text
        assert "SOC 2 Type II" in text
        assert "ISO/IEC 27001:2022" in text
        assert "DevSuperSuite" in text
        assert "security@devsupersuite.com" in text

    def test_11_cli_interface_all_flags(self):
        """Verifies CLI flags execute with zero exit code and DevSuperSuite branding."""
        script_path = REPO_ROOT / "services" / "enterprise_ebpf_socket_interlock.py"
        assert script_path.exists()

        flags = [
            ["--audit-rules"],
            ["--simulate-packet"],
            ["--export-whitepaper"],
            ["--export-audit-log"],
            ["--verify-airgap"],
        ]

        for flag_set in flags:
            proc = subprocess.run(
                [sys.executable, str(script_path)] + flag_set,
                capture_output=True,
                text=True,
                timeout=20,
            )
            assert proc.returncode == 0, f"CLI execution failed with {flag_set}: {proc.stderr}"
            assert "DevSuperSuite" in proc.stdout

    def test_12_strict_brand_anonymity_under_devsupersuite(self):
        """Enforces 100% brand anonymity under DevSuperSuite Security & Compliance Desk."""
        target_files = [
            REPO_ROOT / "services" / "enterprise_ebpf_socket_interlock.py",
            REPO_ROOT / "services" / "reports" / "ebpf_airgap_socket_attestation_report.md",
            REPO_ROOT / "data" / "ebpf_socket_audit_log.json",
        ]

        prohibited_names = [
            bytes.fromhex("70726174696b").decode("utf-8"),
            bytes.fromhex("7061646b6172").decode("utf-8"),
            bytes.fromhex("6174706164").decode("utf-8"),
        ]

        phone_pattern = re.compile(
            r"(?<![A-Za-z0-9_-])(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?![A-Za-z0-9_-])"
        )

        for file_path in target_files:
            assert file_path.exists(), f"Target file does not exist: {file_path}"
            content = file_path.read_text(encoding="utf-8")

            # Check prohibited personal names
            for name in prohibited_names:
                assert name not in content.lower(), (
                    f"Brand anonymity violation: Found prohibited name '{name}' in {file_path.name}"
                )

            # Scrub safe timestamps, ISO dates, GUIDs before phone regex
            scrubbed = re.sub(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}", "", content)
            scrubbed = re.sub(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", "", scrubbed)
            scrubbed = re.sub(r"WHITEPAPER-EBPF-AIRGAP-\d{4}-V\d", "", scrubbed)

            phone_matches = phone_pattern.findall(scrubbed)
            assert not phone_matches, (
                f"Brand anonymity violation: Found phone pattern in {file_path.name}: {phone_matches}"
            )

            # Confirm corporate branding
            assert "DevSuperSuite" in content, (
                f"Missing corporate brand DevSuperSuite in {file_path.name}"
            )
            assert "security@devsupersuite.com" in content, (
                f"Missing corporate email in {file_path.name}"
            )

