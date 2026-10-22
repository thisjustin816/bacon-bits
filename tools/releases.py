"""Check and copy both original diagnostic releases and their SHA-256 list."""
from pathlib import Path
import hashlib,os,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
lines=[]
for build,name in [('build','Bacon Bit Bench (MBC5+Rumble).gbc'),('build/mbc3','Bacon Bit Bench (MBC3+RTC).gbc')]:
 env=dict(os.environ,BB_BUILD_DIR=build)
 subprocess.run([sys.executable,'tools/check_build.py'],cwd=ROOT,env=env,check=True)
 source=ROOT/build/'bacon-bits.gbc';shutil.copyfile(source,ROOT/name)
 lines.append(hashlib.sha256(source.read_bytes()).hexdigest()+'  '+name)
(ROOT/'SHA256SUMS').write_text('\n'.join(lines)+'\n')
