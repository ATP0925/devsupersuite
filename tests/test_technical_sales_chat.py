import os
import sys
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from services.technical_sales_chat_engine import (
    TechnicalSalesChatEngine,
    TechnicalSalesIntentClassifier,
    IntentType,
    TECHNICAL_KNOWLEDGE_BASE,
    GUMROAD_CHECKOUT_URL,
    LIVE_SANDBOX_URL,
)

class TestTechnicalSalesChatEngine:
    """Test suite for DevSuperSuite Technical Sales Chat Assistant Engine."""

    def setup_method(self):
        self.engine = TechnicalSalesChatEngine()

    def test_01_intent_classification_accuracy(self):
        test_cases = [
            ("How does your AST slicing reduce tokens in large codebases?", IntentType.AST_SLICING_ARCHITECTURE),
            ("Can I run this offline in an isolated air-gapped SCIF environment with zero-telemetry?", IntentType.OFFLINE_AIRGAP),
            ("How does your entropy scanner stop API keys and tokens leaking?", IntentType.SECRET_INTERCEPTION),
            ("How much does the Pro Lifetime license cost and are updates free?", IntentType.PRICING_AND_LICENSING),
            ("What is your refund guarantee if it doesn't work for our stack?", IntentType.REFUND_GUARANTEE),
            ("Hi there, can someone assist me?", IntentType.FALLBACK_GENERAL),
        ]
        for query, expected_intent in test_cases:
            detected_intent, score = TechnicalSalesIntentClassifier.classify(query)
            assert detected_intent == expected_intent, f"Failed for query '{query}': got {detected_intent}, expected {expected_intent}"
            assert score >= 0.0

    def test_02_chat_response_generation(self):
        payload = {
            "session_id": "visitor_test_1",
            "message": "Can we deploy this inside an air-gapped SCIF environment without calling home?",
            "user_email": "dev@enterprise.internal"
        }
        response = self.engine.process_inbound_message(payload)
        assert response is not None
        assert "reply_text" in response
        assert "detected_intent" in response
        assert response["detected_intent"] == IntentType.OFFLINE_AIRGAP
        assert "https://devsupersuite.web.app" in response["reply_text"] or "https://devsupersuite.web.app" in response["cta_url"]
        assert "DevSuperSuite" in response["reply_text"]

    def test_03_pricing_inquiry_contains_discount_cta(self):
        payload = {
            "session_id": "visitor_test_2",
            "message": "Is there any discount or coupon code available for students or indie devs?",
            "user_email": "student@university.edu"
        }
        response = self.engine.process_inbound_message(payload)
        assert response["detected_intent"] == IntentType.PRICING_AND_LICENSING
        assert "VIPDEV5" in response["cta_url"] or "VIPDEV5" in response["reply_text"]
        assert GUMROAD_CHECKOUT_URL in response["cta_url"]

    def test_04_benchmark_intent_accuracy_audit(self):
        audit_res = self.engine.audit_chat_intents()
        assert audit_res["passed"] is True
        assert audit_res["accuracy_percentage"] >= 90.0
        assert audit_res["total_benchmark_inquiries"] >= 6

    def test_05_inbound_chat_simulation(self):
        sim_results = self.engine.simulate_inbound_traffic()
        assert len(sim_results) >= 6
        for item in sim_results:
            assert "session_id" in item
            assert "inbound_query" in item
            assert "detected_intent" in item
            assert "response_id" in item

    def test_06_export_response_knowledge_bank(self, tmp_path):
        target_path = str(tmp_path / "test_knowledge_base.json")
        export_path = self.engine.export_chat_responses(output_path=target_path)
        assert os.path.exists(export_path)
        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert IntentType.AST_SLICING_ARCHITECTURE.value in data
        assert IntentType.PRICING_AND_LICENSING.value in data

    def test_07_brand_anonymity_compliance(self):
        forbidden_patterns = [
            bytes.fromhex("50726174696b").decode("utf-8"),
            bytes.fromhex("4d6172757469").decode("utf-8"),
            bytes.fromhex("41747061646b6172").decode("utf-8"),
            bytes.fromhex("61747061646b617270726174696b").decode("utf-8"),
            bytes.fromhex("37303538").decode("utf-8"),
            bytes.fromhex("38323038").decode("utf-8"),
            bytes.fromhex("39393235").decode("utf-8")
        ]
        files_to_check = [
            os.path.join(REPO_ROOT, "services", "technical_sales_chat_engine.py"),
            os.path.join(REPO_ROOT, "marketing", "cro_live_chat_objection_playbook.md"),
        ]
        for filepath in files_to_check:
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                for pattern in forbidden_patterns:
                    assert pattern.lower() not in content.lower(), f"Forbidden pattern '{pattern}' found in {filepath}"

    def test_08_cli_execution_smoke(self):
        import subprocess
        script_path = os.path.join(REPO_ROOT, "services", "technical_sales_chat_engine.py")
        res = subprocess.run([sys.executable, script_path, "--summary"], capture_output=True, text=True)
        assert res.returncode == 0
        assert "DEVSUPERSUITE OFFICIAL" in res.stdout
