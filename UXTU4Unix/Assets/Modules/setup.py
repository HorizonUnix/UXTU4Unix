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

def _get_login_item_paths() -> list[str]:
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
    # AppleScript returns a comma-separated list: "/path/a, /path/b"
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

    If a stale entry with the right name but a wrong path is found (e.g. the
    item was moved or ended up in the Trash), it is removed automatically so
    the caller can re-register it at the correct location.
    """
    cmd_name  = os.path.basename(cmd_file)
    paths     = _get_login_item_paths()
    correct   = os.path.realpath(cmd_file)

    has_correct_entry = False
    has_stale_entry   = False

    for p in paths:
        if os.path.basename(p) == cmd_name:
            if os.path.realpath(p) == correct:
                has_correct_entry = True
            else:
                has_stale_entry = True

    if has_stale_entry:
        # Remove every entry with this name (stale paths, duplicates, etc.)
        _remove_login_item_by_name(cmd_name)
        has_correct_entry = False   # will need to be re-added

    return has_correct_entry


def _add_login_item() -> None:
    """Offer to add the app to Login Items on first run (macOS only)."""
    cmd_file = cfg.CMD_FILE
    if _login_item_status(cmd_file):
        return
    ans = input("Start UXTU4Unix with macOS (Login Items)? (y/n): ").strip().lower()
    if ans == "y":
        _add_login_item_path(cmd_file)


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

    clear()
    _prompt_sudo_password()
    _apply_defaults()
    cfg.save()

    # Hardware detection
    clear()
    print("Detecting hardware - this may take a moment...")
    detect_hardware()

    # macOS extras
    if cfg.KERNEL == "Darwin":
        _add_login_item()
        # Offer dependency install if NVRAM isn't configured yet
        from .hardware import check_nvram
        if not check_nvram():
            from .installer import install_menu
            install_menu()

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
        # Try to recover silently; warn if still missing
        if not get_password():
            print("Warning: sudo password not found in keyring.")
            print("Go to Settings -> Sudo password to set it.")
            pause()


def reset_all() -> None:
    """Delete config and stored password, then re-run the welcome wizard."""
    if os.path.isfile(cfg.CONFIG_PATH):
        os.remove(cfg.CONFIG_PATH)
    delete_password()
    # Reload empty config
    cfg.load()
    run_welcome()