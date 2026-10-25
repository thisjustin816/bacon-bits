"""Burn In motor pulses last the set number of frames once per second at every load."""
import argparse,re
from pathlib import Path
from libretro import SameBoy
ROOT=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--core',required=True,type=Path);a.add_argument('--rom',type=Path,default=ROOT/'build/bacon-bits.gbc');args=a.parse_args()
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',args.rom.with_suffix('.noi').read_text(),re.M)}
LOADS=['Light','Medium','High']
results=[]
for load in LOADS:
 for frames in (1,6):
  p=SameBoy(args.core,args.rom)
  def get(name):return p.read(syms['_'+name])[0]
  def row(y):v=p.vram();return ''.join(chr(t+32) if t<96 else '#' for t in v[0x1800+y*32:0x1814+y*32])
  try:
   p.tick(600)
   while get('selected_test')!=7:p.press('right')
   p.press('a');p.tick(30);p.press('down');p.press('down');p.press('a');p.tick(30)  # Output load
   assert 'Rumble f' in row(9),row(9)
   p.press('down')
   for _ in range(frames-1):p.press('right')
   p.press('select');p.press('down')
   while LOADS[[l in row(9) for l in LOADS].index(True)]!=load:p.press('left')
   p.transitions.clear();p.press('a');start=p.frame;p.tick(600)
   edges=[(frame-start,on) for frame,on in p.transitions if frame>start+60]
   pulses=[off-on_at for (on_at,on),(off,_) in zip(edges,edges[1:]) if on]
   starts=[frame for frame,on in edges if on];periods=[b-a for a,b in zip(starts,starts[1:])]
   assert len(pulses)>=7,(load,frames,'Too few motor pulses in ten seconds',edges)
   assert all(abs(width-frames)<=1 for width in pulses),(load,frames,'Pulse widths',pulses)
   assert all(abs(period-60)<=1 for period in periods),(load,frames,'Pulse spacing',periods)
   p.press('b');p.tick(30)
   assert not p.transitions or not p.transitions[-1][1],'Motor left running after Burn In stopped'
   results.append(f'{load} {frames}f')
  finally:p.close()
print('Burn In motor pulses match the set frames once a second:',', '.join(results))
