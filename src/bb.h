#ifndef BB_H
#define BB_H
#include <gb/gb.h>
#include <gb/cgb.h>
uint8_t bb_exit(void) NONBANKED;
void platform_run(void) BANKED;
void link_run(void) BANKED;
void audio_run(void) BANKED;
void buttons_run(void) BANKED;
void display_run(void) BANKED;
void sram_run(void) BANKED;
void burn_run(void) BANKED;
char *ui_decimal(char *out,uint32_t n);
void ui_number(uint8_t x,uint8_t y,uint32_t n);
void ui_screen(const char *title,const char *page);
void ui_field(uint8_t row,const char *label,const char *value,uint8_t selected);
void ui_value(uint8_t row,const char *label,uint32_t value,uint8_t selected);
void ui_status(const char *text);
uint8_t ui_confirm(const char *message);
uint8_t ui_presets(const char *title,const char *const *names,const char *const *notes,uint8_t seen);
uint16_t bb_rom_crc(uint8_t bank,uint16_t offset,uint16_t count,uint16_t crc) NONBANKED;
void bb_cpu(uint8_t fast) NONBANKED;
uint16_t bb_frame(void) NONBANKED;
extern uint8_t selected_test,bb_keys,bb_fast;
extern const unsigned char bb_font[];
void ui_init(void);
void ui_clear(void);
void ui_text(uint8_t x,uint8_t y,const char *s);
void ui_box(uint8_t top,uint8_t bottom);
void ui_cell(uint8_t x,uint8_t y,uint8_t tile);
void ui_header(void);
#endif
