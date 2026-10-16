"""Replay launcher redraws frame by frame and check every live D-pad state."""
from pathlib import Path
import argparse,json,shutil,sys,tempfile
from PIL import ImageDraw
from pyboy import PyBoy
from libretro import SameBoy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from scenes import picture
args=argparse.ArgumentParser();args.add_argument('--core',type=Path,required=True);args.add_argument('--rom',type=Path);a=args.parse_args()
OUT=ROOT/'build/ui-transitions';OUT.mkdir(exist_ok=True)

def label_signature(v):
 # Half-cell label tiles borrow font slots; check both references and patterns.
 return tuple((v[0x1800+y*32+x],v[v[0x1800+y*32+x]*16:v[0x1800+y*32+x]*16+16]) for y in [9,15] for x in list(range(1,9))+list(range(11,19)))
def pixel(v,x,y):
 t=v[0x1800+y//8*32+x//8];at=t*16+(y&7)*2;b=7-(x&7)
 return ((v[at]>>b)&1)|(((v[at+1]>>b)&1)<<1)
class Player:
 def __init__(self,backend,rom,cgb):
  self.backend=backend;self.held=[];self.cgb=cgb;self.check_visible=False;self.frame_count=0;self.events=[]
  if backend=='sameboy':self.p=SameBoy(a.core,rom,model='Game Boy Color' if cgb else 'Game Boy')
  else:self.p=PyBoy(str(rom),window='null',sound_emulated=False,cgb=cgb);self.p.set_emulation_speed(0)
 def hold(self,keys):
  self.events.append({"frame":self.frame_count,"held":list(keys)})
  if self.backend=='sameboy':self.p.held={self.p.BUTTONS[k] for k in keys}
  else:
   for k in self.held:self.p.button_release(k)
   for k in keys:self.p.button_press(k)
  self.held=keys
 def frame(self):
  if self.backend=='sameboy':self.p.tick();v=self.p.vram()
  else:
   self.p.tick(1,True)
   v=bytes(self.p.memory[0,0x8000:0x9fff])+bytes([self.p.memory[0,0x9fff]])+(bytes(self.p.memory[1,0x8000:0x9fff])+bytes([self.p.memory[1,0x9fff]]) if self.cgb else bytes(8192))
  self.frame_count+=1
  if self.check_visible:assert len(self.image().getcolors(65536))>1,'Blank navigation frame'
  return v
 def image(self):return self.p.image if self.backend=='sameboy' else self.p.screen.image
 def tick(self,n):
  for _ in range(n):self.frame()
 def press(self,k):self.hold([k]);self.tick(8);self.hold([]);self.tick(32)
 def close(self):
  if self.backend=='sameboy':self.p.close()
  else:self.p.stop(save=False)
results=[]
for variant in ['', 'mbc3']:
 for backend in ['pyboy','sameboy']:
  for cgb in [True,False]:
   with tempfile.TemporaryDirectory() as td:
    rom=Path(td)/'test.gbc';shutil.copy(a.rom or ROOT/'build'/variant/'bacon-bits.gbc',rom)
    p=Player(backend,rom,cgb);name=f'{variant or "mbc5"}-{backend}-{"cgb" if cgb else "dmg"}';events=[];frames=[]
    try:
     p.tick(600);p.check_visible=True;v=p.frame();font=v[:61*16]+v[65*16:1536];labels=label_signature(v)
     # Slots 61-64 hold focus art; the remaining font and label patterns stay.
     # Check all four same-page directions, including the first Right after boot.
     for key in ['down','up','right','left']:
      p.hold([key])
      for frame in range(48):
       if frame==8:p.hold([])
       v=p.frame();events.append({'input':key,'frame':frame+1})
       frames.append(p.image().copy())
       assert v[:61*16]+v[65*16:1536]==font,(name,key,frame,'Visible font reloaded')
       assert label_signature(v)==labels,(name,key,frame,'Label changed during focus move')
     # Page changes may clear/reveal labels, but must never show other glyphs.
     for _ in range(3):p.press('right')
     for target in [4,8,0]:
      old=label_signature(p.frame());samples=[];p.hold(['right'])
      for frame in range(80):
       if frame==8:p.hold([])
       samples.append(label_signature(p.frame()))
      new=samples[-1];blank=bytes(16)
      for frame,sample in enumerate(samples):
       for index,(tile,glyph) in enumerate(sample):
        assert tile>=96 or glyph in [blank,old[index][1],new[index][1]],(name,target,frame,index,'Transient label garbage')
      if target!=0:
       for _ in range(2 if target==8 else 3):p.press('right')
     # Back on Platform, advance to Buttons and choose the live preset.
     for _ in range(4):p.press('right')
     labels_on_buttons_page=label_signature(p.frame())
     p.press('a');p.press('a');p.tick(60)
     for held in range(16):
      # SameBoy filters impossible opposing inputs before JOYP reaches the ROM.
      if backend=="sameboy" and ((held&3)==3 or (held&12)==12):continue
      keys=[key for bit,key in [(1,'right'),(2,'left'),(4,'up'),(8,'down')] if held&bit]
      p.hold(keys);p.tick(16);v=p.frame();im=picture(4,0);d=ImageDraw.Draw(im)
      for bit,rect,dot in [(4,(42,65,53,77),(47,69,49,71)),(8,(42,96,53,109),(47,101,49,103)),(2,(26,81,38,92),(31,85,33,87)),(1,(57,81,69,92),(62,85,64,87))]:
       if held&bit:d.rectangle(rect,fill=2);d.rectangle(dot,fill=0)
      for y in range(62,112):
       for x in range(23,73):
        if 39<=x<=56 or 78<=y<=95:
         assert pixel(v,x,y)==im.getpixel((x,y)),(name,held,x,y,'D-pad art or outline overwritten')
      if held==5:p.image().save(OUT/(name+'-dpad.png'))
     # Return through the default-Continue dialog, then select Test menu.
     p.hold(['a','b','select','start']);p.tick(90);p.hold([]);p.tick(40)
     p.press('down');p.press('a');p.tick(80)
     p.image().save(OUT/(name+'-returned.png'))
     assert label_signature(p.frame())==labels_on_buttons_page,(name,'Menu did not return to Buttons')
     results.append(name)
    except Exception:
     p.image().save(OUT/(name+'-first-failure.png'))
     (OUT/(name+'-input.json')).write_text(json.dumps({"inputs":p.events,"focus_samples":events},indent=2)+'\n')
     if frames:frames[0].save(OUT/(name+'-replay.gif'),save_all=True,append_images=frames[1:],duration=17,loop=0)
     raise
    finally:p.close()
 if a.rom:break
(OUT/'results.json').write_text(json.dumps(results,indent=2)+'\n')
print('Focus and page transitions passed frame by frame; PyBoy checked 16 D-pad states, SameBoy checked 9 legal states; menu return passed:',', '.join(results))
