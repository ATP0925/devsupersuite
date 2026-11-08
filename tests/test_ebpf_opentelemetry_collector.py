#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - eBPF OpenTelemetry APM Collector Test Suite
Reference: DSS-EBPF-OTEL-TESTS-2026-V1
Classification: Automated Quality Gate & Invariant Validation (Restricted)
Contact: DevSuperSuite Solutions Architecture (solutions@devsupersuite.com)
Author: OmniKernel Labs / DevSuperSuite Quality Assurance & Test Engineering
═══════════════════════════════════════════════════════════════════════════════
"""

import copy
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = REPO_ROOT / "services"
REPORTS_DIR = SERVICES_DIR / "reports"
DEPLOYMENT_DIR = REPO_ROOT / "deployment"
OTEL_DIR = DEPLOYMENT_DIR / "otel"

if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from enterprise_ebpf_opentelemetry_collector import (
    ORGANIZATION_NAME,
    PRIMARY_CONTACT,
    TELEMETRY_CONTACT,
    REFERENCE_CODE,
    MAX_CPU_OVERHEAD_PERCENT,
    DEFAULT_RING_BUFFER_CAPACITY,
    W3C_TRACEPARENT_REGEX,
    W3CTraceContextEngine,
    EBPFGoldenSignalsExtractor,
    EncryptedRingBufferExporter,
    EnterpriseEBPFOpenTelemetryCollector
)


class TestEnterpriseEBPFOpenTelemetryCollector:
    """Enterprise verification suite for eBPF OpenTelemetry APM Distributed Collector."""

    def test_w3c_traceparent_generation_and_validation(self):
        """Validate W3C traceparent header generation, regex validation, and parsing."""
        traceparent = W3CTraceContextEngine.build_traceparent()
        assert W3C_TRACEPARENT_REGEX.match(traceparent) is not None

        parsed = W3CTraceContextEngine.parse_traceparent(traceparent)
        assert parsed["version"] == "00"
        assert len(parsed["trace_id"]) == 32
        assert len(parsed["parent_span_id"]) == 16
        assert parsed["sampled"] is True

        # Invalid traceparent format rejection
        with pytest.raises(ValueError):
            W3CTraceContextEngine.parse_traceparent("invalid-header-string")
        with pytest.raises(ValueError):
            W3CTraceContextEngine.parse_traceparent("01-traceid-spanid-01")

    def test_distributed_span_creation_and_parent_child_linking(self):
        """Verify distributed trace context propagation and parent-child span linkage."""
        root = W3CTraceContextEngine.create_span("HTTP GET /orders", "order-gateway")
        assert root["parent_span_id"] is None
        assert root["w3c_traceparent"].startswith(f"00-{root['trace_id']}-{root['span_id']}-")

        child = W3CTraceContextEngine.create_span(
            "SQL SELECT * FROM orders",
            "db-service",
            parent_traceparent=root["w3c_traceparent"]
        )

        assert child["trace_id"] == root["trace_id"]
        assert child["parent_span_id"] == root["span_id"]
        assert child["span_id"] != root["span_id"]
        assert child["service_name"] == "db-service"

    def test_ebpf_golden_signals_extraction(self):
        """Verify calculation of Google SRE Golden Signals: P50/P90/P99 latency, rate, errors, saturation."""
        extractor = EBPFGoldenSignalsExtractor()

        # Record 100 sample transactions with known distribution
        for i in range(1, 101):
            is_err = (i % 20 == 0)  # 5% error rate
            extractor.record_socket_transaction(duration_ms=float(i), is_error=is_err)

        signals = extractor.calculate_golden_signals(window_seconds=10.0, active_sockets=50, max_sockets=200)

        # Check Latency quantiles ordering
        lat = signals["latency"]
        assert lat["p50_ms"] <= lat["p90_ms"] <= lat["p99_ms"]
        assert 45.0 <= lat["p50_ms"] <= 55.0
        assert 85.0 <= lat["p90_ms"] <= 95.0

        # Check Traffic rate & Errors
        assert signals["traffic"]["rate_rps"] == 10.0  # 100 reqs / 10s
        assert signals["errors"]["error_count"] == 5
        assert signals["errors"]["error_rate_percentage"] == 5.0
        assert signals["saturation"]["saturation_percentage"] == 25.0  # 50 / 200

    def test_ebpf_cpu_overhead_benchmark_under_1_2_percent(self):
        """Verify in-kernel eBPF socket tracing consumes strictly < 1.2% CPU overhead."""
        benchmark = EBPFGoldenSignalsExtractor.benchmark_ebpf_cpu_overhead(iterations=5000)

        assert benchmark["measured_cpu_overhead_percent"] < MAX_CPU_OVERHEAD_PERCENT
        assert benchmark["measured_cpu_overhead_percent"] > 0.0
        assert benchmark["sub_1_2_percent_sla_met"] is True
        assert len(benchmark["probes_monitored"]) >= 3
        assert "kprobe/sock_sendmsg" in benchmark["probes_monitored"]

    def test_encrypted_ring_buffer_push_and_fifo_overflow(self):
        """Validate air-gapped ring buffer AES/HMAC encryption and FIFO drop on capacity overflow."""
        buffer = EncryptedRingBufferExporter(capacity=5)

        for i in range(5):
            span_sample = {"trace_id": f"trace-{i}", "span_id": f"span-{i}", "op": "test"}
            rec = buffer.push_span(span_sample)
            assert len(rec["hmac_auth_tag"]) == 64
            assert rec["encryption_algorithm"] == "AES-256-GCM-HSM"

        stats = buffer.get_buffer_stats()
        assert stats["current_buffered_spans"] == 5
        assert stats["dropped_spans_count"] == 0

        # Push 6th span -> triggers FIFO eviction of oldest span
        buffer.push_span({"trace_id": "trace-overflow", "span_id": "span-overflow"})
        overflow_stats = buffer.get_buffer_stats()
        assert overflow_stats["current_buffered_spans"] == 5
        assert overflow_stats["dropped_spans_count"] == 1

    def test_encrypted_ring_buffer_flush(self):
        """Validate draining and decryption of buffered spans for upstream batch forwarding."""
        buffer = EncryptedRingBufferExporter(capacity=10)
        buffer.push_span({"trace_id": "t1", "span_id": "s1", "service": "auth"})
        buffer.push_span({"trace_id": "t2", "span_id": "s2", "service": "payment"})

        flushed_spans = buffer.flush_spans()
        assert len(flushed_spans) == 2
        assert flushed_spans[0]["service"] == "auth"
        assert flushed_spans[1]["service"] == "payment"

        # Buffer must be empty after flush
        assert buffer.get_buffer_stats()["current_buffered_spans"] == 0

    def test_end_to_end_distributed_transaction_tracing(self):
        """Test complete workflow: eBPF socket intercept, W3C span creation, and ring buffer encryption."""
        collector = EnterpriseEBPFOpenTelemetryCollector()

        # Trace successful transaction
        res = collector.trace_distributed_transaction("ast-compiler", "CompileAST", duration_ms=16.8)
        assert res["span"]["status_code"] == "OK"
        assert res["span"]["duration_ms"] == 16.8
        assert "00-" in res["w3c_traceparent_outbound"]
        assert len(res["encrypted_record"]["hmac_auth_tag"]) == 64

        # Trace failed transaction
        err_res = collector.trace_distributed_transaction("payment-gateway", "ProcessCard", duration_ms=45.2, is_error=True)
        assert err_res["span"]["status_code"] == "ERROR"
        assert err_res["span"]["attributes"]["http.status_code"] == 500

    def test_otel_collector_yaml_config_export_and_validity(self, tmp_path):
        """Verify OpenTelemetry Collector v0.100+ pipeline configuration export and syntax."""
        collector = EnterpriseEBPFOpenTelemetryCollector()
        target_file = tmp_path / "otel_collector_config.yaml"
        collector.export_collector_yaml_config(target_file)

        assert target_file.exists()
        yaml_content = target_file.read_text(encoding="utf-8")

        assert "receivers:" in yaml_content
        assert "ebpf:" in yaml_content
        assert "kprobe/sock_sendmsg" in yaml_content
        assert "otlp:" in yaml_content
        assert "processors:" in yaml_content
        assert "memory_limiter:" in yaml_content
        assert "file/ring_buffer:" in yaml_content
        assert "pipelines:" in yaml_content
        assert PRIMARY_CONTACT in yaml_content

    def test_architecture_report_generation(self, tmp_path):
        """Verify technical whitepaper and APM collector architecture report export."""
        collector = EnterpriseEBPFOpenTelemetryCollector()
        report_file = tmp_path / "ebpf_opentelemetry_apm_report.md"
        collector.export_architecture_report(report_file)

        assert report_file.exists()
        report_text = report_file.read_text(encoding="utf-8")

        assert "In-Kernel eBPF OpenTelemetry APM Collector" in report_text
        assert "kprobe/sock_sendmsg" in report_text
        assert "W3C TraceContext" in report_text
        assert "Air-Gapped Offline OTLP Ring Buffer" in report_text
        assert PRIMARY_CONTACT in report_text

    def test_brand_anonymity_invariants(self):
        """
        Enforce strict institutional brand anonymity:
        Must NOT contain personal names or unauthorized personal email domains.
        Must strictly represent DevSuperSuite Solutions Architecture / OmniKernel Labs.
        """
        forbidden_terms = ["github.com/", "gitlab.com/", "@gmail.com", "@yahoo.com", "@hotmail.com"]
        files_to_check = [
            SERVICES_DIR / "enterprise_ebpf_opentelemetry_collector.py",
            OTEL_DIR / "otel_collector_config.yaml",
            REPORTS_DIR / "ebpf_opentelemetry_apm_report.md"
        ]

        for filepath in files_to_check:
            assert filepath.exists(), f"Expected file {filepath} to exist."
            content = filepath.read_text(encoding="utf-8")

            for term in forbidden_terms:
                assert term not in content.lower(), f"Forbidden term '{term}' found in {filepath.name}"

            assert "DevSuperSuite" in content or "OmniKernel Labs" in content, (
                f"Missing institutional brand in {filepath.name}"
            )
            assert "solutions@devsupersuite.com" in content, (
                f"Missing official contact in {filepath.name}"
            )

    def test_cli_flags_execution(self):
        """Ensure all CLI interface flags execute cleanly with exit code 0."""
        python_exe = sys.executable
        script = str(SERVICES_DIR / "enterprise_ebpf_opentelemetry_collector.py")

        commands = [
            [python_exe, script, "--summary"],
            [python_exe, script, "--benchmark-ebpf-overhead"],
            [python_exe, script, "--simulate-w3c-propagation"],
            [python_exe, script, "--trace-transaction", "test-service", "TestOperation"],
            [python_exe, script, "--flush-ring-buffer"],
            [python_exe, script, "--export-otel-bundle"]
        ]

        for cmd in commands:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            assert res.returncode == 0, f"Command failed: {' '.join(cmd)}\nStderr: {res.stderr}"
            assert len(res.stdout) > 0
