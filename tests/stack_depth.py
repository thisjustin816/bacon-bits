"""Measure how deep the stack grows and keep it clear of static WRAM.

GBDK starts the stack at $E000 and static WRAM ends at s__HEAP_END. After boot
the suite fills the gap between them with $A5, runs every instrument, and
finds the lowest byte that changed. tools/check_build.py holds static WRAM
below STACK_FLOOR, and this suite requires the measured stack to stay above it.
"""
import argparse,json,re
from pathlib import Path
from cart import Cart,ROMS,ROOT
a=argparse.ArgumentParser();a.add_argument('--variant',choices=['mbc5','mbc3']);a.add_argument('--rom',type=Path);args=a.parse_args()
FLOOR=int(re.search(r'^STACK_FLOOR=(0x[\da-f]+)',(ROOT/'tools/check_build.py').read_text(),re.M)[1],16)
FILL=0xa5
results={}
for variant in ['mbc5','mbc3']:
 if args.variant and args.variant!=variant:continue
 for cgb in [True,False]:
  c=Cart(args.rom or ROMS[variant],cgb=cgb)
  try:
   heap=c.syms['s__HEAP_END'];sp=c.p.register_file.SP
   assert heap<sp<=0xe000,(hex(heap),hex(sp))
   # Leave the live frames above SP alone.
   c.p.memory[heap:sp-32]=[FILL]*(sp-32-heap)
   def opened(title):assert title in c.row(4),(title,c.text())
   def leave():c.leave();assert c.get('selected_test')<11
   c.go(0);c.press('a',after=120);opened('Platform');c.press('select');c.press('right');c.press('a');c.press('b',after=60);leave()
   c.go(1);c.press('a',after=60);opened('Link');c.press('down');c.press('right');c.press('start',after=90)
   for _ in range(4):c.press('right')
   c.press('a');c.press('select');c.press('b');c.press('start',after=40);leave()
   c.go(2)
   if variant=='mbc3':c.preset(1);opened('Clock');c.press('a',after=200);c.press('select');c.press('a',after=40);c.press('b',after=40)
   else:c.press('a',after=90);opened('Rumble');c.press('start',after=120);c.press('start',after=40);leave()
   c.go(3);c.preset(4);opened('Audio');c.press('a',after=120);c.press('select');c.press('right');c.press('select');c.press('b',after=40)
   c.go(4);c.preset(1);opened('Buttons');c.hold(['up','right'],30);c.tick(20);leave()
   c.go(5);c.preset(1);opened('Display');c.press('a',after=90);c.press('right',after=90);c.press('b',after=30);c.press('b',after=40)
   c.go(6);c.preset(2);opened('SRAM');c.press('a');c.press('down');c.press('a')
   for _ in range(500):
    if 'SRAM result' in c.text():break
    c.tick(8)
   assert 'SRAM result' in c.text(),c.text()
   c.press('b');c.press('b',after=40)
   c.go(7);c.preset(4);opened('Burn in');c.press('a',after=600);c.press('b',after=40);c.press('b',after=40)
   c.go(8);c.press('a',after=30);opened('Cart LED' if variant=='mbc5' else '')
   if variant=='mbc5':c.press('a',after=30);c.press('a',after=150)
   c.press('b',after=40)
   c.go(9);c.press('a',after=30);opened('Infrared')
   if cgb:c.press('down');c.press('a',after=30);c.press('a',after=150)
   c.press('b',after=40)
   c.go(10);c.preset(1);opened('Flicker');c.press('a',after=120);c.press('b',after=10);c.press('b',after=60)
   gap=bytes(c.p.memory[heap:sp-32])
   lowest=heap+next((i for i,b in enumerate(gap) if b!=FILL),len(gap))
   name=f'{variant}-{"cgb" if cgb else "dmg"}'
   results[name]={'stack_start':hex(sp),'lowest_write':hex(lowest),'depth':sp-lowest,'static_end':hex(heap)}
   print(name,results[name],flush=True)
   assert lowest>FLOOR,(name,'Stack reached the static WRAM floor',hex(lowest),hex(FLOOR))
  finally:c.close()
(ROOT/'build/stack-depth.json').write_text(json.dumps(results,indent=1)+'\n')
deepest=max(r['depth'] for r in results.values())
print(f'Deepest stack {deepest} bytes; floor {hex(FLOOR)} leaves {min(int(r["lowest_write"],16) for r in results.values())-FLOOR} bytes spare')
