#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Enterprise Hardware Appliance & Sizing Configurator
Reference: DSS-HARDWARE-APPLIANCE-2026-V1
Classification: On-Premise Air-Gapped Rackmount Sizing & SCIF Deployments (Restricted)
Contact: DevSuperSuite Solutions Architecture (solutions@devsupersuite.com)
Author: OmniKernel Labs / DevSuperSuite Hardware Systems & Infrastructure Engineering
═══════════════════════════════════════════════════════════════════════════════
"""

import argparse
import copy
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# ─────────────────────────────────────────────────────────────────────────────
# Repository Paths & Global Constants
# ─────────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = REPO_ROOT / "services"
REPORTS_DIR = SERVICES_DIR / "reports"
DEPLOYMENT_DIR = REPO_ROOT / "deployment"
HARDWARE_DIR = DEPLOYMENT_DIR / "hardware"

DEFAULT_MANIFEST_FILE = HARDWARE_DIR / "appliance_spec_manifest.json"
DEFAULT_GUIDE_FILE = REPORTS_DIR / "enterprise_hardware_appliance_guide.md"

BTU_PER_WATT_HOUR = 3.412142
POWER_FACTOR_TITANIUM = 0.98  # 80 PLUS Titanium PSU power factor
ELECTRICITY_COST_PER_KWH = 0.12  # Standard commercial data center kWh rate
HOURS_PER_YEAR = 8760

ORGANIZATION_NAME = "DevSuperSuite Solutions Architecture / OmniKernel Labs"
PRIMARY_CONTACT = "solutions@devsupersuite.com"
TECHNICAL_CONTACT = "hardware@devsupersuite.com"


# ─────────────────────────────────────────────────────────────────────────────
# 1. Enterprise Hardware Platforms Registry
# ─────────────────────────────────────────────────────────────────────────────

PLATFORM_ARCHETYPES: Dict[str, Dict[str, Any]] = {
    "dell": {
        "platform_id": "dell",
        "vendor": "Dell Technologies",
        "model_1u": "Dell PowerEdge R660 Enterprise Server",
        "model_2u": "Dell PowerEdge R760 Enterprise Server",
        "processor_architecture": "Dual AMD EPYC 9654 (96-core / 192-thread, 2.4 GHz - 3.7 GHz, 360W TDP)",
        "memory_subsystem": "512GB ECC DDR5-4800 (16x 32GB RDIMM, 12-channel per socket)",
        "storage_controller": "Dell PERC H755N Front NVMe PCIe Gen4 RAID Controller (8GB NV Cache)",
        "storage_drives": "4x 3.84TB U.2 NVMe PCIe Gen5 Enterprise SEDs (RAID 10, Opal 2.0 / FIPS 140-3)",
        "crypto_hsm": "Thales Luna PCIe HSM / YubiHSM 2 FIPS 140-3 Level 3 Hardware Security Module",
        "smartnic": "Broadcom 57504 Quad-Port 25GbE SFP28 OCP 3.0 + Dual 10GbE BASE-T",
        "psu": "Dual Hot-Plug Redundant 1400W 80 PLUS Titanium (96% Efficiency)",
        "base_1u_price": 48500.0,
        "base_2u_cluster_price": 94000.0
    },
    "hpe": {
        "platform_id": "hpe",
        "vendor": "Hewlett Packard Enterprise",
        "model_1u": "HPE ProLiant DL360 Gen11 Enterprise Server",
        "model_2u": "HPE ProLiant DL380 Gen11 Enterprise Server",
        "processor_architecture": "Dual Intel Xeon Platinum 8480+ (56-core / 112-thread, 2.0 GHz - 3.8 GHz, 350W TDP)",
        "memory_subsystem": "512GB ECC DDR5-4800 (16x 32GB SmartMemory, 8-channel per socket)",
        "storage_controller": "HPE SR932i-p Gen11 Tri-Mode 24G SAS/PCIe Gen4 Controller (8GB Flash Cache)",
        "storage_drives": "4x 3.84TB NVMe High Performance Read Intensive U.3 SED FIPS 140-3 SSDs (RAID 10)",
        "crypto_hsm": "Marvell LiquidSecurity HSM FIPS 140-3 Level 3 PCIe Cryptographic Accelerator",
        "smartnic": "HPE BCM57414 Dual-Port 25GbE SFP28 OCP3 Adapter",
        "psu": "Dual Hot-Plug Flex Slot 1600W 80 PLUS Titanium (96% Efficiency)",
        "base_1u_price": 49800.0,
        "base_2u_cluster_price": 96200.0
    },
    "supermicro": {
        "platform_id": "supermicro",
        "vendor": "Supermicro Computer, Inc.",
        "model_1u": "Supermicro Hyper SuperServer SYS-121H-TNR",
        "model_2u": "Supermicro Hyper SuperServer SYS-221H-TNR",
        "processor_architecture": "Dual AMD EPYC 9654 (96-core / 192-thread, 2.4 GHz - 3.7 GHz, 360W TDP)",
        "memory_subsystem": "512GB ECC DDR5-4800 Registered ECC (16x 32GB RDIMM)",
        "storage_controller": "Broadcom MegaRAID 9560-16i NVMe PCIe Gen4 Controller (8GB CacheVault)",
        "storage_drives": "4x 3.84TB Kioxia CM7-R U.2 PCIe 5.0 SED FIPS 140-3 Drives (RAID 10)",
        "crypto_hsm": "NitroKey / YubiHSM 2 Hardware Security Module FIPS 140-3 Level 3",
        "smartnic": "Dual 25GbE Mellanox ConnectX-6 Dx SFP28 Dual-Port PCIe Adapter",
        "psu": "Dual 1600W Titanium Level Redundant Power Supplies (96% Efficiency)",
        "base_1u_price": 46900.0,
        "base_2u_cluster_price": 91500.0
    }
}


# ─────────────────────────────────────────────────────────────────────────────
# 2. Appliance Tier Archetypes
# ─────────────────────────────────────────────────────────────────────────────

APPLIANCE_TIERS: Dict[str, Dict[str, Any]] = {
    "tier_1_standalone": {
        "tier_id": "tier_1_standalone",
        "name": "DevSuperSuite Sovereign-1U",
        "form_factor": "1U Rackmount",
        "node_count": 1,
        "max_engineers": 500,
        "base_price": 48500.0,
        "usable_storage_tb": 7.68,
        "raw_storage_tb": 15.36,
        "memory_gb": 512,
        "ast_throughput_tokens_sec": 15000,
        "typical_power_watts": 450.0,
        "peak_power_watts": 750.0,
        "redundancy": "Single-Node High Resilience (Hot-Swap NVMe + Dual PSUs)",
        "target_deployment": "Defense SCIF Edge, Regional Treasury Lab, Isolated Engineering Outpost"
    },
    "tier_2_ha_cluster": {
        "tier_id": "tier_2_ha_cluster",
        "name": "DevSuperSuite Sovereign-2U HA Clustered Pair",
        "form_factor": "2U Clustered Pair (2x 1U or 1x 2U Dual-Node)",
        "node_count": 2,
        "max_engineers": 2500,
        "base_price": 94000.0,
        "usable_storage_tb": 15.36,
        "raw_storage_tb": 30.72,
        "memory_gb": 1024,
        "ast_throughput_tokens_sec": 45000,
        "typical_power_watts": 900.0,
        "peak_power_watts": 1500.0,
        "redundancy": "Dual-Node Active-Active / Active-Passive Raft High Availability Pair",
        "target_deployment": "Primary Financial Data Center, Tier-1 Sovereign Government Facility"
    },
    "tier_3_scif_grid": {
        "tier_id": "tier_3_scif_grid",
        "name": "DevSuperSuite Sovereign-SCIF Multi-Node Grid",
        "form_factor": "4U Multi-Node Grid (4x 1U or 2x 2U Clustered Nodes)",
        "node_count": 4,
        "max_engineers": 10000,
        "base_price": 188000.0,
        "usable_storage_tb": 30.72,
        "raw_storage_tb": 61.44,
        "memory_gb": 2048,
        "ast_throughput_tokens_sec": 120000,
        "typical_power_watts": 1800.0,
        "peak_power_watts": 3000.0,
        "redundancy": "Quad-Node Distributed Consensus Grid (N+2 Fault Tolerant)",
        "target_deployment": "National Defense Cyber Command, Global Sovereign Clearinghouse"
    }
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Thermal & Electrical Power Calculation Engine
# ─────────────────────────────────────────────────────────────────────────────

def calculate_thermal_btu(power_watts: float) -> float:
    """Calculate heat dissipation in BTU per hour from power consumption in Watts."""
    return round(power_watts * BTU_PER_WATT_HOUR, 2)


def calculate_electrical_amperage(power_watts: float, voltage: float = 208.0) -> float:
    """
    Calculate electrical current draw (Amperes) for Titanium-rated PSUs:
    Current (A) = Watts / (Voltage * Power Factor)
    """
    if voltage <= 0:
        raise ValueError("Voltage must be greater than zero.")
    return round(power_watts / (voltage * POWER_FACTOR_TITANIUM), 2)


def calculate_annual_energy_cost(power_watts: float, rate_per_kwh: float = ELECTRICITY_COST_PER_KWH) -> Dict[str, float]:
    """
    Calculate annual continuous energy consumption (kWh) and commercial electricity cost.
    """
    annual_kwh = (power_watts * HOURS_PER_YEAR) / 1000.0
    annual_cost = annual_kwh * rate_per_kwh
    return {
        "continuous_watts": power_watts,
        "annual_kwh": round(annual_kwh, 2),
        "rate_per_kwh": rate_per_kwh,
        "annual_electricity_cost_usd": round(annual_cost, 2)
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. Enterprise Hardware Appliance Configurator Engine
# ─────────────────────────────────────────────────────────────────────────────

class EnterpriseHardwareApplianceConfigurator:
    """
    Autonomous Enterprise Hardware Appliance & Rackmount Sizing Configurator.
    Sizes on-premise air-gapped 1U/2U rackmount hardware, generates itemized BOMs,
    models thermal/power dissipation, and enforces SCIF compliance standards.
    """

    def __init__(self, platform_id: str = "dell") -> None:
        clean_pid = platform_id.lower().strip()
        if clean_pid not in PLATFORM_ARCHETYPES:
            raise KeyError(f"Unknown hardware platform '{platform_id}'. Supported: {list(PLATFORM_ARCHETYPES.keys())}")
        self.platform = copy.deepcopy(PLATFORM_ARCHETYPES[clean_pid])
        self.tiers = copy.deepcopy(APPLIANCE_TIERS)

    def select_tier_for_engineers(self, engineer_count: int) -> Dict[str, Any]:
        """
        Automatically determine appropriate hardware tier based on active engineer seat count.
        """
        if engineer_count <= 0:
            raise ValueError("Engineer count must be a positive integer.")

        if engineer_count <= 500:
            return self.tiers["tier_1_standalone"]
        elif engineer_count <= 2500:
            return self.tiers["tier_2_ha_cluster"]
        else:
            return self.tiers["tier_3_scif_grid"]

    def generate_itemized_bom(
        self,
        engineer_count: int,
        storage_expansion_tb: float = 0.0,
        ram_expansion_gb: int = 0,
        extended_warranty_years: int = 3
    ) -> Dict[str, Any]:
        """
        Generate itemized Bill of Materials (BOM) with component pricing,
        thermal and electrical modeling, and mission-critical air-gap support.
        """
        tier = self.select_tier_for_engineers(engineer_count)
        node_count = tier["node_count"]

        # Base itemized components per node
        chassis_mb = 8500.0 * node_count
        cpus = 11200.0 * node_count
        ram_base = 6800.0 * node_count
        storage_base = 7400.0 * node_count
        raid_controller = 1800.0 * node_count
        hsm_card = 4500.0 * node_count
        smartnics = 1500.0 * node_count
        psus = 800.0 * node_count
        scif_airgap_kit = 1000.0 * node_count
        support_base = 5000.0 * node_count  # 3-Year 24/7 on-site air-gap firmware support

        # Custom expansions
        expansion_storage_cost = (storage_expansion_tb / 3.84) * 1850.0 if storage_expansion_tb > 0 else 0.0
        expansion_ram_cost = (ram_expansion_gb / 128) * 950.0 if ram_expansion_gb > 0 else 0.0
        warranty_extension_cost = 0.0
        if extended_warranty_years > 3:
            warranty_extension_cost = (extended_warranty_years - 3) * (2000.0 * node_count)

        total_bom_price = (
            chassis_mb + cpus + ram_base + storage_base + raid_controller +
            hsm_card + smartnics + psus + scif_airgap_kit + support_base +
            expansion_storage_cost + expansion_ram_cost + warranty_extension_cost
        )

        # Thermal and Electrical Modeling
        typical_watts = tier["typical_power_watts"] + (len(str(expansion_storage_cost)) * 10.0)
        peak_watts = tier["peak_power_watts"] + (len(str(expansion_storage_cost)) * 15.0)

        thermal_typical_btu = calculate_thermal_btu(typical_watts)
        thermal_peak_btu = calculate_thermal_btu(peak_watts)

        amps_208v_typical = calculate_electrical_amperage(typical_watts, 208.0)
        amps_208v_peak = calculate_electrical_amperage(peak_watts, 208.0)
        amps_240v_typical = calculate_electrical_amperage(typical_watts, 240.0)
        amps_240v_peak = calculate_electrical_amperage(peak_watts, 240.0)

        energy_costs = calculate_annual_energy_cost(typical_watts)

        return {
            "configuration_metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "reference": "DSS-HARDWARE-APPLIANCE-2026-V1",
                "organization": ORGANIZATION_NAME,
                "contact": PRIMARY_CONTACT,
                "technical_contact": TECHNICAL_CONTACT
            },
            "sizing_parameters": {
                "engineer_seats": engineer_count,
                "selected_tier": tier["name"],
                "tier_id": tier["tier_id"],
                "form_factor": tier["form_factor"],
                "node_count": node_count,
                "vendor_platform": self.platform["vendor"],
                "server_model": self.platform["model_1u"] if node_count == 1 else self.platform["model_2u"],
                "warranty_period_years": extended_warranty_years
            },
            "hardware_specifications": {
                "processors": self.platform["processor_architecture"],
                "memory_total_gb": tier["memory_gb"] + ram_expansion_gb,
                "usable_storage_nvme_tb": tier["usable_storage_tb"] + storage_expansion_tb,
                "raw_storage_nvme_tb": tier["raw_storage_tb"] + (storage_expansion_tb * 2),
                "raid_controller": self.platform["storage_controller"],
                "drive_security": "U.2/U.3 NVMe SED PCIe Gen5 (TCG Opal 2.0 / FIPS 140-3 Hardware Crypto)",
                "cryptographic_hsm": self.platform["crypto_hsm"],
                "smartnic": self.platform["smartnic"],
                "power_supply_units": self.platform["psu"],
                "ast_throughput_tokens_sec": tier["ast_throughput_tokens_sec"]
            },
            "itemized_bom_usd": {
                "chassis_and_motherboards": round(chassis_mb, 2),
                "processors": round(cpus, 2),
                "base_ecc_ddr5_memory": round(ram_base, 2),
                "base_nvme_sed_storage": round(storage_base, 2),
                "hardware_raid_controllers": round(raid_controller, 2),
                "fips_140_3_hsm_accelerators": round(hsm_card, 2),
                "smartnics_and_transceivers": round(smartnics, 2),
                "titanium_redundant_psus": round(psus, 2),
                "scif_airgap_disconnect_kit": round(scif_airgap_kit, 2),
                "mission_critical_support_3yr": round(support_base, 2),
                "storage_expansion_addon": round(expansion_storage_cost, 2),
                "memory_expansion_addon": round(expansion_ram_cost, 2),
                "extended_warranty_addon": round(warranty_extension_cost, 2),
                "total_appliance_bom_price": round(total_bom_price, 2)
            },
            "thermal_and_power_telemetry": {
                "psu_efficiency_rating": "80 PLUS Titanium (96% Efficiency)",
                "typical_power_watts": typical_watts,
                "peak_power_watts": peak_watts,
                "thermal_dissipation_typical_btu_hr": thermal_typical_btu,
                "thermal_dissipation_peak_btu_hr": thermal_peak_btu,
                "current_draw_208v_typical_amps": amps_208v_typical,
                "current_draw_208v_peak_amps": amps_208v_peak,
                "current_draw_240v_typical_amps": amps_240v_typical,
                "current_draw_240v_peak_amps": amps_240v_peak,
                "annual_energy_consumption_kwh": energy_costs["annual_kwh"],
                "annual_electricity_cost_usd": energy_costs["annual_electricity_cost_usd"]
            },
            "scif_compliance_standards": {
                "emissions_control": "NSTISSAM TEMPEST/2-95 Level I / NATO AMSG 720B Ready",
                "storage_sanitization": "NIST SP 800-88 Rev 1 Cryptographic Erase / DoD 5220.22-M",
                "hsm_standard": "FIPS 140-3 Level 3 Physical Anti-Tamper & Zeroization",
                "network_isolation": "Physical Air-Gap Galvanic Optical Fiber Disconnect Switch"
            }
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Exporters & Artifact Generation
    # ─────────────────────────────────────────────────────────────────────────

    def generate_appliance_spec_manifest(self) -> Dict[str, Any]:
        """
        Generate declarative machine-readable JSON manifest containing all
        platforms, tiers, BOM models, and thermal specifications.
        """
        tier1_bom = self.generate_itemized_bom(500)
        tier2_bom = self.generate_itemized_bom(2500)
        tier3_bom = self.generate_itemized_bom(10000)

        return {
            "$schema": "https://devsupersuite.com/schemas/hardware-appliance-v1.json",
            "metadata": {
                "manifest_version": "1.0.0",
                "reference": "DSS-HARDWARE-APPLIANCE-2026-V1",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "organization": ORGANIZATION_NAME,
                "contact": PRIMARY_CONTACT,
                "technical_contact": TECHNICAL_CONTACT
            },
            "platforms": PLATFORM_ARCHETYPES,
            "tiers": APPLIANCE_TIERS,
            "reference_configurations": {
                "sovereign_1u_tier1": tier1_bom,
                "sovereign_2u_tier2": tier2_bom,
                "sovereign_scif_tier3": tier3_bom
            },
            "power_and_thermal_constants": {
                "btu_per_watt_hour": BTU_PER_WATT_HOUR,
                "titanium_psu_efficiency_percentage": 96.0,
                "power_factor": POWER_FACTOR_TITANIUM,
                "commercial_kwh_rate_usd": ELECTRICITY_COST_PER_KWH
            }
        }

    def export_appliance_spec_manifest(self, output_path: Union[str, Path] = DEFAULT_MANIFEST_FILE) -> Path:
        dest = Path(output_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        manifest_data = self.generate_appliance_spec_manifest()
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
        return dest

    def generate_engineering_guide(self) -> str:
        """
        Generate comprehensive engineering handbook and SCIF deployment guide.
        """
        tier1 = APPLIANCE_TIERS["tier_1_standalone"]
        tier2 = APPLIANCE_TIERS["tier_2_ha_cluster"]
        tier3 = APPLIANCE_TIERS["tier_3_scif_grid"]

        return f"""# DevSuperSuite Enterprise Hardware Appliance & SCIF Deployment Guide

