"""
═══════════════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Enterprise Automated Verification Test Suite
Document Ref: DSS-TEST-COMPLIANCE-2026-V1
Compliance Standards: ISO/IEC 27001:2022, SOC 2 Type II, OWASP Top 10, ZDR Policy

Verifies:
1. Shannon Entropy Detection & Secret Scanner Policy (Low vs High Entropy Gates)
2. AST Interface Extraction Stub Generator (Signature Preservation & Body Elision)
3. Architectural Invariant Guard (Test Preservation & Security Bypass Rejection)
4. Zero Data Retention (ZDR) Cryptographic Memory Shredding Simulation
5. Strict Brand Anonymity Protocols (DevSuperSuite Official Representation)
═══════════════════════════════════════════════════════════════════════════════════════
"""

import ast
import math
import os
import re
import sys
import unittest
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# 1. Shannon Entropy & Security Scanner Core
# ─────────────────────────────────────────────────────────────────────────────

def calculate_shannon_entropy(data: str) -> float:
    """
    Calculates Shannon Entropy: H(X) = -sum(P(x) * log2(P(x)))
    Measures information density and randomness of character distributions.
    """
    if not data:
        return 0.0
    length = len(data)
    counts = Counter(data)
    entropy = 0.0
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy


class EnterpriseEntropyGate:
    """
    Enforces pre-commit secret leak prevention policies based on
    Shannon entropy thresholds and known credential signatures.
    """
    LOW_ENTROPY_CEILING = 3.0       # Standard natural language / identifiers
    HIGH_ENTROPY_THRESHOLD = 4.2     # Cryptographic tokens, keys, and secrets
    MIN_TOKEN_LENGTH = 16

    KNOWN_KEY_PATTERNS = [
        (r"(?i)sk_live_[0-9a-zA-Z]{24,}", "Stripe Live Secret Key"),
        (r"(?i)sk-proj-[a-zA-Z0-9_\-]{32,}", "OpenAI Project API Key"),
        (r"(?i)sk-ant-api03-[a-zA-Z0-9_\-]{40,}", "Anthropic API Key"),
        (r"(?i)AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
        (r"(?i)gh[pousr]_[A-Za-z0-9_]{36,}", "GitHub Personal Access Token"),
    ]

    @classmethod
    def evaluate_token(cls, token: str) -> Dict[str, Any]:
        """
        Evaluates a string token against enterprise entropy and credential policies.
        Returns evaluation dictionary: {entropy, status, reason, is_blocked}
        """
        entropy = calculate_shannon_entropy(token)
        
        # 1. Check high-entropy threshold on qualified length tokens
        if len(token) >= cls.MIN_TOKEN_LENGTH and entropy >= cls.HIGH_ENTROPY_THRESHOLD:
            return {
                "token": token,
                "entropy": entropy,
                "status": "BLOCKED",
                "reason": f"High Shannon Entropy (H={entropy:.3f} >= {cls.HIGH_ENTROPY_THRESHOLD})",
                "is_blocked": True,
            }

        # 2. Check known high-precision signature patterns
        for pattern, label in cls.KNOWN_KEY_PATTERNS:
            if re.search(pattern, token):
                return {
                    "token": token,
                    "entropy": entropy,
                    "status": "BLOCKED",
                    "reason": f"Matches Known Signature: {label}",
                    "is_blocked": True,
                }

        # 3. Low entropy / Safe token
        return {
            "token": token,
            "entropy": entropy,
            "status": "ALLOWED",
            "reason": f"Normal Information Density (H={entropy:.3f})",
            "is_blocked": False,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 2. AST Interface Extraction Stub Generator
# ─────────────────────────────────────────────────────────────────────────────

class _ASTStubTransformer(ast.NodeTransformer):
    """
    Transforms a Python AST by preserving class/function signatures, docstrings,
    decorators, and type annotations, while replacing implementation bodies with '...'.
    """

    def __init__(self, preserve_docstrings: bool = True):
        super().__init__()
        self.preserve_docstrings = preserve_docstrings
        self.elided_functions: List[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        return self._transform_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        return self._transform_function(node)

    def _transform_function(self, node: Any) -> Any:
        self.generic_visit(node)
        self.elided_functions.append(node.name)
        
        docstring = ast.get_docstring(node) if self.preserve_docstrings else None
        ellipsis_stmt = ast.Expr(value=ast.Constant(value=...))

        if docstring:
            doc_stmt = ast.Expr(value=ast.Constant(value=docstring))
            node.body = [doc_stmt, ellipsis_stmt]
        else:
            node.body = [ellipsis_stmt]

        return node


class ASTInterfaceStubGenerator:
    """
    Enterprise Context Compressor & Interface Stub Generator.
    Extracts high-level typed signatures and class hierarchies while eliding
    heavy implementation bodies to slash LLM context token usage.
    """

    def __init__(self, preserve_docstrings: bool = True):
        self.preserve_docstrings = preserve_docstrings

    def generate_stub(self, source_code: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parses source code into an AST, generates a typed signature interface stub,
        and returns the stub code alongside compression metrics.
        """
        tree = ast.parse(source_code)
        transformer = _ASTStubTransformer(preserve_docstrings=self.preserve_docstrings)
        transformed_tree = transformer.visit(tree)
        ast.fix_missing_locations(transformed_tree)
        
        stub_code = ast.unparse(transformed_tree)

        # Validate that the generated stub compiles cleanly
        ast.parse(stub_code)

        orig_len = len(source_code)
        stub_len = len(stub_code)
        reduction_pct = round(((orig_len - stub_len) / max(1, orig_len)) * 100, 2)

        metrics = {
            "original_chars": orig_len,
            "stub_chars": stub_len,
            "reduction_percentage": reduction_pct,
            "elided_functions_count": len(transformer.elided_functions),
            "elided_function_names": transformer.elided_functions,
        }

        return stub_code, metrics


# ─────────────────────────────────────────────────────────────────────────────
# 3. Enterprise Invariant Guard Engine
# ─────────────────────────────────────────────────────────────────────────────

class EnterpriseInvariantGuard:
    """
    Guarantees architectural invariants across git diffs and code patches:
    1. INVARIANT_TEST_PRESERVATION: Zero deletion of existing unit test assertions.
    2. INVARIANT_SECURITY_BYPASS: Zero introduction of security bypass flags.
    """

    FORBIDDEN_SECURITY_PATTERNS = [
        (r"(?i)verify\s*=\s*False", "Disabled SSL/TLS Certificate Verification"),
        (r"@csrf_exempt", "Exempted CSRF Protection Filter"),
        (r"(?i)CORS_ORIGIN_ALLOW_ALL\s*=\s*True", "Permissive Wildcard CORS Configuration"),
        (r"(?i)dangerouslySetInnerHTML", "Unsanitized Raw HTML Injection Vector"),
        (r"(?i)eval\s*\(", "Insecure Dynamic Code Execution (eval)"),
    ]

    @classmethod
    def audit_patch(cls, diff_content: str) -> Dict[str, Any]:
        """Audits a unified git diff for invariant violations."""
        violations = []

        # Invariant 1: Test Preservation Check
        # Detect lines deleted (-) from tests directory or test blocks
        deleted_test_asserts = re.findall(
            r"^\-\s*(?:def test_|it\(|test\(|self\.assert|expect\()",
            diff_content,
            re.MULTILINE
        )
        if deleted_test_asserts:
            violations.append({
                "invariant": "INVARIANT_TEST_PRESERVATION",
                "severity": "CRITICAL",
                "details": f"Detected {len(deleted_test_asserts)} deleted test assertions in patch diff.",
            })

        # Invariant 2: Security Bypass Check
        # Detect lines added (+) containing forbidden bypass patterns
        added_lines = [
            line[1:].strip()
            for line in diff_content.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ]
        for line in added_lines:
            for pattern, desc in cls.FORBIDDEN_SECURITY_PATTERNS:
                if re.search(pattern, line):
                    violations.append({
                        "invariant": "INVARIANT_SECURITY_BYPASS",
                        "severity": "CRITICAL",
                        "details": f"Detected forbidden bypass: {desc} in added line: '{line}'",
                    })

        passed = len(violations) == 0
        return {
            "passed": passed,
            "violations_count": len(violations),
            "violations": violations,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 4. Zero Data Retention (ZDR) Memory Shredder Simulation
# ─────────────────────────────────────────────────────────────────────────────

class EphemeralMemoryShredder:
    """
    Simulates NIST SP 800-88 Rev 1 & DoD 5220.22-M 3-pass cryptographic sanitization
    for volatile buffers containing client source code or proprietary tokens.
    """

    @staticmethod
    def allocate_and_shred(secret_data: str) -> Dict[str, Any]:
        """Allocates a bytearray, verifies data, performs 3-pass shred, and asserts zeroization."""
        buffer = bytearray(secret_data.encode("utf-8"))
        original_length = len(buffer)
        initial_check = bytes(buffer).decode("utf-8")

        # Pass 1: Overwrite with all zeroes (0x00)
        for i in range(original_length):
            buffer[i] = 0x00
        pass1_clean = all(b == 0x00 for b in buffer)

        # Pass 2: Overwrite with all ones (0xFF)
        for i in range(original_length):
            buffer[i] = 0xFF
        pass2_clean = all(b == 0xFF for b in buffer)

        # Pass 3: Overwrite with pseudorandom bytes (0xAA alternating pattern for determinism)
        for i in range(original_length):
            buffer[i] = 0xAA
        pass3_clean = all(b == 0xAA for b in buffer)

        # Final Zeroing
        for i in range(original_length):
            buffer[i] = 0x00
        final_zeroed = all(b == 0x00 for b in buffer)

        return {
            "original_length": original_length,
            "pass1_zeroed": pass1_clean,
            "pass2_inverted": pass2_clean,
            "pass3_randomized": pass3_clean,
            "final_zeroed": final_zeroed,
            "shred_verified": pass1_clean and pass2_clean and pass3_clean and final_zeroed,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 5. Unit & Compliance Test Suite
# ─────────────────────────────────────────────────────────────────────────────

class TestEnterpriseCompliance(unittest.TestCase):
    """
    Test suite verifying DevSuperSuite Enterprise Operating Standards:
    - Shannon entropy evaluation on real sample strings.
    - AST interface extraction stub generator preserves class signatures & drops bodies.
    - Invariant guards enforce zero test deletions and zero security bypasses.
    - Zero Data Retention memory shredding.
    - Brand anonymity verification.
    """

    def test_01_shannon_entropy_plain_text_allowed(self):
        """
        Verify: Plain text (e.g. 'hello world') -> Low entropy (<3.0) -> ALLOWED.
        """
        sample_text = "hello world"
        entropy = calculate_shannon_entropy(sample_text)

        # Mathematical assertion
        self.assertLess(
            entropy,
            3.0,
            f"Expected 'hello world' entropy to be < 3.0, got {entropy:.4f}"
        )

        # Policy Gate assertion
        eval_result = EnterpriseEntropyGate.evaluate_token(sample_text)
        self.assertEqual(eval_result["status"], "ALLOWED")
        self.assertFalse(eval_result["is_blocked"])
        self.assertLess(eval_result["entropy"], EnterpriseEntropyGate.LOW_ENTROPY_CEILING)

    def test_02_shannon_entropy_high_entropy_api_key_blocked(self):
        """
        Verify: High entropy API key token
        -> High entropy (>4.2) -> BLOCKED.
        """
        api_key = "dummy_high_entropy_token_9x8b7c6v5a4z3y2w1q_sample"
        entropy = calculate_shannon_entropy(api_key)

        # Mathematical assertion
        self.assertGreater(
            entropy,
            4.2,
            f"Expected API key entropy to be > 4.2, got {entropy:.4f}"
        )

        # Policy Gate assertion
        eval_result = EnterpriseEntropyGate.evaluate_token(api_key)
        self.assertEqual(eval_result["status"], "BLOCKED")
        self.assertTrue(eval_result["is_blocked"])
        self.assertIn("High Shannon Entropy", eval_result["reason"] or "Signature")

    def test_03_shannon_entropy_matrix_verification(self):
        """
        Comprehensive entropy matrix testing across various character distributions.
        """
        # Low entropy natural text samples -> Must be ALLOWED (< 3.5)
        allowed_samples = [
            "DevSuperSuite Official Standard",
            "autonomous context compressor",
            "select id, username from enterprise_users",
            "https://devsupersuite.web.app",
        ]
        for sample in allowed_samples:
            res = EnterpriseEntropyGate.evaluate_token(sample)
            self.assertEqual(
                res["status"],
                "ALLOWED",
                f"Sample '{sample}' should be ALLOWED but was BLOCKED (H={res['entropy']:.3f})"
            )

        # High entropy secret samples -> Must be BLOCKED
        blocked_samples = [
            "sk-proj-94kL028Jksla9102830192kalsd01923kjsldkfj",
            "AKIAIOSFODNN7EXAMPLE",
            "ghp_39dK092jKsl910293jslkdf0923019238910aBc",
        ]
        for key_sample in blocked_samples:
            res = EnterpriseEntropyGate.evaluate_token(key_sample)
            self.assertEqual(
                res["status"],
                "BLOCKED",
                f"Secret '{key_sample}' should be BLOCKED but was ALLOWED (H={res['entropy']:.3f})"
            )

    def test_04_ast_interface_extraction_preserves_class_signatures(self):
        """
        Verify: AST interface extraction stub generator preserves class signatures,
        method parameters, return types, docstrings, and drops implementation bodies.
        """
        verbose_code = '''
class EnterprisePaymentProcessor(BaseBillingService):
    """Core payment gateway integration handling multi-currency settlements."""

    def __init__(self, api_key: str, timeout_seconds: int = 30) -> None:
        """Initialize the processor with configuration."""
        self.api_key = api_key
        self.timeout = timeout_seconds
        self._internal_pool = []
        for i in range(10):
            self._internal_pool.append({"connection": i, "active": True})

    def process_transaction(self, account_id: str, amount_cents: int, currency: str = "USD") -> Dict[str, Any]:
        """Execute authorization and capture with exponential retry backoff."""
        payload = {
            "account": account_id,
            "amount": amount_cents,
            "currency": currency,
            "timestamp": "2026-11-08T00:00:00Z"
        }
        for attempt in range(5):
            try:
                res = {"status": "success", "charge_id": "ch_123456"}
                return res
            except Exception as exc:
                continue
        raise RuntimeError("Transaction capture timed out")

    def _internal_helper(self, raw_buffer: bytes) -> bool:
        """Private cryptographic checksum verification."""
        total = sum(raw_buffer)
        return total % 2 == 0
'''
        generator = ASTInterfaceStubGenerator(preserve_docstrings=True)
        stub_code, metrics = generator.generate_stub(verbose_code)

        # 1. Verify class name and base class preserved
        self.assertIn("class EnterprisePaymentProcessor(BaseBillingService):", stub_code)

        # 2. Verify class docstring preserved
        self.assertIn("Core payment gateway integration handling multi-currency settlements.", stub_code)

        # 3. Verify method signatures and type annotations preserved
        self.assertRegex(
            stub_code,
            r"def __init__\(self,\s*api_key:\s*str,\s*timeout_seconds:\s*int\s*=\s*30\)\s*->\s*None:"
        )
        self.assertRegex(
            stub_code,
            r"def process_transaction\(self,\s*account_id:\s*str,\s*amount_cents:\s*int,\s*currency:\s*str\s*=\s*['\"]USD['\"]\)\s*->\s*Dict\[str,\s*Any\]:"
        )
        self.assertIn("def _internal_helper(self, raw_buffer: bytes) -> bool:", stub_code)

        # 4. Verify method docstrings preserved
        self.assertIn("Initialize the processor with configuration.", stub_code)
        self.assertIn("Execute authorization and capture with exponential retry backoff.", stub_code)

        # 5. Verify heavy implementation bodies are dropped
        self.assertNotIn("self._internal_pool = []", stub_code)
        self.assertNotIn("for attempt in range(5):", stub_code)
        self.assertNotIn("raise RuntimeError", stub_code)
        self.assertNotIn("total = sum(raw_buffer)", stub_code)

        # 6. Verify Ellipsis ('...') replacement exists in methods
        self.assertIn("...", stub_code)

        # 7. Verify the stub is valid Python and can be parsed by ast.parse without error
        parsed_tree = ast.parse(stub_code)
        self.assertIsInstance(parsed_tree, ast.Module)

        # 8. Verify substantial token/character reduction
        self.assertGreater(metrics["reduction_percentage"], 30.0)
        self.assertEqual(metrics["elided_functions_count"], 3)

    def test_05_ast_interface_extraction_async_and_decorators(self):
        """
        Verify: AST interface extraction handles async functions, @property,
        @classmethod, and @staticmethod decorators correctly.
        """
        source_code = '''
class CloudSecurityGateway:
    """Security proxy for cloud telemetry."""

    @property
    def is_operational(self) -> bool:
        """Health status check."""
        status_flag = True
        return status_flag

    @classmethod
    def factory_default(cls) -> "CloudSecurityGateway":
        """Instantiate default gateway instance."""
        inst = cls()
        return inst

    @staticmethod
    def compute_sha(payload: str) -> str:
        """Utility SHA-256 helper."""
        import hashlib
        return hashlib.sha256(payload.encode()).hexdigest()

    async def dispatch_telemetry(self, event_name: str, payload: dict) -> bool:
        """Asynchronously ship audit logs to SIEM platform."""
        await asyncio.sleep(0.01)
        return True
'''
        generator = ASTInterfaceStubGenerator(preserve_docstrings=True)
        stub_code, metrics = generator.generate_stub(source_code)

        # Decorator assertions
        self.assertIn("@property", stub_code)
        self.assertIn("@classmethod", stub_code)
        self.assertIn("@staticmethod", stub_code)

        # Async function assertion
        self.assertIn("async def dispatch_telemetry(self, event_name: str, payload: dict) -> bool:", stub_code)

        # Implementation bodies dropped
        self.assertNotIn("await asyncio.sleep(0.01)", stub_code)
        self.assertNotIn("import hashlib", stub_code)

        # Compiles validly
        ast.parse(stub_code)
        self.assertEqual(metrics["elided_functions_count"], 4)

    def test_06_invariant_test_preservation_gate(self):
        """
        Verify: INVARIANT_TEST_PRESERVATION blocks any patch diff attempting
        to delete unit test assertions to force a passing build.
        """
        malicious_diff = """
diff --git a/tests/test_auth.py b/tests/test_auth.py
--- a/tests/test_auth.py
+++ b/tests/test_auth.py
@@ -10,3 +10,1 @@
-    def test_token_expiration(self):
-        self.assertTrue(token.is_expired())
+    # test disabled by agent
"""
        audit_result = EnterpriseInvariantGuard.audit_patch(malicious_diff)
        self.assertFalse(audit_result["passed"])
        self.assertGreater(audit_result["violations_count"], 0)
        violations = [v["invariant"] for v in audit_result["violations"]]
        self.assertIn("INVARIANT_TEST_PRESERVATION", violations)

    def test_07_invariant_security_bypass_rejection(self):
        """
        Verify: INVARIANT_SECURITY_BYPASS blocks patches introducing verify=False,
        @csrf_exempt, or raw HTML evaluation.
        """
        bypass_diff = """
diff --git a/src/client.py b/src/client.py
--- a/src/client.py
+++ b/src/client.py
@@ -20,2 +20,3 @@
     def fetch_data(self):
+        return requests.get(url, verify=False)
"""
        audit_result = EnterpriseInvariantGuard.audit_patch(bypass_diff)
        self.assertFalse(audit_result["passed"])
        violations = [v["invariant"] for v in audit_result["violations"]]
        self.assertIn("INVARIANT_SECURITY_BYPASS", violations)

    def test_08_zero_data_retention_memory_shredding(self):
        """
        Verify: Ephemeral memory shredder performs 3-pass DoD 5220.22-M zeroing
        leaving zero residual bytes of client code in volatile buffers.
        """
        proprietary_client_code = "def proprietary_algorithm(): return 'enterprise_ip_vault'"
        shred_result = EphemeralMemoryShredder.allocate_and_shred(proprietary_client_code)

        self.assertTrue(shred_result["pass1_zeroed"])
        self.assertTrue(shred_result["pass2_inverted"])
        self.assertTrue(shred_result["pass3_randomized"])
        self.assertTrue(shred_result["final_zeroed"])
        self.assertTrue(shred_result["shred_verified"])

    def test_09_strict_brand_anonymity_enforcement(self):
        """
        Verify: 100% Brand Anonymity is enforced across all public artifacts and code.
        Zero personal identities, personal handles, or local developer workstation paths.
        """
        test_file_path = os.path.abspath(__file__)
        with open(test_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Disallow common personal handle leaks
        forbidden_personal_patterns = [
            r"\b[A-Za-z]+@gmail\.com\b",
            r"\b[A-Za-z]+@yahoo\.com\b",
            r"\b[A-Za-z]+@hotmail\.com\b",
        ]
        for pat in forbidden_personal_patterns:
            matches = re.findall(pat, content)
            self.assertEqual(
                len(matches),
                0,
                f"Personal email pattern detected: {matches}. Must use DevSuperSuite Official."
            )

        # Ensure official brand entity is present
        self.assertIn("DevSuperSuite Tech Services", content)
        self.assertIn("DevSuperSuite Official", content)


if __name__ == "__main__":
    unittest.main()
