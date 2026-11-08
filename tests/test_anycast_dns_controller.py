#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Anycast DNS Controller Test Suite
Reference: DSS-ANYCAST-DNS-TESTS-2026-V1
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
DNS_DIR = DEPLOYMENT_DIR / "dns"

if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from enterprise_anycast_dns_controller import (
    GLOBAL_24_EDGE_POPS,
    ENTERPRISE_CLUSTERS,
    REGIONAL_TEST_CLIENTS,
    EARTH_RADIUS_KM,
    SUB_50MS_SLA_TARGET,
    ANYCAST_IPV4,
    ANYCAST_IPV6,
    ANYCAST_BGP_ASN,
    ORGANIZATION_NAME,
    PRIMARY_CONTACT,
    TECHNICAL_CONTACT,
    calculate_haversine,
    calculate_dns_latency,
    EnterpriseAnycastDNSController
)


class TestEnterpriseAnycastDNSController:
    """Enterprise verification suite for 24-PoP Anycast DNS & Geo-Failover Controller."""

    def test_anycast_24_pop_registry_initialization(self):
        """Validate that all 24 institutional edge PoPs are correctly registered across 5 clusters."""
        controller = EnterpriseAnycastDNSController()
        pops = controller.list_pops()
        assert len(pops) == 24

        expected_regions = {"US-East", "US-West", "EU-Central", "AP-South", "AP-East"}
        observed_regions = {p["region"] for p in pops}
        assert observed_regions == expected_regions

        # Regional PoP counts: 5 US-East, 4 US-West, 6 EU-Central, 4 AP-South, 5 AP-East
        assert len(controller.list_pops("US-East")) == 5
        assert len(controller.list_pops("US-West")) == 4
        assert len(controller.list_pops("EU-Central")) == 6
        assert len(controller.list_pops("AP-South")) == 4
        assert len(controller.list_pops("AP-East")) == 5

        for pop in pops:
            assert pop["bgp_status"] == "ADVERTISED"
            assert pop["bgp_local_pref"] == 100
            assert pop["health_score"] == 100.0
            assert -90.0 <= pop["latitude"] <= 90.0
            assert -180.0 <= pop["longitude"] <= 180.0
            assert "cluster_target" in pop
            assert "unicast_vip" in pop

    def test_haversine_distance_and_dns_latency(self):
        """Verify Great Circle math and DNS latency penalty formulas."""
        # Distance to self
        assert calculate_haversine(39.0438, -77.4874, 39.0438, -77.4874) == 0.0

        # Base DNS latency for 0 km
        base_lat = calculate_dns_latency(0.0, "ADVERTISED", 100.0)
        assert base_lat == 2.0

        # Transit latency for 1000 km (2.0 + 1000*0.015 = 17.0 ms)
        lat_1000 = calculate_dns_latency(1000.0, "ADVERTISED", 100.0)
        assert lat_1000 == 17.0

        # AS-path prepending penalty (+35 ms)
        lat_pre = calculate_dns_latency(1000.0, "PREPENDED_3X", 100.0)
        assert lat_pre == 52.0

        # BGP Route withdrawal penalty (+999 ms)
        lat_w = calculate_dns_latency(1000.0, "WITHDRAWN", 100.0)
        assert lat_w >= 1000.0

    def test_bgp_route_status_updates(self):
        """Test BGP route state transitions: ADVERTISED -> PREPENDED_3X -> WITHDRAWN."""
        controller = EnterpriseAnycastDNSController()
        pop_id = "iad-01"

        # Update to PREPENDED_3X
        ev1 = controller.update_bgp_route_status(pop_id, "PREPENDED_3X")
        pop = controller.get_pop(pop_id)
        assert pop["bgp_status"] == "PREPENDED_3X"
        assert pop["bgp_local_pref"] == 50
        assert ev1["new_status"] == "PREPENDED_3X"

        # Update to WITHDRAWN
        ev2 = controller.update_bgp_route_status(pop_id, "WITHDRAWN")
        assert pop["bgp_status"] == "WITHDRAWN"
        assert pop["bgp_local_pref"] == 0

        # Update back to ADVERTISED
        ev3 = controller.update_bgp_route_status(pop_id, "ADVERTISED")
        assert pop["bgp_status"] == "ADVERTISED"
        assert pop["bgp_local_pref"] == 100

        # Invalid status check
        with pytest.raises(ValueError):
            controller.update_bgp_route_status(pop_id, "UNKNOWN_STATUS")

    def test_health_probe_failure_and_automated_withdrawal(self):
        """Test health probe drop threshold triggering BGP route withdrawal."""
        controller = EnterpriseAnycastDNSController()
        pop_id = "fra-01"

        res = controller.simulate_health_probe_failure(pop_id, drop_count=3)
        assert res["withdrawal_triggered"] is True
        assert res["bgp_status"] == "WITHDRAWN"
        assert res["convergence_time_ms"] <= 150  # 3 * 50ms = 150ms

        pop = controller.get_pop(pop_id)
        assert pop["bgp_status"] == "WITHDRAWN"
        assert pop["health_score"] == 0.0

    def test_rfc7871_edns_client_subnet_geo_steering(self):
        """Test RFC 7871 EDNS-Client-Subnet steering across enterprise regions."""
        controller = EnterpriseAnycastDNSController()

        test_cases = [
            ("client_us_chicago", 41.8781, -87.6298, "ord-01", "US-East"),
            ("client_us_seattle", 47.6062, -122.3321, "sea-01", "US-West"),
            ("client_eu_london", 51.5074, -0.1278, "lhr-01", "EU-Central"),
            ("client_ap_pune", 18.5204, 73.8567, "bom-01", "AP-South"),
            ("client_ap_singapore", 1.3329, 103.7436, "sin-01", "AP-East")
        ]

        for name, lat, lon, exp_pop, exp_cluster in test_cases:
            res = controller.resolve_dns_query("api.devsupersuite.com", lat, lon)
            assert res["primary_pop"]["pop_id"] == exp_pop
            assert res["matched_cluster"]["cluster_id"] == f"cluster-{exp_cluster.lower()}"
            assert res["sub_50ms_sla_met"] is True

    def test_sub50ms_sla_regional_benchmarks(self):
        """Verify sub-50ms DNS resolution SLA across all 5 core enterprise regions."""
        controller = EnterpriseAnycastDNSController()
        bm = controller.benchmark_sub50ms_sla()

        assert bm["sla_pass_rate_percentage"] == 100.0
        assert bm["max_dns_latency_ms"] < SUB_50MS_SLA_TARGET
        assert bm["average_dns_latency_ms"] < 25.0
        assert bm["total_benchmarked_clients"] == len(REGIONAL_TEST_CLIENTS)

        for client_key, record in bm["regional_benchmarks"].items():
            assert record["sub_50ms_sla_met"] is True
            assert record["dns_latency_ms"] < 50.0

    def test_chaos_failover_scenarios(self):
        """Execute multi-region chaos failover scenarios and verify zero dropped queries."""
        controller = EnterpriseAnycastDNSController()
        sim = controller.simulate_chaos_failover_matrix()

        assert sim["total_scenarios_executed"] == 5
        assert sim["zero_dropped_queries_verified"] is True
        assert sim["average_failover_convergence_ms"] <= 300.0

        for sc in sim["scenarios"]:
            assert sc["queries_dropped"] == 0
            assert sc["query_success_rate_percentage"] == 100.0
            assert sc["post_failover_rtt_ms"] < 100.0  # Still sub-100ms even in failover

    def test_rfc1035_zone_file_generation_and_validity(self, tmp_path):
        """Verify RFC 1035 compliant DNS zone file generation."""
        controller = EnterpriseAnycastDNSController()
        target_zone = tmp_path / "zone_devsupersuite_enterprise.zone"
        controller.export_zone_file(target_zone)

        assert target_zone.exists()
        content = target_zone.read_text(encoding="utf-8")
        assert "$ORIGIN devsupersuite.com." in content
        assert "$TTL 300" in content
        assert "SOA" in content
        assert "2026110801" in content  # Serial number
        assert ANYCAST_IPV4 in content
        assert ANYCAST_IPV6 in content
        assert "cluster-us-east" in content
        assert "cluster-eu-central" in content
        assert "cluster-ap-south" in content
        assert "cluster-ap-east" in content

    def test_manifests_json_validity(self, tmp_path):
        """Verify topology and simulation JSON manifests formatting and schema."""
        controller = EnterpriseAnycastDNSController()
        topo_path = tmp_path / "anycast_dns_topology_manifest.json"
        sim_path = tmp_path / "geo_failover_simulation_manifest.json"

        controller.export_topology_manifest(topo_path)
        controller.export_failover_simulation_manifest(sim_path)

        assert topo_path.exists()
        with open(topo_path, "r", encoding="utf-8") as f:
            topo = json.load(f)
        assert topo["metadata"]["organization"] == ORGANIZATION_NAME
        assert topo["metadata"]["contact"] == PRIMARY_CONTACT
        assert topo["anycast_network"]["bgp_asn"] == ANYCAST_BGP_ASN
        assert topo["anycast_network"]["total_edge_pops"] == 24
        assert len(topo["edge_pops"]) == 24

        assert sim_path.exists()
        with open(sim_path, "r", encoding="utf-8") as f:
            sim = json.load(f)
        assert sim["zero_dropped_queries_verified"] is True
        assert len(sim["scenarios"]) == 5

    def test_architecture_report_generation(self, tmp_path):
        """Verify technical whitepaper and latency benchmark report generation."""
        controller = EnterpriseAnycastDNSController()
        report_file = tmp_path / "anycast_dns_resilience_report.md"
        controller.export_architecture_report(report_file)

        assert report_file.exists()
        text = report_file.read_text(encoding="utf-8")
        assert "Global Anycast DNS Routing & Geo-Failover Resilience" in text
        assert "Sub-50ms Regional SLA Empirical Benchmark Matrix" in text
        assert "Automated Health Checks & BGP Route Withdrawal" in text
        assert "solutions@devsupersuite.com" in text

    def test_brand_anonymity_invariants(self):
        """
        Enforce strict 100% brand anonymity:
        Must NOT contain personal names or unauthorized personal email domains.
        Must strictly represent DevSuperSuite Solutions Architecture / OmniKernel Labs.
        """
        forbidden_terms = ["github.com/", "gitlab.com/", "@gmail.com", "@yahoo.com", "@hotmail.com"]
        files_to_check = [
            SERVICES_DIR / "enterprise_anycast_dns_controller.py",
            DNS_DIR / "zone_devsupersuite_enterprise.zone",
            DNS_DIR / "anycast_dns_topology_manifest.json",
            DNS_DIR / "geo_failover_simulation_manifest.json",
            REPORTS_DIR / "anycast_dns_resilience_report.md"
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
        """Ensure all CLI interface flags execute cleanly with return code 0."""
        python_exe = sys.executable
        controller_script = str(SERVICES_DIR / "enterprise_anycast_dns_controller.py")

        commands = [
            [python_exe, controller_script, "--summary"],
            [python_exe, controller_script, "--benchmark-sub50ms"],
            [python_exe, controller_script, "--resolve-dns", "35.6762,139.6503"],
            [python_exe, controller_script, "--simulate-bgp-withdrawal", "ord-01"],
            [python_exe, controller_script, "--simulate-chaos-matrix"],
            [python_exe, controller_script, "--export-dns-bundle"]
        ]

        for cmd in commands:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            assert res.returncode == 0, f"Command failed: {' '.join(cmd)}\nStderr: {res.stderr}"
            assert len(res.stdout) > 0
