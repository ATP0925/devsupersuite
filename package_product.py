"""
Autonomous Product Bundler for Developer Voice & Security Suite
Packages live-voice-responder and agent-shield into a turn-key commercial zip release with MCP server support.
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path

BASE_DIR = Path(r"C:\Users\atpad\.gemini\antigravity\scratch")
DIST_DIR = BASE_DIR / "agent-commerce" / "dist"
BUILD_DIR = BASE_DIR / "agent-commerce" / "build" / "DevSuperSuite"

VOICE_DIR = Path(r"C:\Users\atpad\.gemini\config\skills\live-voice-responder")
SHIELD_DIR = BASE_DIR / "agent-shield"

def build_package():
    print("🚀 [Commerce Engine] Packaging Developer SuperSuite...")
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Copy Live Voice Responder
    voice_dest = BUILD_DIR / "live-voice-responder"
    shutil.copytree(VOICE_DIR, voice_dest, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "*.pyc"))
    print("  ✓ Bundled Live Voice Responder")

    # 2. Copy Agent Shield (includes MCP server)
    shield_dest = BUILD_DIR / "agent-shield"
    shutil.copytree(SHIELD_DIR, shield_dest, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "*.pyc"))
    print("  ✓ Bundled Agent Shield with MCP Server")

    # 3. Create One-Click Setup.bat with MCP Auto-Config
    setup_bat = BUILD_DIR / "Setup_DevSuite.bat"
    with open(setup_bat, "w", encoding="utf-8") as f:
        f.write('''@echo off
title DevSuperSuite - 1-Click Setup & MCP Integrator
color 0a
echo ===================================================
echo   DEVUPERSUITE LABS: VOICE & AGENTSHIELD ENTERPRISE
echo ===================================================
echo [1/3] Installing dependencies for Live Voice Responder...
python -m pip install -r live-voice-responder\\requirements.txt
echo [2/3] Installing AgentShield & MCP Server Engine...
cd agent-shield && python -m pip install -e . && cd ..
echo [3/3] Setting up Cursor & Claude Code MCP configuration...
if not exist .cursor mkdir .cursor
copy /y agent-shield\\mcp_template.json .cursor\\mcp.json >nul 2>&1
copy /y agent-shield\\mcp_template.json .mcp.json >nul 2>&1
echo.
echo ===================================================
echo  SETUP COMPLETE - READY FOR AUTONOMOUS OPERATION
echo ===================================================
echo * Launch Voice Coding: live-voice-responder\\Launch_LiveVoice.bat
echo * Run Security Audit:  agentshield scan
echo * Cursor / Claude MCP: .cursor\\mcp.json generated
echo ===================================================
pause
''')
    print("  ✓ Created 1-Click Setup_DevSuite.bat with MCP support")

    # 4. Create Commercial License & Readme
    readme_txt = BUILD_DIR / "README_COMMERCIAL.txt"
    with open(readme_txt, "w", encoding="utf-8") as f:
        f.write('''==================================================================
  DEVELOPER SUPERSUITE (VOICE + SHIELD + MCP) - COMMERCIAL EDITION
==================================================================
Thank you for acquiring DevSuperSuite Labs tools!

WHAT IS INCLUDED:
1. Live Voice Responder: Full-duplex hands-free voice assistant for
   Claude Code, Cursor, Antigravity, and VS Code. Instant barge-in ("CROW"/"STOP").
2. Agent Shield: Enterprise pre-commit and terminal guardian that blocks
   accidental API key leaks, PII exposure, and destructive commands.
3. Native MCP Server (Model Context Protocol): Direct stdio JSON-RPC tool
   integration for Cursor (.cursor/mcp.json) and Claude Code (.mcp.json).

QUICK START:
1. Double-click Setup_DevSuite.bat
2. Run live-voice-responder\\Launch_LiveVoice.bat
3. Speak naturally—voice commands automatically type and enter into your AI IDE!
4. Cursor/Claude Code will automatically detect tools:
   - scan_code_snippet
   - anonymize_git_identity
   - inspect_staged_diff
   - verify_shield_policy

Commercial Support: contact@devsupersuite.com
Enterprise Portal: https://atp0925.github.io/devsupersuite/
''')

    # 5. Zip into distributable archive
    zip_path = DIST_DIR / "DevSuperSuite_Commercial_v1.0.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(BUILD_DIR):
            for file in files:
                p = Path(root) / file
                rel = p.relative_to(BUILD_DIR)
                zf.write(p, rel)

    file_size_mb = zip_path.stat().st_size / (1024 * 1024)
    file_size_kb = zip_path.stat().st_size / 1024
    print(f"\n🎉 Commercial Bundle Created: {zip_path} ({file_size_kb:.1f} KB / {file_size_mb:.2f} MB)")
    return str(zip_path)

if __name__ == "__main__":
    build_package()
