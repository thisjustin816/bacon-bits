"""Make banked entry points without changing the vendored diagnostics."""
from pathlib import Path
import os
import sys,re
from wording import c_display_strings,display_case
def patch(text,old,new,count=-1):
 # A vendor update that moves a patched line must stop the build, not drop the hook.
 assert old in text,('Vendored source no longer contains',old)
 return text.replace(old,new,count)
ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/os.environ.get('BB_BUILD_DIR','build');out=BUILD/'adapted';out.mkdir(parents=True,exist_ok=True)
if not (BUILD/'manifest.h').exists():(BUILD/'manifest.h').write_text('#define BURN_CRCS {0,0,0,0,0,0,0,0}\n')
p=(ROOT/'vendor/platform-detect/main.c').read_text()
p='#pragma bank 1\n#include "bb.h"\n#include <gbdk/font.h>\n'+p
p=patch(p,'void main(void) {','void platform_run(void) BANKED {')
p=patch(p,'    /* GBDK leaves', '    font_init(); font_load(font_ibm);\n    vsync();\n    /* GBDK leaves')
p='#include "platform_details.h"\n'+p
p=patch(p,'    sgb_answered = sgb_check();','    pd_cgb = (_cpu == CGB_TYPE);\n    sgb_answered = sgb_check();')
p=patch(p,'    binjgb_like =', '    pd_before=ff72.before; pd_obs[0][0]=ff72.first; pd_obs[0][1]=ff72.second; pd_obs[0][2]=ff73.first; pd_obs[0][3]=ff73.second;\n    pd_obs[1][0]=ff74.first;pd_obs[1][1]=ff74.second;\n    binjgb_like =',1)
p=patch(p,'if (write_and_restore(0x75u, 0x00u) != 0x8Fu', 'pd_obs[2][1]=unk75_ff;\n    if ((pd_obs[2][0]=write_and_restore(0x75u, 0x00u)) != 0x8Fu')
for addr,idx in [('6C',3),('4D',7),('01',9)]:
 p=patch(p,f'io_write_read(0x{addr}u, 0x00u) !=',f'(pd_obs[{idx}][0]=io_write_read(0x{addr}u, 0x00u)) !=') if addr=='6C' else patch(p,f'write_and_restore(0x{addr}u, 0x00u)',f'(pd_obs[{idx}][0]=write_and_restore(0x{addr}u, 0x00u))')
p=patch(p,'    pcm_ff =', '    pd_obs[4][0]=io_read(0x76u);pd_obs[4][1]=io_read(0x77u);\n    pcm_ff =')
p=patch(p,'    if (rp00 !=','    pd_obs[5][0]=rp00;\n    if (rp00 !=')
p=patch(p,'    if (vbk00 !=','    pd_obs[6][0]=vbk00;\n    if (vbk00 !=')
p=patch(p,'    if (key0 !=','    pd_obs[8][0]=key0;\n    if (key0 !=')
p=patch(p,'io_write_read(0x4Eu, 0x00u) !=','(pd_obs[10][0]=io_write_read(0x4Eu, 0x00u)) !=');p=patch(p,'io_write_read(0x57u, 0x00u) !=','(pd_obs[10][1]=io_write_read(0x57u, 0x00u)) !=')
p=patch(p,'    if (sgb_answered) tells','    pd_obs[11][0]=sgb_answered;\n    if (sgb_answered) tells')
p=patch(p,'    failed = 0u;','    pd_mask=tells;for(i=0;i<4;++i)pd_oam[i]=oam[i];\n    for(i=0;match[i] && i<11;++i)pd_name[i]=match[i];pd_name[i]=0;\n    failed = 0u;')
p=patch(p,'while (1) vsync();','''LCDC_REG |= 0x10u;set_bkg_data(0,64,bb_font);set_bkg_data(TILE_RULE,1,rule_tile);
    while (1) { vsync(); if (bb_exit()) return;
        if (bb_keys == J_SELECT) {
            pd_show();font_init();font_load(font_ibm);LCDC_REG|=0x10u;set_bkg_data(0,64,bb_font);set_bkg_data(TILE_RULE,1,rule_tile);
            if (_cpu==CGB_TYPE) {vsync();set_bkg_palette(0,5,palettes);}
            pd_restore();
        }
    }''')
