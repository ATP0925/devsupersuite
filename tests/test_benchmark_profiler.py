#!/usr/bin/env python3
"""
Unit and Integration Tests for Enterprise Technical Benchmark Profiler Engine
Reference: tests/test_benchmark_profiler.py
Classification: Automated Quality Gate (100% Pass Required)
Contact: benchmarks@devsupersuite.com
"""

import json
import os
import random
import re
import shutil
import sys
import tempfile
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.enterprise_benchmark_profiler import (
    calculate_percentile,
    calculate_shannon_entropy,
    BenchmarkFixtureGenerator,
    BenchmarkProfilerEngine,
    BenchmarkReportExporter,
    run_cli,
    MAX_P99_LATENCY_MS,
    MAX_PEAK_RSS_MB,
    MIN_TOKEN_REDUCTION_PCT,
    MAX_TRIPWIRE_LATENCY_MS,
    MIN_ENTROPY_THROUGHPUT_LOC_S
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Percentile Math & Statistical Utilities Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_calculate_percentile_monotonic_ordering():
    # Test with random float values
    data = [random.uniform(0.1, 5.0) for _ in range(100)]
    p50 = calculate_percentile(data, 50.0)
    p95 = calculate_percentile(data, 95.0)
    p99 = calculate_percentile(data, 99.0)

    assert p50 <= p95, f"p50 ({p50}) must be <= p95 ({p95})"
    assert p95 <= p99, f"p95 ({p95}) must be <= p99 ({p99})"


def test_calculate_percentile_edge_cases():
    assert calculate_percentile([], 50.0) == 0.0
    assert calculate_percentile([4.2], 99.0) == 4.2
    assert calculate_percentile([1.0, 1.0, 1.0], 50.0) == 1.0
    assert calculate_percentile([1.0, 2.0, 3.0, 4.0, 5.0], 50.0) == 3.0


def test_calculate_shannon_entropy_values():
    assert calculate_shannon_entropy("") == 0.0
    assert calculate_shannon_entropy("aaaaaaa") == 0.0
    assert calculate_shannon_entropy("abcdefgh") == 3.0
    secret = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    assert calculate_shannon_entropy(secret) > 3.5


# ─────────────────────────────────────────────────────────────────────────────
# 2. Synthetic Code Generation Tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("lang", ["Python", "TypeScript", "Rust", "Go", "C++"])
def test_synthetic_code_generation_languages(lang):
    code = BenchmarkFixtureGenerator.generate_synthetic_code(lang, 10000)
    assert len(code) > 100
    assert "target" in code.lower()


# ─────────────────────────────────────────────────────────────────────────────
# 3. AST Slicing Latency & Memory Profiling Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_ast_slicing_profiling_thresholds():
    engine = BenchmarkProfilerEngine(sample_iterations=15)
    res = engine.profile_ast_slicing_latencies("Python", 10000)

    lat = res["latencies_ms"]
    tok = res["token_compression"]
    mem = res["memory_usage"]

    # Verify Monotonic Latency Ordering
    assert lat["p50"] <= lat["p95"] <= lat["p99"]

    # Verify SLA Ceilings
    assert lat["p99"] <= MAX_P99_LATENCY_MS, f"p99 ({lat['p99']}ms) exceeds ceiling ({MAX_P99_LATENCY_MS}ms)"
    assert lat["p99_sla_met"] is True

    # Verify Memory Footprint < 45MB
    assert mem["peak_rss_mb"] <= MAX_PEAK_RSS_MB
    assert mem["rss_sla_met"] is True

    # Verify Token Reduction >= 70%
    assert tok["reduction_percentage"] >= MIN_TOKEN_REDUCTION_PCT
    assert tok["sla_met"] is True


def test_shannon_entropy_scanner_profiling():
    engine = BenchmarkProfilerEngine()
    res = engine.profile_shannon_entropy_scanner(loc_count=10000)

    slas = res["slas"]
    assert res["secrets_detected"] > 0
    assert res["throughput_loc_per_sec"] >= MIN_ENTROPY_THROUGHPUT_LOC_S
    assert slas["throughput_sla_met"] is True
    assert res["tripwire_latency_ms"] <= MAX_TRIPWIRE_LATENCY_MS
    assert slas["tripwire_sla_met"] is True


def test_full_benchmark_suite_execution():
    engine = BenchmarkProfilerEngine(sample_iterations=10)
    suite = engine.run_full_suite()

    assert suite["status"] == "CERTIFIED_HIGH_PERFORMANCE"
    assert len(suite["suite_results"]) == 5
    languages = [r["language"] for r in suite["suite_results"]]
    assert "Python" in languages
    assert "TypeScript" in languages
    assert "Rust" in languages
    assert "Go" in languages
    assert "C++" in languages


# ─────────────────────────────────────────────────────────────────────────────
# 4. Brand Anonymity Verification
# ─────────────────────────────────────────────────────────────────────────────

def test_brand_anonymity_invariants():
    script_path = Path(r"C:\Users\atpad\.gemini\antigravity\scratch\agent-commerce\services\enterprise_benchmark_profiler.py")
    report_path = Path(r"C:\Users\atpad\.gemini\antigravity\scratch\agent-commerce\services\enterprise_technical_benchmark_report.md")

    for p in [script_path, report_path]:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")

        # Must contain institutional brands
        assert "DevSuperSuite" in text
        assert "OmniKernel Labs" in text

        # Must not contain personal phone numbers or external emails
        assert not re.search(r"\+1[- ]?\d{3}[- ]?\d{3}[- ]?\d{4}", text)
        assert not re.search(r"\b\d{3}[-.]\d{3}[-.]\d{4}\b", text)
        assert "gmail.com" not in text
        assert "yahoo.com" not in text
        assert "hotmail.com" not in text


# ─────────────────────────────────────────────────────────────────────────────
# 5. Report Exporter Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_report_exporter_outputs():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_bench_rep_"))
    try:
        rep_file = temp_dir / "bench_report.md"
        aud_file = temp_dir / "bench_audit.md"

        engine = BenchmarkProfilerEngine(sample_iterations=5)
        suite = engine.run_full_suite()

        BenchmarkReportExporter.export_technical_report(suite, rep_file)
        assert rep_file.exists()
        rep_text = rep_file.read_text(encoding="utf-8")
        assert "Enterprise Technical Benchmark Report" in rep_text
        assert "Sub-2.4ms AST Slicing Latency" in rep_text
        assert "Python" in rep_text

        BenchmarkReportExporter.export_audit_report(suite, aud_file)
        assert aud_file.exists()
        aud_text = aud_file.read_text(encoding="utf-8")
        assert "DevSuperSuite Technical Benchmark Audit Report" in aud_text
        assert "[PASS]" in aud_text
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# 6. CLI Execution Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_cli_execution_all_flags():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_cli_bench_"))
    try:
        rep_file = temp_dir / "cli_report.md"
        aud_file = temp_dir / "cli_audit.md"
        json_file = temp_dir / "cli_results.json"

        ret = run_cli([
            "--run-benchmark-suite",
            "--export-benchmark-matrix",
            "--generate-performance-whitepaper",
            "--summary",
            "--samples", "5",
            "--output-report", str(rep_file),
            "--output-audit", str(aud_file),
            "--output-json", str(json_file)
        ])

        assert ret == 0
        assert rep_file.exists()
        assert aud_file.exists()
        assert json_file.exists()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
