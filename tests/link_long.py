"""Link intervals longer than sys_time's 65536-frame wrap.

Two benches run Link under All stress over the free-running cable of
two_consoles.py. Each console's frame counter starts 64 frames short of its
wrap, so ordinary intervals cross it, and those must not read as gaps. Two
seconds in, the cable is unplugged and each counter moves forward 20000
frames at a time, four times, as 22 minutes of silence would. Then the cable
goes back in. The gap, the recovery and the host's wait for a reply must each
count all of the 80000 frames, not the remainder past 65536, and the first
failure recorded during the silence must still be there afterwards.
"""
from pathlib import Path
import shutil,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'vendor/link-sustain/tests'))
from cart import ROMS,symbols
from rom_helpers import configure
from two_consoles import Pair,FRAME,run_frames,press
from link_pair import LINK_TEST,run_frames_paired

JUMP,JUMPS=20000,4
NO_SYNC=5

def main():
 rom=Path(sys.argv[1]) if len(sys.argv)>1 else ROMS['mbc5']
 syms=symbols(rom)
 with tempfile.TemporaryDirectory() as d:
  paths=[Path(d)/f'{i}.gbc' for i in range(2)]
  for path in paths:shutil.copy(rom,path)
  pair=Pair(paths,cable=True)
  try:
   # A build from before the 32-bit clock keeps these intervals in 16 bits.
   wide=4 if '_clock_frames' in syms else 2
   sizes={'max_gap':wide,'max_recovery':wide,'max_reply':wide}
   def get(pb,name,size=1):size=sizes.get(name,size);return int.from_bytes(bytes(pb.memory[syms['_'+name]:syms['_'+name]+size]),'little')
   def set_time(pb,value):
    at=syms['_sys_time'];pb.memory[at]=value&0xff;pb.memory[at+1]=(value>>8)&0xff
   for index,pb in enumerate(pair.machines):
    run_frames(pb,240)
    for _ in range(12):
     if get(pb,'selected_test')==LINK_TEST:break
     press(pb,'right')
    press(pb,'a');press(pb,'a')
    configure(lambda name,size=1,pb=pb:get(pb,name,size),lambda key,pb=pb:press(pb,key),host=index==0,test=4,rate=1,cpu=0)
    set_time(pb,0x10000-64)
   pair.start(step_cycles=64)
   pair.press(1,'start')
   started=pair.machines[1].frame_count
   pair.run_until(lambda:pair.machines[1].frame_count>=started+30,60*FRAME)
   pair.press(0,'start')
   run_frames_paired(pair,120)
   before=[{n:get(pb,n,4) for n in ('good','timeouts','max_gap')} for pb in pair.machines]
   wrapped=[get(pb,'sys_time',2)<0x8000 for pb in pair.machines]
   pair.cable.connected=False
   run_frames_paired(pair,4)
   for _ in range(JUMPS):
    for pb in pair.machines:set_time(pb,get(pb,'sys_time',2)+JUMP)
    run_frames_paired(pair,2)
   first=[(get(pb,'first_code'),get(pb,'first_sec',4)) for pb in pair.machines]
   pair.cable.connected=True
   run_frames_paired(pair,300)
   after=[{n:get(pb,n,4) for n in ('good','timeouts','max_gap','max_recovery','max_reply')} for pb in pair.machines]
   kept=[(get(pb,'first_code'),get(pb,'first_sec',4)) for pb in pair.machines]
  finally:pair.close()
 print('before',before,'wrapped',wrapped);print('first',first,'kept',kept);print('after',after,flush=True)
 silence=JUMP*JUMPS
 assert all(wrapped),'The frame counter did not wrap during the clean run'
 assert all(side['good']>10 and not side['timeouts'] and side['max_gap']<120 for side in before),('A wrap read as a gap',before)
 assert all(side['good']>before[i]['good']+10 for i,side in enumerate(after)),('Link did not recover',after)
 assert all(side['max_gap']>=silence and side['max_recovery']>=silence for side in after),('Gap or recovery wrapped',after)
 assert after[0]['max_reply']>=silence,('Reply wait wrapped',after[0])
 assert all(code==NO_SYNC for code,_ in first) and kept==first,('First failure changed after recovery',first,kept)
 print(f'Link: a frame-counter wrap is no gap, and a {silence}-frame silence counts in full as gap, recovery and reply wait; the first failure survives recovery')

if __name__=='__main__':main()
