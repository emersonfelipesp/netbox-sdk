#!/usr/bin/env bash
# netbox-cli installer — pipe to bash, not sh (uses bash builtins)
# curl -fsSL https://raw.githubusercontent.com/emersonfelipesp/netbox-cli/main/install.sh | bash

set -e

REPO="https://github.com/emersonfelipesp/netbox-cli.git"
BRANCH="main"
PACKAGE="git+${REPO}@${BRANCH}"

# ── ANSI colors (disabled when not a TTY) ────────────────────────────────────
if [ -t 1 ]; then
    RESET=$'\033[0m'    BOLD=$'\033[1m'      DIM=$'\033[2m'
    RED=$'\033[1;31m'   GREEN=$'\033[1;32m'  YELLOW=$'\033[1;33m'
    BLUE=$'\033[1;34m'  CYAN=$'\033[1;36m'   WHITE=$'\033[1;37m'
else
    RESET="" BOLD="" DIM="" RED="" GREEN="" YELLOW="" BLUE="" CYAN="" WHITE=""
fi

# ── Spinner ───────────────────────────────────────────────────────────────────
_SPINNER_PID=""

_spin() {
    local msg="$1"
    while true; do
        for _f in '⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠣' '⠏'; do
            printf "\r  ${CYAN}${_f}${RESET}  ${BOLD}%s${RESET}  " "$msg"
            sleep 0.08
        done
    done
}

spinner_start() {
    _spin "$1" &
    _SPINNER_PID=$!
}

spinner_stop() {
    [ -n "$_SPINNER_PID" ] && kill "$_SPINNER_PID" 2>/dev/null; wait "$_SPINNER_PID" 2>/dev/null || true
    _SPINNER_PID=""
    printf "\r\033[2K"
}

spinner_ok()   { spinner_stop; printf "  ${GREEN}✔${RESET}  ${BOLD}%s${RESET}\n" "$1"; }
spinner_fail() { spinner_stop; printf "  ${RED}✘${RESET}  ${BOLD}%s${RESET}\n" "$1"; }

# ── Output helpers ────────────────────────────────────────────────────────────
step() { printf "\n  ${BLUE}›${RESET}  ${BOLD}%s${RESET}\n" "$1"; }
info() { printf "     ${DIM}%s${RESET}\n" "$1"; }
warn() { printf "  ${YELLOW}⚠${RESET}  ${YELLOW}%s${RESET}\n" "$1"; }

fatal() {
    spinner_stop
    printf "\n  ${RED}✘  Error: %s${RESET}\n\n" "$1" >&2
    exit 1
}

# Run a command silently; on failure stop spinner, print stderr, and exit.
run_silent() {
    local tmp
    tmp="$(mktemp)"
    if ! "$@" >"$tmp" 2>&1; then
        spinner_fail "Failed: $*"
        cat "$tmp" >&2
        rm -f "$tmp"
        exit 1
    fi
    rm -f "$tmp"
}

# ── Banner ────────────────────────────────────────────────────────────────────
printf "\n"
printf "  ${CYAN}${BOLD}┌─────────────────────────────────────────┐${RESET}\n"
printf "  ${CYAN}${BOLD}│${RESET}        ${WHITE}${BOLD}netbox-cli  installer${RESET}            ${CYAN}${BOLD}│${RESET}\n"
printf "  ${CYAN}${BOLD}│${RESET}  ${DIM}API-first NetBox CLI + Textual TUI${RESET}    ${CYAN}${BOLD}│${RESET}\n"
printf "  ${CYAN}${BOLD}│${RESET}  ${DIM}github.com/emersonfelipesp/netbox-cli${RESET}  ${CYAN}${BOLD}│${RESET}\n"
printf "  ${CYAN}${BOLD}└─────────────────────────────────────────┘${RESET}\n"
printf "\n"

# ── 1. Ensure uv ─────────────────────────────────────────────────────────────
step "Checking for uv package manager"

UV_BIN=""
if command -v uv > /dev/null 2>&1; then
    UV_BIN="$(command -v uv)"
    spinner_start "Updating uv"
    run_silent "$UV_BIN" self update
    spinner_ok "uv is up to date  ($("$UV_BIN" --version 2>/dev/null))"
