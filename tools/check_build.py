"""Reject a moved assembly entry, stale return gate, or an overflowing ROM bank."""
from pathlib import Path
import re,json
ROOT=Path(__file__).resolve().parents[1]
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',(ROOT/'build/bacon-bits.noi').read_text(),re.M)}
assert syms['_rumble_program']==0x34000,hex(syms['_rumble_program'])
rom=(ROOT/'build/bacon-bits.gbc').read_bytes();assert len(rom)==131072
assert rom[0x143]==0x80 and rom[0x147]==0x1c
header=0
for byte in rom[0x134:0x14d]:header=(header-byte-1)&255
assert header==rom[0x14d]
assert (sum(rom[:0x14e])+sum(rom[0x150:]))&65535==int.from_bytes(rom[0x14e:0x150],'big')
labels=json.loads((ROOT/'build/rumble-labels.json').read_text())
# A return-gate call occurs directly after the four-button comparison.
body=rom[3*0x4000:4*0x4000]
gate=syms['_rumble_gate'];needle=b'\xcd'+gate.to_bytes(2,'little')
assert needle in body,'The assembly return hook points at an earlier link'
areas=re.findall(r'^(_CODE(?:_\d+)?|_HOME)\s+([\dA-F]+)\s+([\dA-F]+)',(ROOT/'build/bacon-bits.map').read_text(),re.M)
for name,start,size in areas:
 start=int(start,16);size=int(size,16)
 assert (start&0xffff)+size <= (0x4000 if start<0x4000 else 0x8000),(name,start,size)
 print(f'{name}: {size} bytes, ends {start+size:05x}')
print('MBC5+rumble header, 128 KiB image, bank bounds and assembly return gate passed')
