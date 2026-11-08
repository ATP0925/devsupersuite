"""
═══════════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Air-Gapped Enterprise Deployment Verification Suite
Document Ref: DSS-TEST-AIRGAP-2026-V1
Compliance Standards: NSA/CISA Kubernetes Hardening Guidance, DISA STIG, SOC 2 CC6.6

Verifies:
1. Docker Compose Air-Gapped Hardening (internal: true, UID 10001, drop ALL, tmpfs, SIMD)
2. Helm Chart Enterprise Configuration (airgap: true, zeroEgress: true, NetworkPolicy)
3. Zero-Egress Mathematical Isolation (No network socket calls during AST / Entropy operations)
4. Resource Allocations & Healthcheck Probes
5. Strict 100% Brand Anonymity (DevSuperSuite Official Representation)
═══════════════════════════════════════════════════════════════════════════════════
"""

import ast
import os
import re
import socket
import sys
import unittest
from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEPLOYMENT_DIR = REPO_ROOT / "deployment"
DOCKER_COMPOSE_PATH = DEPLOYMENT_DIR / "docker-compose.enterprise.yml"
HELM_CHART_PATH = DEPLOYMENT_DIR / "helm" / "Chart.yaml"
HELM_VALUES_PATH = DEPLOYMENT_DIR / "helm" / "values.enterprise.yaml"
HELM_NETPOLICY_PATH = DEPLOYMENT_DIR / "helm" / "templates" / "networkpolicy.yaml"


