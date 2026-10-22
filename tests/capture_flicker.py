"""Capture the live cartridge's preview, cadence and separate raw LCD phases."""
from pathlib import Path
import argparse,re
from PIL import Image,ImageDraw
from libretro import SameBoy
from media import record
ROOT=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--core',required=True,type=Path);args=a.parse_args()
syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',(ROOT/'build/bacon-bits.noi').read_text(),re.M)}
shots=[]
for model in ['Game Boy Color','Game Boy']:
 p=SameBoy(args.core,ROOT/'build/bacon-bits.gbc',model=model)
 def press(key):p.press(key);p.tick(50)
 try:
  p.tick(600)
  for _ in range(10):press('right')
  press('a');press('a');shots.append((model,'Layer comparison',p.image.copy()))
  press('select');shots.append((model,'Cadence settings',p.image.copy()));press('a')
  for _ in range(600):
   p.tick()
   if p.read(syms['_flicker_ready'])==b'\1':break
  # The phase variable can change before a frame's image is returned, so each
  # raw frame is labelled from its pixels: phase A draws seven-pixel horizontal
  # dashes, and phase B's diagonal strokes never run five pixels across.
  raw={}
  for _ in range(8):
   p.tick();phase=p.read(syms['_flicker_phase'])[0]
   if phase not in raw:raw[phase]=p.image.copy()
  assert set(raw)=={0,1}
  def runs(im):
   gray=im.convert('L');px=gray.load();bg=max(gray.getcolors(),key=lambda c:c[0])[1];count=0
   for y in range(112):
    length=0
    for x in range(160):
     length=length+1 if px[x,y]!=bg and x and px[x,y]==px[x-1,y] else 1 if px[x,y]!=bg else 0
     count+=length==5
   return count
  first,second=sorted(raw.values(),key=runs,reverse=True)
  assert runs(first)>=2*max(runs(second),1),('Raw phases look alike',runs(first),runs(second))
  shots.append((model,'Raw phase A',first));shots.append((model,'Raw phase B',second))
 finally:p.close()
board=Image.new('RGB',(672,328),(227,219,200));d=ImageDraw.Draw(board)
for i,(model,label,im) in enumerate(shots):
 x=4+i%4*168;y=4+i//4*164;board.paste(im,(x,y));d.text((x,y+146),('GBC ' if model.endswith('Color') else 'GB ')+label,fill=(64,40,32))
board.resize((1344,656),Image.Resampling.NEAREST).save(ROOT/'assets/flicker.png')
record(['flicker.png'],{'mbc5':'build/bacon-bits.gbc'},'SameBoy')
print('Captured separate raw frames in SameBoy; no frame averaging or simulated persistence')
