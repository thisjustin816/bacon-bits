"""Cut preset proposals from the cartridge's emulator-rendered tiles."""
from pathlib import Path
import runpy
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
n=runpy.run_path(str(ROOT/'tools/mockup_additions.py'));screen,text,cell=n['screen'],n['text'],n['cell']
shots=[]
for title,labels,note in [
 ('AUDIO PRESETS',['MANUAL','LOW END','PULSE PAIR','STEREO CHECK','BURST CHECK'],'32 HZ SINE / FULL'),
 ('DISPLAY PRESETS',['MANUAL','PIXEL CHECK','COLOR RANGE','MOTION CHECK','FLICKER CHECK'],'1 PIXEL CHECKER'),
 ('SRAM PRESETS',['MANUAL','POWER CYCLE','BANK CHECK','BIT PATTERNS','RETENTION'],'READ SAVED RECORD'),
 ('BURN PRESETS',['MANUAL','QUICK CHECK','LONG SOAK','OUTPUT LOAD','SRAM WATCH'],'1 MIN / MEDIUM')]:
 im=screen(title)
 # Keep the frame style; five choices use a taller box.
 for y in range(5,18):
  for x in range(20):cell(im,x,y,0)
 n['frame'](im,5,16)
 for i,label in enumerate(labels):text(im,3,6+i*2,label)
 cell(im,1,8,71);text(im,(20-len(note))//2,17,note);shots.append(im)
board=Image.new('RGB',(656,144),(232,223,206))
for i,im in enumerate(shots):board.paste(im,(i*164,0))
board.resize((1312,288),Image.Resampling.NEAREST).save(ROOT/'build/preset-mockups.png')
