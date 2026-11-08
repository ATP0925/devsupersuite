"""
==================================================================================================
           UNIT & INTEGRATION TESTS: ENTERPRISE RFP AUTOMATION TEMPLATE ENGINE
==================================================================================================
Governing Authority: DevSuperSuite Solutions Architecture Group
Testing Framework: pytest 9.2.0
Coverage Target: 100% Pass Rate across Ingestion, Fuzzy Matching, Export & Cryptography
Brand Anonymity Notice: 100% Brand Anonymized. Issued exclusively under DevSuperSuite Official.
==================================================================================================
"""

import os
import sys
import json
import csv
import subprocess
import tempfile
import pytest

# Ensure services directory is importable
SERVICES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "services"))
if SERVICES_DIR not in sys.path:
    sys.path.insert(0, SERVICES_DIR)

from enterprise_rfp_automation_template_engine import RFPAutomationEngine, DEFAULT_MASTER_BANK_PATH


@pytest.fixture
def engine():
    """Initializes the RFP Automation Engine with the production master bank."""
    return RFPAutomationEngine(master_bank_path=DEFAULT_MASTER_BANK_PATH)


def test_master_bank_initialization(engine):
    """Verifies that the master answer bank loads successfully with 50+ entries."""
    assert engine.bank_data is not None
    assert len(engine.answers) >= 50
    assert len(engine.domains) == 6
    assert "domain_1" in engine.domains
    assert "domain_6" in engine.domains


def test_tokenization_and_similarity(engine):
    """Tests tokenization and Jaccard similarity logic."""
    tokens1 = engine.tokenize("What is the Shannon entropy threshold?")
    tokens2 = engine.tokenize("Explain the entropy calculation and threshold.")
    assert "shannon" in tokens1
    assert "entropy" in tokens1
    assert "threshold" in tokens1

    sim = engine.calculate_similarity(tokens1, tokens2)
    assert 0.0 < sim <= 1.0


def test_match_question_high_confidence(engine):
    """Tests matching for high-confidence queries."""
    # Test AST query
    match, score, m_type = engine.match_question("How does Tree-Sitter AST context slicing work in OmniKernel?")
    assert match is not None
    assert match["domain_id"] == "domain_1"
    assert score >= 0.35

    # Test entropy query
    match_sec, score_sec, m_type_sec = engine.match_question("How are secrets detected using Shannon entropy H > 3.0 before commit?")
    assert match_sec is not None
    assert match_sec["domain_id"] == "domain_2"
    assert score_sec >= 0.40


def test_match_question_fallback(engine):
    """Tests that esoteric queries receive a graceful fallback response."""
    match, score, m_type = engine.match_question("Xylophone zebra quantum teleportation protocol")
    assert match is not None
    assert score > 0.0
    assert m_type in ["fallback_general", "partial_keyword_fallback"]


def test_ingest_json_rfp(engine):
    """Tests ingestion of JSON format RFPs."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json_data = [
            {"id": "SIG-01", "question": "What is the token reduction percentage of OmniKernel?"},
            {"id": "SIG-02", "question": "How are destructive terminal commands blocked?"},
            {"id": "SIG-03", "question": "Does the system support air-gapped SCIF deployments?"}
        ]
        json.dump(json_data, f)
        temp_path = f.name

    try:
        count = engine.ingest_rfp(temp_path)
        assert count == 3
        assert len(engine.ingested_questions) == 3
        assert engine.ingested_questions[0]["id"] == "SIG-01"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_ingest_csv_rfp(engine):
    """Tests ingestion of CSV format RFPs (e.g. CAIQ/VSA questionnaires)."""
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Control_ID", "Question_Text", "Category"])
        writer.writerow(["CAIQ-01", "How are unit tests protected from AI modification?", "Application Security"])
        writer.writerow(["CAIQ-02", "What is the uptime SLA for the gateway?", "Availability"])
        temp_path = f.name

    try:
        count = engine.ingest_rfp(temp_path)
        assert count == 2
        assert len(engine.ingested_questions) == 2
        assert engine.ingested_questions[0]["id"] == "CAIQ-01"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_ingest_text_rfp(engine):
    """Tests ingestion of plain text / markdown bullet list RFPs."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("1. Describe the ITAR compliance architecture.\n")
        f.write("2. What are the terms for the $54,000 turnkey SOW?\n")
        f.write("3. How does Live Voice Responder achieve sub-110ms latency?\n")
        temp_path = f.name

    try:
        count = engine.ingest_rfp(temp_path)
        assert count == 3
        assert len(engine.ingested_questions) == 3
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_auto_respond_and_cryptographic_hash(engine):
    """Tests auto_respond generation and per-response SHA-256 verification hashes."""
    engine.ingested_questions = [
        {"id": "TST-01", "question": "What is the pre-commit entropy threshold for secret detection?"},
        {"id": "TST-02", "question": "What is the uptime SLA for gateway clusters?"}
    ]
    responses = engine.auto_respond()
    assert len(responses) == 2
    for r in responses:
        assert "rfp_question_id" in r
        assert "verification_hash_sha256" in r
        assert len(r["verification_hash_sha256"]) == 64  # Valid SHA-256 hex string
        assert r["confidence_score"] > 0.0


