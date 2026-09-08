# Security and disclosure

This app can load a host kernel module through SYS_MODULE. It is an
experimental workaround, not a security boundary, and it affects the shared
Bluetooth driver. Read the installation and recovery guide before using it.

The public loader refuses untested kernel/module fingerprints, signed
modules and unsupported table layouts. There is no force option. Do not
disable signature enforcement, AppArmor or protection mode to bypass a
failure. A refusal is preferable to an unvalidated module replacement.

No kernel binaries, firmware, credentials, sensor addresses, network
configuration or raw household diagnostics are distributed here. The app
does not collect telemetry or send data to the maintainer.

For a potential vulnerability, do not disclose credentials or exploit details
in a public issue. If GitHub's **Report a vulnerability** option is available,
use it; otherwise open a minimal issue requesting a private reporting route
without including sensitive details. No response-time guarantee is offered.

Only the latest documented experimental release is considered for fixes.
An official Home Assistant OS kernel with native support is the preferred
long-term solution.
