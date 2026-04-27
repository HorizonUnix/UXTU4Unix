#!/usr/bin/env python3
"""
UXTU4Unix - AMD Zen power management for macOS and Linux.
Entry point: imports modules, runs integrity check, then shows the main menu.
"""
import subprocess
import sys
import os

# Ensure Assets is importable regardless of CWD
_ROOT = os.path.dirname(os.path.realpath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Bootstrap config
from Assets.Modules import config as cfg
cfg.load()

# Module imports
from Assets.Modules.about    import about_menu
from Assets.Modules.hardware import check_binaries, show_info as hardware_info
from Assets.Modules.power    import get_presets, apply_smu, preset_menu
from Assets.Modules.settings import settings_menu
from Assets.Modules.setup    import check_integrity
from Assets.Modules.updater  import check_updates
from Assets.Modules.ui       import clear, pause, quit_app


# Main loop

def main() -> None:
    # Resize terminal for a consistent layout
    subprocess.run("printf '\\e[8;35;80t'", shell=True)

    # Verify config; run first-run setup if needed
    check_integrity()
    # Verify binaries is available before anything else runs
    check_binaries()
    # Software update check
    if cfg.get("Settings", "SoftwareUpdate", "0") == "1":
        check_updates()

    # Apply preset on start
    if cfg.get("Settings", "ApplyOnStart", "1") == "1":
        PRESETS   = get_presets()
        user_mode = cfg.get("User", "Mode")
        if user_mode == "Custom":
            apply_smu("Custom", cfg.get("User", "CustomArgs"))
        elif user_mode in PRESETS:
            apply_smu(PRESETS[user_mode], user_mode)
        else:
            print("Saved preset not found - running setup wizard.")
            pause()
            from Assets.Modules.setup import run_welcome
            run_welcome()

    # Main menu
    OPTIONS = {
        "1": ("Apply power management", preset_menu),
        "2": ("Settings",               settings_menu),
        "h": ("Hardware information",   hardware_info),
        "a": ("About UXTU4Unix",        about_menu),
        "q": ("Quit",                   quit_app),
    }

    while True:
        clear()
        for key, (label, _) in OPTIONS.items():
            print(f"  {key.upper()}. {label}")
        print()
        choice = input("Option: ").strip().lower()
        action = OPTIONS.get(choice)
        if action:
            action[1]()
        else:
            print("Invalid option.")
            pause()


if __name__ == "__main__":
    main()