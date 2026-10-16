"""Show diagonal counts using the cartridge's own rendered font and frame."""
from pathlib import Path
import runpy
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
n=runpy.run_path(str(ROOT/'tools/mockup_additions.py'));im=n['screen']('DIAGONALS','4/4')
for i,label in enumerate(['UP RIGHT','UP LEFT','DN RIGHT','DN LEFT']):
 n['text'](im,2,6+i*2,label);n['text'](im,11,6+i*2,'3' if i==0 else '0');n['cell'](im,1,6+i*2,72 if i==0 else 73)
n['text'](im,1,15,'OPPOSITES');n['text'](im,12,15,'0');n['text'](im,1,16,'ENTRY COUNTS')
im.resize((480,432),Image.Resampling.NEAREST).save(ROOT/'build/diagonal-mockup.png')
