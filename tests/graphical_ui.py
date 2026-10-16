"""Verify the shared brand, four-card launcher, and live platform evidence."""
from pathlib import Path
import shutil,tempfile,sys
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1]
rom=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'build/bacon-bits.gbc'
def row(p,y):return ''.join(chr(n+32).upper() if n<96 else '?' for n in p.memory[0,0x9800+y*32:0x9814+y*32])
with tempfile.TemporaryDirectory() as td:
 f=Path(td)/'ui.gbc';shutil.copy(rom,f)
 for cgb in [True,False]:
  p=PyBoy(str(f),window='null',sound_emulated=False,cgb=cgb);p.set_emulation_speed(0)
  def press(k):p.button_press(k);p.tick(8,True);p.button_release(k);p.tick(30,True)
  try:
   p.tick(240,True);p.screen.image.save(ROOT/'build'/f'graphical-browser-{cgb}.png')
   assert 'TEST CARTRIDGE' in row(p,2),'The complete cartridge brand is missing'
   assert 'PLATFORM' in row(p,9) and 'LINK' in row(p,9),'The four-card menu is missing'
   assert 'RUMBLE' in row(p,15)
   press('a');p.tick(120,True)
   assert 'TEST CARTRIDGE' in row(p,2),'Platform still uses the old interface'
   assert 'PLATFORM' in row(p,4)
   p.screen.image.save(ROOT/'build'/f'graphical-platform-{cgb}.png')
   if cgb:
    assert 'PYBOY' in row(p,16)
    press('a');assert 'PROBE DETAILS' in row(p,4)
    press('b');assert 'PLATFORM' in row(p,4)
  finally:p.stop(save=False)
print('Shared graphical launcher and platform UI passed in CGB and DMG modes')
