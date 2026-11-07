@echo off
title DevSuperSuite - 1-Click Setup
color 0a
echo ===================================================
echo   DEVELOPER SUPERSUITE: VOICE & SECURITY SHIELD
echo ===================================================
echo Installing dependencies for Live Voice & Agent Shield...
python -m pip install -r live-voice-responder\requirements.txt
cd agent-shield && python -m pip install -e . && cd ..
echo.
echo ✅ Setup complete!
echo Launch voice assistant: run live-voice-responder\Launch_LiveVoice.bat
echo Scan security: run agentshield scan
pause
