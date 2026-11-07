@echo off
title DevSuperSuite - 1-Click Setup & MCP Integrator
color 0a
echo ===================================================
echo   DEVUPERSUITE LABS: VOICE & AGENTSHIELD ENTERPRISE
echo ===================================================
echo [1/3] Installing dependencies for Live Voice Responder...
python -m pip install -r live-voice-responder\requirements.txt
echo [2/3] Installing AgentShield & MCP Server Engine...
cd agent-shield && python -m pip install -e . && cd ..
echo [3/3] Setting up Cursor & Claude Code MCP configuration...
if not exist .cursor mkdir .cursor
copy /y agent-shield\mcp_template.json .cursor\mcp.json >nul 2>&1
copy /y agent-shield\mcp_template.json .mcp.json >nul 2>&1
echo.
echo ===================================================
echo  SETUP COMPLETE - READY FOR AUTONOMOUS OPERATION
echo ===================================================
echo * Launch Voice Coding: live-voice-responder\Launch_LiveVoice.bat
echo * Run Security Audit:  agentshield scan
echo * Cursor / Claude MCP: .cursor\mcp.json generated
echo ===================================================
pause
