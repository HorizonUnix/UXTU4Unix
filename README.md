<picture><img align="left" src="/Img/Logo.png" width="20%"/></picture>
<h1>UXTU4Mac (WIP)</h1>
<h3>UXTU but for macOS (riel 🐧)</h3>
<h3>Based on RyzenAdj</h3>

![GitHub Downloads (all assets, latest release)](https://img.shields.io/github/downloads/AppleOSX/UXTU4Mac/total)

---

## Supported APU/CPU
> [!NOTE]
> - If your AMD Ryzen APU/CPU is supported by [NootedRed](https://github.com/ChefKissInc/NootedRed) **or** [UXTU](https://github.com/JamesCJ60/Universal-x86-Tuning-Utility) premade preset section, you can also use this tool.
> - Some `Athlon` APU/CPU are also supported by `UXTU4Mac` if the CPU codenames match with the list below:

| Codename | Product Name |
| :---: | :---: |
| Raven (Ridge) | 2xxxU/H/G/GE |
| Picasso | 3xxxU/H/G/GE |
| Dali | 3xxxU/G |
| Renoir | 4xxxU/H/HS/G/GE |
| Lucienne | 5xxxU |
| Cezanne | 5xxxU/H/HS/HX/G/GE |
| Rembrandt | 6xxx (N/A) |

## Usage

- Install Python from [here](https://www.python.org).
- Download from [Releases](https://github.com/AppleOSX/UXTU4Mac/releases).
- Add `DirectHW.kext` to `EFI\OC\Kexts` and snapshot to `config.plist`.
- Disable SIP (`<7F080000>`) at `csr-active-config` (this flag can be known as `csrutil disable`, and supports patching WiFi on Sonoma).
- Add `debug=0x44` or `debug=0x144` to `boot-args`.
- Reboot and reset NVRAM to take effect.
- [Optional] Disable `Core Performance Boost` in BIOS using [Smokeless_UMAF](https://github.com/DavidS95/Smokeless_UMAF) to get better temperature but sacrifice a lot of performance.
- Run `UXTU4Mac.command`.
- Follow the instructions.

## For advanced users, please visit [Custom.md](Custom.md).

## Comparison 

|  | UXTU | UXTU4Mac |  
|    :---:     |    :---:   |    :---:   |
| GUI | ✅ | ❌ No, currently only for CLI |
| Adjust power management settings | ✅ | ✅ |
| Premade presets | ✅ | ✅ |
| Custom presets | ✅ | ✅ |
| Adaptive mode tracking | ✅ | ❌ |
| Games mode tracking | ✅ | ❌ |
| Auto mode | ✅ | ✅ |
| Support for many hardware | ✅ | ❌ Only for some AMD Ryzen APU/CPU models, [see here](#supported-cpuapu) |

## Check if `DirectHW.kext` is being loaded or not?

<p><img align="center" src="/Img/ck_kext1.png"/><img align="center" src="/Img/ck_kext2.png"/></p>

# Preview
### Auto preset results in better power management (2:30 hours of my battery usage).
### The Extreme preset yields the full potential performance that my Ryzen 5 4500U (Renoir) can handle but only lasts for 1:30 hours of my battery usage. To achieve maximum performance, please plug in with AC.
### Extreme Preset
![Screenshot 2024-02-12 at 15 52 16](https://github.com/AppleOSX/UXTU4Mac/assets/98001973/19e1481a-07ae-4efb-9b50-fac0cf137e0a)

### Special thanks to
- [NotchApple1703](https://github.com/NotchApple1703) for the GUI (after ver 0.1.x)
- [b00t0x](https://github.com/b00t0x) for the guide
- [JamesCJ60](https://github.com/JamesCJ60) for [UXTU](https://github.com/JamesCJ60/Universal-x86-Tuning-Utility)