# Keep the probe and classifier intact; replace every standalone renderer.
a=p.index('    font_init(); font_load(font_ibm);')
b=p.index('    pd_cgb =',a)
p=p[:a]+"    pd_mask=0;pd_likely=0;pd_name[0]=0;\n"+p[b:]
a=p.index('    title();');b=p.index('    /* OAM is only readable',a)
p=p[:a]+'''    if (_cpu != CGB_TYPE) {
        const char *hw=hardware_name(sgb_answered);
        for(i=0;hw[i] && i<9;++i)pd_hardware[i]=hw[i];pd_hardware[i]=0;
        pd_summary();return;
    }
'''+p[b:]
a=p.index('    /* A named emulator counts');p=p[:a]+'''    pd_likely=tells || emulator;
    { const char *hw=hardware_name(sgb_answered);
      for(i=0;hw[i] && i<9;++i)pd_hardware[i]=hw[i];pd_hardware[i]=0; }
    pd_summary();
}
'''
(out/'platform.c').write_text(p)
p=(ROOT/'vendor/link-sustain/main.c').read_text()
p='#pragma bank 2\n#include "bb.h"\nstatic uint8_t link_exit,link_cpu_page;\n'+p
p=patch(p,'void main(void) {','void link_run(void) BANKED {')
p=patch(p,'void serial_isr(void) {','void serial_isr(void) NONBANKED {')
p=patch(p,'RGB(31,31,27), RGB(21,24,19), RGB(10,14,10), RGB(1,3,2)', 'RGB(31,30,27), RGB(31,24,6), RGB(23,9,7), RGB(8,5,4)')
p=patch(p,'    font_init(); handle', '    link_exit = 0; running = 0;\n    font_init(); handle')
p=patch(p,'        if (pressed & J_UP)', '        if ((keys & (J_A|J_B|J_START|J_SELECT)) == (J_A|J_B|J_START|J_SELECT)) {\n            if (bb_exit()) { link_exit = 1; return; }\n            previous = 0; continue;\n        }\n        if (pressed & J_UP)')
p=patch(p,'font_base = ((pmfont_handle)handle)->first_tile;', 'font_base=128;LCDC_REG|=0x10u;set_bkg_data(128,64,bb_font);')
p=patch(p,'font_min[2u + c] + font_base', '(c >= 97 && c <= 122 ? c-32 : c)-32+128')
p=patch(p,'    menu(); shown_running', '    menu(); if (link_exit) goto cleanup; shown_running')
p=patch(p,'        keys = joypad(); pressed = keys & ~previous; previous = keys;','        if (!running && bb_exit()) goto cleanup;\n        keys = joypad(); pressed = keys & ~previous; previous = keys;')
p=patch(p,'menu(); previous = J_START;', 'menu(); if (link_exit) goto cleanup; previous = J_START;')
pos=p.rfind('\n}')
p=p[:pos]+'''\ncleanup:
    running = 0; SC_REG = 0; double_cpu = 0; set_cpu_speed();
    set_interrupts(VBL_IFLAG); remove_SIO(serial_isr); remove_SIO(nowait_int_handler);
    HIDE_SPRITES;
'''+p[pos:]
# Render the original engine through the shared instrument UI.
a=p.index('void draw_header(void)');b=p.index('void set_cpu_speed(void)',a)
p=p[:a]+'#include "link_ui.inc"\n'+p[b:]
a=p.index('void draw_menu_row(uint8_t r)');b=p.index('void change_setting',a)
p=p[:a]+'''static const char *const short_tests[]={"SUSTAIN","SCENE","UNEQUAL","BALL","ALL LOAD"};
static const char *const short_rates[]={"PACED","BURST","FULL"};
void draw_menu_row(uint8_t r) {
 if(cursor<4 && r<4)ui_field(r,menu_label[r],r==ROW_TEST?short_tests[profile]:r==ROW_RATE?short_rates[rate_mode]:menu_value(r),cursor==r);
 else if(cursor==4 && r==4)ui_field(0,"CPU",menu_value(r),1);
}
'''+p[b:]
p=patch(p,'    clear_screen();\n    row(0, "LINK SUSTAIN v1.2");\n    draw_box(2, 8);','    link_cpu_page=0;ui_screen("LINK SETTINGS","1/2");')
# Rows rewrite in place; only a change between the two settings pages redraws the screen.
p=patch(p,'            for (r = 0;', '            if ((cursor==4)!=link_cpu_page) {link_cpu_page=cursor==4;ui_screen("LINK SETTINGS",link_cpu_page?"2/2":"1/2");}\n            for (r = 0;')
a=p.index('            switch (cursor) {',p.index('void menu(void)'));b=p.index('        }\n        phase',a)
p=p[:a]+'            ui_status(cursor==ROW_TEST?profiles[profile]:"STOPPED");\n'+p[b:]
p=patch(p,'if (phase != blink) { blink = phase; row(16, phase ? "    PRESS START" : ""); }','if (phase != blink) blink=phase;')
p=patch(p,'    clear_screen(); start_test();','    link_begin(); start_test();')
a=p.index('    font_init(); handle',p.index('void link_run'));b=p.index('    SHOW_BKG;',a)
p=p[:a]+'''    link_exit=0;running=0;link_view=255;ui_init();
    vsync();set_sprite_palette(0,1,colors);
    set_sprite_data(UI_LINK_BALL,1,ball_tiles);set_sprite_tile(0,UI_LINK_BALL);
'''+p[b:]
p=patch(p,'        if (pressed & (J_LEFT | J_RIGHT)) {','        link_detail_change(pressed);\n        if (pressed & (J_LEFT | J_RIGHT)) {')
p=patch(p,'page = (page + ((pressed & J_RIGHT) ? 1u : 3u)) % 4u; draw();','page = (page + ((pressed & J_RIGHT) ? 1u : 3u)) % 4u;link_detail=0;draw();')
(out/'link.c').write_text(c_display_strings(p))
for name in ['protocol','stress']:
 p=(ROOT/f'vendor/link-sustain/{name}.c').read_text()
 (out/(name+'.c')).write_text('#pragma bank 2\n'+p)
