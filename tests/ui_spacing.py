"""Keep large counters inside the right margin and show SRAM progress promptly."""
from pathlib import Path
import shutil,tempfile,re,sys
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1];rom=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'build/bacon-bits.gbc'
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',rom.with_suffix('.noi').read_text(),re.M)}
with tempfile.TemporaryDirectory() as td:
 f=Path(td)/'spacing.gbc';shutil.copy(rom,f);p=PyBoy(str(f),window='null',sound_emulated=False);p.set_emulation_speed(0)
 def press(k):p.button_press(k);p.tick(8,True);p.button_release(k);p.tick(30,True)
 def row(y):return ''.join(chr(t+32) if t<96 else '#' for t in p.memory[0,0x9800+y*32:0x9814+y*32])
 try:
  p.tick(240,True)
  for _ in range(4):press('right')
  press('a')
  for _ in range(3):press('down')
  press('a');at=syms['_button_opposites'];p.memory[at:at+4]=[255]*4;press('a')
  p.screen.image.save(ROOT/'build'/('counter-overflow-before.png' if 'before' in rom.name else 'counter-spacing-after.png'))
  assert row(17)[12:19]=='4294M  ' and row(17)[19]==' ',row(17)
  assert bytes(p.memory[at:at+4])==bytes([255]*4),'Formatting changed the retained count'
  for k in ['a','b','start','select']:p.button_press(k)
  p.tick(100,True)
  for k in ['a','b','start','select']:p.button_release(k)
  p.tick(30,True);press('down');press('a')
  press('right');press('right');press('a');press('down');press('a');press('a');press('down');press('a')
  body='\n'.join(row(y) for y in range(6,18))
  for _ in range(8):
   if 'Written' in body or 'Verified' in body:break
   p.tick(1,True);body='\n'.join(row(y) for y in range(6,18))
  assert 'Written' in body or 'Verified' in body,body
  p.screen.image.save(ROOT/'build/sram-progress-spacing.png')
 finally:p.stop(save=False)
print('Full 32-bit count retained with a fitted display; SRAM instrument and progress appear immediately')
