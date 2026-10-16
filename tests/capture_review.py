"""Capture browser and audio review frames through ordinary cartridge inputs."""
from pathlib import Path
import tempfile,shutil
from PIL import Image
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td:
 f=Path(td)/'test.gbc';shutil.copy(ROOT/'build/bacon-bits.gbc',f)
 p=PyBoy(str(f),window='null',sound_emulated=False);p.set_emulation_speed(0)
 shots=[]
 def press(k):p.button_press(k);p.tick(8,True);p.button_release(k);p.tick(24,True)
 try:
  p.tick(240,True)
  for i in range(4):
   shots.append(p.screen.image.convert('RGB'));p.screen.image.save(ROOT/'build'/f'review-browser-{i}.png')
   if i<3:press('right')
  press('a');shots.append(p.screen.image.convert('RGB'))
  press('a');press('right');shots.append(p.screen.image.convert('RGB'))
 finally:p.stop(save=False)
 board=Image.new('RGB',(328,448),(255,255,255))
 for i,im in enumerate(shots):board.paste(im,(i%2*168,i//2*152))
 board.resize((656,896),Image.Resampling.NEAREST).save(ROOT/'build/review.png')
