#!/usr/bin/env python3
"""
SoftwareUpdate.py - Standalone updater script.
Can be invoked directly or called by the in-app updater.
"""
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile

URL = "https://github.com/HorizonUnix/UXTU4Unix/releases/latest/download/UXTU4Unix.zip"
KERNEL = os.uname().sysname


def update() -> None:
    script_dir  = os.path.dirname(os.path.realpath(__file__))   # Assets/
    root_dir    = os.path.dirname(script_dir)                   # UXTU4Unix/
    parent_dir  = os.path.dirname(root_dir)                     # parent/

    zip_path    = os.path.join(parent_dir, "UXTU4Unix.zip")
    new_folder  = os.path.join(parent_dir, "UXTU4Unix_new")
    config_src  = os.path.join(root_dir, "Assets", "config.toml")
    config_bak  = os.path.join(parent_dir, "config.toml.bak")

    try:
        # Backup existing config
        if os.path.isfile(config_src):
            shutil.copy2(config_src, config_bak)
            print("Config backed up.")

        # Download
        print(f"Downloading from {URL}...")
        urllib.request.urlretrieve(URL, zip_path)

        # Extract to temp folder
        print("Extracting...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(new_folder)

        # Swap directories
        shutil.rmtree(root_dir)
        inner = os.path.join(new_folder, "UXTU4Unix")
        shutil.move(inner, parent_dir)
        shutil.rmtree(new_folder, ignore_errors=True)

        # Fix executable permissions
        new_root = os.path.join(parent_dir, "UXTU4Unix")
        if KERNEL == "Darwin":
            binaries = [
                os.path.join(new_root, "UXTU4Unix.command"),
                os.path.join(new_root, "Assets", "Darwin", "ryzenadj"),
                os.path.join(new_root, "Assets", "Darwin", "dmidecode"),
            ]
            launch = os.path.join(new_root, "UXTU4Unix.command")
        else:
            launch = os.path.join(new_root, "UXTU4Unix.py")
            binaries = [
                launch,
                os.path.join(new_root, "Assets", "Linux", "ryzenadj"),
            ]

        for path in binaries:
            if os.path.exists(path):
                subprocess.run(["chmod", "+x", path], check=True)

        # Restore config
        new_config = os.path.join(new_root, "Assets", "config.toml")
        if os.path.isfile(config_bak):
            shutil.move(config_bak, new_config)
            print("Config restored.")

        # Clean zip
        if os.path.isfile(zip_path):
            os.remove(zip_path)

        print("Update successful. Relaunching…")
        if KERNEL == "Darwin":
            subprocess.Popen(["open", launch])
        else:
            subprocess.Popen([sys.executable, launch])

    except Exception as exc:
        print(f"Update error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    update()