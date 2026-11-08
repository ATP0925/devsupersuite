"""
OmniKernel 5.0 MCP Server: Standard JSON-RPC stdio protocol interface for Cursor, Claude Code, and Windsurf.
Exposes context compression, invariant auditing, and Shannon Entropy security directly to AI agents.
"""

import sys
import json
import logging
from typing import Dict, Any, List
from omnikernel.compressor import ASTContextCompressor, estimate_token_count
from omnikernel.invariants import InvariantGuard

# Configure silent error logging to stderr to prevent corrupting stdio JSON-RPC
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="[OmniKernel-MCP] %(message)s")


def create_tools_manifest() -> List[Dict[str, Any]]:
    return [
        {
            "name": "compress_context",
            "description": "Performs AST-aware neural context compression on code to reduce token usage by 70-85% while preserving all function signatures, types, and exports.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "source_code": {
                        "type": "string",
                        "description": "The raw code string or file content to compress."
                    },
                    "language": {
                        "type": "string",
                        "description": "Language of source (e.g. 'python', 'javascript', 'typescript', 'generic')",
                        "default": "python"
                    }
                },
                "required": ["source_code"]
            }
        },
        {
            "name": "audit_patch_invariants",
            "description": "Audits a proposed code patch against architectural safety invariants (prevents test deletion, CSRF/SSL bypasses, and unauthorized circular dependencies).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "original_code": {
                        "type": "string",
                        "description": "The original baseline code before modification."
                    },
                    "proposed_patch": {
                        "type": "string",
                        "description": "The new modified code proposed by the AI."
                    }
                },
                "required": ["original_code", "proposed_patch"]
            }
        },
        {
            "name": "calculate_roi_savings",
            "description": "Calculates monthly dollar savings and token reductions achieved by OmniKernel AST compression.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "daily_turns": {
                        "type": "integer",
                        "description": "Estimated number of AI prompts per day (default: 150).",
                        "default": 150
                    },
                    "avg_tokens_per_turn": {
                        "type": "integer",
                        "description": "Average uncompressed prompt tokens per turn (default: 4500).",
                        "default": 4500
                    }
                }
            }
        }
    ]


def handle_compress_context(arguments: Dict[str, Any]) -> Dict[str, Any]:
    source = arguments.get("source_code", "")
    lang = arguments.get("language", "python").lower()

    compressor = ASTContextCompressor()
    if lang == "python":
        compressed_text, metrics = compressor.compress_python(source)
    else:
        compressed_text, metrics = compressor.compress_generic(source)

    return {
        "status": "SUCCESS",
        "metrics": metrics,
        "compressed_source": compressed_text
    }


def handle_audit_patch_invariants(arguments: Dict[str, Any]) -> Dict[str, Any]:
    orig = arguments.get("original_code", "")
    patch = arguments.get("proposed_patch", "")
    return InvariantGuard.audit_patch(orig, patch)


def handle_calculate_roi_savings(arguments: Dict[str, Any]) -> Dict[str, Any]:
    daily_turns = arguments.get("daily_turns", 150)
    avg_tokens = arguments.get("avg_tokens_per_turn", 4500)

    # 78% average compression benchmark
    compressed_tokens = int(avg_tokens * 0.22)
    daily_tokens_saved = (avg_tokens - compressed_tokens) * daily_turns
    monthly_tokens_saved = daily_tokens_saved * 30

    # Pricing benchmark: $3.00 per 1M tokens (Claude 3.5 Sonnet / GPT-4o input cache rates)
    monthly_dollar_savings = round((monthly_tokens_saved / 1_000_000) * 3.00, 2)
    annual_dollar_savings = round(monthly_dollar_savings * 12, 2)

    return {
        "daily_tokens_saved": daily_tokens_saved,
        "monthly_tokens_saved": monthly_tokens_saved,
        "monthly_dollar_savings_usd": monthly_dollar_savings,
        "annual_dollar_savings_usd": annual_dollar_savings,
        "roi_on_license": f"{round((monthly_dollar_savings / 29.0) * 100, 1)}% ROI in first month on $29 license"
    }


def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "omnikernel-mcp-server",
                            "version": "5.0.0",
                            "vendor": "DevSuperSuite Labs"
                        }
                    }
                }
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": create_tools_manifest()}
                }
            elif method == "tools/call":
                name = params.get("name")
                args = params.get("arguments", {})

                if name == "compress_context":
                    res = handle_compress_context(args)
                elif name == "audit_patch_invariants":
                    res = handle_audit_patch_invariants(args)
                elif name == "calculate_roi_savings":
                    res = handle_calculate_roi_savings(args)
                else:
                    resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Tool '{name}' not found"}}
                    print(json.dumps(resp), flush=True)
                    continue

                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(res, indent=2)}]
                    }
                }
            else:
                resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method '{method}' unhandled"}}

            print(json.dumps(resp), flush=True)

        except Exception as e:
            err = {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}
            print(json.dumps(err), flush=True)


if __name__ == "__main__":
    main()

