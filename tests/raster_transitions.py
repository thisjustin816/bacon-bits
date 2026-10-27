"""The persistent header must survive navigation and diagnostic returns on the LCD."""
from pathlib import Path
import argparse,json,hashlib,re
from PIL import Image
from libretro import SameBoy
ROOT=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--core',type=Path,required=True);a.add_argument('--rom',type=Path);args=a.parse_args()
out=ROOT/'build/raster-transitions';out.mkdir(exist_ok=True)
for variant in ['', 'mbc3']:
 for model in ['Game Boy Color','Game Boy']:
  rom=args.rom or ROOT/'build'/variant/'bacon-bits.gbc'
  syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',rom.with_suffix('.noi').read_text(),re.M)}
  p=SameBoy(args.core,rom,model=model)
  def get(name,size=1):return int.from_bytes(p.read(syms['_'+name],size),'little')
  events=[];shots=[]
  try:
   p.tick(600);header=p.image.crop((0,0,160,24)).tobytes()
   def tick(n):
    for _ in range(n):
     p.tick()
     assert p.image.crop((0,0,160,24)).tobytes()==header,(variant,model,p.frame,'Persistent header corrupted')
   def press(k):
    events.append({'frame':p.frame,'key':k});p.held={p.BUTTONS[k]};tick(8);p.held=set();tick(40)
   # All page changes, including wraparound, and all diagnostic entrances.
   for selected in range(11):
    if selected:press('right')
    assert get('selected_test')==selected,('Navigation missed a route',selected)
    revision=get('ui_revision',2);press('a')
    assert get('ui_revision',2)!=revision,('Diagnostic did not open',selected)
    if selected>=3 or selected==1 or (variant and selected==2):
     press('up');press('a') # Manual settings, with outputs stopped.
     press('select');press('select')
    shots.append(p.image.copy())
    if selected in [0,1,2,4] and not (variant and selected==2):
     p.held={0,2,3,8};tick(100);p.held=set();tick(30);press('down');press('a')
    else:press('b')
    v=p.vram();footer=''.join(chr(t+32) if t<96 else '#' for t in v[0x1800+17*32:0x1800+17*32+20])
    assert f'{selected//4+1} of 3' in footer,('Did not return to the browser',selected,footer)
   press('right')
   name=f'{variant or "mbc5"}-{model.replace(" ","-")}'
   board=Image.new('RGB',(4*160,3*144))
   for i,shot in enumerate(shots):board.paste(shot,(i%4*160,i//4*144))
   board.save(out/(name+'-passed.png'))
   (out/(name+'-passed.json')).write_text(json.dumps({'rom_sha256':hashlib.sha256((args.rom or ROOT/'build'/variant/'bacon-bits.gbc').read_bytes()).hexdigest(),'frames':p.frame,'inputs':events},indent=2)+'\n')
  except Exception as error:
   name=f'{variant or "mbc5"}-{model.replace(" ","-")}'
   p.image.save(out/(name+'.png'))
   (out/(name+'.json')).write_text(json.dumps({'inputs':events,'frame':p.frame,'error':str(error)},indent=2)+'\n')
   raise
  finally:p.close()
 if args.rom:break
print('Persistent header stayed intact in every sampled navigation and diagnostic transition')
