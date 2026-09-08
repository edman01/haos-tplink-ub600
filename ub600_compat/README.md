# TP-Link UB600 Bluetooth compatibility

Experimental compatibility app for the TP-Link UB600 USB ID `37ad:0600` on
the tested Home Assistant OS 18.2 / amd64 / `6.18.39-haos` module build.

This is a temporary workaround for missing Realtek initialization, not a
universal Bluetooth driver. Prefer an official HAOS update with native
support. Starting the app briefly interrupts **all** USB Bluetooth adapters
using `btusb`.

Read [DOCS.md](DOCS.md) before installing. Keep protection mode enabled.
No Home Assistant token, sensor MAC address, cloud account or app settings
are required.
