#!/usr/bin/env python3
"""
Unit and integration tests for DevSuperSuite Technical Newsletter & Substack Editorial Syndicate (Phase 46).
Validates systems engineering editorial depth, Substack/Buttondown/beehiiv multi-platform payload schemas,
canonical SEO / GEO link preservation, SIMD code intrinsics, and 100% Brand Anonymity Protocol.
"""

import json
import os
import sys
import tempfile
import pytest

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from marketing.newsletter_editorial_syndicate import (
    NewsletterEditorialSyndicate,
    NewsletterEdition,
    BRAND_ENTITY,
    BRAND_EMAIL,
    WEB_APP_BASE,
    GUMROAD_BASE,
    PROMO_CODE,
    PROMO_PRICE,
)


@pytest.fixture
def syndicate() -> NewsletterEditorialSyndicate:
    return NewsletterEditorialSyndicate()


@pytest.fixture
def edition(syndicate: NewsletterEditorialSyndicate) -> NewsletterEdition:
    return syndicate.get_flagship_edition()


# TEST 1: Flagship Edition Metadata & Audience Scope
def test_flagship_edition_metadata(edition: NewsletterEdition):
    assert edition.edition_number == 1
    assert "Systems Architecture Deep-Dive" in edition.title
    assert "INT8 Neural Audio" in edition.title
    assert "Tree-Sitter" in edition.title
    assert "45,000+" in edition.target_audience
    assert edition.slug == "int8-neural-audio-tree-sitter-simd-systems-architecture"
    assert edition.canonical_url == f"{WEB_APP_BASE}/blog/{edition.slug}"
    assert edition.author == BRAND_ENTITY
    assert edition.author_email == BRAND_EMAIL
    assert edition.estimated_read_time >= 10


# TEST 2: Systems Engineering Content Depth & Rigor (>1,800 Words)
def test_technical_content_depth_and_word_count(edition: NewsletterEdition):
    words = edition.content_markdown.split()
    word_count = len(words)

    assert word_count >= 1800, f"Newsletter must be deep-technical (>=1,800 words), was {word_count}"
    
    # Check core architectural topics
    assert "Conquering the 110ms Cognitive Threshold" in edition.content_markdown
    assert "Silicon Realities: Apple Silicon Unified Memory" in edition.content_markdown
    assert "Lock-Free Audio Ring Buffer" in edition.content_markdown
    assert "SIMD Vectorization: ARM NEON & AVX-512" in edition.content_markdown
    assert "Normalized Least Mean Squares" in edition.content_markdown
    assert "Concurrent Tree-Sitter CST Parsing" in edition.content_markdown
    assert "End-to-End Latency Budget" in edition.content_markdown


# TEST 3: Substack Editorial Format & Schema
def test_substack_editorial_format(syndicate: NewsletterEditorialSyndicate, edition: NewsletterEdition):
    payload = syndicate.format_substack_edition(edition)

    assert payload["platform"] == "substack"
    assert payload["title"] == edition.title
    assert payload["subtitle"] == edition.subtitle
    assert payload["canonical_url"] == edition.canonical_url
    assert payload["author"] == BRAND_ENTITY
    assert payload["author_email"] == BRAND_EMAIL
    assert payload["body_markdown"] == edition.content_markdown
    assert payload["send_email"] is True


# TEST 4: Buttondown REST API Format & Schema
def test_buttondown_api_payload(syndicate: NewsletterEditorialSyndicate, edition: NewsletterEdition):
    payload = syndicate.format_buttondown_edition(edition)

    assert payload["platform"] == "buttondown"
    assert payload["subject"] == edition.title
    assert payload["status"] == "published"
    assert isinstance(payload["included_tags"], list)
    assert "rust" in payload["included_tags"]
    assert "metadata" in payload
    assert payload["metadata"]["canonical_url"] == edition.canonical_url
    assert payload["metadata"]["promo_coupon"] == PROMO_CODE


