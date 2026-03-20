#!/bin/sh
# netbox-cli installer
# Usage: curl -fsSL https://raw.githubusercontent.com/emersonfelipesp/netbox-cli/v2/install.sh | sh

set -e

REPO="https://github.com/emersonfelipesp/netbox-cli.git"
BRANCH="v2"
PACKAGE="git+${REPO}@${BRANCH}"

echo ""
echo "  netbox-cli installer"
echo "  API-first NetBox CLI + Textual TUI"
echo ""

# ── 1. Ensure uv is available ────────────────────────────────────────────────
if ! command -v uv > /dev/null 2>&1; then
    echo "→ uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo ""

    # Pick up uv from the default install location without requiring a shell restart
    UV_BIN=""
    for candidate in "$HOME/.local/bin/uv" "$HOME/.cargo/bin/uv"; do
        if [ -x "$candidate" ]; then
            UV_BIN="$candidate"
            break
        fi
    done

    if [ -z "$UV_BIN" ]; then
        echo "  uv was installed but could not be located automatically."
        echo "  Please restart your shell and re-run this installer:"
        echo ""
        echo "    curl -fsSL https://raw.githubusercontent.com/emersonfelipesp/netbox-cli/v2/install.sh | sh"
        echo ""
        exit 0
    fi
else
    UV_BIN="$(command -v uv)"
    echo "→ uv found at $UV_BIN — updating..."
    "$UV_BIN" self update 2>/dev/null || true
fi

echo ""

# ── 2. Install netbox-cli from GitHub ────────────────────────────────────────
echo "→ Installing netbox-cli from GitHub (branch: ${BRANCH})..."
"$UV_BIN" tool install --reinstall "${PACKAGE}"

# Locate the installed nbx binary
NBX_BIN=""
for candidate in "$HOME/.local/bin/nbx" "$HOME/.cargo/bin/nbx"; do
    if [ -x "$candidate" ]; then
        NBX_BIN="$candidate"
        break
    fi
done
if [ -z "$NBX_BIN" ]; then
    NBX_BIN="nbx"  # rely on PATH if none of the known locations matched
fi

echo ""

# ── 3. Install Playwright + Chromium (needed for demo login) ─────────────────
echo "→ Installing Playwright Chromium (required for 'nbx demo init')..."
"$UV_BIN" run --with playwright playwright install chromium --with-deps 2>/dev/null \
    || "$NBX_BIN" --help > /dev/null 2>&1 \
    && python3 -m playwright install chromium --with-deps 2>/dev/null \
    || echo "  Playwright Chromium install skipped (run 'playwright install chromium' manually if needed)."

echo ""
echo "  netbox-cli is installed!"
echo ""
echo "  Quick test with NetBox demo instance:"
echo ""
echo "    nbx demo init          # authenticate with demo.netbox.dev"
echo "    nbx demo dcim devices list"
echo "    nbx demo tui           # launch the interactive TUI"
echo ""
echo "  Connect to your own NetBox:"
echo ""
echo "    nbx init               # enter your URL + API token"
echo "    nbx dcim devices list"
echo "    nbx tui"
echo ""
echo "  Docs & source: https://github.com/emersonfelipesp/netbox-cli"
echo ""
