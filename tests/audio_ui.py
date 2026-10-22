"""Exercise audio controls through the unmodified cartridge's UI in PyBoy."""
from pathlib import Path
from fractions import Fraction
import re,json,tempfile,shutil,sys
import numpy as np
from audio_navigation import select_row,lower_index
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1]
rom=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'build/bacon-bits.gbc'
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',rom.with_suffix('.noi').read_text(),re.M)}
def shown(hundredths):
 # The front page prints at most five characters: 0.1 Hz below 1 kHz, whole Hz, then kHz.
 if hundredths>=10000000:return f'{hundredths//100000}k Hz'
 if hundredths>=100000:return f'{hundredths//100} Hz'
 return f'{hundredths//100}.{hundredths%100//10} Hz'
def text(p):return '\n'.join(''.join(chr(t+32).upper() if t<96 else '#' for t in p.memory[0,0x9800+y*32:0x9800+y*32+20]) for y in range(18))
with tempfile.TemporaryDirectory() as td:
 f=Path(td)/'test.gbc';shutil.copy(rom,f)
 p=PyBoy(str(f),window='null',sound_emulated=True);p.set_emulation_speed(0)
 def get(name,size=1):return int.from_bytes(bytes(p.memory[syms['_'+name]:syms['_'+name]+size]),'little')
 def press(k):p.button_press(k);p.tick(8,True);p.button_release(k);p.tick(12,True)
 def row(n):
  select_row(get,press,n)
 def record(frames):
  chunks=[]
  for _ in range(frames):p.tick(1,True);chunks.append(p.sound.ndarray.copy())
  return np.concatenate(chunks,axis=0).astype(float)
 try:
  p.tick(240,True);press('right');press('right');press('right');press('a');p.tick(60,True);press('up');press('a');p.tick(60,True)
  assert ' 64.0 HZ' in text(p),text(p)
  assert 'SILENT' in text(p) and get('tone_playing')==0
  press('a');assert 'PLAYING' in text(p)
  endpoints=[]
  for voice in range(4):
   assert get('tone_voice')==voice
   row(1)
   lower_index(get,press)
   count=34 if voice<3 else 60
   first=get('tone_hundredths',4)
   assert first==(6400 if voice<2 else 3200 if voice<3 else 457)
   for i in range(1,count):
    before=get('tone_hundredths',4);press('right')
    assert get('tone_index')==i and get('tone_hundredths',4)>before,(voice,i,get('tone_index'),get('audio_row'),get('audio_page'))
   last=get('tone_hundredths',4)
   assert last==(13107200 if voice<2 else 6553600 if voice<3 else 52428800)
   assert shown(last).upper() in text(p),(shown(last),text(p))
   press('right');assert get('tone_index')==count-1,'Stepping past the end wrapped to an unexpected pitch'
   endpoints.append({'voice':voice,'first_hundredths':first,'last_hundredths':last,'steps':count})
   row(2);maximum=3 if 2<=voice<3 else 15
   for level in range(maximum-1,-1,-1):press('left');assert get('tone_level')==level
   assert np.std(record(5))<0.1,'Zero level produced audio samples'
   for level in range(1,maximum+1):press('right');assert get('tone_level')==level
   if voice<3:row(0);press('right')
  # Use a midrange pulse for independent stereo sample checks.
  row(0);press('right');row(1)
  lower_index(get,press,22)
  row(3)
  for expected in [1,2,0]:
   press('right');assert get('tone_output')==expected
   audio=record(20);energy=np.std(audio,axis=0)
   if expected==0:assert min(energy)>0.1,energy
   elif expected==1:assert energy[0]>0.1 and energy[1]<0.1,energy
   else:assert energy[1]>0.1 and energy[0]<0.1,energy
  p.screen.image.save(ROOT/'build/audio-playing.png')
  press('b');assert get('tone_playing')==0 and p.memory[0xff26]&0x80==0
  assert 'BACON BIT BENCH' in text(p)
  # Platform detection must still find an idle APU after playing every voice.
  press('left');press('left');press('left');press('a');p.tick(180,True)
  assert p.memory[0xff76]==0 and p.memory[0xff77]==0
  (ROOT/'build/audio-ui-results.json').write_text(json.dumps(endpoints,indent=2)+'\n')
  print('Audio UI: exact displayed endpoints, 34/60 steps, every level, clamps, stereo samples, safe exit, and idle APU passed')
 finally:p.stop(save=False)
