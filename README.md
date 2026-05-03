<picture><img align="left" src="/Img/Logo.png"/></picture>
<h4>Powered by RyzenAdj and Python</h4>

[![GitHub Downloads](https://img.shields.io/github/downloads/HorizonUnix/UXTU4Unix/total?style=flat-square&color=blue)](https://github.com/HorizonUnix/UXTU4Unix/releases)
[![Latest Release](https://img.shields.io/github/v/release/HorizonUnix/UXTU4Unix?style=flat-square&color=green)](https://github.com/HorizonUnix/UXTU4Unix/releases/latest)
[![Python](https://img.shields.io/badge/Python-3.10%2B-yellow?style=flat-square)](https://www.python.org/)
[![License](https://img.shields.io/github/license/HorizonUnix/UXTU4Unix?style=flat-square)](LICENSE)

<br/>

> [!NOTE]
> - The upcoming v0.6.0 update will be released on 10 May, you can get a preview and demo [here](https://github.com/HorizonUnix/UXTU4Unix/releases/tag/0.6.0Beta03).
> - After 10 May, `UXTU4Unix` will be renamed to `UXTU4Unix`.

> [!WARNING]
> **macOS Support Notice:** With the end of Hackintosh support in macOS 26 Tahoe, the `v0.5.x` series will be the **last** to support macOS. Development will shift solely to Linux afterwards until UXTU officially supports Linux.

> [!CAUTION]
> **macOS Users:** Do **not** use UXTU4Unix alongside [SMCAMDProcessor](https://github.com/trulyspinach/SMCAMDProcessor). They conflict with each other and may cause instability.

---

## Table of Contents

- [Overview](#overview)
- [Compatibility](#compatibility)
- [Requirements](#requirements)
- [Installation](#installation)
  - [macOS](#for-macos)
  - [Linux](#for-linux)
- [Secure Boot (Linux)](#secure-boot-linux)
- [Configuration](#configuration)
- [Frequently Asked Questions](#frequently-asked-questions)
- [Preview](#preview)
- [Acknowledgments](#acknowledgments)

---

## Overview

UXTU4Unix is a power management tool for **AMD Ryzen APUs and CPUs** on macOS and Linux. It wraps [RyzenAdj](https://github.com/FlyGoat/RyzenAdj) with an interactive terminal UI, allowing you to apply, schedule, and automatically switch between power presets based on your workload and power source without touching the BIOS.

Key features:
- Premade presets for a wide range of AMD APUs and desktop CPUs
- Dynamic Mode - automatically switches between presets on AC vs. battery
- Auto-reapply on a configurable timer
- Detailed hardware information panel (CPU, cache, memory)
- Startup integration (macOS Login Items / Linux XDG Autostart)
- Built-in updater with config backup and restore

---

## Compatibility

### Supported Hardware
- AMD Ryzen APUs compatible with [NootedRed](https://github.com/ChefKissInc/NootedRed) or listed in the **Premade Preset** section of [UXTU](https://github.com/JamesCJ60/Universal-x86-Tuning-Utility)
- Any AMD CPU/APU supported by [RyzenAdj](https://github.com/FlyGoat/RyzenAdj)

### Supported Operating Systems

| Platform | Version |
|----------|---------|
| macOS    | 11 Big Sur -> 26 Tahoe with Python 3.10+ |
| Linux    | Any distribution with Python 3.10+ |

---

## Requirements

| Requirement | macOS | Linux |
|-------------|-------|-------|
| Python | 3.10+ | 3.10+ |
| `keyring` Python library | ✅ | ✅ |
| `dmidecode` | Bundled | Must install separately |
| `ryzenadj` | Bundled | Bundled in `Assets/Linux/` |
| `libpci` | Bundled (custom ryzenadj build) | Required by RyzenAdj |
| Secure Boot | Must be disabled | Must be disabled (or see [below](#secure-boot-linux)) |

---

## Installation

### 1. Download

Grab the latest release from the [Releases page](https://github.com/HorizonUnix/UXTU4Unix/releases/latest) and extract it.

### 2. Install Python Dependencies

```bash
pip3 install -r /path/to/UXTU4Unix/requirements.txt
```

---

### For macOS

> [!IMPORTANT]
> Secure Boot must be disabled in your BIOS before running UXTU4Unix on macOS.

1. Run the launcher:
   ```bash
   open /path/to/UXTU4Unix.command
   ```
   Or via terminal:
   ```bash
   python3 /path/to/UXTU4Unix.py
   ```

2. Follow the first-run setup wizard.

3. **Optional - Temperature Management:** For better thermal control, disable **Core Performance Boost** in your BIOS using [Smokeless_UMAF](https://github.com/DavidS95/Smokeless_UMAF).
   > ⚠️ This will reduce peak CPU performance. Core Performance Boost on macOS Hackintosh is not well-optimised and can cause thermal issues.

#### Fixing Python Certificates on macOS

If you encounter SSL errors, run the certificate installer bundled with Python:

<p align="left">
  <img src="/Img/cert1.png" width="380"/>
  <img src="/Img/cert2.png" width="380"/>
</p>

---

### For Linux

1. Install system dependencies:

   **Debian / Ubuntu**
   ```bash
   sudo apt install dmidecode libpci-dev
   ```
   **Fedora / RHEL**
   ```bash
   sudo dnf install dmidecode pciutils-devel
   ```
   **Arch**
   ```bash
   sudo pacman -S dmidecode pciutils
   ```

2. Run the script:
   ```bash
   python3 /path/to/UXTU4Unix.py
   ```

---

## Secure Boot (Linux)

If you want to keep Secure Boot enabled, you must load the `ryzen_smu` kernel module manually instead of disabling Secure Boot.

### Steps (from ryzenadj repo)

1. **Install build prerequisites** (Fedora example - adjust for your distro):
   ```bash
   sudo dnf install cmake gcc gcc-c++ dkms openssl
   ```

2. **Clone and install `ryzen_smu`:**
   ```bash
   git clone https://github.com/amkillam/ryzen_smu   # Active fork
   cd ryzen_smu/
   sudo make dkms-install
   ```

3. **Enroll the DKMS-generated UEFI key:**
   ```bash
   sudo mokutil --import /var/lib/dkms/mok.pub
   ```
   > You will be prompted to set a one-time password. Remember it for the next step.

4. **Restart** - your system will boot into the MOK Manager.
   - Choose **Enroll MOK**
   - Enter the password you set above
   - Reboot

5. **Verify** the module loaded:
   ```bash
   sudo dmesg | grep ryzen_smu
   ```
   > A "kernel tainted" message is expected and harmless - it simply indicates a non-mainline module was loaded.

---

## Configuration

UXTU4Unix stores its configuration at `UXTU4Unix/Assets/config.toml`. It is created and managed automatically, but can be edited manually if needed.

### Example `config.toml`

```ini
[User]
mode = Custom
customargs = --max-performance

[Settings]
time = 30
softwareupdate = 1
reapply = 1
applyonstart = 1
dynamicmode = 0
debug = 1

[Info]
cpu = AMD Ryzen 5 7535HS with Radeon Graphics
signature = Family 25, Model 68, Stepping 1
architecture = Zen 3 - Zen 4
family = Rembrandt
type = Amd_Apu
```

### `[User]`

| Key | Type | Description |
|-----|------|-------------|
| `mode` | string | Preset name to apply on load, or `Custom` to use `customargs` |
| `customargs` | string | Raw ryzenadj arguments used when `mode = Custom` |

### `[Settings]`

| Key | Default | Values | Description |
|-----|---------|--------|-------------|
| `time` | `3` | seconds | Interval between automatic preset re-applications |
| `softwareupdate` | `1` | `0` / `1` | Check for updates on startup |
| `reapply` | `1` | `0` / `1` | Automatically re-apply preset on a timer |
| `applyonstart` | `1` | `0` / `1` | Apply saved preset when the program launches |
| `dynamicmode` | `0` | `0` / `1` | Switch presets automatically based on power source |
| `debug` | `1` | `0` / `1` | Show debug output in the UI |
| `sip` | `03080000` | hex string | Required SIP flags for ryzenadj *(macOS only)* |

### `[Info]`

Populated automatically by dmidecode on first run. Stores CPU name, CPUID signature, architecture, codename, and type used for preset matching.

> **Tip:** If your CPU reports an unrecognised name (e.g. `AMD Demo CPU`), you can manually set `cpu` to a known model string such as `AMD Ryzen 5 7535HS with Radeon Graphics` to match the correct preset.

For advanced ryzenadj argument reference, see [Custom.md](Custom.md).

---

## Frequently Asked Questions

### Why does UXTU4Unix require SIP to be disabled on macOS?

The bundled `ryzenadj` and `DirectHW` binaries are treated as untrusted kernel extensions by macOS. SIP must be partially disabled and the `ALLOW_UNTRUSTED_KEXTS` flag (`0x1`) must be set in `csr-active-config` for them to run. UXTU4Unix's setup wizard handles this automatically.

### Why are some CPUs not supported?

When porting presets from UXTU to UXTU4Unix, some tuning commands were found to be incompatible with ryzenadj. UXTU uses additional methods to adjust CPU and APU settings beyond what ryzenadj exposes - particularly for desktop CPU presets. Only the compatible subset of commands was retained. Support is expanded with each release.

### Why is my preset not being applied on startup?

Check that `applyonstart = 1` is set in `config.toml` and that the `mode` value matches a valid preset name. You can verify this from **Settings -> Preset** in the UI.

### Does Dynamic Mode work on desktop CPUs?

Dynamic Mode is designed for laptops - it switches between presets based on whether the system is on AC or battery. On a desktop with no battery, it will always use the AC preset.

---

## Preview

<p align="left">
  <img src="/Img/main_menu.png" width="380"/>
  <img src="/Img/apply_preset.png" width="380"/>
  <img src="/Img/preset.png" width="380"/>
  <img src="/Img/preset_setting.png" width="380"/>
  <img src="/Img/hardware_info.png" width="380"/>
  <img src="/Img/settings.png" width="380"/>
</p>

---


## Acknowledgments

| Contributor | Contribution |
|-------------|-------------|
| [b00t0x](https://github.com/b00t0x) | Guidance on building ryzenadj with DirectHW and pciutils-osx |
| [FlyGoat](https://github.com/FlyGoat) | [RyzenAdj](https://github.com/FlyGoat/RyzenAdj) |
| [JamesCJ60](https://github.com/JamesCJ60) | [UXTU](https://github.com/JamesCJ60/Universal-x86-Tuning-Utility) original preset design and inspiration |
| [corpnewt](https://github.com/corpnewt) | macOS `.command` launcher template |
| [NotchApple1703](https://github.com/NotchApple1703) | Advisor |
