"""
setup.py
"""

from __future__ import annotations

import os
import subprocess

from . import config as cfg
from .hardware import detect as detect_hardware
from .ui import clear, confirm, pause

from .service import (
    install_service,
    restart_service,
    service_running,
    wait_for_daemon_or_warn,
)

DEFAULT_SETTINGS_TIME = "3"
DEFAULT_SETTINGS_SOFTWARE_UPDATE = "1"
DEFAULT_SETTINGS_REAPPLY = "0"
DEFAULT_SETTINGS_APPLY_ON_START = "1"
DEFAULT_SETTINGS_DYNAMIC_MODE = "0"
DEFAULT_SETTINGS_DEBUG = "1"


def ensure_binaries_executable() -> None:
    path = cfg.RYZENADJ
    if path and os.path.isfile(path) and not os.access(path, os.X_OK):
        try:
            subprocess.run(["chmod", "+x", path], check=True)
        except subprocess.CalledProcessError as exc:
            print(f"  Warning: could not mark '{path}' as executable: {exc}")


def _apply_defaults() -> None:
    cfg.ensure_sections("User", "Settings", "Info")
    if not cfg.get("User", "Mode"):
        cfg.set("User", "Mode", "Balance")
    cfg.set("Settings", "Time",           DEFAULT_SETTINGS_TIME)
    cfg.set("Settings", "SoftwareUpdate", DEFAULT_SETTINGS_SOFTWARE_UPDATE)
    cfg.set("Settings", "ReApply",        DEFAULT_SETTINGS_REAPPLY)
    cfg.set("Settings", "ApplyOnStart",   DEFAULT_SETTINGS_APPLY_ON_START)
    cfg.set("Settings", "DynamicMode",    DEFAULT_SETTINGS_DYNAMIC_MODE)
    cfg.set("Settings", "Debug",          DEFAULT_SETTINGS_DEBUG)


def _step(n: int, total: int, title: str) -> None:
    clear()
    print(f"  Step {n}/{total}  —  {title}\n")


def run_welcome() -> None:
    if cfg.KERNEL not in ("Linux",):
        clear()
        print(f"  Unsupported OS: {cfg.KERNEL}")
        return

    cfg.ensure_sections("User", "Settings", "Info")
    total_steps = 3

    _step(1, total_steps, "Welcome")
    print("  UXTU4Linux — AMD Zen power management for Linux")
    print("  Built on RyzenAdj — inspired by UXTU\n")
    pause()

    _step(2, total_steps, "Daemon service")
    _apply_defaults()
    ensure_binaries_executable()
    cfg.save()
    print("  The power daemon runs in the background keeping your preset active.")
    print("  It is required for UXTU4Linux to work properly.\n")
    if confirm("Install and enable daemon service"):
        if service_running():
            restart_service()
        else:
            install_service()
        wait_for_daemon_or_warn(context="setup")
    else:
        print("\n  Daemon is required. Exiting setup.")
        pause()
        return
    pause()

    _step(3, total_steps, "Hardware detection")
    print("  Detecting hardware...\n")
    detect_hardware()

    cpu      = cfg.get("Info", "CPU")
    family   = cfg.get("Info", "Family")
    arch     = cfg.get("Info", "Architecture")
    cpu_type = cfg.get("Info", "Type")
    sig      = cfg.get("Info", "Signature")

    label_width = 14

    def row(label: str, value: str) -> None:
        print(f"  \033[2m{label:<{label_width}}\033[0m  {value}")

    row("CPU",       cpu      or "Not detected")
    row("Family",    family   or "Unknown")
    row("Arch",      arch     or "Unknown")
    row("Type",      cpu_type or "Unknown")
    row("Signature", sig      or "Unknown")
    print()
    pause()

    clear()
    print("  Setup complete. UXTU4Linux is ready.\n")
    pause()


def check_integrity() -> None:
    if not os.path.isfile(cfg.CONFIG_PATH) or os.stat(cfg.CONFIG_PATH).st_size == 0:
        run_welcome()
        return

    cfg.load()

    required = cfg.REQUIRED if isinstance(cfg.REQUIRED, dict) else {s: () for s in cfg.REQUIRED}

    def has_all_sections() -> bool:
        return all(cfg.instance().has_section(section) for section in required)

    def has_all_keys() -> bool:
        for section, keys in required.items():
            if not cfg.instance().has_section(section):
                continue
            if any(key not in cfg.instance()[section] for key in keys):
                return False
        return True

    broken = not (has_all_sections() and has_all_keys())
    if broken:
        reset_all()


def reset_all() -> None:
    if os.path.isfile(cfg.CONFIG_PATH):
        os.remove(cfg.CONFIG_PATH)
    cfg.load()
    run_welcome()
