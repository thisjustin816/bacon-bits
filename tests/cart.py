"""Shared PyBoy driver for suites that navigate the cartridge by its symbols."""
from pathlib import Path
import re,shutil,tempfile
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1]
ROMS={'mbc5':ROOT/'build/bacon-bits.gbc','mbc3':ROOT/'build/mbc3/bacon-bits.gbc'}

def symbols(rom):
 return {n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',Path(rom).with_suffix('.noi').read_text(),re.M)}

class Cart:
 """One fresh PyBoy instance on a private copy of the ROM, booted to the browser."""
 def __init__(self,rom,cgb=True,sound=False):
  self.rom=Path(rom);self.syms=symbols(rom);self.folder=tempfile.TemporaryDirectory()
  path=Path(self.folder.name)/'cart.gbc';shutil.copy(self.rom,path)
  self.p=PyBoy(str(path),window='null',sound_emulated=sound,cgb=cgb);self.p.set_emulation_speed(0);self.p.tick(240,True)
 def get(self,name,size=1):
  at=self.syms['_'+name];return int.from_bytes(bytes(self.p.memory[at:at+size]),'little')
 def tick(self,frames=1):self.p.tick(frames,True)
 def press(self,key,held=8,after=24):self.p.button_press(key);self.tick(held);self.p.button_release(key);self.tick(after)
 def hold(self,keys,frames):
  for key in keys:self.p.button_press(key)
  self.tick(frames)
  for key in keys:self.p.button_release(key)
 def tiles(self,y):return list(self.p.memory[0,0x9800+y*32:0x9814+y*32])
 def row(self,y):return ''.join(chr(t+32) if t<96 else '#' for t in self.p.memory[0,0x9800+y*32:0x9814+y*32])
 def text(self):return '\n'.join(self.row(y) for y in range(18))
 def go(self,test):
  for _ in range(12):
   if self.get('selected_test')==test:return
   self.press('right')
  raise AssertionError(('Browser never reached test',test))
 def preset(self,choice):
  """Open the selected test and pick preset 1-4; 0 keeps the current settings."""
  self.press('a');assert 'presets' in self.row(5),self.text()
  first=1 if 'Manual' in self.text() else 0
  for _ in range(choice-first if choice>=first else 4):self.press('down')
  self.press('a')
 def leave(self):
  """Open the return dialog with the four-button chord and choose Test menu."""
  self.hold(['a','b','start','select'],70);self.tick(30);self.press('down');self.press('a');self.tick(40)
 def close(self):self.p.stop(save=False);self.folder.cleanup()