# TEST 5: beehiiv Custom Post API Format & Schema
def test_beehiiv_api_payload(syndicate: NewsletterEditorialSyndicate, edition: NewsletterEdition):
    payload = syndicate.format_beehiiv_edition(edition)

    assert payload["platform"] == "beehiiv"
    assert payload["title"] == edition.title
    assert payload["content_format"] == "markdown"
    assert payload["canonical_url"] == edition.canonical_url
    assert payload["status"] == "confirmed"
    assert "meta_tags" in payload
    assert payload["meta_tags"]["author"] == BRAND_ENTITY


# TEST 6: Canonical SEO / GEO Preservation
def test_canonical_seo_and_geo_preservation(syndicate: NewsletterEditorialSyndicate, edition: NewsletterEdition):
    ok, issues = syndicate.audit_canonical_integrity(edition)
    assert ok is True, f"Canonical audit failed: {issues}"
    assert len(issues) == 0

    # Test rejection of external non-canonical URL
    corrupt_edition = NewsletterEdition(
        edition_number=99,
        title="Corrupted",
        slug="corrupted",
        subtitle="Corrupted",
        target_audience="Devs",
        canonical_url="https://external-news.com/blog/corrupted",
        content_markdown="Body text",
        estimated_read_time=5
    )
    c_ok, c_issues = syndicate.audit_canonical_integrity(corrupt_edition)
    assert c_ok is False
    assert any("does not resolve to devsupersuite.web.app" in s for s in c_issues)


# TEST 7: Strict 100% Brand Anonymity Protocol Enforcement
def test_brand_anonymity_enforcement(syndicate: NewsletterEditorialSyndicate):
    # Production edition must be 100% clean
    ok, violations = syndicate.audit_brand_anonymity()
    assert ok is True, f"Brand Anonymity violations: {violations}"
    assert len(violations) == 0

    # Test that forbidden terms trigger failures
    leaked_corpus = "Written by boss personal cell +1-555-881-2910 at residential address"
    leak_ok, leak_violations = syndicate.audit_brand_anonymity(text=leaked_corpus)
    assert leak_ok is False
    assert len(leak_violations) >= 2


# TEST 8: Memory Layout Diagrams & SIMD Code Intrinsics
def test_memory_layout_and_code_snippets(edition: NewsletterEdition):
    # Rust cache alignment & atomic ring buffer
    assert "#[repr(align(64))]" in edition.content_markdown
    assert "AtomicUsize" in edition.content_markdown

    # ARM NEON SIMD intrinsics
    assert "vdotq_s32" in edition.content_markdown or "aarch64" in edition.content_markdown

    # NLMS Acoustic Echo Cancellation mathematical formula
    assert "w^T(n)" in edition.content_markdown or "NLMS" in edition.content_markdown
    assert "Double-Talk" in edition.content_markdown


# TEST 9: Disk Export of All Editions (Substack, Buttondown, beehiiv)
def test_export_all_editions_to_disk():
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_syndicate = NewsletterEditorialSyndicate(output_dir=tmpdir)
        paths = temp_syndicate.export_all_editions()

        assert "master_markdown" in paths
        assert "substack_manifest" in paths
        assert "buttondown_api" in paths
        assert "beehiiv_api" in paths

        for name, filepath in paths.items():
            assert os.path.exists(filepath), f"File {filepath} was not created"
            assert os.path.getsize(filepath) > 100, f"File {filepath} is unexpectedly small"

        # Validate JSON content integrity
        with open(paths["buttondown_api"], "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["platform"] == "buttondown"
            assert data["metadata"]["promo_coupon"] == PROMO_CODE

        with open(paths["beehiiv_api"], "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["platform"] == "beehiiv"
            assert data["status"] == "confirmed"


# TEST 10: Interactive Sandbox & Permanent Lifetime Access CTAs
def test_interactive_sandbox_and_lifetime_ctas(edition: NewsletterEdition):
    assert WEB_APP_BASE in edition.content_markdown
    assert GUMROAD_BASE in edition.content_markdown
    assert PROMO_CODE in edition.content_markdown
    assert PROMO_PRICE in edition.content_markdown
