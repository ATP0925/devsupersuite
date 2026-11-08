"""Unit and integration tests for DevSuperSuite Hacker News Launch Architect (Phase 49).

Validates:
- Primary and alternate Show HN titles formatting.
- Founding technical comment word count (>= 1,200 words) and mathematical rigor.
- Complete 10 technical objection dossiers and engineering answers.
- Hacker News ranking gravity simulation formula: Score = (P - 1) / (T + 2)^1.8.
- Canonical URLs and VIP launch coupon preservation.
- 100% Brand Anonymity Protocol enforcement.
- Export of production assets on disk.
"""

import json
import math
import os
import sys
import pytest

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from marketing.hackernews_launch_architect import (
    HackerNewsLaunchArchitect,
    HackerNewsRankingSimulator,
    audit_brand_anonymity,
    OFFICIAL_BRAND_NAME,
    OFFICIAL_HN_EMAIL,
    CANONICAL_SANDBOX_URL,
    CANONICAL_CHECKOUT_URL,
    VIP_LAUNCH_COUPON,
    DISCOUNT_PRICE_USD,
    REGULAR_PRICE_USD,
    HN_GRAVITY_EXPONENT
)


@pytest.fixture
def architect() -> HackerNewsLaunchArchitect:
    return HackerNewsLaunchArchitect()


@pytest.fixture
def simulator() -> HackerNewsRankingSimulator:
    return HackerNewsRankingSimulator(gravity=1.8)


def test_titles_formatting_and_length(architect: HackerNewsLaunchArchitect):
    """Verifies Show HN title conventions, character lengths, and alternates."""
    titles = architect.titles
    assert titles["primary"].startswith("Show HN: DevSuperSuite")
    assert len(titles["primary"]) <= 100
    assert len(titles["alternates"]) == 3
    for alt in titles["alternates"]:
        assert alt.startswith("Show HN: DevSuperSuite")
        assert len(alt) <= 110


def test_founding_comment_word_count(architect: HackerNewsLaunchArchitect):
    """Verifies that the founding comment strictly meets or exceeds the 1,200 words mandate."""
    words = len(architect.founding_comment.split())
    assert words >= 1200, f"Founding comment has {words} words, expected >= 1,200"


def test_founding_comment_technical_depth(architect: HackerNewsLaunchArchitect):
    """Verifies critical systems architecture concepts are explained in depth."""
    comment = architect.founding_comment.lower()

    required_concepts = [
        "attention sink",
        "softmax",
        "tree-sitter",
        "c-abi",
        "l1 data cache",
        "avx-512",
        "ring buffer",
        "repr(align(64))",
        "88.5 millisecond",
        "shannon entropy",
        "scif mode"
    ]
    for concept in required_concepts:
        assert concept in comment, f"Missing required concept in founding comment: '{concept}'"


def test_benchmark_metrics_accuracy(architect: HackerNewsLaunchArchitect):
    """Verifies transparent benchmark numbers in the founding comment."""
    comment = architect.founding_comment
    assert "0.84 millisecond" in comment or "0.84 ms" in comment
    assert "83.6%" in comment
    assert "88.5 millisecond" in comment or "88.5 ms" in comment
    assert "2.1 millisecond" in comment or "2.1 ms" in comment


def test_10_technical_objections_completeness(architect: HackerNewsLaunchArchitect):
    """Verifies all 10 anticipated Hacker News technical objections are modeled."""
    objections = architect.technical_objections
    assert len(objections) == 10

    expected_categories = [
        "cursor",
        "syntax error",
        "monorepo",
        "ring buffer",
        "aider",
        "local llm",
        "scif",
        "windows",
        "voice coding",
        "business"
    ]

    combined_categories = " ".join([o["objection_category"].lower() for o in objections])
    for cat in expected_categories:
        assert cat in combined_categories, f"Missing objection category: '{cat}'"

    for obj in objections:
        assert len(obj["skeptic_comment"]) > 50
        assert len(obj["engineering_rebuttal"]) > 200