# The rumble program is self-contained, uses no interrupt vectors, and fits
# in one switchable bank. Its word fixups are resolved at the banked address.
sys.path.insert(0,str(ROOT/'vendor/rumble-pulse'))
source=(ROOT/'vendor/rumble-pulse/build.py').read_text()
from lettering import tiles as letter_tiles
import font
glyphs=bytearray(letter_tiles()[:1024]);original=font.all_tiles()
for code in [91,93]:glyphs[(code-32)*16:(code-31)*16]=original[(code-32)*16:(code-31)*16]
combined_font=bytes(glyphs)+original[1024:1280]+bytes(b^255 for b in glyphs)+bytes(b if i&1 else 0 for i,b in enumerate(glyphs))
source=patch(source,'for byte in font.all_tiles():','for byte in combined_font:')
source=patch(source,'a.org(0x150)','a.org(0x4000)')
source=patch(source,'a.b(0x31, 0xFE, 0xFF)','a.nop().nop().nop()')
noi=BUILD/'bacon-bits.noi'
gate=0
if noi.exists():
 m=re.search(r'DEF _rumble_gate (0x[0-9A-Fa-f]+)',noi.read_text());gate=int(m[1],16) if m else 0
# Keep idle settings so partial return-chord presses can be undone.
source=patch(source,"a.ld('a', 0x91).ldh(rLCDC)", '''a.ld16('hl',0xC000).ld16('de',0xC030).ld('b',0x24)
a.lab('.initial_save').b(0x2A,0x12).inc16('de').dec('b').jr('.initial_save','nz')
a.ld('a', 0x91).ldh(rLCDC)''',1)
source=patch(source,"a.call('readkeys')\na.xor('a').ld_abs_a(sticky)",f'''a.call('readkeys')
a.ld_a_abs(pressed).and_(0x0F).jr('.confirmed_keys','z')
a.ld_a_abs(pressed).ld_abs_a(0xC054)
a.call('waitframe').call('readkeys')
a.ld_a_abs(0xC054).ld('b','a').ld_a_abs(pressed).or_('b').ld_abs_a(pressed)
a.lab('.confirmed_keys')
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
draw_gate=0
if noi.exists():
 m=re.search(r'DEF _rumble_draw_gate (0x[0-9A-Fa-f]+)',noi.read_text());draw_gate=int(m[1],16) if m else 0
# The C renderer runs only at existing draw boundaries, outside timed motor segments.
a=source.index("a.ld('a', 0).ldh(rLCDC)");b=source.index("a.ld('a', 0xFF).ldh(rTMA)",a)
source=source[:a]+source[b:]
source=patch(source,"a.lab('draw_all')",f"a.lab('draw_all').call({draw_gate}).ret()\na.lab('legacy_draw_all')",1)
source=patch(source,"a.lab('draw_footer')",f"a.lab('draw_footer').ld_a_abs(keys).and_(K_SEL).ld_abs_a(lastsel).call({draw_gate}).ret()\na.lab('legacy_draw_footer')",1)
ns={'combined_font':combined_font,'__file__':str(ROOT/'vendor/rumble-pulse/build.py'),'__name__':'banked_build'}
exec(compile(source,'banked_rumble','exec'),ns)
preset_base=ns['a'].labels['presets']
preset_names=[bytes(ns['a'].rom[preset_base+i*16+3:preset_base+(i+1)*16]).split(b'\0')[0].decode().rstrip() for i in range(10)]
(BUILD/'rumble_presets.h').write_text('static const char *const names[]={'+','.join(__import__('json').dumps(display_case(name)) for name in preset_names)+'};\n')
rom=ns['a'].rom[0x4000:ns['code_end']]
(out/'rumble.c').write_text('#pragma bank 3\nconst unsigned char rumble_program[] = {\n'+''.join(','.join(str(x) for x in rom[i:i+24])+',\n' for i in range(0,len(rom),24))+'};\n')
(BUILD/'rumble-labels.json').write_text(__import__('json').dumps(ns['a'].labels,indent=2)+'\n')
print(f'Banked rumble: {len(rom)} bytes; return gate {gate:04x}')
