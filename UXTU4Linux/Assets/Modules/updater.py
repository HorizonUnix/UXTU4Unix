"""
updater.py
"""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import urllib.error
import zipfile

from . import config as cfg
from .ui import clear, pause
from .service import restart_service, service_running


def _ver_tuple(v: str) -> tuple:
    try:
        return tuple(int(x) for x in v.strip().lstrip("v").split("."))
    except ValueError:
        return (0,)


def get_latest_version() -> str:
    try:
        url = urllib.request.urlopen(cfg.LATEST_VER_URL).geturl()
        return url.rstrip("/").split("/")[-1]
    except urllib.error.URLError:
        return "v0.0.0"


def get_changelog() -> str:
    req = urllib.request.Request(cfg.GITHUB_API_URL)
    try:
        raw = urllib.request.urlopen(req).read()
        data = json.loads(raw)
        return data.get("body", "No changelog available.")
    except (urllib.error.URLError, json.JSONDecodeError, UnicodeDecodeError):
        return "No changelog available."


def _do_update() -> None:
    url = "https://github.com/HorizonUnix/UXTU4Linux/releases/latest/download/UXTU4Linux.zip"

    script_dir  = os.path.dirname(os.path.realpath(__file__))
    assets_dir  = os.path.dirname(script_dir)
    src_dir     = os.path.dirname(assets_dir)
    install_dir = os.path.dirname(src_dir)

    zip_path   = os.path.join(install_dir, "UXTU4Linux.zip")
    new_folder = os.path.join(install_dir, "UXTU4Linux_new")
    config_bak = os.path.join(install_dir, "config.toml.bak")

    def _sudo(*args: str) -> int:
        return subprocess.run(["sudo", *args]).returncode

    try:
        if os.path.exists(cfg.CONFIG_PATH):
            shutil.copy2(cfg.CONFIG_PATH, config_bak)

        print("Downloading update...")
        try:
            urllib.request.urlretrieve(url, zip_path)
        except urllib.error.URLError as e:
            raise ConnectionError(f"Download failed: could not retrieve update from {url}") from e

        print("Extracting...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(new_folder)

        if _sudo("rm", "-rf", src_dir) != 0:
            raise PermissionError(f"Could not remove {src_dir} — try running with sudo")

        expected_inner = os.path.join(new_folder, "UXTU4Linux")
        if os.path.isdir(expected_inner):
            inner = expected_inner
        else:
            extracted_dirs = [
                os.path.join(new_folder, name)
                for name in os.listdir(new_folder)
                if os.path.isdir(os.path.join(new_folder, name))
            ]
            if len(extracted_dirs) == 1:
                inner = extracted_dirs[0]
            else:
                raise RuntimeError(
                    f"Unexpected update archive structure in {new_folder}. "
                    f"Expected directory 'UXTU4Linux', found: {[os.path.basename(d) for d in extracted_dirs]}"
                )

        if _sudo("mv", inner, src_dir) != 0:
            raise PermissionError(f"Could not move new release into {src_dir}")

        if _sudo("rm", "-rf", new_folder) != 0:
            print(f"Warning: Could not remove temporary folder: {new_folder}")

        launch = os.path.join(src_dir, "UXTU4Linux.py")
        ryzen  = os.path.join(src_dir, "Assets", "Linux", "ryzenadj")
        for path in (launch, ryzen):
            if os.path.exists(path):
                if _sudo("chmod", "+x", path) != 0:
                    raise PermissionError(f"Could not set executable permission on {path}")

        new_config = os.path.join(src_dir, "Assets", "config.toml")
        if os.path.exists(config_bak):
            shutil.move(config_bak, new_config)

        if os.path.exists(zip_path):
            os.remove(zip_path)

        print("Restarting daemon...")
        if service_running():
            restart_service()

        print("Update complete. Relaunching - please close this window.")
        python_exec = os.path.realpath(sys.executable or "")
        if not python_exec or not os.path.isabs(python_exec) or not os.path.isfile(python_exec) or not os.access(python_exec, os.X_OK):
            raise RuntimeError(f"Refusing to relaunch with untrusted interpreter path: {python_exec!r}")
        subprocess.Popen([python_exec, launch])
        return

    except Exception as e:
        print(f"Update failed: {e}")
        pause()
        

def show_updater() -> None:
    while True:
        clear()
        try:
            latest    = get_latest_version()
            changelog = get_changelog()
        except Exception as e:
            print(f"Could not fetch release info: {e}")
            pause()
            return
        print("─" * 15 + " Software Update " + "─" * 15)
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


def check_updates() -> None:
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

    local  = _ver_tuple(cfg.LOCAL_VERSION)
    remote = _ver_tuple(latest)

    if local < remote:
        show_updater()
    elif local > remote:
        clear()
        print("─" * 15 + " Beta Program " + "─" * 15)
        print("This build is newer than the latest release.")
        print("It may be unstable and is intended for testing only.\n")
        if input("Continue? (y/n): ").strip().lower() != "y":
            sys.exit("Quitting.")
