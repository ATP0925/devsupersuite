# DevSuperSuite & OmniKernel 5.0 — Developer Documentation & Interactive Quick-Start Cookbook

**Product**: DevSuperSuite Official Developer Platform  
**Core Engines**: OmniKernel 5.0 / AgentShield Invariant Guard / Live Voice Responder  
**Version**: `5.0.4-LTS`  
**Live Interactive Sandbox**: [https://devsupersuite.web.app](https://devsupersuite.web.app)  
**Commercial Checkout**: [https://gumroad.com/l/tlzdco](https://gumroad.com/l/tlzdco) ($29 Pro Lifetime)  
**Publisher**: DevSuperSuite Official / OmniKernel Labs  
**Strict Compliance**: 100% Brand Anonymity Guaranteed. Zero personal names or phone numbers.

---

## 📑 Table of Contents
1. [5-Minute Zero-Friction Quick Start](#1-5-minute-zero-friction-quick-start)
   - [macOS & Linux Installation](#macos--linux-installation)
   - [Windows Installation (PowerShell)](#windows-installation-powershell)
   - [System Verification & Diagnostic Health Check](#system-verification--diagnostic-health-check)
2. [IDE & Autonomous Agent Integration Recipes](#2-ide--autonomous-agent-integration-recipes)
   - [Recipe 2.1: Cursor IDE (Composer & Chat MCP Bridge)](#recipe-21-cursor-ide-composer--chat-mcp-bridge)
   - [Recipe 2.2: Claude Code CLI (CLAUDE.md Rules & Git Hooks)](#recipe-22-claude-code-cli-claudemd-rules--git-hooks)
   - [Recipe 2.3: Windsurf Cascade & VS Code Context Bridge](#recipe-23-windsurf-cascade--vs-code-context-bridge)
   - [Recipe 2.4: Neovim, tmux & Terminal Workflows](#recipe-24-neovim-tmux--terminal-workflows)
3. [Advanced Configuration Cookbook (.devsupersuite.json)](#3-advanced-configuration-cookbook-devsupersuitejson)
   - [Recipe 3.1: Fine-Tuning AST Slicing Depth & Type Retention](#recipe-31-fine-tuning-ast-slicing-depth--type-retention)
   - [Recipe 3.2: AgentShield Shannon Entropy Tuning & Fixture Whitelisting](#recipe-32-agentshield-shannon-entropy-tuning--fixture-whitelisting)
   - [Recipe 3.3: Duplex Voice Audio Tuning, VAD & Verbal Barge-In](#recipe-33-duplex-voice-audio-tuning-vad--verbal-barge-in)
4. [Air-Gapped & Offline Activation (SCIF & Enterprise Compliance)](#4-air-gapped--offline-activation-scif--enterprise-compliance)
5. [Interactive Sandbox & Commercial Licensing](#5-interactive-sandbox--commercial-licensing)

---

## 1. 5-Minute Zero-Friction Quick Start

DevSuperSuite runs as a compiled native binary executing directly on developer workstations. It communicates with local IDEs via the **Model Context Protocol (MCP)** and native operating system pipes.

### macOS & Linux Installation
```bash
# 1. Download and install compiled native binary to /usr/local/bin
curl -fsSL https://devsupersuite.web.app/install.sh | bash

# 2. Activate your Pro Lifetime License (Ed25519 Cryptographic Verification)
devsupersuite activate "DSS-PRO-YOUR-KEY-ED25519-VERIFIED" --offline

# 3. Initialize current workspace
devsupersuite init
```

### Windows Installation (PowerShell Administrator)
```powershell
# 1. Download and install binary to $HOME\.devsupersuite\bin
iwr -useb https://devsupersuite.web.app/install.ps1 | iex

# 2. Activate offline license key
devsupersuite activate "DSS-PRO-YOUR-KEY-ED25519-VERIFIED" --offline

# 3. Initialize current workspace
devsupersuite init
```

### System Verification & Diagnostic Health Check
Verify your local compiler bindings, audio subsystem, and pre-commit hooks in one command:
```bash
devsupersuite doctor
```

**Expected Healthy Diagnostic Output:**
```text
DevSuperSuite System Health Check:
  ✔ Native Tree-sitter parsers: Loaded (TS, JS, PY, GO, RS, C++)
  ✔ AgentShield git hooks: Active (.git/hooks/pre-commit)
  ✔ Shannon Entropy Engine: Calibrated (Threshold 4.50 bits/char)
  ✔ Model Context Protocol (MCP): stdio transport operational
  ✔ Audio DSP Subsystem: 48kHz duplex ready (104ms latency)
  ✔ License status: Pro Lifetime Verified (Ed25519)
All systems operational. Zero cloud dependencies.
```

---

## 2. IDE & Autonomous Agent Integration Recipes

---

### Recipe 2.1: Cursor IDE (Composer & Chat MCP Bridge)

To enable automatic AST context compression in Cursor, configure DevSuperSuite as a local MCP server.

#### Automated Setup
```bash
devsupersuite mcp-setup --target cursor
```

#### Manual Configuration (`.cursor/mcp.json` or Global Cursor Settings)
Create or update `.cursor/mcp.json` in your project root:

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

#### Verification in Cursor:
1. Restart Cursor or reload the window (`Ctrl+Shift+P` / `Cmd+Shift+P` $\rightarrow$ *"Reload Window"*).
2. Open Cursor Composer (`Ctrl+I` / `Cmd+I`).
3. Type: `@BillingService.ts (sliced) how do I invoke the proration handler?`
4. **Notice**: Cursor will receive the AST interface skeleton (~88 tokens) instead of the 1,400-token raw implementation body, cutting token consumption by over **85%**.

---

### Recipe 2.2: Claude Code CLI (`CLAUDE.md` Rules & Git Hooks)

Claude Code CLI uses `CLAUDE.md` in repository roots to guide agent behavior. DevSuperSuite automates rule injection and pairs it with pre-commit enforcement.

#### 1. Inject Deterministic AST Instructions into `CLAUDE.md`
Run the automated injector:
```bash
devsupersuite init --target claude-code
```

This appends optimized context instructions to your project's `CLAUDE.md`:

```markdown
<!-- DevSuperSuite OmniKernel 5.0 Directive -->
## Context Optimization Rules
- When reading external dependencies or background files to inspect types, ALWAYS invoke `devsupersuite slice <path>` rather than reading raw file implementations.
- Preserve public exported types and method signatures; do not inspect inner private loops unless explicitly requested.
- Never modify or truncate existing test suites in `tests/` or `*.spec.*`.
```

#### 2. Install AgentShield Pre-Commit Guard
Prevent Claude Code from accidentally committing leaked API secrets or deleting failing test suites during autonomous refactors:
```bash
devsupersuite shield install-hook --entropy-threshold 4.5 --enforce-tests
```

---

### Recipe 2.3: Windsurf Cascade & VS Code Context Bridge

Windsurf Cascade and standard VS Code support MCP context bridges via global extensions.

#### Configuration (`.codebase/mcp.json` or `.vscode/mcp.json`)
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

### Recipe 2.4: Neovim, tmux & Terminal Workflows

For terminal-first engineers using Neovim, tmux, and CLI tools, DevSuperSuite provides lightweight shell functions.

#### 1. Add Bash / Zsh Helper Function (`~/.bashrc` or `~/.zshrc`)
```bash
# Slices target file and copies typed AST interface directly to clipboard
function dss() {
  devsupersuite slice "$1" --clipboard
  echo "✔ Sliced AST copied to clipboard (-83% tokens)"
}

# Scan staged git diff before manual commit
function dss-check() {
  devsupersuite shield scan --staged
}
```

#### 2. Neovim Keybinding (Lua / `init.lua`)
Bind AST slicing to your clipboard in Neovim:
```lua
vim.keymap.set('n', '<leader>as', function()
  local file = vim.fn.expand('%:p')
  vim.fn.system('devsupersuite slice ' .. vim.fn.shellescape(file) .. ' --clipboard')
  print('OmniKernel: Sliced AST copied to clipboard!')
end, { desc = 'Slice current buffer AST to clipboard' })
```

---

## 3. Advanced Configuration Cookbook (`.devsupersuite.json`)

Customize AST pruning rules, entropy sensitivities, and voice triggers in your repository root.

---

### Recipe 3.1: Fine-Tuning AST Slicing Depth & Type Retention

```json
{
  "$schema": "https://devsupersuite.web.app/schemas/v5/config.schema.json",
  "astSlicer": {
    "enabled": true,
    "strategy": "interface-only",
    "prunePrivateMembers": true,
    "retainDocstrings": true,
    "maxRecursionDepth": 4,
    "excludedDirectories": [
      "node_modules",
      "dist",
      "build",
      ".next",
      "coverage"
    ],
    "languageOverrides": {
      "python": {
        "emitTypeComments": true,
        "stubBodyString": "...",
        "preserveDecorators": ["@property", "@abstractmethod", "@dataclass"]
      },
      "typescript": {
        "stripGenerics": false,
        "preserveTypeAliases": true,
        "pruneInternalHelpers": true
      },
      "go": {
        "retainPackageDoc": true,
        "emitEmptyStructBodies": true
      }
    }
  }
}
```

---

### Recipe 3.2: AgentShield Shannon Entropy Tuning & Fixture Whitelisting

Tune character entropy thresholds ($H$) and whitelist benign test fixtures:

```json
{
  "agentShield": {
    "enabled": true,
    "entropy": {
      "threshold": 4.50,
      "minStringLength": 20,
      "whitelistedTokens": [
        "AKIAIOSFODNN7EXAMPLE",
        "pk_test_sample_public_key_only",
        "mock_jwt_token_for_unit_tests"
      ],
      "ignoredPathPatterns": [
        "tests/fixtures/**",
        "**/mock_data.json"
      ]
    },
    "invariants": {
      "enforceTestImmutability": true,
      "testDirectoryPatterns": [
        "tests/**",
        "__tests__/**",
        "**/*.spec.ts",
        "**/*.test.py"
      ],
      "blockedDiffKeywords": [
        "verify=False",
        "@csrf_exempt",
        "// @ts-ignore"
      ]
    }
  }
}
```

---

### Recipe 3.3: Duplex Voice Audio Tuning, VAD & Verbal Barge-In

Configure Live Voice Responder for mechanical keyboard noise suppression and custom barge-in triggers:

```json
{
  "voice": {
    "targetEditor": "cursor",
    "port": 7788,
    "audio": {
      "sampleRate": 48000,
      "channels": 1,
      "dspAecEnabled": true,
      "noiseGateDb": -28
    },
    "vad": {
      "model": "onnx-silero",
      "sensitivity": 0.65,
      "speechOnsetMs": 15
    },
    "bargeIn": {
      "triggerWord": "crow",
      "alternativeTriggers": ["stop", "cancel", "halt"],
      "cutOffLatencyMs": 45,
      "hardwareHotkey": "F8"
    }
  }
}
```

---

## 4. Air-Gapped & Offline Activation (SCIF & Enterprise Compliance)

DevSuperSuite is built from the ground up for zero-egress, high-security enterprise environments:
- **Zero Outbound Telemetry**: The binary makes no outbound network connections during operation.
- **Ed25519 Asymmetric Verification**: License activation checks cryptographic signatures against a public key compiled into the binary. No remote license server check-in pings are required.

### Offline Activation Command
```bash
# Validates key entirely in memory without internet connectivity
devsupersuite activate "DSS-PRO-YOUR-KEY-ED25519-VERIFIED" --offline
```

### Headless CI/CD Runners & Docker Containers
For containerized build pipelines and headless agents, pass the license key as an environment variable:

```bash
# In your Dockerfile or CI environment variables
export DSS_LICENSE_KEY="DSS-PRO-YOUR-KEY-ED25519-VERIFIED"
export DSS_OFFLINE_MODE="true"

# Verify in container
devsupersuite doctor
```

---

## 5. Interactive Sandbox & Commercial Licensing

### Live Interactive Browser Sandbox (Zero Install / Zero Signup)
Test AST slicing, inspect Concrete Syntax Trees, and calculate Shannon entropy on your own files live in your browser:  
👉 **Browser Sandbox:** [https://devsupersuite.web.app](https://devsupersuite.web.app)

### Commercial Pro Lifetime License ($29 Flat / Perpetual)
Unlock the complete standalone CLI, AgentShield git hooks, local MCP server, and Live Voice Responder:  
👉 **Gumroad Store:** [https://gumroad.com/l/tlzdco](https://gumroad.com/l/tlzdco)

- **One-time payment:** $29 USD (No recurring monthly SaaS subscription).
- **Workstations:** Covers up to 3 machines per developer (work, home, laptop).
- **Updates:** Lifetime updates across the entire OmniKernel 5.x generation.

---
*Maintained by DevSuperSuite Official / OmniKernel Labs.*  
*Cookbook Reference: CBK-2026-OMNI-V5*
