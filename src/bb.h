#ifndef BB_H
#define BB_H
#include <gb/gb.h>
#include <gb/cgb.h>
/* Every screen polls input only after it is fully drawn, so the first poll
   uncovers a screen that ui_init hid while it was rebuilt. */
uint8_t bb_joypad(void) NONBANKED;
#define joypad() bb_joypad()
#define UI_FONT_COUNT 96
#define UI_CHROME 96
#define UI_CURSOR 103
#define UI_EMPTY 105
#define UI_PASS 107
#define UI_FAIL 108
#define UI_ACTIVE 109
#define UI_LINK_BALL 110
#define UI_ART 112
#define UI_FOCUS 232
#define UI_FOCUS_EXTRA 61
/* Screen rows: the box's top border holds the title, fields start below a
   blank row, the bottom border holds the status, and one detail line sits
   under the box with a blank row between. */
#define UI_TOP 4
#define UI_FIELD 6
#define UI_BOTTOM 15
#define UI_DETAIL 17
#ifdef BB_MBC3
#define BB_RAM_BANKS 4
#else
#define BB_RAM_BANKS 8
#endif
uint8_t bb_exit(void) NONBANKED;
void platform_run(void) BANKED;
void link_run(void) BANKED;
void audio_run(void) BANKED;
void buttons_run(void) BANKED;
void display_run(void) BANKED;
void flicker_run(void) BANKED;
void sram_run(void) BANKED;
void burn_run(void) BANKED;
char *ui_decimal(char *out,uint32_t n);
uint8_t ui_number(uint8_t x,uint8_t y,uint32_t n);
void ui_pad(uint8_t x,uint8_t y,const char *s,uint8_t width);
void ui_count(uint8_t x,uint8_t y,uint32_t n,uint8_t width);
void ui_line(uint8_t y,const char *text);
void ui_screen(const char *title,const char *page);
void ui_frame(uint8_t bottom,const char *title,const char *page);
void ui_field(uint8_t row,const char *label,const char *value,uint8_t selected);
void ui_value(uint8_t row,const char *label,uint32_t value,uint8_t selected);
void ui_status(const char *text);
void ui_corner(const char *text);
uint8_t ui_confirm(const char *message);
uint8_t ui_presets(const char *title,const char *const *names,const char *const *notes,uint8_t seen);
uint16_t bb_rom_crc(uint8_t bank,uint16_t offset,uint16_t count,uint16_t crc) NONBANKED;
void bb_cpu(uint8_t fast) NONBANKED;
uint16_t bb_frame(void) NONBANKED;
extern uint8_t bb_ram_bank,bb_rumble_bit;
void bb_rumble_start(uint8_t frames) NONBANKED;
void bb_rumble_stop(void) NONBANKED;
extern uint8_t selected_test,bb_keys,bb_fast;
extern const unsigned char bb_font[];
void ui_init(void);
void ui_clear(void);
void ui_text(uint8_t x,uint8_t y,const char *s);
void ui_box(uint8_t top,uint8_t bottom);
void ui_cell(uint8_t x,uint8_t y,uint8_t tile);
void ui_header(void);
extern uint16_t ui_revision;
/* Tiles ui_init must reload: every UI tile, or only the font slots the browser borrows. */
#define UI_TILES_BORROWED 1u
#define UI_TILES_ALL 2u
extern uint8_t bb_tiles_dirty;
/* Set when the window map (9C00) holds something other than the blank cover. */
extern uint8_t bb_cover_dirty,bb_header_dirty;
void ui_reveal(void) NONBANKED;
void ui_cover(void) NONBANKED;
uint8_t ui_page(const char *title,const char *page,uint8_t key);
void ui_hardware(uint8_t scene,uint8_t frame) BANKED;
void rtc_run(void) BANKED;
void rtc_read(uint8_t latch) BANKED;
void led_run(void) BANKED;
void ir_run(void) BANKED;
void rumble_view(void) BANKED;
void rumble_ui_reset(void) BANKED;
void ui_scene(uint8_t scene,uint8_t frame) BANKED;
void ui_scene_reset(void) BANKED;
void ui_scene_border(uint8_t item) BANKED;
void ui_focus(uint8_t item,uint8_t fresh) BANKED;
void ui_scene_redraw(void) BANKED;
#endif
