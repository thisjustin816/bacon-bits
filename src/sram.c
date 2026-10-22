#pragma bank 5
#include "sram.h"
uint8_t ram_mode,ram_banks=BB_RAM_BANKS,ram_pattern=6,ram_stage,ram_bank,ram_want,ram_got,ram_first_bank,ram_valid;
uint16_t ram_seed=1,ram_address,ram_first_address,ram_generation;
uint32_t ram_errors,ram_checked;
static uint8_t record[16],writing,completed,seen,limit,ram_delay;
static const char *const presets[]={"","Power cycle","Bank check","Bit patterns","Retention"};
static const char *const notes[]={"Keep settings","Read saved record","32k bank address","Walking bits / 10x","Random / 30s wait"};
static const char *const patterns[]={"Zero","Ones","55","AA","Walk 1","Walk 0","Address","Random"};
static uint8_t rd(uint16_t address) __naked {address;__asm ld a,(de)
 ret __endasm;}
static void bank(uint8_t n){bb_ram_bank=n;*(volatile uint8_t *)0x4000=n|bb_rumble_bit;}
static uint8_t value(uint8_t b,uint16_t a){uint16_t x;
 /* Bank tags remain distinct even for constant data patterns. */
 if(a<16)return (uint8_t)(0x39u+b*23u+a*7u);
 switch(ram_pattern){case 0:return 0;case 1:return 255;case 2:return 0x55;case 3:return 0xaa;
 case 4:return 1u<<(a&7);case 5:return ~(1u<<(a&7));case 6:return (uint8_t)(a^(a>>8)^b);
 default:x=a^(ram_seed+b*257u);x^=x<<7;x^=x>>9;x^=x<<8;return (uint8_t)x;}}
static uint8_t checksum(void){uint8_t i,c=0x71;for(i=0;i<15;++i)c=(c<<1 | c>>7)^record[i];return c;}
static uint8_t load(void){uint8_t i;bank(0);for(i=0;i<16;++i)record[i]=rd(0xbfe0+i);
 ram_valid=record[0]=='B' && record[1]=='B' && record[2]==1 && record[3]>=1 && record[3]<=BB_RAM_BANKS && record[4]<8 && record[15]==checksum();
 if(ram_valid){ram_banks=record[3];ram_pattern=record[4];ram_seed=record[5]|((uint16_t)record[6]<<8);ram_generation=record[7]|((uint16_t)record[8]<<8);}return ram_valid;}
static void commit(void){uint8_t i;bank(0);++ram_generation;record[0]='B';record[1]='B';record[2]=1;record[3]=ram_banks;record[4]=ram_pattern;record[5]=ram_seed;record[6]=ram_seed>>8;record[7]=ram_generation;record[8]=ram_generation>>8;for(i=9;i<15;++i)record[i]=0;record[15]=checksum();
 for(i=1;i<16;++i)*(volatile uint8_t *)(0xbfe0u+i)=record[i];*(volatile uint8_t *)0xbfe0='B';ram_valid=1;}
uint8_t sram_begin(uint8_t write) BANKED {*(volatile uint8_t *)0x0000=0x0a;writing=write;completed=0;ram_errors=ram_checked=0;ram_stage=0;ram_bank=0;ram_address=0;
 if(!write && !load()){sram_end();return 0;}
 if(write){bank(0);*(volatile uint8_t *)0xbfe0=0;ram_valid=0;}
 ram_stage=write?1:2;return 1;}
uint8_t sram_step(void) BANKED {uint16_t end,n;uint8_t want,got;
 if(!ram_stage)return 1;bank(ram_bank);end=ram_bank?8192:8160;
 for(n=0;n<128 && ram_address<end;++n,++ram_address){want=value(ram_bank,ram_address);
  if(ram_stage==1)*(volatile uint8_t *)(0xa000u+ram_address)=want;
  else {got=rd(0xa000u+ram_address);++ram_checked;if(got!=want){if(!ram_errors){ram_first_bank=ram_bank;ram_first_address=ram_address;ram_want=want;ram_got=got;}++ram_errors;}}}
 if(ram_address==end){ram_address=0;if(++ram_bank==ram_banks){ram_bank=0;if(ram_stage==1)ram_stage=2;else {if(writing && !ram_errors)commit();completed=1;sram_end();return 1;}}}return 0;
}
void sram_end(void) BANKED {ram_stage=0;bank(0);*(volatile uint8_t *)0x0000=0;}
static void result(uint8_t page,uint32_t passes){ui_screen("SRAM result",page==0?"1/3":page==1?"2/3":"3/3");if(!page){ui_field(0,"Result",ram_errors?"Fail":!completed?(ram_valid?"Stopped":"Unknown"):"Pass",0);ui_value(1,"Errors",ram_errors,0);ui_value(2,"Bytes",ram_checked,0);ui_value(3,"Passes",passes,0);}else if(page==1){ui_value(0,"Bank",ram_first_bank,0);ui_value(1,"Offset",ram_first_address,0);ui_value(2,"Expected",ram_want,0);ui_value(3,"Read",ram_got,0);}else{ui_value(0,"Record",ram_generation,0);ui_value(1,"Banks",ram_banks,0);ui_field(2,"Pattern",patterns[ram_pattern],0);ui_value(3,"Seed",ram_seed,0);}ui_status(page==1?"First failure":page==2?"Saved config":"Pattern results");}

