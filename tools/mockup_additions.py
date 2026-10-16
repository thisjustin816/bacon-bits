"""Screen proposals cut from Bacon Bits' own emulator-rendered tiles."""
from pathlib import Path
import tempfile,shutil
from PIL import Image,ImageDraw
from pyboy import PyBoy
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td:
 f=Path(td)/'test.gbc';shutil.copy(ROOT/'build/bacon-bits.gbc',f)
 p=PyBoy(str(f),window='null',sound_emulated=False);p.set_emulation_speed(0);p.tick(240,True);base=p.screen.image.convert("RGB")
 p.memory[0xffff]=0;p.memory[0xd800:0xd802]=[0x18,0xfe];p.register_file.PC=0xd800
 # Render a tile atlas through the emulator, preserving the original UI palette.
 for t in range(64+10):p.memory[0,0x9800+t//16*32+t%16]=t;p.memory[1,0x9800+t//16*32+t%16]=0
 p.tick(2,True);atlas=p.screen.image.convert('RGB')
 tiles=[atlas.crop((t%16*8,t//16*8,t%16*8+8,t//16*8+8)) for t in range(74)]
 p.stop(save=False)
 def cell(im,x,y,t):im.paste(tiles[t],(x*8,y*8))
 def text(im,x,y,s):
  assert x>=0 and x+len(s)<=20,(x,s)
  for i,c in enumerate(s):cell(im,x+i,y,ord(c)-32)
 def frame(im,top=5,bottom=14):
  for x in range(20):cell(im,x,top,66 if x==0 else 67 if x==19 else 64);cell(im,x,bottom,68 if x==0 else 69 if x==19 else 64)
  for y in range(top+1,bottom):cell(im,0,y,65);cell(im,19,y,65)

 def screen(title,page=''):
  im=base.copy()
  for y in range(3,18):
   for x in range(20):cell(im,x,y,0)
  text(im,1,4,title)
  if page:text(im,16,4,page)
  frame(im);return im
 shots=[]
 def fields(title,values,page='',status=''):
  im=screen(title,page)
  for i,(k,v) in enumerate(values):text(im,2,6+i*2,k);text(im,10,6+i*2,v)
  cell(im,1,6,71)
  if status:text(im,(20-len(status))//2,16,status)
  shots.append(im)
 fields('AUDIO RANGE',[('SHAPE','TRIANGLE'),('STEPS','FINE'),('ON FR','HOLD'),('GAP FR','0')],'2/2','SILENT')
 im=screen('BUTTONS','1/3')
 for x,y,s in [(4,7,'UP'),(2,9,'LT'),(6,9,'RT'),(4,11,'DN'),(14,8,'A'),(12,10,'B'),(8,12,'SE'),(11,12,'ST')]:text(im,x,y,s)
 text(im,3,16,'HELD 2  PEAK 3');shots.append(im)
 fields('BUTTON TIMING',[('BUTTON','A'),('PRESSES','23'),('HELD FR','14'),('SHORT','2')],'3/3')
 fields('DISPLAY',[('PATTERN','CHECKER'),('COLOR','GRAY'),('WIDTH','1 PX'),('AXIS','HORIZ')],'1/2')
 fields('SRAM TEST',[('MODE','VERIFY'),('BANKS','4'),('PATTERN','RANDOM'),('PASSES','1')],'1/2','NO RECORD')
 fields('SRAM RESULTS',[('PASS','1'),('CHECKS','32736'),('ERRORS','0'),('FIRST','NONE')],'1/2','RECORD SAVED')
 fields('BURN IN',[('MINUTES','10'),('LOAD','MEDIUM'),('CPU','NORMAL'),('ON FAIL','STOP')],'1/2')
 fields('BURN RESULTS',[('CYCLES','12'),('SECONDS','600'),('ERRORS','0'),('FIRST','NONE')],'1/2','COMPLETE')
 fields('PROBE FF72',[('EXPECT','5A A5'),('READ','00 00'),('RESULT','FAIL'),('CAUSE','IGNORED')],'2/3')
 fields('SIGNATURE',[('NAME','MGBA'),('FF72','UNCHANGED'),('FF75','8F'),('MATCH','YES')],'3/3')
 board=Image.new('RGB',(656,600),(255,255,255))
 for i,im in enumerate(shots):board.paste(im,(i%4*164,i//4*150));im.save(ROOT/'build'/f'addition-mockup-{i}.png')
 board=board.crop((0,0,656,450)).resize((984,675),Image.Resampling.NEAREST);board.save(ROOT/'build/addition-mockups.png')
