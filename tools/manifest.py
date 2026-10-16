"""Embed CRC references, excluding this table and the global header checksum."""
from pathlib import Path
import os
import binascii
ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/os.environ.get('BB_BUILD_DIR','build')
rom=(BUILD/'bacon-bits.gbc').read_bytes();values=[]
for bank in range(8):
 data=bytearray(rom[bank*16384:(bank+1)*16384])
 if bank==0:data=data[:0x14e]+data[0x150:]
 if bank==7:data=data[16:]
 values.append(binascii.crc_hqx(data,0xffff))
(BUILD/'manifest.h').write_text('#define BURN_CRCS {'+','.join(str(x) for x in values)+'}\n')
print('ROM bank CRCs:',','.join(f'{x:04X}' for x in values))