def test_hn_ranking_gravity_formula(simulator: HackerNewsRankingSimulator):
    """Verifies mathematical correctness of Hacker News gravity ranking formula."""
    # Score = (P - 1) / (T + 2)^1.8
    # At T=0, P=101: Score = 100 / (2^1.8)
    expected_score_t0 = 100.0 / math.pow(2.0, 1.8)
    computed_score_t0 = simulator.compute_hn_score(points=101, hours_elapsed=0.0)
    assert abs(computed_score_t0 - expected_score_t0) < 1e-4

    # At T=2, P=171: Score = 170 / (4^1.8)
    expected_score_t2 = 170.0 / math.pow(4.0, 1.8)
    computed_score_t2 = simulator.compute_hn_score(points=171, hours_elapsed=2.0)
    assert abs(computed_score_t2 - expected_score_t2) < 1e-4

    # Test points_needed_for_score inverse function
    target_score = 14.0
    pts_needed = simulator.points_needed_for_score(target_score=target_score, hours_elapsed=2.0)
    resulting_score = simulator.compute_hn_score(points=pts_needed, hours_elapsed=2.0)
    assert resulting_score >= target_score
    assert resulting_score - target_score < 0.2


def test_ranking_simulation_trajectory(simulator: HackerNewsRankingSimulator):
    """Verifies that simulation trajectory outputs monotonic point growth and realistic velocity."""
    traj = simulator.simulate_top_5_trajectory(target_score=14.0)
    assert len(traj) >= 5

    prev_points = 0
    for row in traj:
        assert row["required_total_points"] > prev_points
        assert row["hourly_upvote_velocity"] > 0
        assert row["achieved_gravity_score"] >= 14.0
        assert "Top" in row["front_page_status"]
        prev_points = row["required_total_points"]


def test_canonical_urls_and_coupon_preservation(architect: HackerNewsLaunchArchitect):
    """Verifies sandbox, checkout, coupon code, and pricing details."""
    comment = architect.founding_comment
    assert CANONICAL_SANDBOX_URL in comment
    assert CANONICAL_CHECKOUT_URL in comment
    assert VIP_LAUNCH_COUPON in comment
    assert f"${DISCOUNT_PRICE_USD}" in comment
    assert f"${REGULAR_PRICE_USD}" in comment


def test_brand_anonymity_enforcement(architect: HackerNewsLaunchArchitect):
    """Verifies strict 100% Brand Anonymity Protocol compliance."""
    full_text = (
        architect.founding_comment + " "
        + architect.titles["primary"] + " "
        + " ".join(architect.titles["alternates"]) + " "
        + " ".join([o["skeptic_comment"] + " " + o["engineering_rebuttal"] for o in architect.technical_objections])
    )
    passed, violations = audit_brand_anonymity(full_text)
    assert passed is True, f"Brand anonymity violations: {violations}"
    assert len(violations) == 0

    # Test synthetic violation detection
    leak_passed, leak_violations = audit_brand_anonymity("Contact founder Anthony Padgett at 555-123-4567")
    assert leak_passed is False
    assert len(leak_violations) >= 2


def test_export_production_packet(architect: HackerNewsLaunchArchitect, tmp_path):
    """Verifies exporting dossier and metadata to disk generates valid files."""
    out_dir = str(tmp_path / "marketing_test")
    paths = architect.export_production_packet(base_dir=out_dir)

    assert "dossier" in paths
    assert "metadata" in paths

    for p in paths.values():
        assert os.path.exists(p)
        assert os.path.getsize(p) > 500

    # Validate JSON metadata schema
    with open(paths["metadata"], "r", encoding="utf-8") as f:
        meta = json.load(f)
        assert meta["title_primary"] == architect.titles["primary"]
        assert meta["founding_comment_word_count"] >= 1200
        assert meta["technical_objections_count"] == 10
        assert len(meta["gravity_simulation"]) > 0


def test_markdown_dossier_structure(architect: HackerNewsLaunchArchitect):
    """Verifies the structure of the generated launch dossier markdown."""
    dossier = architect.generate_dossier_markdown()
    assert "# HACKER NEWS 'SHOW HN' LAUNCH DOSSIER" in dossier
    assert "## 1. Submission Title Architecture" in dossier
    assert "## 2. Founding Technical Submission Comment" in dossier
    assert "## 3. Hacker News Gravity Ranking Simulation" in dossier
    assert "## 4. Top 10 Anticipated Technical Objections" in dossier
    assert "| Elapsed Time | Target Score | Total Upvotes Required |" in dossier
