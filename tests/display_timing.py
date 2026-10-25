"""Display flicker phases last the set interval, and full-view controls respond."""
import argparse,itertools
from pathlib import Path
from cart import Cart,ROMS
a=argparse.ArgumentParser();a.add_argument('--rom',type=Path,default=ROMS['mbc5']);args=a.parse_args()

def ready(c):
 for _ in range(240):
  if c.get('display_ready'):return True
  c.tick()
 return False

def palette(c,cgb):
 if not cgb:return c.p.memory[0xff47]
 c.p.memory[0xff68]=0x80;return c.p.memory[0xff69]

for cgb in (True,False):
 for interval in (1,2,30):
  c=Cart(args.rom,cgb)
  try:
   c.go(5);c.preset(4);c.p.memory[c.syms['_display_interval']]=interval
   c.press('a');assert ready(c)
   samples=[]
   for _ in range(interval*8+8):c.tick();samples.append(palette(c,cgb))
   runs=[len(list(group)) for _,group in itertools.groupby(samples)][1:-1]
   assert runs and set(runs)=={interval},(cgb,interval,'Flicker phases',runs)
  finally:c.close()
 c=Cart(args.rom,cgb)
 try:
  c.go(5);c.preset(1);c.press('a');assert ready(c) and c.get('display_pattern')==2
  c.press('right');assert c.get('display_pattern')==3 and ready(c),'Right did not change the running pattern'
  before=palette(c,cgb);c.press('select');assert c.get('display_invert')==1 and palette(c,cgb)!=before,'Select did not invert the running pattern'
  c.press('b');assert not c.get('display_running') and 'Display' in c.row(5)
 finally:c.close()
 print(('CGB' if cgb else 'DMG')+': flicker phases of 1, 2 and 30 frames, and Right/Select/B during the full view',flush=True)
