# v0.1.0 - Experimental UB600 compatibility app

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