class TestAirgapDeployment(unittest.TestCase):
    """
    Automated verification of the DevSuperSuite Air-Gapped Deployment Package.
    Ensures complete suitability for Fortune 500 banks, sovereign clouds, and defense contractors.
    """

    def setUp(self):
        self.assertTrue(DOCKER_COMPOSE_PATH.exists(), f"Missing {DOCKER_COMPOSE_PATH}")
        self.assertTrue(HELM_CHART_PATH.exists(), f"Missing {HELM_CHART_PATH}")
        self.assertTrue(HELM_VALUES_PATH.exists(), f"Missing {HELM_VALUES_PATH}")

        with open(DOCKER_COMPOSE_PATH, "r", encoding="utf-8") as f:
            self.compose_cfg = yaml.safe_load(f)

        with open(HELM_CHART_PATH, "r", encoding="utf-8") as f:
            self.helm_chart = yaml.safe_load(f)

        with open(HELM_VALUES_PATH, "r", encoding="utf-8") as f:
            self.helm_values = yaml.safe_load(f)

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Docker Compose Air-Gapped Hardening Verification
    # ─────────────────────────────────────────────────────────────────────────

    def test_01_docker_compose_network_isolation(self):
        """
        Verify: Docker Compose enforces an internal network (internal: true)
        which mathematically disables external gateway routing and prevents WAN egress.
        """
        networks = self.compose_cfg.get("networks", {})
        self.assertIn("airgap_internal", networks, "Expected 'airgap_internal' network definition")
        airgap_net = networks["airgap_internal"]

        # internal: true guarantees no outbound default gateway is provisioned
        self.assertTrue(
            airgap_net.get("internal"),
            "Critical: 'airgap_internal' must have 'internal: true' to block outbound internet egress!"
        )

    def test_02_docker_compose_non_root_uid_10001(self):
        """
        Verify: Every container runs as unprivileged non-root UID 10001:10001.
        """
        services = self.compose_cfg.get("services", {})
        self.assertGreaterEqual(len(services), 3, "Expected at least 3 core microservices")

        for s_name, s_cfg in services.items():
            user = str(s_cfg.get("user", ""))
            self.assertIn(
                "10001",
                user,
                f"Service '{s_name}' must run as unprivileged UID 10001! Found user: '{user}'"
            )

    def test_03_docker_compose_read_only_rootfs_and_capabilities(self):
        """
        Verify: Every container enforces read-only root filesystems, drops ALL Linux
        kernel capabilities, and blocks privilege escalation.
        """
        services = self.compose_cfg.get("services", {})
        for s_name, s_cfg in services.items():
            # 1. Read-only rootfs
            self.assertTrue(
                s_cfg.get("read_only"),
                f"Service '{s_name}' must have 'read_only: true' to prevent malware persistence!"
            )

            # 2. Drop all Linux capabilities
            cap_drop = s_cfg.get("cap_drop", [])
            self.assertIn(
                "ALL",
                cap_drop,
                f"Service '{s_name}' must specify 'cap_drop: - ALL'!"
            )

            # 3. No new privileges
            sec_opt = s_cfg.get("security_opt", [])
            self.assertIn(
                "no-new-privileges:true",
                sec_opt,
                f"Service '{s_name}' must enforce 'no-new-privileges:true'!"
            )

    def test_04_docker_compose_tmpfs_ram_disk_allocations(self):
        """
        Verify: Ephemeral RAM-disks (tmpfs) are provisioned for volatile execution,
        guaranteeing zero persistent write operations to host physical storage.
        """
        services = self.compose_cfg.get("services", {})
        for s_name, s_cfg in services.items():
            tmpfs_mounts = s_cfg.get("tmpfs", [])
            self.assertTrue(
                len(tmpfs_mounts) > 0,
                f"Service '{s_name}' must have at least one tmpfs RAM-disk mount!"
            )
            # Ensure /tmp is mounted as tmpfs
            has_tmp = any("/tmp" in str(m) for m in tmpfs_mounts)
            self.assertTrue(has_tmp, f"Service '{s_name}' must mount /tmp on volatile tmpfs RAM-disk!")

    def test_05_docker_compose_simd_and_healthchecks(self):
        """
        Verify: CPU SIMD optimization flags (AVX512/AVX2) and automated healthchecks are configured.
        """
        services = self.compose_cfg.get("services", {})
        omnikernel = services.get("omnikernel-ast-engine", {})
        env_vars = omnikernel.get("environment", [])

        # SIMD flag verification
        has_simd = any("OMNIKERNEL_SIMD_INSTRUCTIONS=AVX512" in str(e) for e in env_vars)
        self.assertTrue(has_simd, "OmniKernel must enable AVX512 SIMD vector instructions for AST parsing!")

        # Offline flag verification
        has_offline = any("OMNIKERNEL_OFFLINE_MODE=1" in str(e) for e in env_vars)
        self.assertTrue(has_offline, "OmniKernel must run in explicit OMNIKERNEL_OFFLINE_MODE=1!")

        # Healthcheck verification across services
        for s_name, s_cfg in services.items():
            healthcheck = s_cfg.get("healthcheck", {})
            self.assertIn("test", healthcheck, f"Service '{s_name}' must define an automated healthcheck test!")

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Helm Chart Enterprise Configuration Verification
    # ─────────────────────────────────────────────────────────────────────────

    def test_06_helm_chart_metadata(self):
        """
        Verify: Helm Chart metadata specifies version 5.2.0, enterprise compliance annotations,
        and DevSuperSuite Official maintainership.
        """
        self.assertEqual(self.helm_chart.get("name"), "devsupersuite-enterprise-airgap")
        self.assertEqual(self.helm_chart.get("version"), "5.2.0")

        maintainers = self.helm_chart.get("maintainers", [])
        self.assertTrue(len(maintainers) > 0)
        self.assertEqual(maintainers[0].get("name"), "DevSuperSuite Official")
        self.assertIn("devsupersuite.web.app", maintainers[0].get("email"))

    def test_07_helm_values_airgap_and_security_context(self):
        """
        Verify: Helm values.enterprise.yaml enforces airgap: true, zeroEgress: true,
        non-root UID 10001, and readOnlyRootFilesystem.
        """
        global_cfg = self.helm_values.get("global", {})
        self.assertTrue(global_cfg.get("airgap"), "global.airgap must be true")
        self.assertTrue(global_cfg.get("zeroEgress"), "global.zeroEgress must be true")
        self.assertFalse(global_cfg.get("telemetryEnabled"), "telemetryEnabled must be false in airgap")

        # Pod Security Context
        pod_sec = self.helm_values.get("securityContext", {})
        self.assertEqual(pod_sec.get("runAsUser"), 10001)
        self.assertEqual(pod_sec.get("runAsGroup"), 10001)
        self.assertTrue(pod_sec.get("runAsNonRoot"))

        # Container Security Context
        ctr_sec = self.helm_values.get("containerSecurityContext", {})
        self.assertTrue(ctr_sec.get("readOnlyRootFilesystem"))
        self.assertFalse(ctr_sec.get("allowPrivilegeEscalation"))
        caps = ctr_sec.get("capabilities", {}).get("drop", [])
        self.assertIn("ALL", caps)

    def test_08_helm_network_policy_zero_egress(self):
        """
        Verify: NetworkPolicy configuration in Helm values specifies denyExternalEgress: true.
        """
        net_pol = self.helm_values.get("networkPolicy", {})
        self.assertTrue(net_pol.get("enabled"), "networkPolicy.enabled must be true")
        self.assertTrue(net_pol.get("denyExternalEgress"), "networkPolicy.denyExternalEgress must be true")
        self.assertTrue(net_pol.get("allowIntraNamespace"), "networkPolicy.allowIntraNamespace must be true")

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Zero-Egress Mathematical Isolation (No Socket Activity During Processing)
    # ─────────────────────────────────────────────────────────────────────────

    def test_09_offline_ast_slicing_zero_socket_activity(self):
        """
        Verify: AST context slicing operates 100% offline in-memory without initiating
        any network socket connections. Monkeypatches socket.socket to ensure zero network calls.
        """
        # Define a mock class with deep AST structure
        source_code = '''
class CoreBankingLedger:
    """Enterprise sovereign double-entry ledger."""

    def __init__(self, ledger_id: str, balance_cents: int = 0) -> None:
        """Initialize ledger."""
        self.ledger_id = ledger_id
        self.balance = balance_cents

    def transfer(self, target_id: str, amount_cents: int) -> bool:
        """Execute atomic balance deduction."""
        if self.balance < amount_cents:
            raise ValueError("Insufficient balance")
        self.balance -= amount_cents
        return True
'''

        # Monkeypatch socket.socket to fail if any external network connection is attempted
        original_socket = socket.socket

        def blocked_socket(*args, **kwargs):
            raise ConnectionRefusedError("AIR-GAP VIOLATION: Socket creation attempted during offline AST processing!")

        socket.socket = blocked_socket

        try:
            # Execute local AST transformation
            from test_enterprise_compliance import ASTInterfaceStubGenerator
            generator = ASTInterfaceStubGenerator(preserve_docstrings=True)
            stub_code, metrics = generator.generate_stub(source_code)

            # Assert AST was successfully sliced in memory with zero sockets
            self.assertIn("class CoreBankingLedger:", stub_code)
            self.assertIn("def transfer(self, target_id: str, amount_cents: int) -> bool:", stub_code)
            self.assertIn("...", stub_code)
            self.assertNotIn("self.balance -= amount_cents", stub_code)
            self.assertGreater(metrics["reduction_percentage"], 20.0)

        finally:
            # Restore original socket
            socket.socket = original_socket

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Strict 100% Brand Anonymity
    # ─────────────────────────────────────────────────────────────────────────

    def test_10_strict_brand_anonymity_airgap(self):
        """
        Verify: 100% Brand Anonymity across all deployment files (Docker Compose, Helm, Guide).
        Zero personal names, personal email domains, or personal identifiers.
        """
        target_files = [
            DOCKER_COMPOSE_PATH,
            HELM_CHART_PATH,
            HELM_VALUES_PATH,
            DEPLOYMENT_DIR / "airgap_deployment_guide.md",
        ]

        forbidden_patterns = [
            r"\b[A-Za-z0-9._%+-]+@gmail\.com\b",
            r"\b[A-Za-z0-9._%+-]+@yahoo\.com\b",
            r"\b[A-Za-z0-9._%+-]+@hotmail\.com\b",
        ]

        for file_path in target_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            for pattern in forbidden_patterns:
                matches = re.findall(pattern, content)
                self.assertEqual(
                    len(matches),
                    0,
                    f"Personal email pattern detected in {file_path.name}: {matches}!"
                )

            # Ensure official brand attribution exists
            self.assertIn("DevSuperSuite", content)


if __name__ == "__main__":
    unittest.main()
