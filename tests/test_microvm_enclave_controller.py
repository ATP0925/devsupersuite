#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - MicroVM Enclave Controller Test Suite
Reference: DSS-MICROVM-TESTS-2026-V1
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
MICROVM_DIR = DEPLOYMENT_DIR / "microvm"

if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from enterprise_microvm_enclave_controller import (
    ORGANIZATION_NAME,
    PRIMARY_CONTACT,
    TECHNICAL_CONTACT,
    REFERENCE_CODE,
    MAX_BOOT_TIME_TARGET_MS,
    MAX_VCPU_LIMIT,
    MAX_MEMORY_BYTES,
    MAX_MEMORY_SWAP_BYTES,
    AF_VSOCK_DOMAIN_ID,
    BASE_JAILER_UID,
    BASE_JAILER_GID,
    SeccompBPFFilter,
    CgroupV2Throttler,
    MicroVMEnclave,
    EnterpriseMicroVMEnclaveController
)


class TestEnterpriseMicroVMEnclaveController:
    """Enterprise verification suite for MicroVM Enclave & Firecracker Isolation."""

    def test_microvm_initialization_and_specs(self):
        """Validate microVM instance defaults: 2 vCPU, 512MB RAM, zero swap, valid VSOCK CID."""
        vm = MicroVMEnclave(vsock_cid=5)
        assert vm.vcpu_count == MAX_VCPU_LIMIT
        assert vm.memory_bytes == MAX_MEMORY_BYTES
        assert vm.vsock_cid >= 3
        assert vm.status == "INITIALIZED"
        assert "microvm-dss-" in vm.vm_id

    def test_sub_5ms_boot_latency(self):
        """Validate Firecracker microVM launch lifecycle strictly satisfies <= 5.0ms SLA."""
        vm = MicroVMEnclave(vsock_cid=6)
        boot_meta = vm.boot()

        assert vm.status == "RUNNING"
        assert boot_meta["boot_latency_ms"] <= MAX_BOOT_TIME_TARGET_MS
        assert boot_meta["sub_5ms_sla_met"] is True
        assert boot_meta["vcpu_allocated"] == 2
        assert boot_meta["memory_mb_allocated"] == 512

    def test_cgroup_v2_throttling_spec(self):
        """Verify Linux cgroup v2 control parameters: CPU quota, memory max, swap=0, read-only rootfs."""
        throttler = CgroupV2Throttler(max_vcpu=2, memory_bytes=536870912)
        spec = throttler.generate_cgroup_v2_spec("test-vm-01")

        ctrl = spec["controllers"]
        assert ctrl["cpu.max"] == "200000 100000"  # 2 vCPUs
        assert ctrl["memory.max"] == 536870912       # 512 MiB
        assert ctrl["memory.swap.max"] == 0          # Strictly zero swap
        assert ctrl["memory.oom.group"] == 1         # Atomic OOM group termination

        # Rootfs mount policy
        mount = spec["rootfs_mount_policy"]
        assert mount["read_only"] is True
        assert "MS_RDONLY" in mount["mount_flags"]

    def test_seccomp_bpf_whitelist_allowed(self):
        """Verify standard runtime syscalls (read, write, mmap, futex) are permitted."""
        whitelisted_calls = ["read", "write", "mmap", "futex", "nanosleep", "exit_group"]
        for call in whitelisted_calls:
            allowed, action, reason = SeccompBPFFilter.evaluate_syscall(call)
            assert allowed is True
            assert action == "SECCOMP_RET_ALLOW"
            assert "WHITELISTED" in reason

    def test_seccomp_bpf_socket_domain_enforcement(self):
        """Verify socket creation is strictly restricted to local AF_VSOCK (domain 40)."""
        # AF_VSOCK (40) is ALLOWED
        allowed, action, _ = SeccompBPFFilter.evaluate_syscall("socket", socket_domain=AF_VSOCK_DOMAIN_ID)
        assert allowed is True
        assert action == "SECCOMP_RET_ALLOW"

        # AF_INET (2) - Raw / TCP is BLOCKED
        allowed_inet, action_inet, _ = SeccompBPFFilter.evaluate_syscall("socket", socket_domain=2)
        assert allowed_inet is False
        assert "EPERM" in action_inet

        # AF_INET6 (10) is BLOCKED
        allowed_inet6, action_inet6, _ = SeccompBPFFilter.evaluate_syscall("socket", socket_domain=10)
        assert allowed_inet6 is False
        assert "EPERM" in action_inet6

    def test_seccomp_bpf_forbidden_high_risk_syscalls(self):
        """Verify ptrace, bpf, and sys_chroot are strictly blocked with process termination."""
        forbidden_calls = ["ptrace", "bpf", "sys_chroot", "kexec_load", "mount"]
        for call in forbidden_calls:
            allowed, action, reason = SeccompBPFFilter.evaluate_syscall(call)
            assert allowed is False
            assert action == "SECCOMP_RET_KILL_PROCESS"
            assert "FORBIDDEN_SYSCALL" in reason

    def test_ephemeral_sandboxed_execution_success(self):
        """Execute sandboxed AST compilation task with whitelisted system calls."""
        vm = MicroVMEnclave(vsock_cid=7)
        vm.boot()

        result = vm.execute_sandboxed_task("task-ast-01", "def parse_tree(): return 'AST_ROOT'")
        assert result["execution_status"] == "COMPLETED"
        assert result["aborted_by_seccomp"] is False
        assert result["execution_duration_ms"] > 0
        assert len(result["payload_digest"]) == 64

    def test_sandboxed_execution_malicious_syscall_aborted(self):
        """Simulate malicious guest attempting ptrace; verify microVM is instantly killed."""
        vm = MicroVMEnclave(vsock_cid=8)
        vm.boot()

        malicious_calls = [
            {"name": "read"},
            {"name": "ptrace"}  # Forbidden injection attempt
        ]

        result = vm.execute_sandboxed_task("task-exploit-01", "malicious_payload", simulated_syscalls=malicious_calls)
        assert result["execution_status"] == "TERMINATED_BY_SECCOMP"
        assert result["aborted_by_seccomp"] is True
        assert "FORBIDDEN_SYSCALL" in result["abort_reason"]
        assert vm.status == "KILLED_BY_SECCOMP"

    def test_microvm_teardown_and_zeroization(self):
        """Verify clean zeroization of memory and cgroups in <= 2.0ms."""
        vm = MicroVMEnclave(vsock_cid=9)
        vm.boot()
        teardown = vm.terminate_and_zeroize()

        assert vm.status == "ZEROIZED"
        assert teardown["teardown_latency_ms"] <= 2.0
        assert teardown["residual_state_remaining"] is False
        assert teardown["tmpfs_zeroized"] is True
        assert teardown["cgroup_destroyed"] is True

    def test_boot_latency_benchmark_suite(self):
        """Run multi-iteration boot benchmark and verify 100% sub-5ms pass rate."""
        controller = EnterpriseMicroVMEnclaveController()
        bm = controller.benchmark_boot_latency(iterations=15)

        assert bm["iterations_executed"] == 15
        assert bm["average_boot_latency_ms"] <= 5.0
        assert bm["max_boot_latency_ms"] <= 5.0
        assert bm["sla_pass_rate_percentage"] == 100.0
        assert bm["sub_5ms_sla_verified"] is True

    def test_jailer_manifest_export_and_json_validity(self, tmp_path):
        """Verify Firecracker jailer manifest generation and valid JSON schema."""
        controller = EnterpriseMicroVMEnclaveController()
        target_file = tmp_path / "jailer_manifest.json"
        controller.export_jailer_manifest(target_file)

        assert target_file.exists()
        with open(target_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["metadata"]["organization"] == ORGANIZATION_NAME
        assert manifest["metadata"]["contact"] == PRIMARY_CONTACT
        assert manifest["jailer_configuration"]["jailer_uid"] == BASE_JAILER_UID
        assert manifest["jailer_configuration"]["rootfs_read_only"] is True
        assert manifest["cgroup_v2_throttling"]["max_vcpus"] == MAX_VCPU_LIMIT
        assert manifest["cgroup_v2_throttling"]["memory_swap_max_bytes"] == 0
        assert "ptrace" in manifest["seccomp_bpf_policy"]["forbidden_syscalls"]

    def test_architecture_report_generation(self, tmp_path):
        """Verify microVM architecture whitepaper export and content completeness."""
        controller = EnterpriseMicroVMEnclaveController()
        report_file = tmp_path / "microvm_enclave_architecture_report.md"
        controller.export_architecture_report(report_file)

        assert report_file.exists()
        text = report_file.read_text(encoding="utf-8")
        assert "DevSuperSuite Technical Report: MicroVM Enclave Isolation & Firecracker Architecture" in text
        assert "Linux KVM" in text
        assert "cgroup v2" in text
        assert "Seccomp-BPF" in text
        assert "AF_VSOCK" in text
        assert "solutions@devsupersuite.com" in text

    def test_brand_anonymity_invariants(self):
        """
        Enforce strict institutional brand anonymity:
        Must NOT contain personal names or unauthorized personal email domains.
        Must strictly represent DevSuperSuite Solutions Architecture / OmniKernel Labs.
        """
        forbidden_terms = ["github.com/", "gitlab.com/", "@gmail.com", "@yahoo.com", "@hotmail.com"]
        files_to_check = [
            SERVICES_DIR / "enterprise_microvm_enclave_controller.py",
            MICROVM_DIR / "jailer_manifest.json",
            REPORTS_DIR / "microvm_enclave_architecture_report.md"
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
        script = str(SERVICES_DIR / "enterprise_microvm_enclave_controller.py")

        commands = [
            [python_exe, script, "--summary"],
            [python_exe, script, "--spawn-microvm", "test-task-42"],
            [python_exe, script, "--benchmark-boot-time"],
            [python_exe, script, "--verify-seccomp-policy"],
            [python_exe, script, "--simulate-untrusted-execution", "def sample(): return 1"],
            [python_exe, script, "--export-jailer-bundle"]
        ]

        for cmd in commands:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            assert res.returncode == 0, f"Command failed: {' '.join(cmd)}\nStderr: {res.stderr}"
            assert len(res.stdout) > 0
