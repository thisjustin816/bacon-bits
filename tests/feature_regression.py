"""Require the evidence screen, including when run against a prior ROM."""
from pathlib import Path
import sys,tempfile,shutil
from pyboy import PyBoy
rom=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'build/bacon-bits.gbc'
with tempfile.TemporaryDirectory() as td:
 f=Path(td)/'test.gbc';shutil.copy(rom,f);p=PyBoy(str(f),window='null',sound_emulated=False);p.set_emulation_speed(0)
 try:
  p.tick(240,True);p.button_press('a');p.tick(8,True);p.button_release('a');p.tick(240,True);p.button_press('select');p.tick(8,True);p.button_release('select');p.tick(90,True)
  text=''.join(chr(t+32) if t<64 else '#' for y in range(18) for t in p.memory[0,0x9800+y*32:0x9800+y*32+20])
  p.screen.image.save(Path(__file__).resolve().parents[1]/'build'/('evidence-before.png' if 'before' in rom.name else 'evidence-after.png'))
  assert 'PROBE DETAILS' in text,'SELECT does not open captured probe evidence'
  print('SELECT opens captured probe evidence')
 finally:p.stop(save=False)
