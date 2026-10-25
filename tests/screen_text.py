"""Settings rows, counters and footers must read cleanly after every redraw."""
import argparse,re
from pathlib import Path
from cart import Cart,ROMS
a=argparse.ArgumentParser();a.add_argument('--rom',type=Path,default=ROMS['mbc5']);a.add_argument('--mbc3',type=Path,default=ROMS['mbc3']);args=a.parse_args()

def rows_separated(c,context):
 """A settings label ends by column 9, so column 10 stays blank beside a value."""
 for y in (7,9,11,13):
  line=c.row(y)
  assert not (line[10].isalnum() and line[11].isalnum()),(context,'Label touches its value',line)

def settings_pages(c,test,preset,pages):
 c.go(test);c.preset(preset)
 for page in range(pages):
  rows_separated(c,(test,page));c.press('select')
 c.press('b');c.tick(30)

def run(cgb):
 c=Cart(args.rom,cgb)
 try:
  # Every Select page of the settings screens reached through presets.
  settings_pages(c,3,2,2);settings_pages(c,5,1,2);settings_pages(c,6,2,2);settings_pages(c,7,1,2);settings_pages(c,10,1,4)
  # Buttons timing: separated rows and one readable footer.
  c.go(4);c.preset(3);rows_separated(c,'buttons timing')
  assert c.row(16).strip('# ')=='Short at most 1 fr',c.row(16)
  c.leave()
  # Link: every detail page, and a minutes:seconds timer at the right edge.
  c.go(1);c.press('a');c.tick(60);c.press('start');c.tick(130)
  # A stress profile opens on the shared-ball page, which has no settings rows.
  for page in range(4):
   for detail in range(4):
    if 'ball' not in c.text():rows_separated(c,('link',page,detail))
    c.press('a')
   c.press('right');c.tick(10)
  assert re.search(r' \d+:[0-5]\d$',c.row(17)[:19]),('Link timer is not minutes:seconds at the right edge',c.row(17))
  c.press('b');c.tick(10);c.press('start');c.tick(30);c.leave()
  if cgb:
   # Infrared: switching from Transmit back to Receive leaves no old letters.
   c.go(9);c.preset(4);c.press('a');c.tick(400);assert c.get('ir_bursts',2)>9
   c.press('a');c.press('left')
   assert c.row(7)[11:18]=='Receive' and not c.row(7)[18].isalpha(),('Stale mode text',c.row(7))
   assert c.row(10)[10:19]==' Edges   ',('Stale counter label',c.row(10))
   assert c.row(12)[10:19]==' 0       ',('Stale counter digits',c.row(12))
   c.press('b')
  # Audio: the highest pulse frequency keeps a space before its unit.
  c.go(3);c.preset(2);assert c.get('audio_row')==1
  for _ in range(12):c.press('right')
  assert c.get('tone_index')==33,c.get('tone_index')
  assert c.row(13)[16:19]==' Hz',('Frequency runs into its unit',c.row(13))
  print(('CGB' if cgb else 'DMG')+': settings rows, Buttons footer, Link pages and timer, Infrared mode switch and Audio cursor read cleanly',flush=True)
 finally:c.close()

def clock():
 c=Cart(args.mbc3)
 try:
  c.go(2);c.preset(1)
  for _ in range(3):c.press('select')
  line=c.row(9);assert c.get('rtc_latch_errors',2)==0
  assert line[10:19].strip()=='0',('Clock change count is not the stored zero',line)
  rows_separated(c,'clock page 4')
  for _ in range(2):c.press('select')
  c.press('left');c.press('left');assert c.get('rtc_mode')==2
  for _ in range(2):c.press('select')
  assert c.row(9)[10:19].strip()=='0',('Halt change count is not zero',c.row(9))
  print('MBC3: Clock change counters show their stored value')
 finally:c.close()

for cgb in (True,False):run(cgb)
clock()
