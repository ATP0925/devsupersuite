#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Edge CDN PoP Controller Test Suite
Reference: DSS-EDGE-CDN-TESTS-2026-V1
Classification: Automated Quality Gate & Invariant Validation (Restricted)
Contact: DevSuperSuite Solutions Architecture (solutions@devsupersuite.com)
Author: OmniKernel Labs / DevSuperSuite Quality Assurance & Test Engineering
═══════════════════════════════════════════════════════════════════════════════
"""

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
EDGE_DIR = DEPLOYMENT_DIR / "edge"

# Add services directory to sys.path
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from enterprise_edge_cdn_controller import (
    GLOBAL_EDGE_POPS,
    CLIENT_PRESETS,
    EARTH_RADIUS_KM,
    FAILOVER_THRESHOLD_CONSECUTIVE_FAILURES,
    FAILOVER_PROBE_INTERVAL_MS,
    DEFAULT_BURST_CAPACITY,
    DEFAULT_REFILL_RATE,
    ANYCAST_GLOBAL_IP,
    ANYCAST_BGP_ASN,
    ORGANIZATION_NAME,
    PRIMARY_CONTACT,
    TECHNICAL_CONTACT,
    haversine_distance,
    estimate_rtt_latency,
    resolve_client_location,
    TokenBucketRateLimiter,
    EdgeWAFInspector,
    EnterpriseEdgeCDNController
)


class TestEnterpriseEdgeCDNController:
    """Enterprise verification suite for Edge CDN PoP Routing & Geo-DNS Controller."""

    def test_edge_pop_registry_initialization(self):
        """Verify all 5 institutional PoPs are registered with complete parameters."""
        controller = EnterpriseEdgeCDNController()
        pops = controller.list_pops()
        assert len(pops) == 5

        expected_pop_ids = {"iad-01", "fra-01", "nrt-01", "sin-01", "bom-01"}
        assert {p["pop_id"] for p in pops} == expected_pop_ids

        for pop in pops:
            assert pop["status"] == "HEALTHY"
            assert pop["health_score"] == 100.0
            assert pop["consecutive_failures"] == 0
            assert pop["anycast_ip"] == ANYCAST_GLOBAL_IP
            assert pop["bgp_anycast_asn"] == ANYCAST_BGP_ASN
            assert "origin_target" in pop
            assert -90.0 <= pop["latitude"] <= 90.0
            assert -180.0 <= pop["longitude"] <= 180.0
            assert pop["capacity_rps"] > 50000

    def test_haversine_distance_calculation(self):
        """Validate spherical Great Circle distance calculations against standard benchmarks."""
        # Zero distance
        assert haversine_distance(39.0438, -77.4874, 39.0438, -77.4874) == 0.0

        # Ashburn to New York (~350 km)
        d_ny_iad = haversine_distance(40.7128, -74.0060, 39.0438, -77.4874)
        assert 340.0 <= d_ny_iad <= 360.0

        # London to Frankfurt (~638 km)
        d_lon_fra = haversine_distance(51.5074, -0.1278, 50.1109, 8.6821)
        assert 620.0 <= d_lon_fra <= 650.0

        # Tokyo to Osaka (~392 km)
        d_tyo_osa = haversine_distance(35.6762, 139.6503, 34.6937, 135.5023)
        assert 380.0 <= d_tyo_osa <= 410.0

    def test_estimate_rtt_latency_model(self):
        """Ensure latency estimation scales with distance and reflects health penalties."""
        base_rtt = estimate_rtt_latency(0.0, health_score=100.0)
        assert base_rtt == 5.0

        rtt_1000km = estimate_rtt_latency(1000.0, health_score=100.0)
        assert rtt_1000km == 20.0  # 5.0 + 1000*0.015

        rtt_5000km = estimate_rtt_latency(5000.0, health_score=100.0)
        assert rtt_5000km == 80.0  # 5.0 + 5000*0.015

        # Penalty check on degraded PoP (health_score = 60.0 -> penalty = (100-60)*0.5 = 20.0ms)
        rtt_degraded = estimate_rtt_latency(1000.0, health_score=60.0)
        assert rtt_degraded == 40.0

    def test_geodns_routing_client_presets(self):
        """Test Geo-DNS steering across global client presets to nearest edge PoPs."""
        controller = EnterpriseEdgeCDNController()

        test_cases = [
            ("client_us_ny", "iad-01"),
            ("client_us_sf", "iad-01"),
            ("client_uk_lon", "fra-01"),
            ("client_de_ber", "fra-01"),
            ("client_jp_osa", "nrt-01"),
            ("client_in_del", "bom-01"),
            ("client_in_blr", "bom-01"),
            ("client_sg_jur", "sin-01"),
        ]

        for preset_key, expected_pop in test_cases:
            res = controller.route_client(preset_key)
            assert res["primary_pop"]["pop_id"] == expected_pop, f"Failed for {preset_key}: got {res['primary_pop']['pop_id']}, expected {expected_pop}"
            assert res["failover_rerouted"] is False
            assert res["primary_pop"]["status"] == "HEALTHY"

    def test_client_location_resolver_heuristics(self):
        """Test client query parsing: presets, coordinate strings, and IP subnets."""
        # 1. Preset
        name, lat, lon, ip = resolve_client_location("client_us_ny")
        assert "New York" in name
        assert lat == 40.7128

        # 2. Coordinates
        name, lat, lon, ip = resolve_client_location("12.9716, 77.5946")
        assert "Custom Geo" in name
        assert lat == 12.9716
        assert lon == 77.5946

        # 3. IP Subnet heuristic (e.g. 192.x -> North America, 198.x -> Europe)
        name_na, lat_na, _, _ = resolve_client_location("192.168.1.10")
        assert "North America" in name_na
        assert lat_na == 39.0438

        name_eu, lat_eu, _, _ = resolve_client_location("198.51.100.50")
        assert "Europe" in name_eu
        assert lat_eu == 50.1109

    def test_health_probe_state_transitions(self):
        """Test consecutive probe drop threshold and sub-300ms failover trigger."""
        controller = EnterpriseEdgeCDNController()
        pop_id = "iad-01"

        # Probe 1: Drop -> DEGRADED
        res1 = controller.record_health_probe(pop_id, success=False)
        assert res1["status"] == "DEGRADED"
        assert res1["consecutive_failures"] == 1
        assert res1["failover_event"] is None

        # Probe 2: Drop -> still DEGRADED
        res2 = controller.record_health_probe(pop_id, success=False)
        assert res2["status"] == "DEGRADED"
        assert res2["consecutive_failures"] == 2
        assert res2["failover_event"] is None

        # Probe 3: Drop -> OFFLINE & Failover Event Triggered
        res3 = controller.record_health_probe(pop_id, success=False)
        assert res3["status"] == "OFFLINE"
        assert res3["consecutive_failures"] == 3
        assert res3["failover_event"] is not None
        assert res3["failover_event"]["sla_met"] is True
        assert res3["failover_event"]["failover_latency_ms"] == 300

        # Recovery probe 1: Success -> Still OFFLINE / Recovering
        res4 = controller.record_health_probe(pop_id, success=True)
        assert res4["consecutive_successes"] == 1

        # Recovery probe 2: Success -> Restored to HEALTHY
        res5 = controller.record_health_probe(pop_id, success=True)
        assert res5["status"] == "HEALTHY"
        assert res5["consecutive_successes"] == 2
        assert res5["health_score"] == 100.0

    def test_sub_300ms_pop_failover_and_rerouting(self):
        """Simulate PoP outage and verify sub-300ms dynamic rerouting to secondary PoP."""
        controller = EnterpriseEdgeCDNController()

        # Initial routing for New York
        initial_route = controller.route_client("client_us_ny")
        assert initial_route["primary_pop"]["pop_id"] == "iad-01"
        assert initial_route["failover_rerouted"] is False

        # Simulate PoP failover on iad-01
        sim = controller.simulate_pop_failover("iad-01")
        assert sim["final_status"] == "OFFLINE"
        assert sim["failover_latency_ms"] <= 300
        assert sim["sub_300ms_sla_verified"] is True

        # Re-route New York client
        failover_route = controller.route_client("client_us_ny")
        assert failover_route["primary_pop"]["pop_id"] != "iad-01"
        assert failover_route["primary_pop"]["pop_id"] == "fra-01"  # Next closest healthy PoP across Atlantic
        assert failover_route["failover_rerouted"] is True
        assert failover_route["nearest_geographic_pop"] == "iad-01"

    def test_token_bucket_rate_limiting_allowed(self):
        """Verify normal requests within burst capacity are permitted (HTTP 200)."""
        limiter = TokenBucketRateLimiter(burst_capacity=10.0, refill_rate=2.0)
        client_ip = "192.0.2.1"

        now = 1000.0
        # Send 5 requests immediately
        for _ in range(5):
            allowed, meta = limiter.allow_request(client_ip, current_time=now, cost=1.0)
            assert allowed is True
            assert meta["http_status"] == 200
            assert meta["mitigated"] is False
            assert meta["action"] == "ALLOW"

        assert meta["remaining_tokens"] == 5.0

    def test_token_bucket_rate_limiting_exhaustion_and_refill(self):
        """Verify throttling (HTTP 429) upon burst exhaustion and recovery upon refill."""
        limiter = TokenBucketRateLimiter(burst_capacity=5.0, refill_rate=5.0)
        client_ip = "192.0.2.2"

        now = 1000.0
        # Exhaust 5 tokens
        for _ in range(5):
            allowed, _ = limiter.allow_request(client_ip, current_time=now, cost=1.0)
            assert allowed is True

        # 6th request should be dropped (HTTP 429)
        allowed, drop_meta = limiter.allow_request(client_ip, current_time=now, cost=1.0)
        assert allowed is False
        assert drop_meta["http_status"] == 429
        assert drop_meta["mitigated"] is True
        assert drop_meta["action"] == "DROP_429"

        # Advance clock by 1.0 second (refills 5.0 tokens)
        now += 1.0
        allowed, refilled_meta = limiter.allow_request(client_ip, current_time=now, cost=1.0)
        assert allowed is True
        assert refilled_meta["http_status"] == 200

    def test_ddos_volumetric_mitigation_simulation(self):
        """Simulate 500-request volumetric flood and verify origin shielding telemetry."""
        limiter = TokenBucketRateLimiter(burst_capacity=20.0, refill_rate=10.0)
        sim = limiter.simulate_ddos_attack("198.51.100.99", total_requests=500, time_window_seconds=1.0)

        assert sim["total_requests"] == 500
        assert sim["allowed_requests"] < 50
        assert sim["mitigated_requests"] >= 450
        assert sim["mitigation_percentage"] >= 90.0
        assert sim["origin_shield_absorbed_percentage"] == 100.0
        assert sim["origin_cluster_protection_status"] == "FULL_PROTECTION_CONFIRMED"

    def test_edge_waf_inspector(self):
        """Test Edge WAF filtering against SQLi, XSS, and directory traversal."""
        # Clean request
        passed, reason = EdgeWAFInspector.inspect_request("/api/v1/workloads/status")
        assert passed is True
        assert reason is None

        # SQL Injection
        passed, reason = EdgeWAFInspector.inspect_request("/api/v1/auth?user=admin' OR '1'='1")
        assert passed is False
        assert "SQL Injection" in reason

        # XSS
        passed, reason = EdgeWAFInspector.inspect_request("/profile", body='<script>alert("xss")</script>')
        assert passed is False
        assert "Cross-Site Scripting" in reason

        # Directory Traversal
        passed, reason = EdgeWAFInspector.inspect_request("/static/../../etc/passwd")
        assert passed is False
        assert "Directory Traversal" in reason

    def test_manifest_export_and_json_validity(self, tmp_path):
        """Verify topology manifest generation and valid JSON schema output."""
        controller = EnterpriseEdgeCDNController()
        target_file = tmp_path / "edge_pop_topology_manifest.json"
        controller.export_topology_manifest(target_file)

        assert target_file.exists()
        with open(target_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["metadata"]["organization"] == ORGANIZATION_NAME
        assert manifest["metadata"]["contact"] == PRIMARY_CONTACT
        assert manifest["network_routing"]["bgp_asn"] == ANYCAST_BGP_ASN
        assert manifest["network_routing"]["failover_sla_max_ms"] == 300
        assert len(manifest["edge_pops"]) == 5
        assert "iad-01" in manifest["edge_pops"]
        assert "bom-01" in manifest["edge_pops"]

    def test_markdown_guide_and_report_generation(self, tmp_path):
        """Verify operational handbook and technical report content integrity."""
        controller = EnterpriseEdgeCDNController()
        guide_file = tmp_path / "enterprise_edge_cdn_guide.md"
        report_file = tmp_path / "edge_cdn_architecture_report.md"

        controller.export_operations_guide(guide_file)
        controller.export_architecture_report(report_file)

        assert guide_file.exists()
        guide_text = guide_file.read_text(encoding="utf-8")
        assert "DevSuperSuite Enterprise Edge CDN PoP & Geo-DNS Operations Guide" in guide_text
        assert "Token Bucket Rate Limiter" in guide_text
        assert "Sub-300ms Failover SLA" in guide_text
        assert "iad-01" in guide_text

        assert report_file.exists()
        report_text = report_file.read_text(encoding="utf-8")
        assert "Global Edge CDN PoP Architecture & Geo-DNS Telemetry" in report_text
        assert "Multi-Region Geo-DNS Latency Matrix" in report_text
        assert "Token Bucket DDoS Rate Limiting Telemetry" in report_text
        assert "solutions@devsupersuite.com" in report_text

    def test_brand_anonymity_invariants(self):
        """
        Enforce institutional Brand Anonymity:
        Must NOT contain personal names or personal email providers.
        Must strictly represent DevSuperSuite / OmniKernel Labs.
        """
        forbidden_terms = ["github.com/", "gitlab.com/", "@gmail.com", "@yahoo.com", "@hotmail.com"]
        files_to_check = [
            SERVICES_DIR / "enterprise_edge_cdn_controller.py",
            SERVICES_DIR / "enterprise_edge_cdn_guide.md",
            REPORTS_DIR / "edge_cdn_architecture_report.md",
            EDGE_DIR / "edge_pop_topology_manifest.json"
        ]

        for filepath in files_to_check:
            assert filepath.exists(), f"Expected file {filepath} to exist."
            content = filepath.read_text(encoding="utf-8")

            # Check for forbidden terms
            for term in forbidden_terms:
                assert term not in content.lower(), f"Forbidden term '{term}' found in {filepath.name}"

            # Ensure valid institutional representation
            assert "DevSuperSuite" in content or "OmniKernel Labs" in content, (
                f"Missing institutional brand in {filepath.name}"
            )
            assert "solutions@devsupersuite.com" in content, (
                f"Missing official contact in {filepath.name}"
            )

    def test_cli_flags_execution(self):
        """Ensure all CLI interface flags execute cleanly with exit code 0."""
        python_exe = sys.executable
        controller_script = str(SERVICES_DIR / "enterprise_edge_cdn_controller.py")

        commands = [
            [python_exe, controller_script, "--summary"],
            [python_exe, controller_script, "--benchmark-geodns"],
            [python_exe, controller_script, "--route-client-ip", "client_sg_jur"],
            [python_exe, controller_script, "--simulate-pop-failover", "fra-01"],
            [python_exe, controller_script, "--simulate-ddos-mitigation"],
            [python_exe, controller_script, "--export-edge-bundle"]
        ]

        for cmd in commands:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            assert res.returncode == 0, f"Command failed: {' '.join(cmd)}\nStderr: {res.stderr}"
            assert len(res.stdout) > 0
