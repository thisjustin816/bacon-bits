"""Deliver a serial interrupt while the graphical renderer maps another bank.

PyBoy reads SB as $FF with no cable, so the test stands in for a received
byte by setting A to $3C just after the interrupt handler reads SB. The ring
slot is planted with another value first, so only the handler's store of the
byte it read can leave $3C there.
"""
from pathlib import Path
from pyboy import PyBoy
import re,shutil,tempfile,sys
ROOT=Path(__file__).resolve().parents[1];rom=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'build/bacon-bits.gbc'
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',rom.with_suffix('.noi').read_text(),re.M)}
BYTE,PLANTED=0x3c,0xa5
# The handler must sit in bank 0; find its LDH A,(SB).
isr=syms['_serial_isr'];code=rom.read_bytes()
assert isr<0x4000,('The serial interrupt is not in the fixed bank',hex(isr))
read_sb=code.find(b'\xf0\x01',isr,isr+64)
assert read_sb>=0,'The serial interrupt never reads SB with LDH A,(SB)'
with tempfile.TemporaryDirectory() as td:
 f=Path(td)/'serial.gbc';shutil.copy(rom,f);p=PyBoy(str(f),window='null',sound_emulated=False);p.set_emulation_speed(0);injected=[];banks=[]
 def press(k):p.button_press(k);p.tick(8,True);p.button_release(k);p.tick(24,True)
 def get(n):return p.memory[syms['_'+n]]
 def interrupt(_):
  if get('running') and not injected:
   slot=get('wr');injected.append(slot);p.memory[syms['_ring']+slot]=PLANTED;p.memory[0xff0f]|=8
 def received(_):
  if injected and not banks:
   banks.append(p.memory[syms['__current_bank']]);p.register_file.A=BYTE
 try:
  p.tick(240,True)
  if get('selected_test')==0:press('right');press('a');press('a')
  press('left');press('down');press('right');assert not get('host') and get('profile')==0
  a=syms['_ui_scene'];p.hook_register(a>>16,a&65535,interrupt,None);p.hook_register(0,read_sb+2,received,None)
  press('start');p.tick(60,True)
  assert injected,'The graphical bank was never reached during serial operation'
  assert banks==[syms['b_ui_scene']],('The serial interrupt did not run while the renderer mapped its bank',banks,syms['b_ui_scene'])
  slot=injected[0]
  assert get('wr')==(slot+1)&127 and p.memory[syms['_ring']+slot]==BYTE,('Serial interrupt did not queue the byte it read',get('wr'),slot,hex(p.memory[syms['_ring']+slot]))
  assert get('running') and get('first_code')==0
  print(f'Injected SIO while the renderer mapped bank {banks[0]}: fixed-bank ISR queued the byte it read and the link test kept running')
 finally:p.stop(save=False)
