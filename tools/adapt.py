"""Make banked entry points without changing the vendored diagnostics."""
from pathlib import Path
import sys,re
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'build/adapted';out.mkdir(parents=True,exist_ok=True)
p=(ROOT/'vendor/platform-detect/main.c').read_text()
p='#pragma bank 1\n#include "bb.h"\n#include <gbdk/font.h>\n'+p
p=p.replace('void main(void) {','void platform_run(void) BANKED {')
p=p.replace('    /* GBDK leaves', '    font_init(); font_load(font_ibm);\n    vsync();\n    /* GBDK leaves')
p=p.replace('while (1) vsync();','while (1) { vsync(); if (bb_exit()) return; }')
(out/'platform.c').write_text(p)
p=(ROOT/'vendor/link-sustain/main.c').read_text()
p='#pragma bank 2\n#include "bb.h"\nstatic uint8_t link_exit;\n'+p
p=p.replace('void main(void) {','void link_run(void) BANKED {')
p=p.replace('    font_init(); handle', '    link_exit = 0; running = 0;\n    font_init(); handle')
p=p.replace('        if (pressed & J_UP)', '        if ((keys & (J_A|J_B|J_START|J_SELECT)) == (J_A|J_B|J_START|J_SELECT)) {\n            if (bb_exit()) { link_exit = 1; return; }\n            previous = 0; continue;\n        }\n        if (pressed & J_UP)')
p=p.replace('    menu(); shown_running', '    menu(); if (link_exit) goto cleanup; shown_running')
p=p.replace('        keys = joypad(); pressed = keys & ~previous; previous = keys;','        if (!running && bb_exit()) goto cleanup;\n        keys = joypad(); pressed = keys & ~previous; previous = keys;')
p=p.replace('menu(); previous = J_START;', 'menu(); if (link_exit) goto cleanup; previous = J_START;')
pos=p.rfind('\n}')
p=p[:pos]+'''\ncleanup:
    running = 0; SC_REG = 0; double_cpu = 0; set_cpu_speed();
    set_interrupts(VBL_IFLAG); remove_SIO(serial_isr); remove_SIO(nowait_int_handler);
    HIDE_SPRITES;
'''+p[pos:]
(out/'link.c').write_text(p)
for name in ['protocol','stress']:
 p=(ROOT/f'vendor/link-sustain/{name}.c').read_text()
 (out/(name+'.c')).write_text('#pragma bank 2\n'+p)
# The rumble program is self-contained, uses no interrupt vectors, and fits
# in one switchable bank. Its word fixups are resolved at the banked address.
sys.path.insert(0,str(ROOT/'vendor/rumble-pulse'))
source=(ROOT/'vendor/rumble-pulse/build.py').read_text()
source=source.replace('a.org(0x150)','a.org(0x4000)')
source=source.replace('a.b(0x31, 0xFE, 0xFF)','a.nop().nop().nop()')
noi=ROOT/'build/bacon-bits.noi'
gate=0
if noi.exists():
 m=re.search(r'DEF _rumble_gate (0x[0-9A-Fa-f]+)',noi.read_text());gate=int(m[1],16) if m else 0
source=source.replace("a.call('readkeys')\na.xor('a').ld_abs_a(sticky)",f'''a.call('readkeys')
a.ld_a_abs(keys).cp(0x0F).jr('.nochord', 'nz')
a.call({gate})
a.or_('a').ret('nz')
a.xor('a').ld_abs_a(keys).ld_abs_a(prev).ld_abs_a(pressed)
a.lab('.nochord')
a.xor('a').ld_abs_a(sticky)''',1)
ns={'__file__':str(ROOT/'vendor/rumble-pulse/build.py'),'__name__':'banked_build'}
exec(compile(source,'banked_rumble','exec'),ns)
rom=ns['a'].rom[0x4000:ns['code_end']]
(out/'rumble.c').write_text('#pragma bank 3\nconst unsigned char rumble_program[] = {\n'+''.join(','.join(str(x) for x in rom[i:i+24])+',\n' for i in range(0,len(rom),24))+'};\n')
(ROOT/'build/rumble-labels.json').write_text(__import__('json').dumps(ns['a'].labels,indent=2)+'\n')
print(f'Banked rumble: {len(rom)} bytes; return gate {gate:04x}')
