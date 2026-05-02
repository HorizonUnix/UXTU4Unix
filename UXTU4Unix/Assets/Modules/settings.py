"""
settings.py - All settings sub-menus.
"""

import getpass
import subprocess

from . import config as cfg
from .power import get_presets, apply_smu
from .secure_password import save_password, has_password
from .ui import clear, pause, confirm

def _toggle_menu(title, description, section, key, *, default="0", enable_label="Enable", disable_label="Disable"):
    """Generic enable/disable toggle sub-menu."""
    while True:
        clear()
        print(f"{'-' * 15} {title} {'-' * 15}")
        print(f"({description})")
        status = cfg.get(section, key, default) == "1"
        print(f"\nStatus: {'Enabled' if status else 'Disabled'}")
        print(f"\n  1. {enable_label}")
        print(f"  2. {disable_label}")
        print("\n  B. Back\n")
        c = input("Option: ").strip().lower()
        if c == "1":
            cfg.set(section, key, "1")
            cfg.save()
        elif c == "2":
            cfg.set(section, key, "0")
            cfg.save()
        elif c == "b":
            break
        else:
            print("Invalid option.")
            pause()


def _verify_sudo(password):
    subprocess.run("sudo -k", shell=True)
    result = subprocess.run(
        ["sudo", "-S", "ls", "/"],
        input=password.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return result.returncode == 0


def preset_cfg():
    presets = get_presets()
    while True:
        clear()
        print("-" * 15 + " Preset " + "-" * 15)
        for i, name in enumerate(presets, 1):
            print(f"  {i}. {name}")
        print("\n  D. Dynamic Mode\n  C. Custom\n  B. Back")
        print("\n  Tip: Dynamic Mode is recommended for normal use.\n")
        c = input("Option: ").strip().lower()
        if c == "b":
            return
        if c == "d":
            cfg.set("User", "Mode", "Balance")
            cfg.set("Settings", "DynamicMode", "1")
            cfg.set("Settings", "ReApply", "1")
            print("Dynamic Mode enabled.")
            pause()
            cfg.save()
            return
        if c == "c":
            args = input("Enter custom ryzenadj arguments: ")
            cfg.set("User", "Mode", "Custom")
            cfg.set("User", "CustomArgs", args)
            cfg.set("Settings", "DynamicMode", "0")
            print("Custom preset saved.")
            pause()
            cfg.save()
            return
        try:
            n = int(c)
            name = list(presets.keys())[n - 1]
            cfg.set("User", "Mode", name)
            cfg.set("Settings", "DynamicMode", "0")
            print(f"Preset '{name}' saved.")
            pause()
            cfg.save()
            return
        except (ValueError, IndexError):
            print("Invalid option.")
            pause()


def sleep_cfg():
    while True:
        clear()
        val = cfg.get("Settings", "Time", "3")
        print("-" * 15 + " Sleep time " + "-" * 15)
        print(f"Auto-reapply every: {val} seconds")
        print("\n  1. Change\n  B. Back\n")
        c = input("Option: ").strip().lower()
        if c == "1":
            new_val = input("New interval in seconds (default 3): ").strip()
            if new_val.isdigit():
                cfg.set("Settings", "Time", new_val)
                cfg.save()
            else:
                print("Invalid value - must be a whole number.")
                pause()
        elif c == "b":
            break
        else:
            print("Invalid option.")
            pause()


def reapply_cfg():
    _toggle_menu("Auto reapply", "Automatically reapply preset on a timer",
                 "Settings", "ReApply",
                 enable_label="Enable Auto reapply", disable_label="Disable Auto reapply")


def applystart_cfg():
    _toggle_menu("Apply on start", "Apply preset when UXTU4Unix launches",
                 "Settings", "ApplyOnStart", default="1",
                 enable_label="Enable Apply on start", disable_label="Disable Apply on start")


def debug_cfg():
    _toggle_menu("Debug", "Show extra process information",
                 "Settings", "Debug", default="1",
                 enable_label="Enable Debug", disable_label="Disable Debug")


def cfu_cfg():
    _toggle_menu("Software update", "Check for updates on launch",
                 "Settings", "SoftwareUpdate", default="1",
                 enable_label="Enable Software update", disable_label="Disable Software update")


def pass_cfg():
    while True:
        clear()
        print("-" * 15 + " Sudo password " + "-" * 15)
        print(f"Stored: {'Yes (system keyring)' if has_password() else 'Not set'}")
        print("\n  1. Change password\n  B. Back\n")
        c = input("Option: ").strip().lower()
        if c == "1":
            while True:
                pw = getpass.getpass("New sudo password: ")
                if _verify_sudo(pw):
                    save_password(pw)
                    print("Password updated.")
                    pause()
                    break
                print("Incorrect password - try again.")
        elif c == "b":
            break
        else:
            print("Invalid option.")
            pause()


def settings_menu():
    def _reset_all():
        from .setup import reset_all
        reset_all()

    while True:
        clear()
        print("-" * 15 + " Settings " + "-" * 15)
        print("  1. Preset")
        print("  2. Sleep time")
        print("  3. Auto reapply")
        print("  4. Apply on start")
        print("  5. Software update")
        print("  6. Sudo password")
        print("  7. Debug")
        print("\n  R. Reset all settings")
        print("  B. Back\n")

        c = input("Option: ").strip().lower()

        base_map = {
            "1": preset_cfg, "2": sleep_cfg, "3": reapply_cfg,
            "4": applystart_cfg, "5": cfu_cfg,
            "6": pass_cfg, "7": debug_cfg,
            "r": _reset_all, "b": None,
        }

        if c == "b":
            break
        action = base_map.get(c)
        if action is None:
            print("Invalid option.")
            pause()
        else:
            action()