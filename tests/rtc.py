"""Verify MBC3 observation, confirmed clock changes and recovery through the UI."""
from pathlib import Path
from pyboy import PyBoy
import tempfile,shutil,re
ROOT=Path(__file__).resolve().parents[1];rom=ROOT/'build/mbc3/bacon-bits.gbc';data=rom.read_bytes();assert (data[0x147],data[0x149])==(0x10,3)
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',rom.with_suffix('.noi').read_text(),re.M)}
with tempfile.TemporaryDirectory() as td:
 f=Path(td)/'rtc.gbc';shutil.copy(rom,f)
 def boot():
  global p
  p=PyBoy(str(f),window='null',sound_emulated=False);p.set_emulation_speed(0);p.tick(240,True)
 def press(k):p.button_press(k);p.tick(8,True);p.button_release(k);p.tick(24,True)
 def get(n,size=1):return int.from_bytes(bytes(p.memory[syms['_'+n]:syms['_'+n]+size]),'little')
 def snapshot():return bytes(p.memory[syms['_rtc_data']:syms['_rtc_data']+5])
 def text():return '\n'.join(''.join(chr(t+32).upper() if t<96 else '#' for t in p.memory[0,0x9800+y*32:0x9814+y*32]) for y in range(18))
 def open_clock():
  press('right');press('right');assert get('selected_test')==2;press('a');p.tick(90,True)
 def preset(n):
  assert 'CLOCK PRESETS' in text(),text()
  for _ in range(n if 'CONTINUE' in text() else n-1):press('down')
  press('a');p.tick(60,True)
 def journal():return bytes(p.memory[0,0xbff0:0xbfff])+bytes([p.memory[0,0xbfff]])
 try:
  boot();open_clock();preset(1);assert 'CLOCK' in text() and get('rtc_valid') and not get('rtc_dirty')
  first=snapshot();press('a');p.tick(180,True);assert get('rtc_ticks')>0 and not get('rtc_dirty') and journal()[:2]!=b'RT';press('b')
  press('a');preset(2);press('a');held=snapshot();p.tick(90,True);assert get('rtc_running') and snapshot()==held and get('rtc_latch_errors',2)==0
  p.tick(180,True);assert not get('rtc_running') and snapshot()!=held and 'LATCH HELD' in text();press('b')
  press('a');preset(3);press('a');assert 'CONFIRM' in text();press('a');assert not get('rtc_dirty') and not get('rtc_running'),'NO default altered the RTC'
  press('a');press('down');press('a');assert get('rtc_dirty') and get('rtc_running') and snapshot()[4]&64 and journal()[:2]==b'RT'
  frozen=snapshot();p.tick(180,True);assert snapshot()==frozen and get('rtc_halt_errors',2)==0;press('b');assert not get('rtc_dirty') and journal()[:2]!=b'RT'
  press('a');preset(4);press('a');press('down');press('a');assert get('rtc_dirty')
  p.tick(240,True);assert get('rtc_rollover_seen') and snapshot()[4]&128 and snapshot()[3]==0 and not snapshot()[4]&1
  p.screen.image.save(ROOT/'build/rtc-rollover.png');press('b');assert not get('rtc_dirty')
  # Persist a pending halt check, then recover on a fresh emulator instance.
  press('a');preset(3);press('a');press('down');press('a');saved=bytes(p.memory[syms['_rtc_saved']:syms['_rtc_saved']+5]);assert get('rtc_dirty')
  p.stop(save=True);boot();open_clock();assert 'RESTORE SAVED RTC?' in text();assert p.memory[0,0x98d3]==97,'Recovery prompt overwrote its frame';press('a');assert get('selected_test')==2
  press('a');assert 'RESTORE SAVED RTC?' in text();press('down');press('a');assert 'CLOCK PRESETS' in text() and journal()[:2]!=b'RT'
  press('a');assert get('rtc_valid') and not snapshot()[4]&64
  assert snapshot()[3:]==saved[3:],'Recovery did not restore day / halt / carry'
  # Standard MBC3 must never offer an eighth SRAM bank or an MBC5 LED output.
  press('b')
  for _ in range(4):press('right')
  press('a');press('down');press('a');assert get('ram_banks')==4
  press('b');press('right');press('right');press('a');assert 'MBC5 RGB CART' in text();press('b')
  print('MBC3: live ticks, held latch, NO confirmation, halt invariance, day-511 carry rollover, restore on exit, battery-file recovery, four-bank SRAM and unsupported-LED guard passed')
 finally:p.stop(save=False)