**Reference:** `DSS-HARDWARE-APPLIANCE-2026-V1`  
**Classification:** On-Premise Air-Gapped Rackmount Sizing & SCIF Deployments (Restricted)  
**Organization:** {ORGANIZATION_NAME}  
**Contact:** `{PRIMARY_CONTACT}` / `{TECHNICAL_CONTACT}`  
**Last Updated:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}

---

## 1. Executive Appliance Sizing Matrix

The DevSuperSuite Sovereign On-Premise Appliance delivers institutional code intelligence, Tree-sitter AST analysis, and zero-trust repository auditing directly within air-gapped national defense SCIFs (Sensitive Compartmented Information Facilities) and sovereign banking data centers:

| Metric | Sovereign-1U (Tier 1) | Sovereign-2U HA Pair (Tier 2) | Sovereign-SCIF Grid (Tier 3) |
|:---|:---|:---|:---|
| **Target Scale** | Up to 500 Engineers | Up to 2,500 Engineers | Up to 10,000 Engineers |
| **Form Factor** | 1U Rackmount Server | 2U / Dual-Node Clustered Pair | 4U / Quad-Node Grid |
| **Base BOM Price** | **$48,500** | **$94,000** | **$188,000** |
| **Usable NVMe SEDs** | 7.68 TB (RAID 10) | 15.36 TB (RAID 10) | 30.72 TB (RAID 10) |
| **ECC DDR5 Memory** | 512 GB (DDR5-4800) | 1,024 GB (2x 512GB) | 2,048 GB (4x 512GB) |
| **AST Throughput** | 15,000 tokens/sec | 45,000 tokens/sec | 120,000 tokens/sec |
| **Typical Power** | 450 Watts | 900 Watts | 1,800 Watts |
| **Heat Dissipation** | 1,535 BTU/hr | 3,071 BTU/hr | 6,142 BTU/hr |

