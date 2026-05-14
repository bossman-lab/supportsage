#!/bin/bash
# SupportSage Cura Plugin Installer
# Detects Cura installation and copies the plugin

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_NAME="SupportSagePlugin"

echo "🧠 Installing SupportSage Cura Plugin..."
echo ""

# Detect platform
case "$(uname -s)" in
  Linux*)
    CURA_CONFIG="${HOME}/.local/share/cura"
    ;;
  Darwin*)
    CURA_CONFIG="${HOME}/Library/Application Support/cura"
    ;;
  MINGW*|MSYS*|CYGWIN*)
    CURA_CONFIG="${APPDATA}/cura"
    ;;
  *)
    echo "❌ Unsupported platform: $(uname -s)"
    exit 1
    ;;
esac

# Find latest Cura version
if [ -d "$CURA_CONFIG" ]; then
    VERSIONS=$(ls "$CURA_CONFIG" | grep -E '^[0-9]+\.[0-9]+' | sort -V)
    LATEST=$(echo "$VERSIONS" | tail -1)
    
    if [ -z "$LATEST" ]; then
        echo "⚠️  No Cura versions found in $CURA_CONFIG"
        echo "   Install manually: copy cura_plugin/ to your Cura plugins folder"
        exit 1
    fi
    
    PLUGIN_DIR="${CURA_CONFIG}/${LATEST}/plugins/${PLUGIN_NAME}"
else
    echo "⚠️  Cura config directory not found at $CURA_CONFIG"
    echo "   Install manually:"
    echo "     cp -r cura_plugin \"${CURA_CONFIG}/<version>/plugins/\""
    exit 1
fi

# Install
mkdir -p "$PLUGIN_DIR"
cp -r "${SCRIPT_DIR}/cura_plugin/"* "$PLUGIN_DIR"

echo "✅ SupportSage installed to: $PLUGIN_DIR"
echo ""
echo "📋 Restart Cura and look under:"
echo "   Extensions → SupportSage"
echo ""
echo "🔧 Usage:"
echo "   1. Open your model in Cura"
echo "   2. Extensions → SupportSage → Run SupportSage on Model..."
echo "   3. Select the STL file (it calls the CLI)"
echo "   4. Settings are applied automatically"
echo ""
echo "📦 Or export strategy from CLI first:"
echo "   supportsage export model.stl -f json -o strategy.json"
echo "   Then in Cura: Load Strategy..."
