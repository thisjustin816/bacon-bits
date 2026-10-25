#pragma bank 5
#include "platform_details.h"
uint8_t pd_obs[13][4],pd_before,pd_oam[4],pd_cgb;
uint16_t pd_mask;
char pd_name[12];
static const char *const titles[]={"FF72 / FF73","FF74","FF75","OPRI FF6C","PCM FF76/77","RP FF56","VBK FF4F","KEY1 FF4D","KEY0 FF4C","SB FF01","FF4E / FF57","SGB probe","Mode 3 writes"};
static const char *const expected[]={"5A A5 3C C3","5A A5","8F FF","FE","00 00","2E/3E/02","FE","Bits 7E","FF","00","FF FF","00","00 00"};
static const char *const reasons[]={"Register storage","Register storage","Bits 4 to 6","Priority mask","Idle APU output","Infrared mask","VRAM bank mask","Unused bits","Post boot value","Serial storage","Unmapped IO","SGB response","Writes mid-line"};
static const uint8_t counts[]={4,2,2,1,2,1,1,1,1,1,2,1,2};
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
static void draw(uint8_t pick,uint8_t failed,uint8_t signature){char s[3],page[6],*end;
 page[0]=0;if(!signature && pd_cgb){end=ui_decimal(page,pick+1u);end[0]='/';end[1]='1';end[2]='3';end[3]=0;}
 ui_screen(signature?"Name evidence":"Probe",page);
 if(!pd_cgb){ui_text(2,7,"CGB probes only");ui_text(2,10,"No CGB readings");ui_status("No CGB probes");return;}
 if(signature){ui_text(2,7,display_name());
  if(pd_name[0]=='B'){ui_text(2,9,"72/73 all FF");ui_text(2,11,"PCM both FF");values(12,pd_obs[0],4);values(13,pd_obs[4],2);}
  else if(pd_name[0]=='M' && pd_name[1]=='G'){ui_text(2,9,"FF72 unchanged");ui_text(2,11,"FF75 FF read 8F");hex(s,pd_before);ui_text(2,12,s);values(13,pd_obs[0],2);hex(s,pd_obs[2][1]);ui_text(10,13,s);}
  else if(pd_name[0]=='P'){ui_text(2,9,"KEY0 read FB");values(11,pd_obs[8],1);}
  else if(pd_name[0]=='V'){ui_text(2,9,"FF4E holds 00");values(11,pd_obs[10],1);}
  else if(pd_name[0]=='G' && pd_name[1]=='E'){ui_text(2,9,"FF57 holds 00");values(11,&pd_obs[10][1],1);}
  else if(pd_name[0]=='G' && pd_name[1]=='A'){ui_text(2,9,"OAM 08 01 EF DE");values(11,pd_oam,4);}
  else if(pd_name[0]=='G'){ui_text(2,9,"VBK read 00");values(11,pd_obs[6],1);}
  else if(pd_name[0]=='M'){ui_text(2,9,"RP read 02");ui_text(2,11,"No other tells");values(13,pd_obs[5],1);}
  else {ui_text(2,9,"No known match");ui_text(2,11,pd_mask?"Tells found":"No tells found");}
  ui_text(1,15,"Signature match");ui_status((pd_name[0]=='N' || pd_name[0]=='U')?"No signature":"Known signature");
 }else{ui_text(2,7,titles[pick]);ui_text(2,9,"Expect");ui_text(2,10,expected[pick]);ui_text(2,12,"Read");values(13,pd_obs[pick],counts[pick]);
 ui_text(14,7,(pd_mask&(1u<<pick))?"Fail":"Pass");ui_text(1,15,reasons[pick]);ui_status(failed?"Failed checks":"All checks");}

}
void pd_show(void) BANKED {uint8_t key,old=0,pick=0,failed=!!pd_mask,signature=0,n,shown;
 if(failed)while(!(pd_mask&(1u<<pick)))++pick;draw(pick,failed,signature);shown=pick|(failed<<4)|(signature<<5);while(joypad())vsync();
 for(;;){vsync();key=joypad();n=key&~old;old=key;if(n&J_B)break;
 if((n&J_SELECT) && pd_cgb)signature^=1;
 if(n&J_A){failed=(!failed && pd_mask);if(failed && !(pd_mask&(1u<<pick)))while(!(pd_mask&(1u<<pick)))pick=(pick+1)%13;}
 if(n&(J_LEFT|J_RIGHT)){do{pick=(pick+((n&J_LEFT)?12:1))%13;}while(failed && !(pd_mask&(1u<<pick)));signature=0;}
 /* Redraw only when the view changed; an identical redraw blinks the screen.
    Without CGB readings every view is the same. */
 if(n && pd_cgb && shown!=(pick|(failed<<4)|(signature<<5))){draw(pick,failed,signature);shown=pick|(failed<<4)|(signature<<5);}
 }while(joypad())vsync();
}

uint8_t pd_likely;
static const palette_color_t cell_palette[4]={RGB(31,30,27),RGB(31,24,6),RGB(23,9,7),RGB(8,5,4)};
char pd_hardware[10];
static void summary(void) {
 uint8_t i,failed=0;
 ui_init();ui_frame(14,"Platform","");ui_scene(1,0);
 for(i=0;i<13;++i)if(pd_mask&(1u<<i))++failed;
 for(i=0;i<12;++i)ui_cell(2+(i%6)*3,i<6?7:13,pd_cgb?((pd_mask&(1u<<i))?UI_FAIL:UI_PASS):UI_EMPTY);
 /* The 13th port sits over the chip, half a cell off the grid, so it is a
    sprite drawn with the cell tiles and the body palette. */
 if(_cpu==CGB_TYPE)set_sprite_palette(0,1,cell_palette);else OBP0_REG=0xe4;
 set_sprite_tile(0,pd_cgb?((pd_mask&(1u<<12))?UI_FAIL:UI_PASS):UI_EMPTY);set_sprite_prop(0,0);
 move_sprite(0,84,72);SHOW_SPRITES;
 ui_text(1,10,pd_hardware);
 ui_status(pd_cgb?display_name():"No CGB probes");
 if(pd_cgb){ui_number(failed<10?13:12,10,failed);ui_text(14,10,"/13");ui_text(12,12,"Tells");ui_text(1,17,pd_likely?"Emu likely":"Emu no tells");}
}
void pd_summary(void) BANKED {
 uint8_t key,old=0,n,candidate=0;
 summary();while(joypad())vsync();
 for(;;){vsync();if(bb_exit()){move_sprite(0,0,0);return;}key=bb_keys;
  if(!key){old=candidate=0;continue;}
  if(key!=candidate){candidate=key;continue;}
  n=key&~old;old=key;
  if(key==J_B && n){move_sprite(0,0,0);return;}
  if(n && (key==J_A || key==J_SELECT)){pd_show();summary();old=0;}
 }
}