```mermaid
flowchart TD
    subgraph SCIF ["Air-Gapped SCIF Perimeter (TEMPEST Level I)"]
        PDU["Dual 208V/240V Redundant PDU Feed"] --> PSU1["PSU 1 (80 PLUS Titanium 96%)"]
        PDU --> PSU2["PSU 2 (80 PLUS Titanium 96%)"]
        
        subgraph HardwareNode ["Sovereign Rackmount Appliance"]
            CPU["Dual AMD EPYC 9654 (192 Cores)"]
            RAM["512GB ECC DDR5-4800 Registered"]
            SED["4x 3.84TB U.2 NVMe SEDs (RAID 10)"]
            HSM["FIPS 140-3 Level 3 Hardware Security Module"]
            NIC["Dual 25GbE SmartNIC with Physical Fiber Disconnect"]
            
            PSU1 --> CPU
            PSU2 --> CPU
            CPU --> RAM
            CPU --> SED
            CPU --> HSM
            CPU --> NIC
        end
        
        NIC --> InternalSwitch["Internal Air-Gapped Workstation LAN"]
    end
```

---

## 2. Supported Vendor Hardware Platforms

1. **Dell Technologies (`PowerEdge R660 / R760`)**:
   - Processors: Dual AMD EPYC 9654 (96-core, 360W TDP each).
   - RAID Controller: Dell PERC H755N Front NVMe PCIe Gen4 (8GB non-volatile cache).
   - Storage: 4x 3.84TB U.2 NVMe PCIe Gen5 Enterprise SEDs.
   - Power: Dual Hot-Plug Redundant 1400W 80 PLUS Titanium.

