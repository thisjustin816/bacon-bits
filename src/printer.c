#pragma bank 5
#include "bb.h"
/* Prints a test sheet on a Game Boy Printer with chosen waits between
   strips and between bytes, to find where a printer and a console stop
   agreeing. Strip k carries k tiles of ink from the left edge, so the paper
   shows which strips the printer still held when it printed. Nothing is
   drawn while packets go out, so the waits are the only gaps. Pages 2 to 4
   check whether the printer takes data after a print with no Init: right
   after the polls that saw it go idle, after 200 ms of quiet, and after one
   00 byte. */
uint8_t prn_strips=4,prn_pause,prn_byte=1,prn_state,prn_alive,prn_status,prn_kept,prn_fast;
/* The Init check: prn_gap is the status the printer answered a data packet
   with after a print and no Init, valid when prn_gapped. prn_stage is how far
   the check got; prn_part1 and prn_part2 are 0 not run, 1 printed, 2 not.
   prn_before is what goes before that packet: 0 nothing past the polls, 1
   quiet, 2 a 00 byte. */
uint8_t prn_gap,prn_gapped,prn_stage,prn_part1,prn_part2,prn_before;
/* sent: the strips in the job prn_kept counts. steady: the check sends data
   bytes at the steady rate whatever Byte ms says. */
static uint8_t seen,row,pace=1,sent,steady,running;
static uint16_t sum;
static const char *const presets[]={"","Steady","Paused 100 ms","Paused 200 ms","Slow bytes"};
static const char *const notes[]={"Keep settings","Back to back","Strips 100 ms apart","Strips 200 ms apart","Strip bytes 6 ms"};
enum {PRN_READY,PRN_PRINTED,PRN_ERROR,PRN_MISSING,PRN_NO_REPLY,PRN_BUSY,PRN_STOPPED};
static const char *const states[]={"Ready","Printed","Error","No printer","No reply","Still busy","Stopped"};
static const uint8_t print_args[4]={1u,0x13u,0xE4u,0x40u};
/* delay() counts CPU cycles, so at double speed it waits half as long. */
static void wait_ms(uint16_t ms){if(bb_fast)ms<<=1;delay(ms);}
/* One byte at the internal clock, 8,192 Hz at normal speed and 16,384 Hz at
   double speed, then the rest of the byte period: prn_byte milliseconds from
   start to start inside a data packet, so the other packets still reach a
   printer that drops slow ones. */
static uint8_t xfer(uint8_t b) {
 SB_REG=b;SC_REG=0x81u;
 while(SC_REG&0x80u);
 b=SB_REG;
 if(pace>1u)wait_ms(pace-1u);
 return b;
}
static void send(uint8_t b){sum+=b;xfer(b);}
/* A packet: magic, command, no compression, length, payload, checksum, and
   the two bytes the printer answers in. A data packet with no args is strip
   number strip, made byte by byte so no buffer or drawing sits between. */
static void packet(uint8_t command,uint8_t strip,uint16_t length,const uint8_t *args) {
 uint16_t i;uint8_t tile,v;
 pace=command==4u&&length&&!steady?prn_byte:1u;
 xfer(0x88u);xfer(0x33u);sum=0;
 send(command);send(0u);send((uint8_t)length);send((uint8_t)(length>>8));
 for(i=0;i!=length;++i) {
  if(args){send(args[i]);continue;}
  tile=(uint8_t)(i>>4);if(tile>=20u)tile-=20u;
  /* Ink on both planes for the strip's own tiles; elsewhere the top pixel
     row is light grey, so each strip's top edge shows on the paper. */
  v=tile<strip?0xFFu:(i<320u && (uint8_t)(i&15u)==0u)?0xFFu:0u;
  send(v);
 }
 xfer((uint8_t)sum);xfer((uint8_t)(sum>>8));
 /* The last byte's wait would fall outside the packet, between strips. */
 prn_alive=xfer(0);pace=1;prn_status=xfer(0);
}
/* A reply the job cannot go on from: the printer missing, a packet it did
   not take, or an error bit (checksum, packet, jam, other, battery). */
