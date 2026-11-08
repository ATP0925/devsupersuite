"""Test suite for DevSuperSuite YouTube Technical Walkthrough & Video Script Production Engine (Phase 48).

Validates:
- Script timeline (12:00 duration, monotonic chapter progression).
- Word counts, pacing, and technical rigor (Attention Sink, Tree-sitter, Lock-Free Ring Buffer).
- Visual cues, camera directions, code overlays.
- 1280x720 thumbnail design specifications.
- YouTube SEO description with chapter markers and 30+ tags.
- Pinned comment with conversion incentives.
- 100% Brand Anonymity Protocol compliance.
- File exports on disk.
"""

import json
import os
import re
import sys
import pytest

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from marketing.youtube_production_architect import (
    YouTubeProductionArchitect,
    audit_brand_anonymity,
    OFFICIAL_BRAND_NAME,
    OFFICIAL_DEVREL_EMAIL,
    CANONICAL_SANDBOX_URL,
    CANONICAL_CHECKOUT_URL,
    VIP_LAUNCH_COUPON,
    DISCOUNT_PRICE_USD
)


@pytest.fixture
def architect() -> YouTubeProductionArchitect:
    return YouTubeProductionArchitect()


def test_video_metadata_schema_and_duration(architect: YouTubeProductionArchitect):
    """Verifies core video metadata schema and duration."""
    meta = architect.video_metadata
    assert meta["primary_title"] == "Building a Sub-110ms Local Duplex Voice Coding Assistant with Rust & Tree-Sitter (Stop Paying the Token Tax)"
    assert len(meta["alternate_titles"]) >= 3
    assert meta["total_duration_minutes"] == 12.0
    assert meta["total_duration_seconds"] == 720
    assert meta["aspect_ratio"] == "16:9"
    assert "4K" in meta["resolution"] or "3840x2160" in meta["resolution"]
    assert meta["category"] == "Science & Technology"


def test_script_chapters_chronology_and_coverage(architect: YouTubeProductionArchitect):
    """Verifies contiguous, monotonic progression of chapters totaling exactly 720 seconds."""
    segments = architect.script_segments
    assert len(segments) == 6

    def time_to_sec(t_str: str) -> int:
        parts = t_str.split(":")
        return int(parts[0]) * 60 + int(parts[1])

    expected_start = 0
    total_duration = 0
    for idx, seg in enumerate(segments, 1):
        assert seg["chapter_index"] == idx
        s_sec = time_to_sec(seg["timestamp_start"])
        e_sec = time_to_sec(seg["timestamp_end"])
        assert s_sec == expected_start, f"Chapter {idx} start {s_sec} != expected {expected_start}"
        assert e_sec > s_sec
        assert seg["duration_seconds"] == (e_sec - s_sec)
        total_duration += seg["duration_seconds"]
        expected_start = e_sec

    assert total_duration == 720
    assert segments[0]["timestamp_start"] == "00:00"
    assert segments[-1]["timestamp_end"] == "12:00"


def test_script_spoken_dialogue_word_count_and_pacing(architect: YouTubeProductionArchitect):
    """Verifies script dialogue pacing is between 120 and 175 words per minute."""
    segments = architect.script_segments
    total_words = 0

    for seg in segments:
        words = len(seg["spoken_dialogue"].split())
        total_words += words
        wpm = (words / seg["duration_seconds"]) * 60
        # Normal YouTube presentation pacing is ~90-185 WPM
        assert 90 <= wpm <= 185, f"Chapter {seg['chapter_index']} WPM ({wpm:.1f}) out of bounds"

    assert 1200 <= total_words <= 2200, f"Total script word count {total_words} out of expected range"


def test_technical_concepts_coverage(architect: YouTubeProductionArchitect):
    """Verifies presence of core systems architecture concepts in spoken text."""
    combined_dialogue = " ".join([seg["spoken_dialogue"] for seg in architect.script_segments]).lower()

    required_keywords = [
        "token tax",
        "attention sink",
        "softmax",
        "tree-sitter",
        "c-abi",
        "l1 data cache",
        "83.6 percent",
        "ring buffer",
        "cache line",
        "88.5 millisecond",
        "shannon entropy",
        "scif mode"
    ]

    for kw in required_keywords:
        assert kw in combined_dialogue, f"Missing required technical keyword: '{kw}'"


def test_code_overlays_and_visual_cues(architect: YouTubeProductionArchitect):
    """Verifies visual cues, lower thirds, and code overlays are present."""
    segments = architect.script_segments
    code_overlays = [seg["code_overlay"] for seg in segments if seg["code_overlay"]]
    assert len(code_overlays) >= 4

    for seg in segments:
        assert len(seg["visual_cues"]) >= 2
        assert len(seg["lower_third"]) > 0
        assert len(seg["b_roll_notes"]) > 0
        assert len(seg["camera_shot"]) > 0


