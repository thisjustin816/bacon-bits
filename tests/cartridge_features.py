"""Exercise compiled RGB commands, infrared controls and both mapper menus."""
from pathlib import Path
import json,re,shutil,tempfile,sys
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1]
rom=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'build/bacon-bits.gbc'
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',rom.with_suffix('.noi').read_text(),re.M)}
with tempfile.TemporaryDirectory() as td:
 f=Path(td)/'hardware.gbc';shutil.copy(rom,f);p=PyBoy(str(f),window='null',sound_emulated=False);p.set_emulation_speed(0)
 def get(n,size=1):return int.from_bytes(bytes(p.memory[syms['_'+n]:syms['_'+n]+size]),'little')
 def press(k):p.button_press(k);p.tick(8,True);p.button_release(k);p.tick(20,True)
 def text():return '\n'.join(''.join(chr(t+32).upper() if t<96 else '#' for t in p.memory[0,0x9800+y*32:0x9814+y*32]) for y in range(18))
 def go(n):
  for _ in range(12):
   if get('selected_test')==n:break
   press('right')
  assert get('selected_test')==n,('Missing cartridge test',n,get('selected_test'))
 try:
  p.tick(240,True);go(8);press('a');assert 'LED PRESETS' in text(),text()
  # Find actual write instructions relative to the compiled banked function.
  addr=syms['_led_send'];bank=addr>>16;base=addr&65535;data=rom.read_bytes();at=bank*16384+base-0x4000;code=data[at:at+128]
  start=code.index(b'\x21\x00\x60\x36\x08\x36\x00')+3
  bit_at=code.index(b'\x21\x00\x60\x70\x36\x00')+3
  end=code.rindex(b'\x21\x00\x60\x36\x08')+3
  transactions=[];bits=[];starts=[]
  def begin(_):starts.append(p.register_file.PC);bits.clear()
  def bit(_):bits.append(p.register_file.B)
  def finish(_):transactions.append(tuple(bits))
  p.hook_register(bank,base+start,begin,None);p.hook_register(bank,base+bit_at,bit,None);p.hook_register(bank,base+end,finish,None)
  press('a');assert not transactions and not get('led_active'),'Choosing a preset enabled the LED'
  press('a');assert get('led_active') and transactions[0]==tuple([6]*8+[2]*16),transactions
  p.tick(130,True);assert tuple([2]*8+[6]*8+[2]*8) in transactions and tuple([2]*16+[6]*8) in transactions
  press('b');assert transactions[-1]==tuple([2]*24) and not get('led_active'),'LED did not receive OFF on exit'
  go(9);press('a');assert 'IR PRESETS' in text();press('down');press('a');assert 'INFRARED' in text() and not get('ir_running')
  assert get('ir_on')==2 and get('ir_off')==3 and get('ir_pulses')==32
  press('a');p.tick(90,True);assert get('ir_running');press('select');assert 'ON US' in text();before=get('ir_on');press('right');assert get('ir_on')==before+1
  press('b');assert not get('ir_running') and not p.memory[0xff4d]&128
  p.screen.image.save(ROOT/'build/cartridge-features.png')
  print('Actual ROM: 24-bit RGB order and MSB-first levels, no automatic output, three primary commands, LED-off cleanup, IR presets, granular timing and exit passed')
 finally:p.stop(save=False)
