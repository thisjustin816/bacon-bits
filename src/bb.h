#ifndef BB_H
#define BB_H
#include <gb/gb.h>
#include <gb/cgb.h>
uint8_t bb_exit(void) NONBANKED;
void platform_run(void) BANKED;
void link_run(void) BANKED;
void audio_run(void) BANKED;
extern uint8_t selected_test;
void ui_init(void);
void ui_clear(void);
void ui_text(uint8_t x,uint8_t y,const char *s);
void ui_box(uint8_t top,uint8_t bottom);
void ui_cell(uint8_t x,uint8_t y,uint8_t tile);
void ui_header(void);
#endif
