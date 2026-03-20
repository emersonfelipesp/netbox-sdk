#!/usr/bin/env bash
# netbox-cli installer
# curl -fsSL https://raw.githubusercontent.com/emersonfelipesp/netbox-cli/v2/install.sh | sh

set -e

REPO="https://github.com/emersonfelipesp/netbox-cli.git"
BRANCH="v2"
PACKAGE="git+${REPO}@${BRANCH}"

# ── ANSI colors ───────────────────────────────────────────────────────────────
RESET="\033[0m"
BOLD="\033[1m"
DIM="\033[2m"

BLACK="\033[30m"
RED="\033[1;31m"
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
BLUE="\033[1;34m"
MAGENTA="\033[1;35m"
CYAN="\033[1;36m"
WHITE="\033[1;37m"

BG_BLUE="\033[44m"
BG_CYAN="\033[46m"

# Disable colors when not a TTY
if [ ! -t 1 ]; then
    RESET="" BOLD="" DIM=""
    BLACK="" RED="" GREEN="" YELLOW="" BLUE="" MAGENTA="" CYAN="" WHITE=""
    BG_BLUE="" BG_CYAN=""
fi

# ── Spinner ───────────────────────────────────────────────────────────────────
_SPINNER_PID=""
_SPINNER_FRAMES='⠋⠙⠹⠸⠼⠴⠦⠧⠣⠏'
_SPINNER_LEN=${#_SPINNER_FRAMES}

_spin() {
    local msg="$1"
    local i=0
    while true; do
        local frame="${_SPINNER_FRAMES:$((i % _SPINNER_LEN)):1}"
        printf "\r  ${CYAN}${frame}${RESET}  ${BOLD}%s${RESET}  " "$msg"
        i=$((i + 1))
        sleep 0.08
    done
}

spinner_start() {
    _spin "$1" &
    _SPINNER_PID=$!
    disown "$_SPINNER_PID" 2>/dev/null || true
}

spinner_stop() {
    if [ -n "$_SPINNER_PID" ]; then
        kill "$_SPINNER_PID" 2>/dev/null || true
        wait "$_SPINNER_PID" 2>/dev/null || true
        _SPINNER_PID=""
    fi
    printf "\r\033[2K"   # clear the spinner line
}

spinner_ok() {
    spinner_stop
    printf "  ${GREEN}✔${RESET}  ${BOLD}%s${RESET}\n" "$1"
}

spinner_fail() {
    spinner_stop
    printf "  ${RED}✘${RESET}  ${BOLD}%s${RESET}\n" "$1"
}

# ── Helpers ───────────────────────────────────────────────────────────────────
step() {
    printf "\n  ${BLUE}›${RESET}  ${BOLD}%s${RESET}\n" "$1"
}

info() {
    printf "     ${DIM}%s${RESET}\n" "$1"
}

success() {
    printf "  ${GREEN}✔${RESET}  %s\n" "$1"
}

warn() {
    printf "  ${YELLOW}⚠${RESET}  ${YELLOW}%s${RESET}\n" "$1"
}

fatal() {
    printf "\n  ${RED}✘  Error: %s${RESET}\n\n" "$1" >&2
    exit 1
}

run_silent() {
    local tmp
    tmp="$(mktemp)"
    if ! "$@" >"$tmp" 2>&1; then
        spinner_fail "Command failed: $*"
        cat "$tmp" >&2
        rm -f "$tmp"
        exit 1
    fi
    rm -f "$tmp"
}

# ── Banner ────────────────────────────────────────────────────────────────────
clear_banner() {
    printf "\n"
    printf "  ${CYAN}${BOLD}┌─────────────────────────────────────────┐${RESET}\n"
    printf "  ${CYAN}${BOLD}│${RESET}        ${WHITE}${BOLD}netbox-cli  installer${RESET}            ${CYAN}${BOLD}│${RESET}\n"
    printf "  ${CYAN}${BOLD}│${RESET}  ${DIM}API-first NetBox CLI + Textual TUI${RESET}    ${CYAN}${BOLD}│${RESET}\n"
    printf "  ${CYAN}${BOLD}│${RESET}  ${DIM}github.com/emersonfelipesp/netbox-cli${RESET}  ${CYAN}${BOLD}│${RESET}\n"
    printf "  ${CYAN}${BOLD}└─────────────────────────────────────────┘${RESET}\n"
    printf "\n"
}

clear_banner

# ── 1. Ensure uv ─────────────────────────────────────────────────────────────
step "Checking for uv package manager"

UV_BIN=""
if command -v uv > /dev/null 2>&1; then
    UV_BIN="$(command -v uv)"
    spinner_start "Updating uv"
    run_silent "$UV_BIN" self update
    spinner_ok "uv is up to date  $(${UV_BIN} --version 2>/dev/null)"
else
    info "uv not found — fetching from astral.sh"
    spinner_start "Installing uv"
    run_silent curl -LsSf https://astral.sh/uv/install.sh -o /tmp/_uv_install.sh
    run_silent sh /tmp/_uv_install.sh
    rm -f /tmp/_uv_install.sh

    for candidate in "$HOME/.local/bin/uv" "$HOME/.cargo/bin/uv"; do
        if [ -x "$candidate" ]; then
            UV_BIN="$candidate"
            break
        fi
    done

    if [ -z "$UV_BIN" ]; then
        spinner_fail "uv installed but not found in expected locations"
        warn "Restart your shell and re-run the installer:"
        printf "\n     ${DIM}curl -fsSL https://raw.githubusercontent.com/emersonfelipesp/netbox-cli/v2/install.sh | sh${RESET}\n\n"
        exit 0
    fi

    spinner_ok "uv installed  $("$UV_BIN" --version 2>/dev/null)"
fi

# ── 2. Install netbox-cli from GitHub ────────────────────────────────────────
step "Installing netbox-cli from GitHub"
info "branch: ${BRANCH}  ·  repo: ${REPO}"

spinner_start "Fetching and installing netbox-cli"
run_silent "$UV_BIN" tool install --reinstall --force "$PACKAGE"
spinner_ok "netbox-cli installed"

# Locate nbx binary
NBX_BIN=""
for candidate in "$HOME/.local/bin/nbx" "$HOME/.cargo/bin/nbx" "$(command -v nbx 2>/dev/null)"; do
    if [ -x "$candidate" ]; then
        NBX_BIN="$candidate"
        break
    fi
done
[ -z "$NBX_BIN" ] && NBX_BIN="nbx"

info "binary: ${NBX_BIN}"

# ── 3. Install Playwright Chromium ────────────────────────────────────────────
step "Installing Playwright Chromium"
info "required for  nbx demo init  (browser-based token retrieval)"

spinner_start "Installing Playwright Chromium (this may take a moment)"
if "$UV_BIN" run --with playwright playwright install chromium --with-deps > /tmp/_pw_install.log 2>&1; then
    spinner_ok "Playwright Chromium ready"
elif python3 -m playwright install chromium --with-deps >> /tmp/_pw_install.log 2>&1; then
    spinner_ok "Playwright Chromium ready"
else
    spinner_stop
    warn "Playwright Chromium install skipped"
    info "Run manually if needed:  playwright install chromium"
fi
rm -f /tmp/_pw_install.log

# ── Done ──────────────────────────────────────────────────────────────────────
printf "\n"
printf "  ${GREEN}${BOLD}┌─────────────────────────────────────────┐${RESET}\n"
printf "  ${GREEN}${BOLD}│${RESET}   ${GREEN}${BOLD}✔  netbox-cli is installed!${RESET}           ${GREEN}${BOLD}│${RESET}\n"
printf "  ${GREEN}${BOLD}└─────────────────────────────────────────┘${RESET}\n"
printf "\n"

printf "  ${BOLD}Quick test — NetBox demo instance:${RESET}\n\n"
printf "     ${CYAN}nbx demo init${RESET}                   ${DIM}# authenticate with demo.netbox.dev${RESET}\n"
printf "     ${CYAN}nbx demo dcim devices list${RESET}      ${DIM}# list devices${RESET}\n"
printf "     ${CYAN}nbx demo tui${RESET}                    ${DIM}# launch the interactive TUI${RESET}\n"
printf "\n"
printf "  ${BOLD}Connect to your own NetBox:${RESET}\n\n"
printf "     ${CYAN}nbx init${RESET}                        ${DIM}# enter your URL + API token${RESET}\n"
printf "     ${CYAN}nbx dcim devices list${RESET}\n"
printf "     ${CYAN}nbx tui${RESET}\n"
printf "\n"
printf "  ${DIM}Docs & source: https://github.com/emersonfelipesp/netbox-cli${RESET}\n"
printf "\n"
