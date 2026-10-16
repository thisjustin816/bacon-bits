"""Compile changed translation units, then link the exact current objects."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--cc',required=True);p.add_argument('--output',default='build');p.add_argument('args',nargs=argparse.REMAINDER);a=p.parse_args()
args=a.args[1:] if a.args[:1]==['--'] else a.args
sources=[x for x in args if x.endswith('.c')];flags=[x for x in args if not x.endswith('.c')]
out=ROOT/a.output;out.mkdir(parents=True,exist_ok=True);obj=out/'objects';obj.mkdir(exist_ok=True)
state_path=out/'compile-state.json';state=json.loads(state_path.read_text()) if state_path.exists() else {}
includes=[ROOT/x[2:] for x in flags if x.startswith('-I')]
def content(path,seen):
 path=path.resolve()
 if path in seen:return b''
 seen.add(path);data=path.read_bytes();result=data
 for opener,name in re.findall(rb'^\s*#\s*include\s*(["<])([^"<>\n]+)[">]',data,re.M):
  for folder in ([path.parent] if opener==b'"' else [])+includes:
   f=folder/name.decode()
   if f.exists():result+=content(f,seen);break
 return result
objects=[]
for source in sources:
 path=ROOT/source;target=obj/(source.replace('/','_')+'.o');objects.append(str(target))
 signature=hashlib.sha256(json.dumps([a.cc,flags]).encode()+content(path,set())).hexdigest()
 if state.get(source)!=signature or not target.exists():
  subprocess.run([a.cc,*flags,'-c','-o',str(target),str(path)],cwd=ROOT,check=True);state[source]=signature
  state_path.write_text(json.dumps(state,indent=2)+'\n')
subprocess.run([a.cc,*flags,'-o',str(out/'bacon-bits.gbc'),*objects],cwd=ROOT,check=True)
