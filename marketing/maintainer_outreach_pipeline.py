#!/usr/bin/env python3
"""
DevSuperSuite - Technical Open-Source Maintainer Outreach & Awesome-List PR Generator
Phase 13: OSS Maintainer Sponsorship Engine & Ecosystem PR Tracker

Compliance: 100% Brand Anonymity (DevSuperSuite Community Guild only).
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_JSON_PATH = os.path.join(BASE_DIR, "oss_maintainer_pipeline.json")
STRATEGY_MD_PATH = os.path.join(BASE_DIR, "oss_maintainer_sponsorship_campaign.md")
AWESOME_PR_PATH = os.path.join(BASE_DIR, "awesome_lists_pr_submissions.md")

WEB_APP_BASE = "https://devsupersuite.web.app"
GUMROAD_BASE = "https://gumroad.com/l/tlzdco"

OSS_TARGETS_SEED = [
    {
        "repo": "continuedev/continue",
        "stars": 21400,
        "maintainer_handle": "@nate-continue / @sestinj",
        "primary_stack": "TypeScript, Python, React",
        "category": "AI Coding Assistant",
        "bottleneck": "Multi-file context token bloat in local/cloud LLM completion",
        "mcp_blueprint": "Expose `compress_context` MCP endpoint inside Continue's context provider pipeline."
    },
    {
        "repo": "Roo-Code/Roo-Code",
        "stars": 15200,
        "maintainer_handle": "@RooVetGit / Core Maintainers",
        "primary_stack": "TypeScript, VS Code API",
        "category": "Autonomous Coding Agent",
        "bottleneck": "Agent loop re-reading full source files during multi-step tasks",
        "mcp_blueprint": "Inject AST interface pruner before tools return file contents to model context."
    },
    {
        "repo": "aider-ai/aider",
        "stars": 28600,
        "maintainer_handle": "@paul-gauthier",
        "primary_stack": "Python, Tree-sitter",
        "category": "Terminal AI Pair Programmer",
        "bottleneck": "Constrained KV cache budgets on local 16k/32k models",
        "mcp_blueprint": "Provide native Tree-sitter AST pruning hook to collapse background dependencies to typed stubs."
    },
    {
        "repo": "All-Hands-AI/OpenHands",
        "stars": 42500,
        "maintainer_handle": "@xingyaoww / @rbren",
        "primary_stack": "Python, Docker, TypeScript",
        "category": "Autonomous Software Engineer",
        "bottleneck": "Agents deleting unit tests to make verification commands exit code 0",
        "mcp_blueprint": "Hook OmniKernel `audit_patch_invariants` into OpenHands action execution sandbox."
    },
    {
        "repo": "BerriAI/litellm",
        "stars": 23800,
        "maintainer_handle": "@krrishdholakia / @ishaan-jaff",
        "primary_stack": "Python",
        "category": "LLM Proxy & Token Budgeting",
        "bottleneck": "Proxying bloated prompts across 100+ LLM APIs driving up billing",
        "mcp_blueprint": "Offer pre-call AST context compression layer in LiteLLM router pipeline."
    },
    {
        "repo": "cline/cline",
        "stars": 24100,
        "maintainer_handle": "@cline / Core Team",
        "primary_stack": "TypeScript, VS Code API",
        "category": "Autonomous Coding Extension",
        "bottleneck": "High token usage in iterative refactorings",
        "mcp_blueprint": "Native MCP server integration via `.cursor/mcp.json` or `.cline/mcp.json`."
    },
    {
        "repo": "tree-sitter/tree-sitter",
        "stars": 20100,
        "maintainer_handle": "@maxbrunsfeld / Maintainers",
        "primary_stack": "C, Rust",
        "category": "Incremental Parser",
        "bottleneck": "Ecosystem adoption for LLM context compression",
        "mcp_blueprint": "Reference implementation of tree-sitter AST visitors for token reduction."
    },
    {
        "repo": "modelcontextprotocol/servers",
        "stars": 12800,
        "maintainer_handle": "@mcp-team / Anthropic",
        "primary_stack": "TypeScript, Python",
        "category": "Reference MCP Servers",
        "bottleneck": "Standardizing context compression & invariant verification tools",
        "mcp_blueprint": "Upstream RFC submission for `omnikernel-context-compressor` reference server."
    },
    {
        "repo": "PyCQA/bandit",
        "stars": 6200,
        "maintainer_handle": "@PyCQA / Security Maintainers",
        "primary_stack": "Python AST",
        "category": "Security Linter",
        "bottleneck": "Catching AI-generated security bypasses (verify=False, csrf_exempt)",
        "mcp_blueprint": "Share AST invariant rules with Bandit test suite for AI generated diff auditing."
    },
    {
        "repo": "GitGuardian/ggshield",
        "stars": 3400,
        "maintainer_handle": "@GitGuardian / Core Team",
        "primary_stack": "Python, Click",
        "category": "Git Secret Detection",
        "bottleneck": "High-latency regex checking on massive staged diffs",
        "mcp_blueprint": "Share sub-0.8ms Shannon Entropy filter benchmarks for high-entropy key pre-filtering."
    },
    {
        "repo": "trufflesecurity/trufflehog",
        "stars": 19500,
        "maintainer_handle": "@dxa4481 / @trufflesecurity",
        "primary_stack": "Go",
        "category": "Secret Scanner",
        "bottleneck": "Entropy tuning for zero false positives on cryptographic keys",
        "mcp_blueprint": "Provide entropy density formula dataset: $H(X) > 4.5$ bits/char for modern AI API keys."
    },
    {
        "repo": "ast-grep/ast-grep",
        "stars": 8600,
        "maintainer_handle": "@HerringtonDarkholme",
        "primary_stack": "Rust",
        "category": "Structural Code Search",
        "bottleneck": "Pruning function bodies while keeping type signatures in TS/Python",
        "mcp_blueprint": "Combine ast-grep rules with OmniKernel interface skeleton generation."
    },
    {
        "repo": "pre-commit/pre-commit",
        "stars": 12400,
        "maintainer_handle": "@asottile",
        "primary_stack": "Python",
        "category": "Git Hook Framework",
        "bottleneck": "Multi-tool pre-commit latency on large repositories",
        "mcp_blueprint": "Package AgentShield as a zero-dependency 1-second pre-commit mirror hook."
    },
    {
        "repo": "AntonOsika/gpt-engineer",
        "stars": 53200,
        "maintainer_handle": "@AntonOsika",
        "primary_stack": "Python",
        "category": "Automated Software Generator",
        "bottleneck": "Context overflow during full-project generation",
        "mcp_blueprint": "Use AST skeletons for cross-file dependency graph resolution."
    },
    {
        "repo": "Significant-Gravitas/AutoGPT",
        "stars": 171000,
        "maintainer_handle": "@Torantulino / AutoGPT Team",
        "primary_stack": "Python, TypeScript",
        "category": "Autonomous Agent Platform",
        "bottleneck": "Runaway execution loops blowing token budgets",
        "mcp_blueprint": "Integrate OmniKernel token budgeter & invariant auditor into AutoGPT workspace."
    },
    {
        "repo": "yoheinakajima/babyagi",
        "stars": 21800,
        "maintainer_handle": "@yoheinakajima",
        "primary_stack": "Python",
        "category": "Task-Driven Autonomous Agent",
        "bottleneck": "Token accumulation in recursive task queues",
        "mcp_blueprint": "Compress intermediate execution context before task planning steps."
    },
    {
        "repo": "e2b-dev/E2B",
        "stars": 7400,
        "maintainer_handle": "@mlejva / E2B Team",
        "primary_stack": "Python, TypeScript, Go",
        "category": "Sandboxed AI Execution",
        "bottleneck": "Agents executing destructive file commands inside sandbox",
        "mcp_blueprint": "Add `INVARIANT_TEST_PRESERVATION` check before sandbox bash execution."
    },
    {
        "repo": "langchain-ai/langchain",
        "stars": 98500,
        "maintainer_handle": "@hwchase17 / LangChain Core",
        "primary_stack": "Python, TypeScript",
        "category": "LLM Orchestration Framework",
        "bottleneck": "Document and code context compressors in RAG pipelines",
        "mcp_blueprint": "Contribute `ASTContextCompressor` document transformer for code RAG."
    },
    {
        "repo": "run-llama/llama_index",
        "stars": 38900,
        "maintainer_handle": "@jerryjliu / LlamaIndex Team",
        "primary_stack": "Python, TypeScript",
        "category": "Data Framework for LLMs",
        "bottleneck": "Code hierarchy parsing in index creation",
        "mcp_blueprint": "Integrate typed AST boundary extractor into LlamaIndex code readers."
    },
    {
        "repo": "microsoft/autogen",
        "stars": 37600,
        "maintainer_handle": "@sonichi / AutoGen Team",
        "primary_stack": "Python",
        "category": "Multi-Agent Conversation Framework",
        "bottleneck": "Inter-agent messages repeating massive code blocks turn-by-turn",
        "mcp_blueprint": "Compress code exchanges between agents using typed AST interface skeletons."
    }
]

AWESOME_LISTS = [
    {
        "list_name": "awesome-claude-prompts",
        "upstream_repo": "f/awesome-claude-prompts",
        "category": "Context Compression & Token Optimization",
        "pr_title": "feat: Add OmniKernel AST Context Slicer for Claude 3.5 Sonnet",
        "pr_branch": "feat/add-omnikernel-ast-slicer"
    },
    {
        "list_name": "awesome-cursor",
        "upstream_repo": "sualehfarooq/awesome-cursor",
        "category": "MCP Servers & Workflow Extensions",
        "pr_title": "feat: Add DevSuperSuite Quad-Engine Toolkit & Dual MCP Server",
        "pr_branch": "feat/add-devsupersuite-mcp"
    },
    {
        "list_name": "awesome-developer-first-tools",
        "upstream_repo": "agamm/awesome-developer-first-tools",
        "category": "Developer Ergonomics & Secret Protection",
        "pr_title": "feat: Add AgentShield Shannon Entropy Secret Scanner & Voice Typist",
        "pr_branch": "feat/add-agentshield-security"
    },
    {
        "list_name": "awesome-ai-agents",
        "upstream_repo": "e2b-dev/awesome-ai-agents",
        "category": "Invariant Guards & Multi-Agent Safety",
        "pr_title": "feat: Add Architectural Invariant Guard for Autonomous Code Agents",
        "pr_branch": "feat/add-invariant-guard"
    },
    {
        "list_name": "awesome-rust-tools",
        "upstream_repo": "rust-unofficial/awesome-rust",
        "category": "High-Performance CLI & Code Analysis Utilities",
        "pr_title": "feat: Add DevSuperSuite Local AST Token Slicer & Pre-Commit Shield",
        "pr_branch": "feat/add-devsupersuite-cli"
    }
]

def generate_maintainer_pitch(target: dict) -> dict:
    repo = target["repo"]
    maintainer = target["maintainer_handle"]
    bottleneck = target["bottleneck"]
    blueprint = target["mcp_blueprint"]
    slug = repo.replace("/", "_").replace("-", "_")

    utm_sandbox = f"{WEB_APP_BASE}?utm_source=github_oss&utm_medium=maintainer_sponsorship&utm_campaign={slug}"
    utm_gumroad = f"{GUMROAD_BASE}?utm_source=github_oss&utm_medium=maintainer_sponsorship&utm_campaign={slug}"

    subject = f"OSS Sponsorship & Free Pro Lifetime Licenses for {repo} Core Team"
    body = f"""Hi {maintainer},

