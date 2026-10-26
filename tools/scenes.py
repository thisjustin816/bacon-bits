"""Draw original native-size instruments and menu cards."""
from pathlib import Path
from generated import write_generated
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
def canvas():
 im=Image.new('P',(160,144),0);return im,ImageDraw.Draw(im)
def chip(d,x,y):
 for i in range(4):
  d.rectangle((x-4,y+3+i*5,x+27,y+5+i*5),fill=3);d.rectangle((x+3+i*5,y-4,x+5+i*5,y+27),fill=3)
 d.rectangle((x,y,x+23,y+23),fill=3);d.rectangle((x+2,y+2,x+21,y+21),fill=1)
 d.rectangle((x+6,y+6,x+17,y+17),fill=3);d.rectangle((x+9,y+9,x+14,y+14),fill=0)
def handheld(d,x,y):
 d.rectangle((x+2,y,x+24,y+37),fill=3);d.rectangle((x,y+2,x+26,y+34),fill=3)
 d.rectangle((x+2,y+2,x+24,y+33),fill=1);d.rectangle((x+4,y+4,x+22,y+17),fill=3)
 d.rectangle((x+6,y+6,x+20,y+15),fill=0)
 d.rectangle((x+5,y+25,x+13,y+27),fill=3);d.rectangle((x+8,y+22,x+10,y+30),fill=3)
 d.rectangle((x+18,y+25,x+20,y+27),fill=2);d.rectangle((x+22,y+22,x+24,y+24),fill=2)
def motor(d,x,y,phase):
 d.rectangle((x,y+6,x+26,y+23),fill=3);d.rectangle((x+2,y+8,x+24,y+21),fill=1)
 for j in range(3):d.line((x+7+j*6,y+9,x+7+j*6,y+20),fill=3)
 d.rectangle((x+27,y+12,x+35,y+15),fill=3);d.rectangle((x+32,y+(3 if phase%2 else 12),x+38,y+(13 if phase%2 else 22)),fill=2)
def panel(d,x,y):
 d.rectangle((x+2,y+2,x+74,y+44),fill=3);d.rectangle((x,y,x+73,y+43),fill=3);d.rectangle((x+1,y+1,x+72,y+42),fill=0)
 for p in [(x,y),(x+73,y),(x,y+43),(x+73,y+43)]:d.point(p,fill=0)
def clock(d,x,y,phase):
 d.ellipse((x,y,x+25,y+25),fill=3);d.ellipse((x+2,y+2,x+23,y+23),fill=1)
 d.line((x+12,y+5,x+12,y+13),fill=3,width=2)
 end=[(x+19,y+13),(x+12,y+20),(x+5,y+13),(x+12,y+5)][phase&3]
 d.line((x+12,y+13,*end),fill=2,width=2)
