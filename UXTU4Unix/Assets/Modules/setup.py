"""
setup.py - First-run wizard, config integrity checking, and reset logic.
"""
import getpass
import os
import subprocess

from . import config as cfg
from .hardware import detect as detect_hardware
from .secure_password import (
    delete_password, get_password, has_password, save_password,
)
from .ui import clear, pause


# Binary permissions

def _ensure_binaries_executable() -> None:
    """
    chmod +x ryzenadj (and dmidecode on macOS) before first use.
    Skips silently if the bit is already set.
    Warns but never aborts if a binary is missing or chmod fails.
    """
    targets = [cfg.RYZENADJ]
    if cfg.KERNEL == "Darwin":
        targets.append(cfg.DMIDECODE)

    for path in targets:
        if not path or not os.path.isfile(path):
            print(f"Warning: binary not found, skipping chmod: {path}")
            continue
        if not os.access(path, os.X_OK):
            try:
                subprocess.run(["chmod", "+x", path], check=True)
                print(f"  chmod +x: {os.path.basename(path)}")
            except subprocess.CalledProcessError as exc:
                print(f"Warning: could not chmod +x {path}: {exc}")


# Sudo password prompt

def _prompt_sudo_password() -> None:
    """Ask for the sudo password, verify it, then store it."""
    while True:
        subprocess.run("sudo -k", shell=True)
        pw = getpass.getpass("Enter your sudo (login) password: ")
        result = subprocess.run(
            ["sudo", "-S", "ls", "/"],
            input=pw.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            save_password(pw)
            return
        print("Incorrect password - please try again.")


# macOS login-item helpers

def _get_login_item_paths() -> list:
    """Return the path of every current login item (macOS only)."""
    result = subprocess.run(
        ["osascript", "-e",
         'tell application "System Events" to get the path of every login item'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    raw = result.stdout.decode().strip()
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def _remove_login_item_by_name(name: str) -> None:
    """Remove all login items whose name matches *name* (macOS only)."""
    subprocess.call(
        ["osascript", "-e",
         f'tell application "System Events" to delete login item "{name}"'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _add_login_item_path(path: str) -> None:
    """Register *path* as a login item (macOS only)."""
    subprocess.call(
        ["osascript", "-e",
         f'tell application "System Events" to make login item at end '
         f'with properties {{path:"{path}", hidden:false}}'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _login_item_status(cmd_file: str) -> bool:
    """
    Return True only when a login item exists and points at *cmd_file* exactly.

    Stale entries (wrong path, moved app) are removed automatically so the
    caller can re-register at the correct location.
    """
    cmd_name = os.path.basename(cmd_file)
    paths    = _get_login_item_paths()
    correct  = os.path.realpath(cmd_file)

    has_correct_entry = False
    has_stale_entry   = False

    for p in paths:
        if os.path.basename(p) == cmd_name:
            if os.path.realpath(p) == correct:
                has_correct_entry = True
            else:
                has_stale_entry = True

    if has_stale_entry:
        _remove_login_item_by_name(cmd_name)
        has_correct_entry = False

    return has_correct_entry


def _add_login_item() -> None:
    """Offer to add the app to Login Items on first run (macOS only)."""
    cmd_file = cfg.CMD_FILE
    if _login_item_status(cmd_file):
        return
    ans = input("Start UXTU4Unix with macOS (Login Items)? (y/n): ").strip().lower()
    if ans == "y":
        _add_login_item_path(cmd_file)


def macos_login_item_validate() -> None:
    """
    Silently fix a stale macOS Login Item entry on every startup.

    _login_item_status() already removes stale entries (wrong path) but
    does not re-register. This function re-adds the item at the correct
    path so the user's startup preference is preserved after a move/rename.

    Rules:
    - No entry at all        -> do nothing (user never opted in).
    - Entry correct          -> do nothing.
    - Entry stale / removed  -> re-register at current CMD_FILE path.
    """
    cmd_file  = cfg.CMD_FILE
    cmd_name  = os.path.basename(cmd_file)
    paths     = _get_login_item_paths()
    correct   = os.path.realpath(cmd_file)

    registered   = False   # any entry with this name exists
    path_correct = False   # and it points to the right place

    for p in paths:
        if os.path.basename(p) == cmd_name:
            registered = True
            if os.path.realpath(p) == correct:
                path_correct = True

    if not registered:
        return   # user never opted in

    if not path_correct:
        # Remove the stale entry (or entries) then re-add at correct path
        _remove_login_item_by_name(cmd_name)
        _add_login_item_path(cmd_file)


# Linux XDG autostart helpers
# Works on GNOME, KDE, XFCE, Cinnamon, MATE and any DE that follows the
# XDG Desktop Application Autostart Specification.

_DESKTOP_FILENAME = "UXTU4Unix.desktop"


def _xdg_autostart_path() -> str:
    """Return the full path to the XDG autostart .desktop file."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return os.path.join(xdg_config, "autostart", _DESKTOP_FILENAME)


def _write_desktop_file(desktop_path: str) -> None:
    """Write the XDG autostart .desktop entry for UXTU4Unix."""
    cmd_file = cfg.CMD_FILE
    python   = "python3"
    content  = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=UXTU4Unix\n"
        "Comment=AMD Zen power management for macOS and Linux\n"
        f"Exec={python} {cmd_file}\n"
        "Terminal=true\n"
        "Hidden=false\n"
        "X-GNOME-Autostart-enabled=true\n"
    )
    os.makedirs(os.path.dirname(desktop_path), exist_ok=True)
    with open(desktop_path, "w") as fh:
        fh.write(content)


def _read_desktop_exec() -> str:
    """
    Parse the Exec= value from the .desktop file.
    Returns an empty string if the file is missing or Exec= is absent.
    """
    desktop_path = _xdg_autostart_path()
    if not os.path.isfile(desktop_path):
        return ""
    with open(desktop_path) as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("Exec="):
                return line[len("Exec="):].strip()
    return ""


def linux_autostart_enabled() -> bool:
    """Return True when the XDG autostart entry exists and is not hidden."""
    desktop_path = _xdg_autostart_path()
    if not os.path.isfile(desktop_path):
        return False
    with open(desktop_path) as fh:
        for line in fh:
            if line.strip().lower() == "hidden=true":
                return False
    return True


def linux_autostart_path_valid() -> bool:
    """
    Return True when the registered Exec= path matches the current CMD_FILE.
    Always returns False when autostart is not enabled.
    """
    if not linux_autostart_enabled():
        return False
    exec_line = _read_desktop_exec()
    # Exec line is "python3 /path/to/UXTU4Unix.py" - extract the script path
    parts = exec_line.split(None, 1)          # split on first whitespace
    registered = parts[-1] if parts else ""   # last token is the script path
    return os.path.realpath(registered) == os.path.realpath(cfg.CMD_FILE)


def linux_autostart_enable() -> None:
    """Create (or overwrite) the XDG autostart entry with the current path."""
    _write_desktop_file(_xdg_autostart_path())


def linux_autostart_disable() -> None:
    """Remove the XDG autostart entry if it exists."""
    desktop_path = _xdg_autostart_path()
    if os.path.isfile(desktop_path):
        os.remove(desktop_path)


def linux_autostart_validate() -> None:
    """
    Silently fix a stale Linux autostart entry on every startup.

    Rules:
    - Not registered at all  -> do nothing (user never opted in).
    - Registered, path OK    -> do nothing.
    - Registered, path wrong -> rewrite .desktop with the correct path.
      (The app was moved/renamed. We repair rather than remove so the
       user's preference to run on startup is preserved.)
    """
    if not linux_autostart_enabled():
        return
    if not linux_autostart_path_valid():
        linux_autostart_enable()   # overwrites with current cfg.CMD_FILE


def _add_linux_autostart() -> None:
    """Offer to enable XDG autostart on first run (Linux only)."""
    if linux_autostart_enabled():
        return
    ans = input("Start UXTU4Unix on login? (XDG autostart) (y/n): ").strip().lower()
    if ans == "y":
        linux_autostart_enable()
        print("Autostart enabled.")


# Default settings

def _apply_defaults() -> None:
    cfg.ensure_sections("User", "Settings", "Info")
    cfg.set("Settings", "Time",           "30")
    cfg.set("Settings", "SoftwareUpdate", "1")
    cfg.set("Settings", "ReApply",        "0")
    cfg.set("Settings", "ApplyOnStart",   "1")
    cfg.set("Settings", "DynamicMode",    "0")
    cfg.set("Settings", "Debug",          "1")
    if cfg.KERNEL == "Darwin":
        cfg.set("Settings", "SIP", "03080000")


# Public API

def run_welcome() -> None:
    """Full first-run wizard: password -> defaults -> hardware detection -> preset."""
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

    # chmod +x binaries before any sudo / dmidecode / ryzenadj call
    clear()
    print("Preparing binaries...")
    _ensure_binaries_executable()
    pause()

    clear()
    _prompt_sudo_password()
    _apply_defaults()
    cfg.save()

    # Hardware detection
    clear()
    print("Detecting hardware - this may take a moment...")
    detect_hardware()

    # Platform-specific startup registration
    if cfg.KERNEL == "Darwin":
        _add_login_item()
        from .hardware import check_nvram
        if not check_nvram():
            from .installer import install_menu
            install_menu()
    elif cfg.KERNEL == "Linux":
        _add_linux_autostart()

    # Preset selection
    from .settings import preset_cfg
    preset_cfg()

    clear()
    print("Setup complete! UXTU4Unix is ready to use.")
    pause()


def check_integrity() -> None:
    """
    Verify config.toml exists, is non-empty, and contains all required keys.
    Trigger the welcome wizard if anything is wrong.
    """
    if not os.path.isfile(cfg.CONFIG_PATH) or os.stat(cfg.CONFIG_PATH).st_size == 0:
        run_welcome()
        return

    cfg.load()

    missing_section = any(
        not cfg.instance().has_section(sec)
        for sec in cfg.REQUIRED
    )
    missing_key = any(
        key not in cfg.instance()[sec]
        for sec, keys in cfg.REQUIRED.items()
        if cfg.instance().has_section(sec)
        for key in keys
    )

    if missing_section or missing_key:
        reset_all()
        return

    if not has_password():
        if not get_password():
            print("Warning: sudo password not found in keyring.")
            print("Go to Settings -> Sudo password to set it.")
            pause()

    # Validate startup registration path on every launch
    if cfg.KERNEL == "Darwin":
        macos_login_item_validate()
    elif cfg.KERNEL == "Linux":
        linux_autostart_validate()


def reset_all() -> None:
    """Delete config and stored password, then re-run the welcome wizard."""
    if os.path.isfile(cfg.CONFIG_PATH):
        os.remove(cfg.CONFIG_PATH)
    delete_password()
    cfg.load()
    run_welcome()