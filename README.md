<picture><img align="left" src="/Img/Logo.png"/></picture>
<h4>Powered by RyzenAdj and Python</h4>

![GitHub Downloads (all assets, latest release)](https://img.shields.io/github/downloads/HorizonUnix/UXTU4Unix/total)

---
> [!WARNING]
> - With the end of Hackintosh support in macOS 26 Tahoe, UXTU4Unix `v0.4.x` series will be the last version to support macOS. After that, we will shift our focus solely to Linux until `UXTU` officially supports Linux.
> - **Warning (macOS):** Avoid using `UXTU4Unix` in conjunction with [SMCAMDProcessor](https://github.com/trulyspinach/SMCAMDProcessor) due to potential conflicts.

### Supported APU & Operating Systems

 - Compatible with AMD Ryzen APUs supported by either [NootedRed](https://github.com/ChefKissInc/NootedRed) or the **Premade Preset** section in [UXTU](https://github.com/JamesCJ60/Universal-x86-Tuning-Utility) (or generally supported by RyzenAdj).
 - Operating Systems: macOS 11 through 26, and Linux (with the Python `keyring` library and Linux `libpci` installed).

### Usage Instructions

**General:**
- Download the official build from the [Releases](https://github.com/AppleOSX/UXTU4Unix/releases).
- Navigate to the downloaded directory in your terminal and install the required dependencies using:
  ```bash
  pip3 install -r requirements.txt
  ```

#### For macOS
1. Disable **Secure Boot** in the BIOS. *(Unknown: Applying the Secure Boot certificate to UEFI may enable compatibility.)*
2. Run `UXTU4Unix.command`, or run the Python script using the terminal: 
   ```bash
   python3 /path/to/UXTU4Unix.py
   ```
3. **Optional (Temperature Management):** For enhanced temperature management and control with `UXTU4Unix`, disable **Core Performance Boost** in the BIOS using [Smokeless_UMAF](https://github.com/DavidS95/Smokeless_UMAF). *Note that this may significantly reduce CPU performance, as the `Core Performance Boost` feature on macOS is not optimal.*

#### For Linux
1. Run the Python script using the terminal:
   ```bash
   python3 /path/to/UXTU4Unix.py
   ```
2. **Secure Boot:** You must either **disable Secure Boot** in your BIOS, OR install the `ryzen_smu` kernel module from RyzenAdj to allow it to function with Secure Boot enabled.

**Adding the `ryzen_smu` kernel module (If keeping Secure Boot enabled):**
To let RyzenAdj use the `ryzen_smu` module, you have to install it first, as it is not part of the standard Linux kernel.

1. **Install Prerequisites** (Fedora example):
   ```bash
   sudo dnf install cmake gcc gcc-c++ dkms openssl
   ```
2. **Clone and Install `ryzen_smu`:**
   ```bash
   git clone [https://github.com/amkillam/ryzen_smu](https://github.com/amkillam/ryzen_smu) # Active fork of the original module
   cd ryzen_smu/ 
   sudo make dkms-install
   ```
3. **Enroll UEFI Keys:** Because you are using Secure Boot, you have to enroll the UEFI keys that `dkms` generated on its first run. These must be added to your machine's UEFI key database. 
   ```bash
   sudo mokutil --import /var/lib/dkms/mok.pub
   ```
   *Note: This command will ask you to set a password. This password is only needed one single time later in the MOK manager.*
4. **Restart and Configure MOK:**
   Restart your system. This will boot into the MOK manager. Choose **Enroll MOK**, enter your password from the previous step, and then reboot. 
5. **Verify:** The module is now loaded and visible via `dmesg`. It will show a message about the kernel being tainted, but this just means it loaded a (potentially proprietary) binary blob.

### Fixing Python Certificates on macOS

<p align="left">
  <img src="/Img/cert1.png">
  <img src="/Img/cert2.png">
</p>

## Frequently Asked Questions

### 1. Why is SIP disabled in macOS?
- The binaries (ryzenAdj and DirectHW) are flagged as untrusted kexts in macOS. To ensure functionality, it is necessary to disable SIP and include the `ALLOW_UNTRUSTED_KEXTS` flag (0x1).

### 2. Why does `UXTU4Unix` lack comprehensive CPU support?
- During the transition of AMD APU presets from `UXTU` to `UXTU4Unix`, some commands were incompatible with ryzenAdj. `UXTU` employs various methods to modify CPU/APU settings beyond those supported by ryzenAdj, particularly concerning CPU presets. Consequently, only select commands were retained as workarounds.

## Advanced Users
For more detailed configurations, please refer to [Custom.md](Custom.md).

## Preview

<p align="left">
  <img src="/Img/main_menu.png">
  <img src="/Img/apply_preset.png">
  <img src="/Img/preset.png">
  <img src="/Img/preset_setting.png">
  <img src="/Img/hardware_info.png">
  <img src="/Img/settings.png">
</p>

### Acknowledgments
- Special thanks to [b00t0x](https://github.com/b00t0x) for guidance on building ryzenAdj based on DirectHW and pciutils-osx.
- [FlyGoat](https://github.com/FlyGoat/) for [RyzenAdj](https://github.com/FlyGoat/RyzenAdj)
- [JamesCJ60](https://github.com/JamesCJ60) for contributions to [UXTU](https://github.com/JamesCJ60/Universal-x86-Tuning-Utility).
- [corpnewt](https://github.com/corpnewt) for the command file on macOS.