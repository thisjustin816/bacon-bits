"""Two benches run Link over a cable that behaves as the hardware's does.

PyBoy's own linked serial makes each side wait for the other, and the
upstream paired suite uses it to check the protocol. Here the host's clock
never waits: an edge that finds the peer unarmed is lost, as on a real cable.
Uses the two-console harness in two_consoles.py.

Clean runs must lose no edge and count no error, at both CPU speeds on each
end and with the consoles' frames apart. A bit flipped in a packet's payload
must show as one CRC error and not as a SEQ error too. A dropped edge must leave the link
recovering. A 40-frame unplug must show as one dropout on the host, packets
missing at the peer, and no two-second gap.
"""
from pathlib import Path
import shutil,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'vendor/link-sustain/tests'))
from cart import ROMS,symbols
from rom_helpers import configure
from two_consoles import Pair,FRAME,run_frames,press

LINK_TEST=1
COUNTERS=(('good',4),('crc_errors',4),('seq_errors',4),('data_errors',4),('timeouts',4),('dropouts',4),('first_code',1),('overflow',2),('underrun',2))

def start(rom,d,*,host_cpu=0,peer_cpu=0,test=0,rate=1,offset=0):
 """Two benches in Link, settings chosen, the peer started and the host
 started half a second later, paired with the given frame offset."""
 syms=symbols(rom)
 paths=[Path(d)/f'{i}.gbc' for i in range(2)]
 for path in paths:shutil.copy(rom,path)
 pair=Pair(paths,cable=True)
 for index,pb in enumerate(pair.machines):
  get=lambda name,size=1,pb=pb:int.from_bytes(bytes(pb.memory[syms['_'+name]:syms['_'+name]+size]),'little')
  run_frames(pb,240)
  for _ in range(12):
   if get('selected_test')==LINK_TEST:break
   press(pb,'right')
  else:raise AssertionError('browser never reached Link')
  press(pb,'a')
  configure(get,lambda key,pb=pb:press(pb,key),host=index==0,test=test,rate=rate,cpu=host_cpu if index==0 else peer_cpu)
 pair.start(step_cycles=64,offset=offset)
 pair.press(1,'start')
 peer_started=pair.machines[1].frame_count
 pair.run_until(lambda:pair.machines[1].frame_count>=peer_started+30,60*FRAME)
 pair.press(0,'start')
 return pair,syms

def counters(pair,syms):
 # A build from before a counter existed reads it as None.
 return [{name:int.from_bytes(bytes(pb.memory[syms['_'+name]:syms['_'+name]+size]),'little') if '_'+name in syms else None for name,size in COUNTERS} for pb in pair.machines]

def run_frames_paired(pair,frames):
 end=min(pair.now(0),pair.now(1))+frames*FRAME
 pair.run_until(lambda:min(pair.now(0),pair.now(1))>=end,(frames+1)*FRAME)

def clean(rom,**settings):
 with tempfile.TemporaryDirectory() as d:
  pair,syms=start(rom,d,**settings)
  try:
   run_frames_paired(pair,420)
   return counters(pair,syms),pair.cable.missed,min(pair.cable.slack,default=None)
  finally:pair.close()

def faulted(rom,kind,receiver,**settings):
 """Run 120 frames, inject the fault, then run 360 more."""
 with tempfile.TemporaryDirectory() as d:
  pair,syms=start(rom,d,**settings)
  try:
   run_frames_paired(pair,120)
   before=counters(pair,syms)
   if kind=='unplug':
    pair.cable.connected=False;run_frames_paired(pair,40);pair.cable.connected=True
   elif kind=='flip':
    # A flipped sync byte hides its packet, which then counts as missing,
    # so the flip goes into a payload byte the CRC covers.
    pair.cable.flip_in_packet(receiver,8)
   else:
    pair.cable.fault(kind,pair.cable.edges+1,receiver)
   run_frames_paired(pair,360)
   return before,counters(pair,syms),pair.cable.injected
  finally:pair.close()

def clean_ok(side):
 return side['good']>20 and not any(side[name] for name in ('crc_errors','seq_errors','data_errors','timeouts','dropouts','first_code','overflow','underrun'))

def main():
 rom=Path(sys.argv[1]) if len(sys.argv)>1 else ROMS['mbc5']
 failures=[]
 for label,settings in (('1x host, 1x peer',{}),('2x host, 2x peer',dict(host_cpu=1,peer_cpu=1)),
                        ('2x host, 1x peer',dict(host_cpu=1)),('1x host, 2x peer',dict(peer_cpu=1)),
                        ('1x, peer half a frame later',dict(offset=FRAME//2)),('2x, all stress',dict(host_cpu=1,peer_cpu=1,test=4))):
  started=time.monotonic()
  sides,missed,slack=clean(rom,**settings)
  print(f'clean {label}: host {sides[0]}, peer {sides[1]}, edges lost {missed}, least slack {slack}; {time.monotonic()-started:.0f} s',flush=True)
  if not all(clean_ok(side) for side in sides) or any(missed):failures.append(('clean',label,sides,missed))
 for kind,receiver in (('flip',0),('flip',1),('drop',1),('unplug',None)):
  started=time.monotonic()
  before,after,injected=faulted(rom,kind,receiver)
  print(f'{kind} {receiver}: before {before}, after {after}, injected {injected}; {time.monotonic()-started:.0f} s',flush=True)
  recovered=all(a['good']>=b['good']+15 for a,b in zip(after,before))
  if kind=='flip':
   hit,other=after[receiver],after[1-receiver]
   ok=hit['crc_errors']==1 and hit['seq_errors']==0 and hit['first_code']==1 and clean_ok(other)
  elif kind=='drop':
   ok=not any(side['timeouts'] for side in after)
  else:
   # The unplugged peer gets no clock, so its packets wait; the host's are lost.
   ok=after[0]['dropouts']==1 and after[1]['dropouts']==0 and after[1]['seq_errors']>=1 and not any(side['timeouts'] for side in after)
  if not (ok and recovered):failures.append((kind,receiver,before,after))
 assert not failures,failures
 print('Link over a free-running cable: no lost edge or error at either CPU speed on each end, a flipped bit is one CRC error, '
       'a dropped edge recovers, and a 40-frame unplug is one host dropout with packets missing at the peer')

if __name__=='__main__':main()
