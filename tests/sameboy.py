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
  before=p.vram();p.chord();shot('modal');p.press('b');after=p.vram()
  assert before[:0x1800]==after[:0x1800],'Modal changed tile patterns after CONTINUE'
  assert all(before[0x1800+y*32+2:0x1800+y*32+18]==after[0x1800+y*32+2:0x1800+y*32+18] for y in range(5,13)),'Modal changed the covered tile-map cells after CONTINUE'
  assert before[0x3800:0x3c00]==after[0x3800:0x3c00],'Modal changed CGB attributes after CONTINUE'
 def leave():p.chord();p.press('down');p.press('a');p.tick(30)
 p.press('a');p.tick(150);shot('platform');modal();leave()
 p.press('right');p.press('a');p.tick(100);shot('link');modal();leave()
 p.press('right');p.press('a');p.tick(100);shot('rumble');modal()
 p.transitions.clear();p.press('start');p.tick(90);shot('rumble-play');assert any(on for _,on in p.transitions),p.transitions
 p.press('b');leave()
 p.press('right');p.press('a');p.tick(60);shot('audio')
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
