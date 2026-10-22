#pragma bank 7
#include "bb.h"
#include "tones.h"
#include "sram.h"
extern const uint16_t burn_expected[8];
#ifdef BB_MBC3
extern uint8_t rtc_valid,rtc_data[5];
#endif
uint32_t burn_seconds,burn_cycles,burn_errors;
uint16_t burn_first_expected,burn_first_read,burn_first_offset;
uint8_t burn_first_kind,burn_first_bank,burn_running,burn_bank,burn_ram_status;
static uint8_t scratch[256];
static uint16_t expected[8],crc,offset;
static uint8_t duration=1,load=1,fast,onfail,output,motor,ram_check;
static uint8_t seen;
static const char *const presets[]={"","Quick check","Long soak","Output load","SRAM watch"};
static const char *const notes[]={"Keep settings","1 min / medium","30 min / high load",
#ifdef BB_MBC3
 "Audio + RTC"
#else
 "Audio + rumble"
#endif
,"Read only SRAM"};
static const uint8_t minutes[]={1,5,10,30,60,0};
static void fail(uint8_t kind,uint8_t b,uint16_t a,uint16_t want,uint16_t got){if(!burn_errors){burn_first_kind=kind;burn_first_bank=b;burn_first_offset=a;burn_first_expected=want;burn_first_read=got;}++burn_errors;}
static void outputs_off(void){burn_audio(255);
#ifndef BB_MBC3
 bb_rumble_stop();
#endif
 bb_cpu(0);}
static void settings(uint8_t page,uint8_t row){ui_page("Burn in",page?"2/2":"1/2",0x70u|page);if(!page){if(minutes[duration])ui_value(0,"Minutes",minutes[duration],row==0);else ui_field(0,"Minutes","Loop",row==0);ui_field(1,"Load",load==0?"Light":load==1?"Medium":"High",row==1);ui_field(2,"CPU",fast?"Double":"Normal",row==2);ui_field(3,"On fail",onfail?"Continue":"Stop",row==3);}else{ui_field(0,"Audio",output==0?"Off":output==1?"Pulse":output==2?"Wave":"Noise",row==0);
#ifdef BB_MBC3
ui_field(1,"RTC",motor?"Watch":"Skip",row==1);
#else
ui_value(1,"Rumble f",motor,row==1);
#endif
ui_field(2,"SRAM",ram_check?"Verify":"Skip",row==2);ui_field(3,"Scratch","256 B",0);}ui_status("Ready");}
static void status_body(uint8_t page){if(!page){uint8_t i;
 ui_hardware(2,(uint8_t)burn_seconds&3u);
 ui_pad(10,6,"Seconds",9);ui_count(10,7,burn_seconds,9);ui_pad(10,9,"Cycles",9);ui_count(10,10,burn_cycles,9);ui_pad(10,12,"Errors",9);ui_count(10,13,burn_errors,9);
 for(i=0;i<8;++i)ui_cell(2+i*2u,14,burn_first_kind==1 && burn_first_bank==i?UI_FAIL:burn_bank==i?UI_PASS:UI_EMPTY);
}else{if(burn_first_kind==4){ui_value(0,"RTC reg",burn_first_offset,0);ui_value(1,"Maximum",burn_first_expected,0);ui_value(2,"Read",burn_first_read,0);ui_value(3,"Errors",burn_errors,0);}
 else if(!burn_first_kind){ui_field(0,"Result","No error",0);ui_value(1,"Cycles",burn_cycles,0);ui_value(2,"Seconds",burn_seconds,0);ui_field(3,"Scratch","Pass",0);}
 else {if(burn_first_kind==2)ui_field(0,"Area","Scratch",0);else ui_value(0,"Bank",burn_first_bank,0);
 if(burn_first_kind==1)ui_field(1,"Scope","16K bank",0);else ui_value(1,"Offset",burn_first_offset,0);
 ui_value(2,"Expected",burn_first_expected,0);ui_value(3,"Read",burn_first_read,0);}}ui_line(15,burn_ram_status==4?"SRAM no record":burn_ram_status==3?"SRAM fail":burn_ram_status==2?"SRAM checked":burn_ram_status==1?"SRAM verify":"SRAM skipped");ui_status(burn_running?"Running":"Stopped");}
