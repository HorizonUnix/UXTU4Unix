#!/usr/bin/env python3
"""
UXTU4Unix - AMD Zen power management for macOS and Linux.
"""
import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.realpath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from Assets.Modules import config as cfg
cfg.load()

from Assets.Modules.about import about_menu
from Assets.Modules.hardware import check_binaries, show_info as hardware_info
from Assets.Modules.power import apply_smu, get_presets, preset_menu
from Assets.Modules.settings import settings_menu
from Assets.Modules.setup import check_integrity, ensure_binaries_executable, run_welcome
from Assets.Modules.updater import check_updates
from Assets.Modules.ui import clear, pause, quit_app


def main():
    subprocess.run("printf '\\e[8;35;80t'", shell=True)
    check_integrity()
    check_binaries()
    ensure_binaries_executable()
    if cfg.get("Settings", "SoftwareUpdate", "0") == "1":
        check_updates()

    if cfg.get("Settings", "ApplyOnStart", "1") == "1":
        presets = get_presets()
        user_mode = cfg.get("User", "Mode")
        if user_mode == "Custom":
            apply_smu("Custom", cfg.get("User", "CustomArgs"))
        elif user_mode in presets:
            apply_smu(presets[user_mode], user_mode)
        else:
            print("Saved preset not found - running setup wizard.")
            pause()
            run_welcome()

    options = {
        "1": ("Apply power management", preset_menu),
        "2": ("Settings", settings_menu),
        "h": ("Hardware information", hardware_info),
        "a": ("About UXTU4Unix", about_menu),
        "q": ("Quit", quit_app),
    }

    while True:
        clear()
        for key, (label, _) in options.items():
            print(f"  {key.upper()}. {label}")
        print()
        choice = input("Option: ").strip().lower()
        action = options.get(choice)
        if action:
            action[1]()
        else:
            print("Invalid option.")
            pause()


if __name__ == "__main__":
    main()