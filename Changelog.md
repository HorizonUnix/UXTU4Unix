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

