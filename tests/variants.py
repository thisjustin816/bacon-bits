"""Open every release entry on both CGB and DMG without automatic outputs."""
from pathlib import Path
from pyboy import PyBoy
from header import pyboy_header,vram_header
import re,tempfile,shutil
ROOT=Path(__file__).resolve().parents[1]
for variant,rom in [('mbc5',ROOT/'build/bacon-bits.gbc'),('mbc3',ROOT/'build/mbc3/bacon-bits.gbc')]:
 syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',rom.with_suffix('.noi').read_text(),re.M)}
 for cgb in [True,False]:
  with tempfile.TemporaryDirectory() as td:
   for selected in range(11):
    f=Path(td)/f'{selected}.gbc';shutil.copy(rom,f);p=PyBoy(str(f),window='null',sound_emulated=False,cgb=cgb);p.set_emulation_speed(0)
    def press(k):p.button_press(k);p.tick(8,True);p.button_release(k);p.tick(24,True)
    def get(n):return p.memory[syms['_'+n]]
    def text():return '\n'.join(''.join(chr(t+32).upper() if t<96 else '#' for t in p.memory[0,0x9800+y*32:0x9814+y*32]) for y in range(18))
    try:
     p.tick(240,True)
     for _ in range(selected):press('right')
     assert get('selected_test')==selected;press('a');p.tick(90,True)
     if 'PRESETS' in text():press('a');p.tick(60,True)
     assert pyboy_header(p,cgb),(variant,cgb,selected,text())
     assert len(p.screen.image.convert('RGB').getcolors(65536))>=2,(variant,cgb,selected)
     if selected==1:assert not get('running')
     if selected==2:assert 'CLOCK' in text() if variant=='mbc3' else 'RUMBLE' in text()
     if selected==3:assert not get('tone_playing')
     if selected==5:assert not get('display_running')
     if selected==6:assert not get('ram_stage') and get('ram_banks')==(4 if variant=='mbc3' else 8)
     if selected==7:
      assert not get('burn_running');press('select');assert ('RTC' in text() and 'RUMBLE' not in text()) if variant=='mbc3' else 'RUMBLE F' in text()
     if selected==8:assert 'MBC5 RGB CART' in text() if variant=='mbc3' else not get('led_active')
     if selected==10:assert not get('flicker_running')
     if selected==9:assert not get('ir_running') and ('NO CGB IR PORT' in text() if not cgb else 'INFRARED' in text())
     p.screen.image.save(ROOT/'build'/f'variant-{variant}-{cgb}-{selected}.png')
    finally:p.stop(save=False)
  print(f'{variant} {"CGB" if cgb else "DMG"}: all eleven routes use the shared UI; outputs and destructive tests remain stopped')
