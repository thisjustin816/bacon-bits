"""Render the original assets through an existing diagnostic's emulator frame."""
from pathlib import Path
import sys,tempfile,shutil
from PIL import Image
from pyboy import PyBoy
from art import icons,encode,PALETTES,ROOT
sys.path.insert(0,str(ROOT/'vendor/rumble-pulse'))
import font
source=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'build/upstream/link-sustain/link-sustain.gbc'
with tempfile.TemporaryDirectory() as td:
 rom=Path(td)/'source.gbc';shutil.copy(source,rom)
 p=PyBoy(str(rom),window='null',sound_emulated=False);p.set_emulation_speed(0);p.tick(150,True)
 p.memory[0xffff]=0;p.memory[0xd800]=0x18;p.memory[0xd801]=0xfe;p.register_file.PC=0xd800
 p.memory[0xff40]=0x91
 header=(ROOT/'src/art.h').read_text()
 import re
 arrays={n:bytes(int(x,16) for x in re.findall(r'0x([0-9a-f]{2})',v)) for n,v in re.findall(r'char (\w+)\[\] = \{(.*?)\};',header,re.S)}
 for i,pal in enumerate(PALETTES):
  for j,(r,g,b) in enumerate(pal):
   val=(r>>3)|((g>>3)<<5)|((b>>3)<<10)
   for k,byte in enumerate([val&255,val>>8]):p.memory[0xff68]=i*8+j*2+k;p.memory[0xff69]=byte
 def upload(base,data):p.memory[0xff4f]=0; p.memory[0x8000+base*16:0x8000+base*16+len(data)]=data
 upload(0,arrays['bb_font']);upload(64,arrays['bb_chrome']);upload(128,arrays['bb_sunrise'])
 # LCDC selects signed BG tile addresses; switch to unsigned for these tiles.
 p.memory[0xff40]=0x91
 shots=[]
 for n,(label,desc) in enumerate(zip(['PLATFORM','LINK SUSTAIN','RUMBLE','AUDIO RANGE'],['IDENTIFY HARDWARE','CHECK BOTH SIDES','COMPARE PULSES','CHECK TONE RANGE'])):
  upload(80,arrays[f'bb_icon_{n}'])
  tiles=[0]*360;attrs=[0]*360
  def cell(x,y,t):tiles[y*20+x]=t
  def text(x,y,s):
   for i,c in enumerate(s):cell(x+i,y,ord(c)-32)
  for y in range(4):
   for x in range(20):attrs[y*20+x]=1
  for y in range(3):
   for x in range(8):cell(12+x,y,128+y*8+x)
  text(1,1,'BACON BITS')
  for x in range(20):cell(x,4,66 if x==0 else 67 if x==19 else 64);cell(x,14,68 if x==0 else 69 if x==19 else 64)
  for y in range(5,14):cell(0,y,65);cell(19,y,65)
  text((20-len(label))//2,5,label)
  cell(1,9,70);cell(18,9,71)
  for y in range(6):
   for x in range(8):cell(6+x,7+y,80+y*8+x)
  for i in range(4):cell(6+i*2,13,72 if n==i else 73)
  text((20-len(desc))//2,16,desc)
  for y in range(18):
   p.memory[0,0x9800+y*32:0x9800+y*32+20]=tiles[y*20:y*20+20]
   p.memory[1,0x9800+y*32:0x9800+y*32+20]=attrs[y*20:y*20+20]
  p.tick(2,True);im=p.screen.image.convert('RGB');shots.append(im);im.save(ROOT/'build'/f'original-mockup-{n}.png')
 # Audio-screen proposal, rendered from the same original tiles.
 tiles=[0]*360;attrs=[0]*360
 for y in range(4):
  for x in range(20):attrs[y*20+x]=1
 for y in range(3):
  for x in range(8):cell(12+x,y,128+y*8+x)
 text(1,1,'BACON BITS');text(4,4,'AUDIO RANGE')
 for x in range(20):cell(x,5,66 if x==0 else 67 if x==19 else 64);cell(x,14,68 if x==0 else 69 if x==19 else 64)
 for y in range(6,14):cell(0,y,65);cell(19,y,65)
 for y,k,v in [(6,'VOICE','PULSE 1'),(8,'HZ','64'),(10,'LEVEL','15/15'),(12,'OUTPUT','BOTH')]:
  text(3,y,k);text(10,y,v)
 cell(1,8,71);text(7,16,'SILENT')
 for y in range(18):
  p.memory[0,0x9800+y*32:0x9800+y*32+20]=tiles[y*20:y*20+20]
  p.memory[1,0x9800+y*32:0x9800+y*32+20]=attrs[y*20:y*20+20]
 p.tick(2,True)
 p.screen.image.convert('RGB').resize((640,576),Image.Resampling.NEAREST).save(ROOT/'build/audio-proposal.png')
 p.stop(save=False)
 board=Image.new('RGB',(328,296),(255,255,255))
 for i,im in enumerate(shots):board.paste(im,(i%2*168,i//2*152))
 board.resize((656,592),Image.Resampling.NEAREST).save(ROOT/'build/original-mockup.png')
