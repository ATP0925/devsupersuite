#!/usr/bin/env python3
"""
Unit and integration tests for DevSuperSuite Reddit Developer Community Engagement & AMA Engine (Phase 44).
Validates 5 target subreddits, flagship AMA post, 15 technical objections registry,
automated comment matcher, 100% Brand Anonymity Protocol, and disk dossier exports.
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

from marketing.reddit_community_amplifier import (
    RedditCommunityAmplifier,
    RedditSubreddit,
    AMAPost,
    TechnicalObjection,
    BRAND_ENTITY,
    BRAND_EMAIL,
    WEB_APP_BASE,
    GUMROAD_BASE,
)


@pytest.fixture
def amplifier() -> RedditCommunityAmplifier:
    return RedditCommunityAmplifier()


# TEST 1: Target Subreddits Registry (5 Subreddits)
def test_target_subreddits_registry():
    subreddits = RedditCommunityAmplifier.get_target_subreddits()
    assert len(subreddits) == 5

    names = [s.name for s in subreddits]
    assert "r/programming" in names
    assert "r/LocalLLaMA" in names
    assert "r/rust" in names
    assert "r/devops" in names
    assert "r/cursor" in names

    for s in subreddits:
        assert isinstance(s.subscribers, str) and len(s.subscribers) > 2
        assert len(s.culture_focus) > 10
        assert len(s.flair) > 0


# TEST 2: Flagship AMA Post Structure & Content
def test_flagship_ama_post_structure():
    ama = RedditCommunityAmplifier.generate_flagship_ama_post("r/programming")

    assert "We replaced Cloud RAG with local SIMD Tree-sitter parsers" in ama.title
    assert ama.author == BRAND_ENTITY
    assert ama.subreddit == "r/programming"
    assert "Attention Sink Dilution" in ama.content_markdown
    assert "Vector RAG Fails on Source Code" in ama.content_markdown
    assert "SIMD Tree-sitter CST Pruning" in ama.content_markdown
    assert "AgentShield (Sub-0.8ms Shannon Entropy)" in ama.content_markdown
    assert "Pre-Commit Invariant Guards" in ama.content_markdown
    assert "Sub-110ms Local Duplex Voice" in ama.content_markdown
    assert WEB_APP_BASE in ama.sandbox_url
    assert len(ama.content_markdown.split()) > 400


# TEST 3: Registry of 15 Chronic Technical Objections
def test_15_technical_objections_completeness():
    objections = RedditCommunityAmplifier.get_15_technical_objections()
    assert len(objections) == 15, "Must contain exactly 15 technical objections"

    ids = [o.objection_id for o in objections]
    assert len(set(ids)) == 15, "All objection IDs must be unique"
    for i in range(1, 16):
        assert f"OBJ-{i:02d}" in ids

    for o in objections:
        assert len(o.keyword_patterns) >= 2
        assert len(o.question_summary) > 15
        assert len(o.detailed_response) > 100


# TEST 4: Automated Comment Response Matcher
def test_comment_response_matcher(amplifier: RedditCommunityAmplifier):
    # Test WASM footprint matching
    m1 = amplifier.match_objection("What is the wasm footprint and memory overhead of tree-sitter?")
    assert m1 is not None
    assert m1.objection_id == "OBJ-01"

    # Test Shannon entropy UUID matching
    m2 = amplifier.match_objection("Isn't your shannon entropy false positive rate on UUIDs going to be annoying?")
    assert m2 is not None
    assert m2.objection_id == "OBJ-04"

    # Test why pure Rust matching
    m3 = amplifier.match_objection("Why did you write this in pure rust instead of python bindings?")
    assert m3 is not None
    assert m3.objection_id == "OBJ-10"

    # Test acoustic echo cancellation matching
    m4 = amplifier.match_objection("How do you handle acoustic echo cancellation without microphone feedback?")
    assert m4 is not None
    assert m4.objection_id == "OBJ-09"

    # Test lifetime sustainability matching
    m5 = amplifier.match_objection("How is a 24 dollars lifetime license sustainable if there is no subscription model?")
    assert m5 is not None
    assert m5.objection_id == "OBJ-15"


# TEST 5: Comment Matcher Rejection of Unrelated Text
def test_comment_response_no_match(amplifier: RedditCommunityAmplifier):
    unrelated = "What is the best coffee shop in San Francisco?"
    match = amplifier.match_objection(unrelated)
    assert match is None


# TEST 6: Strict 100% Brand Anonymity Protocol Enforcement
def test_brand_anonymity_enforcement(amplifier: RedditCommunityAmplifier):
    # Production AMA and objections must be 100% clean
    ok, violations = amplifier.audit_brand_anonymity()
    assert ok is True, f"Brand Anonymity violations: {violations}"
    assert len(violations) == 0

    # Test that forbidden terms trigger failures
    leaked_corpus = "Written by boss personal cell phone +1-555-492-1209 at residential address"
    leak_ok, leak_violations = amplifier.audit_brand_anonymity(text=leaked_corpus)
    assert leak_ok is False
    assert len(leak_violations) >= 2


# TEST 7: Canonical Sandbox and Commercial Checkout URLs
def test_canonical_sandbox_and_checkout_urls(amplifier: RedditCommunityAmplifier):
    ama = amplifier.generate_flagship_ama_post()
    assert WEB_APP_BASE in ama.content_markdown
    assert BRAND_EMAIL in ama.content_markdown

    objections = amplifier.get_15_technical_objections()
    for o in objections:
        assert len(o.detailed_response) > 50


# TEST 8: Disk Export of Dossiers
def test_dossiers_disk_export():
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_amplifier = RedditCommunityAmplifier(output_dir=tmpdir)
        paths = temp_amplifier.export_ama_dossiers()

        assert "flagship_ama_post" in paths
        assert os.path.exists(paths["flagship_ama_post"])
        assert os.path.getsize(paths["flagship_ama_post"]) > 500

        # Check all 15 objection dossiers exist on disk
        for i in range(1, 16):
            obj_id = f"OBJ-{i:02d}"
            assert obj_id in paths
            assert os.path.exists(paths[obj_id])
            assert os.path.getsize(paths[obj_id]) > 200


# TEST 9: Mathematical & Compiler Technical Rigor
def test_math_and_compiler_technical_rigor(amplifier: RedditCommunityAmplifier):
    obj4 = next(o for o in amplifier.get_15_technical_objections() if o.objection_id == "OBJ-04")
    assert "log_2(16) = 4.00" in obj4.detailed_response or "3.45 and 3.78" in obj4.detailed_response
    assert "4.50" in obj4.detailed_response

    obj9 = next(o for o in amplifier.get_15_technical_objections() if o.objection_id == "OBJ-09")
    assert "Normalized Least Mean Squares" in obj9.detailed_response
    assert "Double-Talk" in obj9.detailed_response


# TEST 10: Code Snippets in Complex Objections
def test_code_snippets_in_complex_objections(amplifier: RedditCommunityAmplifier):
    objections = amplifier.get_15_technical_objections()
    code_bearing_objs = [o for o in objections if o.code_snippet is not None]
    assert len(code_bearing_objs) >= 2
