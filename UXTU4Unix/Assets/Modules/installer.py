"""
installer.py - macOS-only: configure OpenCore config.plist for RyzenAdj.
"""
import binascii
import os
import plistlib
import subprocess

from . import config as cfg
from .secure_password import get_password
from .ui import clear, pause, confirm

def edit_plist(config_path):
    sip = cfg.get("Settings", "SIP", "03080000")
    with open(config_path, "rb") as f:
        data = plistlib.load(f)
    nvram_add = (
        data
        .setdefault("NVRAM", {})
        .setdefault("Add", {})
        .setdefault("7C436110-AB2A-4BBB-A880-FE41995C9F82", {})
    )
    boot_args = nvram_add.get("boot-args", "")
    if "debug=0x144" not in boot_args:
        nvram_add["boot-args"] = f"{boot_args} debug=0x144".strip()
    nvram_add["csr-active-config"] = binascii.unhexlify(sip)
    with open(config_path, "wb") as f:
        plistlib.dump(data, f)


def _finish(config_path):
    print("boot-args and SIP updated successfully.")
    print("UXTU4Unix dependencies installed.")
    if confirm("Restart now to apply changes?"):
        input("Save your work, then press Enter to restart...")
        subprocess.call("osascript -e 'tell app \"System Events\" to restart'", shell=True)


def install_auto():
    clear()
    print("Installing UXTU4Unix dependencies (Auto)...\n")
    password = (get_password() or "").encode()
    try:
        subprocess.run(["sudo", "-S", "diskutil", "mount", "EFI"], input=password, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to mount EFI: {e}")
        print("Try Manual mode instead.")
        pause()
        return
    oc_path = "/Volumes/EFI/EFI/OC"
    config_path = os.path.join(oc_path, "config.plist")
    if not os.path.isdir(oc_path):
        print("OC folder not found at /Volumes/EFI/EFI/OC.")
        pause()
        return
    if not os.path.isfile(config_path):
        print("config.plist not found inside the OC folder.")
        pause()
        return
    edit_plist(config_path)
    _finish(config_path)


def install_manual():
    clear()
    print("Installing UXTU4Unix dependencies (Manual)...\n")
    config_path = input("Drag & drop (or type) the path to config.plist: ").strip().strip("'\"")
    if not os.path.isfile(config_path):
        print(f"File not found: '{config_path}'")
        pause()
        return
    edit_plist(config_path)
    _finish(config_path)


def install_menu():
    while True:
        clear()
        print("-" * 15 + " Install dependencies " + "-" * 15)
        print("  1. Auto   (default: /Volumes/EFI/EFI/OC/config.plist)")
        print("  2. Manual (specify path)")
        print("\n  B. Back\n")
        c = input("Option (default 1): ").strip().lower() or "1"
        match c:
            case "1": install_auto()
            case "2": install_manual()
            case "b": break
            case _:
                print("Invalid option.")
                pause()