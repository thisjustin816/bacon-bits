"""Check hardware-test graphics and clock writes with SameBoy's bus and PPU."""
from pathlib import Path
import argparse,re
from libretro import SameBoy
ROOT=Path(__file__).resolve().parents[1];a=argparse.ArgumentParser();a.add_argument('--core',required=True,type=Path);args=a.parse_args()
for variant,rom in [('mbc5',ROOT/'build/bacon-bits.gbc'),('mbc3',ROOT/'build/mbc3/bacon-bits.gbc')]:
 syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',rom.with_suffix('.noi').read_text(),re.M)}
 p=SameBoy(args.core,rom)
 def get(n,size=1):return int.from_bytes(p.read(syms['_'+n],size),'little')
 def text():
  v=p.vram();return '\n'.join(''.join(chr(t+32).upper() if t<96 else '#' for t in v[0x1800+y*32:0x1814+y*32]) for y in range(18))
 def go(n):
  for _ in range(12):
   if get('selected_test')==n:break
   p.press('right')
  assert get('selected_test')==n;p.press('a');p.tick(90)
 try:
  p.tick(600)
  if variant=='mbc3':
   go(2);assert 'RTC PRESETS' in text();p.press('down');p.press('down');p.press('a');p.press('a');assert 'CONFIRM' in text();p.press('down');p.press('a');assert get('rtc_dirty') and get('rtc_data',5).to_bytes(5,'little')[4]&64
   frozen=p.read(syms['_rtc_data'],5);p.tick(180);assert p.read(syms['_rtc_data'],5)==frozen and not get('rtc_halt_errors',2)
   p.image.save(ROOT/'build/sameboy-rtc.png');p.press('b');assert not get('rtc_dirty');go(8);assert 'MBC5 RGB CART' in text();p.press('b')
  else:
   go(8);p.press('a');assert not get('led_active');p.press('a');assert get('led_active');p.tick(90);assert len(p.image.getcolors(65536))>4;p.image.save(ROOT/'build/sameboy-led.png');p.press('b');assert not get('led_active')
  go(9);p.press('down');p.press('a');p.press('a');p.tick(120);assert get('ir_running') and get('ir_bursts',2)>1
  p.image.save(ROOT/'build'/f'sameboy-ir-{variant}.png');p.press('b');assert not get('ir_running') and not get('bb_fast')
  print(f'SameBoy {variant}: shared graphics, palette output, guarded mapper outputs, IR bursts and cleanup'+(', confirmed RTC halt / restore' if variant=='mbc3' else ''))
 finally:p.close()
