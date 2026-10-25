"""A preset chosen with a bouncing A press must not also start the instrument.

A button bounces as it closes, so the press that picks a preset can read as
released for a moment while it is still held. The next screen must not take
that held button as a new press: Flicker must not open its full view and
Infrared must not start listening.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from cart import Cart,ROMS

def bounced_pick(c):
 """Press A on the highlighted preset, let it read released for one frame, then hold it."""
 c.p.button_press('a');c.tick(2);c.p.button_release('a');c.tick(1)
 c.p.button_press('a');c.tick(10);c.p.button_release('a');c.tick(40)

rom=Path(sys.argv[1]) if len(sys.argv)>1 else ROMS['mbc5']
failures=[]
for test,name,running,expect in ((10,'Flicker','flicker_running','FLICKER'),(9,'Infrared','ir_running','INFRARED')):
 c=Cart(rom)
 try:
  c.go(test);c.press('a');assert 'presets' in c.row(4),c.text()
  bounced_pick(c)
  if c.get(running) or expect not in c.text().upper():failures.append((name,c.get(running),c.row(4)))
 finally:c.p.stop(save=False)
assert not failures,failures
print('A bouncing preset press picks the preset without starting Flicker or Infrared')
