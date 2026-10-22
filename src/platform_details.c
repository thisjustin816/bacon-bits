#pragma bank 5
#include "platform_details.h"
uint8_t pd_obs[12][4],pd_before,pd_oam[4],pd_cgb;
uint16_t pd_mask;
char pd_name[12];
static const char *const titles[]={"FF72 / FF73","FF74","FF75","OPRI FF6C","PCM FF76/77","RP FF56","VBK FF4F","KEY1 FF4D","KEY0 FF4C","SB FF01","FF4E / FF57","SGB probe"};
static const char *const expected[]={"5A A5 3C C3","5A A5","8F FF","FE","00 00","2E/3E/02","FE","Bits 7E","FF","00","FF FF","00"};
static const char *const reasons[]={"Register storage","Register storage","Bits 4 to 6","Priority mask","Idle APU output","Infrared mask","VRAM bank mask","Unused bits","Post boot value","Serial storage","Unmapped IO","SGB response"};
static const uint8_t counts[]={4,2,2,1,2,1,1,1,1,1,2,1};
static const char *display_name(void) {
 if(pd_name[0]=='B')return "binjgb";
 if(pd_name[0]=='P')return "PyBoy";
 if(pd_name[0]=='V')return "VBA-M";
 if(pd_name[0]=='M')return pd_name[1]=='G'?"mGBA":"MiSTer FPGA";
 if(pd_name[0]=='G')return pd_name[1]=='E'?"Gearboy":pd_name[1]=='A'?"Gambatte":"GB Online";
 return pd_name[0]=='N'?"None":"Unknown";
}
static void hex(char *s,uint8_t n){static const char h[]="0123456789ABCDEF";s[0]=h[n>>4];s[1]=h[n&15];s[2]=0;}
static void values(uint8_t y,const uint8_t *data,uint8_t count){char s[3];uint8_t i;for(i=0;i<count;i++){hex(s,data[i]);ui_text(2+3*i,y,s);}}
static void draw(uint8_t pick,uint8_t failed,uint8_t signature){char s[3];
 ui_screen(signature?"Name evidence":"Probe details","");
 if(!pd_cgb){ui_text(2,7,"CGB probes only");ui_text(2,10,"No CGB readings");ui_status("No CGB probes");return;}
 if(signature){ui_text(2,6,display_name());
  if(pd_name[0]=='B'){ui_text(2,8,"72/73 all FF");ui_text(2,10,"PCM both FF");values(12,pd_obs[0],4);values(13,pd_obs[4],2);}
  else if(pd_name[0]=='M' && pd_name[1]=='G'){ui_text(2,8,"FF72 unchanged");ui_text(2,10,"FF75 FF read 8F");hex(s,pd_before);ui_text(2,12,s);values(13,pd_obs[0],2);hex(s,pd_obs[2][1]);ui_text(10,13,s);}
  else if(pd_name[0]=='P'){ui_text(2,8,"KEY0 read FB");values(12,pd_obs[8],1);}
  else if(pd_name[0]=='V'){ui_text(2,8,"FF4E holds 00");values(12,pd_obs[10],1);}
  else if(pd_name[0]=='G' && pd_name[1]=='E'){ui_text(2,8,"FF57 holds 00");values(12,&pd_obs[10][1],1);}
  else if(pd_name[0]=='G' && pd_name[1]=='A'){ui_text(2,8,"OAM 08 01 EF DE");values(12,pd_oam,4);}
  else if(pd_name[0]=='G'){ui_text(2,8,"VBK read 00");values(12,pd_obs[6],1);}
  else if(pd_name[0]=='M'){ui_text(2,8,"RP read 02");ui_text(2,10,"No other tells");values(12,pd_obs[5],1);}
  else {ui_text(2,8,"No known match");ui_text(2,10,pd_mask?"Tells found":"No tells found");}
  ui_text(1,15,"Signature match");ui_status((pd_name[0]=='N' || pd_name[0]=='U')?"No signature":"Known signature");
 }else{ui_text(2,6,titles[pick]);ui_text(2,8,"Expect");ui_text(2,9,expected[pick]);ui_text(2,11,"Read");values(12,pd_obs[pick],counts[pick]);
 ui_text(14,6,(pd_mask&(1u<<pick))?"Fail":"Pass");ui_number(pick<9?15:14,4,pick+1);ui_text(16,4,"/12");ui_text(1,15,reasons[pick]);ui_status(failed?"Failed checks":"All checks");}

}
void pd_show(void) BANKED {uint8_t key,old=0,pick=0,failed=!!pd_mask,signature=0,n,shown;
 if(failed)while(!(pd_mask&(1u<<pick)))++pick;draw(pick,failed,signature);shown=pick|(failed<<4)|(signature<<5);while(joypad())vsync();
 for(;;){vsync();key=joypad();n=key&~old;old=key;if(n&J_B)break;
 if((n&J_SELECT) && pd_cgb)signature^=1;
 if(n&J_A){failed=(!failed && pd_mask);if(failed && !(pd_mask&(1u<<pick)))while(!(pd_mask&(1u<<pick)))pick=(pick+1)%12;}
 if(n&(J_LEFT|J_RIGHT)){do{pick=(pick+((n&J_LEFT)?11:1))%12;}while(failed && !(pd_mask&(1u<<pick)));signature=0;}
 /* Redraw only when the view changed; an identical redraw blinks the screen.
    Without CGB readings every view is the same. */
 if(n && pd_cgb && shown!=(pick|(failed<<4)|(signature<<5))){draw(pick,failed,signature);shown=pick|(failed<<4)|(signature<<5);}
 }while(joypad())vsync();
}

uint8_t pd_likely;
char pd_hardware[10];
static void summary(void) {
 uint8_t i,failed=0;
 ui_init();ui_text(1,4,"Platform");ui_box(5,14);ui_scene(1,0);
 for(i=0;i<12;++i){if(pd_mask&(1u<<i))++failed;
  ui_cell(2+(i%6)*3,i<6?7:13,pd_cgb?((pd_mask&(1u<<i))?UI_FAIL:UI_PASS):UI_EMPTY);
 }
 ui_text(1,10,pd_hardware);
 ui_status(pd_cgb?display_name():"No CGB probes");
 if(pd_cgb){ui_number(failed<10?13:12,10,failed);ui_text(14,10,"/12");ui_text(12,12,"Tells");ui_text(1,17,pd_likely?"Emu likely":"Emu no tells");}
}
void pd_summary(void) BANKED {
 uint8_t key,old=0,n,candidate=0;
 summary();while(joypad())vsync();
 for(;;){vsync();if(bb_exit())return;key=bb_keys;
  if(!key){old=candidate=0;continue;}
  if(key!=candidate){candidate=key;continue;}
  n=key&~old;old=key;
  if(key==J_B && n)return;
  if(n && (key==J_A || key==J_SELECT)){pd_show();summary();old=0;}
 }
}
