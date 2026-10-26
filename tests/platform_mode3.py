"""Platform's 13th tell: VRAM and palette writes made while a line is drawn.

PyBoy lets both writes through, so the tell must fail there and the 13th
port, a sprite over the chip, must show the failed mark. SameBoy drops them
as a console does, so with --core the tell must pass there.
"""
import argparse,shutil,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from cart import ROMS,symbols
from pyboy import PyBoy
a=argparse.ArgumentParser();a.add_argument('--core',type=Path);a.add_argument('--rom',type=Path,default=ROMS['mbc5'])
args=a.parse_args();syms=symbols(args.rom)
UI_PASS,UI_FAIL=107,108

def mode3_obs(read):return list(read(syms['_pd_obs']+48,2))
def mask(read):m=read(syms['_pd_mask'],2);return m[0]|m[1]<<8

with tempfile.TemporaryDirectory() as d:
 path=Path(d)/'cart.gbc';shutil.copy(args.rom,path)
 p=PyBoy(str(path),window='null',sound_emulated=False);p.set_emulation_speed(0)
 try:
  p.tick(240,True);p.button_press('a');p.tick(8,True);p.button_release('a');p.tick(150,True)
  read=lambda at,n:bytes(p.memory[at:at+n])
  assert mode3_obs(read)==[1,1] and mask(read)&(1<<12),(mode3_obs(read),hex(mask(read)))
  assert p.memory[0xfe02]==UI_FAIL and p.memory[0xfe01]==84 and p.memory[0xfe00]==72,list(p.memory[0xfe00:0xfe04])
 finally:p.stop(save=False)
print('PyBoy: both mode-3 writes landed, the 13th tell failed and its port shows the failed mark')
if args.core:
 from libretro import SameBoy
 s=SameBoy(args.core,args.rom,model='Game Boy Color')
 try:
  s.tick(600);s.press('a');s.tick(200)
  read=s.read
  assert mode3_obs(read)==[0,0] and not mask(read)&(1<<12),(mode3_obs(read),hex(mask(read)))
 finally:s.close()
 print('SameBoy: both mode-3 writes were dropped and the 13th tell passed')
