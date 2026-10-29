"""SRAM cycles and stops, Burn In's SRAM watch, and browser Up/Down order."""
import argparse
from pathlib import Path
from cart import Cart,ROMS
a=argparse.ArgumentParser();a.add_argument('--rom',type=Path,default=ROMS['mbc5']);args=a.parse_args()

def wait(c,done,frames):
 for _ in range(frames//8):
  if done():return
  c.tick(8)
 raise AssertionError(c.text())

c=Cart(args.rom)
try:
 # Up and Down move two cards at a time through one list of twelve, wrapping at the ends, in
 # both columns.
 seen=[]
 for key in ['down']*6+['up']*6:c.press(key);seen.append(c.get('selected_test'))
 assert seen==[2,4,6,8,10,0,10,8,6,4,2,0],seen
 c.press('right');seen=[]
 for key in ['down']*6+['up']*6:c.press(key);seen.append(c.get('selected_test'))
 assert seen==[3,5,7,9,11,1,11,9,7,5,3,1],seen
 c.press('left')
 # Bit patterns preset cycles ten passes; one bank keeps the run short.
 c.go(6);c.preset(3);assert c.get('ram_mode')==2 and c.get('ram_pattern')==4
 c.press('down')
 for _ in range(3):c.press('left')
 assert c.get('ram_banks')==1
 c.press('a');c.press('down');c.press('a')
 wait(c,lambda:'SRAM result' in c.text(),40000);c.tick(40)
 assert c.row(6)[2:19].split()==['Result','Pass'] and c.row(12)[2:19].split()==['Passes','10'],c.text()
 # Each pass restarts the byte count, so Bytes shows one pass of one bank.
 assert c.get('ram_errors',4)==0 and c.get('ram_checked',4)==8160,c.get('ram_checked',4)
 # Stopping a write part way leaves no valid record and reports Unknown, not Pass.
 c.press('b');c.press('a');c.press('down');c.press('a');c.tick(20);c.press('b')
 assert 'Unknown' in c.row(6) and not c.get('ram_valid'),c.text()
 c.press('b');c.press('b')
 # Write four banks so Burn In's read-only watch has a record to verify.
 c.go(6);c.preset(2);assert c.get('ram_mode')==1 and c.get('ram_banks')==4
 c.press('a');c.press('down');c.press('a')
 wait(c,lambda:'SRAM result' in c.text(),8000);assert 'Pass' in c.row(6) and c.get('ram_valid'),c.text()
 c.press('b');c.press('b')
 c.go(7);c.preset(4);c.press('a')
 wait(c,lambda:c.get('burn_ram_status')>=2,16000)
 assert c.get('burn_ram_status')==2 and not c.get('burn_errors',4),'SRAM watch did not verify the record'
 # A flipped bit during the next pass is reported with its bank and offset, then Stop on fail ends the run.
 c.p.memory[2,0xa500]^=1
 wait(c,lambda:not c.get('burn_running'),32000);c.tick(60)
 assert c.get('burn_first_kind')==3 and c.get('burn_first_bank')==2 and c.get('burn_first_offset',2)==0x500,(c.get('burn_first_kind'),c.get('burn_first_bank'),c.get('burn_first_offset',2))
 assert c.get('burn_ram_status')==3 and 'SRAM fail' in c.row(17),c.text()
 print('Up/Down order, ten SRAM cycle passes, Unknown after a stopped write, and Burn In SRAM watch pass and fail passed')
finally:c.close()
