"""A CONTINUE choice must consume the buttons used to open the modal."""
from pathlib import Path
import tempfile,shutil,re,sys
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1]
rom=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'build/bacon-bits.gbc'
noi=rom.with_suffix('.noi')
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',noi.read_text(),re.M)}
with tempfile.TemporaryDirectory() as td:
 f=Path(td)/'test.gbc';shutil.copy(rom,f)
 p=PyBoy(str(f),window='null',sound_emulated=False);p.set_emulation_speed(0)
 def press(k):p.button_press(k);p.tick(8,True);p.button_release(k);p.tick(20,True)
 def chord():
  for k in ['a','b','start','select']:p.button_press(k)
  p.tick(8,True)
  for k in ['a','b','start','select']:p.button_release(k)
  p.tick(20,True)
 try:
  p.tick(240,True);press('right');press('a');p.tick(60,True);press('a');p.tick(120,True)
  assert p.memory[syms['_running']]==0
  chord();press('b');p.tick(90,True)
  p.screen.image.save(ROOT/'build/modal-regression-link.png')
  assert p.memory[syms['_running']]==0,'CONTINUE replayed START and started Link Sustain'
  chord();press('down');press('a');press('right');press('a');p.tick(120,True)
  chord();press('b');p.tick(90,True)
  p.screen.image.save(ROOT/'build/modal-regression-rumble.png')
  assert p.memory[0xc011]==0,'CONTINUE replayed START and started Rumble Pulse'
  print('CONTINUE consumes the chord in Link Sustain and Rumble Pulse')
 finally:p.stop(save=False)
