"""Cold boots, diagnostic routing, modal restoration, and shared-RAM hygiene."""
from pathlib import Path
import tempfile,shutil,re,json
from pyboy import PyBoy
from header import pyboy_header,vram_header
ROOT=Path(__file__).resolve().parents[1]
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',(ROOT/'build/bacon-bits.noi').read_text(),re.M)}
rom=ROOT/'build/bacon-bits.gbc'
def text(p,mode="plain"):
 return '\n'.join(''.join(chr(t+32).upper() if t<96 else '#' for t in p.memory[0,0x9800+y*32:0x9814+y*32]) for y in range(18))
def platform_text(p):return '\n'.join(''.join(chr(t+32).upper() if t<96 else '-' for t in p.memory[0,0x9800+y*32:0x9800+y*32+20]) for y in range(18))
for cgb in [True,False]:
 with tempfile.TemporaryDirectory() as td:
  f=Path(td)/'test.gbc';shutil.copy(rom,f);p=PyBoy(str(f),window='null',sound_emulated=True,cgb=cgb);p.set_emulation_speed(0)
  def press(k):p.button_press(k);p.tick(8,True);p.button_release(k);p.tick(20,True)
  def chord():
   for k in ['a','b','start','select']:p.button_press(k)
   p.tick(8,True)
   for k in ['a','b','start','select']:p.button_release(k)
   p.tick(20,True)
  def leave():chord();assert 'CONTINUE' in text(p,'popup'),text(p);press('down');press('a');p.tick(40,True)
  def modal():
   before=bytes(p.memory[0,0x8800:0x8d00]);chord();assert 'CONTINUE' in text(p,'popup');press('b')
   assert before==bytes(p.memory[0,0x8800:0x8d00]),'CONTINUE did not restore borrowed tile patterns'
  try:
   p.tick(240,True);assert pyboy_header(p,cgb),text(p)
   assert 'PLATFORM' in text(p)
   assert len(p.screen.image.convert('RGB').getcolors(65536))>=4
   press('left');assert p.memory[syms['_selected_test']]==11;press('right');assert 'PLATFORM' in text(p)
   press('a');p.tick(240,True)
   assert ('PYBOY' if cgb else 'NO CGB PROBES') in text(p),text(p)
   modal();leave();assert 'PLATFORM' in text(p)
   press('right');press('a');p.tick(60,True);assert 'LINK PRESETS' in text(p),text(p);press('a');p.tick(100,True)
   assert p.memory[syms['_running']]==0
   modal();leave();assert 'LINK' in text(p)
   press('right');press('a');p.tick(100,True)
   assert 'RUMBLE' in text(p),text(p)
   modal();leave();assert 'RUMBLE' in text(p)
   # Rumble shares $C000 with shadow OAM. Every sprite must be hidden again.
   assert all(p.memory[0xfe00+i*4]==0 for i in range(40)), 'Rumble left stale sprites in OAM'
   press('right');press('a');p.tick(60,True);press('up');press('a');p.tick(60,True)
   assert 'AUDIO' in text(p) and 'SILENT' in text(p),text(p)
   press('a');assert 'PLAYING' in text(p);press('b');assert p.memory[syms['_selected_test']]==3
   assert p.memory[0xff26]&15==0,'Audio remained active on exit'
   p.screen.image.save(ROOT/'build'/('smoke-cgb.png' if cgb else 'smoke-dmg.png'))
   print(('CGB' if cgb else 'DMG')+': browser wrap, four tests, modal restoration, rumble return and sprite cleanup passed')
  finally:p.stop(save=False)
