"""Verify the shipped glyphs and the solid header backdrop in both LCD modes."""
from pathlib import Path
import tempfile,shutil,sys
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from lettering import tiles
from header import pyboy_header,vram_header
from PIL import Image
# The published glyph sheet must decode to the same tiles the ROM carries.
sheet=Image.open(ROOT/'assets/font.png').convert('L');decoded=bytearray()
for i in range(96):
 for y in range(8):
  bits=sum(0x80>>x for x in range(8) if sheet.getpixel((i%16*8+x,i//16*8+y))<128);decoded+=bytes((bits,bits))
assert bytes(decoded)==tiles(),'assets/font.png differs from the ROM font'
for cgb in [True,False]:
 with tempfile.TemporaryDirectory() as td:
  f=Path(td)/'test.gbc';shutil.copy(ROOT/'build/bacon-bits.gbc',f);p=PyBoy(str(f),window='null',sound_emulated=False,cgb=cgb);p.set_emulation_speed(0)
  try:
   p.tick(240,True)
   # Launcher punctuation slots carry centered labels; entering a test restores them.
   p.button_press('a');p.tick(8,True);p.button_release('a');p.tick(90,True)
   assert bytes(p.memory[0,0x8000:0x8600])==tiles()
   # The sky above and below the name is one solid color.
   image=p.screen.image.convert('RGB');assert len({image.getpixel((x,1)) for x in range(160)})==1
   assert len({image.getpixel((x,22)) for x in range(160)})==1
   assert pyboy_header(p,cgb)
  finally:p.stop(save=False)
print('Original bold glyphs and a solid header backdrop passed in CGB and DMG')
