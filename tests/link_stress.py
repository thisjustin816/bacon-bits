"""Link's rate presets, Custom pacing and masked workload over a free-running cable.

Uses the cable of two_consoles.py, where an edge that finds the peer
unarmed is lost. Each case runs both benches for 420 frames and reads the
counters and the bytes each end took, at normal and at double speed.

The Paced, Burst and Full presets, on either wire, must stay clean and move
the bytes the build before Custom pacing moved, within 3%: Full moves about
1.5% fewer, the cost of the 32-bit interval clock. Custom bursts of 8 bytes
with 488 us between them must stay clean and move at least 1.2 times the
Burst preset's bytes; the loop's own work, not the burst, limits both. With 8 lines masked each frame on both ends, as the
Busy game preset sets, Burst must stay clean, while Custom All with no idle
loses the bytes that arrive while the peer's interrupts are off and fails.
64 masked lines on the host must stay clean and only slow it, as the host
sends nothing while its own interrupts are off.
"""
from pathlib import Path
import sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from cart import ROMS
from link_pair import start,counters,run_frames_paired,clean_ok

# Rows on the second setup page, in the order setup() steps through them.
BURST_DEFAULT,IDLE_DEFAULT=4,6
IDLE_0US,IDLE_488US=0,4
MASKED_8,MASKED_64=4,7
# Peer bytes in 420 frames on the build before Custom pacing (dc0f716), by CPU speed.
BASELINE={0:{'Paced':340,'Burst':639,'Full':896,'Full on the fast wire':896},
          1:{'Paced':386,'Burst':1236,'Full':1456,'Full on the fast wire':1456}}

def custom(burst=None,idle=None,masked=(0,0)):
 """A setup() for start() that sets Burst and Idle on the host and the
 masked-lines step on each end. The cursor starts on the CPU row."""
 def setup(index,press):
  press('down')
  if index==0 and burst is not None:
   for _ in range((burst-BURST_DEFAULT)%17):press('right')
  press('down')
  if index==0 and idle is not None:
   for _ in range((idle-IDLE_DEFAULT)%8):press('right')
  press('down')
  for _ in range(masked[index]):press('right')
 return setup

def measure(rom,**settings):
 with tempfile.TemporaryDirectory() as d:
  pair,syms=start(rom,d,**settings)
  try:
   run_frames_paired(pair,420)
   return counters(pair,syms),list(pair.cable.missed),list(pair.cable.bytes)
  finally:pair.close()

def failed(side):
 return any(side[name] for name in ('crc_errors','seq_errors','data_errors','timeouts','first_code'))

# Each case: label, settings, whether it must fail, and a case whose peer
# byte count this one's must exceed by a factor (above 1) or stay under.
CASES=(
 ('Paced',dict(rate=0),False,None),
 ('Burst',dict(rate=1),False,None),
 ('Full',dict(rate=2),False,None),
 ('Full on the fast wire',dict(rate=2,link=1),False,None),
 ('Custom 8 bytes, 488 us idle',dict(rate=3,setup=custom(burst=8,idle=IDLE_488US)),False,('Burst',1.2)),
 ('Burst, 8 lines masked',dict(rate=1,setup=custom(masked=(MASKED_8,MASKED_8))),False,None),
 ('Custom All, no idle, 8 lines masked',dict(rate=3,setup=custom(burst=0,idle=IDLE_0US,masked=(MASKED_8,MASKED_8))),True,None),
 ('Full, host masks 64 lines',dict(rate=2,setup=custom(masked=(MASKED_64,0))),False,('Full',0.9)),
)

def main():
 rom=Path(sys.argv[1]) if len(sys.argv)>1 else ROMS['mbc5']
 failures=[]
 for cpu in (0,1):
  results={}
  for label,settings,fails,compare in CASES:
   started=time.monotonic()
   sides,missed,taken=measure(rom,host_cpu=cpu,peer_cpu=cpu,**settings)
   results[label]=taken[1]
   print(f'{cpu+1}x {label}: host {sides[0]}, peer {sides[1]}, edges lost {missed}, bytes taken {taken}; {time.monotonic()-started:.0f} s',flush=True)
   if fails:ok=any(missed) and any(failed(side) for side in sides)
   else:ok=all(clean_ok(side) for side in sides) and not any(missed)
   if label in BASELINE[cpu]:
    base=BASELINE[cpu][label];ok=ok and abs(taken[1]-base)<=0.03*base
   if compare:
    other,factor=compare;bound=factor*results[other]
    ok=ok and (taken[1]>=bound if factor>1 else taken[1]<bound)
   if not ok:failures.append((cpu,label,sides,missed,taken))
 assert not failures,failures
 print('Link stress: the presets pace as before Custom pacing and stay clean, an 8-byte Custom burst moves more than Burst, '
       '8 masked lines stay clean at Burst and fail with no idle, and masked lines on the host only slow it, at both CPU speeds')

if __name__=='__main__':main()
