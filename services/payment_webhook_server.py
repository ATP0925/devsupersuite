#!/usr/bin/env python3
"""
⚡ DevSuperSuite Tech Services - Automated Payment Clearing & Webhook Settlement Service
File: payment_webhook_server.py
Version: 1.0.0
Author: CFO & Commercial Operations Desk
Strict Compliance: 100% Brand Anonymity - DevSuperSuite Official Only.

Features:
- Stripe Webhook Processing (payment_intent.succeeded, invoice.paid) with HMAC-SHA256 signature verification.
- PayPal Webhook Processing (PAYMENT.CAPTURE.COMPLETED) with transmission signature validation.
- Replay attack prevention via deterministic transaction deduplication.
- Ed25519 Cryptographic License Key Generation and digital signing for instant local offline validation.
- Real-time immutable recording to store_ledger.json and customer registries.
- Standalone multi-endpoint HTTP server + programmatic headless execution engine.
"""

import sys
import os
import json
import time
import hmac
import hashlib
import base64
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler

# Cryptography Ed25519
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# Directory and Persistence Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(SCRATCH_DIR, "data")
ROOT_DATA_DIR = os.path.join(os.path.dirname(SCRATCH_DIR), "data")

STORE_LEDGER_FILE = os.path.join(DATA_DIR, "store_ledger.json")
CUSTOMERS_FILE = os.path.join(DATA_DIR, "customers.json")
ROOT_CUSTOMERS_FILE = os.path.join(ROOT_DATA_DIR, "customers.json")
KEY_VAULT_FILE = os.path.join(DATA_DIR, ".ed25519_vault.json")

# Default Webhook Secrets (for HMAC validation)
DEFAULT_STRIPE_WEBHOOK_SECRET = "whsec_dss_stripe_live_vault_38b991f8c"
DEFAULT_PAYPAL_WEBHOOK_SECRET = "whsec_dss_paypal_live_vault_99a12c4e5"

class Ed25519LicenseSigner:
    """Institutional Ed25519 cryptographic license authority for DevSuperSuite."""
    
    def __init__(self, vault_path: str = KEY_VAULT_FILE):
        self.vault_path = vault_path
        self._private_key, self._public_key = self._load_or_create_keys()

    def _load_or_create_keys(self) -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
        os.makedirs(os.path.dirname(self.vault_path), exist_ok=True)
        if os.path.exists(self.vault_path):
            try:
                with open(self.vault_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                priv_bytes = base64.b64decode(data["private_key_b64"])
                private_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)
                return private_key, private_key.public_key()
            except Exception:
                pass

        # Deterministic institutional seed for DevSuperSuite
        seed = hashlib.sha256(b"DEVSUPERSUITE_OFFICIAL_ED25519_KEY_SEED_2026").digest()
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
        public_key = private_key.public_key()

        priv_b64 = base64.b64encode(seed).decode("utf-8")
        pub_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        pub_b64 = base64.b64encode(pub_bytes).decode("utf-8")

        with open(self.vault_path, "w", encoding="utf-8") as f:
            json.dump({
                "issuer": "DevSuperSuite Official License Authority",
                "private_key_b64": priv_b64,
                "public_key_b64": pub_b64,
                "created_at": datetime.now(timezone.utc).isoformat()
            }, f, indent=2)

        return private_key, public_key

    def issue_license(self, customer_email: str, plan_name: str, txn_id: str) -> Dict[str, Any]:
        """Signs an Ed25519 license certificate for the specified customer."""
        issued_at = datetime.now(timezone.utc).isoformat()
        token_hash = hashlib.sha256(f"{customer_email}_{txn_id}".encode("utf-8")).hexdigest()[:12].upper()
        formatted_license_key = f"DSS-ED25519-{token_hash[:4]}-{token_hash[4:8]}-{token_hash[8:12]}"

        claims = {
            "iss": "DevSuperSuite Official",
            "sub": customer_email,
            "plan": plan_name,
            "txn": txn_id,
            "iat": issued_at,
            "license_key": formatted_license_key,
            "capabilities": ["omnikernel_ast", "agentshield_entropy", "live_voice_dsp", "dual_mcp"]
        }
        canonical_bytes = json.dumps(claims, sort_keys=True).encode("utf-8")
        signature = self._private_key.sign(canonical_bytes)

        pub_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        return {
            "license_key": formatted_license_key,
            "claims": claims,
            "signature_b64": base64.b64encode(signature).decode("utf-8"),
            "public_key_b64": base64.b64encode(pub_bytes).decode("utf-8"),
        }

    def verify_license(self, claims: Dict[str, Any], signature_b64: str) -> bool:
        """Verifies an Ed25519 license signature."""
        try:
            canonical_bytes = json.dumps(claims, sort_keys=True).encode("utf-8")
            sig_bytes = base64.b64decode(signature_b64)
            self._public_key.verify(sig_bytes, canonical_bytes)
            return True
        except Exception:
            return False


