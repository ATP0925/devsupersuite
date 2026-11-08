#!/usr/bin/env python3
"""
Unit and integration tests for DevSuperSuite Product Hunt Launch Architect & Asset Generator (Phase 45).
Validates tagline constraints, Maker's comment depth, 6-slide gallery specifications (1270x760),
dynamic launch schedule, hunter outreach dossiers, and 100% Brand Anonymity Protocol.
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

from marketing.producthunt_launch_architect import (
    ProductHuntLaunchArchitect,
    GallerySlide,
    HunterPitch,
    ProductHuntSubmission,
    BRAND_ENTITY,
    BRAND_EMAIL,
    WEB_APP_BASE,
    GUMROAD_BASE,
    PROMO_CODE,
    PROMO_PRICE,
)


@pytest.fixture
def architect() -> ProductHuntLaunchArchitect:
    return ProductHuntLaunchArchitect()


# TEST 1: Tagline Character Limit Constraint (<= 60 chars)
def test_tagline_character_limit(architect: ProductHuntLaunchArchitect):
    tagline = architect.get_tagline()
    assert isinstance(tagline, str)
    assert len(tagline) <= 60, f"Tagline must be <= 60 chars (was {len(tagline)})"
    assert len(tagline) >= 20, f"Tagline is too brief (was {len(tagline)})"
    assert "AST" in tagline or "AI" in tagline


# TEST 2: Maker's First Comment Depth & Word Count (~650 words)
def test_maker_comment_depth_and_word_count(architect: ProductHuntLaunchArchitect):
    comment = architect.get_maker_comment()
    words = comment.split()
    word_count = len(words)

    assert word_count >= 500, f"Maker comment is too brief: {word_count} words (Target: ~650)"
    assert word_count <= 850, f"Maker comment is too verbose: {word_count} words"

    # Must cover foundational architecture
    assert "Tree-sitter" in comment
    assert "AgentShield" in comment
    assert "Shannon entropy" in comment or "entropy" in comment
    assert "Pre-Commit Invariant" in comment or "invariant" in comment
    assert "Duplex Voice" in comment or "Voice" in comment
    assert WEB_APP_BASE in comment
    assert GUMROAD_BASE in comment
    assert PROMO_CODE in comment


# TEST 3: Gallery Slides Count and Aspect Ratio (6 Slides in 1270x760)
def test_gallery_slides_count_and_aspect_ratio(architect: ProductHuntLaunchArchitect):
    slides = architect.get_gallery_slides()
    assert len(slides) == 6, "Must provide exactly 6 flagship gallery slides"

    for idx, slide in enumerate(slides, 1):
        assert slide.slide_number == idx
        assert slide.aspect_ratio == "1270x760"
        assert len(slide.title) > 3
        assert len(slide.headline) > 10
        assert len(slide.key_features) >= 3
        assert slide.metric_badge is not None


# TEST 4: Gallery Slides Content Coverage
def test_gallery_slides_content_coverage(architect: ProductHuntLaunchArchitect):
    slides = architect.get_gallery_slides()
    all_headlines = " ".join([s.headline for s in slides])

    assert "Tree-Sitter" in all_headlines or "AST" in all_headlines
    assert "-83.6%" in all_headlines or "Collapse" in all_headlines
    assert "Shannon Entropy" in all_headlines or "Secret" in all_headlines
    assert "Unit Tests" in all_headlines or "Invariant" in all_headlines
    assert "Voice" in all_headlines or "Duplex" in all_headlines
    assert "SaaS Seat Taxes" in all_headlines or "Lifetime" in all_headlines


# TEST 5: Launch Schedule Specification
def test_launch_schedule_spec(architect: ProductHuntLaunchArchitect):
    schedule = architect.get_launch_schedule()

    assert schedule["target_day_of_week"] in ["Tuesday", "Wednesday"]
    assert "12:01 AM PT" in schedule["launch_window_pt"]
    assert len(schedule["hourly_milestones"]) >= 5

    hours = [m["hour_pt"] for m in schedule["hourly_milestones"]]
    assert "12:01 AM" in hours
    assert "11:59 PM" in hours


# TEST 6: Top Hunter Outreach Pitches
def test_hunter_outreach_pitches(architect: ProductHuntLaunchArchitect):
    pitches = architect.get_hunter_pitches()
    assert len(pitches) >= 2

    handles = [p.hunter_handle for p in pitches]
    assert "@chrismessina" in handles
    assert "@kevin" in handles

    for p in pitches:
        assert len(p.personalized_hook) > 20
        assert len(p.pitch_body) > 100
        assert WEB_APP_BASE in p.pitch_body


# TEST 7: Day-1 Community Comment Responders
def test_day1_comment_responses(architect: ProductHuntLaunchArchitect):
    responses = architect.get_day1_comment_responses()
    assert len(responses) >= 4

    topics = [r["topic"] for r in responses]
    assert any("Pricing" in t for t in topics)
    assert any("IDE" in t or "Compatibility" in t for t in topics)
    assert any("Privacy" in t for t in topics)
    assert any("Tree-Sitter" in t for t in topics)

    for r in responses:
        assert len(r["trigger_keywords"]) > 10
        assert len(r["response"]) > 100


# TEST 8: Strict 100% Brand Anonymity Protocol Enforcement
def test_brand_anonymity_protocol(architect: ProductHuntLaunchArchitect):
    # Production Maker comment and pitches must be 100% compliant
    ok, violations = architect.audit_brand_anonymity()
    assert ok is True, f"Brand Anonymity violations: {violations}"
    assert len(violations) == 0

    # Test rejection of leaked personal names/phones
    leaked_corpus = "Written by the boss personal phone +1-555-920-1928 at residential address"
    leak_ok, leak_violations = architect.audit_brand_anonymity(text=leaked_corpus)
    assert leak_ok is False
    assert len(leak_violations) >= 2


# TEST 9: Canonical Sandbox and Coupon Verification
def test_canonical_sandbox_and_coupon_preservation(architect: ProductHuntLaunchArchitect):
    comment = architect.get_maker_comment()
    assert f"coupon={PROMO_CODE}" in comment
    assert PROMO_PRICE in comment
    assert BRAND_EMAIL in comment


# TEST 10: Disk Export of Complete Launch Package
def test_export_launch_package_to_disk():
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_architect = ProductHuntLaunchArchitect(output_dir=tmpdir)
        paths = temp_architect.export_launch_package()

        assert "submission_manifest" in paths
        assert "maker_comment" in paths
        assert "gallery_slides_spec" in paths
        assert "gallery_slides_deck" in paths
        assert "hunter_outreach" in paths
        assert "day1_responses" in paths
        assert "launch_schedule" in paths

        for name, filepath in paths.items():
            assert os.path.exists(filepath), f"File {filepath} was not created"
            assert os.path.getsize(filepath) > 50, f"File {filepath} is unexpectedly small"

        # Validate JSON parseability
        with open(paths["submission_manifest"], "r", encoding="utf-8") as f:
            manifest = json.load(f)
            assert manifest["product_name"] == "DevSuperSuite"
            assert manifest["tagline_length"] <= 60

        with open(paths["gallery_slides_spec"], "r", encoding="utf-8") as f:
            slides_data = json.load(f)
            assert slides_data["slide_count"] == 6