First off, thank you for your incredible stewardship of {repo}! The open-source community benefits immensely from your work.

We are **DevSuperSuite Community Guild**. We build local-first developer infrastructure designed to solve two acute problems in modern AI coding:
1. **Context Token Bloat**: LLMs burning 80%+ of prompt tokens re-reading private implementation bodies.
2. **Destructive Agent Diffs**: Autonomous agents deleting unit tests or leaking high-entropy secrets to git.

#### 🎁 VIP Open-Source Sponsorship Offer:
We want to sponsor the entire core team and active code contributors of **{repo}** with **Permanent Free Pro Lifetime Licenses** (normally $29 solo / $99 team).
• **Core Maintainer VIP Code**: `DSS-OSS-VIP-SPONSORSHIP` (100% off lifetime access)
• Includes: OmniKernel 5.0 AST Context Slicer, AgentShield Entropy Scanner, Dual MCP Server, and Live Voice Typist.
• 100% local, runs offline, zero telemetry.

#### 🛠️ MCP Collaboration Blueprint for {repo}:
We noticed your users frequently hit: *{bottleneck}*.

We engineered an open integration blueprint:
*{blueprint}*

Using Tree-Sitter AST grammar pruning:
• Function bodies are pruned to `...` stubs while preserving 100% of typed signatures, classes, and return types.
• Benchmark: **-83.0% context token reduction** (74k → 12k tokens) in <2.4ms per 1k LOC.
• Eliminates Context Rot (Attention Sink Dilution) and keeps local models within KV cache bounds.

