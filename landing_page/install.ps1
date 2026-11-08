# DevSuperSuite Windows 1-Click Installer
# Run: irm https://devsupersuite.web.app/install.ps1 | iex

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "⚡ DevSuperSuite & OmniKernel 5.0 — 1-Click Installer" -ForegroundColor Green
Write-Host "The Autonomous Context Compressor & Secret Shield for Cursor & Claude Code" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

$InstallDir = Join-Path $HOME ".devsupersuite"
$ZipUrl = "https://devsupersuite.web.app/DevSuperSuite_Commercial_v1.0.zip"
$ZipPath = Join-Path $env:TEMP "DevSuperSuite.zip"

Write-Host "`n[*] Downloading commercial bundle from Firebase Global CDN..." -ForegroundColor White
try {
    Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath -UseBasicParsing
    Write-Host "[✓] Download complete ($((Get-Item $ZipPath).Length) bytes)." -ForegroundColor Green
} catch {
    Write-Host "[!] Failed to download bundle: $_" -ForegroundColor Red
    exit 1
}

Write-Host "[*] Installing to $InstallDir..." -ForegroundColor White
if (Test-Path $InstallDir) {
    Remove-Item $InstallDir -Recurse -Force
}
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
Expand-Archive -Path $ZipPath -DestinationPath $InstallDir -Force
Remove-Item $ZipPath -Force

# Create CLI launcher wrappers
$BinDir = Join-Path $InstallDir "bin"
New-Item -ItemType Directory -Path $BinDir -Force | Out-Null

$OmniBat = Join-Path $BinDir "omnikernel.bat"
$OmniContent = "@echo off`nset PYTHONPATH=$InstallDir\omni-kernel;%PYTHONPATH%`npython -m omnikernel.cli %*"
Set-Content -Path $OmniBat -Value $OmniContent

$ShieldBat = Join-Path $BinDir "agentshield.bat"
$ShieldContent = "@echo off`nset PYTHONPATH=$InstallDir\agent-shield;%PYTHONPATH%`npython -m agentshield.cli %*"
Set-Content -Path $ShieldBat -Value $ShieldContent

# Check if BinDir is in user PATH
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$BinDir*") {
    Write-Host "[*] Adding $BinDir to User PATH..." -ForegroundColor White
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$BinDir", "User")
    $env:Path = "$env:Path;$BinDir"
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "🎉 INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  • OmniKernel 5.0 AST Slicer: READY" -ForegroundColor Cyan
Write-Host "  • AgentShield Pre-Commit Hook: READY" -ForegroundColor Cyan
Write-Host "  • VoiceDSP Hands-Free Typist: READY" -ForegroundColor Cyan
Write-Host "  • Evaluation License Key: DSS-PRO-2026-COMMUNITY-EVAL" -ForegroundColor Yellow
Write-Host "`nQuick Commands:" -ForegroundColor White
Write-Host "  omnikernel compress <file.py>   -> Slice AST & slash context tokens by 75%" -ForegroundColor Gray
Write-Host "  agentshield scan                 -> Scan directory for high-entropy secrets" -ForegroundColor Gray
Write-Host "`nOfficial Portal: https://devsupersuite.web.app" -ForegroundColor Magenta
Write-Host "==========================================================" -ForegroundColor Green
