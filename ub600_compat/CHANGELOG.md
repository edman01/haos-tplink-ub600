# Changelog

## 0.1.1 - Adapter presence guard (experimental)

- Require a visible USB device with VID/PID `37ad:0600` before preparing
  the driver and recheck before kernel commands and driver unloading.
- Wait without driver changes if the adapter is absent or sysfs cannot be
  read; retry every 30 seconds, including when another adapter uses btusb.
- Read no serial numbers, MAC addresses or sensor data.
- Add offline presence, hot-unplug and retry-loop regression tests.
- Clarify shared USB identifiers and waiting behavior in English.

The new guard is offline-tested, not a new hardware compatibility claim.
End-to-end public app-store installation on another system remains untested.

## 0.1.0 - Experimental initial public release

- Package the hardware-tested four-byte UB600 Realtek quirk workaround as a
  Home Assistant OS app repository.
- Add a public-release gate for the exact tested kernel and original module
  SHA-256 before any driver unloading.
- Preserve the original OS module and attempt stock-driver recovery on
  patched-module load failure.
- Include synthetic parser tests, mocked loader tests, publication checks,
  English instructions and upstream-fix references.
- Exclude all private sensor integrations, device identities, credentials,
  home configuration, backups and raw logs.

Hardware validation is limited to the configuration in the repository
README. Public packaging and new safety guards have offline tests; no
multi-system compatibility claim is made.
