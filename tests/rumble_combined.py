"""Replay the original timing suite against the banked assembly bytes."""
from pathlib import Path
import json,runpy,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor/rumble-pulse'))
import build
rom=(ROOT/'build/bacon-bits.gbc').read_bytes()
# The timing interpreter has a flat 32 KiB bus. Map the combined ROM's
# rumble bank at $4000 and enter it directly, bypassing the C launcher.
flat=bytearray(0x8000)
flat[0x100:0x103]=bytes([0xc3,0,0x40])
flat[0x4000:]=rom[3*0x4000:4*0x4000]
build.a.rom=flat
build.a.labels=json.loads((ROOT/'build/rumble-labels.json').read_text())
runpy.run_path(str(ROOT/'vendor/rumble-pulse/test.py'),run_name='__main__')
print('Original rumble timing suite passed against the combined ROM bank')
