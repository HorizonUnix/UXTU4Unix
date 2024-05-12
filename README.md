<picture><img align="left" src="/Img/Logo.png" width="20%"/></picture>
<h1>UXTU4Unix (WIP)</h1>
<h3>Based on RyzenAdj and Python</h3>

![GitHub Downloads (all assets, latest release)](https://img.shields.io/github/downloads/AppleOSX/UXTU4Mac/total)

---

> [!CAUTION]
> - **Do not** use `UXTU4Unix` with [SMCAMDProcessor](https://github.com/trulyspinach/SMCAMDProcessor) as they may conflict with each other.
> - This is not an **alternative solution** to [SMCAMDProcessor](https://github.com/trulyspinach/SMCAMDProcessor), [NootedRed](https://github.com/ChefKissInc/NootedRed) and [AMDPlatformPlugin](https://github.com/ChefKissInc/AMDPlatformPlugin/) for their CPU/APU power management itself.

## Supported APU & OS

> [!NOTE]
> - AMD Ryzen APUs processors that are supported by either [NootedRed](https://github.com/ChefKissInc/NootedRed) or the **Premade Preset** section in [UXTU](https://github.com/JamesCJ60/Universal-x86-Tuning-Utility) (or simply supported by RyzenAdj)
> - Support ranges from macOS 10.4 to the latest version (14).
> - Linux is supported (tested on Debian-based distros, Fedora).

## Usage
- Disable `Secure Boot`
- Download the official build from [Releases](https://github.com/AppleOSX/UXTU4Unix/releases)
- Run `UXTU4Unix.command` (only for macOS) or run `UXTU4Unix.py` by using `python3` command ( `python3 /path/to/UXTU4Unix.py` )
- Follow the instructions.
- [macOS only] Disable `Core Performance Boost` in BIOS using [Smokeless_UMAF](https://github.com/DavidS95/Smokeless_UMAF) to achieve better temperature and better control with `UXTU4Unix` but sacrifice a lot of CPU performance

## FAQ
### 1. Why do we have to disable SIP in macOS?
- Honestly, the binary file (ryzenAdj and DirectHW) is recognized in macOS as untrusted kexts. So, in order to get it working, we have to disable SIP including the flag `ALLOW_UNTRUSTED_KEXTS` (0x1).
### 2. Why does `UXTU4Unix` lack CPU support?
- When I ported a bunch of AMD APU presets from `UXTU` to `UXTU4Unix`, some commands were not compatible with ryzenAdj (because `UXTU` uses lots of methods to change CPU/APU settings besides ryzenAdj), especially the CPU presets. So, I could only keep some commands as a `work-around`.
### 3. GUI wen eta?
- `idk` - NotchApple1703 said to me, but we will release it soon.

## For advanced users, please visit [Custom.md](Custom.md).
# Preview

<p align="left">
  <img src="/Img/main_menu.png">
  <img src="/Img/apply_preset.png">
  <img src="/Img/preset.png">
  <img src="/Img/preset_setting.png">
  <img src="/Img/settings.png">
</p>

> [!CAUTION]
> - We **think** the members and owners of ChefKiss Inc shouldn't use this tool. Why? Because Visual **will** say `Do not use this tool because it will break our NootedRed/AMDPlatformPlugin power management, etc...`. So, is that true? We still don't know because I've been banned from both Telegram and GitHub by ChefKiss (Visual)
> - PR is welcome btw

### Special thanks to
- [b00t0x](https://github.com/b00t0x) for the guide to build ryzenAdj based on DirectHW and pciutils-osx
- [JamesCJ60](https://github.com/JamesCJ60) for [UXTU](https://github.com/JamesCJ60/Universal-x86-Tuning-Utility)
- [corpnewt](https://github.com/corpnewt) for command file
- [NotchApple1703](https://github.com/NotchApple1703) for the GUI (starting from version `0.3.x` or `0.4.x`)
