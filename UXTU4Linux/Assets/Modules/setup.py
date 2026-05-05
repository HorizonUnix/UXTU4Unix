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


def ensure_binaries_executable() -> None:
    for path in [cfg.RYZENADJ]:
        if path and os.path.isfile(path) and not os.access(path, os.X_OK):
            try:
                subprocess.run(["chmod", "+x", path], check=True)
            except subprocess.CalledProcessError as exc:
                print(f"  Warning: could not mark '{path}' as executable: {exc}")


def _apply_defaults() -> None:
    cfg.ensure_sections("User", "Settings", "Info")
    if not cfg.get("User", "Mode"):
        cfg.set("User", "Mode", "Balance")
    cfg.set("Settings", "Time",           "3")
    cfg.set("Settings", "SoftwareUpdate", "1")
    cfg.set("Settings", "ReApply",        "0")
    cfg.set("Settings", "ApplyOnStart",   "1")
    cfg.set("Settings", "DynamicMode",    "0")
    cfg.set("Settings", "Debug",          "1")


def _step(n: int, total: int, title: str) -> None:
    clear()
    print(f"  Step {n}/{total}  —  {title}\n")


def run_welcome() -> None:
    if cfg.KERNEL not in ("Linux",):
        clear()
        print(f"  Unsupported OS: {cfg.KERNEL}")
        return

    cfg.ensure_sections("User", "Settings", "Info")
    TOTAL = 3

    _step(1, TOTAL, "Welcome")
    print("  UXTU4Linux — AMD Zen power management for Linux")
    print("  Built on RyzenAdj — inspired by UXTU\n")
    pause()

    _step(2, TOTAL, "Daemon service")
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

    _step(3, TOTAL, "Hardware detection")
    print("  Detecting hardware...\n")
    detect_hardware()

    cpu      = cfg.get("Info", "CPU")
    family   = cfg.get("Info", "Family")
    arch     = cfg.get("Info", "Architecture")
    cpu_type = cfg.get("Info", "Type")
    sig      = cfg.get("Info", "Signature")

    W = 14

    def row(label: str, value: str) -> None:
        print(f"  \033[2m{label:<{W}}\033[0m  {value}")

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

    broken = (
        any(not cfg.instance().has_section(s) for s in required)
        or any(
            k not in cfg.instance()[s]
            for s, keys in required.items()
            if cfg.instance().has_section(s)
            for k in keys
        )
    )
    if broken:
        reset_all()


def reset_all() -> None:
    if os.path.isfile(cfg.CONFIG_PATH):
        os.remove(cfg.CONFIG_PATH)
    cfg.load()
    run_welcome()
