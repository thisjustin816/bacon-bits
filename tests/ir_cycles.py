"""Measure RP edge spacing by executing the compiled naked burst instructions."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1];rom=(ROOT/'build/bacon-bits.gbc').read_bytes()
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',(ROOT/'build/bacon-bits.noi').read_text(),re.M)}
a=syms['_ir_burst'];code=rom[(a>>16)*16384+(a&65535)-16384:];durations=[]
for count,on,off in [(32,2,3),(64,1,1),(1,32,32),(64,32,32)]:
 memory={syms['_ir_pulses']:count,syms['_ir_on']:on,syms['_ir_off']:off};r=dict(A=0,B=0,C=0,D=0,E=0);pc=cycles=0;zero=False;edges=[]
 for _ in range(100000):
  op=code[pc];pc+=1
  if op in [0xc5,0xd5]:cycles+=16
  elif op in [0xd1,0xc1]:cycles+=12
  elif op==0xfa:address=int.from_bytes(code[pc:pc+2],'little');pc+=2;r['A']=memory[address];cycles+=16
  elif op in [0x47,0x57,0x5f]:r[{0x47:'B',0x57:'D',0x5f:'E'}[op]]=r['A'];cycles+=4
  elif op==0x0e:r['C']=code[pc];pc+=1;cycles+=8
  elif op in [0xf3,0xfb]:cycles+=4
  elif op==0x3e:r['A']=code[pc];pc+=1;cycles+=8
  elif op==0xe2:cycles+=8;assert r['C']==0x56;edges.append((cycles,r['A']))
  elif op in [0x7a,0x7b]:r['A']=r['D' if op==0x7a else 'E'];cycles+=4
  elif op in [0x3d,0x05]:reg='A' if op==0x3d else 'B';r[reg]=(r[reg]-1)&255;zero=not r[reg];cycles+=4
  elif op==0x20:
   offset=code[pc];pc+=1
   if not zero:pc+=offset-256 if offset>127 else offset;cycles+=12
   else:cycles+=8
  elif op==0xc9:cycles+=16;break
  else:raise AssertionError((pc-1,hex(op)))
 else:raise AssertionError('Burst never returned')
 assert len(edges)==count*2 and edges[-1][1]==0xc0
 for i in range(count):assert edges[i*2+1][0]-edges[i*2][0]==16*(on+1)
 for i in range(count-1):assert edges[i*2+2][0]-edges[i*2+1][0]==16*(off+2)
 durations.append(cycles/4194304*1000)
assert max(durations)<17,'A burst blocks more than one video frame'
print('Compiled infrared: 1/32/64 pulses, exact ON/OFF cycles, normal-speed 11.44/19.07 us preset, receiver enabled and transmitter off on return; maximum burst under 17 ms')
