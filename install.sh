#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/opt/uxtu4unix"
VENV_DIR="$INSTALL_DIR/venv"
VENV_PYTHON="$VENV_DIR/bin/python3"
SRC_DIR="$INSTALL_DIR/src"
BIN_WRAPPER="/usr/local/bin/uxtu4unix"
SERVICE_NAME="uxtu4unix.service"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"
RELEASE_TAG="0.6.0Beta03"
RELEASE_ZIP="UXTU4Unix-v0.6Beta03.zip"
RELEASE_URL="https://github.com/HorizonUnix/UXTU4Unix/releases/download/${RELEASE_TAG}/${RELEASE_ZIP}"
TMP_DIR="$(mktemp -d)"

_R='\033[0m'; _C='\033[0;96m'; _G='\033[0;32m'; _Y='\033[1;33m'; _E='\033[0;31m'
info() { echo -e "${_C}  ·${_R} $*"; }
ok()   { echo -e "${_G}  ✓${_R} $*"; }
warn() { echo -e "${_Y}  !${_R} $*"; }
die()  { echo -e "${_E}  ✗${_R} $*"; exit 1; }
hr()   { echo -e "  $(printf '─%.0s' {1..58})"; }

trap 'rm -rf "$TMP_DIR"' EXIT

[[ $EUID -eq 0 ]] && die "Do not run as root. Run as your normal user:  bash install.sh"

CURRENT_USER="$(whoami)"
CURRENT_GROUP="$(id -gn)"

detect_init() {
    if command -v systemctl &>/dev/null && systemctl --version &>/dev/null 2>&1; then
        echo "systemd"
    elif [[ -f /sbin/openrc ]]; then
        echo "openrc"
    elif [[ -d /run/runit ]]; then
        echo "runit"
    else
        echo "unknown"
    fi
}

detect_pm() {
    if   command -v apt-get &>/dev/null; then echo "apt"
    elif command -v dnf     &>/dev/null; then echo "dnf"
    elif command -v yum     &>/dev/null; then echo "yum"
    elif command -v pacman  &>/dev/null; then echo "pacman"
    elif command -v zypper  &>/dev/null; then echo "zypper"
    else die "Unsupported distro — https://github.com/HorizonUnix/UXTU4Unix"
    fi
}

install_deps() {
    info "Installing dependencies (requires sudo)..."
    case "$1" in
        apt)
            export DEBIAN_FRONTEND=noninteractive
            sudo apt-get update -qq 2>/dev/null
            sudo apt-get install -y -qq --no-install-recommends \
                python3 python3-venv python3-pip \
                dmidecode wget unzip curl \
                gnome-keyring libsecret-1-0 dbus-x11 2>/dev/null
            ;;
        dnf)
            sudo dnf install -y -q python3 python3-pip \
                dmidecode wget unzip curl \
                gnome-keyring libsecret 2>/dev/null
            ;;
        yum)
            sudo yum install -y -q python3 python3-pip \
                dmidecode wget unzip curl \
                gnome-keyring libsecret 2>/dev/null
            ;;
        pacman)
            sudo pacman -Sy --noconfirm --quiet \
                python python-pip \
                dmidecode wget unzip curl \
                gnome-keyring libsecret 2>/dev/null
            ;;
        zypper)
            sudo zypper install -y --quiet python3 python3-pip \
                dmidecode wget unzip curl \
                gnome-keyring libsecret1 2>/dev/null
            ;;
    esac
    ok "Done."
}

download_release() {
    info "Downloading $RELEASE_TAG ..."
    local err="$TMP_DIR/dl.err"
    if command -v wget &>/dev/null; then
        if wget --version 2>&1 | grep -q "GNU Wget2"; then
            wget -q -O "$TMP_DIR/release.zip" "$RELEASE_URL" 2>"$err" \
                || { cat "$err" >&2; die "Download failed."; }
        else
            wget -q --show-progress -O "$TMP_DIR/release.zip" "$RELEASE_URL" 2>"$err" \
                || { cat "$err" >&2; die "Download failed."; }
        fi
    elif command -v curl &>/dev/null; then
        curl -fsSL -o "$TMP_DIR/release.zip" "$RELEASE_URL" 2>"$err" \
            || { cat "$err" >&2; die "Download failed."; }
    else
        die "Neither wget nor curl found."
    fi
    ok "Done."
}

install_files() {
    info "Extracting..."
    unzip -q "$TMP_DIR/release.zip" -d "$TMP_DIR/extracted" || die "Failed to extract."
    local src
    src="$(find "$TMP_DIR/extracted" -maxdepth 1 -mindepth 1 -type d | head -1)"
    [[ -d "$src" ]] || die "Couldn't find source dir in zip."

    # Create install dir owned by the current user
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown "$CURRENT_USER:$CURRENT_GROUP" "$INSTALL_DIR"

    rm -rf "$SRC_DIR"
    cp -r "$src" "$SRC_DIR"
    ok "Installed to $SRC_DIR"
}

patch_entry_point() {
    info "Patching entry point..."
    [[ -f "$SRC_DIR/UXTU4Unix.py" ]] || die "UXTU4Unix.py not found in $SRC_DIR"
    sed -i "1s|.*|#!${VENV_PYTHON}|" "$SRC_DIR/UXTU4Unix.py" || die "sed failed."
    python3 - "$SRC_DIR/UXTU4Unix.py" "${VENV_PYTHON}" <<'PYEOF' || die "Guard injection failed."
import sys
path, venv = sys.argv[1], sys.argv[2]
guard = (
    "import sys as _sys, os as _os\n"
    f"_venv = '{venv}'\n"
    "if _os.path.isfile(_venv) and _os.path.realpath(_sys.executable) != _os.path.realpath(_venv):\n"
    "    _os.execv(_venv, [_venv] + _sys.argv)\n"
)
with open(path, "r") as f:
    lines = f.readlines()
lines.insert(1, guard)
with open(path, "w") as f:
    f.writelines(lines)
PYEOF
    ok "Done."
}

