"""Expected Audio values written out here, not read from the ROM or its generators."""
import math
# The pulse frequency steps in Hz. Wave plays each step an octave lower.
PULSE_HZ=[64,65,66,68,70,72,76,80,85,90,96,100,110,120,128,140,160,180,200,220,256,320,440,512,640,880,1024,2048,4096,8192,16384,32768,65536,131072]
# Wave RAM for each wave shape, two 4-bit samples per byte, high nibble first.
SINE=bytes.fromhex('89abdeefffeedba98654211000112456')
WAVES=[SINE,bytes([0xff]*8+[0]*8),bytes([(i<<4)|(i+1) for i in range(0,16,2)]+[(i<<4)|(i-1) for i in range(15,0,-2)]),
 bytes([i*17 for i in range(16)]),bytes([i*17 for i in range(15,-1,-1)]),bytes([0xff]*4+[0]*12)]

# The sine table is the cartridge's reviewed one; keep it within one step of the curve.
_samples=[n for b in SINE for n in (b>>4,b&15)]
assert all(abs(s-(7.5+7.5*math.sin(2*math.pi*i/32)))<=1 for i,s in enumerate(_samples)),'SINE is not a sine'
