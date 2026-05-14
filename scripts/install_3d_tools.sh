#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
#   🛠  SupportSage 3D Printing Toolkit — One-Click Install
#   Installs: SupportSage + FilamentDB + Printsight
# ──────────────────────────────────────────────────────────────
set -euo pipefail

REPO="https://github.com/bossman-lab"
VENV_HINT=""

# ── Detect Python / venv ──
if command -v python3 &>/dev/null; then
    PY=python3
elif command -v python &>/dev/null; then
    PY=python
else
    echo "❌ Python 3 not found. Install Python 3.10+ first."
    exit 1
fi

# Check if we're inside a venv
if [ -z "${VIRTUAL_ENV:-}" ]; then
    VENV_HINT=" (may need --break-system-packages)"
fi

PIP_CMD="$PY -m pip install"

echo ""
echo "  🧠 SupportSage 3D Printing Toolkit"
echo "  ─────────────────────────────────────"
echo ""

# ── 1. Install SupportSage (core) ──
echo "  [1/3] Installing SupportSage..."
if [ -d "$(dirname "$0")/.." ]; then
    $PIP_CMD -e "$(dirname "$0")/.." 2>&1 | tail -2
else
    $PIP_CMD "${REPO}/supportsage/releases/download/v0.1.0/supportsage-0.1.0-py3-none-any.whl"
fi
echo "  ✅ SupportSage installed"

# ── 2. Install FilamentDB ──
echo ""
echo "  [2/3] Installing FilamentDB..."
$PIP_CMD "${REPO}/filamentdb/releases/download/v0.1.0/filamentdb-0.1.0-py3-none-any.whl" 2>&1 | tail -2 || {
    echo "  ⚠️  Falling back to git install..."
    TMPDIR=$(mktemp -d)
    git clone --depth 1 "${REPO}/filamentdb.git" "$TMPDIR/filamentdb" 2>/dev/null
    $PIP_CMD -e "$TMPDIR/filamentdb"
    rm -rf "$TMPDIR"
}
echo "  ✅ FilamentDB installed"

# ── 3. Install Printsight ──
echo ""
echo "  [3/3] Installing Printsight..."
$PIP_CMD "${REPO}/printsight/releases/download/v0.2.0/printsight-0.2.0-py3-none-any.whl" 2>&1 | tail -2 || {
    echo "  ⚠️  Falling back to git install..."
    TMPDIR=$(mktemp -d)
    git clone --depth 1 "${REPO}/printsight.git" "$TMPDIR/printsight" 2>/dev/null
    $PIP_CMD -e "$TMPDIR/printsight"
    rm -rf "$TMPDIR"
}
echo "  ✅ Printsight installed"

# ── Verify ──
echo ""
echo "  ── Verification ──"
for cmd in supportsage filamentdb printsight; do
    if command -v "$cmd" &>/dev/null; then
        echo "  ✅ $cmd: $($cmd --version 2>&1 | head -1)"
    else
        echo "  ⚠️  $cmd: not found on PATH"
    fi
done

echo ""
echo "  🎉 Done! Try these:"
echo ""
echo "    # Analyze + filament recommendations"
echo "    supportsage analyze model.stl --filament 'Bambu Lab PLA Basic'"
echo ""
echo "    # Tree supports + filament + print inspection"
echo "    supportsage tree model.stl -o optimized.stl --filament 'eSun PLA+' --inspect after_print.jpg"
echo ""
echo "    # Open the web GUI"
echo "    supportsage-gui --open"
echo ""
