"""Verify the shipped glyphs and an uninterrupted horizon in both LCD modes."""
from pathlib import Path
import tempfile,shutil,sys
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from lettering import tiles
for cgb in [True,False]:
 with tempfile.TemporaryDirectory() as td:
  f=Path(td)/'test.gbc';shutil.copy(ROOT/'build/bacon-bits.gbc',f);p=PyBoy(str(f),window='null',sound_emulated=False,cgb=cgb);p.set_emulation_speed(0)
  try:
   p.tick(240,True);assert bytes(p.memory[0,0x8000:0x8400])==tiles()
   image=p.screen.image.convert('RGB');assert len({image.getpixel((x,23)) for x in range(160)})==1
   assert len({image.getpixel((x,31)) for x in range(160)})==1
   if cgb:assert list(p.memory[1,0x9860:0x9874])==[0]*20
  finally:p.stop(save=False)
print('Original bold glyphs and solid header/subheading bands passed in CGB and DMG')
