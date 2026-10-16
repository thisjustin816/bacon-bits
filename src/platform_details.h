#ifndef PLATFORM_DETAILS_H
#define PLATFORM_DETAILS_H
#include "bb.h"
extern uint8_t pd_obs[12][4],pd_before,pd_oam[4],pd_cgb;
extern uint16_t pd_mask;
extern char pd_name[12];
void pd_show(void) BANKED;
void pd_restore(void) BANKED;
#endif
