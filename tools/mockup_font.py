"""Render a proposed font in the existing cartridge's real browser frame."""
from pathlib import Path
import tempfile,shutil
from PIL import Image
from pyboy import PyBoy
from lettering import tiles
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td:
 f=Path(td)/'test.gbc';shutil.copy(ROOT/'build/bacon-bits.gbc',f);p=PyBoy(str(f),window='null',sound_emulated=False);p.set_emulation_speed(0)
 try:
  p.tick(240,True);before=p.screen.image.convert('RGB');p.memory[0x8000:0x8400]=list(tiles());
  # The full-width horizon and a cream band keep text on one background.
  p.memory[0x8000+74*16:0x8000+75*16]=[0,0]*4+[0,255]*4
  for x in range(12):p.memory[0x9800+2*32+x]=74
  p.memory[0xff4f]=1
  for x in range(20):p.memory[0x9800+3*32+x]=0
  p.memory[0xff4f]=0;p.tick(3,True);after=p.screen.image.convert('RGB')
  before.save(ROOT/'build/font-before.png');after.save(ROOT/'build/font-proposed.png')
  board=Image.new('RGB',(328,144),(232,223,206));board.paste(before,(0,0));board.paste(after,(168,0));board.resize((984,432),Image.Resampling.NEAREST).save(ROOT/'build/font-comparison.png')
 finally:p.stop(save=False)
