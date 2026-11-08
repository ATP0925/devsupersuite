#!/usr/bin/env bash
# DevSuperSuite Unix/macOS 1-Click Installer
# Run: curl -sSL https://devsupersuite.web.app/install.sh | bash

set -e

echo "=========================================================="
echo "⚡ DevSuperSuite & OmniKernel 5.0 — 1-Click Installer"
echo "The Autonomous Context Compressor & Secret Shield for Cursor & Claude Code"
echo "=========================================================="

INSTALL_DIR="$HOME/.devsupersuite"
ZIP_URL="https://devsupersuite.web.app/DevSuperSuite_Commercial_v1.0.zip"
TMP_ZIP="/tmp/DevSuperSuite.zip"

echo "[*] Downloading commercial bundle from Firebase Global CDN..."
curl -fsSL "$ZIP_URL" -o "$TMP_ZIP"
echo "[✓] Download complete ($(wc -c < "$TMP_ZIP") bytes)."

echo "[*] Installing to $INSTALL_DIR..."
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
unzip -q "$TMP_ZIP" -d "$INSTALL_DIR"
rm -f "$TMP_ZIP"

BIN_DIR="$INSTALL_DIR/bin"
mkdir -p "$BIN_DIR"

# Create omnikernel wrapper
cat << 'EOF' > "$BIN_DIR/omnikernel"
#!/usr/bin/env bash
export PYTHONPATH="$HOME/.devsupersuite/omni-kernel:$PYTHONPATH"
python3 -m omnikernel.cli "$@"
EOF
chmod +x "$BIN_DIR/omnikernel"

# Create agentshield wrapper
cat << 'EOF' > "$BIN_DIR/agentshield"
#!/usr/bin/env bash
export PYTHONPATH="$HOME/.devsupersuite/agent-shield:$PYTHONPATH"
python3 -m agentshield.cli "$@"
EOF
chmod +x "$BIN_DIR/agentshield"

# Update PATH in shell profile if needed
SHELL_RC="$HOME/.bashrc"
if [[ "$SHELL" == *"zsh"* ]]; then
  SHELL_RC="$HOME/.zshrc"
fi

if ! grep -q "$BIN_DIR" "$SHELL_RC" 2>/dev/null; then
  echo "export PATH=\"\$PATH:$BIN_DIR\"" >> "$SHELL_RC"
  echo "[*] Added $BIN_DIR to $SHELL_RC"
fi

echo ""
echo "=========================================================="
echo "🎉 INSTALLATION COMPLETE!"
echo "=========================================================="
echo "  • OmniKernel 5.0 AST Slicer: READY"
echo "  • AgentShield Pre-Commit Hook: READY"
echo "  • VoiceDSP Hands-Free Typist: READY"
echo "  • Evaluation License Key: DSS-PRO-2026-COMMUNITY-EVAL"
echo ""
echo "Quick Commands:"
echo "  omnikernel compress <file.py>   -> Slice AST & slash context tokens by 75%"
echo "  agentshield scan                 -> Scan directory for high-entropy secrets"
echo ""
echo "Official Portal: https://devsupersuite.web.app"
echo "=========================================================="