def test_audit_coverage(engine):
    """Tests coverage auditing metrics."""
    audit = engine.audit_coverage()
    assert audit["total_questions"] >= 50
    assert audit["match_rate_percentage"] > 0.0
    assert len(audit["master_verification_hash_sha256"]) == 64
    assert len(audit["domain_distribution"]) > 0


def test_export_submission_markdown(engine):
    """Tests publication-grade Markdown export."""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        temp_out = f.name

    try:
        out_path = engine.export_submission(output_path=temp_out, client_name="Acme Aerospace Corp", format_type="markdown")
        assert os.path.exists(out_path)
        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Enterprise Security Assessment & RFP Formal Technical Submission" in content
        assert "Acme Aerospace Corp" in content
        assert "DevSuperSuite Solutions Architecture" in content
        assert "sha256:" in content
    finally:
        if os.path.exists(temp_out):
            os.remove(temp_out)


def test_export_submission_json(engine):
    """Tests JSON export format."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        temp_out = f.name

    try:
        out_path = engine.export_submission(output_path=temp_out, client_name="Global Bank Corp", format_type="json")
        assert os.path.exists(out_path)
        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["metadata"]["client_name"] == "Global Bank Corp"
        assert len(data["responses"]) >= 50
    finally:
        if os.path.exists(temp_out):
            os.remove(temp_out)


def test_cli_execution_summary():
    """Tests CLI execution with --summary flag."""
    script_path = os.path.join(SERVICES_DIR, "enterprise_rfp_automation_template_engine.py")
    cmd = [sys.executable, script_path, "--summary"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "DEVSUPERSUITE ENTERPRISE RFP AUTOMATION TEMPLATE ENGINE" in res.stdout
    assert "ARCH-AST" in res.stdout


def test_cli_execution_audit_coverage():
    """Tests CLI execution with --audit-coverage flag."""
    script_path = os.path.join(SERVICES_DIR, "enterprise_rfp_automation_template_engine.py")
    cmd = [sys.executable, script_path, "--audit-coverage"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "ENTERPRISE RFP RESPONSE COVERAGE & INTEGRITY AUDIT" in res.stdout
    assert "Master SHA-256 Audit Hash:" in res.stdout


def test_brand_anonymity_compliance(engine):
    """Strictly validates 100% Brand Anonymity (DevSuperSuite Official only)."""
    script_path = os.path.join(SERVICES_DIR, "enterprise_rfp_automation_template_engine.py")
    with open(script_path, "r", encoding="utf-8") as f:
        script_code = f.read()

    # Disallow common personal names or personal phone numbers
    forbidden = ["github.com/atpad", "atpad", "personal", "+1-555"]
    for term in forbidden:
        assert term not in script_code.lower(), f"Forbidden personal attribution detected: {term}"

    assert "DevSuperSuite" in script_code
    assert "solutions@devsupersuite.com" in script_code
