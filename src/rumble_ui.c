#pragma bank 5
#include "bb.h"
#include <string.h>
#define R ((volatile uint8_t *)0xc000u)
static uint8_t rumble_ready,rumble_last_page=255;
static uint8_t trace[768];
static const uint8_t visible_offsets[]={0,1,2,3,4,5,17,24,25,26,28,30,31,32};
static uint8_t previous_view[14];
static const char *const modes[]={"Pattern","On sweep","Off sweep","Preset"};
#include <rumble_presets.h>
static void waveform(void) {
 uint8_t x,y,i,high,last=0;uint16_t at;
 memset(trace,0,sizeof(trace));
 for(x=0;x<128;++x){high=(R[3]==1)?(x<(uint16_t)R[5]*4u):(R[3]==2)?(x>=R[5]*4u):((R[0]>>(x>>4))&1u);
  y=high?4:16;at=((uint16_t)(y>>3)*16u+(x>>3))*16u+(y&7u)*2u;trace[at+1]|=0x80u>>(x&7u);
  if(x && high!=last)for(i=4;i<=16;++i){at=((uint16_t)(i>>3)*16u+(x>>3))*16u+(i&7u)*2u;trace[at+1]|=0x80u>>(x&7u);}last=high;
  /* In the pattern editor, underline the bit Left/Right selects. */
  if(R[3]==0 && (x>>4)==R[1] && (x&15u)>=2u && (x&15u)<14u)for(i=20;i<22;++i){at=((uint16_t)(i>>3)*16u+(x>>3))*16u+(i&7u)*2u;trace[at+1]|=0x80u>>(x&7u);}
 }
 fill_bkg_rect(2,11,16,3,0);set_bkg_data(160,48,trace);for(y=0;y<3;++y)for(x=0;x<16;++x)ui_cell(2+x,11+y,160+y*16+x);
}
void rumble_ui_reset(void) BANKED {rumble_ready=0;rumble_last_page=255;}
void rumble_view(void) BANKED {
 uint8_t detail=!!(R[7]&4u),width,i,changed=0,fresh,trace_changed;char s[12],*end;uint32_t nominal_ms;
 fresh=!rumble_ready || detail!=rumble_last_page;
 for(i=0;i<14;++i)if(previous_view[i]!=R[visible_offsets[i]])changed=1;
 if(!fresh && !changed)return;
 trace_changed=fresh || previous_view[0]!=R[0] || previous_view[1]!=R[1] || previous_view[3]!=R[3] || previous_view[5]!=R[5];
 for(i=0;i<14;++i)previous_view[i]=R[visible_offsets[i]];
 if(fresh){ui_screen("Rumble",detail?"2/2":"1/2");rumble_ready=1;rumble_last_page=detail;}
 if(detail){
  ui_value(0,R[24]?"Bit ms":"Bit fr",R[24]?R[2]:R[25],0);ui_field(1,"Prespin",R[4]?"On":"Off",0);
  if(R[26])ui_value(2,"Run bits",R[26],0);else ui_field(2,"Run bits","Hold",0);
  ui_value(3,"Gap bits",R[28],0);
 }else{
  ui_scene(3,R[17]?1:0);
  fill_bkg_rect(9,7,10,3,0);ui_text(9,7,modes[R[3]]);
  if(R[3]==3)ui_text(8,9,names[R[30]]);
  else if(R[3]==1 || R[3]==2){end=ui_decimal(s,R[5]);*end++=' ';*end++='b';*end++='i';*end++='t';if(R[5]!=1)*end++='s';*end=0;ui_text(10,9,s);}
  else {end=ui_decimal(s,R[24]?R[2]:R[25]);*end++=' ';*end++=R[24]?'m':'f';*end++=R[24]?'s':'r';*end=0;ui_text(10,9,s);}
  width=(R[3]==1 || R[3]==2)?R[5]:8;
  nominal_ms=R[24]?(uint16_t)width*R[2]:((uint32_t)width*R[25]*16742UL+500u)/1000u;
  end=ui_decimal(s,nominal_ms);*end++=' ';*end++='m';*end++='s';*end=0;ui_pad(10,10,s,9);
  if(trace_changed)waveform();
  fill_bkg_rect(0,15,20,1,0);
  if(R[3]==1 || R[3]==2){ui_text(1,15,"Felt at");if(R[31+(R[3]==2)])ui_number(12,15,R[31+(R[3]==2)]);else ui_text(12,15,"None");}
 }
 ui_status(R[17]?"Running":detail?"Timing settings":"Stopped");
}
