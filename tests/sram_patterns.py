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
 def expected(pattern,a,seed,bank=0):
  # The first sixteen bytes of each bank are its tag.
  if a<16:return (0x39+bank*23+a*7)&255
  if pattern<4:return [0,0xff,0x55,0xaa][pattern]
  if pattern==4:return 1<<(a&7)
  if pattern==5:return 255^(1<<(a&7))
  if pattern==6:return (a^(a>>8)^bank)&255
  # Random is a 16-bit xorshift (7, 9, 8) of the address and the bank's seed.
  x=a^((seed+bank*257)&0xffff);x^=(x<<7)&0xffff;x^=x>>9;x^=(x<<8)&0xffff
  return x&255
 def text():return '\n'.join(''.join(chr(t+32).upper() if t<96 else '#' for t in p.memory[0,0x9800+y*32:0x9800+y*32+20]) for y in range(18))
 try:
  p.tick(240,True)
  for _ in range(6):press('right')
  press('a');p.tick(60,True);press('up');press('a');p.tick(60,True);press('right');press('down')
  for _ in range(3):press('left')
  assert get('ram_banks')==1;press('down');press('right');press('right');assert get('ram_pattern')==0
  dumps=[]
  for pattern in range(8):
   assert get('ram_pattern')==pattern
   press('a');press('down');press('a')
   for _ in range(100):
    p.tick(8,True)
    if 'SRAM RESULT' in text():p.tick(40,True);break
   assert 'PASS' in text() and get('ram_checked',4)==8160,(pattern,text())
   # The cartridge verifies with the generator it wrote with, so compare the
   # bank with each pattern as specified, independently of that generator.
   data=bytes(p.memory[0,0xa000:0xa000+8160])
   want=bytes(expected(pattern,a,get('ram_seed',2)) for a in range(8160))
   wrong=[a for a in range(8160) if data[a]!=want[a]]
   assert not wrong,(pattern,'SRAM bytes differ from the pattern',[(hex(a),data[a],want[a]) for a in wrong[:8]])
   dumps.append(data[16:])
   press('b');press('right')
  assert len(set(dumps))==8,'Two SRAM patterns wrote the same bytes'
  print('SRAM: all eight patterns match their specified bytes, one-bank boundaries, completed record updates, and confirmed writes passed')
 finally:p.stop(save=False)
