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
  # The graph scrolls by rewriting a 16x6 block of the map after VBlank. It
  # must finish before line 48, where the graph's first row is drawn.
  ends=[];hooked=set()
  def returned(_):ends.append(p.memory[0xff44])
  def copying(_):
   sp=p.register_file.SP;back=p.memory[sp]|p.memory[sp+1]<<8
   if back not in hooked:hooked.add(back);p.hook_register(syms['b_audio_run'] if back>=0x4000 else 0,back,returned,None)
  at=syms['_set_bkg_tiles'];p.hook_register(0,at,copying,None)
  p.tick(240,True)
  assert len(ends)>=30,('Graph copies seen in 240 frames',len(ends))
  late=[ly for ly in ends if 48<=ly<144]
  assert not late,('Graph copy still running when the graph is drawn, at lines',sorted(set(late)))
  print(f'Twelve one-frame frequency taps at different animation phases were applied; {len(ends)} graph copies ended by line {max(ly for ly in ends if ly<144)}')
 finally:p.stop(save=False)
