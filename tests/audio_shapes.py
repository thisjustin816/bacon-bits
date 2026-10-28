"""Check every waveform, raw divisor stepping, and timed playback through the UI."""
from pathlib import Path
import re,tempfile,shutil
import numpy as np
from pyboy import PyBoy
from audio_navigation import select_row
from audio_expected import WAVES
ROOT=Path(__file__).resolve().parents[1]
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',(ROOT/'build/bacon-bits.noi').read_text(),re.M)}
with tempfile.TemporaryDirectory() as td:
 f=Path(td)/'test.gbc';shutil.copy(ROOT/'build/bacon-bits.gbc',f);p=PyBoy(str(f),window='null',sound_emulated=True);p.set_emulation_speed(0)
 def get(n,size=1):return int.from_bytes(bytes(p.memory[syms['_'+n]:syms['_'+n]+size]),'little')
 def press(k):p.button_press(k);p.tick(8,True);p.button_release(k);p.tick(24,True)
 def row(n):
  select_row(get,press,n)
 try:
  p.tick(240,True)
  for _ in range(3):press('right')
  press('a');p.tick(60,True);press('up');press('a');p.tick(60,True);press('a')
  waveforms=[]
  for voice in range(4):
   assert get('tone_voice')==voice
   press('select');row(0)
   limit=4 if voice<2 else 6 if voice==2 else 2
   shapes=[]
   for _ in range(limit):
    shape=p.memory[syms['_tone_shape']+voice];shapes.append(shape)
    if voice<2:assert p.memory[0xff11 if voice==0 else 0xff16]>>6==shape,(voice,shape,p.memory[0xff11 if voice==0 else 0xff16],get("tone_playing"),get("audio_page"))
    elif voice==2:
     # Stop mutes the wave channel with its DAC on, and wave RAM reads back
     # only while the channel is off, so the harness turns the DAC off to read it.
     press('a');assert p.memory[0xff1a]&0x80 and not p.memory[0xff1c]&0x60
     p.memory[0xff1a]=0;samples=bytes(p.memory[0xff30:0xff40]);p.memory[0xff1a]=0x80;waveforms.append(samples);press('a')
     assert samples==WAVES[shape],(shape,'wave RAM',samples.hex(),WAVES[shape].hex())
    else:assert bool(p.memory[0xff22]&8)==bool(shape)
    press('right')
   assert set(shapes)==set(range(limit)),shapes
   if voice<3:
    row(1);press('right');assert get('tone_fine')
    press('select');row(1);before=get('tone_register',2);press('right');assert get('tone_register',2)==before+1;press('left');assert get('tone_register',2)==before
    press('select');row(1);press('right');assert not get('tone_fine');press('select')
   else:press('select')
   row(0);press('right')
  assert len(set(waveforms))==6
  # Pulse, thirty-frame burst with a thirty-frame gap; poll every frame.
  press('select');row(2)
  for _ in range(30):press('right')
  row(3)
  for _ in range(30):press('right')
  assert get('tone_on')==30 and get('tone_gap')==30
  if not get('tone_playing'):press('a')
  gates=[];levels=[]
  for _ in range(200):p.tick(1,True);gates.append(get('tone_gate'));levels.append(float(np.std(p.sound.ndarray.astype(float))))
  assert 0 in gates and 1 in gates
  edges=[i for i in range(1,len(gates)) if gates[i]!=gates[i-1]]
  assert len(edges)>=4 and all(30<=b-a<=35 for a,b in zip(edges,edges[1:])),edges
  # The samples must follow the gate. Skip the two frames after each edge,
  # which hold the change part way through.
  steady=[i for i in range(2,len(gates)) if gates[i]==gates[i-1]==gates[i-2]]
  loud=[i for i in steady if gates[i] and levels[i]<0.1];heard=[i for i in steady if not gates[i] and levels[i]>=0.1]
  assert not loud and not heard,('Burst samples do not follow the gate: silent while on',loud[:8],'audible while resting',heard[:8],[round(levels[i],2) for i in heard[:8]])
  press('b');assert not p.memory[0xff26]&0x80
  print('Audio: eight pulse duties, six exact wave RAM patterns, two noise widths, single-register fine steps, timed bursts with silent gaps, and safe exit passed')
 finally:p.stop(save=False)
