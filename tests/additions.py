"""Exercise detailed diagnostics and fault cases on the compiled cartridge."""
from pathlib import Path
import tempfile,shutil,re,json,sys
import numpy as np
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1]
rom=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'build/bacon-bits.gbc'
pattern_bytes=(4 if rom.read_bytes()[0x147]==0x10 else 8)*8192-32
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',rom.with_suffix('.noi').read_text(),re.M)}
def run(cgb):
 with tempfile.TemporaryDirectory() as td:
  path=Path(td)/'test.gbc';shutil.copy(rom,path)
  p=PyBoy(str(path),window='null',sound_emulated=False,cgb=cgb);p.set_emulation_speed(0)
  def get(n,size=1):return int.from_bytes(bytes(p.memory[syms['_'+n]:syms['_'+n]+size]),'little')
  def press(k,n=8):p.button_press(k);p.tick(n,True);p.button_release(k);p.tick(16,True)
  def text():return '\n'.join(''.join(chr(t+32).upper() if t<96 else '#' for t in p.memory[0,0x9800+y*32:0x9800+y*32+20]) for y in range(18))
  def launch(n):
   for _ in range(16):
    if get('selected_test')==n:break
    press('right')
   else:raise AssertionError(('Could not reach browser',text()))
   press('a');p.tick(60,True)
   if n>=3:press('up');press('a');p.tick(60,True)
  def wait(n,pred):
   for _ in range(n):
    p.tick(8,True)
    if pred():p.tick(40,True);return
   raise AssertionError(text())
  try:
   p.tick(240,True);launch(0);p.tick(180,True)
   before=bytes(p.memory[0,0x9800:0x9a40]);press('select')
   assert 'PROBE DETAILS' in text(),'Platform evidence view absent\n'+text()
   if cgb:
    assert get('pd_obs',48).to_bytes(48,'little')[32]==0xfb
    press('a') # all probes
    for _ in range(12):assert 'EXPECT' in text() and 'READ' in text();press('right')
    press('select');assert 'NAME EVIDENCE' in text() and 'PYBOY' in text()
   else:assert 'NO CGB READINGS' in text()
   press('b');p.tick(90,True);assert all(before[y*32:y*32+20]==bytes(p.memory[0,0x9800+y*32:0x9800+y*32+20]) for y in range(18)),'Platform summary map changed'
   for k in ['a','b','select','start']:p.button_press(k)
   p.tick(8,True)
   for k in ['a','b','select','start']:p.button_release(k)
   p.tick(16,True);press('down');press('a')
   launch(4);assert all(label in text() for label in ['BUTTONS','SELECT','START','HELD']),'Initial button view was blank';base=get('button_presses',32).to_bytes(32,'little');press('a',12)
   counts=get('button_presses',32).to_bytes(32,'little');assert int.from_bytes(counts[16:20],'little')==int.from_bytes(base[16:20],'little')+1
   assert int.from_bytes(bytes(p.memory[syms['_button_longest']+8:syms['_button_longest']+10]),'little')>=12
   p.button_press('right');p.tick(1,True);p.button_release('right');p.tick(8,True)
   assert get('button_short',4)>=1,'A one-frame sampled press was not counted'
   press('select');press('select');assert 'HOLD FR' in text();press('a');assert 'HOLD MS' in text()
   press('start');assert 'CONFIRM' in text();press('a');assert get('button_presses',32)!=0,'NO default cleared counters'
   for k in ['a','b','select','start']:p.button_press(k)
   p.tick(100,True)
   for k in ['a','b','select','start']:p.button_release(k)
   p.tick(16,True);press('down');press('a');launch(5)
   for pattern in range(7):
    assert get('display_pattern')==pattern
    press('a');wait(100,lambda:get('display_ready'))
    assert get('display_running') and len(p.screen.image.getcolors(65536))>=1
    if pattern==4:assert len(p.screen.image.getcolors(65536))==(32 if cgb else 4),p.screen.image.getcolors(65536)
    p.screen.image.save(ROOT/'build'/f'display-{cgb}-{pattern}.png')
    press('b');press('right')
   press('b');launch(6);press('a');assert 'UNKNOWN' in text(),text();press('b')
   press('right');press('a');assert 'CONFIRM' in text();press('a');assert not get('ram_stage'),'NO default started destructive test'
   press('a');press('down');press('a');wait(500,lambda:'SRAM RESULT' in text())
   assert 'PASS' in text() and get('ram_checked',4)==pattern_bytes,(text(),get('ram_checked',4))
   # A real emulator battery file, followed by a fresh machine instance.
   p.stop(save=True);p=PyBoy(str(path),window='null',sound_emulated=False,cgb=cgb);p.set_emulation_speed(0);p.tick(240,True);launch(6)
   press('a');wait(400,lambda:'SRAM RESULT' in text());assert 'PASS' in text(),text()
   p.memory[3,0xa123]^=0x40;press('b');press('a');wait(400,lambda:'SRAM RESULT' in text())
   assert 'FAIL' in text() and get('ram_errors',4)==1
   assert get('ram_first_bank')==3 and get('ram_first_address',2)==0x123
   p.memory[3,0xa123]^=0x40
   saved=bytes(p.memory[1,0xa000:0xa010]);p.memory[1,0xa000:0xa010]=list(p.memory[0,0xa000:0xa010])
   press('b');press('a');wait(400,lambda:'SRAM RESULT' in text())
   assert get('ram_errors',4)==16 and get('ram_first_bank')==1 and get('ram_first_address',2)==0
   p.memory[1,0xa000:0xa010]=list(saved);p.memory[0,0xbfef]^=1
   press('b');press('a');assert 'UNKNOWN' in text() and get('ram_checked',4)==0

   press('b');press('b');launch(7);press('a');wait(800,lambda:get('burn_cycles',4)>=1)
   assert get('burn_errors',4)==0,(get('burn_errors',4),get('burn_first_kind'))
   press('b');assert not get('burn_running') and not p.memory[0xff26]&0x80
   print(('CGB' if cgb else 'DMG')+': probe evidence, button counters, seven display patterns, 32-step ramp, SRAM confirmation/power cycle/data fault/bank tags/record corruption and ROM burn cycle passed',flush=True)
  finally:p.stop(save=False)
for cgb in [True,False]:run(cgb)
