"""Add UB600's Realtek quirk to an unsigned HAOS btusb module copy.

No executable code changes. Reuse the duplicate 13d3:3549 quirk entry,
preserving the first identical entry and every existing supported device.
Refuse unfamiliar ELF layouts, signed modules, and unexpected table data.
The original system module is never modified.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def patch_module(raw):
    if not 64 <= len(raw) <= 64 * 1024 * 1024:
        raise ValueError('Unexpected module size')
    if raw[:7] != b'\x7fELF\x02\x01\x01':
        raise ValueError('Only ELF64 little-endian modules are supported')
    if struct.unpack_from('<HH', raw, 16) != (1, 62):
        raise ValueError('Expected x86-64 relocatable kernel module')
    if b'~Module signature appended~' in raw:
        raise ValueError('Signed module: refusing to invalidate its signature')
    shoff = struct.unpack_from('<Q', raw, 40)[0]
    shentsize, shnum, shstrndx = struct.unpack_from('<HHH', raw, 58)
    if shentsize != 64 or not 1 < shnum < 4096:
        raise ValueError('Unexpected section table')
    if shoff < 64 or shoff + shnum * 64 > len(raw) or not 0 < shstrndx < shnum:
        raise ValueError('Section table is out of bounds')
    sections = [struct.unpack_from('<IIQQQQIIQQ', raw, shoff + i * 64)
                for i in range(shnum)]

    def section_data(index):
        if not 0 <= index < len(sections):
            raise ValueError('Invalid section index')
        section = sections[index]
        if section[4] + section[5] > len(raw):
            raise ValueError('Section data is out of bounds')
        return raw[section[4]:section[4] + section[5]]

    def string_at(table, offset):
        if not 0 <= offset < len(table) or b'\x00' not in table[offset:]:
            raise ValueError('Invalid string-table offset')
        return table[offset:].split(b'\x00', 1)[0]

    names = section_data(shstrndx)
    symbols = []
    for section_index, section in enumerate(sections):
        if section[1] != 2:
            continue
        strings = section_data(section[6])
        if section[9] != 24 or section[5] % 24:
            raise ValueError('Unexpected symbol size')
        section_data(section_index)
        for offset in range(section[4], section[4] + section[5], 24):
            symbol = struct.unpack_from('<IBBHQQ', raw, offset)
            name = string_at(strings, symbol[0])
            if name == b'quirks_table':
                symbols.append(symbol)
    if len(symbols) != 1:
        raise ValueError('Expected exactly one quirks_table symbol')
    symbol = symbols[0]
    if not 0 < symbol[3] < len(sections) or symbol[1] & 15 != 1:
        raise ValueError('Quirk table is not a defined data object')
    section = sections[symbol[3]]
    section_data(symbol[3])
    section_name = string_at(names, section[0]).decode('ascii')
    if not section_name.startswith('.rodata') or section[2] & 4:
        raise ValueError('Quirk table is not non-executable read-only data')
    start, size = section[4] + symbol[4], symbol[5]
    if size % 32 or size < 320 or start + size > section[4] + section[5]:
        raise ValueError('Unexpected USB table layout')
    table = [raw[pos:pos + 32] for pos in range(start, start + size, 32)]
    if table[-1] != bytes(32):
        raise ValueError('Quirk table lacks its terminator')
    target = struct.pack('<HHH18xQ', 3, 0x37ad, 0x0600, 0x210000)
    if target in table:
        return raw, {'status': 'native_support', 'sha256': sha256(raw)}
    if any(struct.unpack_from('<HH', entry, 2) == (0x37ad, 0x0600) for entry in table):
        raise ValueError('UB600 already has an unrecognized quirk entry')
    donor = struct.pack('<HHH18xQ', 3, 0x13d3, 0x3549, 0x210000)
    duplicates = [i for i, entry in enumerate(table) if entry == donor]
    if len(duplicates) != 2:
        raise ValueError('Expected exactly two identical 13d3:3549 entries')
    index = duplicates[-1]
    offset = start + index * 32
    result = bytearray(raw)
    result[offset:offset + 32] = target
    revised = list(table)
    revised[index] = target
    if set(revised) != set(table) | {target}:
        raise ValueError('Existing device support would change')
    diffs = [i for i, (old, new) in enumerate(zip(raw, result)) if old != new]
    if diffs != list(range(offset + 2, offset + 6)):
        raise ValueError('Unexpected changes outside VID/PID')
    info = {
        'status': 'patched_copy', 'section': section_name,
        'table_offset': start, 'table_size': size, 'entry_index': index,
        'duplicate_preserved_at_index': duplicates[0],
        'device': '37ad:0600', 'driver_flags': '0x210000',
        'changed_offsets': diffs, 'original_sha256': sha256(raw),
        'patched_sha256': sha256(result),
    }
    return bytes(result), info


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.destination.resolve():
        raise SystemExit('Source and destination must differ')
    patched, report = patch_module(args.source.read_bytes())
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    args.destination.write_bytes(patched)
    args.destination.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
