"""Slowdown burns a known share of each update; every count must match the arithmetic.

The expected values come from the cycle arithmetic below, never from the
cartridge's own schedule. One iteration of the burn loop costs 28 cycles and
2,508 of them fill a 70,224-cycle frame, so a load of L percent runs
round(2508 x L / 100) iterations, twice that at double speed, where a frame
is 140,448 CPU cycles. Each update also spends OVERHEAD cycles that are not
burn: the VBlank that wakes it, GBDK's handler, the readout and the loop's
own work. A VBlank that lands while an update works is a lag frame and costs
INTERRUPT cycles more. An update of n iterations takes k lag frames, the
smallest k with OVERHEAD + 28n + k x INTERRUPT < (k + 1) x frame.

Three counts must agree with that table at every update: the cartridge's
VBlank handler (slow_lag), its gaps between wakes (slow_tick_lag) and this
suite's own test at the VBlank vector, where the byte before the interrupted
address is HALT ($76) only when the loop was idle. The handler clears its busy
flag one instruction before the HALT, so an update whose work ends within that
instruction of a VBlank reads as idle to the handler and as lag to the other
two. No case here comes within MARGIN cycles of a frame boundary, and the
suite stops if the pinned windows would put one there.

PyBoy runs everything; --core runs the counting cases in SameBoy instead,
which has no hooks, so there the handler and gap counts are compared with the
table after each run. Both are emulators: these results are not hardware.
Case names on the command line run only those parts.
"""
import argparse,ctypes,io,re,sys
from pathlib import Path
from cart import Cart,ROMS,ROOT,symbols
a=argparse.ArgumentParser();a.add_argument('--core',type=Path);a.add_argument('--rom',type=Path,default=ROMS['mbc5']);a.add_argument('--mbc3',type=Path,default=ROMS['mbc3'])
a.add_argument('parts',nargs='*',help='table, threshold, cycles, controls, cleanup (all of them by default)');args=a.parse_args()

FRAME=70224;LOOP=28;FRAME_LOOPS=2508
# Measured on the first build: the smallest burn that lags is 2,388
# iterations at normal speed and 4,896 at double, so the overhead to the busy
# flag lies in this window at both speeds. Two lag frames start at 4,815.
OVERHEAD=(3360,3388)
INTERRUPT=(2240,2296)
MARGIN=56
# The readout handler's cycles from entry to return, whatever the counts hold.
HANDLER_CYCLES=1044
SLOWDOWN=12
PATTERNS={'steady':0,'pulse':1,'ramp':2}

def loops(percent,fast=False):
 n=(percent*FRAME_LOOPS+50)//100
 return 2*n if fast else n
def lag_frames(n,fast=False):
 frame=FRAME*(2 if fast else 1);found=set()
 for overhead in OVERHEAD:
  for interrupt in INTERRUPT:
   k=0
   while overhead+LOOP*n+k*interrupt>=(k+1)*frame:k+=1
   for j in range(k+1):
    gap=overhead+LOOP*n+j*interrupt-(j+1)*frame
    if abs(gap)<MARGIN:raise AssertionError(('Case inside the boundary band',n,fast,overhead,interrupt,gap))
   found.add(k)
 assert len(found)==1,('Lag depends on where the overhead lies in its window',n,found)
 return found.pop()
