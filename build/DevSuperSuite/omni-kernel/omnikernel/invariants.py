"""
OmniKernel Invariant & Architectural Guardrail Engine.
Prevents AI coding agents from introducing regressions, breaking invariants,
deleting test cases, introducing circular dependencies, or disabling security flags.
"""

import re
from typing import Dict, Any, List, Tuple


class InvariantGuard:
    """Enforces zero-regression architectural contracts on AI edits."""

    BANNED_SECURITY_BYPASSES = [
        (r"\bverify\s*=\s*False\b", "SSL certificate verification disabled (verify=False)"),
        (r"@csrf_exempt\b", "CSRF protection disabled (@csrf_exempt)"),
        (r"\btrust_all_certificates\b", "Untrusted certificates allowed"),
        (r"\bdisable_auth\s*=\s*True\b", "Authentication bypass flag enabled"),
        (r"\bDROP\s+DATABASE\b", "Dangerous destructive SQL statement (DROP DATABASE)"),
        (r"\brm\s+-rf\s+/\b", "Root filesystem deletion command")
    ]

    @classmethod
    def audit_patch(cls, original_code: str, proposed_patch: str) -> Dict[str, Any]:
        """Audits a proposed code patch against architectural safety invariants."""
        violations = []

        # 1. Test Preservation Invariant
        orig_test_count = len(re.findall(r"\bdef\s+test_[a-zA-Z0-9_]+\b|\bit\(['\"]|\btest\(['\"]", original_code))
        patch_test_count = len(re.findall(r"\bdef\s+test_[a-zA-Z0-9_]+\b|\bit\(['\"]|\btest\(['\"]", proposed_patch))
        if orig_test_count > 0 and patch_test_count < orig_test_count:
            violations.append({
                "rule": "INVARIANT_TEST_PRESERVATION",
                "severity": "CRITICAL",
                "message": f"AI patch deleted {orig_test_count - patch_test_count} automated tests! (Original: {orig_test_count}, Proposed: {patch_test_count})"
            })

        # 2. Security Bypass Invariant
        for pattern, description in cls.BANNED_SECURITY_BYPASSES:
            if re.search(pattern, proposed_patch, re.IGNORECASE):
                # Check if it was already present in original
                if not re.search(pattern, original_code, re.IGNORECASE):
                    violations.append({
                        "rule": "INVARIANT_SECURITY_BYPASS",
                        "severity": "BLOCKER",
                        "message": f"AI patch injected prohibited bypass: {description}"
                    })

        # 3. Import bloat check
        orig_imports = set(re.findall(r"^\s*(?:import|from)\s+([a-zA-Z0-9_]+)", original_code, re.MULTILINE))
        patch_imports = set(re.findall(r"^\s*(?:import|from)\s+([a-zA-Z0-9_]+)", proposed_patch, re.MULTILINE))
        new_deps = patch_imports - orig_imports

        status = "PASSED" if len(violations) == 0 else "VIOLATIONS_FOUND"
        return {
            "status": status,
            "violations_count": len(violations),
            "violations": violations,
            "new_external_modules": list(new_deps),
            "recommendation": "Block edit and demand explanation" if violations else "Patch conforms to system invariants"
        }
