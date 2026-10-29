"""Prints with every Printer preset on PyBoy's Game Boy Printer and checks the paper, the
readings and the byte timing the instrument sets. PyBoy's printer accepts any timing and never
resets, so these runs check what the cartridge sends, not how a printer answers it."""
from pathlib import Path
import itertools,re,shutil,tempfile
from pyboy import PyBoy
from cart import Cart,ROMS,ROOT,symbols

LINE=0.10899;FRAME=154*LINE # Milliseconds at normal speed, which the instrument runs at.

def local_symbols(rom):
 """Static functions in printer.c, placed from the module listing and printer_run."""
 listing=(ROOT/'build/objects/src_printer.c.lst').read_text()
 labels={m.group(2):int(m.group(1),16) for m in re.finditer(r'^\s*([0-9A-F]{8})\s+\d+\s+(_\w+)::?$',listing,re.M)}
 run=symbols(rom)['_printer_run'];base=(run&0xFFFF)-labels['_printer_run']
 return run>>16,{name:base+at for name,at in labels.items()}

class PrinterCart(Cart):
 def __init__(self,rom,cgb,printer=True):
  self.rom=Path(rom);self.syms=symbols(rom);self.folder=tempfile.TemporaryDirectory()
  self.paper=Path(self.folder.name)/'paper';self.paper.mkdir()
  path=Path(self.folder.name)/'cart.gbc';shutil.copy(self.rom,path)
  extra=dict(printer=True,printer_output=str(self.paper)) if printer else {}
  self.p=PyBoy(str(path),window='null',sound_emulated=False,cgb=cgb,**extra);self.p.set_emulation_speed(0)
  self.bytes=[];self.faults={};self.calls=0;self.gap_fault=None
  bank,local=local_symbols(rom)
  self.p.hook_register(bank,local['_xfer'],self.sent,None)
  self.p.hook_register(bank,local['_failed'],self.inject,None)
  self.p.hook_register(bank,local['_gap'],self.inject_gap,None)
  self.p.tick(240,True)
 def sent(self,_):
  self.bytes.append((self.p.frame_count*FRAME+self.p.memory[0xFF44]*LINE,self.p.register_file.A))
 def inject(self,_):
  '''Replaces the reply that the n-th failed() call of the job reads: {n: (alive, status)}.
  A key of None applies to every call.'''
  self.calls+=1;fault=self.faults.get(self.calls,self.faults.get(None))
  if fault:self.p.memory[self.syms['_prn_alive']],self.p.memory[self.syms['_prn_status']]=fault
 def inject_gap(self,_):
  '''Replaces the reply to the data packet the Init check sends with no Init: (alive, status).'''
  if self.gap_fault:self.p.memory[self.syms['_prn_alive']],self.p.memory[self.syms['_prn_status']]=self.gap_fault
 def kept(self):return self.row(12).strip('#').split('Kept')[1].strip()
 def status(self):
  '''The bottom border's reading, without the reply in its corner.'''
  return re.sub(r'[ #]*([0-9A-F]{2} [0-9A-F]{2})? #$','',self.row(15)).strip('# ')
 def reply(self):
  '''The alive and status bytes in the bottom border's corner, or None.'''
  m=re.search(r'([0-9A-F]{2} [0-9A-F]{2}) #$',self.row(15));return m and m.group(1)
 def print_job(self,faults={}):
  self.bytes=[];self.faults=faults;self.calls=0;self.press('a')
  for _ in range(2400):
   if self.status() not in ('Sending','Printing','Part 1','No Init','Part 2'):break
   self.tick()
  self.tick(10)
 def check_job(self,faults={},gap=None):
  '''Runs the Init check on page 2; faults and gap replace replies as in print_job.'''
  self.gap_fault=gap;self.print_job(faults)
 def fields(self):
  '''The four readings on page 2 and the detail line below the box.'''
  return [self.row(y)[2:18].strip('# ') for y in (6,8,10,12)]+[self.row(17).strip()]
 def papers(self):
  '''The last check's two sheets: part 1 was saved when part 2 started, part 2 is still held.'''
  from PIL import Image
  return Image.open(sorted(self.paper.glob('*.png'))[-1]),self.sheet()
 def sheet(self):
  '''The last print. PyBoy holds it until the next print's top margin ends it.'''
  return self.p.printer_image()
 def packets(self):
  """Each packet as (command, times of its payload bytes, start, end), from its 0x88 0x33."""
  out=[];b=self.bytes;i=0
  while i+5<len(b):
   assert b[i][1]==0x88 and b[i+1][1]==0x33,('Packet does not start with its magic bytes',i,b[i:i+2])
   length=b[i+4][1]|b[i+5][1]<<8;end=i+6+length+4
   if end>len(b):break
   out.append((b[i+2][1],[t for t,_ in b[i+6:i+6+length]],b[i][0],b[end-1][0]));i=end
  return out

