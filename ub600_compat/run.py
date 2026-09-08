"""Install a narrowly validated, ephemeral btusb quirk at each HAOS boot."""
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import threading
import time

from patch_btusb import patch_module, sha256
from compatibility import require_tested_build

STOP = threading.Event()
DATA = Path('/data')


def kernel_release():
    return os.uname().release


def read_original(kernel):
    return (Path('/lib/modules') / kernel / 'kernel/drivers/bluetooth/btusb.ko').read_bytes()


def module_loaded():
    return Path('/sys/module/btusb').is_dir()


def log(message):
    print(time.strftime('%Y-%m-%dT%H:%M:%S%z'), message, flush=True)


def command(*args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=25)
    if result.returncode:
        raise RuntimeError(f'{args[0]} failed: {result.stderr.strip()} {result.stdout.strip()}')
    return result.stdout.strip()


def write_status(**values):
    values['time'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
    temporary = DATA / 'status.json.tmp'
    temporary.write_text(json.dumps(values, indent=2) + '\n')
    temporary.replace(DATA / 'status.json')


def install():
    kernel = kernel_release()
    if not re.fullmatch(r'[a-zA-Z0-9._-]+', kernel):
        raise ValueError('Unexpected kernel release')
    original = read_original(kernel)
    patched, report = patch_module(original)
    log(json.dumps(report))
    if report['status'] == 'native_support':
        command('/sbin/modprobe', 'btusb')
        write_status(state='native_support', kernel=kernel, original_sha256=sha256(original))
        return
    # The public release is deliberately narrower than the ELF parser: only
    # the hardware-tested stock module may be replaced. This runs before kmod.
    require_tested_build(kernel, sha256(original))
    destination = DATA / f'btusb-ub600-{kernel}.ko'
    destination.write_bytes(patched)
    os.chmod(destination, 0o600)
    (DATA / f'btusb-ub600-{kernel}.json').write_text(json.dumps(report, indent=2) + '\n')
    # Load the stock module first if necessary, so kmod resolves its dependencies.
    # Use rmmod, not modprobe -r: the latter also removes those dependencies.
    command('/sbin/modprobe', 'btusb')
    command('/sbin/rmmod', 'btusb')
    try:
        command('/sbin/insmod', str(destination))
    except Exception:
        command('/sbin/modprobe', 'btusb')
        raise
    if not module_loaded():
        raise RuntimeError('btusb did not register after loading')
    write_status(state='compatibility_driver_loaded', kernel=kernel,
                 device='37ad:0600', original_sha256=sha256(original),
                 patched_sha256=sha256(patched), changed_bytes=4)
    log('UB600 compatibility driver loaded; stock module unchanged. USB reconnects use this driver.')


def main():
    import fcntl  # Linux-only; tests can import the loader without this module.

    DATA.mkdir(exist_ok=True)
    with (DATA / 'loader.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        install()
        # Keep an app-visible running state. The kernel handles discovery and
        # firmware reload after USB reconnect; no periodic radio resets.
        while not STOP.wait(30):
            if not module_loaded():
                log('Bluetooth USB module was unloaded; restoring compatibility driver.')
                install()


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: STOP.set())
    signal.signal(signal.SIGINT, lambda *_: STOP.set())
    try:
        main()
    except Exception as error:
        log(f'ERROR: {error}')
        write_status(state='error', error=str(error))
        raise
