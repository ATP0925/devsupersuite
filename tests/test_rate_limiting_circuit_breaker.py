#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════════
DevSuperSuite Tech Services - Automated Verification Suite: Rate Limiting & Circuit Breaker
Reference: DSS-TEST-RESILIENCE-CB-2026-V1
Target: Continuous Verification of Token Bucket Limiting, Circuit Breaker & Jitter
Contact: DevSuperSuite Information Security (infosec@devsupersuite.com)
Author: Directorate of QA Automation & Security Compliance, DevSuperSuite Official
═══════════════════════════════════════════════════════════════════════════════════
"""

import json
import re
import sys
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = REPO_ROOT / "services"
REPORTS_DIR = SERVICES_DIR / "reports"
DEPLOYMENT_DIR = REPO_ROOT / "deployment"
TESTS_DIR = REPO_ROOT / "tests"

sys.path.insert(0, str(SERVICES_DIR))

from rate_limiting_circuit_breaker_engine import (
    TokenBucketRateLimiter,
    ExponentialBackoffWithJitter,
    SlidingWindowCircuitBreaker,
    RateLimitingCircuitBreakerOrchestrator,
    run_resilience_pipeline,
    RESILIENCE_MD_PATH,
    RESILIENCE_JSON_PATH,
)


class TestRateLimitingCircuitBreaker(unittest.TestCase):
    """
    Continuous regression test suite validating dynamic token bucket rate limiting,
    DDoS burst protection, three-state circuit breakers, and exponential backoff jitter.
    """

    def setUp(self) -> None:
        self.orchestrator = RateLimitingCircuitBreakerOrchestrator(repo_root=REPO_ROOT)

    def test_01_token_bucket_standard_tier_consumption_and_throttling(self) -> None:
        """
        Verifies standard tier token bucket admits up to 100 requests and throttles the 101st.
        """
        limiter = TokenBucketRateLimiter(tier="standard", initial_tokens=100.0)

        # Consume 100 tokens
        for _ in range(100):
            allowed, remaining = limiter.consume(1)
            self.assertTrue(allowed)

        # 101st request must be throttled
        allowed_101, wait_time = limiter.consume(1)
        self.assertFalse(allowed_101)
        self.assertGreater(wait_time, 0.0)

    def test_02_token_bucket_enterprise_tier_bursts(self) -> None:
        """
        Verifies enterprise tier allows bursts up to 1,000 requests before throttling.
        """
        limiter = TokenBucketRateLimiter(tier="enterprise", initial_tokens=1000.0)

        # Consume 1,000 burst tokens
        for _ in range(1000):
            allowed, _ = limiter.consume(1)
            self.assertTrue(allowed)

        # 1001st request must be throttled
        allowed_excess, wait_time = limiter.consume(1)
        self.assertFalse(allowed_excess)
        self.assertGreater(wait_time, 0.0)

    def test_03_token_bucket_refill_dynamics(self) -> None:
        """
        Verifies token bucket refills smoothly over time up to capacity ceiling.
        """
        limiter = TokenBucketRateLimiter(tier="standard", initial_tokens=10.0)
        limiter.consume(10)
        self.assertLess(limiter.tokens, 1.0)

        # Set high refill rate to test replenishment
        limiter.refill_rate = 1000.0
        limiter.last_refill_timestamp = time.perf_counter() - 0.05  # simulated 50ms elapsed
        limiter._refill()

        self.assertGreaterEqual(limiter.tokens, 10.0)
        self.assertLessEqual(limiter.tokens, limiter.capacity)

    def test_04_exponential_backoff_full_jitter_bounds(self) -> None:
        """
        Validates exponential backoff calculation and asserts full jitter bounds.
        """
        engine = ExponentialBackoffWithJitter(base_backoff_ms=100.0, max_backoff_ms=2000.0)

        for attempt in range(5):
            sleep_ms = engine.calculate_sleep_duration_ms(attempt)
            ceiling = min(2000.0, 100.0 * (2.0 ** attempt))
            self.assertGreaterEqual(sleep_ms, 0.0)
            self.assertLessEqual(sleep_ms, ceiling)

        # Validate jitter variation
        samples = [engine.calculate_sleep_duration_ms(3) for _ in range(10)]
        self.assertGreater(len(set(samples)), 1, "Jittered values must be non-deterministic")

    def test_05_circuit_breaker_closed_to_open_tripping(self) -> None:
        """
        Verifies circuit breaker trips to OPEN when failure rate exceeds 50% in sliding window.
        """
        cb = SlidingWindowCircuitBreaker(
            window_size=10,
            failure_threshold_percentage=50.0,
            min_requests_to_evaluate=5,
        )

        self.assertEqual(cb.state, SlidingWindowCircuitBreaker.STATE_CLOSED)

        # Inject 4 failures out of 6 requests (66.7% failure rate > 50%)
        cb.record_result(True)
        cb.record_result(False)
        cb.record_result(False)
        cb.record_result(False)
        cb.record_result(False)
        cb.record_result(True)

        self.assertEqual(cb.state, SlidingWindowCircuitBreaker.STATE_OPEN)
        self.assertGreater(cb.tripped_count, 0)
        self.assertGreater(cb.current_failure_rate, 50.0)

    def test_06_circuit_breaker_fail_fast_rejection(self) -> None:
        """
        Verifies that an OPEN circuit breaker fails fast without invoking downstream services.
        """
        cb = SlidingWindowCircuitBreaker(cooldown_period_seconds=10.0)
        cb.state = SlidingWindowCircuitBreaker.STATE_OPEN
        cb.last_state_change_time = time.perf_counter()

        can_call, reason = cb.can_execute()
        self.assertFalse(can_call)
        self.assertIn("CIRCUIT_BREAKER_OPEN_FAIL_FAST", reason)

    def test_07_circuit_breaker_half_open_recovery(self) -> None:
        """
        Verifies that after cooldown expires, circuit transitions to HALF-OPEN,
        and consecutive successful probes reset state to CLOSED.
        """
        cb = SlidingWindowCircuitBreaker(
            cooldown_period_seconds=0.01,
            consecutive_success_threshold=3,
        )
        cb.state = SlidingWindowCircuitBreaker.STATE_OPEN
        cb.last_state_change_time = time.perf_counter() - 0.05  # expired cooldown

        can_call, state = cb.can_execute()
        self.assertTrue(can_call)
        self.assertEqual(cb.state, SlidingWindowCircuitBreaker.STATE_HALF_OPEN)

        # 3 consecutive successes reset circuit to CLOSED
        cb.record_result(True)
        self.assertEqual(cb.state, SlidingWindowCircuitBreaker.STATE_HALF_OPEN)
        cb.record_result(True)
        self.assertEqual(cb.state, SlidingWindowCircuitBreaker.STATE_HALF_OPEN)
        cb.record_result(True)
        self.assertEqual(cb.state, SlidingWindowCircuitBreaker.STATE_CLOSED)

    def test_08_traffic_load_simulation_orchestrator(self) -> None:
        """
        Validates orchestrator traffic load simulation across standard and enterprise tiers.
        """
        res_std = self.orchestrator.simulate_traffic_load(150, "standard")
        self.assertEqual(res_std["enforcement_status"], "PASS")
        self.assertEqual(res_std["requests_allowed"], 100)
        self.assertEqual(res_std["requests_throttled_429"], 50)

        res_ent = self.orchestrator.simulate_traffic_load(1050, "enterprise")
        self.assertEqual(res_ent["enforcement_status"], "PASS")
        self.assertEqual(res_ent["requests_allowed"], 1000)
        self.assertEqual(res_ent["requests_throttled_429"], 50)

    def test_09_cli_execution_and_report_artifacts(self) -> None:
        """
        Validates CLI execution and confirms generation of Markdown report and JSON payload.
        """
        ret = run_resilience_pipeline(
            simulate_traffic=True,
            audit_rate_limits=True,
            test_circuit_breaker=True,
            summary=False,
            repo_root=REPO_ROOT,
        )
        self.assertEqual(ret, 0)

        self.assertTrue(RESILIENCE_MD_PATH.exists())
        self.assertTrue(RESILIENCE_JSON_PATH.exists())

        with open(RESILIENCE_MD_PATH, "r", encoding="utf-8") as f:
            md_text = f.read()

        self.assertIn("API Rate Limiting, DDoS Mitigation & Circuit Breaker Report", md_text)
        self.assertIn("Token Bucket Dynamic Rate Limiting Evaluation", md_text)
        self.assertIn("Three-State Circuit Breaker State Transition Matrix", md_text)
        self.assertIn("OFFICIAL API RESILIENCE & CIRCUIT BREAKER ATTESTATION SEAL", md_text)

        with open(RESILIENCE_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["metadata"]["organization"], "DevSuperSuite Official")
        self.assertIn("sha256_digest", data["metadata"])
        self.assertEqual(len(data["metadata"]["sha256_digest"]), 64)
        self.assertEqual(data["resilience_summary"]["overall_status"], "CERTIFIED_RESILIENCE_COMPLIANT")

    def test_10_strict_brand_anonymity_under_infosec_devsupersuite(self) -> None:
        """
        Enforces 100% Brand Anonymity under DevSuperSuite Information Security (infosec@devsupersuite.com).
        Zero personal founder names, personal handles, personal emails, or phone numbers.
        """
        files_to_check = [
            SERVICES_DIR / "rate_limiting_circuit_breaker_engine.py",
            RESILIENCE_MD_PATH,
            RESILIENCE_JSON_PATH,
        ]

        forbidden_patterns = [
            r"\b[A-Za-z0-9._%+-]+@(?!(?:devsupersuite\.com))\w+\.\w+\b",
            r"(?<![a-zA-Z0-9])(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}(?![a-zA-Z0-9])",
            r"github\.com\/(?!DevSuperSuiteOfficial)[a-zA-Z0-9_\-]+",
        ]

        for filepath in files_to_check:
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                self.assertIn("DevSuperSuite", content, f"Must reference DevSuperSuite in {filepath.name}")
                self.assertIn("infosec@devsupersuite.com", content, f"Must reference official contact in {filepath.name}")

                # Exclude cryptographic hex digests to avoid false positives on digit runs
                cleaned_content = re.sub(r"[a-f0-9]{32,64}", "", content, flags=re.IGNORECASE)

                for pattern in forbidden_patterns:
                    matches = list(re.finditer(pattern, cleaned_content, re.IGNORECASE))
                    self.assertEqual(len(matches), 0, f"Found forbidden personal pattern in {filepath.name}: {matches}")


if __name__ == "__main__":
    unittest.main()
