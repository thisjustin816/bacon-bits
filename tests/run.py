"""Run the cartridge suites and retain a log and ROM identity for every group."""
from pathlib import Path
import argparse,concurrent.futures,hashlib,json,os,subprocess,sys,threading
ROOT=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--core',type=Path,help='SameBoy libretro core; without it the SameBoy suites are reported as not run');a.add_argument('--jobs',type=int,default=4);a.add_argument('--resume',action='store_true',help='skip suites that already passed for the same ROMs, test sources and core, as recorded in build/verification-progress.json');a.add_argument('--shard',metavar='K/N',help='run slice K of N of the suites a full run starts together, as in 2/4; the slow suites run only when named');a.add_argument('--list',action='store_true',help='print the suites this run would start, one per line, and exit');a.add_argument('cases',nargs='*',help='run only these suites, for example the ones a change touches');args=a.parse_args()
commands={name:[sys.executable,'tests/'+name+'.py'] for name in ['smoke','modal_regression','rumble_combined','audio_ui','audio_backend','audio_shapes','audio_responsiveness','additions','sram_patterns','burn_faults','presets','lettering','menu_alignment','ui_spacing','diagonals','graphical_ui','serial_ui_bank','cartridge_features','ir_cycles','ir_pair','preset_bounce','platform_mode3','rtc','variants','flicker','display_font','screen_text','display_timing','buttons_chord','burn_cadence','sram_burn','audio_dacs','stack_depth']}
commands['build_check']=[sys.executable,'tools/check_build.py']
commands['mbc3_build_check']=[sys.executable,'tools/check_build.py']
commands['mbc3_additions']=[sys.executable,'tests/additions.py','build/mbc3/bacon-bits.gbc']
commands['mbc3_audio_backend']=[sys.executable,'tests/audio_backend.py','build/mbc3/bacon-bits.gbc']
commands['mbc3_audio']=[sys.executable,'tests/audio_ui.py','build/mbc3/bacon-bits.gbc']
commands['mbc3_audio_dacs']=[sys.executable,'tests/audio_dacs.py','--rom','build/mbc3/bacon-bits.gbc']
sameboy=['sameboy','audio_sameboy','additions_sameboy','rumble_return','hardware_sameboy','ui_transitions','menu_art','raster_transitions','burn_rumble','screen_tour','flicker_sameboy','platform_mode3_sameboy']
if args.core:
 for name in sameboy:commands[name]=[sys.executable,'tests/'+(name[:-len('_sameboy')] if name in ('flicker_sameboy','platform_mode3_sameboy') else name)+'.py','--core',str(args.core)]
slow=['link_combined','upstream','link_pair','link_long','link_stress','link_snapshot']
known=set(commands)|set(sameboy)|set(slow)
unknown=[name for name in args.cases if name not in known]
if unknown:a.error('unknown suites: '+', '.join(unknown))
if args.cases:
 missing=[name for name in args.cases if name in sameboy and not args.core]
 if missing:a.error('these suites need --core: '+', '.join(missing))
 commands={name:command for name,command in commands.items() if name in args.cases}
 slow=[name for name in slow if name in args.cases]
if args.shard:
 try:index,count=map(int,args.shard.split('/'));assert 1<=index<=count
 except (ValueError,AssertionError):a.error('--shard takes K/N with 1 <= K <= N')
 if args.cases:a.error('--shard takes the place of suite names')
 commands={name:command for position,(name,command) in enumerate(commands.items()) if position%count==index-1};slow=[]
if args.list:
 print('\n'.join([*commands,*slow]));raise SystemExit(0)
paths=[('mbc5','build/bacon-bits.gbc'),('mbc3','build/mbc3/bacon-bits.gbc')]
identities={name:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for name,path in paths}
if args.jobs<1:a.error('--jobs must be positive')
# Every finished suite is recorded at once, so a run cut short by a restart loses only the suites in
# flight. A pass is reused only under the ROMs, test and tool sources and core that produced it.
def fingerprint():
 h=hashlib.sha256()
 for name,digest in sorted(identities.items()):h.update(f'{name} {digest}\n'.encode())
 for folder in ('tests','tools'):
  for path in sorted((ROOT/folder).rglob('*.py')):h.update(path.relative_to(ROOT).as_posix().encode()+b'\0'+path.read_bytes()+b'\0')
 if args.core:h.update(hashlib.sha256(args.core.read_bytes()).digest())
 return h.hexdigest()
progress=ROOT/'build/verification-progress.json';key=fingerprint()
try:saved=json.loads(progress.read_text())
except (OSError,ValueError):saved={}
passed=set(saved.get('passed',[])) if saved.get('fingerprint')==key else set()
reusable=set(passed) if args.resume else set()
resumed=[];lock=threading.Lock()
def record(name,code):
 with lock:
  (passed.add if code==0 else passed.discard)(name)
  temporary=progress.with_name(progress.name+'.tmp');temporary.write_text(json.dumps({'fingerprint':key,'passed':sorted(passed)},indent=2)+'\n');temporary.replace(progress)
def run(item):
 name,command=item;env=dict(os.environ)
 if name in reusable:
  resumed.append(name);print(name,'PASS (resumed)',flush=True);return name,0
 if name=='mbc3_build_check':env['BB_BUILD_DIR']='build/mbc3'
 log=ROOT/'build'/('verify-'+name+'.log')
 with log.open('w') as out:
  try:code=subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=subprocess.STDOUT,timeout=1800 if name in slow else 600).returncode
  except subprocess.TimeoutExpired:
   out.write('\nSuite exceeded its time limit\n');code=124
 record(name,code);print(name,'PASS' if code==0 else 'FAIL',flush=True);return name,code
with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:results=dict(pool.map(run,commands.items()))
# Each paired suite owns its workers and temporary emulator, so run the two
# slow groups separately from one another and from the sample-capture suites.
for name in slow:results.update([run((name,[sys.executable,'tests/'+name+'.py']))])
after={name:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for name,path in paths}
if identities!=after:results['rom_changed_during_verification']=1
skipped=[] if args.core or args.cases else sameboy
if skipped:print('NOT RUN (no --core):',', '.join(skipped),flush=True)
(ROOT/'build/verification.json').write_text(json.dumps({'rom_sha256':identities,'results':results,'not_run':skipped,'resumed':sorted(resumed),'selected':args.cases or 'all'},indent=2)+'\n')
raise SystemExit(any(results.values()))
