## This Section Explains UXTU's Configuration File

- The configuration file, also known as the config file, is typically stored in the same folder as the script and is named `config.ini` (UXTU4Mac/config.ini). 
- Here is an example of a `config.ini` file:

```ini
[User]
fip = 0
mode = Custom
loginitems = 1
password = 2009
skipcfu = 0
customargs = --max-performance

```
Explain:
- `fip` (failsafe: 0) (0:Disabled, 1:Enabled): To enable FIP ( File Integrity Protection )
- `mode` (string type): This parameter specifies which preset to run when the config file is loaded.
- `loginitems` (failsafe: 0) (0:Disabled, 1:Enabled): This parameter tells the script that it has been added to Login Items and will not ask for the next setting adjustment.
- `password`: This is the sudo password required for 70% of UXTU4Mac operations, especially ryzenAdj.
- `skipcfu` (failsafe: 0) (0:Disabled, 1:Enabled): This is a secret quirk that makes the script **skip** check CFU on startup.
- `customargs` for custom args load
