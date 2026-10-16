"""Check centered label pixels, card borders and font restoration in both mappers."""
from pathlib import Path
import re,shutil,sys,tempfile
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from lettering import GLYPHS,tiles
rom_override=Path(sys.argv[1]) if len(sys.argv)>1 else None
for variant in ['', 'mbc3']:
 rom=rom_override or ROOT/'build'/variant/'bacon-bits.gbc'
 for cgb in [True,False]:
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/'menu.gbc';shutil.copy(rom,f);p=PyBoy(str(f),window='null',sound_emulated=False,cgb=cgb);p.set_emulation_speed(0)
   def press(key):p.button_press(key);p.tick(8,True);p.button_release(key);p.tick(30,True)
   def ink(x,y):
    t=p.memory[0,0x9800+(y//8)*32+x//8];addr=0x8000+t*16+(y&7)*2
    return bool(p.memory[0,addr] & p.memory[0,addr+1] & (0x80>>(x&7)))
   try:
    p.tick(240,True)
    header=''.join(chr(t+32) if t<96 else '#' for t in p.memory[0,0x9825:0x982f])
    assert header=='Bacon Bits',header
    clock=rom.read_bytes()[0x147]==0x10
    pages=[['Platform','Link','Clock' if clock else 'Rumble','Audio'],['Buttons','Display','Save RAM','Burn in'],['Cart LED','IR']]
    for page,labels in enumerate(pages):
     for i,label in enumerate(labels):
      center=120 if i&1 else 40;start=center-len(label)*4;y=120 if i&2 else 72
      expected={(start+j*8+1+dx,y+dy) for j,c in enumerate(label) for dy,row in enumerate(GLYPHS[c]) for dx,v in enumerate(row) if v=='#'}
      actual={(x,yy) for yy in range(y,y+8) for x in range(center-32,center+32) if ink(x,yy)}
      assert actual==expected,(variant,cgb,page,label,'Label is not centered or shares a border')
     # Lower cards must have their bottom border, including the row below the text.
     if page<2:assert all(ink(x,128) for x in range(8,76)),(variant,cgb,'Missing lower border')
     if page<2:
      for _ in range(4):press('right')
    # Entering IR restores every punctuation tile borrowed by the launcher.
    press('right');press('a');p.tick(60,True)
    assert bytes(p.memory[0,0x8000:0x8600])==tiles(),'Launcher label tiles leaked into a test'
    p.screen.image.save(ROOT/'build'/f'menu-font-restored-{variant or "mbc5"}-{cgb}.png')
   finally:p.stop(save=False)
 if rom_override:break
print('Mixed-case labels, centered pixels, complete card borders and restored test font passed for CGB/DMG and both mappers')
