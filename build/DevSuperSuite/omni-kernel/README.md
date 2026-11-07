# OmniKernel 5.0 (VibeCoding OS & Neural Context Compressor)

> **Eliminate the AI Token Tax & Stop Context Rot in Cursor, Claude Code, and Windsurf.**

---

## The Problem
Modern AI coding models (Claude 3.5 Sonnet, Claude Opus, GPT-4o) suffer from **Context Rot**:
1. When you reference files in your repository, editors like Cursor bundle full implementation bodies into the prompt.
2. Prompts swell to 30,000+ tokens, costing developers $100s/month in API limits.
3. The model gets overwhelmed by implementation noise, hallucinates, or introduces regressions.

---

## The OmniKernel Solution
OmniKernel dynamically parses your code's **Abstract Syntax Tree (AST)**, retains typed function signatures, class interfaces, and docstrings, while cleanly eliding internal implementation details.

- **70% to 85% Token Reduction:** 10,000-token files compress to ~1,800 tokens.
- **100% Symbol Preservation:** AI models retain perfect situational awareness of all types and imports.
- **Architectural Invariant Guard:** Automatically blocks AI patches that delete unit tests or disable security checks.
- **Native Model Context Protocol (MCP) Server:** Seamless stdio integration with Cursor and Claude Code.

---

## 1-Click Installation in Cursor & Claude Code

Add OmniKernel to `.cursor/mcp.json` or `.mcp.json`:

```json
{
  "mcpServers": {
    "omnikernel": {
      "command": "python",
      "args": ["-m", "omnikernel.mcp_server"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

---

## Developer Commercial License
OmniKernel is part of the **DevSuperSuite Commercial Enterprise Edition**:
- **Official Enterprise Portal:** [https://devsupersuite.web.app](https://devsupersuite.web.app)
- **Instant Commercial Purchase:** [https://gumroad.com/l/tlzdco](https://gumroad.com/l/tlzdco)
