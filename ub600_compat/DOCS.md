# Installation, verification and recovery

## Before installation

- Use this only for **TP-Link UB600 USB ID `37ad:0600`** with the symptoms
  described in the repository README. An adapter being visible does not
  establish that its firmware loaded or that it receives advertisements.
- Check for an official **Home Assistant OS** update with the upstream UB600
  fix first. Updating Home Assistant Core alone does not replace the host
  kernel. This workaround is unnecessary when the native driver works.
- This release replaces only the exact unsigned amd64 module build recorded
  in the compatibility table. It deliberately rejects other builds.
- Make a current Home Assistant backup and ensure you can access the host or
  VM console. Do not depend solely on Bluetooth input devices for recovery.
- Choose a maintenance window: starting/restarting the app unloads the
  shared `btusb` module and can interrupt other USB Bluetooth devices.
- For a VM, pass the physical USB adapter through to the Home Assistant OS
  guest, including after a host reboot. Windows recognizing the adapter is
  not enough. Do not pass a Zigbee stick to a Bluetooth integration.

Do not disable Secure Boot, module-signature enforcement, AppArmor or
protection mode to get around a refusal. Do not use this workaround as the
sole basis for a safety-critical monitoring system.

## Add the repository and install

1. Open Home Assistant **Settings > Apps** (or **Add-ons** on older versions)
   and open the app store.
2. Open its menu and choose **Repositories**. Add:

   ```text
   https://github.com/edman01/haos-tplink-ub600
   ```

3. Refresh the store if necessary. Open **TP-Link UB600 Bluetooth
   compatibility** and select **Install**. Supervisor builds the image from
   this repository; the first download can be large.
4. Keep **Protection mode** on. Enable **Start on boot**. There are no
   configuration options, tokens or sensor addresses to enter.
5. Start the app during the maintenance window and read its log.

Do not run a second local copy of this app alongside the repository version.
If a local repair copy is already installed, disable its start-on-boot and
stop it before using this package. Do not edit or delete Home Assistant
configuration or sensor registries to install this adapter workaround.

## Verify the repair

Successful log output includes `patched_copy`, a four-byte change report,
and `UB600 compatibility driver loaded; stock module unchanged`.

The app stores a status report and source/copy SHA-256 hashes in its own
`/data` volume. It does not expose a web interface or network listener.

In the Home Assistant OS host kernel log, a working Realtek initialization
includes firmware loads for:

```text
rtl_bt/rtl8761bu_fw.bin
rtl_bt/rtl8761bu_config.bin
```

Then verify in **Settings > Devices & services > Bluetooth** that the
adapter is present and, crucially, check that your sensor's readings actually
change or its new packets arrive. Restored historical readings and a
`Running` app badge are not sufficient evidence.

Once this works, reboot **Home Assistant OS/the VM**, not only Core, and
repeat the measurement check. The app starts in the `system` phase before
Core. Do not repeatedly restart it as a scanning method.

If BLE advertisements arrive but one sensor still fails, check that its
integration supports the sensor's broadcast format (for example BTHome
versus PVVX). This repository does not change sensor formats or migrate
entities.

## Refusals and troubleshooting

| Message or symptom | Meaning and next step |
| --- | --- |
| `Untested kernel/module build` | No kernel command has been run. Prefer a native-support OS update or wait for a tested release. Do not remove the gate. |
| `Signed module` / unexpected ELF or table layout | This release cannot safely handle that file. It exits without replacing the stock driver. Do not weaken system protections. |
| `native_support` | The validated quirk already exists; the stock driver was loaded without a module swap. Verify readings, then remove this workaround when no longer needed. |
| Module file missing | The OS may use a compressed, built-in or differently placed module. This release does not support that layout. |
| `rmmod` failed | The stock module was not replaced. Check other users of the module; do not force-remove it. |
| `insmod` failed | The loader attempts to reload the stock module. If Bluetooth remains unavailable, stop the app, disable start-on-boot and reboot the host. |
| Firmware loads but no sensors arrive | Check physical USB passthrough, distance, interference and sensor batteries; verify the sensor integration separately. |

App logs can be reviewed in the app's **Log** tab. When reporting a problem,
share the OS/kernel version, app version, USB **vendor/product ID only** and
a short **redacted** error. Do not upload full diagnostics, backups,
configuration, serial numbers or unredacted Bluetooth scans.

## Remove the workaround

1. Disable the app's **Start on boot**.
2. Stop the app and uninstall it when ready.
3. Reboot **Home Assistant OS/the VM**. Stopping the app alone does not unload
   a driver already in kernel memory; the reboot restores the stock driver.
4. Verify Bluetooth using the official driver. If the OS still lacks the
   USB-ID fix, the original scanning problem will return; use a supported
   OS update or reinstall the tested workaround if appropriate.

The original `/lib/modules/.../btusb.ko` is never overwritten. Uninstalling
the app may remove its own generated copy and status reports, but it does
not remove sensor data or Home Assistant configuration.

## Technical design and privileges

The app receives read-only host module files and **SYS_MODULE** through
Home Assistant's `kernel_modules` setting. SYS_MODULE is powerful: loading
kernel code affects the entire host. Enabled AppArmor/protection mode does
not make a kernel-module loader risk-free.

This app does not request full access, host PID, Docker API, Supervisor API,
Home Assistant API, D-Bus, configuration-folder mounts or inbound ports. It
uses the normal container network but its loader makes no network requests.

The quirk lives in `btusb`'s internal `quirks_table`, not its exported USB
alias table. A generic USB `new_id` binding alone does not supply this
Realtek initialization path. The patcher checks the ELF type, architecture,
non-executable data section, quirk symbol, table terminator, duplicate donor
entries and exact changed-byte set. The loader additionally checks the
hardware-tested kernel and original module hash **before** invoking kmod.

The loader uses `modprobe btusb`, `rmmod btusb`, then `insmod` of the copy.
It does not use `modprobe -r`, which can also remove required dependencies.
If loading the copy fails, it attempts `modprobe btusb` to restore the stock
module. Its background loop only reacts if the module disappears; it does
not periodically reset the Bluetooth radio.

## Technical references

- [Native upstream UB600 fix](https://github.com/torvalds/linux/commit/bc597f0cc44f0b173c50ee986a047219cd559ee9)
- [Linux 6.18 btusb source](https://github.com/torvalds/linux/blob/v6.18/drivers/bluetooth/btusb.c)
- [Linux 6.18.45 btusb source with native support](https://github.com/gregkh/linux/blob/v6.18.45/drivers/bluetooth/btusb.c)
- [Linux USB device-table layout](https://github.com/torvalds/linux/blob/v6.18/include/linux/mod_devicetable.h)
- [Home Assistant app configuration and kernel_modules](https://developers.home-assistant.io/docs/apps/configuration/)
- [Home Assistant app repositories](https://developers.home-assistant.io/docs/apps/repository/)