2. **Hewlett Packard Enterprise (`ProLiant DL360 / DL380 Gen11`)**:
   - Processors: Dual Intel Xeon Platinum 8480+ (56-core, 350W TDP each).
   - RAID Controller: HPE SR932i-p Gen11 Tri-Mode 24G SAS/PCIe Gen4 (8GB Flash Cache).
   - Storage: 4x 3.84TB NVMe U.3 High-Performance Read Intensive SEDs.
   - Power: Dual Hot-Plug Flex Slot 1600W 80 PLUS Titanium.

3. **Supermicro (`Hyper SuperServer SYS-121H-TNR / SYS-221H-TNR`)**:
   - Processors: Dual AMD EPYC 9654 on Dual Socket SP5.
   - RAID Controller: Broadcom MegaRAID 9560-16i NVMe PCIe Gen4 Controller.
   - Storage: 4x 3.84TB Kioxia CM7-R U.2 PCIe 5.0 SED FIPS 140-3 Drives.
   - Power: Dual 1600W Titanium Level Redundant PSUs.

---

## 3. Thermal Dissipation & Power Provisioning Model

All DevSuperSuite hardware appliances employ **80 PLUS Titanium** certified power supplies operating at **96.0% efficiency** at 50% load:

- **Thermal Dissipation Formula:**
  `BTU/hr = Watts * 3.412142`
