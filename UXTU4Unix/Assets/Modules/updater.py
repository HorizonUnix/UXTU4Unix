"""
updater.py - Version checking and self-update logic.
"""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile

from . import config as cfg
from .ui import clear, pause

_MACOS_LAST_SERIES = (0, 5)

def _ver_tuple(v):
    try:
        return tuple(int(x) for x in v.strip().lstrip("v").split("."))
    except ValueError:
        return (0,)


def _series(t):
    """Return (major, minor) from a version tuple."""
    return (t[0], t[1]) if len(t) >= 2 else (t[0], 0)


def _get_all_releases():
    """Fetch all releases from the GitHub API."""
    url = cfg.GITHUB_API_URL.replace("/releases/latest", "/releases?per_page=50")
    req = urllib.request.Request(url)
    return json.loads(urllib.request.urlopen(req).read())


def get_latest_version():
    """
    Return the latest version string appropriate for the current platform.

    macOS  : latest non-prerelease tag in the v0.5.x series.
    Linux  : global latest release.
    """
    if cfg.KERNEL != "Darwin":
        url = urllib.request.urlopen(cfg.LATEST_VER_URL).geturl()
        return url.rstrip("/").split("/")[-1]

    releases = _get_all_releases()
    for rel in releases:
        tag = rel.get("tag_name", "")
        if not rel.get("prerelease", False) and _series(_ver_tuple(tag)) == _MACOS_LAST_SERIES:
            return tag

    raise RuntimeError(
        f"No release found in the "
        f"{'.'.join(str(x) for x in _MACOS_LAST_SERIES)}.x series."
    )


def get_changelog():
    req = urllib.request.Request(cfg.GITHUB_API_URL)
    data = json.loads(urllib.request.urlopen(req).read())
    return data.get("body", "No changelog available.")


def _get_changelog_for_tag(tag):
    url = cfg.GITHUB_API_URL.replace("/releases/latest", f"/releases/tags/{tag}")
    req = urllib.request.Request(url)
    data = json.loads(urllib.request.urlopen(req).read())
    return data.get("body", "No changelog available.")


def _is_beyond_macos_series(ver):
    return _series(_ver_tuple(ver)) > _MACOS_LAST_SERIES


def _print_eol_notice(global_latest):
    clear()
    print("-" * 15 + " macOS End-of-Support Notice " + "-" * 15)
    print(
        "\n"
        "  v0.5.x is the last UXTU4Unix series that supports macOS.\n"
        f"  The project has moved on to {global_latest}, which will not\n"
        "  be available for macOS.\n\n"
        "  You will continue to receive v0.5.x patch updates only.\n"
    )
    pause()


def _do_update(tag=None):
    """Download the release zip for *tag* (or latest) and replace the current installation."""
    if tag:
        url = f"https://github.com/HorizonUnix/UXTU4Unix/releases/download/{tag}/UXTU4Unix.zip"
    else:
        url = "https://github.com/HorizonUnix/UXTU4Unix/releases/latest/download/UXTU4Unix.zip"

    script_dir = os.path.dirname(os.path.realpath(__file__))
    assets_dir = os.path.dirname(script_dir)
    root_dir = os.path.dirname(assets_dir)
    parent_dir = os.path.dirname(root_dir)

    zip_path = os.path.join(parent_dir, "UXTU4Unix.zip")
    new_folder = os.path.join(parent_dir, "UXTU4Unix_new")
    config_bak = os.path.join(parent_dir, "config.toml.bak")

    try:
        if os.path.exists(cfg.CONFIG_PATH):
            shutil.copy2(cfg.CONFIG_PATH, config_bak)

        print("Downloading update...")
        urllib.request.urlretrieve(url, zip_path)

        print("Extracting...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(new_folder)

        shutil.rmtree(root_dir)
        inner = os.path.join(new_folder, "UXTU4Unix")
        shutil.move(inner, parent_dir)
        shutil.rmtree(new_folder, ignore_errors=True)

        new_root = os.path.join(parent_dir, "UXTU4Unix")
        if cfg.KERNEL == "Darwin":
            for binary in ("UXTU4Unix.command", "Assets/Darwin/ryzenadj", "Assets/Darwin/dmidecode"):
                path = os.path.join(new_root, binary)
                if os.path.exists(path):
                    subprocess.run(["chmod", "+x", path], check=True)
            launch = os.path.join(new_root, "UXTU4Unix.command")
        else:
            launch = os.path.join(new_root, "UXTU4Unix.py")
            ryzen = os.path.join(new_root, "Assets", "Linux", "ryzenadj")
            for path in (launch, ryzen):
                if os.path.exists(path):
                    subprocess.run(["chmod", "+x", path], check=True)

        new_config = os.path.join(new_root, "Assets", "config.toml")
        if os.path.exists(config_bak):
            shutil.move(config_bak, new_config)

        if os.path.exists(zip_path):
            os.remove(zip_path)

        print("Update complete. Relaunching - please close this window.")
        if cfg.KERNEL == "Darwin":
            subprocess.Popen(["open", launch])
        else:
            os.execv(sys.executable, [sys.executable, launch])

    except Exception as e:
        print(f"Update failed: {e}")
        pause()


def show_updater():
    while True:
        clear()
        try:
            latest = get_latest_version()
            changelog = _get_changelog_for_tag(latest)
        except Exception as e:
            print(f"Could not fetch release info: {e}")
            pause()
            return

        if cfg.KERNEL == "Darwin":
            try:
                global_url = urllib.request.urlopen(cfg.LATEST_VER_URL).geturl()
                global_latest = global_url.rstrip("/").split("/")[-1]
                if _is_beyond_macos_series(global_latest):
                    _print_eol_notice(global_latest)
                    clear()
            except Exception:
                pass

        print("-" * 15 + " Software Update " + "-" * 15)
        print("A new update is available!\n")
        print(f"Latest version : {latest}")
        if cfg.KERNEL == "Darwin":
            print("  (macOS receives v0.5.x updates only)")
        print(f"\nChangelog:\n{changelog}\n")
        c = input("Update now? (y/n): ").strip().lower()
        if c == "y":
            _do_update(tag=latest)
            raise SystemExit
        elif c == "n":
            print("Skipping update.")
            break
        else:
            print("Please enter 'y' or 'n'.")


def check_updates():
    """Check for updates on startup. Retries up to 10 times on failure."""
    MAX_RETRIES = 10
    clear()
    latest = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            latest = get_latest_version()
            break
        except Exception as e:
            print(f"Could not fetch version (attempt {attempt}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(5)

    if latest is None:
        clear()
        print("Failed to fetch the latest version after multiple retries.")
        if input("Skip the update check and continue? (y/n): ").strip().lower() != "y":
            sys.exit("Quitting.")
        return

    # On macOS, separately check if the global latest has moved past 0.5.x
    # and show the EOL notice once per session before doing any comparison.
    if cfg.KERNEL == "Darwin":
        try:
            global_url = urllib.request.urlopen(cfg.LATEST_VER_URL).geturl()
            global_latest = global_url.rstrip("/").split("/")[-1]
            if _is_beyond_macos_series(global_latest):
                _print_eol_notice(global_latest)
                clear()
        except Exception:
            pass

    local = _ver_tuple(cfg.LOCAL_VERSION)
    remote = _ver_tuple(latest)

    if local < remote:
        show_updater()
    elif local > remote:
        clear()
        print("-" * 15 + " Beta Program " + "-" * 15)
        print("This build is newer than the latest release.")
        print("It may be unstable and is intended for testing only.\n")
        if input("Continue? (y/n): ").strip().lower() != "y":
            sys.exit("Quitting.")
