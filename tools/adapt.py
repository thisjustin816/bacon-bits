"""Make banked entry points without changing the vendored diagnostics."""
from pathlib import Path
import sys,re
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'build/adapted';out.mkdir(parents=True,exist_ok=True)
p=(ROOT/'vendor/platform-detect/main.c').read_text()
p='#pragma bank 1\n#include "bb.h"\n#include <gbdk/font.h>\n'+p
p=p.replace('void main(void) {','void platform_run(void) BANKED {')
p=p.replace('    /* GBDK leaves', '    font_init(); font_load(font_ibm);\n    vsync();\n    /* GBDK leaves')
p='#include "platform_details.h"\n'+p
p=p.replace('    sgb_answered = sgb_check();','    pd_cgb = (_cpu == CGB_TYPE);\n    sgb_answered = sgb_check();')
p=p.replace('    binjgb_like =', '    pd_before=ff72.before; pd_obs[0][0]=ff72.first; pd_obs[0][1]=ff72.second; pd_obs[0][2]=ff73.first; pd_obs[0][3]=ff73.second;\n    pd_obs[1][0]=ff74.first;pd_obs[1][1]=ff74.second;\n    binjgb_like =',1)
p=p.replace('if (write_and_restore(0x75u, 0x00u) != 0x8Fu', 'pd_obs[2][1]=unk75_ff;\n    if ((pd_obs[2][0]=write_and_restore(0x75u, 0x00u)) != 0x8Fu')
for addr,idx in [('6C',3),('4D',7),('01',9)]:
 p=p.replace(f'io_write_read(0x{addr}u, 0x00u) !=',f'(pd_obs[{idx}][0]=io_write_read(0x{addr}u, 0x00u)) !=') if addr=='6C' else p.replace(f'write_and_restore(0x{addr}u, 0x00u)',f'(pd_obs[{idx}][0]=write_and_restore(0x{addr}u, 0x00u))')
p=p.replace('    pcm_ff =', '    pd_obs[4][0]=io_read(0x76u);pd_obs[4][1]=io_read(0x77u);\n    pcm_ff =')
p=p.replace('    if (rp00 !=','    pd_obs[5][0]=rp00;\n    if (rp00 !=')
p=p.replace('    if (vbk00 !=','    pd_obs[6][0]=vbk00;\n    if (vbk00 !=')
p=p.replace('    if (key0 !=','    pd_obs[8][0]=key0;\n    if (key0 !=')
p=p.replace('io_write_read(0x4Eu, 0x00u) !=','(pd_obs[10][0]=io_write_read(0x4Eu, 0x00u)) !=').replace('io_write_read(0x57u, 0x00u) !=','(pd_obs[10][1]=io_write_read(0x57u, 0x00u)) !=')
p=p.replace('    if (sgb_answered) tells','    pd_obs[11][0]=sgb_answered;\n    if (sgb_answered) tells')
p=p.replace('    failed = 0u;','    pd_mask=tells;for(i=0;i<4;++i)pd_oam[i]=oam[i];\n    for(i=0;match[i] && i<11;++i)pd_name[i]=match[i];pd_name[i]=0;\n    failed = 0u;')
p=p.replace('while (1) vsync();','''LCDC_REG |= 0x10u;set_bkg_data(0,64,bb_font);set_bkg_data(TILE_RULE,1,rule_tile);
    while (1) { vsync(); if (bb_exit()) return;
        if (bb_keys == J_SELECT) {
            pd_show();font_init();font_load(font_ibm);LCDC_REG|=0x10u;set_bkg_data(0,64,bb_font);set_bkg_data(TILE_RULE,1,rule_tile);
            if (_cpu==CGB_TYPE) {vsync();set_bkg_palette(0,5,palettes);}
            pd_restore();
        }
    }''')
