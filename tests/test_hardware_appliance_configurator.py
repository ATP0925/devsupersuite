#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Hardware Appliance Configurator Test Suite
Reference: DSS-HARDWARE-APPLIANCE-TESTS-2026-V1
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
HARDWARE_DIR = DEPLOYMENT_DIR / "hardware"

if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from enterprise_hardware_appliance_configurator import (
    PLATFORM_ARCHETYPES,
    APPLIANCE_TIERS,
    BTU_PER_WATT_HOUR,
    POWER_FACTOR_TITANIUM,
    ELECTRICITY_COST_PER_KWH,
    ORGANIZATION_NAME,
    PRIMARY_CONTACT,
    TECHNICAL_CONTACT,
    calculate_thermal_btu,
    calculate_electrical_amperage,
    calculate_annual_energy_cost,
    EnterpriseHardwareApplianceConfigurator
)


class TestEnterpriseHardwareApplianceConfigurator:
    """Enterprise verification suite for Hardware Appliance Sizing & BOM Configurator."""

    def test_platform_archetypes_initialization(self):
        """Validate Dell, HPE, and Supermicro server specifications and base BOM pricing."""
        expected_platforms = {"dell", "hpe", "supermicro"}
        assert set(PLATFORM_ARCHETYPES.keys()) == expected_platforms

        # Dell PowerEdge R660 / R760 checks
        dell = PLATFORM_ARCHETYPES["dell"]
        assert "Dell PowerEdge R660" in dell["model_1u"]
        assert "AMD EPYC 9654" in dell["processor_architecture"]
        assert dell["base_1u_price"] == 48500.0
        assert dell["base_2u_cluster_price"] == 94000.0
        assert "Opal 2.0 / FIPS 140-3" in dell["storage_drives"]
        assert "Titanium" in dell["psu"]

        # HPE ProLiant Gen11 checks
        hpe = PLATFORM_ARCHETYPES["hpe"]
        assert "HPE ProLiant DL360 Gen11" in hpe["model_1u"]
        assert "Intel Xeon Platinum 8480+" in hpe["processor_architecture"]
        assert hpe["base_1u_price"] == 49800.0

        # Supermicro Hyper SuperServer checks
        sm = PLATFORM_ARCHETYPES["supermicro"]
        assert "Supermicro Hyper SuperServer" in sm["model_1u"]
        assert sm["base_1u_price"] == 46900.0

    def test_appliance_tiers_specs(self):
        """Validate 1U Standalone, 2U Clustered Pair, and SCIF Grid specifications."""
        tier1 = APPLIANCE_TIERS["tier_1_standalone"]
        assert tier1["node_count"] == 1
        assert tier1["max_engineers"] == 500
        assert tier1["base_price"] == 48500.0
        assert tier1["usable_storage_tb"] == 7.68
        assert tier1["typical_power_watts"] == 450.0

        tier2 = APPLIANCE_TIERS["tier_2_ha_cluster"]
        assert tier2["node_count"] == 2
        assert tier2["max_engineers"] == 2500
        assert tier2["base_price"] == 94000.0
        assert tier2["usable_storage_tb"] == 15.36
        assert tier2["typical_power_watts"] == 900.0

        tier3 = APPLIANCE_TIERS["tier_3_scif_grid"]
        assert tier3["node_count"] == 4
        assert tier3["max_engineers"] == 10000
        assert tier3["base_price"] == 188000.0
        assert tier3["usable_storage_tb"] == 30.72
        assert tier3["typical_power_watts"] == 1800.0

    def test_tier_selection_by_engineer_count(self):
        """Test dynamic selection of hardware tiers based on engineer seat thresholds."""
        configurator = EnterpriseHardwareApplianceConfigurator()

        # Under 500 seats -> Tier 1
        t_100 = configurator.select_tier_for_engineers(100)
        assert t_100["tier_id"] == "tier_1_standalone"

        t_500 = configurator.select_tier_for_engineers(500)
        assert t_500["tier_id"] == "tier_1_standalone"

        # 501 to 2500 seats -> Tier 2
        t_501 = configurator.select_tier_for_engineers(501)
        assert t_501["tier_id"] == "tier_2_ha_cluster"

        t_2500 = configurator.select_tier_for_engineers(2500)
        assert t_2500["tier_id"] == "tier_2_ha_cluster"

        # Over 2500 seats -> Tier 3
        t_2501 = configurator.select_tier_for_engineers(2501)
        assert t_2501["tier_id"] == "tier_3_scif_grid"

        # Invalid seat counts
        with pytest.raises(ValueError):
            configurator.select_tier_for_engineers(0)
        with pytest.raises(ValueError):
            configurator.select_tier_for_engineers(-50)

    def test_thermal_btu_and_amperage_calculations(self):
        """Validate thermal heat dissipation (BTU/hr) and PDU current draw calculations."""
        # Thermal BTU
        btu_450 = calculate_thermal_btu(450.0)
        assert round(btu_450, 1) == 1535.5

        btu_900 = calculate_thermal_btu(900.0)
        assert round(btu_900, 1) == 3070.9

        # Amperage at 208V with PF 0.98
        amps_208 = calculate_electrical_amperage(450.0, 208.0)
        expected_amps_208 = round(450.0 / (208.0 * 0.98), 2)
        assert amps_208 == expected_amps_208

        # Amperage at 240V
        amps_240 = calculate_electrical_amperage(450.0, 240.0)
        expected_amps_240 = round(450.0 / (240.0 * 0.98), 2)
        assert amps_240 == expected_amps_240

        # Invalid voltage
        with pytest.raises(ValueError):
            calculate_electrical_amperage(450.0, 0.0)

    def test_annual_energy_cost_calculation(self):
        """Verify annual energy consumption (kWh) and operating expense projections."""
        energy = calculate_annual_energy_cost(450.0, rate_per_kwh=0.12)
        assert energy["continuous_watts"] == 450.0
        assert energy["annual_kwh"] == 3942.0  # (450 * 8760) / 1000
        assert energy["annual_electricity_cost_usd"] == 473.04  # 3942 * 0.12

    def test_itemized_bom_sum_consistency(self):
        """Ensure itemized BOM line items precisely sum up to total appliance BOM price."""
        configurator = EnterpriseHardwareApplianceConfigurator(platform_id="dell")

        # Tier 1 (1 node)
        bom_500 = configurator.generate_itemized_bom(500)
        items_1u = bom_500["itemized_bom_usd"]
        sum_items_1u = (
            items_1u["chassis_and_motherboards"] +
            items_1u["processors"] +
            items_1u["base_ecc_ddr5_memory"] +
            items_1u["base_nvme_sed_storage"] +
            items_1u["hardware_raid_controllers"] +
            items_1u["fips_140_3_hsm_accelerators"] +
            items_1u["smartnics_and_transceivers"] +
            items_1u["titanium_redundant_psus"] +
            items_1u["scif_airgap_disconnect_kit"] +
            items_1u["mission_critical_support_3yr"]
        )
        assert items_1u["total_appliance_bom_price"] == sum_items_1u
        assert items_1u["total_appliance_bom_price"] == 48500.0

        # Tier 2 (2 nodes)
        bom_2500 = configurator.generate_itemized_bom(2500)
        items_2u = bom_2500["itemized_bom_usd"]
        assert items_2u["total_appliance_bom_price"] == 97000.0  # 48500 * 2 nodes
        assert bom_2500["sizing_parameters"]["node_count"] == 2

    def test_bom_expansions_and_warranty_addons(self):
        """Validate dynamic price adjustments for NVMe storage, RAM, and warranty extensions."""
        configurator = EnterpriseHardwareApplianceConfigurator()

        # Add 3.84TB storage expansion + 128GB RAM expansion + 5-year warranty (2 extra years)
        bom_expanded = configurator.generate_itemized_bom(
            engineer_count=450,
            storage_expansion_tb=3.84,
            ram_expansion_gb=128,
            extended_warranty_years=5
        )
        items = bom_expanded["itemized_bom_usd"]

        assert items["storage_expansion_addon"] == 1850.0
        assert items["memory_expansion_addon"] == 950.0
        assert items["extended_warranty_addon"] == 4000.0  # 2 extra years * 2000
        assert items["total_appliance_bom_price"] == 48500.0 + 1850.0 + 950.0 + 4000.0

        specs = bom_expanded["hardware_specifications"]
        assert specs["memory_total_gb"] == 512 + 128
        assert specs["usable_storage_nvme_tb"] == 7.68 + 3.84

    def test_manifest_export_and_json_validity(self, tmp_path):
        """Verify machine-readable hardware manifest export and JSON schema validation."""
        configurator = EnterpriseHardwareApplianceConfigurator()
        target_file = tmp_path / "appliance_spec_manifest.json"
        configurator.export_appliance_spec_manifest(target_file)

        assert target_file.exists()
        with open(target_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["metadata"]["organization"] == ORGANIZATION_NAME
        assert manifest["metadata"]["contact"] == PRIMARY_CONTACT
        assert "dell" in manifest["platforms"]
        assert "hpe" in manifest["platforms"]
        assert "tier_1_standalone" in manifest["tiers"]
        assert "sovereign_1u_tier1" in manifest["reference_configurations"]

    def test_engineering_guide_generation(self, tmp_path):
        """Verify comprehensive hardware handbook and SCIF deployment guide export."""
        configurator = EnterpriseHardwareApplianceConfigurator()
        guide_file = tmp_path / "enterprise_hardware_appliance_guide.md"
        configurator.export_engineering_guide(guide_file)

        assert guide_file.exists()
        content = guide_file.read_text(encoding="utf-8")
        assert "DevSuperSuite Enterprise Hardware Appliance & SCIF Deployment Guide" in content
        assert "PowerEdge R660" in content
        assert "ProLiant DL360" in content
        assert "TEMPEST/2-95 Level I" in content
        assert "NIST SP 800-88 Rev 1" in content
        assert "solutions@devsupersuite.com" in content

    def test_brand_anonymity_invariants(self):
        """
        Enforce strict institutional brand anonymity:
        Must NOT contain personal names or unauthorized personal email providers.
        Must strictly represent DevSuperSuite Solutions Architecture / OmniKernel Labs.
        """
        forbidden_terms = ["github.com/", "gitlab.com/", "@gmail.com", "@yahoo.com", "@hotmail.com"]
        files_to_check = [
            SERVICES_DIR / "enterprise_hardware_appliance_configurator.py",
            HARDWARE_DIR / "appliance_spec_manifest.json",
            REPORTS_DIR / "enterprise_hardware_appliance_guide.md"
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
        configurator_script = str(SERVICES_DIR / "enterprise_hardware_appliance_configurator.py")

        commands = [
            [python_exe, configurator_script, "--summary"],
            [python_exe, configurator_script, "--size-appliance", "450"],
            [python_exe, configurator_script, "--size-appliance", "1800", "--select-platform", "hpe"],
            [python_exe, configurator_script, "--calculate-thermal-power"],
            [python_exe, configurator_script, "--export-hardware-bundle"]
        ]

        for cmd in commands:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            assert res.returncode == 0, f"Command failed: {' '.join(cmd)}\nStderr: {res.stderr}"
            assert len(res.stdout) > 0
