"""Rebuild and run every vendored standalone diagnostic suite."""
from pathlib import Path
import shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'build/upstream';DEST.mkdir(parents=True,exist_ok=True)
def run(args,cwd):subprocess.run(args,cwd=cwd,check=True)
for name in ['platform-detect','link-sustain']:
 d=DEST/name;d.mkdir(exist_ok=True)
 shutil.copytree(ROOT/'vendor'/name/'tests',d/'tests',dirs_exist_ok=True)
 shutil.copy(ROOT/'vendor'/name/'Makefile',d/'Makefile')
 (d/'src').mkdir(exist_ok=True)
 for f in (ROOT/'vendor'/name).iterdir():
  if f.suffix in ['.c','.h']:shutil.copy(f,d/'src'/f.name)
 run(['make'],d)
 suites=[['smoke.py']] if name=='platform-detect' else [['protocol.py'],['stress.py'],['smoke.py'],['features.py'],['paired.py'],['paired.py','--stress']]
 for suite in suites:run([sys.executable,'tests/'+suite[0],*suite[1:]],d)
d=DEST/'rumble-pulse';shutil.copytree(ROOT/'vendor/rumble-pulse',d/'src',dirs_exist_ok=True)
run([sys.executable,'src/build.py'],d)
run([sys.executable,'src/test.py'],d)
print('Every vendored standalone suite passed')
