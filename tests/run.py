"""Run the cartridge suites and retain a log and ROM identity for every group."""
from pathlib import Path
import argparse,concurrent.futures,hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--core',required=True,type=Path);a.add_argument('--jobs',type=int,default=4);args=a.parse_args()
commands={name:[sys.executable,'tests/'+name+'.py'] for name in ['smoke','modal_regression','rumble_combined','audio_ui','audio_backend','audio_shapes','audio_responsiveness','additions','sram_patterns','burn_faults','presets','feature_regression','lettering','menu_alignment','ui_spacing','diagonals','graphical_ui','serial_ui_bank','cartridge_features','ir_cycles','rtc','variants','flicker']}
commands['build_check']=[sys.executable,'tools/check_build.py']
commands['mbc3_additions']=[sys.executable,'tests/additions.py','build/mbc3/bacon-bits.gbc']
commands['mbc3_audio_backend']=[sys.executable,'tests/audio_backend.py','build/mbc3/bacon-bits.gbc']
commands['mbc3_audio']=[sys.executable,'tests/audio_ui.py','build/mbc3/bacon-bits.gbc']
for name in ['sameboy','audio_sameboy','additions_sameboy','rumble_return','hardware_sameboy','ui_transitions','menu_art']:commands[name]=[sys.executable,'tests/'+name+'.py','--core',str(args.core)]
commands['flicker_sameboy']=[sys.executable,'tests/flicker.py','--core',str(args.core)]
paths=[('mbc5','build/bacon-bits.gbc'),('mbc3','build/mbc3/bacon-bits.gbc')]
identities={name:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for name,path in paths}
def run(item):
 name,command=item;log=ROOT/'build'/('verify-'+name+'.log')
 with log.open('w') as out:code=subprocess.run(command,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT).returncode
 print(name,'PASS' if code==0 else 'FAIL',flush=True);return name,code
with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:results=dict(pool.map(run,commands.items()))
# Each paired suite owns its workers and temporary emulator, so run the two
# slow groups separately from one another and from the sample-capture suites.
for name in ['link_combined','upstream']:results.update([run((name,[sys.executable,'tests/'+name+'.py']))])
after={name:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for name,path in paths}
if identities!=after:results['rom_changed_during_verification']=1
(ROOT/'build/verification.json').write_text(json.dumps({'rom_sha256':identities,'results':results},indent=2)+'\n')
raise SystemExit(any(results.values()))
