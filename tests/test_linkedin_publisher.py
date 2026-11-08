#!/usr/bin/env python3
"""
Unit and integration tests for DevSuperSuite LinkedIn Technical Article & Carousel Generator (Phase 43).
Validates 10-slide architectural carousel layout, post copy engagement metrics,
LinkedIn UGC API payloads, 100% Brand Anonymity Protocol, and headless exports.
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

from marketing.linkedin_publisher_engine import (
    LinkedInPublisherEngine,
    CarouselSlide,
    LinkedInPost,
    BRAND_ENTITY,
    BRAND_EMAIL,
    ORGANIZATION_URN,
    WEB_APP_BASE,
    GUMROAD_BASE,
)


@pytest.fixture
def engine() -> LinkedInPublisherEngine:
    return LinkedInPublisherEngine()


@pytest.fixture
def slides(engine: LinkedInPublisherEngine):
    return engine.get_10_slide_carousel()


@pytest.fixture
def post(engine: LinkedInPublisherEngine):
    return engine.get_linkedin_post_copy()


# TEST 1: Carousel 10-Slide Manifest Schema & Numbering
def test_carousel_manifest_schema(slides):
    assert len(slides) == 10, "Carousel must contain exactly 10 architectural slides"
    
    for idx, slide in enumerate(slides, 1):
        assert slide.slide_number == idx
        assert isinstance(slide.title, str) and len(slide.title) > 5
        assert isinstance(slide.subtitle, str) and len(slide.subtitle) > 5
        assert isinstance(slide.bullet_points, list) and len(slide.bullet_points) >= 3
        assert BRAND_ENTITY in slide.footer_text
        assert WEB_APP_BASE in slide.footer_text


# TEST 2: Essential Systems Architecture Topics Coverage
def test_carousel_topics_coverage(slides):
    all_titles = " ".join([s.title + " " + s.subtitle for s in slides]).lower()
    
    assert "hallucinate" in all_titles or "context" in all_titles
    assert "softmax" in all_titles
    assert "tree-sitter" in all_titles or "ast" in all_titles
    assert "shannon entropy" in all_titles or "credential" in all_titles
    assert "unit tests" in all_titles or "invariant" in all_titles
    assert "voice coding" in all_titles or "voice" in all_titles


# TEST 3: High-Engagement LinkedIn Post Copy Structure
def test_linkedin_post_copy_structure(post: LinkedInPost):
    assert len(post.hook) > 20
    assert "$114,000" in post.hook or "$114,000" in post.body_markdown
    assert "Attention Sink Dilution" in post.body_markdown
    assert "Tree-Sitter" in post.body_markdown
    assert "AgentShield" in post.body_markdown
    assert WEB_APP_BASE in post.cta
    assert GUMROAD_BASE in post.cta
    assert len(post.hashtags) >= 5
    assert "#SoftwareEngineering" in post.hashtags
    assert "#CTO" in post.hashtags


# TEST 4: LinkedIn UGC Share API Payload Schema
def test_linkedin_api_ugc_payload_schema(engine: LinkedInPublisherEngine, post: LinkedInPost):
    payload = engine.generate_ugc_post_payload(post)

    assert payload["author"] == ORGANIZATION_URN
    assert payload["lifecycleState"] == "PUBLISHED"
    assert "specificContent" in payload
    content = payload["specificContent"]["com.linkedin.ugc.ShareContent"]
    assert content["shareMediaCategory"] == "CAROUSEL"
    assert post.hook in content["shareCommentary"]["text"]
    assert len(content["media"]) == 1
    assert "originalUrl" in content["media"][0]
    assert payload["visibility"]["com.linkedin.ugc.MemberNetworkVisibility"] == "PUBLIC"


# TEST 5: Carousel 1:1 Aspect Ratio & Visual Layout Settings
def test_carousel_aspect_ratio_and_visual_layout(engine: LinkedInPublisherEngine, slides):
    manifest = engine.generate_carousel_manifest(slides)

    assert manifest["manifest_version"] == "1.0.0"
    assert manifest["brand"] == BRAND_ENTITY
    assert manifest["slide_count"] == 10
    layout = manifest["layout"]
    assert layout["aspect_ratio"] == "1:1"
    assert layout["width_px"] == 1080
    assert layout["height_px"] == 1080
    assert "color_palette" in layout
    assert layout["color_palette"]["background"] == "#0B0F19"
    assert "typography" in layout


# TEST 6: Strict 100% Brand Anonymity Protocol Enforcement
def test_brand_anonymity_enforcement(engine: LinkedInPublisherEngine):
    # Production carousel and post must pass cleanly
    ok, violations = engine.audit_brand_anonymity()
    assert ok is True, f"Brand Anonymity violations detected: {violations}"
    assert len(violations) == 0

    # Test rejection of forbidden personal leaks
    leaked_corpus = "Boss personal phone +1-555-019-2831 residential address founder personal cell"
    leak_ok, leak_violations = engine.audit_brand_anonymity(text=leaked_corpus)
    assert leak_ok is False
    assert len(leak_violations) >= 2


# TEST 7: Canonical Link & Sandbox Web URL Preservation
def test_canonical_and_sandbox_links_preservation(engine: LinkedInPublisherEngine, slides, post: LinkedInPost):
    manifest = engine.generate_carousel_manifest(slides)
    assert manifest["canonical_url"].startswith("https://devsupersuite.web.app/blog/")
    assert WEB_APP_BASE in post.cta
    assert "devrel@devsupersuite.com" in post.cta


# TEST 8: Headless Payloads Export to Disk
def test_headless_export_to_disk():
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_engine = LinkedInPublisherEngine(output_dir=tmpdir)
        paths = temp_engine.export_headless_payloads()

        assert "ugc_post_json" in paths
        assert "carousel_manifest_json" in paths
        assert "feed_post_markdown" in paths
        assert "carousel_deck_markdown" in paths

        for key, filepath in paths.items():
            assert os.path.exists(filepath), f"File {filepath} was not created"
            assert os.path.getsize(filepath) > 100, f"File {filepath} is unexpectedly small"

        # Validate JSON content integrity
        with open(paths["ugc_post_json"], "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["author"] == ORGANIZATION_URN

        with open(paths["carousel_manifest_json"], "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["slide_count"] == 10


# TEST 9: LinkedIn Character Limit Compliance
def test_character_limit_compliance(post: LinkedInPost):
    full_text = f"{post.hook}\n\n{post.body_markdown}\n\n{post.cta}\n\n{' '.join(post.hashtags)}"
    char_count = len(full_text)
    # LinkedIn post character limit is 3,000 characters. Optimal engagement is 1,200 - 2,200 characters.
    assert char_count < 3000, f"LinkedIn post exceeds 3,000 character hard limit (was {char_count})"
    assert char_count > 800, f"LinkedIn post is too short for a deep-technical breakdown (was {char_count})"


# TEST 10: Slide Code Fences and ASCII Diagrams
def test_slide_code_fences_and_diagrams(slides):
    has_code = any(s.code_snippet is not None for s in slides)
    has_diagram = any(s.diagram_ascii is not None for s in slides)
    has_metric = any(s.metric_highlight is not None for s in slides)

    assert has_code is True, "Carousel must include code snippets for technical credibility"
    assert has_diagram is True, "Carousel must include ASCII architectural diagrams"
    assert has_metric is True, "Carousel must include highlighted metrics on slides"
