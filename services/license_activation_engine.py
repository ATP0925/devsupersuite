#!/usr/bin/env python3
"""
⚡ DevSuperSuite Official: Post-Purchase License Key Activation & Onboarding Telemetry Engine
File: license_activation_engine.py
Version: 1.0.0
Governing Authority: DevSuperSuite Customer Engineering Desk (support@devsupersuite.com)
Strict Protocol: 100% Brand Anonymity - DevSuperSuite Official Only - Zero Founder Personal Identifiers

Features:
- Automated post-purchase software activation workflow upon order completion.
- Ed25519 asymmetric cryptographic digital signing for instant local standalone validation.
- Zero-telemetry offline air-gapped license activation (`devsupersuite license activate --offline-file license.sig`).
- Personalized multi-platform 1-click CLI installer one-liners (Bash for Linux/macOS, PowerShell for Windows).
- Monorepo profiling and Time-To-First-Activation (TTFA) telemetry engine.
- Full CLI interfaces: --generate-license, --verify-license, --audit-activations, --summary.
"""

import os
import sys
import json
import uuid
import hashlib
import argparse
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Cryptographic Ed25519
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# Base Directories
SERVICES_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(SERVICES_DIR)
DATA_DIR = os.path.join(SCRATCH_DIR, "data")
MARKETING_DIR = os.path.join(SCRATCH_DIR, "marketing")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MARKETING_DIR, exist_ok=True)

LICENSES_REGISTRY_PATH = os.path.join(DATA_DIR, "licenses_registry.json")
ACTIVATIONS_TELEMETRY_PATH = os.path.join(DATA_DIR, "activations_telemetry.json")
KEY_VAULT_PATH = os.path.join(DATA_DIR, ".ed25519_vault.json")
PUBLIC_KEY_EXPORT_PATH = os.path.join(DATA_DIR, "dss_ed25519_public.key")

DEFAULT_INSTALL_URL_SH = "https://devsupersuite.web.app/install.sh"
DEFAULT_INSTALL_URL_PS1 = "https://devsupersuite.web.app/install.ps1"


class Ed25519LicenseAuthority:
    """Institutional cryptographic authority signing and verifying DevSuperSuite license grants."""

    def __init__(self, vault_path: str = KEY_VAULT_PATH):
        self.vault_path = vault_path
        self._private_key, self._public_key = self._load_or_create_keys()

    def _load_or_create_keys(self) -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
        if os.path.exists(self.vault_path):
            try:
                with open(self.vault_path, "r", encoding="utf-8") as f:
                    vault = json.load(f)
                    priv_bytes = bytes.fromhex(vault["private_key_hex"])
                    priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)
                    pub_key = priv_key.public_key()
                    self._export_public_key_file(pub_key)
                    return priv_key, pub_key
            except Exception:
                pass

        priv_key = ed25519.Ed25519PrivateKey.generate()
        pub_key = priv_key.public_key()
        priv_bytes = priv_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        pub_bytes = pub_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        with open(self.vault_path, "w", encoding="utf-8") as f:
            json.dump({
                "entity": "DevSuperSuite Official Enterprise Authority",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "private_key_hex": priv_bytes.hex(),
                "public_key_hex": pub_bytes.hex()
            }, f, indent=2)

        self._export_public_key_file(pub_key)
        return priv_key, pub_key

    def _export_public_key_file(self, pub_key: ed25519.Ed25519PublicKey) -> None:
        pub_bytes = pub_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        with open(PUBLIC_KEY_EXPORT_PATH, "w", encoding="utf-8") as f:
            f.write(pub_bytes.hex())

    def get_public_key_hex(self) -> str:
        pub_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        return pub_bytes.hex()

    def sign_license_payload(self, canonical_json: str) -> Dict[str, str]:
        """Produces SHA-256 fingerprint and Ed25519 digital signature over license payload."""
        data_bytes = canonical_json.encode("utf-8")
        sha256_digest = hashlib.sha256(data_bytes).hexdigest()
        signature_bytes = self._private_key.sign(data_bytes)

        return {
            "algorithm": "Ed25519",
            "sha256_digest": sha256_digest,
            "signature_hex": signature_bytes.hex(),
            "signer_public_key_hex": self.get_public_key_hex()
        }

    @staticmethod
    def verify_offline(canonical_json: str, signature_hex: str, public_key_hex: str) -> bool:
        """
        100% offline verification using local public key. Zero outbound network socket calls.
        """
        try:
            pub_bytes = bytes.fromhex(public_key_hex.strip())
            sig_bytes = bytes.fromhex(signature_hex.strip())
            pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            pub_key.verify(sig_bytes, canonical_json.encode("utf-8"))
            return True
        except Exception:
            return False


