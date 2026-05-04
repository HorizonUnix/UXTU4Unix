<picture><img align="left" src="/Img/Logo.png"/></picture>
<h4>Powered by RyzenAdj and Python</h4>
 
[![GitHub Downloads](https://img.shields.io/github/downloads/HorizonUnix/UXTU4Unix/total?style=flat-square&color=blue)](https://github.com/HorizonUnix/UXTU4Unix/releases)
[![Latest Release](https://img.shields.io/github/v/release/HorizonUnix/UXTU4Unix?style=flat-square&color=green)](https://github.com/HorizonUnix/UXTU4Unix/releases/latest)
[![Python](https://img.shields.io/badge/Python-3.10%2B-yellow?style=flat-square)](https://www.python.org/)
[![License](https://img.shields.io/github/license/HorizonUnix/UXTU4Unix?style=flat-square)](LICENSE)
 
<br/>
 
## Overview
 
UXTU4Unix is a power management tool for **AMD Ryzen APUs and CPUs** on Linux (and formerly macOS). It wraps [RyzenAdj](https://github.com/FlyGoat/RyzenAdj) with an interactive terminal UI and a background systemd daemon, letting you apply and auto-switch power presets without touching the BIOS.
 
**Key features:**
- Premade presets for a wide range of AMD APUs and desktop CPUs
- Dynamic Mode - auto-switches between presets on AC vs. battery
- Auto-reapply on a configurable timer via background daemon
- Built-in updater with config backup and restore
- Secure keyring-backed sudo password storage
---
 
## Compatibility
 
| Platform | Status |
|----------|--------|
| Linux - systemd, Python 3.10+ | ✅ Actively supported |
| macOS 11 – 15 | ⚠️ Deprecated as of v0.5.22 [Wiki](https://github.com/HorizonUnix/UXTU4Unix/wiki/macOS-Installation-and-Troubleshooting) |
 
> [!IMPORTANT]
> **systemd is required.** Distros using OpenRC, runit, or other init systems are not supported.
 
---
 
## Installation
 
```bash
curl -fsSL https://raw.githubusercontent.com/HorizonUnix/UXTU4Unix/main/install.sh | bash
```
 
For full details, troubleshooting, and manual steps see the **[Wiki](../../wiki)**.
 
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
 
## Acknowledgments
 
| Contributor | Contribution |
|-------------|-------------|
| [b00t0x](https://github.com/b00t0x) | Guidance on building ryzenadj with DirectHW and pciutils-osx |
| [FlyGoat](https://github.com/FlyGoat) | [RyzenAdj](https://github.com/FlyGoat/RyzenAdj) |
| [JamesCJ60](https://github.com/JamesCJ60) | [UXTU](https://github.com/JamesCJ60/Universal-x86-Tuning-Utility) preset design and inspiration |
| [corpnewt](https://github.com/corpnewt) | macOS `.command` launcher template |
| [NotchApple1703](https://github.com/NotchApple1703) | Advisor |
 
