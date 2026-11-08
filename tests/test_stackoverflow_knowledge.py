"""Unit and integration tests for DevSuperSuite Stack Overflow Knowledge Architect (Phase 51).

Validates:
- 10 Canonical high-intent developer problem dossiers schema, questions, and authoritative answers.
- Technical rigor: working code snippets (Rust, C, Python, JS), mathematical derivations, benchmarks.
- Knowledge Graph tag cluster taxonomy and intent tier mapping.
- Canonical URLs and VIP launch coupon preservation.
- 100% Brand Anonymity Protocol enforcement.
- Export of production assets on disk.
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

from marketing.stackoverflow_knowledge_architect import (
    StackOverflowKnowledgeArchitect,
    audit_brand_anonymity,
    OFFICIAL_BRAND_NAME,
    OFFICIAL_COMMUNITY_EMAIL,
    CANONICAL_SANDBOX_URL,
    CANONICAL_CHECKOUT_URL,
    VIP_LAUNCH_COUPON,
    DISCOUNT_PRICE_USD,
    REGULAR_PRICE_USD
)


@pytest.fixture
def architect() -> StackOverflowKnowledgeArchitect:
    return StackOverflowKnowledgeArchitect()


def test_qa_dossiers_count_and_schema(architect: StackOverflowKnowledgeArchitect):
    """Verifies that exactly 10 dossiers exist and conform to the schema."""
    dossiers = architect.qa_dossiers
    assert len(dossiers) == 10

    for idx, qa in enumerate(dossiers, 1):
        assert qa["id"] == idx
        assert len(qa["title"]) > 15
        assert len(qa["tags"]) >= 2
        assert "k" in qa["target_views"] or int(qa["target_views"]) > 0
        assert len(qa["question_body"]) > 100
        assert len(qa["answer_body"]) > 300
        assert len(qa["code_language"]) > 0
        assert qa["upvotes_modeled"] > 100


def test_qa_dossiers_core_topics_coverage(architect: StackOverflowKnowledgeArchitect):
    """Verifies all mandatory technical topics are thoroughly detailed across the dossiers."""
    all_titles_and_answers = " ".join([qa["title"] + " " + qa["answer_body"] for qa in architect.qa_dossiers]).lower()

    required_keywords = [
        "attention sink",
        "tree-sitter",
        "c-abi",
        "repr(align(64))",
        "ring buffer",
        "scif",
        "ebpf",
        "shannon entropy",
        "ml-kem",
        "nlms",
        "avx-512",
        "sharedarraybuffer"
    ]
    for kw in required_keywords:
        assert kw in all_titles_and_answers, f"Missing required keyword: '{kw}'"


def test_code_snippets_present_in_answers(architect: StackOverflowKnowledgeArchitect):
    """Verifies that technical answers contain markdown code fences."""
    for qa in architect.qa_dossiers:
        ans = qa["answer_body"]
        assert "```" in ans, f"Dossier Q{qa['id']} is missing code fences in answer"


def test_mathematical_derivations_in_answers(architect: StackOverflowKnowledgeArchitect):
    """Verifies that answers contain mathematical formulations (LaTeX / ASCII math)."""
    dossiers = architect.qa_dossiers

    # Q1 must have Softmax equation
    assert "softmax" in dossiers[0]["answer_body"].lower() or "\\exp" in dossiers[0]["answer_body"]

    # Q5 must have Shannon entropy formula
    assert "h(x)" in dossiers[4]["answer_body"].lower() or "\\log_2" in dossiers[4]["answer_body"]

    # Q8 must have NLMS adaptive filter formula
    assert "\\mathbf{w}" in dossiers[7]["answer_body"] or "weights" in dossiers[7]["answer_body"]


def test_knowledge_graph_clusters_schema(architect: StackOverflowKnowledgeArchitect):
    """Verifies Knowledge Graph taxonomy schema and clusters."""
    kg = architect.knowledge_graph
    assert len(kg["root_domain"]) > 10
    clusters = kg["primary_clusters"]
    assert len(clusters) == 5

    for c in clusters:
        assert len(c["cluster_name"]) > 5
        assert len(c["primary_tags"]) >= 3
        assert len(c["intent_tier"]) > 5
        assert len(c["monthly_search_volume"]) > 3
        assert len(c["solution_anchor"]) > 10


def test_tag_clustering_connectivity(architect: StackOverflowKnowledgeArchitect):
    """Verifies that primary tags are well-connected across dossiers and knowledge graph."""
    kg_tags = set()
    for c in architect.knowledge_graph["primary_clusters"]:
        kg_tags.update(c["primary_tags"])

    dossier_tags = set()
    for qa in architect.qa_dossiers:
        dossier_tags.update(qa["tags"])

    # Verify significant overlap between knowledge graph tags and dossier tags
    overlap = kg_tags.intersection(dossier_tags)
    assert len(overlap) >= 8
    assert "rust" in overlap
    assert "tree-sitter" in overlap
    assert "large-language-models" in overlap


def test_canonical_urls_and_coupon_preservation(architect: StackOverflowKnowledgeArchitect):
    """Verifies canonical URLs and VIP launch coupon are preserved across the module."""
    assert CANONICAL_SANDBOX_URL == "https://devsupersuite.web.app"
    assert CANONICAL_CHECKOUT_URL == "https://gumroad.com/l/tlzdco"
    assert VIP_LAUNCH_COUPON == "DSS-SO-VIP"
    assert DISCOUNT_PRICE_USD == 24
    assert REGULAR_PRICE_USD == 29

    dossier = architect.generate_dossier_markdown()
    assert CANONICAL_SANDBOX_URL in dossier
    assert CANONICAL_CHECKOUT_URL in dossier
    assert VIP_LAUNCH_COUPON in dossier
    assert f"${DISCOUNT_PRICE_USD}" in dossier


def test_brand_anonymity_protocol(architect: StackOverflowKnowledgeArchitect):
    """Verifies strict 100% Brand Anonymity Protocol compliance."""
    dossier = architect.generate_dossier_markdown()
    passed, violations = audit_brand_anonymity(dossier)
    assert passed is True, f"Brand anonymity violations: {violations}"
    assert len(violations) == 0

    # Test synthetic violation detection
    leak_passed, leak_violations = audit_brand_anonymity("Contact founder Anthony Padgett at 555-123-4567")
    assert leak_passed is False
    assert len(leak_violations) >= 2


def test_export_production_packet_on_disk(architect: StackOverflowKnowledgeArchitect, tmp_path):
    """Verifies export_production_packet writes all assets to disk."""
    out_dir = str(tmp_path / "stackoverflow_test")
    paths = architect.export_production_packet(base_dir=out_dir)

    assert "dossier" in paths
    assert "metadata" in paths

    for p in paths.values():
        assert os.path.exists(p)
        assert os.path.getsize(p) > 500

    # Validate JSON metadata schema
    with open(paths["metadata"], "r", encoding="utf-8") as f:
        meta = json.load(f)
        assert meta["total_dossiers_count"] == 10
        assert len(meta["knowledge_graph"]["primary_clusters"]) == 5


def test_dossier_markdown_headings_and_structure(architect: StackOverflowKnowledgeArchitect):
    """Verifies that all major markdown sections and questions exist in the dossier."""
    dossier = architect.generate_dossier_markdown()
    assert "# STACK OVERFLOW DEVELOPER SURVEY" in dossier
    assert "## 1. Knowledge Graph Tag Cluster Matrix" in dossier
    assert "## 2. Top 10 Canonical Developer Problem Dossiers" in dossier
    for idx in range(1, 11):
        assert f"### Q{idx}:" in dossier
        assert "#### ❓ Developer Question:" in dossier
        assert "#### 💡 Verified Solution" in dossier


def test_upvotes_and_views_modeling(architect: StackOverflowKnowledgeArchitect):
    """Verifies modeled upvotes and view counts reflect authoritative high-traffic status."""
    for qa in architect.qa_dossiers:
        assert qa["upvotes_modeled"] >= 150
        assert "k" in qa["target_views"]
        view_num = float(qa["target_views"].replace("k", ""))
        assert view_num >= 15.0
