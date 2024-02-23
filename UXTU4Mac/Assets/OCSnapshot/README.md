# OCSnapshot
Python CLI version of ProperTree's OC Snapshot function.

```
usage: OCSnapshot.py [-h] [-i INPUT_FILE] [-o OUTPUT_FILE] [-s SNAPSHOT]
                     [-v OC_VERSION] [-c] [-f]

options:
  -h, --help            show this help message and exit
  -i INPUT_FILE, --input-file INPUT_FILE
                        Path to the input plist - will use an empty dictionary
                        if none passed.
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        Path to the output plist if different than input.
  -s SNAPSHOT, --snapshot SNAPSHOT
                        Path to the OC folder to snapshot.
  -v OC_VERSION, --oc-version OC_VERSION
                        The OC version schema to use. Accepts X.Y.Z version
                        numbers, latest, or auto-detect. Default is auto-
                        detect.
  -c, --clean-snapshot  Remove existing ACPI, Kernel, Driver, and Tool entries
                        before adding anew.
  -f, --force-update-schema
                        Add missing or remove erroneous keys from existing
                        snapshot entries.
  ```
