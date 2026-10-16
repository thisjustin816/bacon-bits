"""Original cartridge LED, infrared port, clock and memory instruments."""
from pathlib import Path
from generated import write_generated
from PIL import Image,ImageDraw
from scenes import encode_tile,array,chip
ROOT=Path(__file__).resolve().parents[1]
def picture(scene,phase):
 im=Image.new('P',(160,144),0);d=ImageDraw.Draw(im)
 if scene==0:
  d.rectangle((27,94,62,101),fill=3);d.rectangle((31,64,58,94),fill=3);d.ellipse((31,55,58,82),fill=3)
  d.rectangle((34,67,55,91),fill=1);d.ellipse((34,59,55,82),fill=1)
  d.line((38,100,38,113),fill=3,width=2);d.line((52,100,52,110),fill=3,width=2)
  d.line((38,75,45,68,49,77),fill=0,width=2)
 elif scene==1:
  for x in [20,60]:
   d.rectangle((x,75,x+10,96),fill=3);d.ellipse((x,69,x+10,79),fill=3);d.rectangle((x+3,75,x+7,90),fill=1)
   d.line((x+3,97,x+3,108),fill=3);d.line((x+8,97,x+8,104),fill=3)
  for x in range(34,58,6):
   d.line((x,79,x+3,76),fill=2 if phase&1 else 1);d.line((x,86,x+3,89),fill=2 if phase&1 else 1)
 elif scene==2:
  d.ellipse((18,60,69,111),fill=3);d.ellipse((21,63,66,108),fill=1);d.ellipse((24,66,63,105),fill=0)
  for x,y in [(43,67),(43,101),(25,84),(59,84)]:d.rectangle((x,y,x+2,y+2),fill=3)
  d.line((44,85,44,71),fill=3,width=2);end=[(57,85),(44,98),(31,85),(44,72)][phase&3];d.line((44,85,*end),fill=2,width=2)
 else:chip(d,32,75)
 return im
out='/* Generated original component drawings; tools/hardware_art.py. */\n';sizes=[]
for scene in range(4):
 union=[bytes(16)];maps=[]
 for phase in range(4):
  im=picture(scene,phase);m=[]
  for y in range(6,14):
   for x in range(1,19):
    tile=encode_tile(im,x,y)
    if tile not in union:union.append(tile)
    m.append(0 if tile==bytes(16) else 112+union.index(tile)-1)
  maps.append(m)
 assert len(union)<129
 assert max(sum(a!=b for a,b in zip(old,new)) for old in maps for new in maps)<=32, "Animation update queue too small"
 out+=array('hardware_tiles_'+str(scene),b''.join(union[1:]));sizes.append(len(union)-1)
 for phase,m in enumerate(maps):out+=array('hardware_map_'+str(scene)+'_'+str(phase),m)
 print('hardware',scene,'tiles',len(union)-1)
out+='static const uint8_t *const hardware_tiles[]={'+','.join('hardware_tiles_'+str(i) for i in range(4))+'};\n'
out+='static const uint8_t *const hardware_maps[4][4]={'+','.join('{'+','.join('hardware_map_'+str(i)+'_'+str(f) for f in range(4))+'}' for i in range(4))+'};\n'
out+=array('hardware_sizes',sizes)
write_generated(ROOT/'src/hardware_data.h',out)
