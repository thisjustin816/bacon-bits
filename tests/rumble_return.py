"""A return chord must preserve rumble settings when its keys arrive in stages."""
from pathlib import Path
import argparse,sys
from libretro import SameBoy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor/rumble-pulse'))
import build
args=argparse.ArgumentParser();args.add_argument('--core',required=True,type=Path);args.add_argument('--rom',type=Path,default=ROOT/'build/bacon-bits.gbc');a=args.parse_args()
# Every setting the instrument keeps between runs: pattern, cursor, bit length, mode,
# prespin, unit, frame length, run bits, gap bits and preset.
SETTINGS=[build.pattern,build.cursor,build.blen_ms,build.mode,build.prespin,build.unit,build.blen_fr,build.duration,build.gap,build.presetn]
p=SameBoy(a.core,a.rom)
def text():
 v=p.vram();return '\n'.join(''.join(chr(t+32).upper() if t<96 else '#' for t in v[0x1800+y*32:0x1800+y*32+20]) for y in range(18))
def settings():return [p.read(at)[0] for at in SETTINGS]
try:
 p.tick(600);p.press('right');p.press('right');p.press('a');p.tick(100)
 # An idle instrument must keep its completed waveform visible every frame.
 settled=p.vram()[0x1800:0x1a00]
 for frame in range(60):
  p.tick();assert p.vram()[0x1800:0x1a00]==settled,('Idle rumble redraw changed the map',frame)
 # Leave the default mode so a reset to defaults cannot pass for a kept setting.
 p.press('b');p.tick(20);assert p.read(build.mode)[0]==1,('B did not select the next mode',p.read(build.mode)[0])
 # B alone changes the mode, Select alone nothing and Start alone runs the motor.
 # Each key is held for ten frames before the rest of the chord.
 for first in ['b','select','start']:
  before=settings()
  p.held={p.BUTTONS[first]};p.tick(10);p.held={p.BUTTONS[k] for k in ('a','b','select','start')}
  for _ in range(60):
   p.tick()
   if 'CONTINUE' in text():break
  else:raise AssertionError((first,'first: the return dialog never opened',text()))
  p.held=set();p.tick(12);p.press('b');p.tick(60);after=settings()
  assert before==after,(first,'first: the return chord changed rumble settings',before,after)
  assert not p.transitions or not p.transitions[-1][1],(first,'first: the motor was left running',p.transitions[-4:])
 p.image.save(ROOT/'build'/('rumble-return-before.png' if 'before' in a.rom.name else 'rumble-return-after.png'))
 print('SameBoy return chord retains every rumble setting with B, Select or Start held first')
finally:p.close()
