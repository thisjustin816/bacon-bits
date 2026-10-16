"""Capture cartridge inputs and animations from the compiled release ROMs."""
from pathlib import Path
import tempfile,shutil
from PIL import Image,ImageDraw
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1];shots=[];browsers=[]
with tempfile.TemporaryDirectory() as td:
 for selected in range(12):
  variant='mbc3' if selected==11 else '';pick=2 if selected==11 else selected
  f=Path(td)/f'{selected}.gbc';shutil.copy(ROOT/'build'/variant/'bacon-bits.gbc',f)
  p=PyBoy(str(f),window='null',sound_emulated=False);p.set_emulation_speed(0)
  def press(k,after=30):p.button_press(k);p.tick(8,True);p.button_release(k);p.tick(after,True)
  try:
   p.tick(240,True)
   for _ in range(pick):press('right')
   if selected in [0,4,8]:browsers.append(p.screen.image.convert('RGB'))
   if selected==0:
    frames=[]
    for _ in range(40):p.tick(2,True);frames.append(p.screen.image.convert('RGB').resize((480,432),Image.Resampling.NEAREST))
    frames[0].save(ROOT/'assets/browser.gif',save_all=True,append_images=frames[1:],duration=34,loop=0)
   press('a');p.tick(90,True)
   if pick>=3 or selected==11:
    if pick==4:
     for _ in range(3):press('down')
    if pick==6:press('down')
    press('a');p.tick(60,True)
   if pick==1:press('start');press('right')
   if pick==3:press('a')
   if pick==4:p.button_press('up');p.button_press('right');p.tick(16,True)
   if pick==6:press('a');press('down');press('a',after=40)
   if pick in [7,8,9] or selected==11:press('a')
   if selected==11:p.tick(90,True)
   if pick==3:
    frames=[]
    for _ in range(40):p.tick(2,True);frames.append(p.screen.image.convert('RGB').resize((480,432),Image.Resampling.NEAREST))
    frames[0].save(ROOT/'assets/audio.gif',save_all=True,append_images=frames[1:],duration=34,loop=0)
   p.screen.image.save(ROOT/'build'/f'review-test-{selected}.png');shots.append(p.screen.image.convert('RGB'))
  finally:p.stop(save=False)
 board=Image.new('RGB',(680,664),(227,219,200));d=ImageDraw.Draw(board)
 labels=['Platform','Link Cable','Rumble','Audio Range','D-pad diagonals','Display settings','SRAM pattern check','Burn In','Cartridge LED','Infrared','Flicker comparison','Real Time Clock']
 for i,(im,label) in enumerate(zip(shots,labels)):
  x=8+i%4*168;y=8+i//4*168;board.paste(im,(x,y));d.text((x,y+146),label,fill=(64,40,32))
 # Last row shows the three browser pages.
 for i,im in enumerate(browsers):board.paste(im,(8+i*168,512))
 board.resize((1360,1328),Image.Resampling.NEAREST).save(ROOT/'assets/review.png')
 # Presets remain part of the shared UI.
 preset_shots=[]
 for selected in [3,4,5,6,7]:
  f=Path(td)/f'preset-{selected}.gbc';shutil.copy(ROOT/'build/bacon-bits.gbc',f);p=PyBoy(str(f),window='null',sound_emulated=False);p.set_emulation_speed(0);p.tick(240,True)
  try:
   for _ in range(selected):press('right')
   press('a');p.tick(60,True);preset_shots.append(p.screen.image.convert('RGB'))
  finally:p.stop(save=False)
 board=Image.new('RGB',(840,160),(227,219,200))
 for i,im in enumerate(preset_shots):board.paste(im,(8+i*168,8))
 board.resize((1680,320),Image.Resampling.NEAREST).save(ROOT/'assets/presets.png')
 # Native menu focus and live controls, in both display modes.
 controls=[]
 for cgb in [True,False]:
  f=Path(td)/f'controls-{cgb}.gbc';shutil.copy(ROOT/'build/bacon-bits.gbc',f)
  p=PyBoy(str(f),window='null',sound_emulated=False,cgb=cgb);p.set_emulation_speed(0)
  try:
   p.tick(240,True)
   for _ in range(4):press('right')
   controls.append(p.screen.image.convert('RGB'))
   press('a');press('a');p.button_press('up');p.button_press('right');p.tick(24,True)
   controls.append(p.screen.image.convert('RGB'))
  finally:p.stop(save=False)
 board=Image.new('RGB',(336,328),(227,219,200));d=ImageDraw.Draw(board)
 for i,im in enumerate(controls):
  x=4+i%2*168;y=4+i//2*164;board.paste(im,(x,y));d.text((x,y+146),('Color' if i<2 else 'Monochrome')+(' menu' if i%2==0 else ' live buttons'),fill=(64,40,32))
 board.resize((1008,984),Image.Resampling.NEAREST).save(ROOT/'assets/controls.png')