(out/'platform.c').write_text(p)
p=(ROOT/'vendor/link-sustain/main.c').read_text()
p='#pragma bank 2\n#include "bb.h"\nstatic uint8_t link_exit;\n'+p
p=p.replace('void main(void) {','void link_run(void) BANKED {')
p=p.replace('    font_init(); handle', '    link_exit = 0; running = 0;\n    font_init(); handle')
p=p.replace('        if (pressed & J_UP)', '        if ((keys & (J_A|J_B|J_START|J_SELECT)) == (J_A|J_B|J_START|J_SELECT)) {\n            if (bb_exit()) { link_exit = 1; return; }\n            previous = 0; continue;\n        }\n        if (pressed & J_UP)')
p=p.replace('font_base = ((pmfont_handle)handle)->first_tile;', 'font_base=128;LCDC_REG|=0x10u;set_bkg_data(128,64,bb_font);')
p=p.replace('font_min[2u + c] + font_base', '(c >= 97 && c <= 122 ? c-32 : c)-32+128')
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
from lettering import tiles as letter_tiles
import font
glyphs=bytearray(letter_tiles());original=font.all_tiles()
for code in [91,93]:glyphs[(code-32)*16:(code-31)*16]=original[(code-32)*16:(code-31)*16]
combined_font=bytes(glyphs)+original[1024:1280]+bytes(b^255 for b in glyphs)+bytes(b if i&1 else 0 for i,b in enumerate(glyphs))
source=source.replace('for byte in font.all_tiles():','for byte in combined_font:')
source=source.replace('a.org(0x150)','a.org(0x4000)')
source=source.replace('a.b(0x31, 0xFE, 0xFF)','a.nop().nop().nop()')
noi=ROOT/'build/bacon-bits.noi'
gate=0
if noi.exists():
 m=re.search(r'DEF _rumble_gate (0x[0-9A-Fa-f]+)',noi.read_text());gate=int(m[1],16) if m else 0
# Keep idle settings so partial return-chord presses can be undone.
source=source.replace("a.ld('a', 0x91).ldh(rLCDC)", '''a.ld16('hl',0xC000).ld16('de',0xC030).ld('b',0x24)
a.lab('.initial_save').b(0x2A,0x12).inc16('de').dec('b').jr('.initial_save','nz')
a.ld('a', 0x91).ldh(rLCDC)''',1)
source=source.replace("a.call('readkeys')\na.xor('a').ld_abs_a(sticky)",f'''a.call('readkeys')
a.ld_a_abs(keys).or_('a').jr('.has_keys','nz')
a.ld16('hl',0xC000).ld16('de',0xC030).ld('b',0x24)
a.lab('.idle_save').b(0x2A,0x12).inc16('de').dec('b').jr('.idle_save','nz')
a.lab('.has_keys')
a.ld_a_abs(keys).cp(0x0F).jr('.nochord', 'nz')
a.ld16('hl',0xC030).ld16('de',0xC000).ld('b',0x24)
a.lab('.restore_idle').b(0x2A,0x12).inc16('de').dec('b').jr('.restore_idle','nz')
a.call({gate})
a.or_('a').ret('nz')
a.xor('a').ld_abs_a(keys).ld_abs_a(prev).ld_abs_a(pressed)
a.call('draw_all')
a.lab('.nochord')
a.xor('a').ld_abs_a(sticky)''',1)
ns={'combined_font':combined_font,'__file__':str(ROOT/'vendor/rumble-pulse/build.py'),'__name__':'banked_build'}
exec(compile(source,'banked_rumble','exec'),ns)
rom=ns['a'].rom[0x4000:ns['code_end']]
(out/'rumble.c').write_text('#pragma bank 3\nconst unsigned char rumble_program[] = {\n'+''.join(','.join(str(x) for x in rom[i:i+24])+',\n' for i in range(0,len(rom),24))+'};\n')
(ROOT/'build/rumble-labels.json').write_text(__import__('json').dumps(ns['a'].labels,indent=2)+'\n')
print(f'Banked rumble: {len(rom)} bytes; return gate {gate:04x}')
