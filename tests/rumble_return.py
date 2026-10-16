"""A return chord must preserve rumble settings when its keys arrive in stages."""
from pathlib import Path
import argparse,sys
from libretro import SameBoy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor/rumble-pulse'))
import build
args=argparse.ArgumentParser();args.add_argument('--core',required=True,type=Path);args.add_argument('--rom',type=Path,default=ROOT/'build/bacon-bits.gbc');a=args.parse_args()
p=SameBoy(a.core,a.rom)
try:
 p.tick(600);p.press('right');p.press('right');p.press('a');p.tick(100)
 # An idle instrument must keep its completed waveform visible every frame.
 settled=p.vram()[0x1800:0x1a00]
 for frame in range(60):
  p.tick();assert p.vram()[0x1800:0x1a00]==settled,('Idle rumble redraw changed the map',frame)
 before=p.read(build.mode)[0];p.chord();p.press('b');p.tick(60);after=p.read(build.mode)[0]
 p.image.save(ROOT/'build'/('rumble-return-before.png' if 'before' in a.rom.name else 'rumble-return-after.png'))
 assert before==after,('Return chord changed the rumble mode',before,after)
 print('SameBoy return chord retains the original rumble mode')
finally:p.close()
