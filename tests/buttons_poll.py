"""The Buttons loop reads the pad as often as before its hints: only the timing and diagonal refreshes skip polls."""
import argparse
from pathlib import Path
from cart import Cart,ROMS
a=argparse.ArgumentParser();a.add_argument('--rom',type=Path,default=ROMS['mbc5']);args=a.parse_args()
# Frames between two reads of the pad. The live and count pages never skip one. The timing page's refresh costs one
# skipped poll every 16 frames and the diagonals page's costs three, as they did before the hints.
ALLOWED={0:{1},1:{1},2:{1,2},3:{1,4}}
for cgb in (True,False):
 for page in range(4):
  c=Cart(args.rom,cgb=cgb)
  try:
   c.go(4);c.preset(1)
   for _ in range(page):c.press('select')
   assert c.get('button_page')==page,page
   at=c.syms['_sys_time'];times=[]
   c.p.hook_register(0,c.syms['_joypad'],lambda ctx:times.append(int.from_bytes(bytes(c.p.memory[at:at+2]),'little')),None)
   c.tick(2000)
   c.p.hook_deregister(0,c.syms['_joypad'])
   steps={b-a for a,b in zip(times,times[1:])}
   assert steps<=ALLOWED[page],('cgb' if cgb else 'dmg',page,'Buttons loop skipped more polls than before',sorted(steps))
  finally:c.close()
print('Buttons loop poll rate: the live and count pages never skip a poll; the timing and diagonal refreshes skip no more than before, in CGB and DMG')