def picture(scene,phase):
 im,d=canvas()
 if scene in [0,5,6,7]:
  for i,(x,y) in enumerate([(4,37),(82,37),(4,85),(82,85)]):
   if scene==6 and i>=3:continue
   panel(d,x,y)
   if scene==5:
    if i==0:
     d.rectangle((x+33,y+5,x+40,y+26),fill=3);d.rectangle((x+26,y+12,x+47,y+19),fill=3);d.rectangle((x+55,y+13,x+59,y+17),fill=2)
    elif i==1:
     d.rectangle((x+17,y+5,x+56,y+27),fill=3);d.rectangle((x+20,y+8,x+53,y+24),fill=1)
     for yy in range(y+8,y+24,4):
      for xx in range(x+20,x+53,4):
       if ((xx-x)//4+(yy-y)//4)&1:d.rectangle((xx,yy,min(xx+2,x+53),yy+2),fill=0)
    elif i==2:chip(d,x+24,y+6)
    else:clock(d,x+25,y+3,phase)
   elif scene==6:
    if i==0:
     d.ellipse((x+26,y+4,x+45,y+23),fill=3);d.ellipse((x+29,y+7,x+42,y+20),fill=2 if phase&1 else 1);d.line((x+31,y+23,x+31,y+29),fill=3);d.line((x+40,y+23,x+40,y+29),fill=3)
    elif i==1:
     d.rectangle((x+18,y+9,x+28,y+22),fill=3);d.rectangle((x+48,y+9,x+58,y+22),fill=3)
     for xx in range(x+31,x+45,5):d.line((xx,y+13,xx+2,y+16),fill=2)
    else:
     d.rectangle((x+22,y+6,x+49,y+25),fill=3);d.rectangle((x+24,y+8,x+47,y+23),fill=0)
     for yy in range(y+9,y+23,2):
      for xx in range(x+25,x+47,2):
       if ((xx-x)//2+(yy-y)//2+(phase&1))&1:d.rectangle((xx,yy,xx+1,yy+1),fill=1)
     d.rectangle((x+32,y+12,x+39,y+19),fill=2)
   elif i==0:chip(d,x+24 if i==0 else x+26,y+6)
   elif i==1:
    d.rectangle((x+13,y+9,x+24,y+26),fill=3);d.rectangle((x+47,y+9,x+58,y+26),fill=3);d.line((x+24,y+17,x+47,y+17),fill=2,width=2)
    d.rectangle((x+29+phase*3,y+15,x+32+phase*3,y+19),fill=1)
   elif i==2:
    if scene==7:clock(d,x+25,y+3,phase)
    else:motor(d,x+18,y+2,phase)
   else:
    for j,h in enumerate([7,15,23,13,9]):d.rectangle((x+23+j*6,y+28-h,x+26+j*6,y+27),fill=2 if (j+phase)%3 else 3)
 elif scene==1:
  for i in range(12):
   x=16+i%6*24;y=56 if i<6 else 104;d.line((x+4,y+8 if i<6 else y-1,79,76 if i<6 else 101),fill=1)
  # The 13th port, a sprite over the chip's top edge.
  d.line((79,62,79,76),fill=1)
  chip(d,68,73)
 elif scene==2:
  handheld(d,15,62);handheld(d,117,62);d.line([(28,62),(28,56),(130,56),(130,62)],fill=3,width=2)
  for j in range(3):
   x=45+(phase*6+j*24)%65;d.rectangle((x,55,x+4,58),fill=2)
 elif scene==3:motor(d,24+phase%2,61,phase)
 elif scene==4:
  d.rectangle((39,62,56,112),fill=3);d.rectangle((23,78,72,95),fill=3)
  d.rectangle((42,65,53,109),fill=1);d.rectangle((26,81,69,92),fill=1)
  for x,y in [(16,56),(64,56),(16,104),(64,104)]:d.rectangle((x,y,x+7,y+7),fill=1)
 return im

def encode_tile(im,tx,ty):
 data=[]
 for y in range(8):
  lo=hi=0
  for x in range(8):
   c=im.getpixel((tx*8+x,ty*8+y));lo=(lo<<1)|(c&1);hi=(hi<<1)|(c>>1)
  data.extend([lo,hi])
 return bytes(data)
def array(name,data):return 'static const uint8_t '+name+'[]={'+','.join(map(str,data))+'};\n'
def main():
 output='/* Generated original instrument drawings; tools/scenes.py. */\n'
 sizes=[]
 for scene in range(8):
  union=[bytes(16)];maps=[];rect=(0,4,20,13) if scene in [0,5,6,7] else (1,6,18,8)
  for phase in range(4):
   im=picture(scene,phase);m=[]
   for y in range(rect[1],rect[1]+rect[3]):
    for x in range(rect[0],rect[0]+rect[2]):
     tile=encode_tile(im,x,y)
     if tile not in union:union.append(tile)
     m.append(0 if tile==bytes(16) else 112+union.index(tile)-1)
   maps.append(m)
  assert len(union)-1<=120,(scene,len(union))
  assert max(sum(a!=b for a,b in zip(old,new)) for old in maps for new in maps)<=32, "Animation update queue too small"
  output+=array('scene_tiles_'+str(scene),b''.join(union[1:]))
  for phase,m in enumerate(maps):output+=array('scene_map_'+str(scene)+'_'+str(phase),m)
  sizes.append((len(union)-1,rect));print('scene',scene,'tiles',len(union)-1)
 output+='static const uint8_t *const scene_tiles[]={'+','.join('scene_tiles_'+str(i) for i in range(8))+'};\n'
 output+='static const uint8_t *const scene_maps[8][4]={'+','.join('{'+','.join('scene_map_'+str(i)+'_'+str(f) for f in range(4))+'}' for i in range(8))+'};\n'
 output+='static const uint8_t scene_sizes[8][5]={'+','.join('{'+','.join(map(str,(n,*r)))+'}' for n,r in sizes)+'};\n'
 write_generated(ROOT/'src/scene_data.h',output)

if __name__=='__main__':main()
