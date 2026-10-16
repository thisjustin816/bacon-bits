#pragma bank 3
#include "bb.h"
uint16_t ir_edges,ir_active_frames,ir_bursts;
uint8_t ir_mode,ir_on=10,ir_off=18,ir_pulses=32,ir_period=30,ir_running;
static uint8_t seen,last_page=255;
static const char *const presets[]={"","Receive","Short bursts","Slow beacon","Dense bursts"};
static const char *const notes[]={"Keep settings","Watch input only","32 pulses / 500 ms","32 pulses / 2 sec","64 pulses / 250 ms"};
/* Normal-speed timings: ON=(ticks+1)*16 cycles, OFF=(ticks+2)*16.
   No renderer, VBlank handler or C loop runs between the two RP edges. */
void ir_burst(void) BANKED __naked {
 __asm
  push bc
  push de
  ld a,(_ir_pulses)
  ld b,a
  ld a,(_ir_on)
  ld d,a
  ld a,(_ir_off)
  ld e,a
  ld c,#0x56
  di
  001$:
  ld a,#0xc1
  ldh (c),a
  ld a,d
  002$:
  dec a
  jr nz,002$
  ld a,#0xc0
  ldh (c),a
  ld a,e
  003$:
  dec a
  jr nz,003$
  dec b
  jr nz,001$
  ei
  pop de
  pop bc
  ret
 __endasm;
}
static void view(uint8_t detail,uint8_t row){if(last_page!=detail){ui_screen("Infrared",detail?"Set":"");last_page=detail;}
 if(detail){ui_value(0,"On us",((uint16_t)ir_on+1u)*3815UL/1000UL,row==0);ui_value(1,"Off us",((uint16_t)ir_off+2u)*3815UL/1000UL,row==1);ui_value(2,"Pulses",ir_pulses,row==2);ui_value(3,"Every fr",ir_period,row==3);}
 else {ui_hardware(1,(ir_mode?ir_bursts:ir_edges)&3u);ui_text(2,6,ir_mode?"Transmit":"Receive");ui_text(11,10,ir_mode?"Bursts":"Edges");ui_number(11,12,ir_mode?ir_bursts:ir_edges);}
 ui_status(ir_running?(ir_mode?"Sending bursts":"Listening"):"Idle");}
void ir_run(void) BANKED {
 last_page=255;
 uint8_t preset,key,old=0,n,detail=0,row=0,prior=0,signal,lit,was_fast;uint16_t frame=0,since=0;
 if(_cpu!=CGB_TYPE || _is_GBA){ui_screen("Infrared","");ui_text(2,8,"No CGB IR port");while(joypad())vsync();while(!(joypad()&J_B))vsync();while(joypad())vsync();return;}
 preset=ui_presets("IR presets",presets,notes,seen);if(preset==255)return;seen=1;
 if(preset){ir_mode=preset!=1;ir_on=2;ir_off=3;ir_pulses=preset==4?64:32;ir_period=preset==3?120:preset==4?15:30;}
 was_fast=KEY1_REG>>7;bb_cpu(0);ir_running=0;ir_edges=ir_active_frames=ir_bursts=0;RP_REG=0;view(detail,row);
 for(;;){if(!ir_running)vsync();key=joypad();n=key&~old;old=key;
  if(n&J_B)break;
  if(n&J_SELECT){detail^=1;row=0;view(detail,row);}
  if(detail){if(n&J_UP)row=(row+3u)&3u;if(n&J_DOWN)row=(row+1u)&3u;
   if(n&(J_LEFT|J_RIGHT)){uint8_t *v=row==0?&ir_on:row==1?&ir_off:row==2?&ir_pulses:&ir_period;
    if(n&J_RIGHT){if(*v<(row<2?32:row==2?64:240))++*v;}else if(*v>1)--*v;
   }
  }else if(n&(J_LEFT|J_RIGHT))ir_mode^=1;
  if(n&J_A){ir_running^=1;RP_REG=ir_running?0xc0:0;since=bb_frame();prior=0;}
  if(ir_running){
   if(ir_mode && (uint16_t)(bb_frame()-since)>=ir_period){since=bb_frame();ir_burst();if(ir_bursts<65535)++ir_bursts;}
   frame=bb_frame();lit=0;
   /* Poll across the frame; one VBlank sample would miss short incoming bursts. */
   while(bb_frame()==frame){signal=!(RP_REG&2u);if(signal && !prior){if(ir_edges<65535)++ir_edges;}prior=signal;lit|=signal;}
   if(lit && ir_active_frames<65535)++ir_active_frames;
  }
  if(n || (ir_running && !(bb_frame()&15u)))view(detail,row);
 }
 RP_REG=0;ir_running=0;bb_cpu(was_fast);
}