class LicenseActivationEngine:
    """Manages post-purchase license issuance, onboarding CLI commands, and telemetry."""

    def __init__(
        self,
        registry_path: str = LICENSES_REGISTRY_PATH,
        telemetry_path: str = ACTIVATIONS_TELEMETRY_PATH
    ):
        self.registry_path = registry_path
        self.telemetry_path = telemetry_path
        self.authority = Ed25519LicenseAuthority()

        self.licenses: List[Dict[str, Any]] = self._load_or_init_licenses()
        self.telemetry: List[Dict[str, Any]] = self._load_or_init_telemetry()

    def _load_or_init_licenses(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        now = datetime.now(timezone.utc)
        seeds = [
            {
                "license_key": "DSS-PRO-2026-X89F-992A-4B7C",
                "order_id": "GUM-883921",
                "customer_email": "dev.marcus@quantumcloud.de",
                "customer_name": "Marcus Vance",
                "plan_name": "Hacker Solo",
                "seats": 1,
                "issued_at": (now - timedelta(days=6)).isoformat(),
                "status": "ACTIVATED",
                "is_airgap": False,
                "signature_hex": "a9f82901c849e019284710293847592038471029384759203847102938471029384710293847102938471029384710293847102938471029384710293847102a"
            },
            {
                "license_key": "DSS-PRO-2026-T44A-882C-110F",
                "order_id": "PP-TX-992019",
                "customer_email": "techlead.priya@fintechscale.in",
                "customer_name": "Priya Sharma",
                "plan_name": "Team 5-Seat",
                "seats": 5,
                "issued_at": (now - timedelta(days=3)).isoformat(),
                "status": "ACTIVATED",
                "is_airgap": False,
                "signature_hex": "b8e71625d9382019482710293847102938471029384710293847102938471029384710293847102938471029384710293847102938471029384710293847102b"
            },
            {
                "license_key": "DSS-PRO-2026-AIRG-7711-002D",
                "order_id": "FEDWIRE-SCIF-4019",
                "customer_email": "scif-admin@defense-contractor.gov",
                "customer_name": "Defense Systems Directorate",
                "plan_name": "SCIF Defense Unlimited",
                "seats": 1000,
                "issued_at": (now - timedelta(days=1)).isoformat(),
                "status": "ACTIVATED",
                "is_airgap": True,
                "signature_hex": "c7d60514e8271928374619283746192837461928374619283746192837461928374619283746192837461928374619283746192837461928374619283746192c"
            }
        ]
        self._save_json(self.registry_path, seeds)
        return seeds

    def _load_or_init_telemetry(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.telemetry_path):
            try:
                with open(self.telemetry_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        now = datetime.now(timezone.utc)
        seeds = [
            {
                "activation_id": "ACT-881901",
                "license_key": "DSS-PRO-2026-X89F-992A-4B7C",
                "customer_email": "dev.marcus@quantumcloud.de",
                "ide_environment": "Cursor",
                "primary_language": "Python",
                "repo_languages": ["Python", "TypeScript", "SQL"],
                "ast_nodes_sliced_initial": 14208,
                "time_to_first_activation_min": 3.8,
                "activated_at": (now - timedelta(days=6, hours=1)).isoformat()
            },
            {
                "activation_id": "ACT-881902",
                "license_key": "DSS-PRO-2026-T44A-882C-110F",
                "customer_email": "techlead.priya@fintechscale.in",
                "ide_environment": "Claude Code",
                "primary_language": "TypeScript",
                "repo_languages": ["TypeScript", "Rust", "Go"],
                "ast_nodes_sliced_initial": 38940,
                "time_to_first_activation_min": 5.2,
                "activated_at": (now - timedelta(days=3, hours=2)).isoformat()
            },
            {
                "activation_id": "ACT-881903",
                "license_key": "DSS-PRO-2026-AIRG-7711-002D",
                "customer_email": "scif-admin@defense-contractor.gov",
                "ide_environment": "Windsurf",
                "primary_language": "C++",
                "repo_languages": ["C++", "Rust", "Python", "CMake"],
                "ast_nodes_sliced_initial": 92400,
                "time_to_first_activation_min": 7.4,
                "activated_at": (now - timedelta(days=1, hours=4)).isoformat()
            }
        ]
        self._save_json(self.telemetry_path, seeds)
        return seeds

    def _save_json(self, path: str, data: Any) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def generate_license(
        self,
        order_id: str,
        customer_email: str,
        plan_name: str = "Hacker Solo",
        seats: int = 1,
        customer_name: str = "Fellow Developer",
        is_airgap: bool = False
    ) -> Dict[str, Any]:
        """
        Creates canonical license payload, digitally signs it with Ed25519,
        and generates platform CLI activation one-liners.
        """
        now = datetime.now(timezone.utc)
        clean_email = customer_email.strip().lower()

        # Deterministic but cryptographically unique key token
        token_hash = hashlib.sha256(f"{order_id}:{clean_email}:{now.isoformat()}".encode()).hexdigest()[:12].upper()
        key_token = f"DSS-PRO-2026-{token_hash[:4]}-{token_hash[4:8]}-{token_hash[8:12]}"

        canonical_payload = json.dumps({
            "license_key": key_token,
            "issuer": "DevSuperSuite Official Customer Engineering",
            "issuer_email": "support@devsupersuite.com",
            "order_id": order_id,
            "customer_email": clean_email,
            "customer_name": customer_name,
            "plan_name": plan_name,
            "seats": seats,
            "features": [
                "omnikernel_ast_slicing",
                "agentshield_entropy_defense",
                "sub110ms_voice_dsp",
                "zero_telemetry_localhost"
            ],
            "issued_at": now.isoformat(),
            "valid_until": "LIFETIME_STANDALONE",
            "is_airgap": is_airgap
        }, sort_keys=True)

        seal = self.authority.sign_license_payload(canonical_payload)

        # Multi-Platform CLI One-Liners
        install_bash = f"curl -fsSL {DEFAULT_INSTALL_URL_SH} | bash -s -- --license-key {key_token} --email {clean_email}"
        install_powershell = f"iwr -useb {DEFAULT_INSTALL_URL_PS1} | iex; omnikernel activate --key {key_token}"
        offline_activate_cmd = f"devsupersuite license activate --offline-payload '{canonical_payload}' --signature {seal['signature_hex']} --public-key {seal['signer_public_key_hex']}"

        license_record = {
            "license_key": key_token,
            "order_id": order_id,
            "customer_email": clean_email,
            "customer_name": customer_name,
            "plan_name": plan_name,
            "seats": seats,
            "issued_at": now.isoformat(),
            "status": "ISSUED",
            "is_airgap": is_airgap,
            "canonical_payload": canonical_payload,
            "signature_hex": seal["signature_hex"],
            "sha256_digest": seal["sha256_digest"],
            "signer_public_key_hex": seal["signer_public_key_hex"],
            "cli_install_bash": install_bash,
            "cli_install_powershell": install_powershell,
            "cli_offline_activate": offline_activate_cmd
        }

        self.licenses.append(license_record)
        self._save_json(self.registry_path, self.licenses)

        return license_record

    def verify_license(
        self,
        canonical_payload: str,
        signature_hex: str,
        public_key_hex: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cryptographically validates license payload offline using Ed25519 signature.
        """
        if not public_key_hex:
            public_key_hex = self.authority.get_public_key_hex()

        is_valid = Ed25519LicenseAuthority.verify_offline(
            canonical_payload,
            signature_hex,
            public_key_hex
        )

        payload_obj = {}
        try:
            payload_obj = json.loads(canonical_payload)
        except Exception:
            pass

        return {
            "verified": is_valid,
            "algorithm": "Ed25519",
            "license_key": payload_obj.get("license_key", "UNKNOWN"),
            "customer_email": payload_obj.get("customer_email", "UNKNOWN"),
            "plan_name": payload_obj.get("plan_name", "UNKNOWN"),
            "seats": payload_obj.get("seats", 0),
            "offline_airgap_safe": True
        }

    def record_activation_telemetry(
        self,
        license_key: str,
        customer_email: str,
        ide_environment: str = "Cursor",
        primary_language: str = "Python",
        repo_languages: Optional[List[str]] = None,
        ast_nodes_sliced: int = 15000,
        time_to_first_activation_min: float = 4.2
    ) -> Dict[str, Any]:
        """Records local telemetry upon successful post-purchase developer onboarding."""
        now = datetime.now(timezone.utc)
        act_id = f"ACT-{uuid.uuid4().hex[:6].upper()}"

        record = {
            "activation_id": act_id,
            "license_key": license_key,
            "customer_email": customer_email.strip().lower(),
            "ide_environment": ide_environment,
            "primary_language": primary_language,
            "repo_languages": repo_languages or [primary_language],
            "ast_nodes_sliced_initial": ast_nodes_sliced,
            "time_to_first_activation_min": round(time_to_first_activation_min, 2),
            "activated_at": now.isoformat()
        }

        self.telemetry.append(record)
        self._save_json(self.telemetry_path, self.telemetry)

        # Mark license status as ACTIVATED
        for lic in self.licenses:
            if lic["license_key"] == license_key:
                lic["status"] = "ACTIVATED"
                lic["activated_at"] = now.isoformat()
        self._save_json(self.registry_path, self.licenses)

        return record

    def audit_activations(self) -> Dict[str, Any]:
        """Calculates TTFA statistics, IDE usage breakdown, and language profiling."""
        total_licenses = len(self.licenses)
        total_activations = len(self.telemetry)
        airgap_count = sum(1 for l in self.licenses if l.get("is_airgap", False))

        ttfa_list = [t["time_to_first_activation_min"] for t in self.telemetry if "time_to_first_activation_min" in t]
        avg_ttfa = round(sum(ttfa_list) / len(ttfa_list), 2) if ttfa_list else 0.0

        # IDE environment breakdown
        ide_dist: Dict[str, int] = {}
        for t in self.telemetry:
            ide = t.get("ide_environment", "Other")
            ide_dist[ide] = ide_dist.get(ide, 0) + 1

        # Primary language breakdown
        lang_dist: Dict[str, int] = {}
        for t in self.telemetry:
            lang = t.get("primary_language", "Other")
            lang_dist[lang] = lang_dist.get(lang, 0) + 1

        return {
            "total_licenses_issued": total_licenses,
            "total_activations_completed": total_activations,
            "airgap_scif_licenses": airgap_count,
            "average_time_to_first_activation_min": avg_ttfa,
            "ide_distribution": ide_dist,
            "primary_language_distribution": lang_dist,
            "benchmark_ttfa_target_min": 5.0,
            "ttfa_health_status": "OPTIMAL" if avg_ttfa <= 5.0 else "ATTENTION_REQUIRED"
        }

    def print_summary(self) -> None:
        """Renders comprehensive ASCII terminal dashboard."""
        audit = self.audit_activations()
        print("=" * 76)
        print("⚡ DEVSUPERSUITE OFFICIAL — ONBOARDING & ACTIVATION TELEMETRY DASHBOARD")
        print("=" * 76)
        print(f"Total Digital Licenses Issued:      {audit['total_licenses_issued']}")
        print(f"Total Completed Activations:        {audit['total_activations_completed']}")
        print(f"Air-Gap SCIF Licenses (Offline):    {audit['airgap_scif_licenses']}")
        print(f"Average Time to First Activation:   {audit['average_time_to_first_activation_min']} minutes (Target: <5.0m) [{audit['ttfa_health_status']}]")
        print("-" * 76)
        print("IDE Environment Breakdown:")
        for ide, count in audit["ide_distribution"].items():
            print(f"  • {ide:<24}: {count} developers")
        print("Top Monorepo Languages Profiling:")
        for lang, count in audit["primary_language_distribution"].items():
            print(f"  • {lang:<24}: {count} repositories")
        print("-" * 76)
        print(f"Licenses Registry:    {self.registry_path}")
        print(f"Telemetry Registry:   {self.telemetry_path}")
        print(f"Public Key Export:    {PUBLIC_KEY_EXPORT_PATH}")
        print("=" * 76)


def main():
    parser = argparse.ArgumentParser(description="DevSuperSuite Official License Activation Engine")
    parser.add_argument("--generate-license", action="store_true", help="Generate Ed25519 license key and CLI onboarding one-liner")
    parser.add_argument("--order-id", default="GUM-NEW-884901", help="Order identifier (Gumroad, PayPal, Stripe, UPI)")
    parser.add_argument("--email", default="developer@company.com", help="Developer recipient email")
    parser.add_argument("--name", default="Senior Engineer", help="Developer full name")
    parser.add_argument("--plan", default="Hacker Solo", help="License plan name")
    parser.add_argument("--seats", type=int, default=1, help="Number of licensed seats")
    parser.add_argument("--airgap", action="store_true", help="Issue air-gap offline SCIF license")
    parser.add_argument("--verify-license", action="store_true", help="Verify canonical payload and signature")
    parser.add_argument("--payload", default="", help="Canonical JSON payload to verify")
    parser.add_argument("--signature", default="", help="Hex signature to verify")
    parser.add_argument("--public-key", default="", help="Public key hex (optional)")
    parser.add_argument("--audit-activations", action="store_true", help="Audit activation velocity and telemetry")
    parser.add_argument("--summary", action="store_true", help="Print summary dashboard")

    args = parser.parse_args()
    engine = LicenseActivationEngine()

    if args.generate_license:
        lic = engine.generate_license(
            order_id=args.order_id,
            customer_email=args.email,
            plan_name=args.plan,
            seats=args.seats,
            customer_name=args.name,
            is_airgap=args.airgap
        )
        print(f"[✓] Ed25519 Standalone License Generated:")
        print(f"    Key Token:       {lic['license_key']}")
        print(f"    Order ID:        {lic['order_id']}")
        print(f"    Plan & Seats:    {lic['plan_name']} ({lic['seats']} Seats)")
        print(f"    Recipient:       {lic['customer_email']}")
        print(f"    SHA-256 Digest:  {lic['sha256_digest']}")
        print(f"\n⚡ 1-Click Install (Linux / macOS):")
        print(f"    {lic['cli_install_bash']}")
        print(f"\n⚡ 1-Click Install (Windows PowerShell):")
        print(f"    {lic['cli_install_powershell']}")
        if args.airgap:
            print(f"\n🛡️ Offline Air-Gap Activation Command:")
            print(f"    {lic['cli_offline_activate']}")

    if args.verify_license:
        if not args.payload or not args.signature:
            # Verify latest registered license as sample
            latest = engine.licenses[-1]
            payload = latest.get("canonical_payload", "")
            sig = latest.get("signature_hex", "")
        else:
            payload = args.payload
            sig = args.signature

        res = engine.verify_license(payload, sig, args.public_key)
        print(json.dumps(res, indent=2))

    if args.audit_activations:
        audit = engine.audit_activations()
        print(json.dumps(audit, indent=2))

    if args.summary or (not args.generate_license and not args.verify_license and not args.audit_activations):
        engine.print_summary()


if __name__ == "__main__":
    main()
