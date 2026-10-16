"""Check four reported D-pad corners, hold duration, and opposing inputs."""
from pathlib import Path
import tempfile,re,shutil
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1]
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',(ROOT/'build/bacon-bits.noi').read_text(),re.M)}
for cgb in [True,False]:
 with tempfile.TemporaryDirectory() as td:
  f=Path(td)/'test.gbc';shutil.copy(ROOT/'build/bacon-bits.gbc',f);p=PyBoy(str(f),window='null',sound_emulated=False,cgb=cgb);p.set_emulation_speed(0)
  def get(n,size=1):return int.from_bytes(bytes(p.memory[syms['_'+n]:syms['_'+n]+size]),'little')
  def press(k):p.button_press(k);p.tick(8,True);p.button_release(k);p.tick(24,True)
  try:
   p.tick(240,True)
   for _ in range(4):press('right')
   press('a');p.tick(60,True)
   for _ in range(3):press('down')
   press('a');p.tick(60,True);assert get('button_page')==3
   for corner,keys in enumerate([['up','right'],['up','left'],['down','right'],['down','left']]):
    for k in keys:p.button_press(k)
    p.tick(12,True)
    assert int.from_bytes(bytes(p.memory[syms['_button_diagonal']+corner*4:syms['_button_diagonal']+corner*4+4]),'little')==1
    assert p.memory[0,0x9800+(7 if corner<2 else 13)*32+(2 if corner&1 else 8)]==109
    for k in keys:p.button_release(k)
    p.tick(12,True)
    assert int.from_bytes(bytes(p.memory[syms['_button_diagonal_peak']+corner*2:syms['_button_diagonal_peak']+corner*2+2]),'little')>=10
   assert get('button_diagonal',16).to_bytes(16,'little')==b'\x01\0\0\0'*4
   for k in ['left','right']:p.button_press(k)
   p.tick(12,True)
   for k in ['left','right']:p.button_release(k)
   p.tick(12,True);assert get('button_opposites',4)==1
   press('a');assert get('button_diagonal_view')==1;press('a');assert get('button_diagonal_view')==2
   p.screen.image.save(ROOT/'build'/f'diagonals-{cgb}.png')
  finally:p.stop(save=False)
print('CGB/DMG diagonals: all four entries and held markers, individual longest holds, frame/ms views, and opposite-direction reporting passed')
