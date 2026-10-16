"""Drive the real compiled APU routines and measure emulator audio captures."""
from pathlib import Path
import re,shutil,tempfile,json,sys
import numpy as np
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1]
rom=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'build/bacon-bits.gbc'
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',rom.with_suffix('.noi').read_text(),re.M)}
with tempfile.TemporaryDirectory() as td:
 f=Path(td)/'test.gbc'
 data=bytearray(rom.read_bytes())
 # Enter a WRAM sentinel after GBDK startup instead of entering the browser.
 entry=syms['_main'];data[entry:entry+3]=bytes([0xc3,0,0xdb]);f.write_bytes(data)
 p=PyBoy(str(f),window='null',sound_emulated=True);p.set_emulation_speed(0)
 def install(_):p.memory[0xdb00:0xdb03]=[0xf3,0x18,0xfe]
 p.hook_register(0,0x100,install,None);p.tick(240,True)
 def put(name,value):p.memory[syms['_'+name]]=value
 def call(name):
  addr=syms['_'+name];assert addr>>16==4
  code=bytes([0x3e,4,0xea,0,0x20,0xcd,addr&255,(addr>>8)&255,0x18,0xfe])
  p.memory[0xdb10:0xdb10+len(code)]=code;p.register_file.PC=0xdb10;p.tick(30,True)
  assert p.register_file.PC in [0xdb18,0xdb19],hex(p.register_file.PC)
 def record(frames=150):
  chunks=[]
  for _ in range(frames):p.tick(1,True);chunks.append(p.sound.ndarray.copy())
  a=np.concatenate(chunks,axis=0)
  return a
 def level(a):return float(np.std(a.astype(float)))
 results=[]
 try:
  for voice in range(4):
   put('tone_voice',voice);put('tone_index',0);put('tone_level',3 if 2<=voice<3 else 15);put('tone_output',0);put('tone_playing',1);put('tone_gate',1)
   call('tone_apply');a=record(480 if voice>=3 else 150);print('capture',voice,a.shape,level(a),flush=True)
   assert level(a)>0.1,(voice,'silent capture')
   if voice<3:
    # Nyquist-safe fundamentals at the lowest stepped frequency.
    mono=a.astype(float).mean(axis=1);mono-=mono.mean();spectrum=np.abs(np.fft.rfft(mono*np.hanning(len(mono))))
    freqs=np.fft.rfftfreq(len(mono),1/p.sound.sample_rate);expected=64 if voice<2 else 32
    region=np.flatnonzero((freqs>expected*0.8)&(freqs<expected*1.2));peak=float(freqs[region[np.argmax(spectrum[region])]])
    assert abs(peak-expected)<1,(voice,peak,expected)
    results.append({'voice':voice,'expected_hz':expected,'captured_peak_hz':peak})
   put('tone_level',0);call('tone_apply');silent=record(60)
   assert level(silent)<0.1,(voice,'mute was audible in capture',level(silent))
  (ROOT/'build/audio-backend-results.json').write_text(json.dumps(results,indent=2)+'\n')
  print('Compiled APU: four channels produce emulator samples, mute is silent, pulse/wave low endpoints have the expected fundamental')
 finally:p.stop(save=False)
