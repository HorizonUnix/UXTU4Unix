"""
setup.py - First-run wizard, config integrity checking, and reset logic.
"""
import getpass
import os
import subprocess

from . import config as cfg
from .hardware import detect as detect_hardware
from .secure_password import delete_password, get_password, has_password, save_password
from .ui import clear, pause


# Binary permissions

def ensure_binaries_executable():
    """chmod +x ryzenadj (and dmidecode on macOS)."""
    targets = [cfg.RYZENADJ]
    if cfg.KERNEL == "Darwin":
        targets.append(cfg.DMIDECODE)
    for path in targets:
        if not path or not os.path.isfile(path):
            print(f"Warning: binary not found: {path}")
            continue
        if not os.access(path, os.X_OK):
            try:
                subprocess.run(["chmod", "+x", path], check=True)
                print(f"  chmod +x: {os.path.basename(path)}")
            except subprocess.CalledProcessError as e:
                print(f"Warning: could not chmod +x {path}: {e}")


# Sudo password

def _prompt_sudo_password():
    while True:
        subprocess.run("sudo -k", shell=True)
        pw = getpass.getpass("Enter your sudo (login) password: ")
        result = subprocess.run(
            ["sudo", "-S", "ls", "/"],
            input=pw.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            save_password(pw)
            return
        print("Incorrect password - please try again.")


# macOS Login Item helpers

def _get_login_item_paths():
    result = subprocess.run(
        ["osascript", "-e", 'tell application "System Events" to get the path of every login item'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    raw = result.stdout.decode().strip()
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def _remove_login_item_by_name(name):
    subprocess.call(
        ["osascript", "-e", f'tell application "System Events" to delete login item "{name}"'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def _add_login_item_path(path):
    subprocess.call(
        ["osascript", "-e",
         f'tell application "System Events" to make login item at end '
         f'with properties {{path:"{path}", hidden:false}}'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def _login_item_status(cmd_file):
    """
    Return True when a login item exists pointing at cmd_file exactly.
    Stale entries (wrong path) are removed automatically.
    """
    cmd_name = os.path.basename(cmd_file)
    correct = os.path.realpath(cmd_file)
    has_correct = False
    has_stale = False
    for p in _get_login_item_paths():
        if os.path.basename(p) == cmd_name:
            if os.path.realpath(p) == correct:
                has_correct = True
            else:
                has_stale = True
    if has_stale:
        _remove_login_item_by_name(cmd_name)
        has_correct = False
    return has_correct


def _add_login_item():
    """Offer to add to Login Items on first run (macOS only)."""
    cmd_file = cfg.CMD_FILE
    if _login_item_status(cmd_file):
        return
    if input("Start UXTU4Unix with macOS (Login Items)? (y/n): ").strip().lower() == "y":
        _add_login_item_path(cmd_file)


def macos_login_item_validate():
    """
    Silently fix a stale macOS Login Item on every startup.
    If user opted in and path is wrong, remove and re-register at correct path.
    """
    cmd_file = cfg.CMD_FILE
    cmd_name = os.path.basename(cmd_file)
    correct = os.path.realpath(cmd_file)
    registered = False
    path_correct = False
    for p in _get_login_item_paths():
        if os.path.basename(p) == cmd_name:
            registered = True
            if os.path.realpath(p) == correct:
                path_correct = True
    if not registered:
        return
    if not path_correct:
        _remove_login_item_by_name(cmd_name)
        _add_login_item_path(cmd_file)


# Linux XDG autostart helpers

_DESKTOP_FILENAME = "UXTU4Unix.desktop"


def _xdg_autostart_path():
    xdg_config = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return os.path.join(xdg_config, "autostart", _DESKTOP_FILENAME)


def _write_desktop_file(desktop_path):
    content = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=UXTU4Unix\n"
        "Comment=AMD Zen power management for macOS and Linux\n"
        f"Exec=python3 {cfg.CMD_FILE}\n"
        "Terminal=true\n"
        "Hidden=false\n"
        "X-GNOME-Autostart-enabled=true\n"
    )
    os.makedirs(os.path.dirname(desktop_path), exist_ok=True)
    with open(desktop_path, "w") as f:
        f.write(content)


def _read_desktop_exec():
    desktop_path = _xdg_autostart_path()
    if not os.path.isfile(desktop_path):
        return ""
    with open(desktop_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("Exec="):
                return line[len("Exec="):].strip()
    return ""


def linux_autostart_enabled():
    desktop_path = _xdg_autostart_path()
    if not os.path.isfile(desktop_path):
        return False
    with open(desktop_path) as f:
        for line in f:
            if line.strip().lower() == "hidden=true":
                return False
    return True


def linux_autostart_path_valid():
    if not linux_autostart_enabled():
        return False
    exec_line = _read_desktop_exec()
    parts = exec_line.split(None, 1)
    registered = parts[-1] if parts else ""
    return os.path.realpath(registered) == os.path.realpath(cfg.CMD_FILE)


def linux_autostart_enable():
    _write_desktop_file(_xdg_autostart_path())


def linux_autostart_disable():
    desktop_path = _xdg_autostart_path()
    if os.path.isfile(desktop_path):
        os.remove(desktop_path)


def linux_autostart_validate():
    """
    Silently fix a stale Linux autostart entry on every startup.
    Repairs path rather than removing so the user's preference is kept.
    """
    if not linux_autostart_enabled():
        return
    if not linux_autostart_path_valid():
        linux_autostart_enable()


def _add_linux_autostart():
    if linux_autostart_enabled():
        return
    if input("Start UXTU4Unix on login? (XDG autostart) (y/n): ").strip().lower() == "y":
        linux_autostart_enable()
        print("Autostart enabled.")


# Defaults

def _apply_defaults():
    cfg.ensure_sections("User", "Settings", "Info")
    cfg.set("Settings", "Time", "3")
    cfg.set("Settings", "SoftwareUpdate", "1")
    cfg.set("Settings", "ReApply", "0")
    cfg.set("Settings", "ApplyOnStart", "1")
    cfg.set("Settings", "DynamicMode", "0")
    cfg.set("Settings", "Debug", "1")
    if cfg.KERNEL == "Darwin":
        cfg.set("Settings", "SIP", "03080000")


# Public API

def run_welcome():
    """First-run wizard: binaries -> password -> hardware -> preset."""
    if cfg.KERNEL not in ("Darwin", "Linux"):
        clear()
        print(f"Unsupported OS: {cfg.KERNEL}  (only macOS and Linux are supported).")
        return

    cfg.ensure_sections("User", "Settings", "Info")
    clear()
    print("-" * 20 + " Welcome to UXTU4Unix " + "-" * 20)
    print("Designed for AMD Zen-based processors on macOS / Linux")
    print("Based on RyzenAdj and inspired by UXTU\n")
    print("Let's do some initial setup.")
    pause()

    clear()
    print("Preparing binaries...")
    ensure_binaries_executable()
    pause()

    clear()
    _prompt_sudo_password()
    _apply_defaults()
    cfg.save()

    clear()
    print("Detecting hardware - this may take a moment...")
    detect_hardware()

    if cfg.KERNEL == "Darwin":
        _add_login_item()
        from .hardware import check_nvram
        if not check_nvram():
            from .installer import install_menu
            install_menu()
    elif cfg.KERNEL == "Linux":
        _add_linux_autostart()

    from .settings import preset_cfg
    preset_cfg()

    clear()
    print("Setup complete! UXTU4Unix is ready to use.")
    pause()


def check_integrity():
    """Verify config exists and has all required keys. Run wizard if not."""
    if not os.path.isfile(cfg.CONFIG_PATH) or os.stat(cfg.CONFIG_PATH).st_size == 0:
        run_welcome()
        return

    cfg.load()

    broken = (
        any(not cfg.instance().has_section(sec) for sec in cfg.REQUIRED)
        or any(
            key not in cfg.instance()[sec]
            for sec, keys in cfg.REQUIRED.items()
            if cfg.instance().has_section(sec)
            for key in keys
        )
    )
    if broken:
        reset_all()
        return

    if not has_password() and not get_password():
        print("Warning: sudo password not found in keyring.")
        print("Go to Settings -> Sudo password to set it.")
        pause()

    if cfg.KERNEL == "Darwin":
        macos_login_item_validate()
    elif cfg.KERNEL == "Linux":
        linux_autostart_validate()


def reset_all():
    if os.path.isfile(cfg.CONFIG_PATH):
        os.remove(cfg.CONFIG_PATH)
    delete_password()
    cfg.load()
    run_welcome()