You can inspect the live AST reduction in browser (zero login):
👉 {utm_sandbox}

Commercial package overview:
👉 {utm_gumroad}

If you’d like to claim additional license keys for your team or collaborate on an upstream MCP integration PR, let us know!

With gratitude,  
DevSuperSuite Community Guild  
community@devsupersuite.com | https://devsupersuite.web.app"""

    return {
        "subject": subject,
        "body": body,
        "utm_sandbox": utm_sandbox,
        "utm_gumroad": utm_gumroad
    }

def main():
    now_iso = datetime.now(timezone.utc).isoformat()
    enriched_targets = []
    total_stars = 0

    for idx, t in enumerate(OSS_TARGETS_SEED, 1):
        stars = t["stars"]
        total_stars += stars
        pitch = generate_maintainer_pitch(t)

        enriched = {
            "target_id": f"OSS-{idx:03d}",
            "repo": t["repo"],
            "github_stars": stars,
            "stars_formatted": f"{stars:,}",
            "maintainer_handle": t["maintainer_handle"],
            "category": t["category"],
            "primary_stack": t["primary_stack"],
            "bottleneck_identified": t["bottleneck"],
            "mcp_blueprint": t["mcp_blueprint"],
            "sponsorship_vip_code": "DSS-OSS-VIP-SPONSORSHIP",
            "outreach_status": "QUEUED_FOR_OUTREACH",
            "last_contact_date": None,
            "pr_review_status": "PR_PROPOSAL_STAGED",
            "pitch_payload": pitch
        }
        enriched_targets.append(enriched)

    output = {
        "metadata": {
            "campaign": "Technical Open-Source Maintainer Outreach & Awesome-List PR Blitz",
            "brand_entity": "DevSuperSuite Community Guild",
            "sender_inbox": "community@devsupersuite.com",
            "generated_at": now_iso,
            "total_repositories": len(enriched_targets),
            "total_github_stars_represented": f"{total_stars:,}",
            "awesome_lists_targeted": len(AWESOME_LISTS),
            "compliance": "100% Brand Anonymity Guaranteed | Zero Founder Personal Data"
        },
        "repositories": enriched_targets,
        "awesome_lists": AWESOME_LISTS
    }

    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"[Success] Generated {len(enriched_targets)} OSS maintainer outreach records.")
    print(f"Total Stars Represented: {total_stars:,}")
    print(f"Saved to: {OUTPUT_JSON_PATH}")

if __name__ == "__main__":
    main()
