# ⚡ DevSuperSuite & OmniKernel 5.0
### The Autonomous Context Compressor, Invariant Guard & Quad-Engine Dev Toolkit
**Built for 10x Engineers & Vibecoders on Cursor, Claude Code, Antigravity, and VS Code.**

[![Firebase Live](https://img.shields.io/badge/Production-devsupersuite.web.app-brightgreen?style=for-the-badge&logo=firebase)](https://devsupersuite.web.app)
[![MCP Compatible](https://img.shields.io/badge/MCP-Cursor%20%26%20Claude%20Code-cyan?style=for-the-badge&logo=anthropic)](https://devsupersuite.web.app)
[![Gumroad Store](https://img.shields.io/badge/Gumroad_Store-Instant_Delivery_%2429-pink?style=for-the-badge&logo=gumroad)](https://gumroad.com/l/tlzdco)
[![Awesome MCP](https://img.shields.io/badge/Awesome--MCP--Servers-Indexed-blue?style=for-the-badge&logo=github)](https://github.com/ATP0925/awesome-mcp-servers/pull/18866)
[![License](https://img.shields.io/badge/License-Commercial_Solo-purple?style=for-the-badge)](https://gumroad.com/l/tlzdco)

---

## 🚀 The Quad-Engine Architecture

DevSuperSuite solves the four most expensive bottlenecks in AI-assisted software engineering:

### 1. 🧠 OmniKernel 5.0 (AST Context Slicing Engine)
- **Token Bill Slasher**: Slices Python/TypeScript AST trees to preserve typed interfaces, classes, and exported signatures while removing bloated implementation bodies.
- **70%–84% Context Token Savings**: Reduces Claude 3.5 Sonnet / GPT-4o context load from 80k tokens to <18k tokens, eliminating **Context Rot** and saving ~$180+/month in API billing.
- **Model Context Protocol (MCP) JSON-RPC 2.0**: Native `mcp_server.py` integration for Cursor, Claude Code, and Windsurf.

### 2. 🛡️ Architectural Invariant Guard
- **Prevents Destructive AI Patches**: Automatically audits agent git diffs before execution.
- **Test Preservation Invariant**: Blocks AI agents from deleting unit tests to make a build pass (`INVARIANT_TEST_PRESERVATION`).
- **Security Bypass Invariant**: Rejects patches introducing `verify=False`, `@csrf_exempt`, or exposed hardcoded secrets.

### 3. 🎙️ Live Voice Responder
- **Sub-110ms DSP Pipeline**: Full-duplex hands-free voice coding directly into your editor.
- **Acoustic Echo Cancellation**: Filter fan hum, loud keyboard mechanical switches, and mute assistant audio loopback.
- **Voice Barge-In**: Interrupt mid-output instantly by saying *"CROW"* or pressing `F8`.

### 4. 🔒 AgentShield Zero-Day Secret Scanner
- **Shannon Entropy Density**: Detects high-entropy random keys ($H(X) = -\sum P(x) \log_2 P(x)$) across 15+ providers (Stripe, OpenAI, Anthropic, AWS, GitHub PATs).
- **Zero-Latency Pre-Commit**: Pre-commit git hooks that block credential leaks before staging or pushing.

---

## ⚡ 1-Click Terminal Installation (Zero Dependencies)

### Windows (PowerShell):
```powershell
irm https://devsupersuite.web.app/install.ps1 | iex
```

### macOS & Linux (Bash/Zsh):
```bash
curl -sSL https://devsupersuite.web.app/install.sh | bash
```

Installs `omnikernel` (AST context slicer) and `agentshield` (pre-commit secret scanner) directly into your user PATH in under 3 seconds.

---

## 🎮 Live Interactive Playground (No Install Required)

Test the AST slicer, entropy scanner, and ROI calculator in real-time on our Google Cloud CDN:  
👉 **[Launch Live Sandbox at devsupersuite.web.app](https://devsupersuite.web.app)**

---

## ⚡ 1-Click Cursor / Claude Code MCP Setup

Add the following to your `.cursor/mcp.json` or Claude Code config:

```json
{
  "mcpServers": {
    "omnikernel": {
      "command": "python",
      "args": ["-m", "omnikernel.mcp_server"],
      "env": {
        "OMNIKERNEL_GUARD_LEVEL": "STRICT"
      }
    }
  }
}
```

### Available MCP Tools:
- `compress_context`: AST-compresses Python/TypeScript source code to minimal interface stubs.
- `audit_patch_invariants`: Pre-execution invariant auditor for agent diffs and patches.
- `calculate_roi_savings`: Real-time token dollar savings calculator based on provider rates.

---

## 🛒 Commercial Pricing & Instant Download

Instant delivery of standalone binaries, source code, batch launchers, and MCP servers:

| Tier | Price | Commercial License | Included Engines |
| :--- | :---: | :---: | :--- |
| **Developer Solo** | **$29 USD** | Lifetime (1 Developer) | OmniKernel 5.0 + AgentShield + Live Voice + Dual MCP |
| **Team / Studio** | **$99 USD** | Lifetime (Up to 10 Seats) | Everything + Priority Security Updates + Custom Invariant Rules |

👉 **[Instant Card & Global Checkout on Gumroad ($29 / $99)](https://gumroad.com/l/tlzdco)**

---

## 📦 What's Inside the Commercial Archive (`DevSuperSuite_Commercial_v1.0.zip`)

```
DevSuperSuite_Commercial_v1.0/
├── omni-kernel/              # AST context compressor & MCP server
├── agent-shield/             # Shannon entropy zero-day secret shield
├── live-voice-responder/     # Sub-110ms neural voice coding engine
├── .cursor/mcp.json          # Pre-configured Cursor & Claude Code MCP integration
├── Setup_DevSuite.bat        # 1-Click launcher & dependency installer
└── README_COMMERCIAL.txt     # Quickstart documentation & license
```

---

## 🛡️ Privacy & Anonymity Guarantee

DevSuperSuite is built privacy-first. All AST compression and entropy secret scans run **100% locally on your machine**. Zero code, zero tokens, and zero telemetry data ever leave your localhost.

© 2026 DevSuperSuite Official. All rights reserved.
