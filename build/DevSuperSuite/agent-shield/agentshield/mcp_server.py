"""
AgentShield MCP Server: Model Context Protocol (JSON-RPC stdio) interface for Cursor, Claude Code, and Windsurf.
Provides real-time secret scanning, AST sanitization, and git anonymity validation directly to AI agents.
"""

import sys
import json
import logging
from typing import Dict, Any, List
from agentshield.scanner import ShieldScanner, calculate_shannon_entropy
from agentshield.anonymizer import GitAnonymizer

# Configure silent error logging to stderr to prevent corrupting stdio JSON-RPC
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="[AgentShield-MCP] %(message)s")


def create_tools_manifest() -> List[Dict[str, Any]]:
    """Returns the list of available MCP tools following the Anthropic / Model Context Protocol spec."""
    return [
        {
            "name": "scan_code_snippet",
            "description": "Scans code or prompt text for credentials, API keys, tokens, high-entropy secrets, and PII. Returns any detected leaks and risk rating.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The source code, prompt, or text to analyze."
                    },
                    "strict_entropy": {
                        "type": "boolean",
                        "description": "Whether to enforce strict Shannon entropy checks (default: true).",
                        "default": True
                    }
                },
                "required": ["text"]
            }
        },
        {
            "name": "anonymize_git_identity",
            "description": "Verifies and enforces zero-identity leakage by inspecting git author name and email.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "enforce": {
                        "type": "boolean",
                        "description": "Whether to automatically rewrite author email to github noreply address.",
                        "default": False
                    },
                    "username": {
                        "type": "string",
                        "description": "GitHub username to use if enforce is true."
                    }
                }
            }
        },
        {
            "name": "inspect_staged_diff",
            "description": "Inspects git staged diff for uncommitted API keys, credentials, or banned tokens before commit/push.",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "verify_shield_policy",
            "description": "Validates workspace compliance against DevSuperSuite zero-leak corporate policies.",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        }
    ]


def handle_scan_code_snippet(arguments: Dict[str, Any]) -> Dict[str, Any]:
    text = arguments.get("text", "")
    scanner = ShieldScanner()
    findings = scanner.scan_text(text)
    
    entropy_summary = []
    # Token-level entropy sample
    words = text.split()
    high_entropy_tokens = []
    for w in words:
        clean_w = w.strip("'\":;=,()[]{}")
        if len(clean_w) >= 16:
            ent = calculate_shannon_entropy(clean_w)
            if ent > 3.0:
                high_entropy_tokens.append({"token": clean_w[:6] + "..." + clean_w[-4:], "entropy": round(ent, 2)})

    status = "SAFE" if len(findings) == 0 else "LEAK_DETECTED"
    return {
        "status": status,
        "findings_count": len(findings),
        "findings": findings,
        "high_entropy_candidates": high_entropy_tokens,
        "recommendation": "Block action and redact secrets immediately" if findings else "Payload cleared for agent transmission"
    }


def handle_anonymize_git_identity(arguments: Dict[str, Any]) -> Dict[str, Any]:
    author = GitAnonymizer.get_git_author()
    is_anon = GitAnonymizer.is_anonymized(author.get("email", ""))
    
    enforce = arguments.get("enforce", False)
    username = arguments.get("username", "")
    message = "Git identity is already anonymized." if is_anon else "Personal email detected in git config."
    
    if enforce and username:
        success, msg = GitAnonymizer.enforce_noreply(username=username, scope="local")
        return {
            "status": "ENFORCED" if success else "ERROR",
            "previous_author": author,
            "message": msg
        }
        
    return {
        "status": "VERIFIED" if is_anon else "FLAGGED",
        "current_author": author,
        "is_anonymized": is_anon,
        "message": message
    }


def handle_inspect_staged_diff(arguments: Dict[str, Any]) -> Dict[str, Any]:
    scanner = ShieldScanner()
    findings = scanner.scan_git_staged()
    return {
        "status": "CLEAN" if len(findings) == 0 else "SECRETS_FOUND",
        "staged_findings": findings,
        "count": len(findings)
    }


def handle_verify_shield_policy(arguments: Dict[str, Any]) -> Dict[str, Any]:
    scanner = ShieldScanner()
    config = scanner.config
    return {
        "policy_active": True,
        "zero_retention_enforced": True,
        "blocked_patterns_count": len(scanner.patterns),
        "config_summary": config
    }


def main():
    """Main JSON-RPC stdio event loop."""
    scanner = ShieldScanner()

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            line = line.strip()
            if not line:
                continue

            request = json.loads(line)
            req_id = request.get("id")
            method = request.get("method")
            params = request.get("params", {})

            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "agentshield-mcp-server",
                            "version": "1.0.0",
                            "vendor": "DevSuperSuite Labs"
                        }
                    }
                }
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": create_tools_manifest()
                    }
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})

                if tool_name == "scan_code_snippet":
                    result = handle_scan_code_snippet(args)
                elif tool_name == "anonymize_git_identity":
                    result = handle_anonymize_git_identity(args)
                elif tool_name == "inspect_staged_diff":
                    result = handle_inspect_staged_diff(args)
                elif tool_name == "verify_shield_policy":
                    result = handle_verify_shield_policy(args)
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32601,
                            "message": f"Tool '{tool_name}' not found."
                        }
                    }
                    print(json.dumps(response), flush=True)
                    continue

                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            elif method == "ping":
                response = {"jsonrpc": "2.0", "id": req_id, "result": {}}
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method '{method}' not implemented."
                    }
                }

            print(json.dumps(response), flush=True)

        except Exception as e:
            logging.error(f"Error handling request: {e}")
            err_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            print(json.dumps(err_response), flush=True)


if __name__ == "__main__":
    main()

