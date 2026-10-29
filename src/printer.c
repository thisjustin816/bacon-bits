#pragma bank 5
#include "bb.h"
/* Prints a test sheet on a Game Boy Printer with chosen waits between
   strips and between bytes, to find where a printer and a console stop
   agreeing. Strip k carries k tiles of ink from the left edge, so the paper
   shows which strips the printer still held when it printed. Nothing is
   drawn while packets go out, so the waits are the only gaps. */
uint8_t prn_strips=4,prn_pause,prn_byte=1,prn_state,prn_alive,prn_status,prn_kept;
/* sent: the strips in the job prn_kept counts. */
static uint8_t seen,row,pace=1,sent;
static uint16_t sum;
static const char *const presets[]={"","Steady","Paused 100 ms","Paused 200 ms","Slow bytes"};
static const char *const notes[]={"Keep settings","Back to back","Strips 100 ms apart","Strips 200 ms apart","Strip bytes 6 ms"};
enum {PRN_READY,PRN_PRINTED,PRN_ERROR,PRN_MISSING,PRN_NO_REPLY,PRN_BUSY,PRN_STOPPED};
static const char *const states[]={"Ready","Printed","Error","No printer","No reply","Still busy","Stopped"};
static const uint8_t print_args[4]={1u,0x13u,0xE4u,0x40u};
/* One byte at the normal 8,192 Hz clock, then the rest of the byte period:
   prn_byte milliseconds from start to start inside a data packet, so the
   other packets still reach a printer that drops slow ones. */
static uint8_t xfer(uint8_t b) {
 SB_REG=b;SC_REG=0x81u;
 while(SC_REG&0x80u);
 b=SB_REG;
 if(pace>1u)delay(pace-1u);
 return b;
}
static void send(uint8_t b){sum+=b;xfer(b);}
/* A packet: magic, command, no compression, length, payload, checksum, and
   the two bytes the printer answers in. A data packet with no args is strip
   number strip, made byte by byte so no buffer or drawing sits between. */
static void packet(uint8_t command,uint8_t strip,uint16_t length,const uint8_t *args) {
 uint16_t i;uint8_t tile,v;
 pace=command==4u&&length?prn_byte:1u;
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
static void job(void) {
 uint8_t k,wiped=1u,busy=0;uint16_t f;
 prn_kept=0;sent=prn_strips;
 packet(1u,0,0,0);if(failed(1))return;
 for(k=1;k<=sent;++k) {
  /* B is read between strips, since a slow strip can take seconds. */
  if(joypad()&J_B){packet(8u,0,0,0);prn_state=PRN_STOPPED;return;}
  if(k>1u&&prn_pause)delay((uint16_t)prn_pause*10u);
  packet(4u,k,640u,0);if(failed(0))return;
  /* A data packet's reply carries 08 once earlier strips are held; a reply
     without it after the first means the printer reset and dropped them. */
  if(!(prn_status&8u))wiped=k;
 }
 prn_kept=(uint8_t)(sent-wiped+1u);
 packet(4u,0,0,0);if(failed(0))return;
 packet(2u,0,4u,print_args);if(failed(0))return;
 ui_status("Printing");
 for(f=0;;++f) {
  vsync();
  if(joypad()&J_B){packet(8u,0,0,0);prn_state=PRN_STOPPED;return;}
  packet(15u,0,0,0);if(failed(0))return;
  if(prn_status&2u)busy=1;
  else if(busy||f>=30u)break;
  if(f>=1200u){prn_state=PRN_BUSY;return;}
 }
 prn_state=PRN_PRINTED;
}
static const char hex[]="0123456789ABCDEF";
static void view(void) {
 char s[9];
 ui_page("Printer","",0);
 ui_value(0,"Strips",prn_strips,row==0);
 ui_value(1,"Pause ms",(uint16_t)prn_pause*10u,row==1);
 ui_value(2,"Byte ms",prn_byte,row==2);
 /* Kept is counted only once every strip went out. */
 if(!prn_kept)ui_field(3,"Kept","",0);
 else {ui_decimal(s,prn_kept);s[1]=' ';s[2]='o';s[3]='f';s[4]=' ';ui_decimal(s+5,sent);ui_field(3,"Kept",s,0);}
 /* The printer's last two reply bytes, alive then status, in the corner. */
 if(prn_state!=PRN_READY&&prn_state!=PRN_MISSING){s[0]=hex[prn_alive>>4];s[1]=hex[prn_alive&15u];s[2]=' ';s[3]=hex[prn_status>>4];s[4]=hex[prn_status&15u];s[5]=0;ui_corner(s);}
 else ui_corner("");
 if(prn_state==PRN_ERROR){s[0]='E';s[1]='r';s[2]='r';s[3]='o';s[4]='r';s[5]=' ';s[6]=hex[prn_status>>4];s[7]=hex[prn_status&15u];s[8]=0;ui_status(s);}
 else ui_status(states[prn_state]);
}
void printer_run(void) BANKED {
 uint8_t preset,key,old=0,n,was_fast;
 preset=ui_presets("Printer presets",presets,notes,seen);if(preset==255)return;seen=1;
 if(preset){prn_strips=4;prn_pause=preset==2?10u:preset==3?20u:0;prn_byte=preset==4?6u:1u;}
 /* The printer takes the 8,192 Hz clock, which only normal speed gives. */
 was_fast=KEY1_REG>>7;bb_cpu(0);prn_state=PRN_READY;row=0;view();
 for(;;) {
  vsync();key=joypad();n=key&~old;old=key;
  if(n&J_B)break;
  if(n&J_UP)row=row?row-1u:2u;
  if(n&J_DOWN)row=row==2u?0:row+1u;
  if(n&(J_LEFT|J_RIGHT)) {
   uint8_t *v=row==0?&prn_strips:row==1?&prn_pause:&prn_byte;
   uint8_t low=row==1?0:1u,high=row==0?9u:row==1?25u:8u;
   if(n&J_RIGHT){if(*v<high)++*v;}else if(*v>low)--*v;
  }
  if(n&J_A){ui_status("Sending");job();while(joypad())vsync();old=0;}
  if(n)view();
 }
 bb_cpu(was_fast);
}
