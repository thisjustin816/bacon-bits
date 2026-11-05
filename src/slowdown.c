#pragma bank 1
#include "bb.h"
#include <string.h>

/* One burn iteration takes 28 cycles and a normal-speed frame 70,224, so
   2,508 iterations fill a frame exactly. */
#define FRAME_LOOPS 2508u
#define FRAME_CYCLES 70224UL
/* Cycles of each update that are not burn, from the VBlank that wakes the
   loop to its next wait (the interrupt, GBDK's handler, the readout and the
   loop's own work), and the cost of one VBlank that interrupts a burn.
   tests/slowdown.py measures both and holds them to these values. */
#define OVERHEAD_CYCLES 3374UL
#define INTERRUPT_CYCLES 2268UL

uint8_t slow_load=15,slow_pattern,slow_fast,slow_base=10,slow_heavy=4,slow_light=4,slow_steps=30;
uint8_t slow_running;
static uint8_t seen,saved_ie;

extern uint8_t slow_frames[3],slow_lag[3],slow_window,slow_window_count,slow_frame64,slow_run,slow_longest,slow_busy;
extern uint8_t slow_tick_lag[3],slow_keys,slow_update_x,slow_index,slow_left,slow_count,slow_reps[2];
extern uint16_t slow_last,slow_sched[60];
void slow_vbl(void);
uint8_t slow_update(void);

static const char *const presets[]={"","Under budget","Over budget","Pulse","Ramp"};
static const char *const notes[]={"Keep settings","Steady 75%","Steady 125%","4 at 125%, 4 at 50%","25% to 150%"};
static const char *const patterns[]={"Steady","Pulse","Ramp"};
static const char *const titles[]={"Steady run","Pulse run","Ramp run"};

/* Loops for a load of step x 5 percent, rounded to the nearest loop. */
static uint16_t loops(uint8_t step,uint8_t fast) {
 uint16_t n=(uint16_t)(((uint32_t)step*5u*FRAME_LOOPS+50u)/100u);
 if(fast)n<<=1;
 return n;
}
static char *percent(char *s,uint8_t step) {char *e=ui_decimal(s,step*5u);*e++='%';*e=0;return e;}
/* The busy share of an update at Load and the lag frames it should cost, as
   "Busy 130%: 1 in 2". */
