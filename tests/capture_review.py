"""Capture ordinary cartridge inputs for the review sheet."""
from pathlib import Path
import tempfile,shutil
from PIL import Image,ImageDraw
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1]
shots=[]
with tempfile.TemporaryDirectory() as td:
 for selected in range(8):
  f=Path(td)/f'test-{selected}.gbc';shutil.copy(ROOT/'build/bacon-bits.gbc',f)
  p=PyBoy(str(f),window='null',sound_emulated=False);p.set_emulation_speed(0)
  def press(k):p.button_press(k);p.tick(8,True);p.button_release(k);p.tick(30,True)
  try:
   p.tick(240,True)
   for _ in range(selected):press('right')
   shots.append(p.screen.image.convert('RGB'));press('a');p.tick(180,True)
   if selected>=3:press('a');p.tick(60,True)
   if selected==0:press('select')
   if selected==3:press('select');press('right');press('right')
   if selected==4:
    for _ in range(3):press('select')
    p.button_press('up');p.button_press('right');p.tick(12,True);p.button_release('up');p.button_release('right');p.tick(12,True)
   if selected==6:press('a')
   if selected==7:press('a');p.tick(180,True)
   p.screen.image.save(ROOT/'build'/f'review-test-{selected}.png')
  finally:p.stop(save=False)
 for i in range(8):shots.append(Image.open(ROOT/'build'/f'review-test-{i}.png').convert('RGB'))
 board=Image.new('RGB',(680,616),(232,223,206))
 for i,im in enumerate(shots):board.paste(im,(8+i%4*168,8+i//4*152))
 board.resize((1360,1232),Image.Resampling.NEAREST).save(ROOT/'assets/review.png')
