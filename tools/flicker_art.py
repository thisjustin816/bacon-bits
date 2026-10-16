"""Original probe, shadow, reference patches and the compact comparison preview."""
from pathlib import Path
from PIL import Image,ImageDraw
from scenes import encode_tile,array
from generated import write_generated
ACTOR=['......3333......','....33311333....','...3311111133...','..331111111133..',
 '.33111111111133.','3311111221111133','3111111221111113','3111111111111113',
 '3311111111111133','.33311111111333.','...3311111133...','....33311333....',
 '.....333333.....','......3223......','......3223......','.......33.......']
def plane(x,y,phase):
 if not phase:
  return 1 if y%8==4 and x%16<7 else 2 if y%8==7 and x%16==2 else 0
 return 2 if x%16<9 and (x-y)%16 in (0,1) else 0

def main():
 actor=Image.new('P',(16,24));d=ImageDraw.Draw(actor)
 for y,row in enumerate(ACTOR):
  for x,c in enumerate(row):
   if c!='.':actor.putpixel((x,y),int(c))
 d.ellipse((0,20,15,23),fill=3)
 # Store the four body tiles first, followed by the two shadow tiles.
 out='/* Original native artwork; tools/flicker_art.py. */\n'+array('flicker_actor',b''.join(encode_tile(actor,x,y) for y in range(3) for x in range(2)))
 preview=Image.new('P',(128,48))
 for y in range(48):
  for x in range(128):preview.putpixel((x,y),3 if x==63 else plane(x if x<64 else x-64,y,0 if x<64 else (x^y)&1))
 for at in [20,83]:
  for y,row in enumerate(ACTOR):
   for x,c in enumerate(row):
    if c!='.':preview.putpixel((at+x,10+y),int(c))
 ref=Image.new('P',(160,24));d=ImageDraw.Draw(ref);d.line((0,0,159,0),fill=3)
 for y in range(5,21):
  for x in range(16,48):ref.putpixel((x,y),3 if (x^y)&1 else 0)
 d.rectangle((64,5,95,20),fill=3);d.rectangle((112,5,143,20),outline=3)
 for name,im,start in [('preview',preview,112),('reference',ref,210)]:
  atlas=[bytes(16)];mapping=[]
  for y in range(im.height//8):
   for x in range(im.width//8):
    tile=encode_tile(im,x,y)
    if tile not in atlas:atlas.append(tile)
    mapping.append(0 if tile==bytes(16) else start+atlas.index(tile)-1)
  assert len(atlas)-1<=(98 if name=='preview' else 15)
  out+=array('flicker_'+name+'_tiles',b''.join(atlas[1:]))+array('flicker_'+name+'_map',mapping)
 write_generated(Path(__file__).resolve().parents[1]/'src/flicker_data.h',out)
if __name__=='__main__':main()
