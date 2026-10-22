"""Check APU writes and stereo output through SameBoy's unmodified-ROM UI."""
from pathlib import Path
import argparse,re,json
import numpy as np
from audio_navigation import select_row,lower_index
from libretro import SameBoy
ROOT=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--core',required=True,type=Path);args=a.parse_args()
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',(ROOT/'build/bacon-bits.noi').read_text(),re.M)}
p=SameBoy(args.core,ROOT/'build/bacon-bits.gbc')
def get(name,size=1):return int.from_bytes(p.read(syms['_'+name],size),'little')
def row(n):
 select_row(get,p.press,n)
def io(n):return p.read(0xff00+n)[0]
def text():
 v=p.vram();return '\n'.join(''.join(chr(t+32).upper() if t<96 else '#' for t in v[0x1800+y*32:0x1800+y*32+20]) for y in range(18))
def capture(frames=30):
 p.capture=True;p.samples.clear();p.tick(frames)
 data=np.frombuffer(b''.join(p.samples),dtype=np.int16).reshape(-1,2).astype(float)
 assert len(data)>100
 return data
checks=0
try:
 p.tick(600);p.press('right');p.press('right');p.press('right');p.press('a');p.tick(60);p.press('up');p.press('a');p.tick(60)
 assert ' 64.0 HZ' in text(),text();assert not get('tone_playing')
 p.press('a')
 for voice in range(4):
  assert get('tone_voice')==voice
  row(1)
  lower_index(get,p.press)
  count=34 if voice<3 else 60
  for index in range(count):
   if index:p.press('right')
   if voice<3:
    reg=get('tone_register',2);lo,hi=(0x13,0x14) if voice==0 else (0x18,0x19) if voice==1 else (0x1d,0x1e)
    assert io(lo)==reg&255 and io(hi)&7==reg>>8,(voice,index,reg,io(lo),io(hi))
   else:assert io(0x22)==get('tone_noise_clock')
   checks+=1
  row(2);maximum=3 if voice==2 else 15
  for level in range(maximum,-1,-1):
   if level<maximum:p.press('left')
   if voice==2:assert io(0x1c)&0x60==[0,0x60,0x40,0x20][level]
   # Bit 3 keeps the DAC on at level 0.
   else:assert io(0x12 if voice==0 else 0x17 if voice==1 else 0x21)==level<<4|8
   checks+=1
  for _ in range(maximum):p.press('right')
  if voice<3:row(0);p.press('right')
 # The real UI drives both stereo routing and the audio samples.
 row(0);p.press('right');row(1)
 lower_index(get,p.press,22)
 row(3)
 for output in [1,2,0]:
  # Every channel stays routed to the chosen sides; the samples show only the selected voice sounds.
  p.press('right');assert io(0x25)==[0xff,0xf0,0x0f][output]
  energy=np.std(capture(),axis=0)
  if output==1:assert energy[0]>1 and energy[1]<1,energy
  elif output==2:assert energy[1]>1 and energy[0]<1,energy
  else:assert min(energy)>1,energy
 p.image.save(ROOT/'build/sameboy-audio-playing.png')
 p.press('b');assert io(0x26)&0x80==0
 (ROOT/'build/sameboy-audio-results.json').write_text(json.dumps({'apu_settings_checked':checks,'stereo':'left, right, both captured','exit':'APU off'},indent=2)+'\n')
 print(f'SameBoy audio: {checks} frequency/clock/level register settings, stereo sample routing, and APU shutdown passed')
finally:p.close()
