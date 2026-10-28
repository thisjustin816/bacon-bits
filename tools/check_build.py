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
# The tile layout comes from src/bb.h and the code that loads each range, so a
# moved base or a longer range is judged by its real values.
ui={n:int(v,0) for n,v in re.findall(r'^#define (UI_\w+) (\d+|0x[\da-fA-F]+)u?$',(ROOT/'src/bb.h').read_text(),re.M)}
main_source=(ROOT/'src/main.c').read_text();art=(ROOT/'src/art.h').read_text()
def art_tiles(name):return len(re.findall(r'0x[\da-fA-F]{2}',re.search(name+r'\[\] = \{([^}]+)\}',art)[1]))//16
chrome=int(re.search(r'set_bkg_data\(UI_CHROME,(\d+),bb_chrome\)',main_source)[1]);probes=int(re.search(r'set_bkg_data\(UI_PASS,(\d+),bb_probes\)',main_source)[1])
assert art_tiles('bb_font')==ui['UI_FONT_COUNT'] and art_tiles('bb_chrome')==chrome and art_tiles('bb_probes')==probes,(art_tiles('bb_font'),art_tiles('bb_chrome'),art_tiles('bb_probes'))
assert ui['UI_FONT_COUNT']<=ui['UI_CHROME'] and ui['UI_CHROME']+chrome<=ui['UI_PASS'],'Chrome overlaps the font or the probe marks'
assert ui['UI_PASS']+probes<=ui['UI_LINK_BALL']<ui['UI_ART'],'Link sprite overlaps the font or instruments'
assert len(counts)==8 and max(counts)<=128,counts
assert ui['UI_ART']+max(counts)<=ui['UI_FOCUS'],'Instrument tiles overlap the focus border'
focus_slots=eval(re.search(r'^ slots=(.+)$',(ROOT/'tools/controls_art.py').read_text(),re.M)[1],{'range':range,'list':list})
assert focus_slots==list(range(ui['UI_FOCUS'],ui['UI_FOCUS']+8))+list(range(ui['UI_FOCUS_EXTRA'],ui['UI_FOCUS_EXTRA']+4)),('Focus art slots differ from src/bb.h',focus_slots)
assert max(focus_slots)<256,'Focus border runs past the tile table'
label_slots=set(map(int,re.search(r'slots\[\]=\{([^}]+)\}',main_source)[1].split(',')))
assert label_slots.isdisjoint(focus_slots), 'Focus patterns overlap centered-label slots'
assert max(label_slots)<ui['UI_FONT_COUNT'],'Centered-label slots run past the font'
controls=(ROOT/'src/button_data.h').read_text()
button_bytes=re.search(r'button_tiles\[\]=\{([^}]+)\}',controls)[1].split(',')
assert len(button_bytes)==37*16, 'Live D-pad tile budget changed'
print(f'Mixed-case font and instrument ranges passed; browser uses {ui["UI_PASS"]+probes+max(counts)+8} resident tiles, including focus; live D-pad uses 37 tiles')

# Flicker keeps the UI font resident while both maps alternate.
flicker=(ROOT/'src/flicker_data.h').read_text()
flicker_source=(ROOT/'src/flicker.c').read_text()
sizes={}
for name in ('preview','reference'):
 values=re.search(r'flicker_'+name+r'_tiles\[\]=\{([^}]+)\}',flicker)[1].split(',')
 assert len(values)%16==0,(name,len(values));sizes[name]=len(values)//16
preview=int(re.search(r'set_bkg_data\((\d+),sizeof\(flicker_preview_tiles\)',flicker_source)[1])
phases=int(re.search(r'set_bkg_data\((\d+)u\+phase\*count\+t',flicker_source)[1])
reference=int(re.search(r'set_bkg_data\((\d+),sizeof\(flicker_reference_tiles\)',flicker_source)[1])
actor,actors=map(int,re.search(r'set_sprite_data\((\d+),(\d+),flicker_actor\)',flicker_source).groups())
# The full view streams two phases of n*n tiles; a checker cell of c pixels
# repeats every n tiles once its factors of two are removed, as in prepare().
cell=lambda c:c if c&1 else c>>1 if (c>>1)&1 else c>>2
full=2*max(cell(c)**2 for c in range(1,9))
assert preview==phases==ui['UI_ART'],(preview,phases,'Flicker tiles must start after the resident UI tiles')
assert preview+max(sizes['preview'],full)<=reference,('Flicker preview or full-view tiles overlap the reference',sizes['preview'],full,reference)
assert reference+sizes['reference']<=actor and actor+actors<=ui['UI_FOCUS'],('Flicker reference, sprites and focus overlap',reference,sizes['reference'],actor,actors)
assert syms['_flicker_run']>>16==4,'Flicker moved out of its allocated code bank'
print(f'Flicker fits {ui["UI_PASS"]+probes+full+sizes["reference"]+actors} resident patterns, {actors} sprites, and both preloaded LCD maps')

# The Color header's tiles live alone in VRAM bank 1 and its map covers rows 0-2.
logo=(ROOT/'src/logo.h').read_text()
logo_tiles=int(re.search(r'BB_LOGO_TILES (\d+)',logo)[1])
logo_map=re.search(r'bb_logo_map\[\]=\{([^}]+)\}',logo)[1].split(',')
assert logo_tiles<=256 and len(logo_map)==60 and max(map(int,logo_map))<logo_tiles,(logo_tiles,len(logo_map))
print(f'Color header uses {logo_tiles} tiles in VRAM bank 1')

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
# Text can also come from a string table indexed in the call, such as a list of
# button names, so the entries of every table named there are checked too.
def tables(source):
 return {name:body for name,body in re.findall(r'\b(\w+)\s*\[[^\]]*\]\s*=\s*\{([^{}]*)\}',source)}
too_long=[];checked=0
for path in sorted(ROOT.glob('src/*.c'))+sorted(ROOT.glob('src/*.inc'))+[BUILD/'adapted/link.c']:
 source=path.read_text()
 # A table may sit in an included file.
 known=tables(source)
 for include in re.findall(r'#include "(\w+\.inc)"',source):known.update(tables((ROOT/'src'/include).read_text()))
 for name,columns in [('ui_field',(1,2)),('ui_value',(1,))]:
  for args in call_arguments(source,name):
   for column in columns:
    texts=re.findall(r'"((?:[^"\\]|\\.)*)"',args[column])
    for table in re.findall(r'\b(\w+)\s*\[',args[column]):texts+=re.findall(r'"((?:[^"\\]|\\.)*)"',known.get(table,''))
    checked+=len(texts);too_long+=[(path.name,text) for text in texts if len(text)>8]
assert not too_long,('Settings text wider than its eight columns',too_long)
print(f'Every settings label and value fits its eight columns ({checked} strings, including indexed tables)')
