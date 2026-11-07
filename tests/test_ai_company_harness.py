"""
Multi-Agent Comprehensive Test Harness for DevSuperSuite Labs
Empirically audits and verifies all operational dimensions:
- MCP Protocol compliance
- Secret scanning & Shannon entropy calculation
- Release ZIP manifest integrity
- Strict Anonymity & PII avoidance
"""

import os
import sys
import json
import zipfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SHIELD_PATH = REPO_ROOT / "build" / "DevSuperSuite" / "agent-shield"
OMNI_PATH = REPO_ROOT / "build" / "DevSuperSuite" / "omni-kernel"
for p in [str(SHIELD_PATH), str(OMNI_PATH)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from agentshield.scanner import ShieldScanner, calculate_shannon_entropy
from agentshield.anonymizer import GitAnonymizer
from agentshield.mcp_server import create_tools_manifest as create_shield_manifest, handle_scan_code_snippet, handle_verify_shield_policy
from omnikernel.compressor import ASTContextCompressor
from omnikernel.invariants import InvariantGuard
from omnikernel.mcp_server import create_tools_manifest as create_omni_manifest, handle_calculate_roi_savings


class TestAICompanyHarness(unittest.TestCase):

    def setUp(self):
        self.scanner = ShieldScanner()

    def test_01_mcp_tools_manifest(self):
        """Validates that MCP tools manifest conforms to Anthropic/MCP standards."""
        tools = create_shield_manifest()
        tool_names = [t["name"] for t in tools]
        self.assertIn("scan_code_snippet", tool_names)
        self.assertIn("anonymize_git_identity", tool_names)
        self.assertIn("inspect_staged_diff", tool_names)
        self.assertIn("verify_shield_policy", tool_names)
        for t in tools:
            self.assertIn("inputSchema", t)
            self.assertEqual(t["inputSchema"]["type"], "object")

        omni_tools = create_omni_manifest()
        omni_names = [t["name"] for t in omni_tools]
        self.assertIn("compress_context", omni_names)
        self.assertIn("audit_patch_invariants", omni_names)
        self.assertIn("calculate_roi_savings", omni_names)

    def test_02_mcp_secret_detection(self):
        """Verifies MCP tool blocks leaked API keys and flags them as LEAK_DETECTED."""
        leaky_prompt = "const apiKey = 'sk-proj-a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8s9T0u1V2w3X4y5Z6';"
        res = handle_scan_code_snippet({"text": leaky_prompt})
        self.assertEqual(res["status"], "LEAK_DETECTED")
        self.assertGreaterEqual(res["findings_count"], 1)
        self.assertEqual(res["findings"][0]["type"], "openai_api_key")

    def test_03_mcp_clean_code_zero_false_positives(self):
        """Verifies harmless code returns SAFE with zero false alarms."""
        clean_code = """
        def compute_fibonacci(n: int) -> int:
            if n <= 1:
                return n
            return compute_fibonacci(n - 1) + compute_fibonacci(n - 2)
        """
        res = handle_scan_code_snippet({"text": clean_code})
        self.assertEqual(res["status"], "SAFE")
        self.assertEqual(res["findings_count"], 0)

    def test_04_shannon_entropy_mathematics(self):
        """Tests Shannon Entropy calculation on known high and low entropy strings."""
        low_ent = calculate_shannon_entropy("aaaaaaaaaaaa")
        self.assertEqual(low_ent, 0.0)

        mid_ent = calculate_shannon_entropy("password")
        self.assertLess(mid_ent, 3.0)

        high_ent = calculate_shannon_entropy("9xK#mQ7$vL2@pZ8!wR4&")
        self.assertGreater(high_ent, 4.0)

    def test_05_strict_anonymity_across_repo(self):
        """Assures zero personal identifiers leak into public codebase."""
        forbidden = [r"\bpratik\b", r"\bmaruti\b", r"\batpadkar\b"]
        leaks = []
        extensions = [".html", ".js", ".md", ".json", ".css", ".py"]

        for root, dirs, files in os.walk(REPO_ROOT):
            if any(x in root for x in [".git", "dist", "node_modules", ".pytest_cache", ".vercel"]):
                continue
            for f in files:
                if any(f.endswith(ext) for ext in extensions):
                    # Skip test file itself matching regex definitions
                    if f == "test_ai_company_harness.py":
                        continue
                    p = Path(root) / f
                    try:
                        content = p.read_text(encoding="utf-8", errors="ignore")
                        for pat in forbidden:
                            matches = re.findall(pat, content, re.IGNORECASE)
                            if matches:
                                leaks.append((str(p.relative_to(REPO_ROOT)), pat, len(matches)))
                    except Exception:
                        pass

        self.assertEqual(len(leaks), 0, f"Identity leaks found: {leaks}")

    def test_06_release_zip_integrity(self):
        """Verifies production ZIP exists, contains required engines, and has proper size."""
        zip_path = REPO_ROOT / "dist" / "DevSuperSuite_Commercial_v1.0.zip"
        self.assertTrue(zip_path.exists())
        self.assertGreater(zip_path.stat().st_size, 50 * 1024)

        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            self.assertTrue(any("live-voice-responder" in n for n in names))
            self.assertTrue(any("agent-shield" in n for n in names))
            self.assertTrue(any("omni-kernel" in n for n in names))
            self.assertTrue(any("Setup_DevSuite.bat" in n for n in names))
            self.assertTrue(any("mcp_server.py" in n for n in names))

    def test_07_omnikernel_ast_compression(self):
        """Verifies OmniKernel AST compressor reduces tokens while preserving signatures."""
        sample_code = '''
def handle_transaction(tx_id: str, amount: float) -> bool:
    """Verifies transaction validity and executes ledger write."""
    log_info("Starting tx", tx_id)
    if amount <= 0:
        raise ValueError("Invalid amount")
    db = get_database_connection()
    tx = db.begin()
    res = tx.execute("UPDATE accounts SET balance = balance + :amt", {"amt": amount})
    tx.commit()
    return True
'''
        comp = ASTContextCompressor()
        compressed, metrics = comp.compress_python(sample_code)
        self.assertIn("handle_transaction", compressed)
        self.assertIn("OmniKernel", compressed)
        self.assertGreater(metrics["tokens_saved"], 0)
        self.assertGreaterEqual(metrics["compression_ratio_pct"], 35.0)

    def test_08_omnikernel_invariant_guard(self):
        """Verifies InvariantGuard detects test deletion and security bypasses."""
        orig = "def test_auth(): pass\ndef test_db(): pass"
        bad_patch = "def test_auth(): pass\nverify = False"
        audit = InvariantGuard.audit_patch(orig, bad_patch)
        self.assertEqual(audit["status"], "VIOLATIONS_FOUND")
        rules_triggered = [v["rule"] for v in audit["violations"]]
        self.assertIn("INVARIANT_TEST_PRESERVATION", rules_triggered)
        self.assertIn("INVARIANT_SECURITY_BYPASS", rules_triggered)

    def test_09_omnikernel_roi_calculator(self):
        """Verifies OmniKernel financial savings calculation."""
        res = handle_calculate_roi_savings({"daily_turns": 100, "avg_tokens_per_turn": 4000})
        self.assertGreater(res["monthly_dollar_savings_usd"], 0.0)
        self.assertGreater(res["annual_dollar_savings_usd"], 0.0)
        self.assertIn("ROI", res["roi_on_license"])


if __name__ == "__main__":
    import re
    unittest.main(verbosity=2)
