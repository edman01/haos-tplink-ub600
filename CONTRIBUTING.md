# Contributing

Keep this project narrowly focused on TP-Link UB600 USB ID `37ad:0600`.
Do not add household-specific sensor setup, MAC addresses, credentials,
network endpoints, backups, screenshots or actual kernel-module fixtures.

Run these commands from the repository root with Python 3.12 or later:

```sh
python -m unittest discover -s tests -v
python tools/check_publication.py
```

Tests must never load/unload a real kernel module. Use synthetic ELF data
and mocked commands. Do not confuse unit/CI success with hardware testing.

Changes to compatibility support need documented hardware evidence:
architecture, OS/kernel version, original module hash, exact changed bytes,
firmware initialization, fresh BLE advertisements and a host reboot test.
Do not add a hash to the accepted list based only on parser success. Prefer
the upstream kernel fix instead of expanding this workaround indefinitely.

Publication checklist:

- Keep author/committer metadata free of private names and private email;
  use an appropriate GitHub noreply address when committing.
- Review `git diff --cached` and `git ls-files`, not the surrounding workspace.
- Run the content/privacy check and all tests.
- Publish source only, with the tested-environment and kernel-privilege warnings.
- Mark experimental GitHub releases as pre-releases.
- Do not claim a public app-store install was verified unless it actually was.
