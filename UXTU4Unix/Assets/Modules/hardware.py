"""
hardware.py - CPU detection, codename resolution, and hardware info display.
"""

import os
import shlex
import shutil
import subprocess

from . import config as cfg
from .ui import clear, pause

# Ordered list used for pre/post-Matisse comparisons in preset selection
RYZEN_FAMILY = [
    "Unknown", "SummitRidge", "PinnacleRidge", "RavenRidge", "Dali", "Pollock",
    "Picasso", "FireFlight", "Matisse", "Renoir", "Lucienne", "VanGogh",
    "Mendocino", "Vermeer", "Cezanne_Barcelo", "Rembrandt", "Raphael",
    "DragonRange", "PhoenixPoint", "PhoenixPoint2", "HawkPoint", "HawkPoint2",
    "SonomaValley", "GraniteRidge", "FireRange", "StrixHalo", "StrixPoint",
    "KrackanPoint", "KrackanPoint2",
]


# Low-level helper

def run_cmd(command: str, *, use_sudo: bool = False) -> str:
    """
    Run *command* and return stripped stdout.

    sudo path  : password is piped to stdin via -S (never exposed in ps/argv).
    non-sudo   : command is split with shlex - no shell=True, no injection risk.
    """
    from .secure_password import get_password

    if use_sudo:
        password = (get_password() or "").encode()
        proc = subprocess.Popen(
            ["sudo", "-S", "sh", "-c", command],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, _ = proc.communicate(input=password)
    else:
        try:
            args = shlex.split(command)
        except ValueError:
            return ""
        proc = subprocess.Popen(
            args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, _ = proc.communicate()

    return stdout.decode("utf-8", errors="replace").strip()


# Common locations for system binaries
_SBIN_PATHS = "/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/sbin:/usr/local/bin"


def _find_dmidecode() -> str | None:
    """
    Locate dmidecode by searching both $PATH and known sbin directories.
    Returns the full path string, or None if not found anywhere.
    """
    user_path = os.environ.get("PATH", "")
    combined = user_path + (":" if user_path else "") + _SBIN_PATHS
    seen = []
    for p in combined.split(":"):
        if p and p not in seen:
            seen.append(p)
    return shutil.which("dmidecode", path=":".join(seen))


def check_binaries() -> None:
    """
    dmidecode missing -> install guide.
    ryzenadj missing  -> prompt to re-download the release.
    """

    dmi_path = _find_dmidecode()
    if dmi_path is None:
        print(
            "\nError: 'dmidecode' is not installed or not found.\n"
            "Install it with your package manager:\n"
            "  Debian/Ubuntu : sudo apt install dmidecode\n"
            "  Fedora/RHEL   : sudo dnf install dmidecode\n"
            "  Arch          : sudo pacman -S dmidecode\n"
            "  openSUSE      : sudo zypper install dmidecode\n"
        )
        raise SystemExit(1)

    # Store resolved absolute path so all _dmi() calls use it directly,
    # bypassing PATH issues that also affect the sudo sh -c subshell.
    cfg.DMIDECODE = dmi_path

    if not os.path.isfile(cfg.RYZENADJ):
        print(
            "\nError: 'ryzenadj' not found.\n"
            "The binary is missing - the installation may be incomplete.\n"
        )
        ans = input("Re-download the latest release now? (y/n): ").strip().lower()
        if ans == "y":
            from .updater import _do_update
            _do_update()
        raise SystemExit(1)


def _dmi(field: str) -> str:
    """Extract a single dmidecode processor field."""
    return run_cmd(
        f"{cfg.DMIDECODE} -t processor | grep '{field}' | awk -F': ' '{{print $2}}'",
        use_sudo=True,
    )


def _dmi_raw(dmi_type: str) -> str:
    """Return full raw dmidecode output for a given type."""
    return run_cmd(f"{cfg.DMIDECODE} -t {dmi_type}", use_sudo=True)


def _extract_field(raw: str, field: str) -> str:
    """Return the first value matching 'field: value' in raw dmidecode output."""
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.startswith(f"{field}:"):
            return stripped.split(":", 1)[-1].strip()
    return "N/A"


# Section parsers

def _parse_device_info() -> dict[str, str]:
    raw_sys   = _dmi_raw("system")
    raw_board = _dmi_raw("baseboard")
    return {
        "name":     _extract_field(raw_sys,   "Product Name"),
        "producer": _extract_field(raw_sys,   "Manufacturer"),
        "model":    _extract_field(raw_board, "Product Name"),
    }


def _parse_processor_dmidecode() -> dict[str, str]:
    raw   = _dmi_raw("processor")
    speed = _extract_field(raw, "Current Speed")
    if speed == "N/A":
        speed = _extract_field(raw, "Max Speed")
    return {
        "manufacturer": _extract_field(raw, "Manufacturer"),
        "cores":        _extract_field(raw, "Core Count"),
        "threads":      _extract_field(raw, "Thread Count"),
        "base_clock":   speed,
    }


def _format_cache(size_str: str) -> str:
    """Convert '384 kB' -> '0.38 MB', '16384 kB' -> '16 MB', etc."""
    parts = size_str.split()
    if len(parts) < 2:
        return size_str
    try:
        value = float(parts[0])
        unit  = parts[1].lower().rstrip("b").rstrip("i")
        if unit == "k":
            mb = value / 1024
            return f"{mb:.2f} MB" if mb < 1 else f"{mb:.0f} MB"
        if unit == "m":
            return f"{value:.0f} MB"
        if unit == "g":
            return f"{value * 1024:.0f} MB"
    except (ValueError, IndexError):
        pass
    return size_str


def _parse_cache_sizes() -> tuple[str, str, str]:
    """Return (L1, L2, L3) formatted cache size strings."""
    raw           = _dmi_raw("cache")
    l1 = l2 = l3 = "N/A"
    current_level: str | None = None

    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.startswith("Socket Designation:"):
            val = stripped.split(":", 1)[-1].strip().upper()
            if   "L1" in val: current_level = "L1"
            elif "L2" in val: current_level = "L2"
            elif "L3" in val: current_level = "L3"
            else:             current_level = None
        elif stripped.startswith("Installed Size:") and current_level:
            fmt = _format_cache(stripped.split(":", 1)[-1].strip())
            if   current_level == "L1": l1 = fmt
            elif current_level == "L2": l2 = fmt
            elif current_level == "L3": l3 = fmt

    return l1, l2, l3


def _parse_memory() -> dict[str, str]:
    """Parse dmidecode -t memory and return a summary dict."""
    raw = _dmi_raw("memory")

    total_mb     = 0
    mem_type     = "Unknown"
    speed        = "Unknown"
    manufacturer = "Unknown"
    part_number  = "Unknown"
    module_width = 64
    module_count = 0

    current: dict[str, str] = {}
    in_device = False

    def _flush(d: dict) -> None:
        nonlocal total_mb, mem_type, speed, manufacturer, part_number
        nonlocal module_width, module_count

        raw_size = d.get("Size", "")
        if not raw_size or "No Module" in raw_size or "Not Installed" in raw_size:
            return

        parts = raw_size.split()
        try:
            sz   = int(parts[0])
            unit = parts[1].upper() if len(parts) > 1 else "MB"
            if unit == "GB":
                sz *= 1024
        except (ValueError, IndexError):
            return

        total_mb     += sz
        module_count += 1

        if d.get("Type", "Unknown") not in ("Unknown", ""):
            mem_type = d["Type"]
        for spd_key in ("Configured Memory Speed", "Speed"):
            if d.get(spd_key, "Unknown") not in ("Unknown", ""):
                speed = d[spd_key]
                break
        if d.get("Manufacturer", "Unknown") not in ("Unknown", ""):
            manufacturer = d["Manufacturer"]
        if d.get("Part Number", "Unknown") not in ("Unknown", ""):
            part_number = d["Part Number"].strip()
        try:
            module_width = int(d.get("Data Width", "64").split()[0])
        except ValueError:
            pass

    for line in raw.splitlines():
        stripped = line.strip()
        if stripped == "Memory Device":
            if in_device:
                _flush(current)
            current   = {}
            in_device = True
        elif in_device and ":" in stripped:
            key, _, val = stripped.partition(":")
            current[key.strip()] = val.strip()

    if in_device:
        _flush(current)

    total_str   = f"{total_mb // 1024} GB" if total_mb >= 1024 else f"{total_mb} MB"
    spd_fmt     = speed if speed != "Unknown" else ""
    summary     = f"{total_str} {mem_type}" + (f" @ {spd_fmt}" if spd_fmt else "")
    total_bus   = module_width * module_count
    width_str   = f"{total_bus} bit"
    modules_str = f"{module_count} * {module_width} bit"

    return {
        "summary":      summary,
        "manufacturer": manufacturer,
        "part_number":  part_number,
        "width":        width_str,
        "modules":      modules_str,
    }


# Codename / architecture

def _resolve_codename(cpu: str, cpu_family: int, cpu_model: int):
    """Return (architecture, family) strings from CPUID family/model numbers."""
    if cpu == "Intel":
        return "Intel", "Intel"

    arch, family = "Unknown", "Unknown"

    if cpu_family == 23:
        arch = "Zen 1 - Zen 2"
        match cpu_model:
            case 1:         family = "SummitRidge"
            case 8:         family = "PinnacleRidge"
            case 17 | 18:   family = "RavenRidge"
            case 24:        family = "Picasso"
            case 32:        family = "Pollock" if any(s in cpu for s in ("15e", "15Ce", "20e")) else "Dali"
            case 80:        family = "FireFlight"
            case 96:        family = "Renoir"
            case 104:       family = "Lucienne"
            case 113:       family = "Matisse"
            case 144 | 145: family = "VanGogh"
            case 160:       family = "Mendocino"

    elif cpu_family == 25:
        arch = "Zen 3 - Zen 4"
        match cpu_model:
            case 33:      family = "Vermeer"
            case 63 | 68: family = "Rembrandt"
            case 80:      family = "Cezanne_Barcelo"
            case 97:      family = "DragonRange" if "HX" in cpu else "Raphael"
            case 116:     family = "PhoenixPoint"
            case 120:     family = "PhoenixPoint2"
            case 117:     family = "HawkPoint"
            case 124:     family = "HawkPoint2"

    elif cpu_family == 26:
        arch = "Zen 5 - Zen 6"
        match cpu_model:
            case 68:      family = "FireRange" if "HX" in cpu else "GraniteRidge"
            case 96:      family = "KrackanPoint"
            case 104:     family = "KrackanPoint2"
            case 32 | 36: family = "StrixPoint"
            case 112:     family = "StrixHalo"

    return arch, family


_DESKTOP_FAMILIES = {
    "SummitRidge", "PinnacleRidge", "Matisse",
    "Vermeer", "Raphael", "GraniteRidge",
}


def _cpu_type(family: str, arch: str) -> str:
    if family in _DESKTOP_FAMILIES:
        return "Amd_Desktop_Cpu"
    if arch == "Intel":
        return "Intel"
    if arch == "Unknown":
        return "Unknown"
    return "Amd_Apu"


# Public API

def detect() -> None:
    """
    Populate the [Info] config section using dmidecode, then derive
    codename, architecture, and CPU type.
    """
    check_binaries()
    for key, dmi_field in {"CPU": "Version", "Signature": "Signature"}.items():
        cfg.set("Info", key, _dmi(dmi_field))
    _compute_codename()
    cfg.save()


def _compute_codename() -> None:
    """Derive Family, Architecture, and Type from Signature; update config."""
    raw_cpu   = cfg.get("Info", "CPU")
    signature = cfg.get("Info", "Signature")

    try:
        words      = signature.split()
        cpu_family = int(words[words.index("Family") + 1].rstrip(","))
        cpu_model  = int(words[words.index("Model")  + 1].rstrip(","))
    except (ValueError, IndexError):
        cfg.set("Info", "Architecture", "Unknown")
        cfg.set("Info", "Family",       "Unknown")
        cfg.set("Info", "Type",         "Unknown")
        return

    arch, family = _resolve_codename(raw_cpu, cpu_family, cpu_model)
    cfg.set("Info", "Architecture", arch)
    cfg.set("Info", "Family",       family)
    cfg.set("Info", "Type",         _cpu_type(family, arch))


def refresh_codename() -> None:
    """Recompute codename from already-stored Signature (no dmidecode call)."""
    _compute_codename()
    cfg.save()


def smu_version() -> str:
    """Return the SMU BIOS Interface Version string from ryzenadj."""
    return run_cmd(
        f"{cfg.RYZENADJ} -i | grep 'SMU BIOS Interface Version'",
        use_sudo=True,
    ).strip()


def show_info() -> None:
    """Print a full hardware information summary to the terminal."""
    clear()

    W = 16

    def row(label: str, value: str) -> None:
        print(f"  {label:<{W}} {value}")

    dev = _parse_device_info()
    print("Device Information")
    row("Name",     dev["name"])
    row("Producer", dev["producer"])
    row("Model",    dev["model"])
    print()

    proc        = _parse_processor_dmidecode()
    l1, l2, l3  = _parse_cache_sizes()

    print("Processor Information")
    row("Processor",  cfg.get("Info", "CPU"))
    row("Producer",   proc["manufacturer"])
    row("Codename",   cfg.get("Info", "Family"))
    row("Caption",    cfg.get("Info", "Signature"))
    row("Cores",      proc["cores"])
    row("Threads",    proc["threads"])
    row("Base Clock", proc["base_clock"])
    row("L1 Cache",   l1)
    row("L2 Cache",   l2)
    row("L3 Cache",   l3)

    smu = smu_version()
    if smu:
        print(f"  {smu}")
    print()

    mem = _parse_memory()
    print("Memory Information")
    row("Memory",   mem["summary"])
    row("Producer", mem["manufacturer"])
    row("Model",    mem["part_number"])
    row("Width",    mem["width"])
    row("Modules",  mem["modules"])
    print()

    pause()