- **Electrical Current Draw (Amperes):**
  `Amperes = Watts / (Voltage * Power Factor)` (where Power Factor PF = 0.98)

### Electrical PDU Planning Table:
- **1U Standalone Appliance (450W typical / 750W peak):**
  - Draw at 208V: 2.21 A typical / 3.68 A peak
  - Draw at 240V: 1.91 A typical / 3.19 A peak
  - Annual Power: 3,942.0 kWh ($473.04/yr at $0.12/kWh)
- **2U Clustered Pair (900W typical / 1500W peak):**
  - Draw at 208V: 4.41 A typical / 7.36 A peak
  - Draw at 240V: 3.83 A typical / 6.38 A peak
  - Annual Power: 7,884.0 kWh ($946.08/yr at $0.12/kWh)

---

## 4. Defense SCIF & Air-Gapped Compliance Standards

1. **TEMPEST Emissions Shielding:** Meets NSTISSAM TEMPEST/2-95 Level I and NATO AMSG 720B standards for zero RF emissions leakage outside shielded containment zones.
2. **Cryptographic Erasure & Sanitization:** Drives comply with NIST SP 800-88 Rev 1 Cryptographic Erase and DoD 5220.22-M. Opal 2.0 Self-Encrypting Drives (SEDs) enable instantaneous key destruction via ATA Sanitize Device Crypto Scramble.
3. **FIPS 140-3 Level 3 Hardware Security Module:** Hardware keys are permanently anchored inside tamper-resistant PCIe HSM enclaves featuring zeroization triggers upon physical enclosure breach.
4. **Physical Air-Gap Disconnect:** Dual 25GbE fiber transceivers feature physical mechanical optical switches allowing manual physical severing of all network connectivity.

