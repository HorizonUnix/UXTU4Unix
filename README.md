
<h2>UXTU4Unix (Work-in-Progress)</h2>
<h4>Powered by RyzenAdj and Python</h4>

![GitHub Downloads (all assets, latest release)](https://img.shields.io/github/downloads/AppleOSX/UXTU4Mac/total)

---

> [!CAUTION]
> - **Caution:** Avoid using `UXTU4Unix` in conjunction with [SMCAMDProcessor](https://github.com/trulyspinach/SMCAMDProcessor) due to potential conflicts.
> - This project does not serve as an alternative to [SMCAMDProcessor](https://github.com/trulyspinach/SMCAMDProcessor), [NootedRed](https://github.com/ChefKissInc/NootedRed), or [AMDPlatformPlugin](https://github.com/ChefKissInc/AMDPlatformPlugin/) for CPU/APU power management.

## Supported APU & Operating Systems

> [!NOTE]
> - Compatible with AMD Ryzen APUs supported by either [NootedRed](https://github.com/ChefKissInc/NootedRed) or the **Premade Preset** section in [UXTU](https://github.com/JamesCJ60/Universal-x86-Tuning-Utility) (or generally supported by RyzenAdj).
> - Operating Systems: macOS 10.9 through 15, and Linux (tested on Debian-based distributions and Fedora).

## Usage Instructions

- Disable `Secure Boot` in the BIOS. (Unknown: Applying the Secure Boot certificate to UEFI may enable compatibility.)
- Download the official build from the [Releases](https://github.com/AppleOSX/UXTU4Unix/releases).
- Run `UXTU4Unix.command` (macOS only) or run `UXTU4Unix.py` using the command: `python3 /path/to/UXTU4Unix.py` or `python /path/to/UXTU4Unix.py`.
- Follow the on-screen instructions.
- [macOS only] For enhanced temperature management and control with `UXTU4Unix`, disable `Core Performance Boost` in the BIOS using [Smokeless_UMAF](https://github.com/DavidS95/Smokeless_UMAF). Note that this may significantly reduce CPU performance, as the `Core Performance Boost` feature on macOS is not optimal.

## Fixing Python Certificates on macOS

<p align="left">
  <img src="/Img/cert1.png">
  <img src="/Img/cert2.png">
</p>

## Frequently Asked Questions

### 1. Why is SIP disabled in macOS?
- The binaries (ryzenAdj and DirectHW) are flagged as untrusted kexts in macOS. To ensure functionality, it is necessary to disable SIP and include the `ALLOW_UNTRUSTED_KEXTS` flag (0x1).

### 2. Why does `UXTU4Unix` lack comprehensive CPU support?
- During the transition of AMD APU presets from `UXTU` to `UXTU4Unix`, some commands were incompatible with ryzenAdj. `UXTU` employs various methods to modify CPU/APU settings beyond those supported by ryzenAdj, particularly concerning CPU presets. Consequently, only select commands were retained as workarounds.

### 3. What is the timeline for the GUI?
- The release of the GUI is forthcoming, as communicated by NotchApple1703.

## Advanced Users
For more detailed configurations, please refer to [Custom.md](Custom.md).

# Preview

<p align="left">
  <img src="/Img/main_menu.png">
  <img src="/Img/apply_preset.png">
  <img src="/Img/preset.png">
  <img src="/Img/preset_setting.png">
  <img src="/Img/settings.png">
</p>

### Acknowledgments
- Special thanks to [b00t0x](https://github.com/b00t0x) for guidance on building ryzenAdj based on DirectHW and pciutils-osx.
- [JamesCJ60](https://github.com/JamesCJ60) for contributions to [UXTU](https://github.com/JamesCJ60/Universal-x86-Tuning-Utility).
- [corpnewt](https://github.com/corpnewt) for the command file on macOS.
- [NotchApple1703](https://github.com/NotchApple1703) for the GUI (starting from `0.4.x`).
