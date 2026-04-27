"""
settings.py - All settings sub-menus (preset, sleep, reapply, SIP, etc.).
"""
import getpass
import subprocess

from . import config as cfg
from .power import get_presets, apply_smu
from .secure_password import get_password, save_password, has_password
from .ui import clear, pause, confirm

# Helpers

def _toggle_menu(
    title: str,
    description: str,
    section: str,
    key: str,
    *,
    default: str = "0",
    enable_label: str = "Enable",
    disable_label: str = "Disable",
) -> None:
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


def _verify_sudo(password: str) -> bool:
    subprocess.run("sudo -k", shell=True)
    result = subprocess.run(
        ["sudo", "-S", "ls", "/"],
        input=password.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.returncode == 0


# Individual sub-menus

def preset_cfg() -> None:
    PRESETS = get_presets()
    while True:
        clear()
        print("-" * 15 + " Preset " + "-" * 15)
        for i, name in enumerate(PRESETS, 1):
            print(f"  {i}. {name}")
        print("\n  D. Dynamic Mode\n  C. Custom (Beta)\n  B. Back")
        print("\n  Tip: Dynamic Mode is recommended for normal use.\n")
        c = input("Option: ").strip().lower()

        if c == "b":
            return

        if c == "d":
            cfg.set("User",     "Mode", "Balance")
            cfg.set("Settings", "DynamicMode", "1")
            cfg.set("Settings", "ReApply",     "1")
            print("Dynamic Mode enabled.")
            pause()
            cfg.save()
            return

        if c == "c":
            args = input("Enter custom ryzenadj arguments: ")
            cfg.set("User",     "Mode",       "Custom")
            cfg.set("User",     "CustomArgs", args)
            cfg.set("Settings", "DynamicMode", "0")
            print("Custom preset saved.")
            pause()
            cfg.save()
            return

        try:
            n = int(c)
            name = list(PRESETS.keys())[n - 1]
            cfg.set("User",     "Mode", name)
            cfg.set("Settings", "DynamicMode", "0")
            print(f"Preset '{name}' saved.")
            pause()
            cfg.save()
            return
        except (ValueError, IndexError):
            print("Invalid option.")
            pause()


def sleep_cfg() -> None:
    while True:
        clear()
        val = cfg.get("Settings", "Time", "30")
        print("-" * 15 + " Sleep time " + "-" * 15)
        print(f"Auto-reapply every: {val} seconds")
        print("\n  1. Change\n  B. Back\n")
        c = input("Option: ").strip().lower()
        if c == "1":
            new_val = input("New interval in seconds (default 30): ").strip()
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


def reapply_cfg() -> None:
    _toggle_menu(
        "Auto reapply", "Automatically reapply preset on a timer",
        "Settings", "ReApply",
        enable_label="Enable Auto reapply",
        disable_label="Disable Auto reapply",
    )


def applystart_cfg() -> None:
    _toggle_menu(
        "Apply on start", "Apply preset when UXTU4Unix launches",
        "Settings", "ApplyOnStart", default="1",
        enable_label="Enable Apply on start",
        disable_label="Disable Apply on start",
    )


def debug_cfg() -> None:
    _toggle_menu(
        "Debug", "Show extra process information",
        "Settings", "Debug", default="1",
        enable_label="Enable Debug",
        disable_label="Disable Debug",
    )


def cfu_cfg() -> None:
    _toggle_menu(
        "Software update", "Check for updates on launch",
        "Settings", "SoftwareUpdate", default="1",
        enable_label="Enable Software update",
        disable_label="Disable Software update",
    )


def pass_cfg() -> None:
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


def sip_cfg() -> None:
    """macOS only - edit the required SIP flags."""
    while True:
        clear()
        sip = cfg.get("Settings", "SIP", "03080000")
        print("-" * 15 + " SIP flags " + "-" * 15)
        print(f"Current: {sip}")
        print("\n  1. Change SIP flags\n  B. Back\n")
        c = input("Option: ").strip().lower()
        if c == "1":
            print("Must include at least ALLOW_UNTRUSTED_KEXTS (0x1).")
            new_sip = input("New SIP flags: ").strip()
            if new_sip:
                cfg.set("Settings", "SIP", new_sip)
                cfg.save()
        elif c == "b":
            break
        else:
            print("Invalid option.")
            pause()


def login_cfg() -> None:
    """Add/remove UXTU4Unix from startup - Login Items on macOS, XDG autostart on Linux."""
    import os
    from . import config as cfg_mod

    if cfg_mod.KERNEL == "Darwin":
        from .setup import (
            _add_login_item_path,
            _login_item_status,
            _remove_login_item_by_name,
        )
        cmd_file = cfg_mod.CMD_FILE
        cmd_name = os.path.basename(cmd_file)

        while True:
            clear()
            enabled = _login_item_status(cmd_file)
            print("-" * 15 + " Run on startup " + "-" * 15)
            print("(macOS Login Items)")
            print(f"\nStatus: {'Enabled' if enabled else 'Disabled'}")
            print("\n  1. Enable\n  2. Disable\n  B. Back\n")
            c = input("Option: ").strip().lower()
            if c == "1":
                if not enabled:
                    _add_login_item_path(cmd_file)
                    print("Added to Login Items.")
                    pause()
                else:
                    print("Already registered at the correct path.")
                    pause()
            elif c == "2":
                if enabled:
                    _remove_login_item_by_name(cmd_name)
                    print("Removed from Login Items.")
                    pause()
                else:
                    print("Not in Login Items.")
                    pause()
            elif c == "b":
                break
            else:
                print("Invalid option.")
                pause()

    elif cfg_mod.KERNEL == "Linux":
        from .setup import (
            linux_autostart_enabled,
            linux_autostart_enable,
            linux_autostart_disable,
        )

        while True:
            clear()
            enabled = linux_autostart_enabled()
            print("-" * 15 + " Run on startup " + "-" * 15)
            print("(XDG autostart - works on GNOME, KDE, XFCE and most DEs)")
            print(f"\nStatus: {'Enabled' if enabled else 'Disabled'}")
            print("\n  1. Enable\n  2. Disable\n  B. Back\n")
            c = input("Option: ").strip().lower()
            if c == "1":
                if not enabled:
                    linux_autostart_enable()
                    print("Autostart enabled.")
                    pause()
                else:
                    print("Already enabled.")
                    pause()
            elif c == "2":
                if enabled:
                    linux_autostart_disable()
                    print("Autostart disabled.")
                    pause()
                else:
                    print("Autostart is not enabled.")
                    pause()
            elif c == "b":
                break
            else:
                print("Invalid option.")
                pause()


# Top-level Settings menu

def settings_menu() -> None:
    from . import config as cfg_mod

    def _open_installer() -> None:
        from .installer import install_menu
        install_menu()

    def _reset_all() -> None:
        from .setup import reset_all
        reset_all()

    while True:
        clear()
        print("-" * 15 + " Settings " + "-" * 15)
        print("  1. Preset")
        print("  2. Sleep time")
        print("  3. Auto reapply")
        print("  4. Apply on start")

        if cfg_mod.KERNEL == "Darwin":
            print("  5. Run on startup")
            print("  6. Software update")
            print("  7. Sudo password")
            print("  8. SIP flags")
            print("  9. Debug")
            print("\n  I. Install UXTU4Unix dependencies")
        else:
            print("  5. Run on startup")
            print("  6. Software update")
            print("  7. Sudo password")
            print("  8. Debug")

        print("\n  R. Reset all settings")
        print("  B. Back\n")

        c = input("Option: ").strip().lower()

        if cfg_mod.KERNEL == "Darwin":
            darwin_map = {
                "1": preset_cfg,
                "2": sleep_cfg,
                "3": reapply_cfg,
                "4": applystart_cfg,
                "5": login_cfg,
                "6": cfu_cfg,
                "7": pass_cfg,
                "8": sip_cfg,
                "9": debug_cfg,
                "i": _open_installer,
                "r": _reset_all,
                "b": None,
            }
            action = darwin_map.get(c)
        else:
            linux_map = {
                "1": preset_cfg,
                "2": sleep_cfg,
                "3": reapply_cfg,
                "4": applystart_cfg,
                "5": login_cfg,
                "6": cfu_cfg,
                "7": pass_cfg,
                "8": debug_cfg,
                "r": _reset_all,
                "b": None,
            }
            action = linux_map.get(c)

        if c == "b":
            break
        elif action is None:
            print("Invalid option.")
            pause()
        else:
            action()