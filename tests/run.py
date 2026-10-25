"""Run the cartridge suites and retain a log and ROM identity for every group."""
from pathlib import Path
import argparse,concurrent.futures,hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--core',type=Path,help='SameBoy libretro core; without it the SameBoy suites are reported as not run');a.add_argument('--jobs',type=int,default=4);a.add_argument('cases',nargs='*',help='run only these suites, for example the ones a change touches');args=a.parse_args()
commands={name:[sys.executable,'tests/'+name+'.py'] for name in ['smoke','modal_regression','rumble_combined','audio_ui','audio_backend','audio_shapes','audio_responsiveness','additions','sram_patterns','burn_faults','presets','lettering','menu_alignment','ui_spacing','diagonals','graphical_ui','serial_ui_bank','cartridge_features','ir_cycles','ir_pair','preset_bounce','rtc','variants','flicker','display_font','screen_text','display_timing','buttons_chord','burn_cadence','sram_burn','audio_dacs','stack_depth']}
commands['build_check']=[sys.executable,'tools/check_build.py']
commands['mbc3_build_check']=[sys.executable,'tools/check_build.py']
commands['mbc3_additions']=[sys.executable,'tests/additions.py','build/mbc3/bacon-bits.gbc']
commands['mbc3_audio_backend']=[sys.executable,'tests/audio_backend.py','build/mbc3/bacon-bits.gbc']
commands['mbc3_audio']=[sys.executable,'tests/audio_ui.py','build/mbc3/bacon-bits.gbc']
commands['mbc3_audio_dacs']=[sys.executable,'tests/audio_dacs.py','--rom','build/mbc3/bacon-bits.gbc']
sameboy=['sameboy','audio_sameboy','additions_sameboy','rumble_return','hardware_sameboy','ui_transitions','menu_art','raster_transitions','burn_rumble','screen_tour','flicker_sameboy']
if args.core:
 for name in sameboy:commands[name]=[sys.executable,'tests/'+('flicker' if name=='flicker_sameboy' else name)+'.py','--core',str(args.core)]
slow=['link_combined','upstream','link_pair']
known=set(commands)|set(sameboy)|set(slow)
unknown=[name for name in args.cases if name not in known]
if unknown:a.error('unknown suites: '+', '.join(unknown))
if args.cases:
 missing=[name for name in args.cases if name in sameboy and not args.core]
 if missing:a.error('these suites need --core: '+', '.join(missing))
 commands={name:command for name,command in commands.items() if name in args.cases}
 slow=[name for name in slow if name in args.cases]
paths=[('mbc5','build/bacon-bits.gbc'),('mbc3','build/mbc3/bacon-bits.gbc')]
identities={name:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for name,path in paths}
if args.jobs<1:a.error('--jobs must be positive')
def run(item):
 name,command=item;env=dict(os.environ)
 if name=='mbc3_build_check':env['BB_BUILD_DIR']='build/mbc3'
 log=ROOT/'build'/('verify-'+name+'.log')
 with log.open('w') as out:
  try:code=subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=subprocess.STDOUT,timeout=1800 if name in ['link_combined','upstream','link_pair'] else 600).returncode
  except subprocess.TimeoutExpired:
   out.write('\nSuite exceeded its time limit\n');code=124
 print(name,'PASS' if code==0 else 'FAIL',flush=True);return name,code
with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:results=dict(pool.map(run,commands.items()))
# Each paired suite owns its workers and temporary emulator, so run the two
# slow groups separately from one another and from the sample-capture suites.
for name in slow:results.update([run((name,[sys.executable,'tests/'+name+'.py']))])
after={name:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for name,path in paths}
if identities!=after:results['rom_changed_during_verification']=1
skipped=[] if args.core or args.cases else sameboy
if skipped:print('NOT RUN (no --core):',', '.join(skipped),flush=True)
(ROOT/'build/verification.json').write_text(json.dumps({'rom_sha256':identities,'results':results,'not_run':skipped,'selected':args.cases or 'all'},indent=2)+'\n')
raise SystemExit(any(results.values()))
