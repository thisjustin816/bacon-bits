"""Audio keeps every channel's DAC on while the instrument is open.

Turning a DAC off and on pops on hardware, and PyBoy does not reproduce the
pop, so the suite reads the DAC enable bits on every frame and before every
instruction of tone_stop, tone_power and tone_apply instead: NRx2 bits 7-3 for
the pulse and noise channels, and NR30 bit 7 for the wave channel. Loading wave
RAM needs the wave DAC off, so that one window is allowed and counted.
"""
import argparse
from pathlib import Path
from cart import Cart,ROMS
a=argparse.ArgumentParser();a.add_argument('--rom',type=Path,default=ROMS['mbc5']);args=a.parse_args()

# SM83 instruction lengths: one byte unless listed here. 0xCB and its operand take two.
LENGTH=[1]*256
for op in [0x06,0x0e,0x10,0x16,0x18,0x1e,0x20,0x26,0x28,0x2e,0x30,0x36,0x38,0x3e,0xc6,0xcb,0xce,0xd6,0xde,0xe0,0xe6,0xe8,0xee,0xf0,0xf6,0xf8,0xfe]:LENGTH[op]=2
for op in [0x01,0x08,0x11,0x21,0x31,0xc2,0xc3,0xc4,0xca,0xcc,0xcd,0xd2,0xd4,0xda,0xdc,0xea,0xfa]:LENGTH[op]=3
def instructions(rom,start,end):
 """Instruction addresses from start up to end, which must fall on a boundary."""
 data=rom.read_bytes();at=start;found=[]
 while at<end:
  op=data[(at>>16)*0x4000+(at&0x3fff)];assert op not in (0xd3,0xdb,0xdd,0xe3,0xe4,0xeb,0xec,0xed,0xf4,0xfc,0xfd),('Not code',hex(at))
  found.append((at,data[(at>>16)*0x4000+(at&0x3fff):][:LENGTH[op]]));at+=LENGTH[op]
 assert at==end,('Decoding overran the next function',hex(at),hex(end))
 return found

c=Cart(args.rom,sound=True)
try:
 frames=0;off=[];armed=False;reloads=0;hooked=0;window_off=0
 def dacs():
  m=c.p.memory;return {'pulse 1':m[0xff12]&0xf8,'pulse 2':m[0xff17]&0xf8,'wave':m[0xff1a]&0x80,'noise':m[0xff21]&0xf8}
 def watch(label,n=1):
  global frames
  for _ in range(n):
   c.tick();frames+=1
   for name,on in dacs().items():
    if not on:off.append((label,frames,name))
 # Frame samples miss a DAC switched off and back on inside one call, which is
 # the pop. Hook every instruction of tone_stop, tone_power and tone_apply.
 code=instructions(args.rom,c.syms['_tone_stop'],c.syms['_burn_audio'])
 starts={at for at,_ in code};assert {c.syms['_tone_power'],c.syms['_tone_apply']}<=starts
 apply=[(at,b) for at,b in code if at>=c.syms['_tone_apply']]
 stores=[i for i,(at,b) in enumerate(apply) if b in (b'\xe0\x1a',b'\xea\x1a\xff')]
 # Loading wave RAM needs the wave DAC off. That window, from the store of 0 to
 # NR30 up to the store that turns it back on, is the only one allowed.
 assert len(stores)==2,('Expected two NR30 stores in tone_apply',[hex(apply[i][0]) for i in stores])
 # PC holds only the 16-bit address inside the bank.
 window={at&0xffff for at,_ in apply[stores[0]+1:stores[1]+1]};reload_at=apply[stores[0]][0]&0xffff
 def step(_):
  global reloads,hooked,window_off
  if not armed:return
  pc=c.p.register_file.PC;hooked+=1
  if pc==reload_at:reloads+=1
  for name,on in dacs().items():
   if on:continue
   if name=='wave' and pc in window:window_off+=1
   else:off.append(('inside a call',hex(pc),name))
 for at in starts:c.p.hook_register(at>>16,at&0xffff,step,None)
 def press(key,label,after=24):
  c.p.button_press(key);watch(label,8);c.p.button_release(key);watch(label,after)
 # Burst check plays a triangle wave in 30-frame bursts and gaps.
 c.go(3);c.preset(4);c.tick(30);assert 'Audio' in c.row(4),c.text()
 armed=True;watch('opened, silent',30)
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
 # Only the first wave play loads wave RAM; voice changes and bursts must not.
 assert reloads==1,('Wave RAM loads',reloads)
 # The hooks must have run and seen the one allowed DAC-off window, or they prove nothing.
 assert hooked>=1000 and window_off,('Instruction hooks did not observe the APU calls',hooked,window_off)
 print(f'All four DACs stayed on for {frames} frames and inside every APU call of bursts, voice changes, frequency steps, level 0 and stop/start, apart from one wave RAM load ({hooked} instructions checked)')
finally:c.close()
