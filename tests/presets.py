"""Every scenario opens editable settings; continuing preserves custom values."""
from pathlib import Path
import tempfile,re,shutil
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1]
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',(ROOT/'build/bacon-bits.noi').read_text(),re.M)}
for test in range(3,8):
 for choice in range(1,5):
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/'test.gbc';shutil.copy(ROOT/'build/bacon-bits.gbc',f);p=PyBoy(str(f),window='null',sound_emulated=False);p.set_emulation_speed(0)
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
print('Twenty presets: expected scenario settings, no automatic playback/writes, and CONTINUE keeps customized audio values')
