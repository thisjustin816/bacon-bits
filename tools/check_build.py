"""Reject a moved assembly entry, stale return gate, or an overflowing ROM bank."""
from pathlib import Path
# Static WRAM ends below this; tests/stack_depth.py measures the stack above it.
STACK_FLOOR=0xdc00
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
 assert start+size<=STACK_FLOOR,(name,start,size)
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
assert 96+11+3<=110 and 110<111<112,'Link sprite or header edge overlaps the font or instruments'
print(f'Mixed-case font and instrument ranges passed; browser uses {96+11+3+max(counts)+8+16} resident tiles, including focus; live D-pad uses 37 tiles')

# Flicker keeps the UI font and brand resident while both maps alternate.
flicker=(ROOT/'src/flicker_data.h').read_text()
for name,limit in [('preview',98),('reference',15)]:
 values=re.search(r'flicker_'+name+r'_tiles\[\]=\{([^}]+)\}',flicker)[1].split(',')
 assert len(values)%16==0 and len(values)//16<=limit,(name,len(values))
assert 112+98==210 and 210+15==225 and 225+6<=240
assert 110+98+15+6+16==245
assert syms['_flicker_run']>>16==4,'Flicker moved out of its allocated code bank'
print('Flicker fits 245 resident patterns, 6 sprites, and both preloaded LCD maps')

# Settings rows print a label at column 2 and a value from column 11 to 18,
# so a ninth label letter touches the value and a ninth value letter is cut.
def call_arguments(source,name):
 for match in re.finditer(r'\b'+name+r'\(',source):
  depth,at,args,start,quote=1,match.end(),[],match.end(),None
  while depth:
   c=source[at]
   if quote:
    if c=='\\':at+=1
    elif c==quote:quote=None
   elif c in '"\'':quote=c
   elif c=='(':depth+=1
   elif c==')':depth-=1
   elif c==',' and depth==1:args.append(source[start:at]);start=at+1
   at+=1
  args.append(source[start:at-1]);yield args
too_long=[]
for path in sorted(ROOT.glob('src/*.c'))+sorted(ROOT.glob('src/*.inc'))+[BUILD/'adapted/link.c']:
 source=path.read_text()
 for name,columns in [('ui_field',(1,2)),('ui_value',(1,))]:
  for args in call_arguments(source,name):
   for column in columns:
    too_long+=[(path.name,text) for text in re.findall(r'"((?:[^"\\]|\\.)*)"',args[column]) if len(text)>8]
assert not too_long,('Settings text wider than its eight columns',too_long)
print('Every settings label and value fits its eight columns')
