"""
DevSuperSuite Tech Services - FIPS 140-3 PKCS#11 Hardware Token Test Suite
File: tests/test_pkcs11_token_vault.py
Governing Authority: DevSuperSuite Security & Compliance Desk
Contact: security@devsupersuite.com
Regulatory Baseline: OASIS PKCS#11 v3.1 / NIST FIPS 140-3 Level 3 / NIST SP 800-57
"""

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from services.enterprise_pkcs11_token_vault import (
    EnterprisePKCS11TokenVault,
    PKCS11HardwareToken,
    TokenSlotInfo,
    CKR,
    CKU,
    CKS,
    CKM,
    CKK,
    export_pkcs11_token_manifest,
    export_pkcs11_security_report,
)


class TestEnterprisePKCS11TokenVault:
    """Comprehensive test suite for FIPS 140-3 PKCS#11 hardware root-of-trust controller."""

    @pytest.fixture
    def vault(self):
        return EnterprisePKCS11TokenVault()

    def test_01_token_initialization_and_slot_enumeration(self, vault):
        """Verifies multi-slot enumeration across YubiKey, Nitrokey, and Thales Luna tokens."""
        tokens = vault.list_tokens()
        assert len(tokens) == 3

        slot_0 = tokens[0]
        assert slot_0["slot_id"] == 0
        assert "YubiKey 5 FIPS" in slot_0["model_name"]
        assert "NIST-CMVP-#4570" in slot_0["fips_certification_id"]
        assert slot_0["fips_security_level"] == "FIPS 140-3 Level 3"

        slot_1 = tokens[1]
        assert slot_1["slot_id"] == 1
        assert "Nitrokey HSM 2" in slot_1["model_name"]

        slot_2 = tokens[2]
        assert slot_2["slot_id"] == 2
        assert "Luna PCIe HSM" in slot_2["model_name"]

    def test_02_session_open_and_user_login(self, vault):
        """Verifies session state transitions from public to authenticated user mode."""
        token = vault.get_token(0)
        assert token is not None
        assert token.session_state == CKS.CKS_RW_PUBLIC_SESSION

        # Successful login
        res = token.login(CKU.CKU_USER, "123456")
        assert res == CKR.CKR_OK
        assert token.session_state == CKS.CKS_RW_USER_FUNCTIONS
        assert token.slot_info.user_pin_retries_remaining == 3

        # Logout
        logout_res = token.logout()
        assert logout_res == CKR.CKR_OK
        assert token.session_state == CKS.CKS_RW_PUBLIC_SESSION

    def test_03_pin_hardware_rate_limiting_and_lockout(self):
        """Verifies hardware ASIC locks after exactly 3 failed PIN attempts."""
        slot = TokenSlotInfo(
            slot_id=99,
            manufacturer_id="TestHSM",
            model_name="Test Token",
            serial_number="TEST-001",
            firmware_version="1.0",
            fips_certification_id="FIPS-TEST",
            fips_security_level="Level 3",
        )
        token = PKCS11HardwareToken(slot, user_pin="CORRECT_PIN", so_pin="SO_PIN_123")

        # Attempt 1: Fail
        r1 = token.login(CKU.CKU_USER, "WRONG_1")
        assert r1 == CKR.CKR_PIN_INCORRECT
        assert token.slot_info.user_pin_retries_remaining == 2
        assert token.slot_info.is_user_locked is False

        # Attempt 2: Fail
        r2 = token.login(CKU.CKU_USER, "WRONG_2")
        assert r2 == CKR.CKR_PIN_INCORRECT
        assert token.slot_info.user_pin_retries_remaining == 1

        # Attempt 3: Fail & Lock
        r3 = token.login(CKU.CKU_USER, "WRONG_3")
        assert r3 == CKR.CKR_PIN_LOCKED
        assert token.slot_info.user_pin_retries_remaining == 0
        assert token.slot_info.is_user_locked is True

        # Attempt 4: Even correct PIN is rejected once locked
        r4 = token.login(CKU.CKU_USER, "CORRECT_PIN")
        assert r4 == CKR.CKR_PIN_LOCKED

    def test_04_security_officer_unblock_and_pin_reset(self):
        """Verifies Security Officer (SO) unblocks a locked token and restores access."""
        slot = TokenSlotInfo(
            slot_id=99,
            manufacturer_id="TestHSM",
            model_name="Test Token",
            serial_number="TEST-002",
            firmware_version="1.0",
            fips_certification_id="FIPS-TEST",
            fips_security_level="Level 3",
        )
        token = PKCS11HardwareToken(slot, user_pin="ORIGINAL_PIN", so_pin="SO_SECRET_99")

        # Force lockout
        token.login(CKU.CKU_USER, "BAD1")
        token.login(CKU.CKU_USER, "BAD2")
        token.login(CKU.CKU_USER, "BAD3")
        assert token.slot_info.is_user_locked is True

        # Unblock using SO PIN
        unblock_res = token.unblock_user_pin("SO_SECRET_99", "NEW_PIN_456")
        assert unblock_res == CKR.CKR_OK
        assert token.slot_info.is_user_locked is False
        assert token.slot_info.user_pin_retries_remaining == 3

        # Login with new PIN succeeds
        login_res = token.login(CKU.CKU_USER, "NEW_PIN_456")
        assert login_res == CKR.CKR_OK
        token.logout()

    def test_05_so_pin_rate_limiting_permanent_zeroization(self):
        """Verifies 3 consecutive failed SO PIN attempts permanently zeroizes token."""
        slot = TokenSlotInfo(
            slot_id=99,
            manufacturer_id="TestHSM",
            model_name="Test Token",
            serial_number="TEST-003",
            firmware_version="1.0",
            fips_certification_id="FIPS-TEST",
            fips_security_level="Level 3",
        )
        token = PKCS11HardwareToken(slot, user_pin="PIN1", so_pin="SO_SECURE")

        # SO attempt 1 & 2
        assert token.login(CKU.CKU_SO, "SO_BAD1") == CKR.CKR_PIN_INCORRECT
        assert token.login(CKU.CKU_SO, "SO_BAD2") == CKR.CKR_PIN_INCORRECT
        assert token.slot_info.is_zeroized is False

        # SO attempt 3: Triggers permanent zeroization
        r3 = token.login(CKU.CKU_SO, "SO_BAD3")
        assert r3 == CKR.CKR_TOKEN_ZEROIZED
        assert token.slot_info.is_zeroized is True

        # Further operations permanently fail
        assert token.login(CKU.CKU_USER, "PIN1") == CKR.CKR_TOKEN_ZEROIZED
        assert token.login(CKU.CKU_SO, "SO_SECURE") == CKR.CKR_TOKEN_ZEROIZED

    def test_06_ed25519_keypair_generation_in_silicon(self, vault):
        """Verifies Ed25519 keypair generation inside silicon with non-extractability flags."""
        token = vault.get_token(0)
        assert token is not None
        token.login(CKU.CKU_USER, "123456")

        status, handle, pub_pem = token.generate_keypair(CKK.CKK_EC_EDWARDS, "TEST-ED25519-KEY")
        assert status == CKR.CKR_OK
        assert handle is not None
        assert pub_pem is not None
        assert "BEGIN PUBLIC KEY" in pub_pem

        # Verify attributes
        c_status, is_priv = token.get_attribute_value(handle, "CKA_PRIVATE")
        assert c_status == CKR.CKR_OK and is_priv is True

        e_status, extractable = token.get_attribute_value(handle, "CKA_EXTRACTABLE")
        assert e_status == CKR.CKR_OK and extractable is False

        token.logout()

    def test_07_ecdsa_p384_keypair_generation_in_silicon(self, vault):
        """Verifies ECDSA P-384 keypair generation in hardware token."""
        token = vault.get_token(2)
        assert token is not None
        token.login(CKU.CKU_USER, "987654")

        status, handle, pub_pem = token.generate_keypair(CKK.CKK_EC, "TEST-P384-KEY")
        assert status == CKR.CKR_OK
        assert handle is not None
        assert pub_pem is not None

        # Verify key type
        t_status, key_type = token.get_attribute_value(handle, "CKA_KEY_TYPE")
        assert t_status == CKR.CKR_OK and key_type == CKK.CKK_EC.value

        token.logout()

    def test_08_rsa4096_keypair_generation_in_silicon(self, vault):
        """Verifies RSA-4096 keypair generation in hardware token."""
        token = vault.get_token(1)
        assert token is not None
        token.login(CKU.CKU_USER, "654321")

        status, handle, pub_pem = token.generate_keypair(CKK.CKK_RSA, "TEST-RSA4096-KEY")
        assert status == CKR.CKR_OK
        assert handle is not None
        assert pub_pem is not None
        assert "BEGIN PUBLIC KEY" in pub_pem

        token.logout()

    def test_09_private_key_extraction_prohibited(self, vault):
        """Verifies CKA_VALUE extraction of private key raises CKR_KEY_NOT_EXTRACTABLE."""
        token = vault.get_token(0)
        assert token is not None
        token.login(CKU.CKU_USER, "123456")

        _, handle, _ = token.generate_keypair(CKK.CKK_EC_EDWARDS, "TEST-SENSITIVE-KEY")
        assert handle is not None

        # Attempt to read private key bytes
        read_status, val = token.get_attribute_value(handle, "CKA_VALUE")
        assert read_status == CKR.CKR_KEY_NOT_EXTRACTABLE
        assert val is None, "Private key material must NEVER be exposed in memory!"

        token.logout()

    def test_10_hardware_signing_git_release_msa(self, vault):
        """Verifies hardware signing of Git commits, release digests, and MSA contracts."""
        # 1. Git Commit Signing (Slot 0 - Ed25519)
        git_payload = b"commit tree 01928374\nauthor DevSuperSuite\n\nRelease verification"
        ok_git, sig_git, pub_git, _ = vault.sign_git_commit(0, "123456", git_payload)
        assert ok_git is True
        assert len(sig_git) == 64
        assert vault.verify_hardware_signature(pub_git, git_payload, sig_git, CKM.CKM_EDDSA) is True
        assert vault.verify_hardware_signature(pub_git, b"Tampered Git Payload", sig_git, CKM.CKM_EDDSA) is False

        # 2. Release Digest Signing (Slot 1 - RSA-4096 PSS)
        rel_digest = hashlib.sha256(b"DevSuperSuite-Release-Binary-v3.2.0").digest()
        ok_rel, sig_rel, pub_rel, _ = vault.sign_release_digest(1, "654321", rel_digest)
        assert ok_rel is True
        assert len(sig_rel) == 512  # 4096 bits = 512 bytes
        assert vault.verify_hardware_signature(pub_rel, rel_digest, sig_rel, CKM.CKM_RSA_PKCS_PSS) is True
        assert vault.verify_hardware_signature(pub_rel, b"Wrong Digest", sig_rel, CKM.CKM_RSA_PKCS_PSS) is False

        # 3. Customer MSA Signing (Slot 2 - ECDSA P-384)
        msa_hash = hashlib.sha384(b"Master Services Agreement Contract Document").digest()
        ok_msa, sig_msa, pub_msa, _ = vault.sign_msa_contract(2, "987654", msa_hash)
        assert ok_msa is True
        assert len(sig_msa) > 90  # DER encoded P-384 signature ~100-104 bytes
        assert vault.verify_hardware_signature(pub_msa, msa_hash, sig_msa, CKM.CKM_ECDSA_SHA384) is True

    def test_11_cli_interface_all_flags(self):
        """Verifies CLI flags execute with zero exit code and DevSuperSuite branding."""
        script_path = REPO_ROOT / "services" / "enterprise_pkcs11_token_vault.py"
        assert script_path.exists()

        flags = [
            ["--list-tokens"],
            ["--simulate-sign"],
            ["--verify-lockout"],
            ["--export-manifest"],
            ["--export-report"],
        ]

        for flag_set in flags:
            proc = subprocess.run(
                [sys.executable, str(script_path)] + flag_set,
                capture_output=True,
                text=True,
                timeout=25,
            )
            assert proc.returncode == 0, f"CLI execution failed with {flag_set}: {proc.stderr}"
            assert "DevSuperSuite" in proc.stdout

    def test_12_strict_brand_anonymity_under_devsupersuite(self, vault):
        """Enforces 100% brand anonymity under DevSuperSuite Security & Compliance Desk."""
        manifest_path = export_pkcs11_token_manifest(vault)
        report_path = export_pkcs11_security_report(vault)

        target_files = [
            REPO_ROOT / "services" / "enterprise_pkcs11_token_vault.py",
            manifest_path,
            report_path,
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
            scrubbed = re.sub(r"REPORT-PKCS11-FIPS140-3-\d{4}-V\d", "", scrubbed)

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

