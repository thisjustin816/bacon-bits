"""Check compiled menu icon outlines and complete animation poses in SameBoy."""
from pathlib import Path
import argparse,collections,json,sys
from PIL import Image
from libretro import SameBoy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from scenes import picture
args=argparse.ArgumentParser();args.add_argument('--core',type=Path,required=True);args.add_argument('--rom',type=Path);a=args.parse_args()
OUT=ROOT/'build/menu-art';OUT.mkdir(exist_ok=True)
def pixel(v,x,y):
 t=v[0x1800+y//8*32+x//8];at=t*16+(y&7)*2;b=7-(x&7)
 return ((v[at]>>b)&1)|(((v[at+1]>>b)&1)<<1)
def check_edges(v,page,context):
 assert 103 not in [v[0x1800+y*32+x] for y in range(4,17) for x in range(20)],(context,"Extra menu cursor")
 for card,(left,top) in enumerate([(4,37),(82,37),(4,85),(82,85)]):
  if page==2 and card>1:continue
  assert all(pixel(v,x,top)==3 and pixel(v,x,top+43)==3 for x in range(left+2,left+72)),(context,card,"Card top or bottom erased")
  assert all(pixel(v,left,y)==3 and pixel(v,left+73,y)==3 for y in range(top+2,top+42)),(context,card,"Card side erased")
 if page==2:assert all(pixel(v,x,85)==0 for x in range(160)),(context,"Focus drew an absent lower card")
shots=[]
for variant in ['', 'mbc3']:
 for model in ['Game Boy Color','Game Boy']:
  p=SameBoy(a.core,a.rom or ROOT/'build'/variant/'bacon-bits.gbc',model=model);events=[]
  def press(key):
   events.append({'frame':p.frame,'key':key,'held_frames':8,'released_frames':12});p.press(key)
  try:
   p.tick(600);palette={}
   for page,scene in enumerate([7 if variant else 0,5,6]):
    if page:
     for _ in range(4):press('right')
     p.tick(60)
    # Learn the emulator's displayed palette from a settled frame. The modal
    # color for each (attribute, pixel) pair excludes moving-edge samples.
    v=p.vram();colours=collections.defaultdict(collections.Counter)
    for y in range(144):
     for x in range(160):
      attr=(v[0x3800+y//8*32+x//8]&7) if model=='Game Boy Color' else 0
      colours[attr,pixel(v,x,y)][p.image.getpixel((x,y))]+=1
    palette.update({key:values.most_common(1)[0][0] for key,values in colours.items()})
    if model=="Game Boy Color":
     for index in range(4):palette.setdefault((3,index),palette[0,(1-index) if index<2 else index])
    templates=[picture(scene,f) for f in range(4)]
    for frame in range(64):
     p.tick();v=p.vram()
     for card,(left,top) in enumerate([(4,37),(82,37),(4,85),(82,85)]):
      if page==2 and card>1:continue
      points=[(x,y) for y in range(top+3,top+31) for x in range(left+12,left+63)]
      points+=[(x,top+2) for x in range(left+12,left+63) if any(template.getpixel((x,top+2)) for template in templates)]
      raw=bytes(pixel(v,x,y) for x,y in points)
      valid=[f for f,template in enumerate(templates) if raw==bytes(template.getpixel((x,y)) for x,y in points)]
      assert valid,(variant,model,page,card,frame,'Mixed animation tile map')
      # Compare the rasterized frame as well as the map at frame end.
      displayed=[p.image.getpixel((x,y)) for x,y in points]
      expected=[]
      for template in templates:
       expected.append([palette[((v[0x3800+y//8*32+x//8]&7) if model=='Game Boy Color' else 0),template.getpixel((x,y))] for x,y in points])
      if displayed not in expected:
       p.image.save(OUT/'first-failing-frame.png')
       (OUT/'first-failing-input.json').write_text(json.dumps({'variant':variant,'model':model,'page':page,'card':card,'frame':frame})+'\n')
       raise AssertionError((variant,model,page,card,frame,'Mixed rasterized animation pose'))
     check_edges(v,page,(variant,model,page,frame))
     if page==1:
      assert all(pixel(v,136,y)==3 for y in range(42,65)),'Checker crossed the display frame'
     if page==2:
      assert all(pixel(v,130,y)==3 for y in range(46,60)),'IR rays crossed the receiver outline'
     if frame%16==0:shots.append(p.image.copy())
    # Focus each other card, then restore the first before changing pages.
    for selected in range(1,2 if page==2 else 4):
     press('right');check_edges(p.vram(),page,(variant,model,page,selected))
    for _ in range(1 if page==2 else 3):press('left')
  except Exception as error:
   p.image.save(OUT/'first-failing-frame.png')
   (OUT/'first-failing-input.json').write_text(json.dumps({'variant':variant,'model':model,'frame':p.frame,'inputs':events,'failure':str(error)},indent=2)+'\n')
   raise
  finally:p.close()
 if a.rom:break
board=Image.new('RGB',(4*164,((len(shots)+3)//4)*148),(227,219,200))
for i,im in enumerate(shots):board.paste(im,(i%4*164,i//4*148))
board.save(OUT/'all-cards-and-phases.png')
print('All card icons passed complete map and raster poses, display containment and IR receiver outlines in CGB/DMG and both releases')