static void prediction(char *s) {
 uint32_t frame=FRAME_CYCLES,busy;uint8_t lag=0;char *e;
 if(slow_fast)frame<<=1;
 busy=(uint32_t)loops(slow_load,slow_fast)*28u+OVERHEAD_CYCLES;
 while(busy+(uint32_t)lag*INTERRUPT_CYCLES>=frame*(lag+1u))++lag;
 strcpy(s,"Busy ");e=ui_decimal(s+5,(busy*100u+frame/2u)/frame);
 if(!lag){strcpy(e,"%: no lag");return;}
 strcpy(e,"%: ");e=ui_decimal(e+3,lag);strcpy(e," in ");ui_decimal(e+4,lag+1u);
}
static void settings(uint8_t page,uint8_t row) {
 char v[20],*e;
 ui_page("Slowdown",page?"2/2":"1/2",0xc0u|page);
 if(!page){
  percent(v,slow_load);ui_field(0,"Load",v,row==0);
  ui_field(1,"Pattern",patterns[slow_pattern],row==1);
  ui_field(2,"CPU",slow_fast?"Double":"Normal",row==2);
  if(slow_pattern)percent(v,slow_base);else strcpy(v,"-");
  ui_field(3,"Base",v,row==3);
  prediction(v);ui_line(UI_DETAIL,v);
 }else{
  e=ui_decimal(v,slow_heavy);strcpy(e," upd");ui_field(0,"Heavy",v,row==0);
  e=ui_decimal(v,slow_light);strcpy(e," upd");ui_field(1,"Light",v,row==1);
  ui_value(2,"Steps",slow_steps,row==2);
  ui_field(3,"Wait","VBlank",0);
  ui_line(UI_DETAIL,slow_pattern==1?"Pulse: Heavy, Light":slow_pattern==2?"Ramp: Base to Load":"Steady: Load only");
 }
 ui_status("Stopped");
}
static void digits(uint8_t x,uint8_t y,const uint8_t *bcd) {
 uint8_t i=3;
 while(i){--i;ui_cell(x++,y,16u+(bcd[i]>>4));ui_cell(x++,y,16u+(bcd[i]&15u));}
}
static uint32_t value(const uint8_t *bcd) {
 uint32_t n=0;uint8_t i=3;
 while(i){--i;n=n*100u+(bcd[i]>>4)*10u+(bcd[i]&15u);}
 return n;
}
static void running_screen(void) {
 char v[8];uint8_t x;
 percent(v,slow_load);ui_screen(titles[slow_pattern],v);
 ui_text(2,6,"VBlank");ui_text(2,8,"Update");
 for(x=9;x<18;++x){ui_cell(x,6,UI_CHROME+0);ui_cell(x,8,UI_CHROME+0);}
 ui_text(2,10,"Frames");ui_text(2,12,"Lag fr");
 digits(11,10,slow_frames);digits(11,12,slow_lag);
 ui_status(bb_fast?"Running x2":"Running");ui_corner("00/64");
 ui_line(UI_DETAIL,"Run   0  Max   0");
}
static void start(void) {
 uint8_t i,k;uint16_t load,base,span;
 memset(bb_shared,0,256);
 bb_cpu(slow_fast);
 running_screen();
 load=loops(slow_load,bb_fast);base=loops(slow_base,bb_fast);
 slow_reps[0]=slow_reps[1]=1;
 if(slow_pattern==0){slow_sched[0]=load;slow_count=1;}
 else if(slow_pattern==1){slow_sched[0]=load;slow_sched[1]=base;slow_count=2;slow_reps[0]=slow_heavy;slow_reps[1]=slow_light;}
 else{
  /* Step i of k runs Base + (Load - Base) * i / (k - 1) loops, rounded
     toward Base, so both ends run exactly. */
  k=slow_steps;span=load>base?load-base:base-load;
  for(i=0;i<k;++i){uint16_t d=(uint16_t)((uint32_t)span*i/(k-1u));slow_sched[i]=load>base?base+d:base-d;}
  slow_count=k;
 }
 slow_left=slow_reps[0];
 if(_cpu==CGB_TYPE){palette_color_t p[4]={RGB(31,30,27),RGB(31,24,6),RGB(23,9,7),RGB(8,5,4)};set_sprite_palette(0,1,p);}
 OBP0_REG=0xe4;SPRITES_8x8;
 for(i=0;i<2;++i){set_sprite_tile(i,UI_ACTIVE);set_sprite_prop(i,0);move_sprite(i,80,i?8u*8u+16u:6u*8u+16u);}
 SHOW_SPRITES;
 slow_keys=joypad();
 saved_ie=IE_REG;
 /* Counting starts at a VBlank, so the first wake is one frame later. */
 vsync();
 CRITICAL{slow_last=sys_time;add_VBL(slow_vbl);IE_REG=VBL_IFLAG;}
 slow_running=1;
}
static void stop(void) {
 CRITICAL{remove_VBL(slow_vbl);IE_REG=saved_ie;}
 slow_busy=0;slow_running=0;
 bb_cpu(0);
}
static void results(void) {
 char v[20],*e;uint32_t frames=value(slow_frames),lag=value(slow_lag),share;
 share=frames?(lag*1000u+frames/2u)/frames:0;
 ui_status("Stopped");
 digits(11,10,slow_frames);digits(11,12,slow_lag);
 strcpy(v,"Share ");e=ui_decimal(v+6,share/10u);*e++='.';*e++='0'+(char)(share%10u);
 strcpy(e,"%  Max ");e[7]='0'+(char)slow_longest;e[8]=0;
 ui_line(UI_DETAIL,v);
}
static uint8_t clamp(uint8_t v,int8_t step,uint8_t low,uint8_t high) {
 if(step>0 && v<high)return v+1u;
 if(step<0 && v>low)return v-1u;
 return v;
}
void slowdown_run(void) BANKED {
 uint8_t key,old=0,n,page=0,row=0,shown=0;
 {uint8_t preset=ui_presets("Slowdown presets",presets,notes,seen);if(preset==255)return;seen=1;
  if(preset){slow_fast=0;slow_heavy=slow_light=4;slow_steps=30;slow_base=10;slow_pattern=0;slow_load=15;
   if(preset==2)slow_load=25;
   if(preset==3){slow_pattern=1;slow_load=25;}
   if(preset==4){slow_pattern=2;slow_load=30;slow_base=5;slow_steps=60;}}}
 settings(page,row);
 for(;;){
  vsync();key=joypad();n=key&~old;old=key;
  if((key&(J_A|J_B|J_START|J_SELECT))==(J_A|J_B|J_START|J_SELECT)){HIDE_SPRITES;if(bb_exit())return;shown=0;settings(page,row);old=0;continue;}
  if(shown){
   /* The results stay up until B leaves or Start goes back to settings. */
   if(n&J_B)return;
   if(n&J_START){shown=0;settings(page,row);}
   continue;
  }
  if(n&J_B)return;
  if(n&J_SELECT){page^=1;row=0;}
  if(n&J_UP)row=(row+(page?2u:3u))%(page?3u:4u);
  if(n&J_DOWN)row=(row+1u)%(page?3u:4u);
  if(n&(J_LEFT|J_RIGHT)){int8_t s=(n&J_RIGHT)?1:-1;
   if(!page){
    if(row==0)slow_load=clamp(slow_load,s,1,40);
    else if(row==1)slow_pattern=(slow_pattern+3u+s)%3u;
    else if(row==2 && _cpu==CGB_TYPE)slow_fast^=1;
    else if(row==3)slow_base=clamp(slow_base,s,1,40);
   }else{
    if(row==0)slow_heavy=clamp(slow_heavy,s,1,60);
    else if(row==1)slow_light=clamp(slow_light,s,1,60);
    else slow_steps=clamp(slow_steps,s,2,60);
   }
  }
  if(n&J_A){
   start();
   while(!(key=slow_update()));
   stop();
   if(key==2){HIDE_SPRITES;if(bb_exit())return;settings(page,row);}
   else{results();shown=1;}
   old=joypad();page=0;continue;
  }
  if(n)settings(page,row);
 }
}
