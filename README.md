<picture><img align="left" src="/Img/Logo.png" width="20%"/></picture>
<h1>UXTU4Mac (WIP)</h1>
<h3>UXTU but for macOS</h3>
<h3>Based on RyzenAdj</h3>

---

## Due to some issues, we'll delay version 0.1.x (which introduces a new GUI) to 3 weeks
## Supported CPU/APU

| Codename | Name |
| :---: | :---: |
| Raven (Ridge) | 2xxxU/H/G/GE |
| Picasso | 3xxxU/H/G/GE |
| Dali | 3xxxU/G |
| Renoir | 4xxxU/H/HS/G/GE |
| Lucienne | 5xxxU |
| Cezanne | 5xxxU/H/HS/HX/G/GE |
| Rembrandt | 6xxx (N/A) |

> [!NOTE]
> If your CPU/APU is supported by [NootedRed](https://github.com/ChefKissInc/NootedRed)/[UXTU](https://github.com/JamesCJ60/Universal-x86-Tuning-Utility), you can also use this tool too.

## Usage

- Download from [Releases](https://github.com/AppleOSX/UXTU4Mac/releases).
- Add `DirectHW.kext` to `EFI\OC\Kexts` and snapshot to `config.plist`.
- Disable SIP (<7F080000>) at `csr-active-config` (this flag can be known as `csrutil disable`).
- Add `debug=0x44` or `debug=0x144` to `boot-args`.
- Reboot and reset NVRAM to take effect.
- [Optional] Disable `Core Performance Boost` in BIOS using [Smokeless_UMAF](https://github.com/DavidS95/Smokeless_UMAF) to get better temperature but sacrifice a lot of performance.
- Run `start-macOS.command`.
- Follow the instructions.

### Auto preset results in better power management (2:30 hours of my battery usage).
### The Extreme preset yields the full potential performance that my Ryzen 5 4500U (Renoir) can handle but only lasts for 1:30 hours of my battery usage. To achieve maximum performance, please plug in with AC.
### [Removed] ECO Preset
![IMG_0124](https://github.com/gorouflex/RielUXTU4Mac/assets/98001973/1d67984a-1166-4551-a1b6-04865b72c53b)

### [Replaced with another args] Extreme Preset
![IMG_0123](https://github.com/gorouflex/RielUXTU4Mac/assets/98001973/46565c9a-8abd-4b9f-ad2e-5bde5c39a4c1)

### Special thanks to
- [NotchApple1703](https://github.com/NotchApple1703) for the GUI (after ver 0.1.x)
- [b00t0x](https://github.com/b00t0x) for the guide
- [JamesCJ60](https://github.com/JamesCJ60) for [UXTU](https://github.com/JamesCJ60/Universal-x86-Tuning-Utility)
