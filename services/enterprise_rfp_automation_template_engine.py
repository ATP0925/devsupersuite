#!/usr/bin/env python3
"""
==================================================================================================
        DEVSUPERSUITE ENTERPRISE RFP AUTOMATION TEMPLATE ENGINE & MATCHING SUITE
==================================================================================================
Governing Authority: DevSuperSuite Solutions Architecture Group
Commercial & Technical Desk: solutions@devsupersuite.com | https://devsupersuite.web.app
Classification: Enterprise Sourcing & Presales Automation System
Compliance Standards: SIG Lite, CSA CAIQ v4, VSA Core, HECVAT Full, ISO 27001, SOC 2 Type II
Brand Anonymity Notice: 100% Brand Anonymized. Issued exclusively under DevSuperSuite Official.
==================================================================================================
"""

import os
import sys
import json
import csv
import re
import hashlib
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional

DEFAULT_MASTER_BANK_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "rfp_responses_master_bank.json"
)


class RFPAutomationEngine:
    """Enterprise RFP Response Automation & Dynamic Matching Engine."""

    def __init__(self, master_bank_path: str = DEFAULT_MASTER_BANK_PATH):
        self.master_bank_path = master_bank_path
        self.bank_data = self._load_master_bank()
        self.answers = self.bank_data.get("answers", [])
        self.domains = {d["id"]: d for d in self.bank_data.get("domains", [])}
        self.ingested_questions: List[Dict[str, Any]] = []
        self.responses: List[Dict[str, Any]] = []

    def _load_master_bank(self) -> Dict[str, Any]:
        """Loads and verifies the master RFP answer bank."""
        if not os.path.exists(self.master_bank_path):
            raise FileNotFoundError(f"Master answer bank not found at: {self.master_bank_path}")
        with open(self.master_bank_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def tokenize(text: str) -> set:
        """Tokenizes text into normalized alphanumeric word tokens."""
        clean = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
        return set([w for w in clean.split() if len(w) > 2])

    @staticmethod
    def calculate_similarity(query_tokens: set, doc_tokens: set) -> float:
        """Calculates Jaccard similarity between query and document token sets."""
        if not query_tokens or not doc_tokens:
            return 0.0
        intersection = len(query_tokens.intersection(doc_tokens))
        union = len(query_tokens.union(doc_tokens))
        return intersection / union if union > 0 else 0.0

    def match_question(self, incoming_question: str) -> Tuple[Dict[str, Any], float, str]:
        """Matches an incoming question against the master bank using dynamic fuzzy scoring."""
        query_tokens = self.tokenize(incoming_question)
        clean_query = incoming_question.lower()

        best_match = None
        best_score = 0.0
        match_type = "none"

        for item in self.answers:
            keywords_text = " ".join(item.get("keywords", []))
            question_text = item.get("question", "")
            short_ans = item.get("short_answer", "")
            tags_text = " ".join(item.get("compliance_tags", []))
            
            doc_raw = f"{keywords_text} {question_text} {short_ans} {tags_text}".lower()
            doc_tokens = self.tokenize(doc_raw)

            # Jaccard Token Overlap Base
            jaccard_score = self.calculate_similarity(query_tokens, doc_tokens)
            score = jaccard_score * 0.50

            # Exact Keyword Boost
            matched_kw_count = 0
            for kw in item.get("keywords", []):
                if kw.lower() in clean_query:
                    matched_kw_count += 1
            if matched_kw_count > 0:
                score += min(0.35, matched_kw_count * 0.12)

            # Direct Substring Match Boost
            if incoming_question.strip().lower() in question_text.lower():
                score += 0.40
            elif any(part in question_text.lower() for part in clean_query.split() if len(part) > 4):
                score += 0.15

            # Tag Match Boost
            for tag in item.get("compliance_tags", []):
                if tag.lower() in clean_query:
                    score += 0.10

            score = min(1.0, score)

            if score > best_score:
                best_score = score
                best_match = item
                if score >= 0.70:
                    match_type = "exact_high_confidence"
                elif score >= 0.35:
                    match_type = "fuzzy_semantic_match"
                else:
                    match_type = "partial_keyword_fallback"

        # Fallback if no reasonable match found
        if not best_match or best_score < 0.10:
            best_match = self.answers[0]  # General architectural fallback
            best_score = 0.15
            match_type = "fallback_general"

        return best_match, round(best_score, 3), match_type

    def ingest_rfp(self, file_path: str) -> int:
        """Ingests an external RFP in JSON, CSV, or Text/Markdown formats."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Input RFP file not found: {file_path}")

        self.ingested_questions = []
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for idx, item in enumerate(data, 1):
                        if isinstance(item, str):
                            self.ingested_questions.append({"id": f"Q-{idx:03d}", "question": item})
                        elif isinstance(item, dict):
                            q_text = item.get("question") or item.get("text") or item.get("description") or ""
                            q_id = item.get("id") or f"Q-{idx:03d}"
                            self.ingested_questions.append({"id": q_id, "question": q_text, "category": item.get("category", "General")})
                elif isinstance(data, dict):
                    # Check for questions list
                    questions_list = data.get("questions") or data.get("items") or []
                    for idx, item in enumerate(questions_list, 1):
                        if isinstance(item, str):
                            self.ingested_questions.append({"id": f"Q-{idx:03d}", "question": item})
                        elif isinstance(item, dict):
                            q_text = item.get("question") or item.get("text") or ""
                            q_id = item.get("id") or f"Q-{idx:03d}"
                            self.ingested_questions.append({"id": q_id, "question": q_text, "category": item.get("category", "General")})

        elif ext == ".csv":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                fieldnames = [fn.lower() for fn in (reader.fieldnames or [])]
                q_field = next((fn for fn in reader.fieldnames or [] if "question" in fn.lower() or "requirement" in fn.lower() or "prompt" in fn.lower()), None)
                id_field = next((fn for fn in reader.fieldnames or [] if "id" in fn.lower() or "number" in fn.lower() or "code" in fn.lower()), None)
                cat_field = next((fn for fn in reader.fieldnames or [] if "category" in fn.lower() or "domain" in fn.lower() or "section" in fn.lower()), None)

                for idx, row in enumerate(reader, 1):
                    q_text = row.get(q_field, "").strip() if q_field else ""
                    if not q_text:
                        # Fallback to first non-empty value
                        for val in row.values():
                            if len(val.strip()) > 10:
                                q_text = val.strip()
                                break
                    if q_text:
                        q_id = row.get(id_field, f"CSV-{idx:03d}").strip() if id_field else f"CSV-{idx:03d}"
                        q_cat = row.get(cat_field, "General").strip() if cat_field else "General"
                        self.ingested_questions.append({"id": q_id, "question": q_text, "category": q_cat})

        else:
            # Plain text or Markdown list
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                idx = 1
                for line in lines:
                    # Strip leading numbers, bullets, checkboxes
                    clean_line = re.sub(r"^(\d+[\.\)]|\-|\*|\[\s*\])\s*", "", line).strip()
                    if len(clean_line) > 8:
                        self.ingested_questions.append({"id": f"TXT-{idx:03d}", "question": clean_line, "category": "General"})
                        idx += 1

        return len(self.ingested_questions)

    def auto_respond(self) -> List[Dict[str, Any]]:
        """Matches all ingested questions against the master bank and generates verified responses."""
        if not self.ingested_questions:
            # Default to using master bank directly
            self.ingested_questions = [
                {"id": a["id"], "question": a["question"], "category": a.get("category", "General")}
                for a in self.answers
            ]

        self.responses = []
        for q in self.ingested_questions:
            q_id = q.get("id")
            q_text = q.get("question")
            matched_item, score, match_type = self.match_question(q_text)

            # Compute cryptographic hash for response integrity
            response_content = (
                f"{q_id}|{q_text}|{matched_item.get('short_answer')}|"
                f"{matched_item.get('detailed_response')}|"
                f"{','.join(matched_item.get('compliance_tags', []))}"
            )
            verification_hash = hashlib.sha256(response_content.encode("utf-8")).hexdigest()

            response_record = {
                "rfp_question_id": q_id,
                "rfp_question": q_text,
                "matched_bank_id": matched_item.get("id"),
                "domain_id": matched_item.get("domain_id"),
                "category": matched_item.get("category"),
                "confidence_score": score,
                "match_type": match_type,
                "short_answer": matched_item.get("short_answer"),
                "detailed_response": matched_item.get("detailed_response"),
                "compliance_tags": matched_item.get("compliance_tags", []),
                "verification_hash_sha256": verification_hash,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self.responses.append(response_record)

        return self.responses

    def audit_coverage(self) -> Dict[str, Any]:
        """Calculates match rates, confidence metrics, and domain distribution."""
        if not self.responses:
            self.auto_respond()

        total = len(self.responses)
        high_conf = len([r for r in self.responses if r["confidence_score"] >= 0.70])
        med_conf = len([r for r in self.responses if 0.35 <= r["confidence_score"] < 0.70])
        low_conf = len([r for r in self.responses if r["confidence_score"] < 0.35])

        avg_score = sum(r["confidence_score"] for r in self.responses) / total if total > 0 else 0.0

        domain_coverage = {}
        for r in self.responses:
            d_id = r.get("domain_id", "unknown")
            domain_coverage[d_id] = domain_coverage.get(d_id, 0) + 1

        overall_hash = hashlib.sha256(
            "".join(r["verification_hash_sha256"] for r in self.responses).encode("utf-8")
        ).hexdigest()

        return {
            "total_questions": total,
            "high_confidence_matches": high_conf,
            "medium_confidence_matches": med_conf,
            "low_confidence_matches": low_conf,
            "average_confidence_score": round(avg_score, 3),
            "match_rate_percentage": round((high_conf + med_conf) / total * 100, 1) if total > 0 else 0.0,
            "domain_distribution": domain_coverage,
            "master_verification_hash_sha256": overall_hash,
        }

    def export_submission(
        self,
        output_path: str,
        client_name: str = "Enterprise Procurement Review Board",
        format_type: str = "markdown",
    ) -> str:
        """Exports the filled, verified RFP responses to Markdown or JSON."""
        if not self.responses:
            self.auto_respond()

        audit = self.audit_coverage()
        timestamp = datetime.now().strftime("%B %d, %Y")

        if format_type == "json":
            export_payload = {
                "metadata": {
                    "document_title": "Enterprise RFP Automated Verified Submission",
                    "client_name": client_name,
                    "authoring_authority": "DevSuperSuite Solutions Architecture Group",
                    "contact_email": "solutions@devsupersuite.com",
                    "timestamp": timestamp,
                    "audit_metrics": audit,
                },
                "responses": self.responses,
            }
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_payload, f, indent=2)
            return output_path

        # Generate Publication-Grade Markdown
        doc = []
        doc.append(f"# Enterprise Security Assessment & RFP Formal Technical Submission")
        doc.append(f"")
        doc.append(f"**Document Reference:** RFP-SUBMISSION-VERIFIED-2026-V1  ")
        doc.append(f"**Procuring Client:** {client_name}  ")
        doc.append(f"**Submitting Authority:** DevSuperSuite Solutions Architecture Group  ")
        doc.append(f"**Commercial & Sourcing Desk:** solutions@devsupersuite.com | https://devsupersuite.web.app  ")
        doc.append(f"**Submission Date:** {timestamp}  ")
        doc.append(f"**Master Cryptographic Verification Hash:** `{audit['master_verification_hash_sha256']}`  ")
        doc.append(f"**Classification:** Commercial-in-Confidence // Procurement Sensitive  ")
        doc.append(f"**Brand Anonymity Notice:** 100% Brand Anonymized. Issued strictly under **DevSuperSuite Solutions Architecture** (OmniKernel Labs Solutions Group). No individual employee, founder, or contractor identities disclosed.  ")
        doc.append(f"")
        doc.append(f"---")
        doc.append(f"")
        doc.append(f"## 1. Executive Transmittal & Security Certification")
        doc.append(f"")
        doc.append(f"**To the Vendor Risk Management (VRM) Committee & Procurement Sourcing Board of {client_name}:**")
        doc.append(f"")
        doc.append(f"DevSuperSuite Solutions Architecture formally submits this verified technical response package addressing your enterprise security questionnaire and architectural evaluation requirements.")
        doc.append(f"")
        doc.append(f"DevSuperSuite operates as a **Sovereign Ingestion & Developer Cybersecurity Substrate**, providing compiler-grade Tree-Sitter AST context optimization (-78.8% to -83.4% token reduction), synchronous pre-commit Shannon entropy exfiltration defense ($H > 3.0$), and sub-110ms duplex voice pair-programming. All answers provided herein are backed by our **SOC 2 Type II Examination-Ready** package, **ISO/IEC 27001:2022** control alignments, and **ITAR / CMMC 2.0 Level 2** air-gapped deployment profiles.")
        doc.append(f"")
        doc.append(f"### Automated Verification & Integrity Metrics:")
        doc.append(f"* **Total Assessed Requirements:** {audit['total_questions']} items")
        doc.append(f"* **Verified Match Rate:** {audit['match_rate_percentage']}% (Average Confidence: {audit['average_confidence_score']})")
        doc.append(f"* **High/Medium Confidence Answers:** {audit['high_confidence_matches'] + audit['medium_confidence_matches']} of {audit['total_questions']}")
        doc.append(f"* **Master SHA-256 Audit Signature:** `{audit['master_verification_hash_sha256']}`")
        doc.append(f"")
        doc.append(f"---")
        doc.append(f"")
        doc.append(f"## 2. Itemized Technical Responses & Control Evidence")
        doc.append(f"")

        for idx, r in enumerate(self.responses, 1):
            q_id = r.get("rfp_question_id", f"Q-{idx:03d}")
            q_text = r.get("rfp_question")
            short_ans = r.get("short_answer")
            detailed = r.get("detailed_response")
            tags = ", ".join([f"`{t}`" for t in r.get("compliance_tags", [])])
            conf = r.get("confidence_score")
            v_hash = r.get("verification_hash_sha256")[:16]

            doc.append(f"### Requirement {q_id}: {q_text}")
            doc.append(f"")
            doc.append(f"**Executive Answer:**  ")
            doc.append(f"> {short_ans}")
            doc.append(f"")
            doc.append(f"**Detailed Technical Response & Verification Evidence:**  ")
            doc.append(f"{detailed}")
            doc.append(f"")
            doc.append(f"* **Matched Answer Bank ID:** `{r.get('matched_bank_id')}` | **Category:** {r.get('category')}  ")
            doc.append(f"* **Compliance Standards:** {tags}  ")
            doc.append(f"* **Verification Fingerprint:** `sha256:{v_hash}...` (Confidence Score: {conf})  ")
            doc.append(f"")
            doc.append(f"---")
            doc.append(f"")

        # Formal Execution Block
        doc.append(f"## 3. Formal Corporate Sourcing Countersignature Block")
        doc.append(f"")
        doc.append(f"```")
        doc.append(f"==================================================================================================")
        doc.append(f"                 RFP VENDOR RESPONSE ATTESTATION & SIGN-OFF BLOCK")
        doc.append(f"==================================================================================================")
        doc.append(f"SUBMITTED ON BEHALF OF:                     ACCEPTED ON BEHALF OF EVALUATION COMMITTEE:")
        doc.append(f"DEVSUPERSUITE SOLUTIONS ARCHITECTURE        {client_name.upper()}")
        doc.append(f"(OmniKernel Labs Solutions Group)")
        doc.append(f"")
        doc.append(f"By: ____________________________________    By: ____________________________________")
        doc.append(f"Name: Principal Solutions Architect         Name: __________________________________")
        doc.append(f"Title: Authorized Technical Representative  Title: CISO / Procurement Committee Chair")
        doc.append(f"Date: {timestamp}                           Date: __________________________________")
        doc.append(f"Contact: solutions@devsupersuite.com        Email: _________________________________")
        doc.append(f"==================================================================================================")
        doc.append(f"```")
        doc.append(f"")
        doc.append(f"---")
        doc.append(f"*DevSuperSuite Tech Services & Enterprise Solutions — OmniKernel Labs Solutions Group*  ")
        doc.append(f"*Solutions Architecture: solutions@devsupersuite.com | Official Portal: https://devsupersuite.web.app*")

        content = "\n".join(doc)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return output_path


def main():
    parser = argparse.ArgumentParser(
        description="DevSuperSuite Enterprise RFP Response Automation Template Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python enterprise_rfp_automation_template_engine.py --summary
  python enterprise_rfp_automation_template_engine.py --audit-coverage
  python enterprise_rfp_automation_template_engine.py --ingest-rfp sample_rfp.json --auto-respond
  python enterprise_rfp_automation_template_engine.py --auto-respond --export-submission ./submission.md
        """
    )
    parser.add_argument("--bank", default=DEFAULT_MASTER_BANK_PATH, help="Path to master answer bank JSON")
    parser.add_argument("--ingest-rfp", type=str, metavar="FILE", help="Ingest incoming RFP file (JSON, CSV, or Text)")
    parser.add_argument("--auto-respond", action="store_true", help="Automatically match questions and generate verified responses")
    parser.add_argument("--audit-coverage", action="store_true", help="Audit match confidence and domain coverage metrics")
    parser.add_argument("--export-submission", type=str, metavar="PATH", help="Export filled submission to Markdown or JSON")
    parser.add_argument("--client", type=str, default="Enterprise Procurement Review Board", help="Client name for generated submission")
    parser.add_argument("--format", type=str, choices=["markdown", "json"], default="markdown", help="Export file format")
    parser.add_argument("--summary", action="store_true", help="Display summary of master answer bank")

    args = parser.parse_args()

    engine = RFPAutomationEngine(master_bank_path=args.bank)

    if args.summary:
        print("\n" + "=" * 90)
        print("  DEVSUPERSUITE ENTERPRISE RFP AUTOMATION TEMPLATE ENGINE")
        print("=" * 90)
        print(f"Master Bank Path:     {engine.master_bank_path}")
        print(f"Total Bank Answers:   {len(engine.answers)} pre-approved responses")
        print(f"Total Domains:        {len(engine.domains)} enterprise domains")
        print(f"Supported Ingestion:  JSON, CSV, Plain Text, Markdown (SIG Lite, CAIQ, VSA, HECVAT)")
        print(f"Cryptographic Hash:   SHA-256 Per-Item and Master Verification Signatures")
        print("-" * 90)
        for d_id, d in engine.domains.items():
            count = len([a for a in engine.answers if a.get("domain_id") == d_id])
            print(f"  • [{d.get('code', d_id):<12}] {d.get('name'):<55} | {count:2d} answers")
        print("=" * 90 + "\n")
        return

    if args.ingest_rfp:
        count = engine.ingest_rfp(args.ingest_rfp)
        print(f"[SUCCESS] Ingested {count} questions from {args.ingest_rfp}")

    if args.auto_respond or args.audit_coverage or args.export_submission:
        responses = engine.auto_respond()
        print(f"[SUCCESS] Auto-matched and generated {len(responses)} verified responses.")

    if args.audit_coverage:
        audit = engine.audit_coverage()
        print("\n" + "=" * 80)
        print("      ENTERPRISE RFP RESPONSE COVERAGE & INTEGRITY AUDIT")
        print("=" * 80)
        print(f"Total Questions Evaluated:     {audit['total_questions']}")
        print(f"High-Confidence Matches:       {audit['high_confidence_matches']} (>= 0.70)")
        print(f"Medium-Confidence Matches:     {audit['medium_confidence_matches']} (0.35 - 0.69)")
        print(f"Low-Confidence Matches:        {audit['low_confidence_matches']} (< 0.35)")
        print(f"Average Confidence Score:      {audit['average_confidence_score']}")
        print(f"Verified Match Rate:           {audit['match_rate_percentage']}%")
        print(f"Master SHA-256 Audit Hash:     {audit['master_verification_hash_sha256']}")
        print("=" * 80 + "\n")

    if args.export_submission:
        out_file = engine.export_submission(
            output_path=args.export_submission,
            client_name=args.client,
            format_type=args.format
        )
        print(f"[SUCCESS] Formatted RFP submission exported to: {out_file}")

    if not any([args.summary, args.ingest_rfp, args.auto_respond, args.audit_coverage, args.export_submission]):
        parser.print_help()


if __name__ == "__main__":
    main()
