#ifndef SRAM_TEST_H
#define SRAM_TEST_H
#include "bb.h"
extern uint8_t ram_mode,ram_banks,ram_pattern,ram_stage,ram_bank,ram_want,ram_got,ram_first_bank,ram_valid;
extern uint16_t ram_seed,ram_address,ram_first_address,ram_generation;
extern uint32_t ram_errors,ram_checked;
uint8_t sram_begin(uint8_t write) BANKED;
uint8_t sram_step(void) BANKED;
void sram_end(void) BANKED;
#endif
