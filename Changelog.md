## [0.3.1]

## General

- Refactor code for `Linux` and `macOS` Edition
- Fix DIR logic on `Linux`

## [0.3.03]

## General

- Fix `ReApply` settings logic
## [0.3.02]

- Moved from `AppleOSX` to @HorizonUnix
## [0.3.01]

## General
- Fix the detection order of `G` and `GE` APU.
- Remove the Intel check; RyzenAdj checks itself.
- Fix the issue with unsupported hardware
## [0.3.0]

## General
- Support CPU (Desktop CPU)
- Use UXTU codename instead of RyzenAdj for future support
- Improve logic to get presets
- Fix DIR
- Optimize code
- Get Family, Model to translate CPU/APU codename
- Use dmidecode to get CPU information
- Only get information for the first time, after that, read info from the config file
- Add a check for Intel chipset
- Fix logging file
### Linux
- Support Hardware Information
- Extend Terminal or Shell Window to 100x30
### macOS
- Use dmidecode from [Acidanthera](https://github.com/acidanthera/dmidecode)
## [0.2.9]

### General
- Fixed Phoenix support
- Removed Mendocino support because it is not supported by RyzenAdj
- Removed some old APU codenames and used RyzenAdj codenames instead
- Fixed some annoying issues with Settings, Apply preset, Dynamic mode, Auto reapply

## macOS
- Forced to use Py3 instead of Py2
- Removed SSL check due to some issues
- Fixed and synced DIR logic with Linux

## Linux
- Removed `SIP` settings because it is only for macOS
## [0.2.8]

### General
- Rename from `UXTU4Mac` to `UXTU4Unix`
- Support Linux (tested on Debian-based distro)
- Rework project structure
### macOS 
- Removed GPU/APU info
### Please download from GitHub if you failed update from built-in updater

## [0.2.7]

- Fixed a bug with the Updater
- Fixed a bug with CFU
- Reformatted CLI
- Improved support for Mendocino APU
## This is the first official commercial version for everyone, after numerous bug fixes and improvements
## [0.2.6]

- Extended APU support based on RyzenAdj
- Supported RyzenAdj v0.15.0
- Removed some information in Hardware information
- Added a logic to preset
## [0.2.5]

- Fixed a bug related to CFU
- Fixed various bugs related to the get_presets function
- Fixed the logic in the welcome_tutorial
- Added an SSL certificate check before running CFU to avoid hangs (thanks to @nlqanh524)
## [0.2.41]

- Fix various bug related to Welcome tutorial and get presets
- Fix filename

## [0.2.4]

- Extended presets based on UXTU's preset.
- Added support for each APU Generation Preset, similar to UXTU.
- Quick fix to Updater and CFU.
- Fix line error in `Hardware Information`
- New `9. Debug` under `Settings` to enable/disable some debug processes
### Currently, UXTU4Mac lacks CPU support because some commands in the original UXTU are incompatible with ryzenAdj.
## [0.2.32]

- Quick fix to Updater and CFU
### Please download from GitHub if you failed update from built-in updater
## [0.2.31]

- Fix line error in `Hardware Information`
- New `9. Debug` under `Settings` to enable/disable some debug processes
## [0.2.3]

## Software Update
- No longer keep Logs folder
## Apply Preset
- Fixed a stupid bug about sudo password
- Restored debug function

## [0.2.2]

### FIP:
- Removed/dropped support for FIP
- Removed FIP check in CFU
### Settings:
- Fixed various bugs related to `1. Preset` settings
- Fixed various bugs related to Dynamic Mode
- Reworked some logic
- Default config file is now located in `UXTU4Mac/Assets`
- New config file structure
### Welcome Tutorial:
- Improved some processes
### Hardware Information:
- Removed `Device Information`
- Removed `UXTU4Mac dependencies`
### Checks For Update:
- Now, if the script fails to fetch the latest version, it will retry 10 times. Afterward, it will ask whether to skip CFU or not.
### Other:
- Completely reworked the entire code structure
## [0.2.1]
## Input
- Improve user input handle
## .command file
- Default Terminal window when open now 100x30 instead of 80x20
## Other
- Reorder code structure
## [0.2.0]

### This update brings to you a similar experience from the UXTU from Windows
## Dynamic Mode
- Reworked dynamic mode logic
- Now, instead of tracking processes, it will track the battery to switch suit modes
- Added a new logical check: if it's still the same mode, it will not reapply
## Settings
- Added a new `4. Auto reapply` option under `Settings` to enable/disable auto reapply preset function
- Default setting will disable auto reapply
## Preset
- Properly ported preset from UXTU
- Added new presets `AC` and `DC` which are for some APU/CPU
## Other
- Using a new banner
- Displaying CPU name under the banner

## [0.1.9]

- Remove OcSnapShot
- Remove `DirectHW.kext` since ryzenAdj already do that with pciutils
- Fix a bug about Dynamic Mode
- New `SIP Flags` under Settings which change the required SIP flags
## [0.1.82]

- Proper support for Dynamic mode
- Fix various bug about Dynamic mode and preset
## [0.1.81]

- Fix a bug with Dynamic mode
## Please delete your old `config.ini` since it will not worked on this version
## [0.1.8]

- Support Dynamic mode aka Adaptive mode on UXTU, still in beta process
### Happy Women Day (8/3)!
## [0.1.73]

- Small changes to main menu, install menu and processes
## [0.1.72]

- Rework CLI
- Remove some function in About UXTU4Mac
- Improve logic
## [0.1.71]

- Small changes for code structure
## [0.1.7]

- Fix a serious bug about `apply_smu`
- Rework some code structure
- Rebrand with new logo for CLI
- New command file thanks to @corpnewt source code
- Better experience
- Optimize code
## [0.1.63]

- Fix a bug with built-in Updater
- Remove `sys` library
## [0.1.62]

- Fix a bug with CFU
- Fix a bug with `apply_smu`
- Change default SIP flags from `03080000` to `0B080000` which higher than `03080000`
### Please reinstall your kext and SIP through Settings -> Install UXTU4Mac Kexts
## [0.1.61]

- Rework `Settings` menu
- Proper support for Login Items
- Change SIP flags from `7F080000` to `03080000`
### Please reinstall your kext and SIP through Settings -> Install UXTU4Mac Kexts
## [0.1.6]

- Reworked the entire code structure
- Script now runs faster with better optimization
- Fix various bugs related to loops and other function
- Use While loop instead `threading` for `apply_smu` a.k.a `run_cmd`
## [0.1.52]

- Fix a bug with `Welcome` section
- Proper config file check before start script
## [0.1.51]

- Fix a bug when disable login items does not actually delete it
- Fix a bug with `run_cmd` and related
- Fix a bug with `Welcome` section
- Fix a bug with `About UXTU4Mac` section
- Now will check both FIP and CFU status before disable one of them due to some issues
## [0.1.5]

- Fix a lot of bug related to `Settings` and other sections
- Default sleep time now `10`s instead of `3`s
- New Time Sleep settings under `Settings` to set sleep time
- Improve handling about user option
  
## [0.1.4]

- Enhance FIP, more secure and safe
- Rework `Settings` and `Welcome` section
- Add a build number
- Add a new update name
- Now `Settings` have these section:
```
P. Preset setting
F. FIP setting
C. CFU setting
L. Login Items setting
S. Sudo Password setting
```

## [0.1.3]

- Support for Custom preset for config file
- Introduce FIP ( File Integrity Protection ) which protect main script file ( Beta ), disabled by default
- Now check SIP flags before running ryzenAdj

## [0.1.2]

- Fix a bug when Updater doesn't delete zip file after update
- Now script will restart itself after update
- Now script will check DirectHW.kext and debug=0x144 before running ryzenAdj
- New section name `UXTU4Mac dependencies` under About UXTU4Mac to check DirectHW.kext and debug=0x144

## [0.1.11]

- Add a tester list
- Make CLI look better with a little rework
- Fix a bug with Install kext and dependencies
- Fix a bug with About UXTU4Mac

## [0.1.1]

- Support backup `Logs` folder and `config.ini` when update UXTU4Mac
- Support show changelog on updater
- Fix a bug with CFU
- Now users have another option to specify config.plist path for install kext and dependencies
- Add a note after install kext and dependencies

## [0.1.0]

### Welcome to version series `0.1.x` with a better experience of using UXTU4Mac

- Include a B. Back button when applying the preset
- Add `I. Install kexts and dependencies (Beta)` to install kexts in `OC/Kexts/` and set SIP and `boot-args` automatically
- Now, when running the script, it will always apply the preset; users can press B to go back to the main menu
- Remove `SkipWelcome` in the config file
- Use OCSnapShot from @corpnewt for snapshot config files
- When running the script for the first time, it will install kexts automatically
- Improved welcome setup
- Cleaned up
- Fixed a bug with CFU
- Support Updater
- Add `LoginItems` to the config file
- Support force updating to the latest version under About UXTU4Mac
- Support applying presets from available presets beside loading from the config file
### Please delete your old `config.ini` since it's from the `0.0.x` series and incompatible with series `0.1.x`


## [0.0.98]

- Optimize code
- Add a logic to check sudo password
- Add a welcome tutorial (beta)


## [0.0.97]

- Supported for CPU codename and SMU version properly ( replace for the long dict in `0.0.96` )
- Add some warning and note
- Fix and add some hardware information
- Make output look cleaner


## [0.0.96]

- Support for more hardware information
- Fix a issue when no internet connection result a config override
### This will be the last update for `0.0.x` series


## [0.0.95]

- Support Hardware Information reader
- Switched to logging method
- Support logging to file ( Stored in `Logs` folder )
### This will be the last update for `0.0.x` series
![Screenshot 2024-02-12 at 22 30 00](https://github.com/gorouflex/UXTU4Mac/assets/98001973/c7faee7b-3f5c-49d7-9362-776206858795)
### 13/2/2024: Fixed a small issue when no internet connection result a config override

## [0.0.94]

- Bring back some UXTU preset
- Add a `SkipCFU` in config file to skip CFU when start (user customized)
- Adjust some guide


## [0.0.93]

- Support for Login Items in macOS ( aka Startup App )
- Refactored code


## [0.0.92]

- Supported for custom preset
- Fix image not being shown on CFU
- Rework structure


## [0.0.91]

- Optimize code
- Fix an issue when tool cannot instanly update config file


## [0.0.9]

### Change log

- Moved to @AppleOSX


## [0.0.8]

### Change log

- Removed useless Preset
- Add new `Auto` preset


## [0.0.7]

### Change log

- Fix args for `Performance` preset
- Add 3 `force` option for `Eco`, `Balance`, and `Extreme`

![image](https://github.com/gorouflex/RielUXTU4Mac/assets/98001973/05609b0d-94f7-4db8-9a2f-42739a38020c)


## [0.0.6]

### v0.0.6 introduces a new way for you to use `RielUXTU4Mac`
### This might the last version of `0.0.x` series
### With the support of @NotchApple1703 i will support GUI soon
### Change log
- New CLI
- New About menu
- New `skipwelcome` in config to skip welcome menu
- Adjust args for `Balance` and `Extreme` Preset

## [0.0.5]

### Change log
- Simplified and optimized code
- Now save password for the next run without require sudo password again
- Show current preset every loop


## [0.0.4]

### Change log
- Support CFU
- Support R&W config file
- Dropped supported for custom arg ( tempo )


## [0.0.3]

- Turn verbose on for debugging
- Add a clear screen function
- Fix GitHub file type

## [0.0.2]

### Change log
- Fix env ( 1 and 255 status code )


## [0.0.1]

### Change log
- Intial commit
- Support RyzenAdj v0.14.0

