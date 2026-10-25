"""Two benches face each other: one sends Infrared bursts, the other counts edges.

The receiver must count every pulse of each transmit preset, with its frames
at three offsets from the sender's. It may stop reading the port once a
frame for its VBlank work, and for its redraw just after a burst. A burst
that arrives during either loses the pulses sent then, so the offsets keep
the bursts clear of the VBlank work.
Uses the two-console harness in two_consoles.py.
"""
from pathlib import Path
import shutil,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from cart import ROMS,symbols
from two_consoles import Pair,Infrared,FRAME,run_frames,press

IR_TEST=9
# Longest wait between two reads of the port: a 48-cycle pulse fits in none.
SAMPLE_GAP=56
# Longest time a frame's VBlank work keeps the receiver off the port.
FRAME_GAP=3000
# How soon after a burst the receiver's redraw starts.
REDRAW_AFTER=2*FRAME

def row(pb,y):return ''.join(chr(t+32) if t<96 else '#' for t in pb.memory[0,0x9800+y*32:0x9814+y*32])
def text(pb):return '\n'.join(row(pb,y) for y in range(18))

def open_preset(pb,syms,choice):
 for _ in range(12):
  if pb.memory[syms['_selected_test']]==IR_TEST:break
  press(pb,'right')
 else:raise AssertionError('browser never reached Infrared')
 press(pb,'a');assert 'presets' in row(pb,5),text(pb)
 first=1 if 'Manual' in text(pb) else 0
 for _ in range(choice-first):press(pb,'down')
 press(pb,'a');assert 'INFRARED' in text(pb).upper(),text(pb)

def run(rom,preset,offset,bursts=3):
 """Returns pulses sent, edges counted, pulses per burst, and the receiver's
 gaps between port reads longer than SAMPLE_GAP."""
 syms=symbols(rom)
 get=lambda pb,name,size=1:int.from_bytes(bytes(pb.memory[syms['_'+name]:syms['_'+name]+size]),'little')
 with tempfile.TemporaryDirectory() as d:
  paths=[Path(d)/f'{i}.gbc' for i in range(2)]
  for path in paths:shutil.copy(rom,path)
  pair=Pair(paths);ir=Infrared(pair)
  try:
   sender,receiver=pair.machines
   for pb in pair.machines:run_frames(pb,240)
   open_preset(sender,syms,preset)
   open_preset(receiver,syms,1)
   press(receiver,'a');assert get(receiver,'ir_running') and not get(receiver,'ir_mode')
   pair.start(step_cycles=8,offset=offset)
   reads=[];read=receiver.mb.ir_read
   receiver.mb.ir_read=lambda:(reads.append(pair.now(1)),read())[1]
   pair.press(0,'a')
   pair.run_until(lambda:get(sender,'ir_bursts',2)>=bursts,(bursts+1)*121*FRAME)
   end=pair.now(0)
   pair.run_until(lambda:pair.now(1)>end+2*FRAME,4*FRAME)
   gaps=[(a,b) for a,b in zip(reads,reads[1:]) if b-a>SAMPLE_GAP]
   # A burst ends with a pulse followed by a long dark stretch.
   offs=[t for t,on in zip(ir.changes[0],ir.lit[0]) if not on]
   ends=[t for t,n in zip(offs,offs[1:]+[float('inf')]) if n-t>FRAME_GAP]
   redraws=[(a,b) for a,b in gaps if b-a>FRAME_GAP and any(e<=a<=e+REDRAW_AFTER for e in ends)]
   gaps=[b-a for a,b in gaps if (a,b) not in redraws]
   return ir.pulses(0),get(receiver,'ir_edges',2),get(sender,'ir_pulses'),gaps,(reads[-1]-reads[0])/FRAME,len(redraws)
  finally:pair.close()

def main():
 rom=Path(sys.argv[1]) if len(sys.argv)>1 else ROMS['mbc5']
 failures=[]
 for preset,name in ((2,'Short bursts'),(4,'Dense bursts')):
  for offset in (FRAME//4,FRAME//2,3*FRAME//4):
   started=time.monotonic()
   sent,counted,per_burst,gaps,frames,redraws=run(rom,preset,offset)
   print(f'{name} offset {offset}: sent {sent} pulses ({per_burst} per burst), counted {counted} edges; '
         f'{len(gaps)} gaps over {SAMPLE_GAP} cycles in {frames:.0f} frames, longest {max(gaps,default=0):.0f}, '
         f'{redraws} redraws after bursts; '
         f'{time.monotonic()-started:.0f} s',flush=True)
   assert sent>=3*per_burst,(sent,per_burst)
   if counted!=sent:failures.append((name,offset,'counted',counted,'of',sent))
   if len(gaps)>frames+1 or max(gaps,default=0)>FRAME_GAP:failures.append((name,offset,'gaps',len(gaps),max(gaps,default=0)))
 assert not failures,failures
 print(f'Infrared receive counts every pulse of each transmit preset at three frame offsets, '
       f'reading the port every {SAMPLE_GAP} cycles or sooner outside one VBlank gap of at most {FRAME_GAP} per frame '
       f'and a redraw after each burst')

if __name__=='__main__':main()
