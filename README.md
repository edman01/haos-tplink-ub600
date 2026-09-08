# TP-Link UB600 compatibility for Home Assistant OS

An **experimental, narrowly scoped workaround** for the TP-Link UB600 USB
Bluetooth adapter **`37ad:0600`** on an older Home Assistant OS kernel that
does not apply the adapter's Realtek firmware-loading quirk.

**Prefer an official Home Assistant OS update with native support.** The
[upstream Linux fix](https://github.com/torvalds/linux/commit/bc597f0cc44f0b173c50ee986a047219cd559ee9)
already exists, and the USB ID is present in
[Linux 6.18.45](https://github.com/gregkh/linux/blob/v6.18.45/drivers/bluetooth/btusb.c).
This project packages a stopgap for the specific older build below. It is not
an official Home Assistant or TP-Link product, a new universal Bluetooth
driver, or a way to enable all advertised Bluetooth 6.0 features.

[Installation and recovery](ub600_compat/DOCS.md) |
[Security and limitations](SECURITY.md)

## What it fixes

On the affected build, the adapter can appear as a USB device or `hci0`, but
`btusb` does not select its Realtek initialization path. The existing
`rtl_bt/rtl8761bu_fw.bin` firmware is consequently not loaded and scanning
does not work.

The app creates a separate copy of the installed, unsigned `btusb.ko`. It
reuses one of two identical quirk-table entries to insert `37ad:0600` with
`BTUSB_REALTEK | BTUSB_WIDEBAND_SPEECH`. Exactly **four USB ID bytes** change;
the other duplicate remains and the existing supported-device set is
preserved. Executable code and the original OS file are not modified.

It does **not** install Windows drivers, update sensor firmware, configure
individual sensors, or replace the BTHome/PVVX/Ruuvi integrations.

## Compatibility: intentionally limited

| Item | Validated configuration |
| --- | --- |
| Adapter | TP-Link UB600, USB ID `37ad:0600`, Realtek RTL8761BU/BUV family |
| Installation | Home Assistant OS 18.2, amd64, in a VirtualBox VM |
| Kernel | `6.18.39-haos` |
| Home Assistant Core during hardware testing | `2026.9.1` |
| Stock module SHA-256 | `1396033d5ef1097147214a6fe127c298455a18137fd6d5bb8dbc8bc869b17d20` |
| Patched-copy SHA-256 | `ced2a0887a85ce2659709ba84ec4e0b9b2a42a3476fe96fb4cf4d2b19b943ac9` |

The public loader **refuses to replace a module from any other kernel or
module build**. There is no force option. A validated native-support entry
uses the stock driver without unloading it. Signed, compressed, stripped or
unexpected module layouts are not supported by this release.

Raspberry Pi/ARM, other hypervisors, bare-metal installs, UB500 variants and
other USB IDs have **not** been validated. A matching product name alone is
not sufficient. This app requires Home Assistant OS with the app store; it
is not an installation method for Home Assistant Container.

## Install

1. Read the [full instructions and recovery procedure](ub600_compat/DOCS.md).
   Have a current backup and local console access before starting.
2. In Home Assistant, open **Settings > Apps** (called **Add-ons** in older
   versions), open the app store, then **Repositories** from its menu.
3. Add this repository URL:

   ```text
   https://github.com/edman01/haos-tplink-ub600
   ```

4. Install **TP-Link UB600 Bluetooth compatibility**, keep protection mode
   enabled, and enable start on boot. Start it during a maintenance window.
5. Check its log and then verify **new sensor measurements**, not merely a
   listed Bluetooth adapter. Follow the full guide for the reboot test.

The image is built locally by Supervisor. Its deliberately pinned Home
Assistant runtime base is large; allow time and free disk space for the first
download. It starts only the loader, not a second Home Assistant instance.

**Starting this app reloads the shared `btusb` kernel module. Every USB
Bluetooth adapter using that module can briefly disconnect.** Do not install
it on a healthy system or assume a running app proves that scanning works.

## Verification and status

The local repair mechanism was hardware-tested on **one** configuration:
Realtek firmware loaded, fresh BLE broadcasts from nine configured sensors
were received, and operation survived full VM reboots. Some of those sensors
also needed separate protocol configuration; those changes are **not** part
of this repository.

The public package adds a strict known-build gate and mocked loader tests.
Those publication changes are tested offline; they have not been installed
on a second household's server. CI is not hardware certification.

Run the offline tests with Python 3.12 or later:

```sh
python -m unittest discover -s tests -v
python tools/check_publication.py
```

The test suite uses synthetic module data and mocked kernel commands. No
actual kernel module is loaded by these tests.

## Privacy and licensing

Only the generic app, synthetic tests and documentation are published. No
home-network addresses, adapter serial numbers, sensor MACs, personal names,
credentials, Home Assistant configuration, database, backups or raw logs are
included. The repository is associated with its public GitHub account; it
does not provide anonymity from that account.

Original scripts and documentation are [MIT licensed](LICENSE). This
repository does not redistribute Linux kernel modules or firmware. Linux,
firmware and the upstream container retain their respective licenses.

Credit for the native USB-ID fix belongs to the upstream Linux contributors;
this repository's contribution is a narrowly validated HAOS workaround and
its packaging. See [technical references](ub600_compat/DOCS.md#technical-references).
