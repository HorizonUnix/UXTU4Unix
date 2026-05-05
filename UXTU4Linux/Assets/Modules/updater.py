"""
updater.py
"""
import json
import os
import re
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
        url = urllib.request.urlopen(cfg.LATEST_VER_URL, timeout=10).geturl()
        return url.rstrip("/").split("/")[-1]
    except urllib.error.URLError as e:
        print(f"Failed to fetch latest version from {cfg.LATEST_VER_URL}: {e}")
        return "v0.0.0"


def get_changelog() -> str:
    req = urllib.request.Request(cfg.GITHUB_API_URL)
    try:
        raw = urllib.request.urlopen(req, timeout=10).read()
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

    expected_structure = (
        os.path.basename(script_dir) == "Modules"
        and os.path.basename(assets_dir) == "Assets"
        and os.path.isdir(os.path.join(install_dir, "Assets"))
        and os.path.isfile(os.path.join(install_dir, "main.py"))
    )
    if not expected_structure:
        raise RuntimeError(
            "Unexpected installation layout detected; aborting update to avoid writing to incorrect paths."
        )

    zip_path   = os.path.join(install_dir, "UXTU4Linux.zip")
    new_folder = os.path.join(install_dir, "UXTU4Linux_new")
    config_bak = os.path.join(install_dir, "config.toml.bak")

    def _sudo(install_root: str, *args: str) -> int:
        """Run a restricted sudo command.

        Note: callers must pass trusted, canonicalized paths. This helper enforces
        a strict command/flag policy to reduce misuse risk.
        """
        if not args:
            raise ValueError("No command provided for sudo execution")

        allowed_commands = {"rm", "cp", "mv", "chmod", "chown", "mkdir"}
        cmd = args[0]
        if cmd not in allowed_commands:
            raise ValueError(f"Disallowed sudo command: {cmd}")
        safe_value_re = re.compile(r"^[A-Za-z0-9._/\-]+$")
        for arg in args:
            if any(ch in arg for ch in ("\x00", "\n", "\r")):
                raise ValueError(f"Invalid character detected in argument: {arg!r}")
        cmd_args = list(args[1:])

        path_args = [a for a in cmd_args if not a.startswith("-")]

        def _validate_args(cmd_args: list, path_args: list, allowed_flags: set, min_paths: int) -> None:
            for a in cmd_args:
                if a.startswith("-"):
                    if a not in allowed_flags:
                        raise ValueError(f"Disallowed flag for {cmd}: {a}")
                else:
                    if not a.strip():
                        raise ValueError("Empty path/value argument is not allowed")
                    if not safe_value_re.fullmatch(a):
                        raise ValueError(f"Invalid characters in sudo argument for {cmd}: {a}")
            if len(path_args) < min_paths:
                raise ValueError(f"Insufficient path arguments for {cmd}")
            _assert_paths_within_install_root(path_args)

        def _is_within_install_root(path_value: str) -> bool:
            real_target = os.path.realpath(path_value)
            try:
                return os.path.commonpath([install_root, real_target]) == install_root
            except ValueError:
                return False

        def _assert_paths_within_install_root(paths: list) -> None:
            for p in paths:
                if not _is_within_install_root(p):
                    raise ValueError(f"Path escapes installation directory: {p}")


        if cmd == "rm":
            _validate_args(cmd_args, path_args, {"-f", "-r", "-rf", "-fr"}, 1)
        elif cmd == "cp":
            _validate_args(cmd_args, path_args, {"-r", "-f", "-a"}, 2)
        elif cmd == "mv":
            _validate_args(cmd_args, path_args, {"-f", "-n"}, 2)
        elif cmd == "chmod":
            _validate_args(cmd_args, path_args, {"-R"}, 2)
        elif cmd == "chown":
            _validate_args(cmd_args, path_args, {"-R"}, 2)
        elif cmd == "mkdir":
            _assert_paths_within_install_root(path_args)
            _validate_args(cmd_args, path_args, {"-p"}, 1)

        return subprocess.run(["sudo", *args], check=False).returncode

    try:
        if os.path.exists(cfg.CONFIG_PATH):
            try:
                shutil.copy2(cfg.CONFIG_PATH, config_bak)
            except OSError as e:
                raise RuntimeError(
                    f"Configuration backup failed: could not copy {cfg.CONFIG_PATH} to {config_bak}. "
                    "Aborting update to avoid potential configuration loss."
                ) from e

        print("Downloading update...")
        try:
            urllib.request.urlretrieve(url, zip_path)
        except urllib.error.URLError as e:
            raise ConnectionError(f"Download failed: could not retrieve update from {url}") from e

        print("Extracting...")

        def _safe_extract_zip(zf: zipfile.ZipFile, dest_dir: str) -> None:
            dest_root = os.path.realpath(dest_dir)
            for member in zf.infolist():
                member_name = member.filename
                if os.path.isabs(member_name):
                    raise RuntimeError(f"Unsafe absolute path in zip entry: {member_name}")

                target_path = os.path.realpath(os.path.join(dest_root, member_name))
                try:
                    common_root = os.path.commonpath([dest_root, target_path])
                except ValueError as e:
                    raise RuntimeError(f"Unsafe path traversal in zip entry: {member_name}") from e
                if common_root != dest_root:
                    raise RuntimeError(f"Unsafe path traversal in zip entry: {member_name}")

                zf.extract(member, dest_root)

        with zipfile.ZipFile(zip_path, "r") as zf:
            _safe_extract_zip(zf, new_folder)

        if _sudo("rm", "-rf", src_dir) != 0:
            raise PermissionError(f"Could not remove {src_dir}; the privileged remove command failed (possible permission issue or directory in use)")

        def _resolve_inner_extracted_dir(base_folder: str) -> str:
            expected_inner = os.path.join(base_folder, "UXTU4Linux")
            if os.path.isdir(expected_inner):
                return expected_inner

            extracted_dirs = [
                os.path.join(base_folder, name)
                for name in os.listdir(base_folder)
                if os.path.isdir(os.path.join(base_folder, name))
            ]
            if len(extracted_dirs) == 1:
                return extracted_dirs[0]

            raise RuntimeError(
                f"Unexpected update archive structure in {base_folder}. "
                f"Expected directory 'UXTU4Linux', found: {[os.path.basename(d) for d in extracted_dirs]}"
            )

        inner = _resolve_inner_extracted_dir(new_folder)

        if _sudo(install_root, "mv", inner, src_dir) != 0:
            raise PermissionError(f"Could not move new release into {src_dir}")

        if _sudo(install_root, "rm", "-rf", new_folder) != 0:
            print(f"Warning: Could not remove temporary folder: {new_folder}")

        launch = os.path.join(src_dir, "UXTU4Linux.py")
        ryzen  = os.path.join(src_dir, "Assets", "Linux", "ryzenadj")
        for path in (launch, ryzen):
            if os.path.exists(path):
                if _sudo(src_dir, "chmod", "+x", path) != 0:
                    raise RuntimeError(f"Could not set executable permission on {path}")

        new_config = os.path.join(src_dir, "Assets", "config.toml")
        if os.path.exists(config_bak):
            try:
                shutil.move(config_bak, new_config)
            except OSError as e:
                raise RuntimeError(
                    f"Failed to restore configuration from {config_bak!r} to {new_config!r}: {e}"
                ) from e

        if os.path.exists(zip_path):
            os.remove(zip_path)

        print("Restarting daemon...")
        if service_running():
            restart_service()

        print("Update complete. Relaunching - please close this window.")
        raw_executable = sys.executable
        if not raw_executable:
            raise RuntimeError("Refusing to relaunch: sys.executable is not set")
        python_exec = os.path.realpath(raw_executable)
        if not python_exec or not os.path.isabs(python_exec) or not os.path.isfile(python_exec) or not os.access(python_exec, os.X_OK):
            raise RuntimeError(f"Refusing to relaunch with untrusted interpreter path: {python_exec!r}")
        if not launch:
            raise RuntimeError("Refusing to relaunch: launch target is not set")
        if not os.path.isabs(launch):
            raise RuntimeError(f"Refusing to relaunch with non-absolute launch target: {launch!r}")
        if not os.path.isfile(launch):
            raise RuntimeError(f"Refusing to relaunch with missing launch target file: {launch!r}")
        if not os.access(launch, os.R_OK):
            raise RuntimeError(f"Refusing to relaunch with unreadable launch target: {launch!r}")
        try:
            subprocess.Popen([python_exec, launch])
        except (OSError, PermissionError, subprocess.SubprocessError) as e:
            raise RuntimeError(
                f"Failed to relaunch updater using interpreter {python_exec!r} and script {launch!r}: {e}"
            ) from e
        return

    except (
        OSError,
        PermissionError,
        ConnectionError,
        RuntimeError,
        ValueError,
        subprocess.SubprocessError,
        urllib.error.URLError,
        zipfile.BadZipFile,
        json.JSONDecodeError,
    ) as e:
        err_type = type(e).__name__
        if isinstance(e, urllib.error.URLError):
            print(f"Update failed ({err_type}): Network error while downloading update: {e}")
            print("Please check your internet connection, DNS, or firewall settings and try again.")
        elif isinstance(e, PermissionError):
            print(f"Update failed ({err_type}): Insufficient permissions: {e}")
            print("Please rerun the updater with the required privileges.")
        elif isinstance(e, zipfile.BadZipFile):
            print(f"Update failed ({err_type}): Downloaded update archive is corrupted: {e}")
            print("Please retry the update; the download may have been incomplete.")
        elif isinstance(e, subprocess.SubprocessError):
            print(f"Update failed ({err_type}): A system command failed during update: {e}")
            print("Please review system state/permissions and try again.")
        elif isinstance(e, json.JSONDecodeError):
            print(f"Update failed ({err_type}): Received invalid release metadata: {e}")
            print("Please try again later.")
        else:
            print(f"Update failed ({err_type}): {e}")
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
    RETRY_DELAY_SECONDS = 5
    clear()
    latest = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            latest = get_latest_version()
            break
        except Exception as e:
            print(f"Could not fetch version (attempt {attempt}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)

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
