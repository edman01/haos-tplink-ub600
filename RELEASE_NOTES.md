# v0.1.1 - Experimental UB600 presence guard

Adds a read-only USB VID/PID presence check before changing the Bluetooth
driver. If UB600 is absent or cannot be observed, the app waits and retries
every 30 seconds without unloading the driver. It rechecks presence just
before unloading; physical removal can still race with that final check.

`37ad:0600` is a shared vendor/product ID, not an individual serial number.
No serial numbers, MAC addresses or sensor data are read by the new guard.
Offline tests cover detection, absence, read errors, hot-unplug and retries.
Public app-store installation on a second system remains untested.

Temporary Home Assistant OS workaround for TP-Link UB600 **USB ID 37ad:0600**
when the stock driver does not apply the Realtek firmware-loading quirk.

**Prefer an official HAOS update with native support.** The upstream fix
already exists; it is present in Linux 6.18.45.

## Scope

- Hardware-tested repair: HAOS 18.2, amd64, VirtualBox, kernel 6.18.39-haos.
- The public loader accepts only the exact tested original module hash.
- Four bytes change in a separate module copy; the OS file remains unchanged.
- AppArmor/protection mode remain enabled. SYS_MODULE is still a powerful
  host-level privilege, and all USB Bluetooth connections may briefly drop.
- No sensor configuration or personal server data is included.

See the [README](README.md) and [installation/recovery guide](ub600_compat/DOCS.md)
before adding the repository to Home Assistant. This release is experimental;
offline tests are not proof of compatibility on other hardware.
