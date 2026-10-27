"""Merge the verification.json files of the CI shards and fail unless every expected suite passed on one pair of ROMs."""
import json,os,sys
from pathlib import Path
expected=Path(sys.argv[1]).read_text().split()
roms=set();results={};not_run=[]
for path in sorted(Path(sys.argv[2]).rglob('verification.json')):
 data=json.loads(path.read_text())
 roms.add(json.dumps(data['rom_sha256'],sort_keys=True));results.update(data['results']);not_run+=data['not_run']
missing=[name for name in expected if name not in results]
failed=sorted(name for name,code in results.items() if code)
problems=[]
if missing:problems.append('not run: '+', '.join(missing))
if failed:problems.append('failed: '+', '.join(failed))
if not_run:problems.append('reported not run: '+', '.join(not_run))
if len(roms)!=1:problems.append(f'{len(roms)} sets of ROM hashes, expected 1')
lines=[f'{len(expected)-len(missing)-len(failed)} of {len(expected)} suites passed']+problems
if len(roms)==1:lines.append('ROM SHA-256: '+', '.join(f'{name} {digest}' for name,digest in json.loads(next(iter(roms))).items()))
print('\n'.join(lines))
if os.environ.get('GITHUB_STEP_SUMMARY'):
 with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as out:out.write('## Verification\n\n'+'\n\n'.join(lines)+'\n')
raise SystemExit(bool(problems))