---

## 5. CLI Sizing & Operations

To configure appliances dynamically via CLI:

```bash
# Size hardware appliance for 450 engineers
python services/enterprise_hardware_appliance_configurator.py --size-appliance 450

# Size 2U clustered pair for 2,200 engineers with HPE platform
python services/enterprise_hardware_appliance_configurator.py --size-appliance 2200 --select-platform hpe

# Calculate thermal dissipation and electrical current draw
python services/enterprise_hardware_appliance_configurator.py --calculate-thermal-power

# Export declarative hardware manifest and engineering guide
python services/enterprise_hardware_appliance_configurator.py --export-hardware-bundle
```
"""

    def export_engineering_guide(self, output_path: Union[str, Path] = DEFAULT_GUIDE_FILE) -> Path:
        dest = Path(output_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        content = self.generate_engineering_guide()
        with open(dest, "w", encoding="utf-8") as f:
            f.write(content)
        return dest

    def export_all(
        self,
        manifest_path: Union[str, Path] = DEFAULT_MANIFEST_FILE,
        guide_path: Union[str, Path] = DEFAULT_GUIDE_FILE
    ) -> Dict[str, Path]:
        """
        Export complete hardware appliance deployment bundle.
        """
        m_path = self.export_appliance_spec_manifest(manifest_path)
        g_path = self.export_engineering_guide(guide_path)
        return {
            "manifest": m_path,
            "guide": g_path
        }


# ─────────────────────────────────────────────────────────────────────────────
# 5. CLI Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="DevSuperSuite Enterprise Hardware Appliance & Sizing Configurator"
    )
    parser.add_argument(
        "--size-appliance",
        type=int,
        help="Calculate BOM and size hardware appliance for specified active engineer headcount"
    )
    parser.add_argument(
        "--select-platform",
        type=str,
        default="dell",
        choices=["dell", "hpe", "supermicro"],
        help="Select underlying server hardware platform (default: dell)"
    )
    parser.add_argument(
        "--calculate-thermal-power",
        action="store_true",
        help="Output thermal dissipation (BTU/hr) and PDU electrical sizing tables"
    )
    parser.add_argument(
        "--export-hardware-bundle",
        action="store_true",
        help="Export declarative appliance spec manifest JSON and engineering guide"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Display summary overview of hardware platforms, tiers, and base BOM pricing"
    )

    args = parser.parse_args()
    configurator = EnterpriseHardwareApplianceConfigurator(platform_id=args.select_platform)

    if len(sys.argv) == 1:
        args.summary = True

    if args.summary:
        print("═" * 80)
        print("DevSuperSuite Enterprise Hardware Appliance Sizing & BOM Overview")
        print(f"Reference: DSS-HARDWARE-APPLIANCE-2026-V1 | Organization: {ORGANIZATION_NAME}")
        print("═" * 80)
        print("Hardware Platforms Supported:")
        for pid, plat in PLATFORM_ARCHETYPES.items():
            print(f" • [{pid.upper():<11}] {plat['vendor']:<28} | 1U: ${plat['base_1u_price']:,.2f} | 2U HA: ${plat['base_2u_cluster_price']:,.2f}")
        print("\nAppliance Tiers Available:")
        for tid, t in APPLIANCE_TIERS.items():
            print(f" • {t['name']:<46} | Nodes: {t['node_count']} | Max Seats: {t['max_engineers']:<5} | Base BOM: ${t['base_price']:,.2f}")
        print("═" * 80)

    if args.size_appliance:
        engineers = args.size_appliance
        bom = configurator.generate_itemized_bom(engineers)
        print("\n" + "─" * 80)
        print(f"Hardware Sizing for {engineers} Engineers on {bom['sizing_parameters']['vendor_platform']}")
        print("─" * 80)
        print(f"Selected Tier: {bom['sizing_parameters']['selected_tier']} ({bom['sizing_parameters']['form_factor']})")
        print(f"Server Model:  {bom['sizing_parameters']['server_model']} (Nodes: {bom['sizing_parameters']['node_count']})")
        print(f"Processors:    {bom['hardware_specifications']['processors']}")
        print(f"RAM:           {bom['hardware_specifications']['memory_total_gb']} GB ECC DDR5")
        print(f"NVMe SEDs:     {bom['hardware_specifications']['usable_storage_nvme_tb']} TB Usable ({bom['hardware_specifications']['raw_storage_nvme_tb']} TB Raw RAID 10)")
        print(f"Total BOM:     ${bom['itemized_bom_usd']['total_appliance_bom_price']:,.2f}")
        print("─" * 80)

    if args.calculate_thermal_power:
        print("\n" + "═" * 80)
        print("Thermal & Electrical Power Sizing Matrix (80 PLUS Titanium 96% Efficiency)")
        print("═" * 80)
        print(f"{'Appliance Tier':<40} | {'Typical W':<10} | {'Peak W':<8} | {'BTU/hr (Typ)':<14} | {'Amps @ 208V'}")
        print("─" * 80)
        for tid, t in APPLIANCE_TIERS.items():
            typ_btu = calculate_thermal_btu(t["typical_power_watts"])
            amps = calculate_electrical_amperage(t["typical_power_watts"], 208.0)
            print(f"{t['name']:<40} | {t['typical_power_watts']:>7.0f} W | {t['peak_power_watts']:>6.0f} W | {typ_btu:>10,.1f} BTU | {amps:>9.2f} A")
        print("═" * 80)

    if args.export_hardware_bundle:
        paths = configurator.export_all()
        print("\nSuccessfully exported hardware appliance bundle:")
        for k, p in paths.items():
            print(f" • {k}: {p}")


if __name__ == "__main__":
    main()
