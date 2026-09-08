"""Exercise the public safety gate and load/recovery order without kmod."""
from contextlib import ExitStack
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ub600_compat'))

import run
from compatibility import TESTED_KERNEL, TESTED_SOURCE_SHA256, require_tested_build
from patch_btusb import sha256


class CompatibilityTests(unittest.TestCase):
    def test_exact_build_accepted(self):
        require_tested_build(TESTED_KERNEL, TESTED_SOURCE_SHA256)

    def test_different_kernel_refused(self):
        with self.assertRaises(ValueError):
            require_tested_build('untested-kernel', TESTED_SOURCE_SHA256)

    def test_different_module_refused(self):
        with self.assertRaises(ValueError):
            require_tested_build(TESTED_KERNEL, '0' * 64)

    def test_empty_identity_refused(self):
        with self.assertRaises(ValueError):
            require_tested_build('', '')


class LoaderTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.directory = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.stack.enter_context(patch.object(run, 'DATA', Path(self.directory)))
        self.present = self.stack.enter_context(patch.object(run, 'adapter_present', return_value=True))
        self.kernel = self.stack.enter_context(patch.object(run, 'kernel_release', return_value=TESTED_KERNEL))
        self.reader = self.stack.enter_context(patch.object(run, 'read_original', return_value=b'synthetic stock module'))
        self.patcher = self.stack.enter_context(patch.object(run, 'patch_module', return_value=(b'synthetic patched module', {'status': 'patched_copy'})))
        self.command = self.stack.enter_context(patch.object(run, 'command', return_value=''))
        self.loaded = self.stack.enter_context(patch.object(run, 'module_loaded', return_value=True))
        self.status = self.stack.enter_context(patch.object(run, 'write_status'))
        self.stack.enter_context(patch.object(run, 'log'))

    def test_missing_adapter_never_reads_or_changes_driver(self):
        self.present.return_value = False
        self.assertFalse(run.install())
        self.reader.assert_not_called()
        self.command.assert_not_called()
        self.assertEqual(list(Path(self.directory).iterdir()), [])
        self.assertEqual(self.status.call_args.kwargs['state'], 'waiting_for_adapter')

    def test_disconnected_during_preparation_never_runs_kmod(self):
        self.present.side_effect = [True, False]
        with patch.object(run, 'require_tested_build'):
            self.assertFalse(run.install())
        self.command.assert_not_called()

    def test_disconnected_after_modprobe_never_unloads_driver(self):
        self.present.side_effect = [True, True, False]
        with patch.object(run, 'require_tested_build'):
            self.assertFalse(run.install())
        self.command.assert_called_once_with('/sbin/modprobe', 'btusb')

    def test_untested_source_does_not_run_any_kernel_command_or_write_copy(self):
        with self.assertRaisesRegex(ValueError, 'Untested'):
            run.install()
        self.command.assert_not_called()
        self.assertEqual(list(Path(self.directory).iterdir()), [])

    def test_invalid_kernel_path_refused_before_read(self):
        self.kernel.return_value = '../invalid'
        with self.assertRaises(ValueError):
            run.install()
        self.reader.assert_not_called()
        self.command.assert_not_called()

    def test_parser_refusal_does_not_run_any_kernel_command(self):
        self.patcher.side_effect = ValueError('Signed module')
        with self.assertRaisesRegex(ValueError, 'Signed'):
            run.install()
        self.command.assert_not_called()

    def test_missing_source_does_not_run_any_kernel_command(self):
        self.reader.side_effect = FileNotFoundError('No supported module')
        with self.assertRaises(FileNotFoundError):
            run.install()
        self.command.assert_not_called()

    def test_native_support_never_unloads(self):
        self.patcher.return_value = (b'synthetic stock module', {'status': 'native_support'})
        run.install()
        self.command.assert_called_once_with('/sbin/modprobe', 'btusb')
        self.assertEqual(self.status.call_args.kwargs['state'], 'native_support')
        self.assertEqual(list(Path(self.directory).iterdir()), [])

    def test_accepted_build_uses_dependency_preserving_order(self):
        with patch.object(run, 'require_tested_build') as gate:
            run.install()
        gate.assert_called_once_with(TESTED_KERNEL, sha256(b'synthetic stock module'))
        commands = [item.args for item in self.command.call_args_list]
        self.assertEqual(commands[:2], [('/sbin/modprobe', 'btusb'), ('/sbin/rmmod', 'btusb')])
        self.assertEqual(commands[2][0], '/sbin/insmod')
        self.assertEqual(Path(commands[2][1]).read_bytes(), b'synthetic patched module')
        self.assertEqual(self.status.call_args.kwargs['state'], 'compatibility_driver_loaded')

    def test_insmod_failure_attempts_stock_recovery(self):
        def fake_command(*args):
            if args[0] == '/sbin/insmod':
                raise RuntimeError('Simulated insmod failure')
            return ''

        self.command.side_effect = fake_command
        with patch.object(run, 'require_tested_build'):
            with self.assertRaisesRegex(RuntimeError, 'Simulated insmod'):
                run.install()
        self.assertEqual(self.command.call_args_list[-1].args, ('/sbin/modprobe', 'btusb'))
        self.status.assert_not_called()

    def test_rmmod_failure_does_not_attempt_insmod(self):
        def fake_command(*args):
            if args[0] == '/sbin/rmmod':
                raise RuntimeError('Module is in use')
            return ''

        self.command.side_effect = fake_command
        with patch.object(run, 'require_tested_build'):
            with self.assertRaisesRegex(RuntimeError, 'in use'):
                run.install()
        self.assertFalse(any(call.args[0] == '/sbin/insmod' for call in self.command.call_args_list))


class AdapterPresenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.override = patch.object(run, 'USB_DEVICES', self.root)
        self.override.start()
        self.addCleanup(self.override.stop)

    def device(self, name, vendor, product):
        device = self.root / name
        device.mkdir()
        (device / 'idVendor').write_text(vendor, encoding='ascii')
        (device / 'idProduct').write_text(product, encoding='ascii')
        return device

    def test_exact_device_detected_without_serial(self):
        self.device('test-device', '37ad\n', '0600\n')
        self.assertTrue(run.adapter_present())

    def test_case_and_whitespace_accepted(self):
        self.device('test-device', '37AD\n', ' 0600\n')
        self.assertTrue(run.adapter_present())

    def test_other_vendor_or_product_refused(self):
        self.device('other-product', '37ad', '9999')
        self.device('other-vendor', 'ffff', '0600')
        self.assertFalse(run.adapter_present())

    def test_empty_bus_refused(self):
        self.assertFalse(run.adapter_present())

    def test_missing_bus_refused(self):
        with patch.object(run, 'USB_DEVICES', self.root / 'missing'):
            self.assertFalse(run.adapter_present())

    def test_unreadable_bus_refused(self):
        with patch.object(Path, 'iterdir', side_effect=PermissionError):
            self.assertFalse(run.adapter_present())

    def test_incomplete_entry_skipped(self):
        (self.root / 'interface').mkdir()
        self.device('test-device', '37ad', '0600')
        self.assertTrue(run.adapter_present())

    def test_unreadable_device_refused(self):
        self.device('test-device', '37ad', '0600')
        with patch.object(Path, 'read_text', side_effect=PermissionError):
            self.assertFalse(run.adapter_present())

    def test_invalid_device_text_refused(self):
        device = self.device('test-device', '37ad', '0600')
        (device / 'idVendor').write_bytes(bytes([255]))
        self.assertFalse(run.adapter_present())


class MonitorTests(unittest.TestCase):
    def test_late_adapter_retried_even_when_stock_module_is_loaded(self):
        with patch.object(run, 'STOP') as stop, patch.object(run, 'install', side_effect=[False, True]) as install, patch.object(run, 'module_loaded', return_value=True):
            stop.wait.side_effect = [False, False, True]
            run.monitor()
        self.assertEqual(install.call_count, 2)

    def test_success_does_not_periodically_reload(self):
        with patch.object(run, 'STOP') as stop, patch.object(run, 'install', return_value=True) as install, patch.object(run, 'module_loaded', return_value=True):
            stop.wait.side_effect = [False, False, True]
            run.monitor()
        install.assert_called_once_with()

    def test_unloaded_module_is_rechecked(self):
        with patch.object(run, 'STOP') as stop, patch.object(run, 'install', return_value=True) as install, patch.object(run, 'module_loaded', return_value=False):
            stop.wait.side_effect = [False, True]
            run.monitor()
        self.assertEqual(install.call_count, 2)


if __name__ == '__main__':
    unittest.main()
