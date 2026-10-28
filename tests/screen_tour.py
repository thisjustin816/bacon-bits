"""Tour every screen frame by frame in SameBoy and reject corrupt glyphs, blinks
and a header left wrong after a full-screen view.

A blink is a map cell that changes and returns to its old tile within a few
frames while the screen is otherwise the same screen. A corrupt glyph is a
cell showing a font slot whose pattern no longer matches the font.
"""
import argparse,json,re,sys
from pathlib import Path
from PIL import Image
from libretro import SameBoy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
a=argparse.ArgumentParser();a.add_argument('--core',required=True,type=Path);a.add_argument('--rom',type=Path);a.add_argument('--frames',type=Path,help='folder for every recorded frame');a.add_argument('--variant',choices=['mbc5','mbc3'],help='tour one build only, for example with --rom')
args=a.parse_args()
# Odd-length browser labels borrow these punctuation slots for half-cell shifts.
LABEL_SLOTS=set(map(int,re.search(r'label_slots\[\]=\{([^}]+)\}',(ROOT/'src/main.c').read_text())[1].split(',')))
BLINK=4
# Body rows below the header; a screen change may blank them, but only briefly.
MAX_BLANK=18
# A clean change lands within three frames: a focus move clears the old
# border in one VBlank and draws the new one over the next two.
MAX_CHANGE_RUN=3
# Leaving a full-screen view, the header must be back within this many frames
# of the press. The B press is read one or two frames after it starts.
HEADER_GRACE=4
# While a tone plays, the Audio waveform scrolls through these map rows and
# columns; the blink check skips only those cells.
WAVE_ROWS=range(6,12);WAVE_COLUMNS=range(2,18)
WAVE_CELLS={(y-3)*20+x for y in WAVE_ROWS for x in WAVE_COLUMNS}
def body_cells(image):
 data=image.crop((0,24,160,144)).tobytes()
 return [hash(b''.join(data[(y*8+r)*480+x*24:(y*8+r)*480+x*24+24] for r in range(8))) for y in range(15) for x in range(20)]
def borrowed_cell(x,y):
 # On the browser, labels sit on rows 9 and 15; the focus border runs along each card's edge.
 return y in (4,9,10,15,16) or (x in (0,9,10,19) and 4<=y<=16)
# The browser's footer reads "1 of 3" to "3 of 3" from column 7.
BROWSER_FOOTER=bytes(ord(c)-32 for c in 'of 3')

