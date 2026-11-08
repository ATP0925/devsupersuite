"""Unit and integration tests for DevSuperSuite GitHub Trending Architect & Awesome-List Syndicate Engine (Phase 50).

Validates:
- Mathematical GitHub Trending algorithm heuristic and 24h star velocity curve.
- 5 Curated Awesome-List infiltration Pull Requests formatting.
- Charm VHS terminal recording script (.tape) syntax and command flow.
- High-converting README shields and social preview specifications.
- 100% Brand Anonymity Protocol compliance.
- File exports on disk.
"""

import json
import os
import sys
import pytest

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from marketing.github_trending_architect import (
    GitHubTrendingArchitect,
    GitHubTrendingSimulator,
    audit_brand_anonymity,
    OFFICIAL_BRAND_NAME,
    OFFICIAL_OSS_EMAIL,
    OFFICIAL_REPO_URL,
    CANONICAL_SANDBOX_URL,
    CANONICAL_CHECKOUT_URL,
    VIP_LAUNCH_COUPON,
    DISCOUNT_PRICE_USD,
    REGULAR_PRICE_USD
)


@pytest.fixture
def architect() -> GitHubTrendingArchitect:
    return GitHubTrendingArchitect()


@pytest.fixture
def simulator() -> GitHubTrendingSimulator:
    return GitHubTrendingSimulator()


def test_trending_simulator_heuristic_weights(simulator: GitHubTrendingSimulator):
    """Verifies trending score computation weights and values."""
    score = simulator.compute_trending_score(
        stars_24h=100,
        forks_24h=15,
        unique_account_ratio=0.95,
        commit_activity_score=1.0
    )
    # Expected: 1.0*100 + 0.4*15 + 0.25*(100*0.95) + 0.15*10 = 100 + 6 + 23.75 + 1.5 = 131.25
    assert abs(score - 131.25) < 0.1


def test_24h_trajectory_simulation_curve(simulator: GitHubTrendingSimulator):
    """Verifies that 24h star simulation hits >= 670 stars and reaches #1 Overall Trending."""
    trajectory = simulator.simulate_24h_trajectory(target_total_stars=680)
    assert len(trajectory) == 24

    final_hour = trajectory[-1]
    assert final_hour["hour"] == 24
    assert 670 <= final_hour["cumulative_stars"] <= 690
    assert final_hour["cumulative_forks"] >= 70
    assert final_hour["rank_overall"] == "#1 Trending (All Languages)"
    assert final_hour["rank_rust"] == "#1 Trending (Rust)"

    # Verify monotonic star accumulation
    prev_stars = 0
    for hour_data in trajectory:
        assert hour_data["cumulative_stars"] >= prev_stars
        prev_stars = hour_data["cumulative_stars"]


def test_awesome_list_prs_count_and_targets(architect: GitHubTrendingArchitect):
    """Verifies that exactly 5 target awesome-lists are modeled with correct metadata."""
    prs = architect.awesome_prs
    assert len(prs) == 5

    expected_ids = {
        "awesome-rust",
        "awesome-ai-devtools",
        "awesome-developer-first",
        "awesome-offline-first",
        "awesome-speech-recognition"
    }
    actual_ids = {pr["id"] for pr in prs}
    assert actual_ids == expected_ids

    for pr in prs:
        assert len(pr["target_repo"]) > 5
        assert len(pr["section"]) > 5
        assert len(pr["pr_title"]) > 10
        assert len(pr["pr_body"]) > 50


def test_awesome_list_diff_formatting(architect: GitHubTrendingArchitect):
    """Verifies that line diffs follow awesome-list markdown syntax."""
    for pr in architect.awesome_prs:
        diff = pr["diff_insertion"]
        assert diff.startswith("+- [")
        assert CANONICAL_SANDBOX_URL in diff
        assert "Tree-sitter" in diff or "duplex" in diff or "telemetry" in diff or "AST" in diff


def test_vhs_tape_syntax_and_commands(architect: GitHubTrendingArchitect):
    """Verifies the Charm VHS .tape file contains valid directives and realistic CLI commands."""
    tape = architect.vhs_tape_content
    assert "Output marketing/assets/terminal_demo.gif" in tape
    assert "Set FontSize" in tape
    assert "Set Width 1200" in tape
    assert "Set Theme" in tape
    assert "Type \"devsupersuite --scif-mode --voice-duplex\"" in tape
    assert "ast-slice" in tape
    assert "cargo test" in tape
    assert "git commit" in tape


