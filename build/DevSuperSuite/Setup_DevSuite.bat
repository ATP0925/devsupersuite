@echo off
title DevSuperSuite OmniKernel 5.0 - 1-Click Setup & MCP Integrator
color 0a
echo ================================================================
echo   DEVUPERSUITE LABS: OMNIKERNEL 5.0 + VOICE + AGENTSHIELD
echo ================================================================
echo [1/4] Installing dependencies for Live Voice Responder...
python -m pip install -r live-voice-responder\requirements.txt
echo [2/4] Installing AgentShield Security Guardian...
cd agent-shield && python -m pip install -e . && cd ..
echo [3/4] Installing OmniKernel 5.0 Neural Context Compressor...
cd omni-kernel && python -m pip install -e . && cd ..
echo [4/4] Setting up Cursor & Claude Code Dual MCP Server Config...
if not exist .cursor mkdir .cursor
copy /y mcp_template.json .cursor\mcp.json >nul 2>&1
copy /y mcp_template.json .mcp.json >nul 2>&1
echo.
echo ================================================================
echo  SETUP COMPLETE - DEVUPERSUITE OMNIKERNEL 5.0 OPERATIONAL
echo ================================================================
echo * Launch Voice Coding:  live-voice-responder\Launch_LiveVoice.bat
echo * Run Security Audit:   agentshield scan
echo * Context Compression:  omnikernel compress <file>
echo * Cursor / Claude MCP:  .cursor\mcp.json generated
echo ================================================================
pause
