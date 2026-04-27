"""
hardware.py - CPU detection, codename resolution, and hardware info display.
"""

import subprocess
from . import config as cfg
from .ui import clear, pause

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
    Run *command* in a shell (or under sudo) and return stripped stdout.
    On sudo calls the stored password is piped to stdin.
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
    else:
        proc = subprocess.Popen(
            command,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        password = b""

    stdout, _ = proc.communicate(input=password)
    return stdout.decode("utf-8", errors="replace").strip()


# dmidecode helper

def _dmi(field: str) -> str:
    """Extract a single dmidecode processor field."""
    return run_cmd(
        f"{cfg.DMIDECODE} -t processor | grep '{field}' | awk -F': ' '{{print $2}}'",
        use_sudo=True,
    )


# Codename / architecture

def _resolve_codename(cpu: str, cpu_family: int, cpu_model: int) -> tuple[str, str]:
    """Return (architecture, family) strings from CPUID family/model numbers."""

    if cpu == "Intel":
        return "Intel", "Intel"

    arch, family = "Unknown", "Unknown"

    if cpu_family == 23:
        arch = "Zen 1 - Zen 2"
        match cpu_model:
            case 1:   family = "SummitRidge"
            case 8:   family = "PinnacleRidge"
            case 17 | 18: family = "RavenRidge"
            case 24:  family = "Picasso"
            case 32:  family = "Pollock" if any(s in cpu for s in ("15e", "15Ce", "20e")) else "Dali"
            case 80:  family = "FireFlight"
            case 96:  family = "Renoir"
            case 104: family = "Lucienne"
            case 113: family = "Matisse"
            case 144 | 145: family = "VanGogh"
            case 160: family = "Mendocino"

    elif cpu_family == 25:
        arch = "Zen 3 - Zen 4"
        match cpu_model:
            case 33:  family = "Vermeer"
            case 63 | 68: family = "Rembrandt"
            case 80:  family = "Cezanne_Barcelo"
            case 97:  family = "DragonRange" if "HX" in cpu else "Raphael"
            case 116: family = "PhoenixPoint"
            case 120: family = "PhoenixPoint2"
            case 117: family = "HawkPoint"
            case 124: family = "HawkPoint2"

    elif cpu_family == 26:
        arch = "Zen 5 - Zen 6"
        match cpu_model:
            case 68:  family = "FireRange" if "HX" in cpu else "GraniteRidge"
            case 96:  family = "KrackanPoint"
            case 104: family = "KrackanPoint2"
            case 32 | 36: family = "StrixPoint"
            case 112: family = "StrixHalo"

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
    fields = {
        "CPU":            "Version",
        "Signature":      "Signature",
        "Voltage":        "Voltage",
        "Max Speed":      "Max Speed",
        "Current Speed":  "Current Speed",
        "Core Count":     "Core Count",
        "Core Enabled":   "Core Enabled",
        "Thread Count":   "Thread Count",
    }
    for key, dmi_field in fields.items():
        cfg.set("Info", key, _dmi(dmi_field))

    _compute_codename()
    cfg.save()


def _compute_codename() -> None:
    """Derive Family, Architecture, and Type from Signature; update config."""
    raw_cpu   = cfg.get("Info", "CPU")
    signature = cfg.get("Info", "Signature")

    try:
        words        = signature.split()
        cpu_family   = int(words[words.index("Family") + 1].rstrip(","))
        cpu_model    = int(words[words.index("Model")  + 1].rstrip(","))
    except (ValueError, IndexError):
        cfg.set("Info", "Architecture", "Unknown")
        cfg.set("Info", "Family",       "Unknown")
        cfg.set("Info", "Type",         "Unknown")
        return

    arch, family = _resolve_codename(raw_cpu, cpu_family, cpu_model)
    cpu_type     = _cpu_type(family, arch)

    cfg.set("Info", "Architecture", arch)
    cfg.set("Info", "Family",       family)
    cfg.set("Info", "Type",         cpu_type)


def refresh_codename() -> None:
    """Recompute codename from already-stored Signature (no dmidecode call)."""
    _compute_codename()
    cfg.save()


def smu_version() -> str:
    """Return the SMU BIOS Interface Version string from ryzenadj."""
    raw = run_cmd(
        f"{cfg.RYZENADJ} -i | grep 'SMU BIOS Interface Version'",
        use_sudo=True,
    )
    return raw.strip()


def show_info() -> None:
    """Print a hardware information summary to the terminal."""
    clear()
    print("Processor Information:")
    print(f"  Processor   : {cfg.get('Info', 'CPU')}")
    print(f"  Codename    : {cfg.get('Info', 'Family')}")
    smu = smu_version()
    if smu:
        print(f"  {smu}")
    print(f"  Architecture: {cfg.get('Info', 'Architecture')}")
    print(f"  Signature   : {cfg.get('Info', 'Signature')}")
    print(f"  Type        : {cfg.get('Info', 'Type')}")
    print(f"  Voltage     : {cfg.get('Info', 'Voltage')}")
    print(f"  Cores       : {cfg.get('Info', 'Core Count')}")
    print(f"  Threads     : {cfg.get('Info', 'Thread Count')}")
    print(f"  Max speed   : {cfg.get('Info', 'Max Speed')}")
    print(f"  Current     : {cfg.get('Info', 'Current Speed')}")
    print()
    pause()


def check_nvram() -> bool:
    """
    macOS only - verify that debug=0x144 boot-arg and the required SIP
    flags are active in NVRAM.
    """
    sip = cfg.get("Settings", "SIP", "03080000")
    try:
        boot = subprocess.run(
            ["nvram", "boot-args"],
            capture_output=True, text=True, check=True,
        )
        if "debug=0x144" not in boot.stdout:
            return False
        csr = subprocess.run(
            ["nvram", "csr-active-config"],
            capture_output=True, text=True, check=True,
        )
        return sip in csr.stdout.replace("%", "")
    except subprocess.CalledProcessError as exc:
        print(f"NVRAM check error: {exc}")
        return False