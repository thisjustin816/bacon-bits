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
  seen=set()
  for _ in range(8):
   p.tick();phase=p.read(syms['_flicker_phase'])[0]
   if phase not in seen:shots.append((model,'Raw phase '+('B' if phase else 'A'),p.image.copy()));seen.add(phase)
  assert seen=={0,1}
 finally:p.close()
board=Image.new('RGB',(672,328),(227,219,200));d=ImageDraw.Draw(board)
for i,(model,label,im) in enumerate(shots):
 x=4+i%4*168;y=4+i//4*164;board.paste(im,(x,y));d.text((x,y+146),('GBC ' if model.endswith('Color') else 'GB ')+label,fill=(64,40,32))
board.resize((1344,656),Image.Resampling.NEAREST).save(ROOT/'assets/flicker.png')
record(['flicker.png'],{'mbc5':'build/bacon-bits.gbc'},'SameBoy')
print('Captured separate raw frames in SameBoy; no frame averaging or simulated persistence')
