"""Prints with every Printer preset on PyBoy's Game Boy Printer and checks the paper, the
readings and the byte timing the instrument sets. PyBoy's printer accepts any timing and never
resets, so these runs check what the cartridge sends, not how a printer answers it."""
from pathlib import Path
import re,shutil,tempfile
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
  self.bytes=[];self.faults={};self.calls=0
  bank,local=local_symbols(rom)
  self.p.hook_register(bank,local['_xfer'],self.sent,None)
  self.p.hook_register(bank,local['_failed'],self.inject,None)
  self.p.tick(240,True)
 def sent(self,_):
  self.bytes.append((self.p.frame_count*FRAME+self.p.memory[0xFF44]*LINE,self.p.register_file.A))
 def inject(self,_):
  '''Replaces the reply that the n-th failed() call of the job reads: {n: (alive, status)}.
  A key of None applies to every call.'''
  self.calls+=1;fault=self.faults.get(self.calls,self.faults.get(None))
  if fault:self.p.memory[self.syms['_prn_alive']],self.p.memory[self.syms['_prn_status']]=fault
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
   if self.status() not in ('Sending','Printing'):break
   self.tick()
  self.tick(10)
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

def check_sheet(image,strips):
 """Strip k is k tiles of black from the left; the rest is white below a light grey top row."""
 image=image.convert('L');assert image.size==(160,16*strips),('Paper is not one band per strip',image.size,strips)
 px=image.load();black=px[0,0]
 for k in range(1,strips+1):
  top=16*(k-1)
  for y in range(top,top+16):
   assert all(px[x,y]==black for x in range(8*k)),('Strip ink is not k tiles wide',k,y)
  grey=px[8*k,top];white=px[8*k,top+1]
  assert grey!=white and grey!=black,('Strip top row is not light grey',k)
  assert all(px[x,top]==grey for x in range(8*k,160)),('Strip top row broken',k)
  assert all(px[x,y]==white for y in range(top+1,top+16) for x in range(8*k,160)),('Ink past the strip',k)

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
  # No printer: the first reply is not 81, and nothing else is shown.
  c=PrinterCart(ROMS[variant],cgb,printer=False)
  try:
   c.go(11);c.preset(1);c.print_job()
   assert c.status()=='No printer' and 'of' not in c.row(12) and c.reply() is None,(where,c.text())
  finally:c.close()
print('Printer: steady, nine-strip, paused and slow-byte prints on PyBoy\'s printer with the sheet checked strip by strip, 200 ms strip pauses, 6 ms data bytes with other packets at full rate, kept counts, error, no-reply, busy, stop and no-printer readings, and CPU speed restored, on CGB and DMG with both mappers')
