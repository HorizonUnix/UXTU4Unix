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
    """chmod +x ryzenadj"""
    targets = [cfg.RYZENADJ]
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


# Defaults

def _apply_defaults():
    cfg.ensure_sections("User", "Settings", "Info")
    cfg.set("Settings", "Time", "3")
    cfg.set("Settings", "SoftwareUpdate", "1")
    cfg.set("Settings", "ReApply", "0")
    cfg.set("Settings", "ApplyOnStart", "1")
    cfg.set("Settings", "DynamicMode", "0")
    cfg.set("Settings", "Debug", "1")


# Public API

def run_welcome():
    """First-run wizard: binaries -> password -> hardware -> preset."""
    if cfg.KERNEL not in ("Linux"):
        clear()
        print(f"Unsupported OS: {cfg.KERNEL}  (only Linux are supported).")
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


def reset_all():
    if os.path.isfile(cfg.CONFIG_PATH):
        os.remove(cfg.CONFIG_PATH)
    delete_password()
    cfg.load()
    run_welcome()