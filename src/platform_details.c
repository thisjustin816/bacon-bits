#pragma bank 5
#include "platform_details.h"
uint8_t pd_obs[12][4],pd_before,pd_oam[4],pd_cgb;
uint16_t pd_mask;
char pd_name[12];
static uint8_t map[360],attrs[360];
static const char *const titles[]={"FF72 / FF73","FF74","FF75","OPRI FF6C","PCM FF76/77","RP FF56","VBK FF4F","KEY1 FF4D","KEY0 FF4C","SB FF01","FF4E / FF57","SGB PROBE"};
static const char *const expected[]={"5A A5 3C C3","5A A5","8F FF","FE","00 00","2E/3E/02","FE","BITS 7E","FF","00","FF FF","00"};
static const char *const reasons[]={"REGISTER STORAGE","REGISTER STORAGE","BITS 4 TO 6","PRIORITY MASK","IDLE APU OUTPUT","INFRARED MASK","VRAM BANK MASK","UNUSED BITS","POST BOOT VALUE","SERIAL STORAGE","UNMAPPED IO","SGB RESPONSE"};
static const uint8_t counts[]={4,2,2,1,2,1,1,1,1,1,2,1};
static void hex(char *s,uint8_t n){static const char h[]="0123456789ABCDEF";s[0]=h[n>>4];s[1]=h[n&15];s[2]=0;}
static void values(uint8_t y,const uint8_t *data,uint8_t count){char s[3];uint8_t i;for(i=0;i<count;i++){hex(s,data[i]);ui_text(2+3*i,y,s);}}
static void draw(uint8_t pick,uint8_t failed,uint8_t signature){char s[3];
 ui_screen(signature?"NAME EVIDENCE":"PROBE DETAILS","");
 if(!pd_cgb){ui_text(2,7,"CGB PROBES ONLY");ui_text(2,10,"NO CGB READINGS");ui_status("NO CGB PROBES");return;}
 if(signature){ui_text(2,6,pd_name);
  if(pd_name[0]=='B'){ui_text(2,8,"72/73 ALL FF");ui_text(2,10,"PCM BOTH FF");values(12,pd_obs[0],4);values(13,pd_obs[4],2);}
  else if(pd_name[0]=='M' && pd_name[1]=='G'){ui_text(2,8,"FF72 UNCHANGED");ui_text(2,10,"FF75 FF READ 8F");hex(s,pd_before);ui_text(2,12,s);values(13,pd_obs[0],2);hex(s,pd_obs[2][1]);ui_text(10,13,s);}
  else if(pd_name[0]=='P'){ui_text(2,8,"KEY0 READ FB");values(12,pd_obs[8],1);}
  else if(pd_name[0]=='V'){ui_text(2,8,"FF4E HOLDS 00");values(12,pd_obs[10],1);}
  else if(pd_name[0]=='G' && pd_name[1]=='E'){ui_text(2,8,"FF57 HOLDS 00");values(12,&pd_obs[10][1],1);}
  else if(pd_name[0]=='G' && pd_name[1]=='A'){ui_text(2,8,"OAM 08 01 EF DE");values(12,pd_oam,4);}
  else if(pd_name[0]=='G'){ui_text(2,8,"VBK READ 00");values(12,pd_obs[6],1);}
  else if(pd_name[0]=='M'){ui_text(2,8,"RP READ 02");ui_text(2,10,"NO OTHER TELLS");values(12,pd_obs[5],1);}
  else {ui_text(2,8,"NO KNOWN MATCH");ui_text(2,10,pd_mask?"TELLS FOUND":"NO TELLS FOUND");}
  ui_text(1,15,"SIGNATURE MATCH");ui_status((pd_name[0]=='N' || pd_name[0]=='U')?"NO SIGNATURE":"KNOWN SIGNATURE");
 }else{ui_text(2,6,titles[pick]);ui_text(2,8,"EXPECT");ui_text(2,9,expected[pick]);ui_text(2,11,"READ");values(12,pd_obs[pick],counts[pick]);
 ui_text(14,6,(pd_mask&(1u<<pick))?"FAIL":"PASS");ui_number(15,4,pick+1);ui_text(17,4,"/12");ui_text(1,15,reasons[pick]);ui_status(failed?"FAILED CHECKS":"ALL CHECKS");}

}
void pd_show(void) BANKED {uint8_t key,old=0,pick=0,failed=!!pd_mask,signature=0,n;
 VBK_REG=0;get_bkg_tiles(0,0,20,18,map);if(_cpu==CGB_TYPE){VBK_REG=1;get_bkg_tiles(0,0,20,18,attrs);VBK_REG=0;}
 if(failed)while(!(pd_mask&(1u<<pick)))++pick;draw(pick,failed,signature);while(joypad())vsync();
 for(;;){vsync();key=joypad();n=key&~old;old=key;if(n&J_B)break;
 if(n&J_SELECT)signature^=1;
 if(n&J_A){failed=(!failed && pd_mask);if(failed && !(pd_mask&(1u<<pick)))while(!(pd_mask&(1u<<pick)))pick=(pick+1)%12;}
 if(n&(J_LEFT|J_RIGHT)){do{pick=(pick+((n&J_LEFT)?11:1))%12;}while(failed && !(pd_mask&(1u<<pick)));signature=0;}
 if(n)draw(pick,failed,signature);
 }while(joypad())vsync();
}
void pd_restore(void) BANKED {VBK_REG=0;set_bkg_tiles(0,0,20,18,map);if(_cpu==CGB_TYPE){VBK_REG=1;set_bkg_tiles(0,0,20,18,attrs);VBK_REG=0;}}