class Tour:
 def __init__(self,variant,model):
  rom=args.rom or ROOT/'build'/variant/'bacon-bits.gbc'
  self.syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',rom.with_suffix('.noi').read_text(),re.M)}
  # Compare VRAM with the font compiled into this ROM.
  at=self.syms['_bb_font'];data=rom.read_bytes();self.font=data[(at>>16)*16384+(at&0xffff)-(16384 if at>>16 else 0):][:1536]
  self.p=SameBoy(args.core,rom,model=model);self.name=f'{variant or "mbc5"}-{"cgb" if "Color" in model else "dmg"}'
  self.history=[];self.step='boot';self.problems=[];self.full_view=False;self.frames=0;self.blank_run=0;self.blank_runs={};self.cells=None;self.change_run=0;self.change_runs={};self.animated=False;self.header=None;self.header_from=None
 def get(self,name):return self.p.read(self.syms['_'+name])[0]
 def text(self,y):
  v=self.p.vram();return ''.join(chr(t+32) if t<96 else '#' for t in v[0x1800+y*32:0x1814+y*32])
 def frame(self):
  self.p.tick();self.frames+=1;v=self.p.vram();cells=v[0x1800:0x1800+32*18]
  visible=[cells[y*32+x] for y in range(18) for x in range(20)]
  # A Color cell whose attribute selects VRAM bank 1 shows a logo tile, not a glyph.
  banked=[bool(v[0x3800+y*32+x]&8) for y in range(18) for x in range(20)] if len(v)>0x2000 else [False]*360
  if args.frames and self.frames%2==0:self.p.image.save(args.frames/f'{self.name}-{self.frames:06d}.png')
  # The boot ROM's logo uses tiles the font takes over; judge the cartridge's own frames.
  # The header is judged on every frame outside a full-screen view, and from
  # HEADER_GRACE frames after the press that leaves one.
  if self.header and (not self.full_view or (self.header_from is not None and self.frames>self.header_from)):
   if self.p.image.crop((0,0,160,24)).tobytes()!=self.header:self.problems.append((self.step,self.frames,'header differs from the browser header'))
  if not self.full_view and self.step!='boot':
   if len(self.p.image.getcolors(65536) or [])<=1:self.problems.append((self.step,self.frames,'blank frame'))
   # Punctuation slots hold browser labels only while the browser is shown.
   browser=bytes(cells[17*32+9:17*32+13])==BROWSER_FOOTER
   # The cover window hides rows 3-17 while a screen is rebuilt; judge only what shows.
   covered=(self.p.read(0xff40)[0]&0x20) and self.p.read(0xff4a)[0]<=24
   for i,t in enumerate(visible):
    if t>=96 or banked[i] or (covered and i>=60):continue
    if browser and (t in LABEL_SLOTS or 61<=t<=64) and borrowed_cell(i%20,i//20):continue
    if t and v[t*16:t*16+16]!=self.font[t*16:t*16+16]:
     self.problems.append((self.step,self.frames,f'corrupt glyph {t} at {i%20},{i//20}'));break
   cells=body_cells(self.p.image)
   changed=sum(a!=b for a,b in zip(cells,self.cells)) if self.cells else 0
   self.cells=cells
   if changed>8:self.change_run+=1
   else:
    if self.change_run:self.change_runs[self.step]=max(self.change_runs.get(self.step,0),self.change_run)
    if self.change_run>MAX_CHANGE_RUN:self.problems.append((self.step,self.frames,f'screen built over {self.change_run} frames'))
    self.change_run=0
   if len(set(cells))==1:self.blank_run+=1
   else:
    if self.blank_run:self.blank_runs[self.step]=max(self.blank_runs.get(self.step,0),self.blank_run)
    if self.blank_run>MAX_BLANK:self.problems.append((self.step,self.frames,f'body blank for {self.blank_run} frames'))
    self.blank_run=0
   # A scrolling waveform repeats, so two different steps can look identical.
   self.history.append([0 if self.animated and i in WAVE_CELLS else c for i,c in enumerate(cells)])
   if len(self.history)>BLINK+1:self.history.pop(0)
   if len(self.history)>=3:
    now=self.history[-1]
    for old in self.history[:-2]:
     # Same screen before and after, but a cell differed in between.
     changed=sum(x!=y for x,y in zip(old,now))
     if changed>12:continue
     for mid in self.history[self.history.index(old)+1:-1]:
      flips=[i for i,(x,y,z) in enumerate(zip(old,mid,now)) if x==z and y!=x]
      if flips:
       self.problems.append((self.step,self.frames,f'{len(flips)} cells blinked, first at {flips[0]%20},{flips[0]//20}'));break
     else:continue
     break
  else:self.history=[];self.cells=None
 def tick(self,n):
  for _ in range(n):self.frame()
 def press(self,key,after=40):
  self.p.held={self.p.BUTTONS[key]};self.tick(8);self.p.held=set();self.tick(after)
 def chord(self):self.p.held={0,2,3,8};self.tick(80);self.p.held=set();self.tick(40)
 def go(self,test):
  for _ in range(12):
   if self.get('selected_test')==test:return
   step=self.step;self.step=f'browse to {test}';self.press('right');self.step=step
  raise AssertionError((self.name,self.step,'Browser never reached test',test))
 def preset(self,choice):
  self.press('a')
  first=1 if 'Manual' in ''.join(self.text(y) for y in range(6,16)) else 0
  for _ in range(choice-first if choice>=first else 4):self.press('down')
  self.press('a')
 def expect(self,title):
  assert title in self.text(4),(self.name,self.step,'Tour lost its place',self.text(4))
 def until(self,title,limit):
  for _ in range(limit):
   if title in self.text(4):return
   self.frame()
  raise AssertionError((self.name,self.step,'Never reached',title))
 def leave(self):self.step+=' / return chord';self.chord();self.press('down');self.press('a',60)
 def close(self):self.p.close()

results={}
for variant in ['', 'mbc3']:
 if args.variant and args.variant!=(variant or 'mbc5'):continue
 for model in ['Game Boy Color','Game Boy']:
  t=Tour(variant,model);cgb='Color' in model
  try:
   t.tick(600);t.header=t.p.image.crop((0,0,160,24)).tobytes()
   t.step='browser animation';t.tick(120)
   for test in range(11):t.step=f'browse {test}';t.go(test);t.tick(30)
   t.step='browser up/down'
   for key in ['down','down','up','up']:t.press(key)
   t.step='platform';t.go(0);t.press('a',120);t.expect('Platform');t.press('select');t.press('right');t.press('a');t.press('select');t.press('b',60);t.leave()
   t.step='link';t.go(1);t.press('a',60);t.expect('Link presets');t.press('a',60);t.expect('Link setup');t.press('down');t.press('right');t.press('start',90)
   for _ in range(4):t.press('right',30)
   t.press('a');t.press('a');t.press('select');t.press('select');t.press('b');t.press('start',40);t.leave()
   if variant:
    t.step='clock';t.go(2);t.preset(1);t.expect('Clock');t.press('a',200)
    for _ in range(4):t.press('select')
    t.press('a',40);t.press('b',40)
   else:
    t.step='rumble';t.go(2);t.press('a',90);t.expect('Rumble')
    for _ in range(4):t.press('b',30)
    t.p.held={t.p.BUTTONS['select']};t.tick(40);t.p.held=set();t.tick(30)
    t.press('start',90);t.press('start',40);t.leave()
   t.step='audio';t.go(3);t.preset(2);t.expect('Audio');t.animated=True;t.history=[];t.press('a',90);t.press('right');t.press('select');t.press('down');t.press('right');t.press('select');t.press('a');t.press('b',40);t.animated=False;t.history=[]
   t.step='buttons';t.go(4);t.preset(1);t.expect('Buttons')
   for _ in range(4):t.press('select')
   t.p.held={t.p.BUTTONS['up'],t.p.BUTTONS['right']};t.tick(30);t.p.held=set();t.tick(20);t.leave()
   t.step='display settings';t.go(5);t.preset(1);t.expect('Display');t.press('select');t.press('select')
   t.step='display full view';t.full_view=True;t.press('a',90);t.press('right',90);t.header_from=t.frames+HEADER_GRACE;t.press('b',10);t.full_view=False;t.header_from=None;t.step='display return';t.tick(60);t.press('b',40)
   t.step='sram';t.go(6);t.preset(2);t.expect('SRAM');t.press('a');t.press('down');t.press('a',10);t.until('SRAM result',4000);t.tick(40);t.press('select');t.press('select');t.press('b');t.press('b',40)
   t.step='burn in';t.go(7);t.preset(1);t.expect('Burn in');t.press('select');t.press('select');t.press('a',300);t.press('select');t.press('select');t.press('b',40);t.press('select');t.press('b',40)
   t.step='cart led';t.go(8);t.press('a',30);t.expect('Cart LED')
   if not variant:t.press('a',30);t.press('a',150);t.press('select');t.press('select')
   t.press('b',40)
   t.step='infrared';t.go(9);t.press('a',30);t.expect('Infrared')
   if cgb:t.press('down');t.press('a',30);t.press('a',150);t.press('left');t.press('select');t.press('select')
   t.press('b',40)
   t.step='flicker settings';t.go(10);t.preset(1);t.expect('Flicker')
   for _ in range(4):t.press('select')
   t.step='flicker full view';t.full_view=True;t.press('a',120);t.header_from=t.frames+HEADER_GRACE;t.press('b',10);t.full_view=False;t.header_from=None;t.step='flicker return';t.tick(60);t.press('b',60)
   t.step='browser after tour';t.tick(120)
   grouped={}
   for step,frame,kind in t.problems:
    key=step+': '+re.sub(r'(\d+ cells blinked|corrupt glyph \d+).*',r'\1',kind);grouped.setdefault(key,[]).append(frame)
   results[t.name]={'longest_change':t.change_runs,'longest_blank':t.blank_runs,'frames':t.frames,'problem_count':len(t.problems),'problems':{k:{'count':len(v),'frames':v[:6]} for k,v in grouped.items()},'examples':t.problems[:12]}
   print(t.name,t.frames,'frames,',len(t.problems),'problems',flush=True)
  finally:t.close()
(ROOT/'build/screen-tour.json').write_text(json.dumps(results,indent=1)+'\n')
bad={k:v['problems'] for k,v in results.items() if v['problem_count']}
assert not bad,json.dumps(bad,indent=1)
print('Every screen, transition and live redraw held its glyphs and header without blinks or blank frames')
