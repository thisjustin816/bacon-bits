"""Replay the original timing suite against the banked assembly bytes."""
from pathlib import Path
import json,runpy,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor/rumble-pulse'))
import build
import emu
class CombinedGB(emu.GB):
 def step(self):
  # LD (DE),A is used by the adapter's idle-state copy, and takes eight cycles.
  if self.rb(self.pc)==0x12:
   self.pc=(self.pc+1)&65535;self.wb((self.d<<8)|self.e,self.a);self.cyc+=8;return 8
  return super().step()
# Check the added instruction's destination, flags, PC and cycle count.
probe=bytearray(0x8000);probe[0x100]=0x12
for address in [0xc000,0xc030,0xdfff]:
 for value in [0,255]:
  cpu=CombinedGB(probe);cpu.d=address>>8;cpu.e=address&255;cpu.a=value
  cpu.fz,cpu.fn,cpu.fh,cpu.fc=1,0,1,1
  assert cpu.step()==8 and cpu.cyc==8 and cpu.pc==0x101 and cpu.rb(address)==value
  assert (cpu.fz,cpu.fn,cpu.fh,cpu.fc)==(1,0,1,1)
emu.GB=CombinedGB
rom=(ROOT/'build/bacon-bits.gbc').read_bytes()
# The timing interpreter has a flat 32 KiB bus. Map the combined ROM's
# rumble bank at $4000 and enter it directly, bypassing the C launcher.
flat=bytearray(0x8000)
flat[0x100:0x103]=bytes([0xc3,0,0x40])
flat[0x4000:]=rom[3*0x4000:4*0x4000]
build.a.rom=flat
build.a.labels=json.loads((ROOT/'build/rumble-labels.json').read_text())
runpy.run_path(str(ROOT/'vendor/rumble-pulse/test.py'),run_name='__main__')
print('Original rumble timing suite passed against the combined ROM bank')
