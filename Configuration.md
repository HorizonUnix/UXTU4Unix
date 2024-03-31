## This Section Explains UXTU's Configuration File

- The configuration file, also known as the config file, is typically stored in the same folder as the script and is named `config.ini` (UXTU4Mac/config.ini). 
- Here is an example of a `config.ini` file:

```ini
[User]
password = 1234
preset = Assets.Presets.AMDAPUPostMatisse_U
mode = Balance
customargs = --enable-oc

[Settings]
time = 30
softwareupdate = 1
reapply = 1
applyonstart = 0
dynamicmode = 0
debug = 1
sip = 03080000
```

Explain:
### `[User]`

- `password`: This is the sudo password (or login password) required for 70% of UXTU4Mac operations, especially ryzenAdj
- `preset`: Path of preset config for various APUs and CPUs
- `mode` (string type): This parameter specifies which preset to run when the config file is loaded.
- `customargs` for custom args load
### `[Settings]`

- `time` (failsafe: 30): Sleep time (seconds) between next apply to SMU
- `softwareupdate` (failsafe: 1) (0:Disabled, 1:Enabled): This is a quirk that makes the script **skip** or **check** CFU on startup.
- `reapply` (failsafe: 1) (0:Disabled, 1:Enabled): To enable/disable auto reapply function
- `applyonstart` (failsafe: 1) (0:Disabled, 1:Enabled): To enable/disable apply preset when start script
- `dynamicmode` (failsafe: 0) (0:Disabled, 1:Enabled): Which enable/disable Dynamic mode for preset
- `debug` (failsafe: 1) (0:Disabled, 1:Enabled): To enable/disable DEBUG function
- `sip` (failsafe: 03080000): Required SIP for ryzenAdj
