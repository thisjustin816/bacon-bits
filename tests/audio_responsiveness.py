"""One-frame frequency taps must survive the animated audio instrument."""
from pathlib import Path
import re,shutil,tempfile,sys
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1];rom=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'build/bacon-bits.gbc'
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',rom.with_suffix('.noi').read_text(),re.M)}
with tempfile.TemporaryDirectory() as td:
 f=Path(td)/'taps.gbc';shutil.copy(rom,f);p=PyBoy(str(f),window='null',sound_emulated=False);p.set_emulation_speed(0)
 def press(k):p.button_press(k);p.tick(8,True);p.button_release(k);p.tick(24,True)
 try:
  p.tick(240,True)
  for _ in range(3):press('right')
  press('a');press('up');press('a');press('a');p.tick(120,True)
  for phase in range(12):
   p.tick(phase+1,True);before=p.memory[syms['_tone_index']];p.button_press('right');p.tick(1,True);p.button_release('right');p.tick(4,True)
   p.screen.image.save(ROOT/'build'/f'audio-tap-{"before-" if len(sys.argv)>1 else ""}{phase}.png')
   assert p.memory[syms['_tone_index']]==before+1,('A one-frame frequency tap was dropped',phase,before,p.memory[syms['_tone_index']])
  print('Twelve one-frame frequency taps at different animation phases were applied')
 finally:p.stop(save=False)
