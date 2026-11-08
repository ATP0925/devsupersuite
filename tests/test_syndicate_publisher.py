#!/usr/bin/env python3
"""
Unit and integration tests for DevSuperSuite Automated Syndicate Publisher Engine.
Validates multi-platform formatting (Dev.to, Hashnode, Medium), canonical SEO / GEO link preservation,
thread-to-article compiler, headless exports, and 100% Brand Anonymity Protocol.
"""

import os
import sys
import tempfile
import pytest

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from marketing.syndicate_article_publisher import (
    ArticleDraft,
    PublishResult,
    ThreadDefinition,
    ThreadToArticleConverter,
    PlatformPayloadFormatter,
    SyndicatePublisher,
    CANONICAL_BASE,
    WEB_APP_BASE,
    BRAND_ENTITY,
    BRAND_EMAIL,
)


@pytest.fixture
def sample_thread() -> ThreadDefinition:
    return ThreadDefinition(
        thread_id="XT-TEST-01",
        title="Why Transformers Suffer Attention Sink Dilution on Monoliths",
        slug="transformers-attention-sink-dilution-monoliths",
        topic="Context-Window Attention Dilution & Token Bloat",
        tweets=[
            "1/4 If you feed 60,000 LOC into Claude Code and watch the model hallucinate database columns, you are suffering from Attention Sink Dilution.",
            "2/4 Transformer self-attention computes softmax(QK^T / sqrt(d_k)). The middle 60% of context decays exponentially.",
            "3/4 Traditional line chunkers sever function signatures from types. Slicing with Tree-sitter eliminates 83% of prompt bloat.",
            "4/4 Grab DevSuperSuite Pro Lifetime to eliminate monthly seat taxes: https://gumroad.com/l/tlzdco"
        ],
        tags=["ai", "compilers", "rust", "typescript"]
    )


@pytest.fixture
def sample_article(sample_thread: ThreadDefinition) -> ArticleDraft:
    return ThreadToArticleConverter.convert_thread(sample_thread)


@pytest.fixture
def publisher() -> SyndicatePublisher:
    return SyndicatePublisher()


# TEST 1: Thread-to-Article Conversion Mechanics
def test_thread_to_article_conversion(sample_thread: ThreadDefinition):
    draft = ThreadToArticleConverter.convert_thread(sample_thread)

    assert draft.title == sample_thread.title
    assert draft.slug == sample_thread.slug
    assert draft.canonical_url == f"{CANONICAL_BASE}/{sample_thread.slug}"
    assert "Executive Overview" in draft.content_markdown
    assert "Verification & Interactive Browser Sandbox" in draft.content_markdown
    assert "```typescript" in draft.content_markdown
    assert draft.author == BRAND_ENTITY
    assert draft.author_email == BRAND_EMAIL
    assert len(draft.content_markdown.split()) > 250


# TEST 2: Dev.to REST Payload Formatting
def test_devto_payload_formatting(sample_article: ArticleDraft):
    payload = PlatformPayloadFormatter.format_devto_payload(sample_article)

    assert "article" in payload
    art = payload["article"]
    assert art["title"] == sample_article.title
    assert art["canonical_url"] == sample_article.canonical_url
    assert art["published"] is True
    assert isinstance(art["tags"], list)
    assert len(art["tags"]) <= 4
    assert sample_article.content_markdown in art["body_markdown"]


# TEST 3: Hashnode GraphQL Mutation Formatting
def test_hashnode_payload_formatting(sample_article: ArticleDraft):
    payload = PlatformPayloadFormatter.format_hashnode_payload(sample_article, publication_id="pub_test_99")

    assert "query" in payload
    assert "publishPost" in payload["query"]
    assert "variables" in payload
    inp = payload["variables"]["input"]
    assert inp["title"] == sample_article.title
    assert inp["originalArticleURL"] == sample_article.canonical_url
    assert inp["slug"] == sample_article.slug
    assert inp["publicationId"] == "pub_test_99"
    assert isinstance(inp["tags"], list)


# TEST 4: Medium REST Payload Formatting
def test_medium_payload_formatting(sample_article: ArticleDraft):
    payload = PlatformPayloadFormatter.format_medium_payload(sample_article, user_id="user_test_42")

    assert payload["title"] == sample_article.title
    assert payload["canonicalUrl"] == sample_article.canonical_url
    assert payload["contentFormat"] == "markdown"
    assert payload["publishStatus"] == "public"
    assert isinstance(payload["tags"], list)
    assert sample_article.content_markdown == payload["content"]


