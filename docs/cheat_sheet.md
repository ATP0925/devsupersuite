# ⚡ DevSuperSuite & OmniKernel 5.0 — Developer Quick Reference Cheat Sheet

**Live Interactive Sandbox**: [https://devsupersuite.web.app](https://devsupersuite.web.app)  
**Commercial Checkout**: [https://gumroad.com/l/tlzdco](https://gumroad.com/l/tlzdco)  
**Brand Identity**: DevSuperSuite Official / OmniKernel Labs (100% Brand Anonymity Guaranteed)

---

## 🚀 1. One-Minute Quickstart

### Install Binary
```bash
# macOS / Linux
curl -fsSL https://devsupersuite.web.app/install.sh | bash

# Windows (PowerShell Administrator)
iwr -useb https://devsupersuite.web.app/install.ps1 | iex
```

### Activate License (Ed25519 Cryptographic Verification)
```bash
# Offline local validation
devsupersuite activate "DSS-PRO-YOUR-KEY-ED25519-VERIFIED" --offline

# Verify active engines
devsupersuite --version
```

---

## 🛠️ 2. Core CLI Commands Cheat Table

| Command | Key Flags | Description |
| :--- | :--- | :--- |
| `devsupersuite init` | `--lang ts\|py\|go\|rs`<br>`--mode standard\|strict` | Initializes `.devsupersuite.json` workspace config. |
| `devsupersuite slice <path>` | `--clipboard, -c`<br>`--format markdown\|mcp\|raw`<br>`--output <file>` | Extracts AST interfaces, dropping function bodies (-83% tokens). |
| `devsupersuite shield install-hook` | `--entropy-threshold 4.5`<br>`--enforce-tests`<br>`--allow-test-removal` | Installs local pre-commit hook blocking API key leaks & test deletion. |
| `devsupersuite shield scan` | `--staged`<br>`--all` | Manually scans files or staged git diff for high-entropy secrets. |
| `devsupersuite voice start` | `--target cursor\|vscode`<br>`--vad-threshold 0.65`<br>`--barge-in crow` | Starts sub-110ms duplex voice engine with acoustic noise gating. |
| `devsupersuite mcp-setup` | `--target cursor\|claude-code`<br>`--global` | Automatically registers local MCP server into IDE configuration. |

---

## 🔌 3. Instant MCP Configuration Blocks

### Cursor (`.cursor/mcp.json` or Global Settings)
```json
{
  "mcpServers": {
    "devsupersuite": {
      "command": "devsupersuite",
      "args": ["mcp", "serve"],
      "env": {
        "DSS_OFFLINE_MODE": "true",
        "DSS_AST_STRATEGY": "interface-only"
      }
    }
  }
}
```

### Claude Code / Windsurf (`.mcp.json`)
```json
{
  "mcpServers": {
    "omnikernel": {
      "command": "devsupersuite",
      "args": ["mcp", "serve", "--transport", "stdio"],
      "env": {
        "DSS_SHIELD_ENABLED": "true"
      }
    }
  }
}
```

---

## 🛡️ 4. Pre-Commit Hook Configuration

### Option A: Native Git Hook (Recommended — 1 Command)
```bash
devsupersuite shield install-hook --entropy-threshold 4.5 --enforce-tests
```

### Option B: `.pre-commit-config.yaml` (Standard Python/Polyglot Repos)
```yaml
repos:
  - repo: local
    hooks:
      - id: devsupersuite-shield
        name: AgentShield Invariant & Shannon Entropy Guard
        entry: devsupersuite shield scan --staged
        language: system
        stages: [commit]
        pass_filenames: false
```

### Option C: Manual `.git/hooks/pre-commit` Script
```bash
#!/usr/bin/env bash
# .git/hooks/pre-commit
exec devsupersuite shield scan --staged --entropy-threshold 4.5
```

---

## 🎙️ 5. Voice Coding Shortcuts & Verbal Barge-In Triggers

| Trigger / Key | Action | Latency |
| :--- | :--- | :---: |
| **`"CROW"`** (Spoken) | **Instant Verbal Barge-In**: Immediately cuts the audio input pipeline and halts assistant generation. | `<45ms` |
| **`"STOP"`** (Spoken) | Verbal Halt: Cancels current prompt transmission. | `<50ms` |
| **`F8`** (Physical Key) | Push-to-Talk / Toggle Voice Listening State. | `Instant` |
| **`Shift + F8`** | Cycle Target Window (Cursor Composer ↔ VS Code ↔ Terminal). | `Instant` |

---

## 🩺 6. Diagnostic One-Liners & Benchmarks

```bash
# Run complete system diagnostic health check
devsupersuite doctor

# View token savings & compression metrics on current repository
devsupersuite stats

# Test character Shannon entropy on any raw string or token
devsupersuite entropy "sk_live_51M0...98sK"
# Output: Entropy: 5.14 bits/char -> [BLOCKED: Exceeds 4.5 threshold]

# Benchmark AST slicing speed on your largest directory
time devsupersuite slice src/ --format raw > /dev/null
```

---

## 📊 7. Shannon Entropy Quick Reference ($H$)

$$\text{Shannon Entropy: } H(X) = -\sum_{i=1}^{n} P(x_i) \log_2 P(x_i)$$

| Character String Type | Shannon Entropy Range | AgentShield Action |
| :--- | :---: | :---: |
| Normal Code / English Prose | **`2.2 – 3.4 bits/char`** | ✅ Allowed |
| UUIDs / Hex Git SHAs | **`3.0 – 3.6 bits/char`** | ✅ Allowed |
| Base64 Images / Long SVGs | **`3.4 – 3.9 bits/char`** | ✅ Allowed (Heuristic Bypass) |
| **Stripe / OpenAI / AWS API Keys** | **`4.5 – 5.9 bits/char`** | 🚨 **BLOCKED (Exit Code 2)** |

---
*Created by DevSuperSuite Official / OmniKernel Labs.*  
*Online Sandbox: [devsupersuite.web.app](https://devsupersuite.web.app) | Commercial License: [gumroad.com/l/tlzdco](https://gumroad.com/l/tlzdco)*
