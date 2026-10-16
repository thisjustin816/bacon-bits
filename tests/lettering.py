"""Verify the shipped glyphs and the shared brand backdrop in both LCD modes."""
from pathlib import Path
import tempfile,shutil,sys
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from lettering import tiles
for cgb in [True,False]:
 with tempfile.TemporaryDirectory() as td:
  f=Path(td)/'test.gbc';shutil.copy(ROOT/'build/bacon-bits.gbc',f);p=PyBoy(str(f),window='null',sound_emulated=False,cgb=cgb);p.set_emulation_speed(0)
  try:
   p.tick(240,True)
   # Launcher punctuation slots carry centered labels; entering a test restores them.
   p.button_press('a');p.tick(8,True);p.button_release('a');p.tick(90,True)
   assert bytes(p.memory[0,0x8000:0x8600])==tiles()
   image=p.screen.image.convert('RGB');assert len({image.getpixel((x,24)) for x in range(32,160)})==1
   assert len({image.getpixel((x,31)) for x in range(32,160)})==1
   if cgb:assert list(p.memory[1,0x9860:0x9874])==[1]*20
  finally:p.stop(save=False)
print('Original bold glyphs and solid brand backdrop passed in CGB and DMG')