def test_readme_badges_completeness(architect: GitHubTrendingArchitect):
    """Verifies README badges schema, image URLs, and links."""
    badges = architect.readme_badges
    assert len(badges) >= 7

    labels = [b["label"] for b in badges]
    assert "GitHub Release" in labels
    assert "Rust MSRV" in labels
    assert "Duplex Latency" in labels
    assert "Token Tax Reduction" in labels
    assert "Offline SCIF Mode" in labels
    assert "Interactive Wasm Sandbox" in labels
    assert "License" in labels

    for b in badges:
        assert b["badge_url"].startswith("https://img.shields.io/badge") or "shields.io" in b["badge_url"]
        assert len(b["link_url"]) > 5


def test_social_preview_card_spec(architect: GitHubTrendingArchitect):
    """Verifies Open Graph social preview dimensions and color palette."""
    spec = architect.social_preview_spec
    assert "1280x640" in spec["dimensions"]
    assert spec["color_palette"]["background"] == "#0D1117"
    assert "Token Tax" in spec["layout"]["headline"]
    assert "Duplex Voice" in spec["layout"]["subheadline"]
    assert len(spec["layout"]["badges"]) == 4


def test_canonical_urls_and_coupon_preservation(architect: GitHubTrendingArchitect):
    """Verifies canonical URLs and VIP launch coupon are preserved across the module."""
    assert CANONICAL_SANDBOX_URL == "https://devsupersuite.web.app"
    assert CANONICAL_CHECKOUT_URL == "https://gumroad.com/l/tlzdco"
    assert VIP_LAUNCH_COUPON == "DSS-GITHUB-VIP"
    assert DISCOUNT_PRICE_USD == 24
    assert REGULAR_PRICE_USD == 29

    dossier = architect.generate_dossier_markdown()
    assert CANONICAL_SANDBOX_URL in dossier
    assert CANONICAL_CHECKOUT_URL in dossier
    assert VIP_LAUNCH_COUPON in dossier
    assert f"${DISCOUNT_PRICE_USD}" in dossier


def test_brand_anonymity_protocol(architect: GitHubTrendingArchitect):
    """Verifies strict 100% Brand Anonymity Protocol compliance."""
    dossier = architect.generate_dossier_markdown()
    passed, violations = audit_brand_anonymity(dossier)
    assert passed is True, f"Brand anonymity violations: {violations}"
    assert len(violations) == 0

    # Test synthetic violation detection
    leak_passed, leak_violations = audit_brand_anonymity("Contact founder Anthony Padgett at 555-123-4567")
    assert leak_passed is False
    assert len(leak_violations) >= 2


def test_export_production_packet_on_disk(architect: GitHubTrendingArchitect, tmp_path):
    """Verifies export_production_packet writes all 3 assets to disk."""
    out_dir = str(tmp_path / "github_trending_test")
    paths = architect.export_production_packet(base_dir=out_dir)

    assert "dossier" in paths
    assert "metadata" in paths
    assert "vhs_tape" in paths

    for p in paths.values():
        assert os.path.exists(p)
        assert os.path.getsize(p) > 200

    # Validate JSON metadata schema
    with open(paths["metadata"], "r", encoding="utf-8") as f:
        meta = json.load(f)
        assert meta["target_total_stars_24h"] == 680
        assert meta["awesome_prs_count"] == 5
        assert len(meta["trajectory_checkpoints"]) == 24


def test_dossier_markdown_headings(architect: GitHubTrendingArchitect):
    """Verifies that all required major markdown sections exist in the dossier."""
    dossier = architect.generate_dossier_markdown()
    assert "# GITHUB TRENDING #1 STRATEGY" in dossier
    assert "## 1. GitHub Trending Algorithm Model" in dossier
    assert "## 2. Curated Awesome-List Infiltration Pull Requests" in dossier
    assert "## 3. Charm VHS Terminal Recording Tape" in dossier
    assert "## 4. High-Converting README Shields" in dossier
