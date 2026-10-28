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
 c.press('start');assert 'Confirm' in c.row(4),'Start tap did not open Clear counts'
 c.press('down');c.press('a');assert c.get('button_presses',32)==0,'Yes did not clear counters'
finally:c.close()
# Start clears from the count, timing and diagonal pages, and the screens say how to clear, change page and leave.
HINTS=['Select: next page','Start: zero counts','Hold A+B+Sel+Start']
def under_box(c):return c.row(17).strip('# ')
c=Cart(args.rom)
try:
 c.go(4);c.preset(1)
 assert c.row(15).strip('# ')=='Hold all 4: exit',('Live page does not say how to leave',c.row(15))
 # The live page keeps its Held and Peak reading under the box, and Start there is only a tested button.
 for _ in range(30):
  c.tick(16);assert under_box(c).startswith('Held'),('Live page line under the box',under_box(c))
 before=c.get('button_presses',32);c.press('start')
 assert 'Confirm' not in c.row(4),'Start opened Clear counts on the live page, where it is a tested button'
 assert c.get('button_presses',32)!=before,'Start was not counted on the live page'
 for page in (1,2,3):
  c.press('select');assert c.get('button_page')==page,page
  if page!=3:assert under_box(c)==HINTS[0],(names[page],'First hint when the page opens',under_box(c))
  c.press('start');assert 'Confirm' in c.row(4),(names[page],'Start did not open Clear counts')
  opened=c.get('button_presses',32);c.press('a');c.tick(20)
  assert 'Confirm' not in c.row(4),(names[page],'The dialog stayed open after No')
  assert opened!=0 and c.get('button_presses',32)==opened,(names[page],'No changed the counts')
  if page!=3:assert under_box(c)==HINTS[0],(names[page],'First hint after the dialog',under_box(c))
  order=[]
  for _ in range(60):
   c.tick(16);line=under_box(c)
   if not order or order[-1]!=line:order.append(line)
  if page==3:assert all(line.startswith('Opposites') for line in order),('Diagonals line under the box',order)
  else:assert order[:4]==[HINTS[0],HINTS[1],HINTS[2],HINTS[0]],(names[page],'Hints did not cycle in order',order)
 # Yes clears every count.
 c.press('start');c.press('down');c.press('a');c.tick(20)
 assert c.get('button_presses',32)==0,'Yes did not clear the counts on the diagonals page'
finally:c.close()
# A dialog hides how long it stayed open. A Start tap soon after it closes is not a gap in the Start presses.
c=Cart(args.rom)
try:
 c.go(4);c.preset(1);c.press('select');c.press('select')
 for _ in range(7):c.press('up')
 assert c.get('button_threshold')==8,c.get('button_threshold')
 c.press('start');c.tick(60)
 gaps=c.get('button_gaps',32)
 for wait in range(4,13):
  c.press('a',after=wait);c.press('start');c.tick(60)
 assert c.get('button_gaps',32)==gaps,'A Start tap after a dialog counted as a gap'
finally:c.close()
print('Buttons: staged and simultaneous chords on all four pages keep page, units, view and counts; Select, A and Start taps act on release; Start clears from every counts page, the screens say how to clear, change page and leave, and a dialog adds no gap')
