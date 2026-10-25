#pragma bank 3
#include "bb.h"
uint16_t ir_edges,ir_bursts;
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
/* Counts rising edges of received light into ir_seen, with interrupts off
   so the VBlank handler cannot leave a gap. It returns once VBlank is due
   and the port has held still for 64 samples, so a burst is never split,
   and VBlank runs as it returns. Samples are 40 cycles apart, 44 at a rise
   and 56 at a fall, so every preset's 48-cycle pulse and 80-cycle gap is
   seen. More than 2,048 rises in one call ends it, in case the light never
   stops changing. It needs the LCD on, since it waits for VBlank. */
uint16_t ir_seen;
static uint8_t ir_level=2;
void ir_listen(void) BANKED __naked {
 __asm
  push bc
  push de
  push hl
  ld c,#0x56
  ld de,#0
  ld l,#64
  di
  ld a,(_ir_level)
  or a
  jr z,004$
  001$:
  ldh a,(c)
  and #2
  jr z,003$
  dec l
  jr nz,001$
  ldh a,(_IF_REG)
  rrca
  ldh a,(c)
  jr c,002$
  ld l,#64
  and #2
  jr z,003$
  jr 001$
  002$:
  and #2
  jr nz,006$
  003$:
  inc de
  ld l,#64
  004$:
  ldh a,(c)
  and #2
  jr nz,005$
  dec l
  jr nz,004$
  ldh a,(_IF_REG)
  rrca
  jr c,007$
  ld l,#64
  jr 004$
  005$:
  ld l,#64
  bit 3,d
  jr z,001$
  006$:
  ld a,#2
  jr 008$
  007$:
  xor a
  008$:
  ld (_ir_level),a
  ld hl,#_ir_seen
  ld (hl),e
  inc hl
  ld (hl),d
  ei
  pop hl
  pop de
  pop bc
  ret
 __endasm;
}
static void view(uint8_t detail,uint8_t row){if(last_page!=detail){ui_screen("Infrared",detail?"Set":"");last_page=detail;}
 if(detail){ui_value(0,"On us",((uint16_t)ir_on+1u)*3815UL/1000UL,row==0);ui_value(1,"Off us",((uint16_t)ir_off+2u)*3815UL/1000UL,row==1);ui_value(2,"Pulses",ir_pulses,row==2);ui_value(3,"Every fr",ir_period,row==3);}
 else {ui_hardware(1,(ir_mode?ir_bursts:ir_edges)&3u);ui_pad(11,7,ir_mode?"Transmit":"Receive",8);ui_pad(11,10,ir_mode?"Bursts":"Edges",8);ui_count(11,12,ir_mode?ir_bursts:ir_edges,8);}
 ui_status(ir_running?(ir_mode?"Sending bursts":"Listening"):"Idle");}
void ir_run(void) BANKED {
 last_page=255;
 uint8_t preset,key,old=0,n,detail=0,row=0,was_fast;uint16_t since=0,shown=0;
 if(_cpu!=CGB_TYPE || _is_GBA){ui_screen("Infrared","");ui_text(2,8,"No CGB IR port");while(joypad())vsync();while(!(joypad()&J_B))vsync();while(joypad())vsync();return;}
 preset=ui_presets("Infrared presets",presets,notes,seen);if(preset==255)return;seen=1;
 if(preset){ir_mode=preset!=1;ir_on=2;ir_off=3;ir_pulses=preset==4?64:32;ir_period=preset==3?120:preset==4?15:30;}
 was_fast=KEY1_REG>>7;bb_cpu(0);ir_running=0;ir_edges=ir_bursts=0;RP_REG=0;view(detail,row);
 for(;;){if(!ir_running)vsync();key=joypad();n=key&~old;old=key;
  if(n&J_B)break;
  if(n&J_SELECT){detail^=1;row=0;view(detail,row);}
  if(detail){if(n&J_UP)row=(row+3u)&3u;if(n&J_DOWN)row=(row+1u)&3u;
   if(n&(J_LEFT|J_RIGHT)){uint8_t *v=row==0?&ir_on:row==1?&ir_off:row==2?&ir_pulses:&ir_period;
    if(n&J_RIGHT){if(*v<(row<2?32:row==2?64:240))++*v;}else if(*v>1)--*v;
   }
  }else if(n&(J_LEFT|J_RIGHT))ir_mode^=1;
  if(n&J_A){ir_running^=1;RP_REG=ir_running?0xc0:0;since=bb_frame();ir_level=2;}
  if(ir_running){
   if(ir_mode && (uint16_t)(bb_frame()-since)>=ir_period){since=bb_frame();ir_burst();if(ir_bursts<65535)++ir_bursts;}
   ir_listen();ir_edges=ir_seen>65535u-ir_edges?65535u:ir_edges+ir_seen;
  }
  /* Redraw only for a new count: a redraw keeps the receiver off the port
     for up to two frames, and after a burst the next is usually far off. */
  if(n || shown!=(ir_mode?ir_bursts:ir_edges)){view(detail,row);shown=ir_mode?ir_bursts:ir_edges;}
 }
 RP_REG=0;ir_running=0;bb_cpu(was_fast);
}
