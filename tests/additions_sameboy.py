"""Check new screen palettes, maps, waveform writes, and CPU switching in SameBoy."""
from pathlib import Path
import re,argparse
from libretro import SameBoy
from display_assertions import check_pattern
from header import vram_header
from audio_expected import WAVES
ROOT=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--core',required=True,type=Path);args=a.parse_args()
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',(ROOT/'build/bacon-bits.noi').read_text(),re.M)}
p=SameBoy(args.core,ROOT/'build/bacon-bits.gbc')
def get(n,size=1):return int.from_bytes(p.read(syms['_'+n],size),'little')
def launch(n):
 for _ in range(16):
  if get('selected_test')==n:break
  p.press('right')
 else:raise AssertionError('Browser was not reached')
 p.press('a');p.tick(90)
 if n>=3:p.press('up');p.press('a');p.tick(60)
def text():
 v=p.vram();return '\n'.join(''.join(chr(t+32).upper() if t<96 else '#' for t in v[0x1800+y*32:0x1800+y*32+20]) for y in range(18))
try:
 # SameBoy starts without a boot ROM, so the logo must load with no help from it.
 p.tick(600);assert vram_header(p.vram(),True),'Color header missing at boot';launch(0);before=p.vram();press=p.press;press('select');assert ' PROBE ' in text().split('\n')[4];p.image.save(ROOT/'build/sameboy-probe.png')
 press('select');assert 'NO KNOWN MATCH' in text();p.image.save(ROOT/'build/sameboy-signature.png');press('b');p.tick(120);after=p.vram()
 for y in range(18):
  assert before[0x1800+y*32:0x1800+y*32+20]==after[0x1800+y*32:0x1800+y*32+20]
  assert before[0x3800+y*32:0x3800+y*32+20]==after[0x3800+y*32:0x3800+y*32+20]
 p.chord();press('down');press('a');launch(3);press('a');press('up');press('right');press('right');assert get('tone_voice')==2
 press('select')
 seen=set()
 for _ in range(6):
  p.capture=True;p.samples.clear();p.tick(40);assert p.read(0xff1a)[0]&0x80
  import numpy as np
  assert np.std(np.frombuffer(b''.join(p.samples),dtype=np.int16))>1
  press('a');shape=p.read(syms['_tone_shape']+2)[0];wave=p.read(0xff30,16);assert wave==WAVES[shape],(shape,wave.hex(),WAVES[shape].hex());seen.add(shape);press('a');press('right')
 assert len(seen)==6;press('b');launch(4);press('a');p.image.save(ROOT/'build/sameboy-buttons.png')
 for _ in range(3):press('select')
 p.held={p.BUTTONS['up'],p.BUTTONS['right']};p.tick(12);p.held=set();p.tick(12)
 assert get('button_diagonal',4)==1 and 'DIAGONALS' in text();p.image.save(ROOT/'build/sameboy-diagonals.png')
 p.held={0,2,3,8};p.tick(110);p.held=set();p.tick(20);press('down');press('a');launch(5)
 for pattern in range(7):
  press('a');p.tick(100);assert get('display_ready');check_pattern(p.image,pattern,True)
  p.image.save(ROOT/'build'/f'sameboy-display-{pattern}.png');press('b');press('right')
 press('b');launch(6);press('a');assert 'UNKNOWN' in text();press('b');press('b');launch(7);press('down');press('down');press('right');press('a');p.tick(200)
 assert get('bb_fast')==1,(get('bb_fast'),get('burn_running'),text());assert get('burn_errors',4)==0;press('b');assert get('bb_fast')==0
 print('SameBoy: probe map/attribute restore, six exact wave RAM patterns with audio captures, buttons, all display palettes including 32 distinct ramp shades, and double-speed burn-in return passed')
finally:p.close()
