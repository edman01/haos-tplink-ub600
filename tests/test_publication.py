"""Check the publication scanner using synthetic, non-personal examples."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from check_publication import ALLOWED_FILES, inspect_text


class PublicationTests(unittest.TestCase):
    def test_usb_id_is_not_a_personal_mac(self):
        self.assertEqual(inspect_text('TP-Link UB600 USB ID 37ad:0600'), [])

    def test_synthetic_mac_is_flagged(self):
        address = ':'.join(['02', '00', '00', '00', '00', '01'])
        self.assertIn('device MAC address', inspect_text(address))

    def test_private_network_is_flagged(self):
        address = '.'.join(['192', '168', '0', '1'])
        self.assertIn('private IPv4 address', inspect_text(address))

    def test_personal_email_is_flagged(self):
        address = 'example' + '@' + 'example.org'
        self.assertIn('external email address', inspect_text(address))

    def test_synthetic_credential_is_flagged(self):
        token = 'gh' + 'p_' + 'x' * 30
        self.assertIn('GitHub credential', inspect_text(token))

    def test_no_binary_or_backup_in_allowlist(self):
        for name in ALLOWED_FILES:
            self.assertFalse(name.endswith(('.ko', '.zip', '.png', '.db', '.sqlite')))
            self.assertNotIn('backup', name)


if __name__ == '__main__':
    unittest.main()
