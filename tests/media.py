"""Record which ROM build and commit each review capture came from."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
RECORD=ROOT/'assets/media.json'

def record(files,roms,emulator):
 """Store the SHA-256 of every ROM a capture used, keyed by the asset's name."""
 data=json.loads(RECORD.read_text()) if RECORD.exists() else {}
 git=lambda *a:subprocess.run(['git',*a],cwd=ROOT,capture_output=True,text=True).stdout.strip()
 # A build from uncommitted sources is marked, since its commit alone does not reproduce it.
 commit=git('rev-parse','--short','HEAD')+('+changes' if git('status','--porcelain','--','src','tools','vendor','Makefile') else '')
 roms={name:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for name,path in roms.items()}
 for name in files:data[name]={'roms':roms,'built_from':commit,'emulator':emulator}
 RECORD.write_text(json.dumps(dict(sorted(data.items())),indent=1)+'\n')
