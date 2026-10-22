"""Measure raw LCD phases, motion, pause/step and cleanup on both releases."""
from pathlib import Path
import argparse,ctypes,re,shutil,tempfile,json,hashlib,collections,itertools
from pyboy import PyBoy
from PIL import Image,ImageDraw
from libretro import SameBoy
ROOT=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--core',type=Path);a.add_argument('--rom',type=Path);args=a.parse_args()
OUT=ROOT/'build'/('flicker-sameboy' if args.core else 'flicker-pyboy');OUT.mkdir(exist_ok=True)
shots=[];results=[]
for variant in ['', 'mbc3']:
 rom=args.rom or ROOT/'build'/variant/'bacon-bits.gbc'
 syms={n:int(v,16) for n,v in re.findall(r'^DEF (\S+) (0x[\da-fA-F]+)$',rom.with_suffix('.noi').read_text(),re.M)}
 assert '_flicker_run' in syms,'Flicker route absent from this ROM'
 for cgb in [True,False]:
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/'test.gbc';shutil.copy(rom,f)
   if args.core:p=SameBoy(args.core,f,model='Game Boy Color' if cgb else 'Game Boy')
   else:p=PyBoy(str(f),window='null',sound_emulated=False,cgb=cgb);p.set_emulation_speed(0)
   def tick(n=1):
    if args.core:p.tick(n)
    else:p.tick(n,True)
   def hold(keys):
    if args.core:p.held={p.BUTTONS[k] for k in keys}
    else:
     for k in ['a','b','start','select','up','down','left','right']:
      (p.button_press if k in keys else p.button_release)(k)
   def press(key):hold([key]);tick(8);hold([]);tick(45)
   def read(addr,size=1):return p.read(addr,size) if args.core else bytes(p.memory[addr:addr+size])
   def get(name,size=1):return int.from_bytes(read(syms['_'+name],size),'little')
   def put(name,value):
    addr=syms['_'+name]
    if args.core:
     for start,(pointer,length) in p.maps.items():
      if pointer and start<=addr<start+length:ctypes.memmove(pointer+addr-start,bytes([value]),1);break
     else:raise KeyError(hex(addr))
    else:p.memory[addr]=value
   def image():return p.image.copy() if args.core else p.screen.image.convert('RGB')
   def vram():return p.vram() if args.core else bytes(p.memory[0,0x8000:0x9fff])+bytes([p.memory[0,0x9fff]])
   def text():
    v=vram();return '\n'.join(''.join(chr(t+32) if t<96 else '#' for t in v[0x1800+y*32:0x1814+y*32]) for y in range(18))
   def start():
    press('a')
    for _ in range(600):
     if get('flicker_ready'):break
     tick()
    assert get('flicker_ready'),('Full view did not finish preparing',get('flicker_cell'),get('flicker_running'))
    tick(5)
   def stop():press('b');assert not get('flicker_ready') and not get('flicker_running');assert 'Bacon Bit Bench' in text()
   dma=[]
   if not args.core:
    def dma_hook(_):dma.append((p.memory[0xff44],p.memory[0xff41]&3))
    p.hook_register(0,syms['_refresh_OAM'],dma_hook,None)
   try:
    tick(600)
    for _ in range(10):press('right')
    assert get('selected_test')==10;shots.append((cgb,'Menu',image()))
    press('a');assert 'Flicker presets' in text();press('a');assert 'Flicker' in text() and not get('flicker_running')
    shots.append((cgb,'Preview',image()))
    # Public controls change all three configuration pages, then Continue keeps them.
    press('select');press('right');assert get('flicker_a')==2
    press('down');press('right');assert get('flicker_b')==2
    press('down');press('right');assert get('flicker_lead')==1
    press('down');press('right');assert get('flicker_cycle')==1
    shots.append((cgb,'Cadence',image()))
    press('select');press('down');press('right');assert get('flicker_speed')==2
    press('down');press('right');assert get('flicker_axis')==1
    press('down');press('right');assert get('flicker_cell')==2
    shots.append((cgb,'Motion',image()))
    press('select');shots.append((cgb,'Colors',image()))
    press('right');assert get('flicker_pair')==(1 if cgb else 0)
    press('down');press('right');assert get('flicker_level_a')==(31 if cgb else 3)
    press('left');assert get('flicker_level_a')==(30 if cgb else 2)
    press('down');press('left');assert get('flicker_level_b')==0
    press('right');assert get('flicker_level_b')==1
    press('down');press('left');assert not get('flicker_compare')
    press('right');assert get('flicker_compare')
    press('b');press('a');assert 'Continue' in text();press('a');assert get('flicker_a')==2 and get('flicker_cell')==2
    # Each preset selects its pattern and leaves output stopped.
    for preset in range(1,5):
     press('b');press('a')
     for _ in range(preset):press('down')
     press('a');assert get('flicker_pattern')==preset-1 and not get('flicker_running')
    put('flicker_pair',0);put('flicker_level_a',31 if cgb else 3);put('flicker_level_b',0)
    # Motion is disabled for phase measurements; the bottom reference must be static.
    for pattern in range(4):
     put('flicker_pattern',pattern);put('flicker_speed',0);put('flicker_cycle',0)
     for a_frames,b_frames in [(1,1),(2,1),(1,3),(7,9),(60,60)]:
      put('flicker_a',a_frames);put('flicker_b',b_frames);put('flicker_lead',1);start()
      if (a_frames,b_frames)==(60,60):assert get('flicker_phase')==1,'Lead B was not first'
      oam=read(0xfe00,160);active=[(oam[i],oam[i+1]) for i in range(0,160,4) if 0<oam[i]<160 and 0<oam[i+1]<168]
      assert len(active)<=6 and max(sum(y<=line+16<y+8 for y,x in active) for line in range(144))<=4,'Sprite budget exceeded'
      records=[];references=[];states=[]
      for _ in range((a_frames+b_frames)*3+12):
       tick();im=image();records.append(hashlib.sha256(im.crop((64,72,80,76) if pattern==1 else (0,0,48,40)).tobytes()).hexdigest());references.append(im.crop((0,120,160,144)).tobytes());states.append((get('flicker_phase'),get('flicker_elapsed'),get('flicker_ticks',2)))
      assert len(set(references))==1,(variant,cgb,pattern,'Reference moved')
      assert len(set(records))==2,(variant,cgb,pattern,a_frames,b_frames,'Missing raw phase')
      assert any(all(len({records[i] for i in range(offset,len(records)) if states[i-offset][0]==phase})==1 for phase in [0,1]) for offset in [0,1]),(variant,cgb,pattern,'Raster phase did not follow map state')
      runs=[len(list(group)) for _,group in itertools.groupby(records)][1:-1]
      assert runs and all(value in (a_frames,b_frames) for value in runs),(variant,cgb,pattern,a_frames,b_frames,runs)
      assert all((new[2]-old[2])&65535==1 for old,new in zip(states,states[1:])),(variant,cgb,'Skipped LCD frame')
      for old,new in zip(states,states[1:]):
       phase,elapsed,_=old
       if elapsed+1>=(b_frames if phase else a_frames):assert new[:2]==(phase^1,0)
       else:assert new[:2]==(phase,elapsed+1)
      if (a_frames,b_frames)==(1,1):shots.append((cgb,['Layers','Shadows','Detail','Color'][pattern],image()))
      stop()
    # Every cell width, both maps, and the no-reference full-height view.
    put('flicker_pattern',2);put('flicker_compare',0)
    for cell in range(1,9):
     put('flicker_cell',cell);start();press('a');assert get('flicker_paused'),('Pause',variant,cgb,cell)
     phase=get('flicker_phase');v=vram()
     for y in range(144):
      for x in range(160):
       tile=v[(0x1c00 if phase else 0x1800)+(y//8)*32+x//8];at=tile*16+(y&7)*2;bit=7-(x&7)
       color=((v[at]>>bit)&1)|(((v[at+1]>>bit)&1)<<1)
       assert color==(3 if ((x//cell)^(y//cell)^phase)&1 else 0),(variant,cgb,cell,x,y,color)
     before=(get('flicker_ticks',2),get('flicker_x'),get('flicker_y'),image().tobytes());tick(20)
     assert before==(get('flicker_ticks',2),get('flicker_x'),get('flicker_y'),image().tobytes()),'Pause advanced'
     ticks=get('flicker_ticks',2);press('right');assert get('flicker_ticks',2)==ticks+1,'Single-step advanced more than one frame'
     stop()
    # Motion clocks, wrap limits and axes use actual consecutive LCD frames.
    put('flicker_pattern',0);put('flicker_compare',1);put('flicker_a',2);put('flicker_b',3)
    for cycle in [0,1]:
     put('flicker_cycle',cycle)
     for axis in range(3):
      put('flicker_axis',axis);put('flicker_speed',8);start()
      old=(get('flicker_x'),get('flicker_y'),get('flicker_phase'))
      for _ in range(60):
       tick();new=(get('flicker_x'),get('flicker_y'),get('flicker_phase'))
       delta=8 if not cycle or old[2]==1 and new[2]==0 else 0
       assert new[0]==(old[0]+(delta if axis!=1 else 0))%144
       assert new[1]==(old[1]+(delta if axis!=0 else 0))%96
       old=new
      stop()
    # Both CGB pairs and endpoint extremes must reach the framebuffer.
    if cgb:
     put('flicker_pattern',3);put('flicker_speed',0);put('flicker_a',60);put('flicker_b',60);put('flicker_lead',0)
     for pair in range(3):
      put('flicker_pair',pair);put('flicker_level_a',31);put('flicker_level_b',31 if pair else 0);start()
      assert image().getpixel((4,4))!=image().getpixel((100,4)),('Color pair collapsed',pair)
      stop()
    start();hold(['a','b','select','start']);tick(80);hold([]);tick(30)
    assert 'Continue' in text() and not get('flicker_ready');press('b');assert 'Flicker' in text()
    hold(['a','b','select','start']);tick(80);hold([]);tick(60);assert 'Test menu' in text(),('Missing second modal',text());press('down');press('a');tick(60)
    assert get('selected_test')==10 and not get('flicker_running')
    assert all(read(0xfe00+i*4)==b'\x00' for i in range(40)),'Stale actor sprites'
    if not args.core:assert p.memory[0xff40]&8==0 and p.memory[0xff42]==p.memory[0xff43]==0
    # Re-entering restores the canonical font before the preset list.
    press('a');assert 'Flicker presets' in text();press('b')
    if not args.core:assert dma and all(144<=ly<=151 and mode==1 for ly,mode in dma),('OAM DMA outside VBlank',collections.Counter(dma))
    results.append(f'{variant or "mbc5"}-{"cgb" if cgb else "dmg"}')
   except Exception:
    image().save(OUT/'first-failing-frame.png');raise
   finally:
    if args.core:p.close()
    else:p.stop(save=False)
 if args.rom:break
board=Image.new('RGB',(5*168,((len(shots)+4)//5)*164),(227,219,200));draw=ImageDraw.Draw(board)
for i,(cgb,label,im) in enumerate(shots):
 x=i%5*168+4;y=i//5*164+4;board.paste(im,(x,y));draw.text((x,y+146),('GBC ' if cgb else 'GB ')+label,fill=(64,40,32))
board.save(OUT/'screens.png');(OUT/'results.json').write_text(json.dumps(results,indent=2)+'\n')
print('Raw phase durations, static reference, 1-8 px cells, frame/cycle motion, pause/step, presets and menu cleanup passed:',', '.join(results))
