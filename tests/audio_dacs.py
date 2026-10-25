"""Audio keeps every channel's DAC on while the instrument is open.

Turning a DAC off and on pops on hardware, and PyBoy does not reproduce the
pop, so the suite reads the DAC enable bits on every frame instead: NRx2 bits
7-3 for the pulse and noise channels, and NR30 bit 7 for the wave channel.
"""
import argparse
from pathlib import Path
from cart import Cart,ROMS
a=argparse.ArgumentParser();a.add_argument('--rom',type=Path,default=ROMS['mbc5']);args=a.parse_args()

c=Cart(args.rom,sound=True)
try:
 frames=0;off=[]
 def watch(label,n=1):
  global frames
  for _ in range(n):
   c.tick();frames+=1;m=c.p.memory
   dacs={'pulse 1':m[0xff12]&0xf8,'pulse 2':m[0xff17]&0xf8,'wave':m[0xff1a]&0x80,'noise':m[0xff21]&0xf8}
   for name,on in dacs.items():
    if not on:off.append((label,frames,name))
 def press(key,label,after=24):
  c.p.button_press(key);watch(label,8);c.p.button_release(key);watch(label,after)
 # Burst check plays a triangle wave in 30-frame bursts and gaps.
 c.go(3);c.preset(4);c.tick(30);assert 'Audio' in c.row(5),c.text()
 watch('opened, silent',30)
 press('a','wave bursts',200)
 for _ in range(3):press('right','wave frequency steps')
 press('up','select voice row')
 press('right','noise bursts',120);assert c.get('tone_voice')==3
 press('right','pulse 1 bursts',120);assert c.get('tone_voice')==0
 press('down','frequency row')
 for _ in range(3):press('right','pulse frequency steps')
 press('down','level row')
 for _ in range(15):press('left','level down to 0',4)
 watch('level 0',60);assert c.get('tone_level')==0
 press('a','stopped',60);assert not c.get('tone_playing')
 press('a','restarted',60);assert c.get('tone_playing')
 assert not off,('DAC turned off',len(off),off[:8])
 print(f'All four DACs stayed on for {frames} frames of bursts, voice changes, frequency steps, level 0 and stop/start')
finally:c.close()