# TEST 5: Canonical Link & SEO / GEO Preservation Audit
def test_canonical_seo_integrity(publisher: SyndicatePublisher, sample_article: ArticleDraft):
    # Valid canonical
    ok, issues = publisher.audit_canonical_integrity(sample_article)
    assert ok is True
    assert len(issues) == 0

    # Tampered canonical URL (wrong domain)
    bad_article = ArticleDraft(
        title="Invalid Test",
        slug="invalid-test",
        subtitle="Sub",
        content_markdown="Some content referencing https://otherdomain.com/blog/invalid-test",
        tags=["test"],
        canonical_url="https://otherdomain.com/blog/invalid-test"
    )
    bad_ok, bad_issues = publisher.audit_canonical_integrity(bad_article)
    assert bad_ok is False
    assert any("does not resolve to devsupersuite.web.app" in s for s in bad_issues)


# TEST 6: 100% Brand Anonymity Protocol Enforcement
def test_brand_anonymity_enforcement(publisher: SyndicatePublisher):
    # Compliant text
    clean_text = f"Written by {BRAND_ENTITY} ({BRAND_EMAIL}) - visit {WEB_APP_BASE} for interactive Wasm tools."
    ok, violations = publisher.audit_brand_anonymity(clean_text)
    assert ok is True
    assert len(violations) == 0

    # Text leaking personal founder data
    leaked_text = f"Written by the boss personal cell +1-555-123-4567 at residential address, contact {BRAND_EMAIL}"
    leak_ok, leak_violations = publisher.audit_brand_anonymity(leaked_text)
    assert leak_ok is False
    assert len(leak_violations) >= 2


# TEST 7: Headless Payload Disk Export
def test_headless_payload_export(publisher: SyndicatePublisher, sample_article: ArticleDraft):
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = publisher.export_headless_payloads(sample_article, tmpdir)

        assert "devto" in paths
        assert "hashnode" in paths
        assert "medium" in paths
        assert "canonical_markdown" in paths

        for name, p in paths.items():
            assert os.path.exists(p)
            assert os.path.getsize(p) > 50


# TEST 8: Multi-Platform Publication Workflow (Dry Run and Mock Transport)
def test_mock_publish_all_platforms(publisher: SyndicatePublisher, sample_article: ArticleDraft):
    # Test dry run
    dry_results = publisher.publish_all(sample_article, dry_run=True)
    assert dry_results["devto"].success is True
    assert dry_results["devto"].status_code == 200
    assert dry_results["hashnode"].success is True
    assert dry_results["medium"].success is True

    # Test mock HTTP client execution
    live_results = publisher.publish_all(sample_article, dry_run=False)
    assert live_results["devto"].success is True
    assert live_results["devto"].status_code == 201
    assert live_results["devto"].canonical_verified is True
    assert "https://dev.to/" in live_results["devto"].published_url

    assert live_results["hashnode"].success is True
    assert live_results["hashnode"].status_code == 200
    assert "https://blog.devsupersuite.com/" in live_results["hashnode"].published_url

    assert live_results["medium"].success is True
    assert live_results["medium"].status_code == 201
    assert "https://medium.com/" in live_results["medium"].published_url


# TEST 9: Publication Gate on Canonical Integrity Failure
def test_publish_error_handling_on_canonical_failure(publisher: SyndicatePublisher):
    corrupt_article = ArticleDraft(
        title="Broken Canonical",
        slug="broken-canonical",
        subtitle="Broken",
        content_markdown="No canonical reference anywhere here.",
        tags=["bug"],
        canonical_url="https://external-pirate-site.com/broken-canonical"
    )

    res_devto = publisher.publish_to_devto(corrupt_article)
    assert res_devto.success is False
    assert res_devto.status_code == 400
    assert "Canonical integrity failure" in res_devto.error_message


# TEST 10: Markdown Thread File Ingestion & Compilation
def test_markdown_file_parsing():
    thread_file = os.path.join(PROJECT_DIR, "marketing", "x_threads", "xt-01_token-tax-attention-sink-dilution-tree-sitter.md")
    if os.path.exists(thread_file):
        draft = ThreadToArticleConverter.from_markdown_file(thread_file, thread_id="XT-01")
        assert "Why LLMs hallucinate" in draft.title
        assert draft.slug == "token-tax-attention-sink-dilution-tree-sitter"
        assert draft.canonical_url.startswith(CANONICAL_BASE)
        assert len(draft.content_markdown.split()) > 300