static uint8_t failed(uint8_t first) {
 if(prn_alive!=0x81u){prn_state=first?PRN_MISSING:PRN_NO_REPLY;return 1;}
 if(prn_status&0xF1u){prn_state=PRN_ERROR;return 1;}
 return 0;
}
/* B between packets sends Break and ends the job. */
static uint8_t stopped(void) {
 if(!(joypad()&J_B))return 0;
 packet(8u,0,0,0);prn_state=PRN_STOPPED;return 1;
}
/* Polls status until the printer has been busy and then idle twice in a row,
   so one reply that lost its busy bit does not end the wait early. Returns 1
   with prn_state set when the job cannot go on. */
static uint8_t printed(void) {
 uint8_t busy=0,idle=0;uint16_t f;
 for(f=0;;++f) {
  vsync();
  if(stopped())return 1;
  packet(15u,0,0,0);if(failed(0))return 1;
  if(prn_status&2u){busy=1;idle=0;}
  else if((busy||f>=30u)&&++idle>=2u)return 0;
  if(f>=1200u){prn_state=PRN_BUSY;return 1;}
 }
}
static void job(void) {
 uint8_t k,wiped=1u;
 prn_kept=0;sent=prn_strips;
 packet(1u,0,0,0);if(failed(1))return;
 for(k=1;k<=sent;++k) {
  /* B is read between strips, since a slow strip can take seconds. */
  if(stopped())return;
  if(k>1u&&prn_pause)wait_ms((uint16_t)prn_pause*10u);
  packet(4u,k,640u,0);if(failed(0))return;
  /* A data packet's reply carries 08 once earlier strips are held; a reply
     without it after the first means the printer reset and dropped them. */
  if(!(prn_status&8u))wiped=k;
 }
 prn_kept=(uint8_t)(sent-wiped+1u);
 packet(4u,0,0,0);if(failed(0))return;
 packet(2u,0,4u,print_args);if(failed(0))return;
 ui_status("Printing");
 if(printed())return;
 prn_state=PRN_PRINTED;
}
/* One strip as a part of its own: Init, the strip, the empty packet that ends
   the image, Print, then the wait. Returns 1 when the check cannot go on. */
static uint8_t part(uint8_t strip,uint8_t first) {
 packet(1u,0,0,0);if(failed(first))return 1;
 if(stopped())return 1;
 packet(4u,strip,640u,0);if(failed(0))return 1;
 packet(4u,0,0,0);if(failed(0))return 1;
 packet(2u,0,4u,print_args);if(failed(0))return 1;
 return printed();
}
/* The reply to a data packet sent after a print with no Init. A packet error
   is the answer being measured, so it ends nothing; only no reply does. */
static uint8_t gap(void) {
 if(prn_alive!=0x81u){prn_state=PRN_NO_REPLY;return 1;}
 prn_gap=prn_status;prn_gapped=1;return 0;
}
static void check_parts(void) {
 prn_stage=1;ui_status("Part 1");
 if(part(1u,1u))return;
 prn_stage=2;ui_status("No Init");
 if(stopped())return;
 /* 200 ms is past the 125 ms after which an idle printer resets as an Init
    does. A 00 byte is a bad packet start; the printer answers FF until the
    line is quiet for 5.12 ms, so the data packet waits 20 ms after it. */
 if(prn_before==1u)delay(200);
 if(prn_before==2u){xfer(0);delay(20);}
 packet(4u,2u,640u,0);if(gap())return;
 prn_stage=3;ui_status("Part 2");
 if(part(2u,0))return;
 prn_stage=4;prn_state=PRN_PRINTED;
}
/* Prints one strip, waits for the printer to go idle, sends one data packet
   with no Init and keeps its reply, then prints a second strip after an Init. */
static void check_view(void);
static const char *const befores[]={"No Init","Quiet","00 byte"};
static void check(void) {
 prn_kept=0;prn_gapped=0;prn_stage=0;prn_part1=prn_part2=0;steady=1;running=1;
 /* The old readings and the hint go before the first packet, not between. */
 check_view();
 check_parts();
 steady=0;running=0;
 prn_part1=prn_stage>=2u?1u:prn_stage?2u:0;
 prn_part2=prn_stage==4u?1u:prn_stage==3u?2u:0;
}
static const char hex[]="0123456789ABCDEF";
/* The state in the bottom border, and the printer's last two reply bytes,
   alive then status, in its corner. */
