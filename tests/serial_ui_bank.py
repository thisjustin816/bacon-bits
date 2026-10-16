"""Deliver a serial interrupt while the graphical renderer maps another bank."""
from pathlib import Path
from pyboy import PyBoy
import re,shutil,tempfile,sys
ROOT=Path(__file__).resolve().parents[1];rom=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'build/bacon-bits.gbc'
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',rom.with_suffix('.noi').read_text(),re.M)}
with tempfile.TemporaryDirectory() as td:
 f=Path(td)/'serial.gbc';shutil.copy(rom,f);p=PyBoy(str(f),window='null',sound_emulated=False);p.set_emulation_speed(0);injected=[]
 def press(k):p.button_press(k);p.tick(8,True);p.button_release(k);p.tick(24,True)
 def get(n):return p.memory[syms['_'+n]]
 def interrupt(_):
  if get('running') and not injected:
   injected.append(get('wr'));p.memory[0xff02]=0;p.memory[0xff01]=0x3c;injected.append(p.memory[0xff01]);p.memory[0xff0f]|=8
 try:
  p.tick(240,True)
  if get('selected_test')==0:press('right');press('a')
  press('left');press('down');press('right');assert not get('host') and get('profile')==0
  a=syms['_ui_scene'];p.hook_register(a>>16,a&65535,interrupt,None);press('start');p.tick(60,True)
  assert injected,'The graphical bank was never reached during serial operation'
  assert get('wr')==injected[0]+1 and p.memory[syms['_ring']+injected[0]]==injected[1],('Serial interrupt did not reach its ring buffer',get('wr'),injected,p.memory[syms['_ring']+injected[0]])
  assert get('running') and get('first_code')==0
  print('Injected SIO while the renderer mapped bank 6: fixed-bank ISR queued the byte and the link test kept running')
 finally:p.stop(save=False)
