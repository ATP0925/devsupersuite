#!/usr/bin/env python3
"""
Unit and Integration Tests for Enterprise APM Observability Integration Kit
Reference: tests/test_apm_observability.py
Classification: Automated Quality Gate (100% Pass Required)
Contact: observability@devsupersuite.com
"""

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.enterprise_apm_observability_integrator import (
    DatadogDashboardGenerator,
    SplunkAppGenerator,
    PrometheusMetricsExporter,
    GrafanaDashboardGenerator,
    ApmReportExporter,
    run_cli
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Datadog Dashboard Manifest Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_datadog_dashboard_schema_validity():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_dd_test_"))
    try:
        out_file = temp_dir / "dd_test.json"
        dashboard = DatadogDashboardGenerator.generate_manifest(out_file)

        assert out_file.exists()
        assert "title" in dashboard
        assert "DevSuperSuite" in dashboard["title"]
        assert "widgets" in dashboard
        assert len(dashboard["widgets"]) >= 5

        # Check required metric queries exist
        queries = []
        for w in dashboard["widgets"]:
            reqs = w.get("definition", {}).get("requests", [])
            for r in reqs:
                if "q" in r:
                    queries.append(r["q"])

        all_queries = " ".join(queries)
        assert "devsupersuite.ast.token_reduction_pct" in all_queries
        assert "devsupersuite.proxy.ttft_ms" in all_queries
        assert "devsupersuite.security.secrets_intercepted_total" in all_queries
        assert "devsupersuite.seats.active" in all_queries
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Grafana Dashboard JSON Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_grafana_dashboard_schema_validity():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_graf_test_"))
    try:
        out_file = temp_dir / "graf_test.json"
        dashboard = GrafanaDashboardGenerator.generate_dashboard(out_file)

        assert out_file.exists()
        assert dashboard["uid"] == "dss-enterprise-apm"
        assert "DevSuperSuite" in dashboard["title"]
        assert "panels" in dashboard
        assert len(dashboard["panels"]) >= 6

        # Check panel metrics
        exprs = []
        for p in dashboard["panels"]:
            for t in p.get("targets", []):
                if "expr" in t:
                    exprs.append(t["expr"])

        all_exprs = " ".join(exprs)
        assert "devsupersuite_ast_token_reduction_ratio" in all_exprs
        assert "devsupersuite_security_secrets_intercepted_total" in all_exprs
        assert "devsupersuite_airgap_egress_violations_total" in all_exprs
        assert "devsupersuite_proxy_ast_prune_latency_seconds_bucket" in all_exprs
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Splunk Technology Add-On Package Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_splunk_ta_package_syntax():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_splunk_test_"))
    try:
        app_dir = temp_dir / "splunk_app_devsupersuite"
        files = SplunkAppGenerator.generate_ta_package(app_dir)

        assert Path(files["app.conf"]).exists()
        assert Path(files["props.conf"]).exists()
        assert Path(files["transforms.conf"]).exists()
        assert Path(files["eventtypes.conf"]).exists()

        # Check props.conf sourcetype & extractions
        props = Path(files["props.conf"]).read_text(encoding="utf-8")
        assert "[devsupersuite:audit]" in props
        assert "KV_MODE = json" in props

        # Check transforms.conf regex
        transforms = Path(files["transforms.conf"]).read_text(encoding="utf-8")
        assert "[devsupersuite_secret_extraction]" in transforms
        assert "[devsupersuite_ast_metrics_extraction]" in transforms

        # Check eventtypes.conf SOC correlation
        eventtypes = Path(files["eventtypes.conf"]).read_text(encoding="utf-8")
        assert "[devsupersuite_security_alert]" in eventtypes
        assert "[devsupersuite_airgap_egress_violation]" in eventtypes
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Prometheus OpenMetrics Naming & Formatting Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_prometheus_metrics_naming_and_format():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_prom_test_"))
    try:
        prom_file = temp_dir / "metrics.prom"
        text = PrometheusMetricsExporter.render_metrics_spec(prom_file)

        assert prom_file.exists()
        assert "# HELP" in text
        assert "# TYPE" in text

        # Verify OpenMetrics counter convention: must end with _total
        counters = re.findall(r"# TYPE\s+(\w+)\s+counter", text)
        assert len(counters) >= 4
        for c in counters:
            assert c.endswith("_total"), f"Prometheus counter '{c}' must end with '_total'"

        # Verify gauges and histograms
        gauges = re.findall(r"# TYPE\s+(\w+)\s+gauge", text)
        assert len(gauges) >= 2
        assert "devsupersuite_ast_token_reduction_ratio" in gauges

        histograms = re.findall(r"# TYPE\s+(\w+)\s+histogram", text)
        assert len(histograms) >= 2
        assert "devsupersuite_proxy_ast_prune_latency_seconds" in histograms
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Brand Anonymity Verification
# ─────────────────────────────────────────────────────────────────────────────

def test_brand_anonymity_invariants():
    script_path = Path(r"C:\Users\atpad\.gemini\antigravity\scratch\agent-commerce\services\enterprise_apm_observability_integrator.py")
    guide_path = Path(r"C:\Users\atpad\.gemini\antigravity\scratch\agent-commerce\services\enterprise_apm_integration_guide.md")

    for p in [script_path, guide_path]:
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
# 6. Report Exporter Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_report_exporters():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_rep_apm_"))
    try:
        guide_out = temp_dir / "guide.md"
        report_out = temp_dir / "report.md"

        ApmReportExporter.export_integration_guide(guide_out)
        assert guide_out.exists()
        g_text = guide_out.read_text(encoding="utf-8")
        assert "Enterprise APM Observability Integration Guide" in g_text
        assert "P1 - CRITICAL" in g_text

        ApmReportExporter.export_audit_report(
            {"datadog": "mock.json", "splunk": "mock_ta", "prometheus": "mock.prom", "grafana": "mock_graf.json"},
            report_out
        )
        assert report_out.exists()
        r_text = report_out.read_text(encoding="utf-8")
        assert "DevSuperSuite Enterprise APM Observability Integration Audit Report" in r_text
        assert "CERTIFIED_APM_COMPLIANT" in r_text
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# 7. CLI Execution Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_cli_execution_all_flags():
    temp_dir = Path(tempfile.mkdtemp(prefix="dss_cli_apm_"))
    try:
        dd_out = temp_dir / "dd.json"
        splunk_out = temp_dir / "splunk_ta"
        prom_out = temp_dir / "spec.prom"
        graf_out = temp_dir / "graf.json"
        guide_out = temp_dir / "guide.md"
        report_out = temp_dir / "report.md"

        ret = run_cli([
            "--generate-datadog-manifest",
            "--generate-splunk-package",
            "--export-prometheus-spec",
            "--generate-grafana-json",
            "--summary",
            "--datadog-out", str(dd_out),
            "--splunk-out-dir", str(splunk_out),
            "--prometheus-out", str(prom_out),
            "--grafana-out", str(graf_out),
            "--guide-out", str(guide_out),
            "--report-out", str(report_out)
        ])

        assert ret == 0
        assert dd_out.exists()
        assert (splunk_out / "default" / "props.conf").exists()
        assert prom_out.exists()
        assert graf_out.exists()
        assert guide_out.exists()
        assert report_out.exists()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
