"""Preparing full-screen display patterns must not overwrite resident UI glyphs."""
from pathlib import Path
import argparse,re,shutil,tempfile
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--rom',type=Path);args=a.parse_args()
for variant in ['', 'mbc3']:
 rom=args.rom or ROOT/'build'/variant/'bacon-bits.gbc'
 syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',rom.with_suffix('.noi').read_text(),re.M)}
 for cgb in [True,False]:
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/'test.gbc';shutil.copy(rom,f)
   p=PyBoy(str(f),window='null',sound_emulated=False,cgb=cgb);p.set_emulation_speed(0)
   def tick(n):p.tick(n,True)
   def press(k):p.button_press(k);tick(8);p.button_release(k);tick(30)
   try:
    tick(240)
    for _ in range(5):press('right')
    press('a');press('up');press('a')
    font=bytes(p.memory[0,0x8000:0x8600])
    def header():return bytes(t for y in range(4) for t in p.memory[0,0x9800+y*32:0x9814+y*32])
    original_header=header()
    for pattern in range(7):
     p.button_press('a')
     for frame in range(120):
      if frame==8:p.button_release('a')
      tick(1)
      if bytes(p.memory[0,0x8000:0x8600])!=font:
       p.screen.image.save(ROOT/'build'/f'display-font-failure-{variant or "mbc5"}-{cgb}.png')
       raise AssertionError((variant,cgb,pattern,frame,'Display preparation overwrote UI font'))
      if frame==5 and pattern==0:p.screen.image.save(ROOT/'build'/f'display-font-passed-{variant or "mbc5"}-{cgb}.png')
     assert p.memory[syms['_display_ready']], 'Display did not become ready'
     press('b')
     if header()!=original_header:
      p.screen.image.save(ROOT/'build'/f'display-header-failure-{variant or "mbc5"}-{cgb}.png')
      raise AssertionError((variant,cgb,pattern,'Display pixels leaked into restored header'))
     press('right')
   finally:p.stop(save=False)
 if args.rom:break
print('All seven display patterns preserve UI glyphs during preparation and playback, CGB/DMG and both mappers')
