"""Burn In timers count LCD frames, however many frames one load cycle takes."""
import argparse,re
from pathlib import Path
from cart import Cart,ROMS
a=argparse.ArgumentParser();a.add_argument('--rom',type=Path,default=ROMS['mbc5']);a.add_argument('--mbc3',type=Path,default=ROMS['mbc3']);args=a.parse_args()

def set_load(c,load):
 # Settings row 1 is Load: Light, Medium, High.
 c.press('down')
 while c.get('burn_running') or 'Load' not in c.row(9):c.tick()
 for _ in range(3):
  if load.lower() in c.row(9).lower():break
  c.press('right')
 assert load in c.row(9),c.row(9)

for load in ('Light','Medium','High'):
 c=Cart(args.mbc3)
 try:
  reads=[];at=c.syms['_rtc_read']
  c.p.hook_register(at>>16,at&0xffff,lambda _:reads.append(c.get('sys_time',2)),None)
  c.go(7);c.preset(3);c.press('select');set_load(c,load)
  reads.clear();c.press('a');start=len(reads);c.tick(640)
  watched=reads[start:]
  # The RTC watch reads the clock about every 64 frames.
  assert 8<=len(watched)<=12,(load,'RTC watch reads in 640 frames',len(watched))
  c.press('b')
 finally:c.close()
 c=Cart(args.rom)
 try:
  c.go(7);c.preset(1);set_load(c,load);c.press('a')
  shown=set();blank=0
  for _ in range(660):
   c.tick();found=re.match(r'\s*(\d+)',c.row(8)[10:19])
   if found:shown.add(int(found[1]))
   # A redraw rewrites each count in place, so no frame shows one missing.
   blank+=any(c.row(y)[x]==' ' for x,y in ((10,8),(10,11),(17,13)))
  assert not blank,(load,'Frames with a blank Seconds, Cycles or Errors count',blank)
  # Seconds redraw at least every 32 frames, so none of the first ten is skipped.
  assert set(range(1,11))<=shown,(load,'Seconds shown',sorted(shown))
  c.press('b')
 finally:c.close()
 print(f'{load} load: RTC watch every 64 frames, Seconds redrawn every second, no blank counts',flush=True)