else
    info "uv not found — fetching from astral.sh"
    spinner_start "Installing uv"
    run_silent curl -LsSf https://astral.sh/uv/install.sh -o /tmp/_uv_install.sh
    run_silent sh /tmp/_uv_install.sh
    rm -f /tmp/_uv_install.sh

    for candidate in "$HOME/.local/bin/uv" "$HOME/.cargo/bin/uv"; do
        [ -x "$candidate" ] && UV_BIN="$candidate" && break
    done

    if [ -z "$UV_BIN" ]; then
        spinner_fail "uv installed but not found — restart your shell and re-run:"
        printf "\n     ${DIM}curl -fsSL https://raw.githubusercontent.com/emersonfelipesp/netbox-cli/main/install.sh | bash${RESET}\n\n"
        exit 0
    fi

    spinner_ok "uv installed  ($("$UV_BIN" --version 2>/dev/null))"
fi

# ── 2. Install netbox-cli from GitHub ────────────────────────────────────────
step "Installing netbox-cli from GitHub"
info "branch: ${BRANCH}  ·  repo: ${REPO}"

spinner_start "Fetching and building netbox-cli"
run_silent "$UV_BIN" tool install --reinstall --force "$PACKAGE"
spinner_ok "netbox-cli installed"

NBX_BIN=""
for candidate in "$HOME/.local/bin/nbx" "$HOME/.cargo/bin/nbx" "$(command -v nbx 2>/dev/null)"; do
    [ -x "$candidate" ] && NBX_BIN="$candidate" && break
done
[ -z "$NBX_BIN" ] && NBX_BIN="$HOME/.local/bin/nbx"
info "binary: ${NBX_BIN}"

# ── 3. Install Playwright Chromium ────────────────────────────────────────────
step "Installing Playwright Chromium"
info "required for 'nbx demo init'  (browser-based token retrieval)"

PW_LOG="$(mktemp)"
PW_OK=false

spinner_start "Downloading Chromium browser (this may take a minute)"

# Try via uv first, then fall back to the system playwright
if "$UV_BIN" run --with playwright playwright install chromium --with-deps >"$PW_LOG" 2>&1; then
    PW_OK=true
elif command -v playwright > /dev/null 2>&1 && playwright install chromium --with-deps >>"$PW_LOG" 2>&1; then
    PW_OK=true
elif python3 -m playwright install chromium --with-deps >>"$PW_LOG" 2>&1; then
    PW_OK=true
fi

if $PW_OK; then
    spinner_ok "Playwright Chromium ready"
else
    spinner_stop
    warn "Playwright Chromium install skipped (run 'uv tool run --from playwright playwright install chromium --with-deps' manually)"
fi
rm -f "$PW_LOG"

# ── 4. Ensure ~/.local/bin is on PATH ────────────────────────────────────────
LOCAL_BIN="$HOME/.local/bin"
PATH_OK=false
case ":${PATH}:" in
    *":${LOCAL_BIN}:"*) PATH_OK=true ;;
esac

if ! $PATH_OK; then
    step "Setting up PATH"
    info "${LOCAL_BIN} is not in your PATH — adding it now"

    SHELL_RC=""
    case "${SHELL}" in
        */zsh)  SHELL_RC="$HOME/.zshrc" ;;
        */fish) SHELL_RC="$HOME/.config/fish/config.fish" ;;
        *)      SHELL_RC="$HOME/.bashrc" ;;
    esac

    PATH_LINE="export PATH=\"\$HOME/.local/bin:\$PATH\""
    if [ -n "$SHELL_RC" ] && ! grep -qF '.local/bin' "$SHELL_RC" 2>/dev/null; then
        printf '\n# Added by netbox-cli installer\n%s\n' "$PATH_LINE" >> "$SHELL_RC"
        spinner_ok "Added to ${SHELL_RC}"
    fi

    # Apply for this session so the success message works
    export PATH="$LOCAL_BIN:$PATH"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
printf "\n"
printf "  ${GREEN}${BOLD}┌─────────────────────────────────────────┐${RESET}\n"
printf "  ${GREEN}${BOLD}│${RESET}   ${GREEN}${BOLD}✔  netbox-cli is installed!${RESET}           ${GREEN}${BOLD}│${RESET}\n"
printf "  ${GREEN}${BOLD}└─────────────────────────────────────────┘${RESET}\n"
printf "\n"

# PATH warning — installer runs in a subshell so the parent shell won't see
# the updated PATH automatically. Always remind the user.
if ! $PATH_OK; then
    printf "  ${YELLOW}⚠${RESET}  ${BOLD}Reload your shell to use 'nbx':${RESET}\n\n"
    printf "     ${CYAN}source ~/.bashrc${RESET}   ${DIM}# bash${RESET}\n"
    printf "     ${CYAN}source ~/.zshrc${RESET}    ${DIM}# zsh${RESET}\n"
    printf "\n"
    printf "  ${DIM}Or run nbx directly without reloading:${RESET}\n\n"
    printf "     ${CYAN}${NBX_BIN} --help${RESET}\n"
    printf "\n"
fi

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
