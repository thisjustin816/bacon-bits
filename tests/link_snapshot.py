"""Link's first-failure snapshot over a free-running cable.

Uses the cable of two_consoles.py. The peer starts alone and waits 150
frames, longer than the 120 that count as no sync. That wait is not a
failure, a gap or a recovery: the peer's views must say so, and the first
packet must clear it. Then the host starts, and once packets flow a bit is
flipped in a payload byte the peer receives. The
peer's snapshot must hold that packet, its sync bytes first and its CRC
bytes those the CRC view reports as received, with the settings in use and
the serial registers read when the failure opened. It must not change while
the link recovers, while the views and pages change, or after a stop.

The snapshot runs once a test, outside the serial interrupt. Its cost is
timed on one console stepped an instruction at a time: a peer waiting alone
latches its no-sync through the same path. The cycles are printed and must
stay under 2500, under 4% of a frame.
"""
from pathlib import Path
import shutil,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
from cart import ROMS,symbols
from link_pair import start,run_frames_paired
from two_consoles import pyboy_module,run_frames,press

SNAPSHOT=(('snap_regs',6),('snap_wr',1),('snap_rd',1),('snap_active',1),('snap_txpos',1),('snap_pending',1),('snap_command',1),
          ('snap_host',1),('snap_rate',1),('snap_burst',1),('snap_idle',1),('snap_masked',1),('snap_rejected',1),('snap_bytes',16))
PEER=1

def snapshot_cost(rom):
 """CPU cycles from latch()'s entry to its return when it opens the first
 failure. The harness's pure-Python PyBoy counts cycles, and stepping it
 one instruction at a time finds both addresses."""
 syms=symbols(rom)
 with tempfile.TemporaryDirectory() as d:
  path=Path(d)/'cost.gbc';shutil.copy(rom,path)
  p=pyboy_module().PyBoy(str(path),window='null',sound_emulated=False);p.set_emulation_speed(0)
  cpu=p.mb.cpu
  def get(name):return p.memory[syms['_'+name]]
  def step_to(pc,bank,frames):
   p.mb.step_cycles=1
   for _ in range(frames*70224):
    p.mb.tick()
    if p.mb.lcd.frame_done:p.mb.lcd.frame_done=False;p.frame_count+=1
    if cpu.PC==pc and (pc<0x4000 or p.mb.cartridge.rombank_selected==bank):return cpu.cycles
   raise AssertionError(('never reached',hex(pc)))
  try:
   run_frames(p,240)
   while get('selected_test')!=1:press(p,'right')
   press(p,'a',after=60);press(p,'a',after=60);press(p,'left')
   assert not get('host')
   # The peer waits alone; 120 frames without a packet open its first failure.
   press(p,'start',after=100)
   latch=syms['_latch']
   entered=step_to(latch&0xffff,latch>>16,60)
   assert not get('first_code')
   back=p.memory[cpu.SP]|p.memory[cpu.SP+1]<<8
   returned=step_to(back,latch>>16,2)
   assert get('first_code')==5,get('first_code')
  finally:p.stop(save=False)
 return returned-entered

def main():
 rom=Path(sys.argv[1]) if len(sys.argv)>1 else ROMS['mbc5']
 cycles=snapshot_cost(rom)
 with tempfile.TemporaryDirectory() as d:
  pair,syms=start(rom,d,host_wait=150)
  pb=pair.machines[PEER]
  def get(name,size=1):at=syms['_'+name];return int.from_bytes(bytes(pb.memory[at:at+size]),'little')
  def snapshot():return {name:bytes(pb.memory[syms['_'+name]:syms['_'+name]+size]) for name,size in SNAPSHOT}
  def rows():return '\n'.join(''.join(chr(t+32) if t<96 else '#' for t in pb.memory[0,0x9800+y*32:0x9814+y*32]) for y in range(18))
  shown=[0]
  def view(detail):
   # A steps through page one's eight views. The peer shows the first after a
   # start, and a page change returns to it.
   while shown[0]!=detail:pair.press(PEER,'a');run_frames_paired(pair,20);shown[0]=(shown[0]+1)%8
   return rows()
  try:
   waited=(get('first_code'),get('good',4),get('timeouts',4))
   wait_view=view(4)
   run_frames_paired(pair,120)
   flowing=get('good',4);connected=(get('first_code'),get('timeouts',4),get('max_recovery',4))
   pair.cable.flip_in_packet(PEER,8)
   run_frames_paired(pair,60)
   first=snapshot();code=get('first_code');received=get('first_received_crc',2)
   failure_views=[view(n) for n in (4,5,6,7)]
   run_frames_paired(pair,240)
   recovered=get('good',4)
   for key in ('right','left','right','right','left','left'):pair.press(PEER,key);run_frames_paired(pair,15)
   shown[0]=0
   after_views=snapshot()
   pair.press(PEER,'b');run_frames_paired(pair,30)
   stopped=(get('running'),snapshot())
  finally:pair.close()
 print('waited',waited,'flowing',flowing,'recovered',recovered,'code',code)
 print({k:v.hex() for k,v in first.items()})
 print('snapshot cycles',cycles)
 for text in failure_views:print('\n'.join(text.split('\n')[4:16]))
 assert waited==(5,0,0) and 'No failure yet' in wait_view,('The initial wait read as a failure',waited,wait_view)
 assert connected==(0,0,0),('The initial wait outlived the first packet as a failure, gap or recovery',connected)
 assert flowing>10 and code==1,('No CRC failure after packets flowed',flowing,code)
 bytes_=first['snap_bytes']
 assert first['snap_rejected']==b'\1' and bytes_[:2]==b'\xd3\x91' and int.from_bytes(bytes_[13:15],'little')==received,('Snapshot is not the rejected packet',bytes_.hex(),hex(received))
 assert first['snap_host']==b'\0' and first['snap_rate']==b'\1' and first['snap_burst']==b'\4' and first['snap_masked']==b'\0',('Settings in use not kept',first)
 assert first['snap_regs'][1]&0x81==0x80,('Peer SC was not armed on the external clock',first['snap_regs'].hex())
 assert recovered>flowing+10,('Link did not recover',flowing,recovered)
 assert after_views==first and stopped==(0,first),('Snapshot changed after recovery, page changes or stop',after_views,stopped)
 assert 'SB SC' in failure_views[0] and 'RX in' in failure_views[1] and 'Burst' in failure_views[2] and 'D3 91' in failure_views[3],failure_views
 assert cycles<2500,('Snapshot cost',cycles)
 print(f'Link: the initial wait is not a failure; a flipped bit leaves a snapshot of the rejected packet, registers, positions and settings, '
       f'unchanged through recovery, page changes and a stop; the snapshot took {cycles} cycles')

if __name__=='__main__':main()
