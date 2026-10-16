"""A damaged ROM must fail burn-in and keep its first failure when continuing."""
from pathlib import Path
import re,tempfile
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1]
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',(ROOT/'build/bacon-bits.noi').read_text(),re.M)}
with tempfile.TemporaryDirectory() as td:
 data=bytearray((ROOT/'build/bacon-bits.gbc').read_bytes());data[7*16384+16383]^=1
 f=Path(td)/'damaged.gbc';f.write_bytes(data);p=PyBoy(str(f),window='null',sound_emulated=False);p.set_emulation_speed(0)
 def get(n,size=1):return int.from_bytes(bytes(p.memory[syms['_'+n]:syms['_'+n]+size]),'little')
 def press(k):p.button_press(k);p.tick(8,True);p.button_release(k);p.tick(16,True)
 try:
  p.tick(240,True)
  for _ in range(4):press('left')
  assert get('selected_test')==7
  press('a');p.tick(60,True);press('up');press('a');p.tick(60,True);press('down');press('right') # high load
  press('down');press('right') # CGB double speed
  press('down');press('right') # continue on failure
  press('a')
  for _ in range(1000):
   p.tick(8,True)
   if get('burn_errors',4):break
  assert get('burn_errors',4)==1 and get('burn_running')
  assert get('burn_first_kind')==1 and get('burn_first_bank')==7
  first=(get('burn_first_expected',2),get('burn_first_read',2));assert first[0]!=first[1]
  cycle=get('burn_cycles',4)
  for _ in range(1000):
   p.tick(8,True)
   if get('burn_cycles',4)>cycle:break
  assert get('burn_errors',4)>=2 and first==(get('burn_first_expected',2),get('burn_first_read',2))
  assert get('burn_seconds',4)>0 and p.memory[0xff4d]&0x80
  press('b');assert not get('burn_running') and not p.memory[0xff4d]&0x80 and not p.memory[0xff26]&0x80,(get('burn_running'),p.memory[0xff4d],p.memory[0xff26])
  print('Burn-in: altered ROM padding detected in bank 7, repeated failure retains first evidence, elapsed time advances at double CPU speed, exit restores speed/APU')
 finally:p.stop(save=False)
