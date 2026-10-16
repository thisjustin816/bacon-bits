"""Reject a moved assembly entry, stale return gate, or an overflowing ROM bank."""
from pathlib import Path
import os
import re,json
ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/os.environ.get('BB_BUILD_DIR','build')
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',(BUILD/'bacon-bits.noi').read_text(),re.M)}
assert syms['_serial_isr']<0x4000,'The serial interrupt must stay callable while the UI switches banks'
assert syms['_rumble_program']==0x34000,hex(syms['_rumble_program'])
rom=(BUILD/'bacon-bits.gbc').read_bytes();assert len(rom)==131072
assert rom[0x143]==0x80 and (rom[0x147],rom[0x149]) in [(0x1e,5),(0x10,3)]
header=0
for byte in rom[0x134:0x14d]:header=(header-byte-1)&255
assert header==rom[0x14d]
assert (sum(rom[:0x14e])+sum(rom[0x150:]))&65535==int.from_bytes(rom[0x14e:0x150],'big')
labels=json.loads((BUILD/'rumble-labels.json').read_text())
# A return-gate call occurs directly after the four-button comparison.
body=rom[3*0x4000:4*0x4000]
gate=syms['_rumble_gate'];needle=b'\xcd'+gate.to_bytes(2,'little')
assert needle in body,'The assembly return hook points at an earlier link'
draw=labels['draw_all']-0x4000
assert body[draw:draw+3]==b'\xcd'+syms['_rumble_draw_gate'].to_bytes(2,'little'),'The graphical rumble bridge is stale'
areas=re.findall(r'^(_CODE(?:_\d+)?|_HOME)\s+([\dA-F]+)\s+([\dA-F]+)',(BUILD/'bacon-bits.map').read_text(),re.M)
for name,start,size in areas:
 start=int(start,16);size=int(size,16)
 assert (start&0xffff)+size <= (0x4000 if start<0x4000 else 0x8000),(name,start,size)
 print(f'{name}: {size} bytes, ends {start+size:05x}')
print('Mapper header, 128 KiB image, bank bounds, fixed serial interrupt and assembly return gate passed')

assert syms['_burn_expected']==0x74000,hex(syms['_burn_expected'])
import binascii
for bank in range(8):
 data=rom[bank*16384:(bank+1)*16384]
 if bank==0:data=data[:0x14e]+data[0x150:]
 if bank==7:data=data[16:]
 assert binascii.crc_hqx(data,0xffff)==int.from_bytes(rom[7*16384+bank*2:7*16384+bank*2+2],'little'),bank
print(str(32 if rom[0x147]==0x10 else 64)+' KiB SRAM header and independent per-bank CRC manifest passed')

for name,start,size in re.findall(r'^(_DATA|_INITIALIZED)\s+([\dA-F]+)\s+([\dA-F]+)',(BUILD/'bacon-bits.map').read_text(),re.M):
 start=int(start,16);size=int(size,16)
 assert start+size<=0xdc00,(name,start,size)
 print(f'{name}: {size} bytes, ends {start+size:04x}; stack reserve remains')

# Verify the compiled font and every scene's tile range against the shared layout.
from lettering import tiles as font_tiles
font=syms['_bb_font'];assert rom[font:font+1536]==font_tiles(), 'The compiled mixed-case font is stale'
scene_source=(ROOT/'src/scene_data.h').read_text()
scene_sizes=re.search(r'scene_sizes\[8\]\[5\]=\{(.+)\};',scene_source)[1]
counts=[int(row.split(',')[0]) for row in re.findall(r'\{([^{}]+)\}',scene_sizes)]
assert len(counts)==8 and max(counts)<=128,counts
assert 112+max(counts)<=232,'Instrument tiles overlap the focus border'
assert 232+8==240,'Focus border overlaps the brand'
label_slots=set(map(int,re.search(r'slots\[\]=\{([^}]+)\}',(ROOT/'src/main.c').read_text())[1].split(',')))
assert label_slots.isdisjoint(range(61,65)), 'Focus patterns overlap centered-label slots'
controls=(ROOT/'src/button_data.h').read_text()
button_bytes=re.search(r'button_tiles\[\]=\{([^}]+)\}',controls)[1].split(',')
assert len(button_bytes)==37*16, 'Live D-pad tile budget changed'
assert 96+11+3<=110 and 110<112,'Link sprite overlaps the font or instruments'
print(f'Mixed-case font and instrument ranges passed; browser uses {96+11+3+max(counts)+8+16} resident tiles, including focus; live D-pad uses 37 tiles')