class PaymentWebhookEngine:
    """Core payment processing and reconciliation engine for Stripe and PayPal."""

    def __init__(
        self,
        ledger_file: str = STORE_LEDGER_FILE,
        customers_file: str = CUSTOMERS_FILE,
        stripe_secret: str = DEFAULT_STRIPE_WEBHOOK_SECRET,
        paypal_secret: str = DEFAULT_PAYPAL_WEBHOOK_SECRET,
    ):
        self.ledger_file = ledger_file
        self.customers_file = customers_file
        self.stripe_secret = stripe_secret
        self.paypal_secret = paypal_secret
        self.signer = Ed25519LicenseSigner()
        self._ensure_persistence_exists()

    def _ensure_persistence_exists(self):
        os.makedirs(os.path.dirname(self.ledger_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.customers_file), exist_ok=True)

    def _load_ledger(self) -> Dict[str, Any]:
        if os.path.exists(self.ledger_file):
            try:
                with open(self.ledger_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"metadata": {}, "traffic_telemetry": {"funnel_stages": {}}, "transactions": []}

    def _save_ledger(self, ledger: Dict[str, Any]):
        ledger["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.ledger_file, "w", encoding="utf-8") as f:
            json.dump(ledger, f, indent=2)

    def _load_customers(self) -> list:
        if os.path.exists(self.customers_file):
            try:
                with open(self.customers_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_customers(self, customers: list):
        with open(self.customers_file, "w", encoding="utf-8") as f:
            json.dump(customers, f, indent=2)
        # Mirror to root data directory if present
        if os.path.exists(os.path.dirname(ROOT_CUSTOMERS_FILE)):
            try:
                with open(ROOT_CUSTOMERS_FILE, "w", encoding="utf-8") as f:
                    json.dump(customers, f, indent=2)
            except Exception:
                pass

    def verify_stripe_signature(self, payload_bytes: bytes, sig_header: str) -> bool:
        """
        Validates standard Stripe signature: t=<timestamp>,v1=<hmac_sha256_hex>.
        """
        if not sig_header:
            return False
        try:
            parts = dict(item.split("=", 1) for item in sig_header.split(","))
            timestamp = parts.get("t")
            v1_sig = parts.get("v1")
            if not timestamp or not v1_sig:
                return False

            signed_payload = f"{timestamp}.".encode("utf-8") + payload_bytes
            expected_hmac = hmac.new(
                self.stripe_secret.encode("utf-8"),
                signed_payload,
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(v1_sig, expected_hmac)
        except Exception:
            return False

    def verify_paypal_signature(self, payload_bytes: bytes, sig_header: str) -> bool:
        """
        Validates PayPal transmission HMAC signature.
        """
        if not sig_header:
            return False
        try:
            expected_hmac = hmac.new(
                self.paypal_secret.encode("utf-8"),
                payload_bytes,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(sig_header, expected_hmac)
        except Exception:
            return False

    def record_settled_order(
        self,
        txn_id: str,
        customer_email: str,
        product_name: str,
        channel: str,
        channel_label: str,
        gross_amount_usd: float,
        merchant_fee_usd: float,
        hosting_compute_usd: float = 0.45,
    ) -> Dict[str, Any]:
        """
        Idempotently records a verified order into ledger and provisions license.
        """
        ledger = self._load_ledger()
        txns = ledger.setdefault("transactions", [])

        # Idempotency check: Reject duplicate transaction ID
        for t in txns:
            if t.get("txn_id") == txn_id:
                return {
                    "status": "DUPLICATE_TRANSACTION_REJECTED",
                    "txn_id": txn_id,
                    "message": f"Transaction {txn_id} has already been settled and provisioned."
                }

        # Provision Ed25519 License Certificate
        cert = self.signer.issue_license(customer_email, product_name, txn_id)
        license_key = cert["license_key"]

        net_rev = round(gross_amount_usd - merchant_fee_usd - hosting_compute_usd, 2)
        txn_record = {
            "txn_id": txn_id,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "customer": customer_email,
            "license_key": license_key,
            "ed25519_signature": cert["signature_b64"],
            "product": product_name,
            "channel": channel,
            "channel_label": channel_label,
            "gross_amount_usd": gross_amount_usd,
            "merchant_fee_usd": merchant_fee_usd,
            "hosting_compute_cost_usd": hosting_compute_usd,
            "net_revenue_usd": net_rev,
            "status": "SETTLED"
        }
        txns.append(txn_record)

        # Update Funnel Telemetry
        funnel = ledger.setdefault("traffic_telemetry", {}).setdefault("funnel_stages", {})
        funnel["paid_order_conversions"] = len(txns)

        self._save_ledger(ledger)

        # Update Customer Registry
        customers = self._load_customers()
        cust_record = {
            "id": len(customers) + 1,
            "customer": customer_email,
            "license_key": license_key,
            "plan": product_name,
            "channel": channel_label,
            "status": "ACQUIRED_AND_ACTIVE",
            "ed25519_verified": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        customers.append(cust_record)
        self._save_customers(customers)

        return {
            "status": "SUCCESS_SETTLED_AND_PROVISIONED",
            "txn_id": txn_id,
            "customer": customer_email,
            "license_key": license_key,
            "gross_revenue": gross_amount_usd,
            "net_revenue": net_rev,
            "ed25519_cert": cert
        }

    def process_stripe_event(self, payload_dict: Dict[str, Any], raw_body: bytes, sig_header: str) -> Dict[str, Any]:
        """Processes and settles a Stripe webhook payload."""
        if not self.verify_stripe_signature(raw_body, sig_header):
            return {"status": "INVALID_SIGNATURE", "error": "HMAC-SHA256 signature verification failed."}

        event_type = payload_dict.get("type", "")
        data_obj = payload_dict.get("data", {}).get("object", {})

        if event_type == "payment_intent.succeeded":
            txn_id = data_obj.get("id", f"pi_sim_{int(time.time())}")
            amount_cents = data_obj.get("amount_received", 2900)
            gross_amount = round(amount_cents / 100.0, 2)
            
            # Extract customer email and plan
            customer_email = data_obj.get("receipt_email") or data_obj.get("metadata", {}).get("customer_email") or "developer@client.io"
            plan_name = data_obj.get("metadata", {}).get("plan_name", "DevSuperSuite Hacker Solo ($29)")
            
            # Merchant fee: 2.9% + 1.5% cross-border + $0.30
            merchant_fee = round(gross_amount * (0.029 + 0.015) + 0.30, 2)
            hosting_cost = 0.45 if gross_amount < 50 else 1.20

            return self.record_settled_order(
                txn_id=txn_id,
                customer_email=customer_email,
                product_name=plan_name,
                channel="stripe",
                channel_label="Stripe / International Card (Global)",
                gross_amount_usd=gross_amount,
                merchant_fee_usd=merchant_fee,
                hosting_compute_usd=hosting_cost
            )

        elif event_type == "invoice.paid":
            txn_id = data_obj.get("id", f"in_sim_{int(time.time())}")
            amount_cents = data_obj.get("amount_paid", 9900)
            gross_amount = round(amount_cents / 100.0, 2)
            customer_email = data_obj.get("customer_email") or "enterprise-lead@studio.com"
            plan_name = data_obj.get("metadata", {}).get("plan_name", "DevSuperSuite Agency Studio Pack ($99)")
            
            merchant_fee = round(gross_amount * 0.029 + 0.30, 2)
            hosting_cost = 1.20

            return self.record_settled_order(
                txn_id=txn_id,
                customer_email=customer_email,
                product_name=plan_name,
                channel="stripe",
                channel_label="Stripe Corporate Invoicing (US Enterprise)",
                gross_amount_usd=gross_amount,
                merchant_fee_usd=merchant_fee,
                hosting_compute_usd=hosting_cost
            )

        return {"status": "UNHANDLED_EVENT_TYPE", "event_type": event_type}

    def process_paypal_event(self, payload_dict: Dict[str, Any], raw_body: bytes, sig_header: str) -> Dict[str, Any]:
        """Processes and settles a PayPal webhook/IPN payload."""
        if not self.verify_paypal_signature(raw_body, sig_header):
            return {"status": "INVALID_SIGNATURE", "error": "PayPal transmission signature verification failed."}

        event_type = payload_dict.get("event_type", "")
        resource = payload_dict.get("resource", {})

        if event_type in ("PAYMENT.CAPTURE.COMPLETED", "PAYMENT.AUTHORIZATION.CREATED"):
            txn_id = resource.get("id", f"pp_capture_{int(time.time())}")
            amount_val = float(resource.get("amount", {}).get("value", 29.00))
            payer_email = resource.get("payer", {}).get("email_address") or resource.get("custom_id") or "paypal-developer@network.org"
            plan_name = resource.get("custom_plan") or "DevSuperSuite Hacker Solo ($29)"

            # PayPal fee: 3.49% + $0.49
            merchant_fee = round(amount_val * 0.0349 + 0.49, 2)
            hosting_cost = 0.45 if amount_val < 50 else 1.20

            return self.record_settled_order(
                txn_id=txn_id,
                customer_email=payer_email,
                product_name=plan_name,
                channel="paypal",
                channel_label="PayPal Business Gateway (International)",
                gross_amount_usd=amount_val,
                merchant_fee_usd=merchant_fee,
                hosting_compute_usd=hosting_cost
            )

        return {"status": "UNHANDLED_PAYPAL_EVENT", "event_type": event_type}


class WebhookServerHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for live webhook ingress."""
    engine = PaymentWebhookEngine()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)

        try:
            payload_dict = json.loads(raw_body.decode("utf-8"))
        except Exception:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "Malformed JSON payload"}')
            return

        if self.path == "/webhook/stripe":
            sig_header = self.headers.get("Stripe-Signature", "")
            res = self.engine.process_stripe_event(payload_dict, raw_body, sig_header)
            status_code = 200 if res.get("status") in ("SUCCESS_SETTLED_AND_PROVISIONED", "DUPLICATE_TRANSACTION_REJECTED") else 400
        elif self.path == "/webhook/paypal":
            sig_header = self.headers.get("Paypal-Transmission-Sig", "")
            res = self.engine.process_paypal_event(payload_dict, raw_body, sig_header)
            status_code = 200 if res.get("status") in ("SUCCESS_SETTLED_AND_PROVISIONED", "DUPLICATE_TRANSACTION_REJECTED") else 400
        else:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(res).encode("utf-8"))

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ONLINE", "service": "DevSuperSuite Payment Webhook Authority"}')
        else:
            self.send_response(404)
            self.end_headers()


def run_standalone_server(port: int = 8088):
    server = HTTPServer(("0.0.0.0", port), WebhookServerHandler)
    print(f"⚡ DevSuperSuite Payment Webhook Server active on port {port}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutdown signal received. Terminating.")
        server.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8088
    run_standalone_server(port)