void sram_run(void) BANKED {uint8_t key,old=0,n,sel=0,page=0,active=0,done=0,redraw=1;uint16_t since=0,last_draw=0;uint32_t passes=0,progress;
 {uint8_t preset=ui_presets("SRAM presets",presets,notes,seen);if(preset==255)return;seen=1;
 if(preset){ram_banks=BB_RAM_BANKS;ram_seed=1;ram_pattern=6;limit=ram_delay=0;ram_mode=preset==1?0:1;
 if(preset==2)ram_banks=4;
 if(preset==3){ram_mode=2;ram_pattern=4;limit=1;}if(preset==4){ram_pattern=7;ram_delay=30;limit=2;}}}
 for(;;){if(!active && !done && redraw){redraw=0;ui_page("SRAM",page?"2/2":"1/2",0x60u|page);if(!page){ui_field(0,"Mode",ram_mode==0?"Verify":ram_mode==1?"Write":"Cycle",sel==0);ui_value(1,"Banks",ram_banks,sel==1);ui_field(2,"Pattern",patterns[ram_pattern],sel==2);ui_field(3,"Passes",limit==0?"1":limit==1?"10":limit==2?"100":"Loop",sel==3);}else{ui_value(0,"Seed",ram_seed,sel==0);ui_value(1,"Delay s",ram_delay,sel==1);ui_field(2,"Tags","16/bank",0);ui_field(3,"Record","32 B",0);}ui_status(ram_mode?"Erases test SRAM":"Read only");}
 vsync();key=joypad();n=key&~old;old=key;
 if(active){if(n&J_B){sram_end();active=0;done=1;result(page,passes);continue;}
  if(ram_stage){if(sram_step()){++passes;since=bb_frame();}}
  else if((uint16_t)(bb_frame()-since)>=(uint16_t)ram_delay*60u){if(ram_errors || (limit<3 && passes>=(limit==0?1UL:limit==1?10UL:100UL))){active=0;done=1;result(page,passes);}else sram_begin(ram_mode==2);}
  if(active && (uint16_t)(bb_frame()-last_draw)>=16u){
   last_draw=bb_frame();
   ui_hardware(3,0);ui_pad(10,6,ram_stage==1?"Write":ram_stage==2?"Verify":"Pause",8);
   {uint8_t i;for(i=0;i<ram_banks;++i)ui_cell(1+i,7,ram_errors && ram_first_bank==i?UI_FAIL:ram_bank==i?UI_ACTIVE:ram_bank>i?UI_PASS:UI_EMPTY);}
   ui_pad(10,8,"Bank",5);ui_count(15,8,ram_bank,3);
   ui_pad(10,10,"Errors",8);ui_count(10,12,ram_errors,8);
   progress=ram_stage==1?(uint32_t)ram_bank*8192u+ram_address-(ram_bank?32u:0u):ram_checked;ui_cell(0,15,0);ui_count(1,15,progress,9);ui_pad(10,15,ram_stage==1?"Written":"Verified",10);
   ui_status(ram_stage==1?"Writing pattern":ram_stage==2?"Verifying data":"Waiting");
  }continue;
 }
 if(done){if(n&J_B){done=0;page=0;redraw=1;}if(n&J_SELECT){page=(page+1)%3;result(page,passes);}continue;}
 if(n)redraw=1;
 if(n&J_B)return;if(n&J_SELECT){page^=1;sel=0;}if(n&J_UP)sel=(sel+(page?1u:3u))%(page?2u:4u);if(n&J_DOWN)sel=(sel+1u)%(page?2u:4u);
 if(n&(J_LEFT|J_RIGHT)){uint8_t inc=(n&J_RIGHT)?1:255;if(!page){if(!sel)ram_mode=(ram_mode+((inc==1)?1:2))%3;else if(sel==1){if(inc==1 && ram_banks<BB_RAM_BANKS)ram_banks*=2;if(inc!=1 && ram_banks>1)ram_banks/=2;}else if(sel==2)ram_pattern=(ram_pattern+inc)&7;else limit=(limit+inc)&3;}else {if(!sel)ram_seed+=inc==1?1:-1;else if(sel==1){if(inc==1 && ram_delay<30)++ram_delay;if(inc!=1 && ram_delay)--ram_delay;}}}
 if(n&J_A){uint8_t ok=ram_mode?ui_confirm("Erase test SRAM?"):1;old=0;if(ok){passes=0;page=0;ui_screen("SRAM run","");if(sram_begin(ram_mode!=0)){active=1;last_draw=bb_frame()-16u;}else {done=1;result(0,0);}}}
 }
}
