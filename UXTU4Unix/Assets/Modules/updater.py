"""
updater.py - Version checking and self-update logic.
"""

import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile

from . import config as cfg
from .ui import clear, pause

# Version fetching

def get_latest_version() -> str:
    """Fetch the latest release tag from GitHub (follows redirect)."""
    final_url = urllib.request.urlopen(cfg.LATEST_VER_URL).geturl()
    return final_url.rstrip("/").split("/")[-1]


def get_changelog() -> str:
    """Fetch the release body (changelog) from the GitHub API."""
    req  = urllib.request.Request(cfg.GITHUB_API_URL)
    data = json.loads(urllib.request.urlopen(req).read())
    return data.get("body", "No changelog available.")


# Update installation

def _do_update() -> None:
    """Download the latest release zip and replace the current installation."""
    url         = "https://github.com/HorizonUnix/UXTU4Unix/releases/latest/download/UXTU4Unix.zip"
    script_dir  = os.path.dirname(os.path.realpath(__file__))        # Assets/Modules
    assets_dir  = os.path.dirname(script_dir)                        # Assets
    root_dir    = os.path.dirname(assets_dir)                        # UXTU4Unix
    parent_dir  = os.path.dirname(root_dir)                          # parent of UXTU4Unix

    zip_path    = os.path.join(parent_dir, "UXTU4Unix.zip")
    new_folder  = os.path.join(parent_dir, "UXTU4Unix_new")
    config_bak  = os.path.join(parent_dir, "config.toml.bak")
    config_src  = cfg.CONFIG_PATH

    try:
        # Backup config
        if os.path.exists(config_src):
            shutil.copy2(config_src, config_bak)

        # Download
        print("Downloading update...")
        urllib.request.urlretrieve(url, zip_path)

        # Extract
        print("Extracting...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(new_folder)

        # Replace old installation
        shutil.rmtree(root_dir)
        inner = os.path.join(new_folder, "UXTU4Unix")
        shutil.move(inner, parent_dir)
        shutil.rmtree(new_folder, ignore_errors=True)

        # Fix permissions
        new_root = os.path.join(parent_dir, "UXTU4Unix")
        if cfg.KERNEL == "Darwin":
            for binary in ("UXTU4Unix.command",
                           "Assets/Darwin/ryzenadj",
                           "Assets/Darwin/dmidecode"):
                path = os.path.join(new_root, binary)
                if os.path.exists(path):
                    subprocess.run(["chmod", "+x", path], check=True)
            launch = os.path.join(new_root, "UXTU4Unix.command")
        else:
            launch = os.path.join(new_root, "UXTU4Unix.py")
            ryzen  = os.path.join(new_root, "Assets", "Linux", "ryzenadj")
            for path in (launch, ryzen):
                if os.path.exists(path):
                    subprocess.run(["chmod", "+x", path], check=True)

        # Restore config
        new_config = os.path.join(new_root, "Assets", "config.toml")
        if os.path.exists(config_bak):
            shutil.move(config_bak, new_config)

        # Clean up zip
        if os.path.exists(zip_path):
            os.remove(zip_path)

        print("Update complete. Relaunching - please close this window.")
        if cfg.KERNEL == "Darwin":
            subprocess.Popen(["open", launch])
        else:
            subprocess.Popen(["python3", launch])

    except Exception as exc:
        print(f"Update failed: {exc}")
        pause()


# Interactive updater

def show_updater() -> None:
    """Prompt the user to install the latest release."""
    while True:
        clear()
        try:
            latest    = get_latest_version()
            changelog = get_changelog()
        except Exception as exc:
            print(f"Could not fetch release info: {exc}")
            pause()
            return

        print("-" * 15 + " Software Update " + "-" * 15)
        print("A new update is available!\n")
        print(f"Latest version : {latest}")
        print(f"\nChangelog:\n{changelog}\n")
        c = input("Update now? (y/n): ").strip().lower()
        if c == "y":
            _do_update()
            raise SystemExit
        elif c == "n":
            print("Skipping update.")
            break
        else:
            print("Please enter 'y' or 'n'.")


# Startup update check

def check_updates() -> None:
    """
    Called on startup when SoftwareUpdate=1.
    Retries up to 10 times on network failure, then asks user to skip.
    """
    MAX_RETRIES = 10
    import time

    clear()
    latest: str | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            latest = get_latest_version()
            break
        except Exception as exc:
            print(f"Could not fetch version (attempt {attempt}/{MAX_RETRIES}): {exc}")
            if attempt < MAX_RETRIES:
                time.sleep(5)

    if latest is None:
        clear()
        print("Failed to fetch the latest version after multiple retries.")
        ans = input("Skip the update check and continue? (y/n): ").strip().lower()
        if ans != "y":
            sys.exit("Quitting.")
        return

    local = cfg.LOCAL_VERSION
    if local < latest:
        show_updater()
    elif local > latest:
        clear()
        print("-" * 15 + " Beta Program " + "-" * 15)
        print("This build is newer than the latest release.")
        print("It may be unstable and is intended for testing only.\n")
        if input("Continue? (y/n): ").strip().lower() != "y":
            sys.exit("Quitting.")