setup_venv() {
    info "Setting up Python venv..."
    local py
    py="$(command -v python3 || command -v python3.12 || command -v python3.11 || command -v python3.10 || true)"
    [[ -n "$py" ]] || die "python3 not found."

    if [[ -d "$VENV_DIR" ]] && ! "$VENV_PYTHON" -c "" &>/dev/null 2>&1; then
        warn "Broken venv — recreating..."
        rm -rf "$VENV_DIR"
    fi

    if [[ ! -d "$VENV_DIR" ]]; then
        "$py" -m venv --without-pip "$VENV_DIR" 2>/dev/null \
            || "$py" -m venv "$VENV_DIR" 2>/dev/null \
            || die "Failed to create venv."
        "$VENV_PYTHON" -m ensurepip --upgrade --default-pip 2>/dev/null || true
    fi

    "$VENV_PYTHON" -m pip install --quiet --no-cache-dir --upgrade pip 2>/dev/null || true

    if [[ -f "$SRC_DIR/requirements.txt" ]]; then
        "$VENV_PYTHON" -m pip install --quiet --no-cache-dir -r "$SRC_DIR/requirements.txt" 2>/dev/null \
            || die "Failed to install requirements."
    else
        warn "No requirements.txt — installing known deps."
        "$VENV_PYTHON" -m pip install --quiet --no-cache-dir pyzmq keyring 2>/dev/null \
            || die "Failed to install deps."
    fi
    ok "Done."
}

set_permissions() {
    info "Setting permissions..."
    chmod +x "$SRC_DIR/UXTU4Unix.py"
    [[ -f "$SRC_DIR/Assets/Linux/ryzenadj" ]] && chmod +x "$SRC_DIR/Assets/Linux/ryzenadj"
    ok "Done."
}

install_wrapper() {
    info "Installing launcher..."
    sudo tee "$BIN_WRAPPER" > /dev/null <<EOF
#!/usr/bin/env bash
exec "$VENV_PYTHON" "$SRC_DIR/UXTU4Unix.py" "\$@"
EOF
    sudo chmod +x "$BIN_WRAPPER"
    [[ -x "$BIN_WRAPPER" ]] || die "Failed to install launcher at $BIN_WRAPPER"
    ok "Launcher → $BIN_WRAPPER"
}

install_service() {
    if [[ "$1" != "systemd" ]]; then
        warn "Init system '$1' not supported — start manually: uxtu4unix"
        return
    fi
    info "Installing systemd service..."
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=UXTU4Unix Power Management Daemon
After=multi-user.target

[Service]
Type=simple
ExecStart=$VENV_PYTHON $SRC_DIR/Assets/Modules/daemon.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME" 2>/dev/null || true
    ok "Service enabled."
}

run_setup() {
    echo ""
    hr
    ok "Installation complete!"
    hr
    echo ""
    info "Launching UXTU4Unix..."
    echo ""
    exec "$BIN_WRAPPER"
}

print_banner() {
    clear
    echo ""
    echo -e "${_C}██╗   ██╗██╗  ██╗████████╗██╗   ██╗██╗  ██╗██╗     ██╗███╗   ██╗██╗   ██╗██╗  ██╗${_R}"
    echo -e "${_C}██║   ██║╚██╗██╔╝╚══██╔══╝██║   ██║██║  ██║██║     ██║████╗  ██║██║   ██║╚██╗██╔╝${_R}"
    echo -e "${_C}██║   ██║ ╚███╔╝    ██║   ██║   ██║███████║██║     ██║██╔██╗ ██║██║   ██║ ╚███╔╝ ${_R}"
    echo -e "${_C}██║   ██║ ██╔██╗    ██║   ██║   ██║╚════██║██║     ██║██║╚██╗██║██║   ██║ ██╔██╗ ${_R}"
    echo -e "${_C}╚██████╔╝██╔╝ ██╗   ██║   ╚██████╔╝     ██║███████╗██║██║ ╚████║╚██████╔╝██╔╝ ██╗${_R}"
    echo -e "${_C} ╚═════╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝      ╚═╝╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝${_R}"
    echo ""
    echo -e "                      ${_Y}Installer  ·  ${RELEASE_TAG}${_R}"
    hr
    echo "  Install path  : $INSTALL_DIR"
    echo "  venv          : $VENV_DIR"
    echo "  Source        : $SRC_DIR"
    echo "  Launcher      : $BIN_WRAPPER"
    echo "  Release       : $RELEASE_URL"
    hr
    echo ""
}

main() {
    print_banner

    local pm init
    pm="$(detect_pm)"
    init="$(detect_init)"
    info "Package manager : $pm"
    info "Init system     : $init"
    echo ""

    install_deps "$pm"
    echo ""
    download_release
    echo ""
    install_files
    echo ""
    patch_entry_point
    echo ""
    setup_venv
    echo ""
    set_permissions
    echo ""
    install_wrapper
    echo ""
    install_service "$init"
    echo ""

    run_setup
}

main "$@"