static void status(uint8_t page){ui_screen(page?(burn_first_kind==1?"ROM failure":burn_first_kind==2?"Scratch failure":burn_first_kind==3?"SRAM failure":burn_first_kind==4?"RTC failure":"No failure"):(burn_running?"Burn run":"Burn stop"),page?"2/2":"1/2");status_body(page);}
void burn_run(void) BANKED {uint8_t row=0,page=0,key,old=0,n,finished=0,i,pattern=0,ram_active=0,draw_wait=0;uint16_t last=0,delta,chunk,a,now;uint32_t phase=0;
#ifdef BB_MBC3
 uint8_t rtc_wait=0;
#endif
 {uint8_t preset=ui_presets("Burn in presets",presets,notes,seen);if(preset==255)return;seen=1;
 if(preset){duration=0;load=1;fast=onfail=output=motor=ram_check=0;
 if(preset==2){duration=3;load=2;fast=(_cpu==CGB_TYPE);}if(preset==3){duration=1;load=2;output=1;motor=1;page=1;}if(preset==4){duration=2;ram_check=1;}}}
 burn_running=0;settings(page,row);
 for(;;){vsync();key=joypad();n=key&~old;old=key;
 if(burn_running){now=bb_frame();delta=now-last;last=now;phase+=(uint32_t)delta*70224UL;while(phase>=4194304UL){phase-=4194304UL;++burn_seconds;}
  chunk=load==0?32:load==1?128:256;crc=bb_rom_crc(burn_bank,offset,chunk,crc);offset+=chunk;
  if(offset==16384){if(crc!=expected[burn_bank])fail(1,burn_bank,0,expected[burn_bank],crc);crc=0xffff;offset=0;if(++burn_bank==8){burn_bank=0;++burn_cycles;}}
  for(a=0;a<256;++a)scratch[a]=(uint8_t)a^pattern;
  for(a=0;a<256;++a){uint8_t got=*(volatile uint8_t *)&scratch[a];if(got!=((uint8_t)a^pattern))fail(2,0,a,(uint8_t)a^pattern,got);}++pattern;
  if(ram_active && sram_step()){ram_active=0;burn_ram_status=ram_errors?3:2;if(ram_errors)fail(3,ram_first_bank,ram_first_address,ram_want,ram_got);}
  if(ram_check && !ram_active && !offset && !burn_bank)ram_active=sram_begin(0);
#ifdef BB_MBC3
  /* One load cycle spans several frames, so count frames rather than
     waiting for an exact frame number the loop may never observe. */
  rtc_wait+=delta;
  if(motor && rtc_wait>=64u){rtc_wait=0;rtc_read(1);if(ram_active)*(volatile uint8_t *)0x0000=0x0a;if(!rtc_valid)for(i=0;i<3;++i)if(rtc_data[i]>(i<2?59:23)){fail(4,0,8u+i,i<2?59:23,rtc_data[i]);break;}}
#endif
  if((n&J_B) || (burn_errors && !onfail) || (minutes[duration] && burn_seconds>=(uint32_t)minutes[duration]*60UL)){burn_running=0;finished=1;if(ram_active)sram_end();outputs_off();status(page);}
  else if(n&J_SELECT){page^=1;status(page);}
  else if((draw_wait+=delta)>=32u){draw_wait=0;status_body(page);}
  continue;
 }
 if(finished){if(n&J_B)return;if(n&J_SELECT){page^=1;status(page);}if(n&J_START){finished=0;settings(page,row);}continue;}
 if(n&J_B)return;if(n&J_SELECT){page^=1;row=0;}if(n&J_UP)row=(row+(page?2u:3u))%(page?3u:4u);if(n&J_DOWN)row=(row+1u)%(page?3u:4u);
 if(n&(J_LEFT|J_RIGHT)){uint8_t add=(n&J_RIGHT)?1:255;if(!page){if(!row)duration=(duration+((add==1)?1:5))%6;else if(row==1)load=(load+((add==1)?1:2))%3;else if(row==2 && _cpu==CGB_TYPE)fast^=1;else if(row==3)onfail^=1;}else {if(!row)output=(output+add)&3;else if(row==1){
#ifdef BB_MBC3
motor^=1;
#else
if(add==1 && motor<6)++motor;if(add!=1 && motor)--motor;
#endif
}else if(row==2)ram_check^=1;}}
 if(n&J_A){for(i=0;i<8;++i)expected[i]=burn_expected[i];burn_seconds=burn_cycles=burn_errors=phase=0;burn_first_kind=burn_first_bank=burn_first_expected=burn_first_read=burn_first_offset=0;burn_bank=0;offset=0;crc=0xffff;last=bb_frame();burn_running=1;if(output)burn_audio(output==1?0:output==2?2:3);
#ifndef BB_MBC3
 if(motor)bb_rumble_start(motor);
#endif
 bb_cpu(fast);ram_active=ram_check?sram_begin(0):0;burn_ram_status=ram_check?(ram_active?1:4):0;page=0;status(page);}else if(n)settings(page,row);
 }
}