static void readout(void) {
 char s[9];
 if(prn_state!=PRN_READY&&prn_state!=PRN_MISSING){s[0]=hex[prn_alive>>4];s[1]=hex[prn_alive&15u];s[2]=' ';s[3]=hex[prn_status>>4];s[4]=hex[prn_status&15u];s[5]=0;ui_corner(s);}
 else ui_corner("");
 if(prn_state==PRN_ERROR){s[0]='E';s[1]='r';s[2]='r';s[3]='o';s[4]='r';s[5]=' ';s[6]=hex[prn_status>>4];s[7]=hex[prn_status&15u];s[8]=0;ui_status(s);}
 else ui_status(states[prn_state]);
}
static void view(void) {
 char s[13];
 ui_page("Printer","1/4",0xb0u);
 ui_value(0,"Strips",prn_strips,row==0);
 ui_value(1,"Pause ms",(uint16_t)prn_pause*10u,row==1);
 ui_value(2,"Byte ms",prn_byte,row==2);
 ui_field(3,"CPU",prn_fast?"Double":"Normal",row==3);
 /* Kept is counted only once every strip went out. */
 if(!prn_kept)ui_line(UI_DETAIL,"");
 else {s[0]='K';s[1]='e';s[2]='p';s[3]='t';s[4]=' ';ui_decimal(s+5,prn_kept);s[6]=' ';s[7]='o';s[8]='f';s[9]=' ';ui_decimal(s+10,sent);ui_line(UI_DETAIL,s);}
 readout();
}
static const char *part_text(uint8_t result){return result==1u?"Printed":result?(prn_state==PRN_STOPPED?"Stopped":"Failed"):"-";}
/* Refused is the packet-error bit of the reply to data sent after a print. */
static void check_view(void) {
 static const char *const pages[]={"2/4","3/4","4/4"};
 char s[3];
 ui_page("Printer",pages[prn_before],0xb1u+prn_before);
 ui_field(0,"Part 1",part_text(prn_part1),0);
 if(prn_gapped){s[0]=hex[prn_gap>>4];s[1]=hex[prn_gap&15u];s[2]=0;}else{s[0]='-';s[1]=0;}
 ui_field(1,befores[prn_before],s,0);
 ui_field(2,"Refused",!prn_gapped?"-":(prn_gap&0x10u)?"Yes":"No",0);
 ui_field(3,"Init",part_text(prn_part2),0);
 /* The verdict needs both readings; the hint stays until a check ran. */
 ui_line(UI_DETAIL,running?"":prn_stage==4u?((prn_gap&0x10u)?"Init needed":"Init not needed"):prn_stage?"Did not finish":"A: run the check");
 readout();
}
void printer_run(void) BANKED {
 uint8_t preset,key,old=0,n,was_fast,page=0;
 preset=ui_presets("Printer presets",presets,notes,seen);if(preset==255)return;seen=1;
 if(preset){prn_strips=4;prn_pause=preset==2?10u:preset==3?20u:0;prn_byte=preset==4?6u:1u;prn_fast=0;}
 /* Normal speed gives the printer its 8,192 Hz clock; CPU Double prints at a Color's
    double speed instead. */
 was_fast=KEY1_REG>>7;bb_cpu(0);prn_state=PRN_READY;row=0;prn_stage=prn_part1=prn_part2=prn_gapped=prn_before=0;view();
 for(;;) {
  vsync();key=joypad();n=key&~old;old=key;
  if(n&J_B)break;
  /* Each check page runs its own check, so a page starts with no readings. */
  if(n&J_SELECT){page=page==3u?0:page+1u;prn_before=page?page-1u:0;row=0;prn_state=PRN_READY;prn_stage=prn_part1=prn_part2=prn_gapped=0;}
  if(page==0) {
  if(n&J_UP)row=row?row-1u:3u;
  if(n&J_DOWN)row=row==3u?0:row+1u;
  /* Double speed needs a Color. */
  if(n&(J_LEFT|J_RIGHT) && row==3u){if(_cpu==CGB_TYPE)prn_fast^=1u;}
  else if(n&(J_LEFT|J_RIGHT)) {
   uint8_t *v=row==0?&prn_strips:row==1?&prn_pause:&prn_byte;
   uint8_t low=row==1?0:1u,high=row==0?9u:row==1?25u:8u;
   if(n&J_RIGHT){if(*v<high)++*v;}else if(*v>low)--*v;
  }
  }
  if(n&J_A){ui_status("Sending");if(page)check();else{bb_cpu(prn_fast);job();bb_cpu(0);}while(joypad())vsync();old=0;}
  if(n){if(page)check_view();else view();}
 }
 bb_cpu(was_fast);
}
