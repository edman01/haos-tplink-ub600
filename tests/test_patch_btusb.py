"""Safety checks without kernel loading or hardware access."""
import struct
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ub600_compat'))

from patch_btusb import patch_module


def fixture():
    donor = struct.pack('<HHH18xQ', 3, 0x13d3, 0x3549, 0x210000)
    target = struct.pack('<HHH18xQ', 3, 0x37ad, 0x0600, 0x210000)
    table = [struct.pack('<HHH18xQ', 3, 0x7777, i, 1) for i in range(10)]
    table[2] = table[8] = donor
    table.append(bytes(32))
    raw = bytearray(2048)
    raw[:7] = b'\x7fELF\x02\x01\x01'
    struct.pack_into('<HH', raw, 16, 1, 62)
    struct.pack_into('<Q', raw, 40, 64)
    struct.pack_into('<HHH', raw, 58, 64, 5, 1)
    names = b'\x00.shstrtab\x00.rodata\x00.symtab\x00.strtab\x00'
    raw[384:384+len(names)] = names
    strings = b'\x00quirks_table\x00'
    raw[1500:1500+len(strings)] = strings
    raw[512:512+len(table)*32] = b''.join(table)
    struct.pack_into('<IBBHQQ', raw, 1400, 1, 1, 0, 2, 0, len(table)*32)
    for index, fields in enumerate([
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        (1, 3, 0, 0, 384, len(names), 0, 0, 1, 0),
        (11, 1, 2, 0, 512, len(table)*32, 0, 0, 8, 0),
        (19, 2, 0, 0, 1400, 24, 4, 0, 8, 24),
        (27, 3, 0, 0, 1500, len(strings), 0, 0, 1, 0),
    ]):
        struct.pack_into('<IIQQQQIIQQ', raw, 64+index*64, *fields)
    return bytes(raw), donor, target


class PatchTests(unittest.TestCase):
    def test_only_four_bytes_and_preserved_donor(self):
        raw, donor, target = fixture()
        patched, report = patch_module(raw)
        self.assertEqual(len(patched), len(raw))
        self.assertEqual(sum(a != b for a, b in zip(raw, patched)), 4)
        self.assertEqual(patched.count(donor), 1)
        self.assertEqual(patched.count(target), 1)
        self.assertEqual(report['duplicate_preserved_at_index'], 2)

    def test_idempotent(self):
        patched, _ = patch_module(fixture()[0])
        self.assertEqual(patch_module(patched), (patched, {
            'status': 'native_support', 'sha256': __import__('hashlib').sha256(patched).hexdigest()}))

    def test_signed_refused(self):
        with self.assertRaises(ValueError):
            patch_module(fixture()[0] + b'~Module signature appended~\n')

    def test_missing_duplicate_refused(self):
        raw, donor, _ = fixture()
        raw = raw.replace(donor, struct.pack('<HHH18xQ', 3, 0x7777, 13, 1), 1)
        with self.assertRaises(ValueError):
            patch_module(raw)

    def test_missing_terminator_refused(self):
        raw = bytearray(fixture()[0])
        raw[512+10*32:512+11*32] = raw[512:544]
        with self.assertRaises(ValueError):
            patch_module(raw)

    def test_wrong_arch_and_non_elf_refused(self):
        for raw in (b'Not ELF', fixture()[0][:18] + b'\xb7\x00' + fixture()[0][20:]):
            with self.assertRaises(ValueError):
                patch_module(raw)

    def test_truncated_elf_refused(self):
        with self.assertRaises(ValueError):
            patch_module(fixture()[0][:63])

    def test_out_of_bounds_section_table_refused(self):
        raw = bytearray(fixture()[0])
        struct.pack_into('<Q', raw, 40, len(raw))
        with self.assertRaises(ValueError):
            patch_module(raw)

    def test_executable_quirk_section_refused(self):
        raw = bytearray(fixture()[0])
        struct.pack_into('<Q', raw, 64 + 2 * 64 + 8, 6)
        with self.assertRaises(ValueError):
            patch_module(raw)

    def test_conflicting_target_flags_refused(self):
        raw, donor, _ = fixture()
        raw = raw.replace(donor, struct.pack('<HHH18xQ', 3, 0x37ad, 0x0600, 1), 1)
        with self.assertRaisesRegex(ValueError, 'unrecognized'):
            patch_module(raw)

    def test_donor_with_different_flags_refused(self):
        raw, donor, _ = fixture()
        raw = raw.replace(donor, struct.pack('<HHH18xQ', 3, 0x13d3, 0x3549, 1), 1)
        with self.assertRaises(ValueError):
            patch_module(raw)


if __name__ == '__main__':
    unittest.main()
