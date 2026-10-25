"""The shared header: on Color the logo, mapped over its tiles in VRAM bank 1;
on monochrome the name in the shared font, centered on row 1."""
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LOGO=[int(v) for v in re.search(r'bb_logo_map\[\]=\{([^}]+)\}',(ROOT/'src/logo.h').read_text())[1].split(',')]
NAME=[ord(c)-32 for c in 'Bacon Bit Bench']
def header_ok(maps,attrs,cgb):
 """maps and attrs are the first three 32-cell rows of the background map
 and of its attributes."""
 rows=[list(maps[y*32:y*32+20]) for y in range(3)]
 if cgb:return sum(rows,[])==LOGO and all(a==0x09 for y in range(3) for a in attrs[y*32:y*32+20])
 return rows[0]==[0]*20 and rows[2]==[0]*20 and rows[1]==[0,0]+NAME+[0,0,0]
def pyboy_header(p,cgb):
 return header_ok(bytes(p.memory[0,0x9800:0x9860]),bytes(p.memory[1,0x9800:0x9860]) if cgb else b'',cgb)
def vram_header(vram,cgb):
 """vram is SameBoy's 16 KiB, bank 0 then bank 1."""
 return header_ok(vram[0x1800:0x1860],vram[0x3800:0x3860],cgb)
