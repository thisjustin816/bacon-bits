"""Write and verify every SRAM pattern through the cartridge's confirmation UI."""
from pathlib import Path
import re,tempfile,shutil
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1]
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',(ROOT/'build/bacon-bits.noi').read_text(),re.M)}
with tempfile.TemporaryDirectory() as td:
 f=Path(td)/'test.gbc';shutil.copy(ROOT/'build/bacon-bits.gbc',f);p=PyBoy(str(f),window='null',sound_emulated=False);p.set_emulation_speed(0)
 def get(n,size=1):return int.from_bytes(bytes(p.memory[syms['_'+n]:syms['_'+n]+size]),'little')
 def press(k):p.button_press(k);p.tick(8,True);p.button_release(k);p.tick(30,True)
 def text():return '\n'.join(''.join(chr(t+32) if t<64 else '#' for t in p.memory[0,0x9800+y*32:0x9800+y*32+20]) for y in range(18))
 try:
  p.tick(240,True)
  for _ in range(6):press('right')
  press('a');p.tick(60,True);press('up');press('a');p.tick(60,True);press('right');press('down')
  for _ in range(3):press('left')
  assert get('ram_banks')==1;press('down');press('right');press('right');assert get('ram_pattern')==0
  for pattern in range(8):
   assert get('ram_pattern')==pattern
   press('a');press('down');press('a')
   for _ in range(100):
    p.tick(8,True)
    if 'SRAM RESULT' in text():p.tick(40,True);break
   assert 'PASS' in text() and get('ram_checked',4)==8160,(pattern,text())
   press('b');press('right')
  print('SRAM: all eight patterns, one-bank boundaries, completed record updates, and confirmed writes passed')
 finally:p.stop(save=False)
