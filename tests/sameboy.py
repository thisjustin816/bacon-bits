"""Exercise the combined cartridge in SameBoy, including modal tile restores."""
from pathlib import Path
import argparse,json,re
import numpy as np
from libretro import SameBoy
ROOT=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--core',type=Path,required=True);a.add_argument('--rom',type=Path,default=ROOT/'build/bacon-bits.gbc');args=a.parse_args()
p=SameBoy(args.core,args.rom)
try:
 p.tick(600);p.image.save(ROOT/'build/sameboy-browser.png')
 assert len(p.image.getcolors(65536))>3
 def shot(name):p.image.save(ROOT/'build'/('sameboy-'+name+'.png'))
 def modal():
  before=p.vram();p.chord();shot('modal');
  v=p.vram();popup=''.join(chr(t+32).upper() if t<96 else '#' for y in range(18) for t in v[0x1800+y*32:0x1800+y*32+20]);assert 'CONTINUE' in popup,'Return chord did not open the modal';p.press('b');after=p.vram()
  assert before[:0x1800]==after[:0x1800],('Modal changed tile patterns after CONTINUE',[(i,a,b) for i,(a,b) in enumerate(zip(before[:0x1800],after[:0x1800])) if a!=b][:40])
  assert all(before[0x1800+y*32+2:0x1800+y*32+18]==after[0x1800+y*32+2:0x1800+y*32+18] for y in range(5,13)),('Modal changed the covered tile-map cells after CONTINUE',[(y,x,before[0x1800+y*32+x],after[0x1800+y*32+x]) for y in range(5,13) for x in range(2,18) if before[0x1800+y*32+x]!=after[0x1800+y*32+x]])
  assert before[0x3800:0x3c00]==after[0x3800:0x3c00],'Modal changed CGB attributes after CONTINUE'
 def leave():p.chord();p.press('down');p.press('a');p.tick(30)
 p.press('a');p.tick(150);shot('platform');modal();leave()
 p.press('right');p.press('a');p.tick(100);shot('link');assert p.vram()[0:16]==bytes(16),'The ball tile overwrote the space glyph';modal();leave()
 p.press('right');p.press('a');p.tick(100);shot('rumble');modal()
 p.transitions.clear();p.press('start');p.tick(90);shot('rumble-play');assert any(on for _,on in p.transitions),p.transitions
 p.press('b');leave()
 p.press('right');p.press('a');p.tick(60);p.press('up');p.press('a');p.tick(60);shot('audio')
 p.capture=True;p.samples.clear();p.press('a');p.tick(30)
 assert p.read(0xff12)[0]==0xf0 and p.read(0xff25)[0]==0x11,'Pulse setup/routing did not reach the APU'
 assert np.std(np.frombuffer(b''.join(p.samples),dtype=np.int16))>1,'Pulse produced no SameBoy audio samples'
 p.press('b');assert p.read(0xff26)[0]&0x80==0,'APU remained active on return'
 def visible(core):assert len(core.image.getcolors(65536))>1,'Blank browser frame'
 for _ in range(4):
  p.held={p.BUTTONS['right']};p.tick(8,visible)
  p.held=set();p.tick(30,visible)
 shot('returned');print('SameBoy: browser, four diagnostics, modal tile/attribute restoration and rumble output passed')
finally:p.close()
