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
    if not cfg.get("Settings", "Time"):
        cfg.set("Settings", "Time", DEFAULT_SETTINGS_TIME)
    if not cfg.get("Settings", "SoftwareUpdate"):
        cfg.set("Settings", "SoftwareUpdate", DEFAULT_SETTINGS_SOFTWARE_UPDATE)
    if not cfg.get("Settings", "ReApply"):
        cfg.set("Settings", "ReApply", DEFAULT_SETTINGS_REAPPLY)
    if not cfg.get("Settings", "ApplyOnStart"):
        cfg.set("Settings", "ApplyOnStart", DEFAULT_SETTINGS_APPLY_ON_START)
    if not cfg.get("Settings", "DynamicMode"):
        cfg.set("Settings", "DynamicMode", DEFAULT_SETTINGS_DYNAMIC_MODE)
    if not cfg.get("Settings", "Debug"):
        cfg.set("Settings", "Debug", DEFAULT_SETTINGS_DEBUG)


def _step(n: int, total: int, title: str) -> None:
    clear()
    print(f"  Step {n}/{total}  —  {title}\n")


def run_welcome() -> None:
    if cfg.KERNEL != "Linux":
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

    def normalize_required(required_value: object) -> dict[str, tuple[str, ...]]:
        """
        Normalize cfg.REQUIRED into:
            {section_name: (required_key_1, required_key_2, ...)}

        Accepted formats:
        - dict[str, iterable[str]]
        - iterable[str] (legacy: section names only, no required keys)
        """
        class InvalidRequiredError(Exception):
            pass

        try:
            if isinstance(required_value, dict):
                normalized: dict[str, tuple[str, ...]] = {}
                for section, keys in required_value.items():
                    if not isinstance(section, str):
                        raise InvalidRequiredError("  Warning: ignoring invalid cfg.REQUIRED section name (must be str).")
                    if keys is None:
                        normalized[section] = ()
                        continue
                    if isinstance(keys, (list, tuple, set)):
                        if any(not isinstance(key, str) for key in keys):
                            raise InvalidRequiredError(
                                f"  Warning: ignoring invalid cfg.REQUIRED keys for section '{section}' (must be str)."
                            )
                        normalized[section] = tuple(keys)
                        continue
                    raise InvalidRequiredError(
                        f"  Warning: ignoring invalid cfg.REQUIRED keys container for section '{section}'."
                    )
                return normalized

            if isinstance(required_value, (list, tuple, set)):
                if any(not isinstance(section, str) for section in required_value):
                    raise InvalidRequiredError("  Warning: ignoring invalid cfg.REQUIRED sections (must be str).")
                return {section: () for section in required_value}

            if required_value is not None:
                raise InvalidRequiredError("  Warning: ignoring invalid cfg.REQUIRED format.")
            return {}
        except InvalidRequiredError as error:
            print(error)
            return {}

    required = normalize_required(cfg.REQUIRED)

    def has_all_sections() -> bool:
        return all(cfg.instance().has_section(section) for section in required)

    def has_all_keys() -> bool:
        for section, keys in required.items():
            if not cfg.instance().has_section(section):
                continue
            section_data = cfg.instance()[section]
            if any(key not in section_data for key in keys):
                return False
        return True

    broken = not (has_all_sections() and has_all_keys())
    if broken:
        print("  Warning: configuration integrity check failed.")
        print("  Resetting will remove the current configuration and recreate defaults.")
        if confirm("Do you want to reset the configuration now?", default=False):
            reset_all()
        else:
            print("  Keeping existing configuration unchanged.")
            pause()


def reset_all() -> None:
    if os.path.isfile(cfg.CONFIG_PATH):
        os.remove(cfg.CONFIG_PATH)
    cfg.load()
    run_welcome()
