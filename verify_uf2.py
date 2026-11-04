import hashlib
import json
import struct
import sys
from pathlib import Path

def inspect(path):
    data = Path(path).read_bytes()
    assert data and len(data) % 512 == 0, 'Invalid UF2 file length'
    blocks = len(data) // 512
    payload = {}
    addresses = []
    for index in range(blocks):
        block = data[index * 512:(index + 1) * 512]
        magic0, magic1, flags, addr, size, number, total, family = struct.unpack_from('<8I', block)
        assert magic0 == 0x0A324655 and magic1 == 0x9E5D5157
        assert struct.unpack_from('<I', block, 508)[0] == 0x0AB16F30
        assert flags == 0x2000 and family == 0xADA52840, 'Wrong UF2 family or flags'
        assert number == index and total == blocks, 'Invalid block numbering'
        assert size == 256 and addr % 256 == 0
        assert 0x26000 <= addr and addr + size <= 0xED000, 'Outside application flash region'
        assert addr not in payload, 'Duplicate target address'
        payload[addr] = block[32:32 + size]
        addresses.append(addr)
    assert addresses == list(range(min(addresses), max(addresses) + 256, 256)), 'Discontinuous image'
    image = b''.join(payload[a] for a in addresses)
    stack, reset = struct.unpack_from('<II', image)
    assert 0x20000000 <= stack <= 0x20040000 and stack % 8 == 0, 'Invalid initial stack pointer'
    assert reset & 1 and min(addresses) <= reset - 1 < max(addresses) + 256, 'Invalid reset vector'
    return {
        'file': Path(path).name, 'bytes': len(data), 'blocks': blocks,
        'family': '0xADA52840', 'flash_start': hex(min(addresses)),
        'flash_end_exclusive': hex(max(addresses) + 256),
        'initial_stack': hex(stack), 'reset_vector': hex(reset),
        'sha256': hashlib.sha256(data).hexdigest(),
        'has_diagnostic_marker': b'QMC5883P diagnostic v1' in image,
        'has_xyz_log': b'QMC5883P raw: X=%d Y=%d Z=%d' in image,
        'passed': True,
    }

if __name__ == '__main__':
    print(json.dumps([inspect(p) for p in sys.argv[1:]], indent=2))
