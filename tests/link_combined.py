"""Run the original link behavior suites in the banked combined ROM."""
from pathlib import Path
import subprocess,shutil,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
d=ROOT/'build/combined-link';d.mkdir(exist_ok=True);(d/'build').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix="bacon-link-") as temporary:
 source=Path(temporary)
 for name in ["src","tools","vendor"]:shutil.copytree(ROOT/name,source/name)
 shutil.copy(ROOT/'Makefile',source/'Makefile')
 subprocess.run(['make','AUTORUN=1','PYTHON='+sys.executable],cwd=source,check=True)
 shutil.copy(source/'build/bacon-bits.gbc',d/'link-sustain.gbc')
 shutil.copy(source/'build/bacon-bits.noi',d/'link-sustain.noi')
shutil.copytree(ROOT/'vendor/link-sustain/tests',d/'tests',dirs_exist_ok=True)
shutil.copytree(ROOT/'vendor/link-sustain',d/'src',ignore=shutil.ignore_patterns('tests','Makefile'),dirs_exist_ok=True)
# The native suite's one instruction hook now points into ROM bank 2.
p=d/'tests/paired.py';text=p.read_text();text=text.replace('p.hook_register(0, syms["_begin_update"],','p.hook_register(syms["_begin_update"] >> 16, syms["_begin_update"] & 0xffff,');p.write_text(text)
p=d/'tests/features.py';text=p.read_text()
text=text.replace('screen_row(p, 2, 7)', 'screen_row(p, 17, 8)')
text=text.replace('has_color(screen_row(p, 3), is_red)', "verdict().startswith('FAIL')")
text=text.replace('has_color(screen_row(p, 3), is_green)', "verdict().startswith('PASS')")
text=text.replace('    inject.sequence = -1', "    def verdict():return ''.join(chr(t+32).upper() if t<96 else '#' for t in p.memory[0,0x9a21:0x9a29])\n    inject.sequence = -1",1)
p.write_text(text)
for args in [['features.py'],['paired.py'],['paired.py','--stress']]:
 subprocess.run([sys.executable,'tests/'+args[0],*args[1:]],cwd=d,check=True)
print('Combined-ROM link feature and paired suites passed')
