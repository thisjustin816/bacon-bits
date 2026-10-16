#ifndef PLATFORM_DETAILS_H
#define PLATFORM_DETAILS_H
#include "bb.h"
extern uint8_t pd_obs[12][4],pd_before,pd_oam[4],pd_cgb;
extern uint16_t pd_mask;
extern char pd_name[12];
extern uint8_t pd_likely;
extern char pd_hardware[10];
void pd_summary(void) BANKED;
void pd_show(void) BANKED;
#endif
