"""Every scenario opens editable settings; continuing preserves custom values."""
from pathlib import Path
import tempfile,re,shutil
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1]
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',(ROOT/'build/bacon-bits.noi').read_text(),re.M)}
for test in range(3,8):
 for choice in range(1,5):
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/'test.gbc';shutil.copy(ROOT/'build/bacon-bits.gbc',f);p=PyBoy(str(f),window='null',sound_emulated=True);p.set_emulation_speed(0)
   def get(n,size=1):return int.from_bytes(bytes(p.memory[syms['_'+n]:syms['_'+n]+size]),'little')
   def press(k):p.button_press(k);p.tick(8,True);p.button_release(k);p.tick(30,True)
   def text():return '\n'.join(''.join(chr(t+32).upper() if t<96 else '#' for t in p.memory[0,0x9800+y*32:0x9800+y*32+20]) for y in range(18))
   try:
    p.tick(240,True)
    for _ in range(test):press('right')
    press('a');p.tick(60,True);assert 'PRESETS' in text() and 'MANUAL' in text()
    for _ in range(choice-1):press('down')
    press('a');p.tick(60,True);assert 'PRESETS' not in text()
    if test==3:
     assert get('tone_voice')==[2,0,0,2][choice-1] and not get('tone_playing')
     if choice==1:assert get('tone_index')==0 and get('tone_level')==3
     if choice==3:assert get('tone_output')==1 and get('tone_level')==8
     if choice==4:assert get('tone_on')==30 and get('tone_gap')==30
     press('right');custom=get('tone_index');press('b');press('a');assert 'CONTINUE' in text();press('a');assert get('tone_index')==custom
    elif test==4:
     assert get('button_page')==[0,2,2,3][choice-1] and get('button_units')==(choice==3)
    elif test==5:
     assert get('display_pattern')==[2,4,5,6][choice-1] and not get('display_running')
    elif test==6:
     assert get('ram_mode')==[0,1,2,1][choice-1] and get('ram_pattern')==[6,6,4,7][choice-1] and not get('ram_stage')
    else:
     assert not get('burn_running')
     if choice==3:assert 'PULSE' in text() and 'RUMBLE F' in text()
    if test!=3:assert not p.memory[0xff26]&0x80
    if test==7 and choice==1:
     press('a')
     for _ in range(1500):
      p.tick(8,True)
      if not get('burn_running'):break
     assert not get('burn_running') and get('burn_seconds',4)==60 and not get('burn_errors',4),(get('burn_seconds',4),get('burn_errors',4))
   finally:p.stop(save=False)
# Link: each preset sets every setting but the role, and Continue keeps a
# masked-lines value set by hand.
LINK={1:dict(profile=4,rate_mode=1,fast=0,double_cpu=0,masked_step=0),2:dict(profile=0,rate_mode=0,fast=0,double_cpu=0,masked_step=0),
      3:dict(profile=4,rate_mode=2,fast=1,double_cpu=1,masked_step=0),4:dict(profile=4,rate_mode=1,fast=0,double_cpu=0,masked_step=4)}
for choice,want in LINK.items():
 with tempfile.TemporaryDirectory() as td:
  f=Path(td)/'test.gbc';shutil.copy(ROOT/'build/bacon-bits.gbc',f);p=PyBoy(str(f),window='null',sound_emulated=True);p.set_emulation_speed(0)
  def get(n,size=1):return int.from_bytes(bytes(p.memory[syms['_'+n]:syms['_'+n]+size]),'little')
  def put(n,v):p.memory[syms['_'+n]]=v
  def press(k):p.button_press(k);p.tick(8,True);p.button_release(k);p.tick(30,True)
  def text():return '\n'.join(''.join(chr(t+32).upper() if t<96 else '#' for t in p.memory[0,0x9800+y*32:0x9800+y*32+20]) for y in range(18))
  try:
   p.tick(240,True);press('right');press('a');p.tick(60,True);assert 'LINK PRESETS' in text() and 'MANUAL' in text(),text()
   # A Custom pacing and a role left from earlier must not survive a preset.
   put('host',0);put('rate_mode',3);put('burst_len',9);put('idle_step',2);put('masked_step',7)
   for _ in range(choice-1):press('down')
   press('a');p.tick(60,True);assert 'LINK SETUP' in text(),text()
   got={n:get(n) for n in want};assert got==want,(choice,got,want)
   assert get('burst_len')==4 and get('idle_step')==6 and get('host')==0,(choice,get('burst_len'),get('idle_step'),get('host'))
   if choice==4:
    for k in ('a','b','start','select'):p.button_press(k)
    p.tick(70,True)
    for k in ('a','b','start','select'):p.button_release(k)
    p.tick(30,True);press('down');press('a');p.tick(40,True)
    press('a');p.tick(60,True);assert 'CONTINUE' in text(),text()
    put('masked_step',2);press('a');p.tick(60,True);assert get('masked_step')==2 and get('rate_mode')==1
  finally:p.stop(save=False)
print('Twenty presets: expected scenario settings, no automatic playback/writes, and CONTINUE keeps customized audio values; '
      'Link presets set every setting but the role, and CONTINUE keeps a hand-set masked value')