def schedule(pattern,load,base=50,heavy=4,light=4,steps=30,fast=False):
 """The burn of each update in one cycle of the pattern, in iterations."""
 high,low=loops(load,fast),loops(base,fast)
 if pattern=='steady':return [high]
 if pattern=='pulse':return [high]*heavy+[low]*light
 span=abs(high-low);sign=1 if high>=low else -1
 return [low+sign*(span*i//(steps-1)) for i in range(steps)]
def busy_text(load,fast=False):
 """The settings page's prediction for Load, as the arithmetic gives it."""
 frame=FRAME*(2 if fast else 1);shares={round((LOOP*loops(load,fast)+o)*100/frame) for o in OVERHEAD}
 assert len(shares)==1,('Busy share depends on where the overhead lies',load,shares)
 lag=lag_frames(loops(load,fast),fast)
 return f'Busy {shares.pop()}%: '+(f'{lag} in {lag+1}' if lag else 'no lag')
def bcd(raw):
 """Packed BCD, least significant byte first; a byte that is not BCD stops the suite."""
 text=bytes(reversed(raw)).hex()
 assert text.isdigit(),('Counter is not BCD',text)
 return int(text)

def wanted(parts):return not args.parts or any(p in args.parts for p in parts)

class Bench(Cart):
 """A bench booted to the browser, with Slowdown's counters read by symbol."""
 def __init__(self,rom=args.rom,cgb=True):
  super().__init__(rom,cgb);self.cgb=cgb
  for name in ('_slow_burn','_slow_vbl','_slow_update','_slow_frames','_slow_lag','_slow_tick_lag','_slow_window','.int_0x40'):
   if name not in self.syms:raise AssertionError(('Slowdown symbol missing from this build',name))
 def counter(self,name):at=self.syms['_'+name];return bcd(bytes(self.p.memory[at:at+3]))
 def put(self,name,value):self.p.memory[self.syms['_'+name]]=value
 def handlers(self):
  at=self.syms['.int_0x40'];found=[]
  while True:
   entry=self.p.memory[at]|self.p.memory[at+1]<<8
   if not entry:return found
   found.append(entry);at+=2
 def settings(self,pattern,load,base=50,heavy=4,light=4,steps=30,fast=False):
  """Open Slowdown on its settings and set them in memory, as the rows would."""
  self.go(SLOWDOWN);self.preset(1);assert 'Slowdown' in self.row(4),self.text()
  self.ie=self.p.memory[0xffff]
  for name,value in (('slow_pattern',PATTERNS[pattern]),('slow_load',load//5),('slow_base',base//5),('slow_heavy',heavy),('slow_light',light),('slow_steps',steps),('slow_fast',int(fast))):self.put(name,value)
 def cleaned(self,context):
  """After a run: the handler is gone, only VBlank interrupts on, CPU at normal speed."""
  assert not self.get('slow_running'),(context,'Still running')
  assert self.syms['_slow_vbl'] not in self.handlers(),(context,'VBlank handler left installed',self.handlers())
  assert self.p.memory[0xffff]==self.ie,(context,'Interrupt enable not restored',hex(self.p.memory[0xffff]),hex(self.ie))
  # A DMG has no KEY1 and reads it as FF.
  assert not self.cgb or not self.p.memory[0xff4d]&0x80,(context,'CPU left at double speed')

class Recorder:
 """Counts at each update's burn and the HALT test at each VBlank of a run."""
 def __init__(self,c):
  self.c=c;p=c.p;self.updates=[];self.vblanks={};self.force=None
  def vector(_):
   if not c.get('slow_running'):return
   sp=p.register_file.SP;back=p.memory[sp]|p.memory[sp+1]<<8
   # Keyed by the VBlank's number in the run; the handler has not counted it yet.
   self.vblanks[c.counter('slow_frames')+1]=(p.memory[(back-1)&0xffff]!=0x76,c.get('slow_run'))
  p.hook_register(0,0x40,vector,None)
  def burn(_):
   if self.force is not None:p.register_file.D=self.force>>8;p.register_file.E=self.force&0xff
   self.updates.append(dict(n=p.register_file.D<<8|p.register_file.E,frames=c.counter('slow_frames'),lag=c.counter('slow_lag'),
    tick=c.get('slow_tick_lag',3),run=c.get('slow_run'),longest=c.get('slow_longest'),window=c.get('slow_window'),shown=(c.row(10)[11:17],c.row(12)[11:17])))
  p.hook_register(0,c.syms['_slow_burn'],burn,None)
 def run(self,updates,limit=6000):
  self.updates.clear();self.vblanks.clear()
  self.c.press('a',after=0)
  for _ in range(limit):
   if len(self.updates)>updates:return
   self.c.tick()
  raise AssertionError(('Run never reached its updates',updates,len(self.updates),self.c.text()))

def check_run(rec,expected,fast,context):
 """Every update against the table: burn, the three lag counts, Run, Max, the readout and the 64-frame window."""
 ups=rec.updates;busy={v:b for v,(b,_) in rec.vblanks.items()}
 table=[lag_frames(n,fast) for n in expected]
 for j,(u,v) in enumerate(zip(ups,ups[1:])):
  where=(context,'update',j)
  assert u['n']==expected[j%len(expected)],(where,'Burn length',u['n'],expected[j%len(expected)])
  lag=table[j%len(table)]
  external=sum(busy[f] for f in range(u['frames']+1,v['frames']+1))
  counts=(v['lag']-u['lag'],v['tick']-u['tick'],external)
  assert counts==(lag,)*3,(where,'Lag frames: handler, gaps between wakes, HALT test',counts,'expected',lag)
  assert v['frames']-u['frames']==1+lag,(where,'Frames per update',v['frames']-u['frames'],lag)
  assert u['frames']==j+1+u['lag'] and u['tick']==u['lag'],(where,'Frames must equal updates plus lag',u)
  assert u['run']==0,(where,'Run not cleared by the idle VBlank that woke the loop',u['run'])
  assert u['longest']==max([table[i%len(table)] for i in range(j)],default=0),(where,'Max',u['longest'])
  # The handler draws first and counts after, so the screen trails the counts by the waking VBlank.
  assert u['shown']==(f"{u['frames']-1:06d}",f"{u['lag']:06d}"),(where,'Readout',u['shown'],u['frames'],u['lag'])
  blocks=u['frames']//64
  if blocks:
   block=sum(busy.get(f,False) for f in range((blocks-1)*64+1,blocks*64+1))
   assert int(f"{u['window']:02x}")==block,(where,'Lag in the last 64-frame block',hex(u['window']),block)
 # Run before each VBlank is the number of lag frames just before it.
 assert sorted(busy)==list(range(1,len(busy)+1)),(context,'The HALT test missed a VBlank')
 run=0
 for f in sorted(busy):
  assert rec.vblanks[f][1]==run,(context,'Run before VBlank',f,rec.vblanks[f][1],run)
  run=run+1 if busy[f] else 0
 return sum(table[j%len(table)] for j in range(len(ups)-1))

def table_cases():
 # Steady loads on both sides of one and two lag frames, and the patterns, each over whole pattern cycles.
 cases=[(True,False,'steady',p,{}) for p in (75,95,100,105,125,150,185,200)]
 cases+=[(True,False,'pulse',125,dict(base=50,heavy=4,light=4)),(True,False,'pulse',125,dict(base=50,heavy=1,light=1)),
  (True,False,'ramp',150,dict(base=25,steps=60)),(True,False,'ramp',200,dict(base=150,steps=10)),
  (True,True,'steady',95,{}),(True,True,'steady',125,{}),(True,True,'steady',200,{}),(True,True,'pulse',125,dict(base=50,heavy=4,light=4)),
  (False,False,'steady',125,{}),(False,False,'pulse',125,dict(base=50,heavy=4,light=4)),(False,False,'ramp',150,dict(base=25,steps=60))]
 for cgb,fast,pattern,load,extra in cases:
  expected=schedule(pattern,load,fast=fast,**extra)
  # Whole pattern cycles covering about 600 frames.
  per_cycle=len(expected)+sum(lag_frames(n,fast) for n in expected)
  cycles=max(1,600//per_cycle)
  c=Bench(cgb=cgb)
  try:
   c.settings(pattern,load,fast=fast,**extra);rec=Recorder(c);rec.run(cycles*len(expected))
   lag=check_run(rec,expected,fast,(cgb,fast,pattern,load,extra))
   ups=rec.updates
   print(f"{'CGB' if cgb else 'DMG'} {'double' if fast else 'normal'} {pattern} {load}% {extra or ''}: {len(ups)-1} updates, "
         f"{ups[-1]['frames']-ups[0]['frames']} frames, {lag} lag frames by handler, gaps and HALT test",flush=True)
   c.press('b');c.cleaned((pattern,load,fast))
  finally:c.close()

def threshold(start,end,lags,fast=False,poke=None):
 """The smallest forced burn whose updates each take lags lag frames by the handler's count."""
 def probe(n):
  c=Bench()
  try:
   c.settings('steady',75,fast=fast);rec=Recorder(c);rec.force=n
   if poke:
    c.press('a',after=0);c.tick(3);poke(c);rec.updates.clear();rec.vblanks.clear()
    for _ in range(400):
     if len(rec.updates)>12:break
     c.tick()
   else:rec.run(12)
   ups=rec.updates[2:]
   return {b['lag']-a['lag'] for a,b in zip(ups,ups[1:])}
  finally:c.close()
 lo,hi=start,end
 while lo<hi:
  mid=(lo+hi)//2
  if max(probe(mid))>=lags:hi=mid
  else:lo=mid+1
 return lo

def threshold_cases():
 frame=FRAME
 n=threshold(2300,2508,1);assert frame-LOOP*n>=OVERHEAD[0] and frame-LOOP*(n-1)<=OVERHEAD[1]+LOOP,('Overhead moved',n,frame-LOOP*n)
 assert n==2388,('Lag threshold moved from the pinned overhead',n)
 fast=threshold(4700,5016,1,fast=True);assert fast==4896,('Double-speed threshold moved',fast)
 two=threshold(4700,5016,2);assert two==4815,('Two-lag threshold moved',two)
 assert OVERHEAD[0]+INTERRUPT[0]<=2*frame-LOOP*two<=OVERHEAD[1]+INTERRUPT[1],('Interrupt cost outside its window',2*frame-LOOP*two)
 # Counts that carry through every digit must cost the readout nothing.
 def carry(c):
  for name,value in (('slow_frames',[0x98,0x99,0x09]),('slow_lag',[0x99,0x99,0x09]),('slow_window_count',0x63)):
   at=c.syms['_'+name]
   if isinstance(value,list):c.p.memory[at:at+3]=value
   else:c.p.memory[at]=value
 carried=threshold(2300,2508,1,poke=carry);assert carried==n,('Threshold moved with counts that carry',carried,n)
 print(f'Thresholds: one lag frame from {n} iterations ({frame-LOOP*n} to {frame-LOOP*(n-1)} cycles of overhead), {fast} at double speed, '
       f'two from {two}; the same with counts that carry through every digit',flush=True)

def cycle_cases():
 """Exact cycles on a pure-Python PyBoy, stepped one instruction at a time from a saved run."""
 from two_consoles import pyboy_module
 def stepped(pattern,load,poke=None,vblanks=70,**extra):
  c=Bench();c.settings(pattern,load,**extra);c.press('a',after=0);c.tick(20)
  if poke:poke(c)
  state=io.BytesIO();c.p.save_state(state);syms=c.syms;c.close()
  pb=pyboy_module().PyBoy(str(args.rom),window='null',sound_emulated=False,cgb=True)
  try:
   state.seek(0);pb.load_state(state);mb=pb.mb;mb.step_cycles=1
   entry,burn=syms['_slow_vbl'],syms['_slow_burn'];handler=[];overhead=[];start=back=wake=None
   for _ in range(vblanks*80000):
    if len(handler)>=vblanks:break
    pc=mb.cpu.PC
    if pc==0x40:wake=mb.cpu.cycles
    if pc==entry and start is None:
     sp=mb.cpu.SP;back=mb.getitem(sp)|mb.getitem(sp+1)<<8;start=mb.cpu.cycles;ly=mb.getitem(0xff44)
    elif start is not None and pc==back:
     handler.append((mb.cpu.cycles-start,ly,mb.getitem(0xff44)));start=None
    if pc==burn and wake is not None:overhead.append(mb.cpu.cycles-wake);wake=None
    mb.tick()
   assert len(handler)>=vblanks,('Stepping found too few VBlanks',len(handler))
   return handler,overhead
  finally:pb.stop(save=False)
 def carry(c):
  for name,value in (('slow_frames',[0x99,0x99,0x09]),('slow_lag',[0x99,0x99,0x09])):
   at=c.syms['_'+name];c.p.memory[at:at+3]=value
 # Over Steady 125% the VBlanks alternate busy and idle and a 64-frame block ends.
 for label,poke in (('counts with no carry',None),('counts that carry through every digit',carry)):
  handler,overhead=stepped('steady',125,poke)
  assert {h[0] for h in handler}=={HANDLER_CYCLES},(label,'Readout handler cycles',sorted({h[0] for h in handler}))
  assert all(144<=ly<=153 and 144<=end<=153 for _,ly,end in handler),(label,'Handler ran outside VBlank',handler[:4])
 # Pulse takes both paths of the schedule step: the overhead of every update must match.
 handler,overhead=stepped('pulse',75,base=50,heavy=3,light=2,vblanks=24)
 assert len(set(overhead))==1,('Update overhead differs between schedule paths',sorted(set(overhead)))
 print(f'Readout handler: {HANDLER_CYCLES} cycles on every VBlank, busy or idle, at a block end and with counts that carry, '
       f'inside VBlank (LY {min(h[1] for h in handler)} to {max(h[2] for h in handler)}); '
       f'{overhead[0]} cycles from the waking VBlank to the burn on every Pulse update',flush=True)

def control_cases():
 c=Bench()
 try:
  presets={1:dict(slow_pattern=0,slow_load=15),2:dict(slow_pattern=0,slow_load=25),3:dict(slow_pattern=1,slow_load=25,slow_base=10,slow_heavy=4,slow_light=4),
           4:dict(slow_pattern=2,slow_load=30,slow_base=5,slow_steps=60)}
  c.go(SLOWDOWN);c.press('a');text=c.text()
  assert 'Slowdown presets' in c.row(4) and 'Manual' in text and all(n in text for n in ('Under budget','Over budget','Pulse','Ramp')),text
  assert c.row(17).strip()=='Steady 75%',('First visit starts on Under budget',c.row(17))
  c.press('b')
  for choice,want in presets.items():
   if choice>1:c.put('slow_fast',1)
   c.preset(choice);got={n:c.get(n) for n in want}
   assert got==want and not c.get('slow_fast') and not c.get('slow_running'),(choice,got,want)
   load=want['slow_load']*5;assert c.row(17).strip()==busy_text(load),(choice,c.row(17),busy_text(load))
   c.press('b')
  # Continue keeps a value set by hand.
  c.preset(2);c.press('right');assert c.get('slow_load')==26 and '130%' in c.row(6),c.row(6)
  c.press('b');c.preset(0);assert 'Slowdown' in c.row(4) and c.get('slow_load')==26 and not c.get('slow_running'),c.text()
  # Row limits.
  for _ in range(45):c.press('left',held=2,after=4)
  assert c.get('slow_load')==1 and '5%' in c.row(6),c.row(6)
  for _ in range(45):c.press('right',held=2,after=4)
  assert c.get('slow_load')==40 and '200%' in c.row(6),c.row(6)
  c.press('down');c.press('right');assert c.get('slow_pattern')==1 and 'Pulse' in c.row(8),c.row(8)
  c.press('down');c.press('right');assert c.get('slow_fast')==1 and 'Double' in c.row(10),c.row(10)
  c.press('right');assert not c.get('slow_fast')
  c.press('down');assert '50%' in c.row(12),c.row(12)
  for _ in range(45):c.press('left',held=2,after=4)
  assert c.get('slow_base')==1 and '5%' in c.row(12),c.row(12)
  c.press('up');c.press('up');c.press('left');assert c.get('slow_pattern')==0 and '-' in c.row(12)[11:19],c.row(12)
  c.press('select');assert '2/2' in c.row(4) and 'VBlank' in c.row(12),c.text()
  for row,name,low,high,unit in ((0,'slow_heavy',1,60,' upd'),(1,'slow_light',1,60,' upd'),(2,'slow_steps',2,60,'')):
   for _ in range(65):c.press('left',held=2,after=4)
   assert c.get(name)==low and c.row(6+2*row)[11:19].strip()==f'{low}{unit}',(name,c.row(6+2*row))
   for _ in range(65):c.press('right',held=2,after=4)
   assert c.get(name)==high and c.row(6+2*row)[11:19].strip()==f'{high}{unit}',(name,c.row(6+2*row))
   c.press('down')
  # The cursor never lands on Wait, the fixed row.
  assert c.row(6)[1]!=' ' and all(c.row(y)[1]==' ' for y in (8,10,12)),c.text()
  c.press('select');assert '1/2' in c.row(4)
  # B leaves for the browser on the fourth page.
  c.press('b');c.tick(20);assert c.get('selected_test')==SLOWDOWN and '4 of 4' in c.row(17),c.text()
 finally:c.close()
 # A DMG offers no double speed.
 c=Bench(cgb=False)
 try:
  c.go(SLOWDOWN);c.preset(1);c.press('down');c.press('down');c.press('right')
  assert not c.get('slow_fast') and 'Normal' in c.row(10),c.row(10)
 finally:c.close()
 print('Presets set every row and start nothing, Manual first then Continue keeps a hand-set Load, every row stops at its limits, '
       'Wait is fixed, the prediction matches the arithmetic and a DMG offers no double speed',flush=True)

def cleanup_cases():
 for rom,variant in ((args.rom,'mbc5'),(args.mbc3,'mbc3')):
  for cgb in (True,False):
   c=Bench(rom,cgb)
   try:
    fast=cgb
    c.settings('steady',125,fast=fast);rec=Recorder(c);rec.run(40)
    assert c.p.memory[0xff40]&2 and c.syms['_slow_vbl'] in c.handlers(),'Run without its markers or handler'
    assert ('Running x2' if fast else 'Running ') in c.row(15),c.row(15)
    # B stops and shows the share; the counts stop with it.
    c.press('b');c.cleaned((variant,cgb,'B'))
    frames,lag=c.counter('slow_frames'),c.counter('slow_lag');share=(lag*1000+frames//2)//frames
    assert 'Stopped' in c.row(15) and c.row(17).strip()==f'Share {share//10}.{share%10}%  Max {c.get("slow_longest")}',(c.row(17),frames,lag)
    assert (c.row(10)[11:17],c.row(12)[11:17])==(f'{frames:06d}',f'{lag:06d}'),('Final readout',c.row(10),c.row(12))
    c.tick(30);assert (c.counter('slow_frames'),c.counter('slow_lag'))==(frames,lag),'Counting went on after the stop'
    # Start goes back to settings and hides the markers; A runs again.
    c.press('start');assert 'Slowdown' in c.row(4) and not c.p.memory[0xff40]&2,c.text()
    c.press('a',after=60);assert c.get('slow_running')
    # The return chord stops the run before its dialog; Continue goes back to settings.
    c.hold(['a','b','start','select'],70);c.tick(30);assert 'Continue' in c.text(),c.text()
    c.cleaned((variant,cgb,'chord'));c.press('a');c.tick(30);assert 'Slowdown' in c.row(4),c.text()
    # Run again and leave by the chord for the test menu.
    c.press('a',after=60);c.leave();c.cleaned((variant,cgb,'menu'))
    assert c.get('selected_test')==SLOWDOWN and '4 of 4' in c.row(17),c.text()
    assert not c.p.memory[0xff40]&2 or all(c.p.memory[0xfe00+i*4]==0 for i in range(2)),'Markers left on the browser'
    # Frames stops before passing 999,999: the run ends itself.
    c.go(SLOWDOWN);c.preset(0);c.press('a',after=10)
    at=c.syms['_slow_frames'];c.p.memory[at:at+3]=[0x70,0x99,0x99]
    for _ in range(120):
     if 'Stopped' in c.row(15):break
     c.tick()
    c.cleaned((variant,cgb,'limit'));frames=c.counter('slow_frames')
    assert 999990<=frames<=999999 and c.row(10)[11:17]==f'{frames:06d}',('Limit',frames,c.text())
    print(f'{variant} {"CGB" if cgb else "DMG"}: B stops and shows the share, Start and the chord return, '
          f'and every exit removes the handler, restores interrupts and CPU speed; a run stops itself at {frames} frames',flush=True)
   finally:c.close()

def sameboy_cases():
 from libretro import SameBoy
 syms=symbols(args.rom)
 for model in ('Game Boy Color','Game Boy'):
  for pattern,load,extra in (('steady',75,{}),('steady',125,{}),('pulse',125,dict(base=50,heavy=4,light=4))):
   p=SameBoy(args.core,args.rom,model=model)
   def get(name,size=1):return int.from_bytes(p.read(syms['_'+name],size),'little')
   def put(name,value):
    at=syms['_'+name]
    for start,(pointer,length) in p.maps.items():
     if pointer and start<=at<start+length:ctypes.memmove(pointer+at-start,bytes([value]),1);return
    raise KeyError(hex(at))
   def row(y):v=p.vram();return ''.join(chr(t+32) if t<96 else '#' for t in v[0x1800+y*32:0x1814+y*32])
   try:
    p.tick(600)
    for _ in range(13):
     if get('selected_test')==SLOWDOWN:break
     p.press('right');p.tick(20)
    assert get('selected_test')==SLOWDOWN
    p.press('a');p.tick(40);assert 'Slowdown presets' in row(4),row(4)
    p.press('a');p.tick(40);assert 'Slowdown' in row(4),row(4)
    for name,value in (('slow_pattern',PATTERNS[pattern]),('slow_load',load//5),('slow_base',extra.get('base',50)//5),('slow_heavy',extra.get('heavy',4)),('slow_light',extra.get('light',4))):put(name,value)
    p.press('a');p.tick(600);p.press('b');p.tick(30)
    frames,lag=bcd(p.read(syms['_slow_frames'],3)),bcd(p.read(syms['_slow_lag'],3));tick=get('slow_tick_lag',3)
    # The stop comes at a wake, and the run's first VBlank woke its first update.
    expected=schedule(pattern,load,**extra);updates=frames-lag-1
    want=sum(lag_frames(expected[j%len(expected)]) for j in range(updates))
    assert (lag,tick)==(want,want),(model,pattern,load,'Lag by handler and gaps',lag,tick,'expected',want,'over',updates,'updates')
    assert not get('slow_running') and 'Stopped' in row(15),row(15)
    print(f'SameBoy {model}: {pattern} {load}% {updates} updates, {frames} frames, {lag} lag frames by handler and gaps, as the table says',flush=True)
   finally:p.close()

if args.core:
 sameboy_cases()
else:
 if wanted(['table']):table_cases()
 if wanted(['threshold']):threshold_cases()
 if wanted(['cycles']):cycle_cases()
 if wanted(['controls']):control_cases()
 if wanted(['cleanup']):cleanup_cases()
print('Slowdown matched the cycle arithmetic'+(' in SameBoy' if args.core else ''))
