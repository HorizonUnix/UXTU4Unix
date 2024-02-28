## This Section Explains UXTU's Configuration File

- The configuration file, also known as the config file, is typically stored in the same folder as the script and is named `config.ini` (UXTU4Mac/config.ini). 
- Here is an example of a `config.ini` file:

```ini
[User]
password = 1234
loginitems = 1
cfu = 1
fip = 1
time = 10
mode = Auto
customargs = --enable-oc
```
Explain:
- `password`: This is the sudo password (or login password) required for 70% of UXTU4Mac operations, especially ryzenAdj.
- `loginitems` (failsafe: 0) (0:Disabled, 1:Enabled): This parameter tells the script that it has been added to Login Items.
- `cfu` (failsafe: 1) (0:Disabled, 1:Enabled): This is a quirk that makes the script **skip** or **check** CFU on startup.
- `fip` (failsafe: 0) (0:Disabled, 1:Enabled): To enable FIP ( File Integrity Protection )
- `mode` (string type): This parameter specifies which preset to run when the config file is loaded.
- `customargs` for custom args load