def check_band(px,top,k,black):
 """Strip k is k tiles of black from the left; the rest is white below a light grey top row."""
 for y in range(top,top+16):
  assert all(px[x,y]==black for x in range(8*k)),('Strip ink is not k tiles wide',k,y)
 grey=px[8*k,top];white=px[8*k,top+1]
 assert grey!=white and grey!=black,('Strip top row is not light grey',k)
 assert all(px[x,top]==grey for x in range(8*k,160)),('Strip top row broken',k)
 assert all(px[x,y]==white for y in range(top+1,top+16) for x in range(8*k,160)),('Ink past the strip',k)

def check_sheet(image,strips):
 image=image.convert('L');assert image.size==(160,16*strips),('Paper is not one band per strip',image.size,strips)
 px=image.load()
 for k in range(1,strips+1):check_band(px,16*(k-1),k,px[0,0])

def check_strip(image,k):
 """A sheet that is the one strip k."""
 image=image.convert('L');assert image.size==(160,16),('Paper is not one band',image.size,k)
 px=image.load();check_band(px,0,k,px[0,0])

def max_gap(times):return max((b-a for a,b in zip(times,times[1:])),default=0)

for variant in ['mbc5','mbc3']:
 for cgb in (True,False):
  where=(variant,'CGB' if cgb else 'DMG')
  c=PrinterCart(ROMS[variant],cgb)
  try:
   key1=c.p.memory[0xFF4D]>>7
   c.go(11);c.preset(1);assert 'Printer' in c.text() and c.status()=='Ready',(where,c.text())
   # Steady: four strips back to back, each byte about one byte period after the last.
   c.print_job();assert c.status()=='Printed',(where,c.text())
   assert '4 of 4' in c.row(12),(where,'Kept',c.row(12))
   assert c.reply() and c.reply().startswith('81 0'),(where,'Reply corner',c.row(15))
   packets=c.packets();assert [p[0] for p in packets][:7]==[1,4,4,4,4,4,2],(where,[p[0] for p in packets])
   steady=max(max_gap(p[1]) for p in packets)
   # PyBoy shifts a byte in about half the 0.98 ms a Game Boy takes, so gaps are compared
   # with the steady ones rather than with hardware byte times.
   assert steady<1.6,(where,'Steady payload bytes are not back to back',steady)
   check_sheet(c.sheet(),4)
   # Nine strips fill the printer's memory.
   c.press('right');c.press('right');c.press('right');c.press('right');c.press('right');c.press('right')
   assert c.get('prn_strips')==9,(where,c.get('prn_strips'))
   c.print_job();assert c.status()=='Printed' and '9 of 9' in c.row(12),(where,c.text())
   check_sheet(c.sheet(),9)
   c.press('b');c.tick(30)
   # Paused 200 ms: the wait sits between data packets, and only there.
   c.preset(3);c.print_job();assert c.status()=='Printed',(where,c.text())
   data=[p for p in c.packets() if p[0]==4 and p[1]]
   pauses=[b[2]-a[3] for a,b in zip(data,data[1:])]
   assert len(pauses)==3 and all(199<x<203 for x in pauses),(where,'Strip pauses',pauses)
   # Slow bytes stay inside the data packets, out of the pause.
   c.press('up');c.press('right',after=4);[c.press('right',after=4) for _ in range(6)]
   assert c.get('prn_byte')==8,(where,c.get('prn_byte'))
   c.print_job();data=[p for p in c.packets() if p[0]==4 and p[1]]
   pauses=[b[2]-a[3] for a,b in zip(data,data[1:])]
   assert len(pauses)==3 and all(199<x<203 for x in pauses),(where,'Strip pauses with slow bytes',pauses)
   c.press('b');c.tick(30)
   # Slow bytes: about 5 ms more from byte to byte in data packets, 6 ms in all on hardware; the
   # other packets stay at full rate.
   c.preset(4);c.print_job();assert c.status()=='Printed',(where,c.text())
   for command,times,_,_ in c.packets():
    gaps=[b-a for a,b in zip(times,times[1:])]
    if command==4 and times:assert all(4.5<g-steady<5.3 for g in gaps),(where,'Slow byte gaps',min(gaps),max(gaps),steady)
    else:assert max_gap(times)<1.6,(where,'Slow pacing reached a packet other than data',command)
   c.press('b');c.tick(30)
   # Replies PyBoy's printer never gives. Calls: 1 Init, 2-5 the strips, 6 the empty packet.
   c.preset(1)
   # Strip 3 answered without 08: the printer reset and dropped strips 1 and 2.
   c.print_job({4:(0x81,0x00)});assert c.status()=='Printed' and c.kept()=='2 of 4',(where,c.text())
   # One idle reply inside a busy stretch does not end the wait; two in a row do.
   # Calls: 1 Init, 2-5 the strips, 6 the empty packet, 7 Print, 8 on the polls.
   busy=(0x81,0x02);idle=(0x81,0x00)
   c.print_job({8:busy,9:busy,10:idle,11:busy,12:idle,13:idle});assert c.status()=='Printed',(where,c.text())
   polls=[p[0] for p in c.packets()][7:]
   assert polls==[15]*6,(where,'Polls after one idle reply in a busy stretch',polls)
   # A missing printer clears the last job's reply from the corner.
   c.print_job({1:(0xFF,0xFF)});assert c.status()=='No printer' and c.reply() is None,(where,c.text())
   # An error bit stops the job and names the byte; nothing was counted.
   c.print_job({1:(0x81,0x10)})
   assert c.status()=='Error 10' and c.reply()=='81 10' and c.kept()=='',(where,c.text())
   # A strip answered with FF, as after a dropped packet.
   c.print_job({3:(0xFF,0xFF)});assert c.status()=='No reply' and c.reply()=='FF FF',(where,c.text())
   # Busy for 20 seconds of polls.
   c.print_job({None:(0x81,0x0A)});assert c.status()=='Still busy',(where,c.text())
   # The kept count is the job's: changing Strips afterwards leaves it.
   c.print_job();c.press('left');assert c.kept()=='4 of 4' and c.get('prn_strips')==3,(where,c.text())
   c.press('right')
   # B held while a strip goes out stops the job at the next strip with Break.
   c.press('up');c.press('right');c.press('right');assert c.get('prn_byte')==3,(where,c.get('prn_byte'))
   c.bytes=[];c.press('a',after=0);c.p.button_press('b')
   for _ in range(600):
    c.tick()
    if c.status()=='Stopped':break
   c.p.button_release('b');c.tick(10)
   commands=[p[0] for p in c.packets()]
   assert c.status()=='Stopped' and commands==[1,4,8],(where,commands,c.text())
   c.press('left');c.press('left');c.press('down')
   # B while the printer runs sends Break and stops.
   c.bytes=[];c.press('a')
   for _ in range(2400):
    c.tick()
    if 'Printing' in c.row(15):break
   c.press('b');c.tick(10)
   assert c.status()=='Stopped' and 8 in [p[0] for p in c.packets()],(where,c.text())
   c.press('b');c.tick(60)
   assert c.p.memory[0xFF4D]>>7==key1,(where,'CPU speed not restored')
   assert c.get('selected_test')==11 and 'of 3' in c.row(17),(where,'Did not return to the browser')
  finally:c.close()
  # Page 2, the Init check. PyBoy's printer takes data after a print, so the refusal is a reply
  # put in at gap(); only a physical printer shows it.
  c=PrinterCart(ROMS[variant],cgb)
  try:
   key1=c.p.memory[0xFF4D]>>7;busy=(0x81,0x02);idle=(0x81,0x00)
   c.go(11);c.preset(1);assert '1/2' in c.row(4),(where,c.row(4))
   c.press('select');assert '2/2' in c.row(4) and c.status()=='Ready',(where,c.text())
   assert c.fields()==['Part 1   -','No Init  -','Refused  -','Init     -','A: run the check'],(where,c.fields())
   # A clean run: Part 1, then one data packet with no Init, then Init and part 2.
   c.check_job();assert c.status()=='Printed',(where,c.text())
   packets=c.packets();commands=[p[0] for p in packets]
   groups=[(k,len(list(g))) for k,g in itertools.groupby(commands)]
   assert [g[0] for g in groups]==[1,4,2,15,4,1,4,2,15] and [g[1] for g in groups[:3]]==[1,2,1],(where,'Packet order',groups)
   assert groups[3][1]>=32 and groups[4][1]==1 and groups[6][1]==2 and groups[8][1]>=32,(where,'Packet order',groups)
   assert [len(p[1]) for p in packets if p[0]==4]==[640,0,640,640,0],(where,'Data lengths')
   shown=c.fields();status=c.get('prn_gap')
   assert shown==['Part 1   Printed','No Init  %02X'%status,'Refused  No','Init     Printed','Init not needed'] and not status&0x10,(where,shown)
   assert c.get('prn_gapped')==1 and c.get('prn_stage')==4 and c.reply().startswith('81 '),(where,c.text())
   first,second=c.papers();check_strip(first,1);check_strip(second,2)
   assert max(max_gap(p[1]) for p in packets)<1.6,(where,'Check data bytes are not at the steady rate')
   # Byte ms on page 1 does not slow the check.
   c.press('select');c.press('down');c.press('down');[c.press('right',after=4) for _ in range(7)]
   assert c.get('prn_byte')==8,(where,c.get('prn_byte'))
   c.press('select');c.check_job();assert c.status()=='Printed',(where,c.text())
   assert max(max_gap(p[1]) for p in c.packets())<1.6,(where,'Byte ms reached the check')
   # One idle reply in a busy stretch does not send the gap packet; the second in a row does.
   # Calls: 1 Init, 2 strip, 3 empty packet, 4 Print, 5 on the polls.
   c.check_job({5:busy,6:busy,7:idle,8:busy,9:idle,10:idle});assert c.status()=='Printed',(where,c.text())
   commands=[p[0] for p in c.packets()]
   assert commands[4:11]==[15]*6+[4],(where,'Polls before the gap packet',commands[:12])
   # A printer that refuses data after a print, as a physical one did: 81 14, then Init.
   c.check_job(gap=(0x81,0x14));assert c.status()=='Printed',(where,c.text())
   assert c.fields()==['Part 1   Printed','No Init  14','Refused  Yes','Init     Printed','Init needed'],(where,c.fields())
   check_strip(c.papers()[0],1);check_strip(c.papers()[1],2)
   # Refused is the packet-error bit, whatever else the reply holds.
   c.check_job(gap=(0x81,0x08));assert c.fields()[1:3]==['No Init  08','Refused  No'],(where,c.fields())
   c.check_job(gap=(0x81,0x10));assert c.fields()[1:3]==['No Init  10','Refused  Yes'],(where,c.fields())
   # No reply to the gap packet: the check ends there, with no Init after it.
   c.check_job(gap=(0xFF,0xFF));commands=[p[0] for p in c.packets()]
   assert c.status()=='No reply' and c.fields()==['Part 1   Printed','No Init  -','Refused  -','Init     -','Did not finish'],(where,c.text())
   assert commands[-1]==4 and commands.count(1)==1,(where,'Packets after no reply',commands)
   # Part 2 refused after its Init: n polls in part 1, so Part 2's Init is call n + 5.
   c.check_job();n1=next(len(list(g)) for k,g in itertools.groupby([p[0] for p in c.packets()]) if k==15)
   c.check_job({4+n1+1:(0x81,0x10)})
   assert c.status()=='Error 10' and c.fields()[0]=='Part 1   Printed' and c.fields()[3]=='Init     Failed' and c.fields()[4]=='Did not finish',(where,c.text())
   # Part 1 with no printer answering the Init.
   c.check_job({1:(0xFF,0xFF)});assert c.status()=='No printer',(where,c.text())
   assert c.fields()==['Part 1   Failed','No Init  -','Refused  -','Init     -','Did not finish'] and [p[0] for p in c.packets()]==[1],(where,c.fields())
   # B between packets sends Break; part 1 stays unfinished.
   c.bytes=[];c.press('a',after=0);c.tick(20);c.p.button_press('b')
   for _ in range(600):
    c.tick()
    if c.status()=='Stopped':break
   c.p.button_release('b');c.tick(10)
   commands=[p[0] for p in c.packets()]
   assert c.status()=='Stopped' and commands[-1]==8 and 4 not in commands[commands.index(15):],(where,commands,c.text())
   assert c.fields()[0]=='Part 1   Stopped',(where,c.fields())
   # Select back shows page 1 with a clean state; B leaves from either page.
   c.press('select');assert '1/2' in c.row(4) and c.status()=='Ready',(where,c.text())
   c.press('select');c.press('b');c.tick(60)
   assert c.p.memory[0xFF4D]>>7==key1,(where,'CPU speed not restored after page 2')
   assert c.get('selected_test')==11 and 'of 3' in c.row(17),(where,'Did not return to the browser from page 2')
  finally:c.close()
  # No printer: the first reply is not 81, and nothing else is shown.
  c=PrinterCart(ROMS[variant],cgb,printer=False)
  try:
   c.go(11);c.preset(1);c.print_job()
   assert c.status()=='No printer' and 'of' not in c.row(12) and c.reply() is None,(where,c.text())
   c.press('select');c.check_job()
   assert c.status()=='No printer' and c.fields()[0]=='Part 1   Failed' and c.reply() is None,(where,c.text())
  finally:c.close()
print('Printer: steady, nine-strip, paused and slow-byte prints on PyBoy\'s printer with the sheet checked strip by strip, 200 ms strip pauses, 6 ms data bytes with other packets at full rate, kept counts, error, no-reply, busy, stop and no-printer readings, and CPU speed restored, and the Init check page: packet order with no Init before the gap packet, the wait for two idle replies, the refusal and other replies shown as the status byte and Refused, failures and stop, and steady data bytes whatever Byte ms says, on CGB and DMG with both mappers')