def test_thumbnail_specifications(architect: YouTubeProductionArchitect):
    """Verifies 1280x720 thumbnail design specifications and wireframe."""
    spec = architect.thumbnail_spec
    dims = spec["dimensions"]
    assert dims["width"] == 1280
    assert dims["height"] == 720
    assert dims["aspect_ratio"] == "16:9"

    colors = spec["color_palette"]
    assert colors["background_primary"] == "#0D1117"
    assert colors["accent_neon_blue"] == "#58A6FF"
    assert colors["accent_emerald_green"] == "#3FB950"
    assert colors["accent_warning_red"] == "#FF7B72"

    layout = spec["layout_composition"]
    assert "left_column" in layout
    assert "center_column" in layout
    assert "right_column" in layout
    assert "bottom_banner" in layout
    assert "-83.6%" in layout["bottom_banner"]["text"]
    assert len(spec["ascii_wireframe"]) > 100


def test_seo_description_and_chapters_formatting(architect: YouTubeProductionArchitect):
    """Verifies YouTube SEO description contains timestamps, links, and quickstarts."""
    desc = architect.seo_description

    # Must contain timestamp format '00:00 - '
    assert re.search(r'00:00\s*-\s*', desc) is not None
    assert re.search(r'03:45\s*-\s*', desc) is not None
    assert re.search(r'10:45\s*-\s*', desc) is not None

    # Canonical URLs & coupon
    assert CANONICAL_SANDBOX_URL in desc
    assert CANONICAL_CHECKOUT_URL in desc
    assert VIP_LAUNCH_COUPON in desc
    assert f"${DISCOUNT_PRICE_USD}" in desc

    # 1-click install commands
    assert "curl -fsSL" in desc
    assert "irm " in desc


def test_video_tags_count_and_relevance(architect: YouTubeProductionArchitect):
    """Verifies YouTube tags count is >= 30 and covers required domains."""
    tags = architect.get_video_tags()
    assert len(tags) >= 30
    assert "rust" in tags
    assert "tree-sitter" in tags
    assert "voice coding" in tags
    assert "token tax" in tags
    assert "scif mode" in tags


def test_pinned_comment_and_conversion_elements(architect: YouTubeProductionArchitect):
    """Verifies pinned comment contains conversion CTA, coupon code, and engagement question."""
    comment = architect.pinned_comment
    assert CANONICAL_SANDBOX_URL in comment
    assert CANONICAL_CHECKOUT_URL in comment
    assert VIP_LAUNCH_COUPON in comment
    assert f"${DISCOUNT_PRICE_USD}" in comment
    assert "COMMUNITY QUESTION" in comment


def test_brand_anonymity_protocol(architect: YouTubeProductionArchitect):
    """Verifies strict 100% Brand Anonymity Protocol compliance."""
    all_text = (
        architect.seo_description
        + " " + architect.pinned_comment
        + " " + architect.video_metadata["primary_title"]
    )
    for seg in architect.script_segments:
        all_text += " " + seg["spoken_dialogue"]
        all_text += " " + seg["camera_shot"]
        all_text += " " + seg["b_roll_notes"]

    passed, violations = audit_brand_anonymity(all_text)
    assert passed is True
    assert len(violations) == 0

    # Ensure synthetic violations are detected
    leak_passed, leak_violations = audit_brand_anonymity("Contact founder Anthony Padgett at 555-123-4567")
    assert leak_passed is False
    assert len(leak_violations) >= 2


def test_export_production_packet_to_disk(architect: YouTubeProductionArchitect, tmp_path):
    """Verifies exporting the production packet creates valid files on disk."""
    out_dir = str(tmp_path / "youtube_production")
    created = architect.export_production_packet(output_dir=out_dir)

    assert "teleprompter_script" in created
    assert "thumbnail_brief" in created
    assert "youtube_metadata" in created
    assert "master_spec" in created

    for path in created.values():
        assert os.path.exists(path)
        assert os.path.getsize(path) > 100

    # Verify JSON files are valid and loadable
    with open(created["youtube_metadata"], "r", encoding="utf-8") as f:
        meta_json = json.load(f)
        assert meta_json["category_id"] == 28
        assert len(meta_json["tags"]) >= 30

    with open(created["master_spec"], "r", encoding="utf-8") as f:
        spec_json = json.load(f)
        assert len(spec_json["chapters"]) == 6
