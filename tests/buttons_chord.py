"""The return chord leaves Buttons settings alone; single taps still act on release."""
import argparse
from pathlib import Path
from cart import Cart,ROMS
a=argparse.ArgumentParser();a.add_argument('--rom',type=Path,default=ROMS['mbc5']);args=a.parse_args()
names=['live','counts','timing','diagonals']

def state(c):return (c.get('button_page'),c.get('button_units'),c.get('button_diagonal_view'),c.get('button_presses',32))

for page in range(4):
 for staged in (False,True):
  c=Cart(args.rom)
  try:
   c.go(4);c.preset(1)
   for _ in range(page):c.press('select')
   assert c.get('button_page')==page,(names[page],c.get('button_page'))
   c.press('a');before=state(c)
   # People press the chord a button at a time; emulator input can arrive together.
   keys=['select','start','a','b']
   if staged:
    for key in keys:c.p.button_press(key);c.tick(6)
    c.tick(70)
   else:
    for key in keys:c.p.button_press(key)
    c.tick(80)
   assert 'Continue' in c.text(),(names[page],staged,'Return dialog did not open',c.text())
   for key in keys:c.p.button_release(key)
   c.tick(20);c.press('b');c.tick(20)
   after=state(c)
   assert after[:3]==before[:3],(names[page],staged,'Chord changed a setting',before[:3],after[:3])
   assert after[3]!=0,(names[page],staged,'Chord cleared the counters')
  finally:c.close()
c=Cart(args.rom)
try:
 c.go(4);c.preset(1)
 c.p.button_press('select');c.tick(10);assert c.get('button_page')==0,'Select acted before release'
 c.p.button_release('select');c.tick(10);assert c.get('button_page')==1,'Select tap did not change page'
 c.press('select');c.press('a');assert c.get('button_units')==1,'A tap did not change units'
 c.press('start');assert 'Confirm' in c.row(5),'Start tap did not open Clear counts'
 c.press('down');c.press('a');assert c.get('button_presses',32)==0,'Yes did not clear counters'
finally:c.close()
print('Buttons: staged and simultaneous chords on all four pages keep page, units, view and counts; Select, A and Start taps act on release')
