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

