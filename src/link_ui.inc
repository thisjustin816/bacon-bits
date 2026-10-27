/* Included in the link engine's bank so serial state stays directly accessible. */
static uint8_t link_detail,link_view=255;
/* A reading counts once two frames agree. A hand lands the return chord's
   buttons a frame or so apart, and a bouncing contact reads released for a
   frame; either would otherwise act on one button alone, and Start starts
   the test. */
static uint8_t link_raw;
static uint8_t link_keys(uint8_t previous) {
 uint8_t raw=joypad(),keys=raw==link_raw?raw:previous;
 link_raw=raw;return keys;
}
const char *burst_text(uint8_t n);
const char *idle_text(uint8_t rate,uint8_t step);
const char *masked_text(uint8_t step);
static void link_body(void) {
 uint8_t y;ui_cover();for(y=UI_TOP;y<=UI_BOTTOM;++y){fill_bkg_rect(0,y,20,1,0);if(running)service();}
 {char count[4]={(char)('1'+page),'/','4',0};ui_frame(UI_BOTTOM,"Link",count);}
}
static void link_begin(void) {link_view=255;link_detail=0;ui_scene(2,0);}
static const char *const link_rates[]={"Paced","Burst","Full","Custom"};
static const char *const link_preset_names[]={"","Soak","Packets only","Full speed","Busy game"};
static const char *const link_preset_notes[]={"Keep settings","All load / burst","Sustain / paced","Fast wire / 2x CPU","8 lines masked"};
static uint8_t link_seen;
/* Every preset sets each setting but the role, which each console picks. */
static void link_preset(uint8_t preset) {
 if(!preset)return;
 profile=preset==2?0u:4u;rate_mode=preset==2?0u:preset==3?2u:1u;
 fast=double_cpu=preset==3 && _cpu==CGB_TYPE;
 burst_len=4;idle_step=6;masked_step=preset==4?4u:0u;
}
static const char *const link_short_failures[]={"None","CRC","Role","Payload","Sequence","No sync","RX full","TX empty","Hang","State","Barrier","Order"};
static const char *const link_snap_status[]={"Read in turn","At first failure","Settings in use","Rejected bytes"};
static char *link_hex(char *out,uint8_t b) {
 uint8_t i;for(i=0;i!=2;++i){uint8_t d=i?b&15u:b>>4;*out++=(char)(d<10u?'0'+d:'A'-10+d);}
 *out=0;return out;
}
static void link_hex_pair(uint8_t row,const char *label,uint8_t a,uint8_t b) {
 char s[6],*end=link_hex(s,a);*end++=' ';link_hex(end,b);ui_field(row,label,s,0);
}
/* Page one's views 4 to 7: the state latch() kept when the first failure opened. */
static void link_snapshot(void) {
 char s[18],*end;uint8_t r,i;
 if(!failed()){ui_text(2,UI_FIELD,"No failure yet");return;}
 if(link_detail==4){
  link_hex_pair(0,"SB SC",snap_regs[0],snap_regs[1]);if(running)service();
  link_hex_pair(1,"IF IE",snap_regs[2],snap_regs[3]);if(running)service();
  link_hex_pair(2,"KEY1 LY",snap_regs[4],snap_regs[5]);if(running)service();
  ui_field(3,"Code",link_short_failures[first_code],0);
 }else if(link_detail==5){
  ui_value(0,"RX in",snap_wr,0);if(running)service();
  ui_value(1,"RX out",snap_rd,0);if(running)service();
  end=ui_decimal(s,snap_active);*end++=' ';*end++='a';*end++='t';*end++=' ';ui_decimal(end,snap_txpos);ui_field(2,"TX pkt",s,0);if(running)service();
  if(snap_pending==1){s[0]='A';s[1]='c';s[2]='k';s[3]=' ';ui_decimal(s+4,snap_command);}
  ui_field(3,"Pending",snap_pending==1?(const char *)s:snap_pending?"Scene":"None",0);
 }else if(link_detail==6){
  ui_field(0,"Rate",snap_host?link_rates[snap_rate]:"By host",0);if(running)service();
  ui_field(1,"Burst",snap_host?burst_text(snap_burst):"By host",0);if(running)service();
  ui_field(2,"Idle",snap_host?idle_text(snap_rate,snap_idle):"By host",0);if(running)service();
  ui_field(3,"Masked",masked_text(snap_masked),0);
 }else if(!snap_rejected)ui_text(2,UI_FIELD,"No packet rejected");
 else for(r=0;r!=3;++r){
  end=s;for(i=r*6u;i!=r*6u+6u && i!=16u;++i){if(end!=s)*end++=' ';end=link_hex(end,snap_bytes[i]);}
  ui_pad(2,UI_FIELD+2u*r,s,17);if(running)service();
 }
}
void draw(void) {
 char value[12];uint16_t ov,un;
 if(link_view!=page){link_body();link_view=page;ui_scene_redraw();}
 HIDE_SPRITES;
 if(page==0 && !link_detail){
  ui_scene(2,good?(uint8_t)good&3u:0);
  ui_count(6,9,good,8);
  ui_text(1,13,host?"Host":"Peer");ui_text(14,13,host?"Peer":"Host");
  ui_status(failed()?failures[first_code]:!good?"Waiting for peer":"Packets accepted");
 }else if(page==0 && link_detail>=4)link_snapshot();
 else if(page==0){
  if(link_detail==1){ui_value(0,"Good",good,0);if(running)service();ui_value(1,"CRC",crc_errors,0);if(running)service();ui_value(2,"Sequence",seq_errors,0);if(running)service();ui_value(3,"Payload",data_errors,0);}
  else if(link_detail==2){CRITICAL{ov=overflow;un=underrun;}ui_value(0,"Gaps",timeouts,0);if(running)service();ui_value(1,"RX full",ov,0);if(running)service();ui_value(2,"TX empty",un,0);if(running)service();ui_value(3,"Fail pkt",first_seq,0);}
  else {ui_value(0,"Fail sec",first_sec,0);if(running)service();ui_value(1,"Exp CRC",first_expected_crc,0);if(running)service();ui_value(2,"Got CRC",first_received_crc,0);if(running)service();ui_value(3,"Exp seq",first_wanted_seq,0);}
 }else if(page==1){
  if(!link_detail){ui_value(0,"Updates",updates,0);if(running)service();ui_value(1,"Scenes",barriers,0);if(running)service();ui_value(2,"Desyncs",state_errors,0);if(running)service();ui_value(3,"Late",deadlines,0);}
  else if(link_detail==1){ui_value(0,"Barriers",barrier_errors,0);if(running)service();ui_value(1,"Skipped",epoch_errors,0);if(running)service();ui_value(2,"Old acks",stale_replies,0);if(running)service();ui_value(3,"Step",simulation.epoch,0);}
  else if(link_detail==2){ui_value(0,"Exp hash",first_wanted_hash,0);if(running)service();ui_value(1,"Got hash",first_got_hash,0);if(running)service();ui_value(2,"Exp step",first_wanted_epoch,0);if(running)service();ui_value(3,"Got step",first_got_epoch,0);}
  else {ui_value(0,"Exp cmd",first_kind,0);if(running)service();ui_value(1,"Got cmd",first_got_kind,0);if(running)service();ui_value(2,"Test err",first_test_mismatch,0);if(running)service();ui_field(3,"Scene",scene_pending?"Loading":waiting?"Wait ack":"Ready",0);}
 }else if(page==2){
  if(!link_detail){ui_value(0,"Reply fr",max_reply,0);if(running)service();ui_value(1,"Gap fr",max_gap,0);if(running)service();ui_value(2,"Recov fr",max_recovery,0);if(running)service();ui_value(3,"Budget",reply_budget(),0);}
  else {ui_field(0,"CPU",double_cpu?"Double":"Normal",0);if(running)service();if(host)ui_value(1,"Wire b/s",(fast?262144UL:8192UL)<<double_cpu,0);else ui_field(1,"Wire b/s","By host",0);if(running)service();ui_field(2,"Rate",host?link_rates[rate_mode]:"By host",0);if(running)service();ui_value(3,"Dropouts",dropouts,0);}
 }else{
  if(profile){SHOW_SPRITES;ui_text(2,7,"Shared ball");}else ui_text(2,8,"No shared ball");
 }
 if(running)service();
 if(!page && link_detail>=4)ui_status(link_snap_status[link_detail-4u]);
 else if(page || link_detail)ui_status(failed()?failures[first_code]:!profile && page==1?"Sustain profile":"Detailed view");
 {char *end=ui_decimal(value,elapsed_seconds/60u);uint8_t x;*end++=':';*end++='0'+(elapsed_seconds%60)/10;*end++='0'+elapsed_seconds%10;*end=0;x=19u-(uint8_t)(end-value);
  ui_cell(0,UI_DETAIL,0);ui_pad(1,UI_DETAIL,failed()?"Fail":!good?"Wait":elapsed_seconds>=PASS_SECONDS?"Pass":running?(frozen?"Held":"Running"):"Stopped",x-1u);ui_text(x,UI_DETAIL,value);ui_cell(19,UI_DETAIL,0);}
 if(running)service();
}
static void link_detail_change(uint8_t pressed) {
 if(pressed&(J_A|J_UP|J_DOWN)){
  uint8_t views=page==0?8u:page==2?2u:4u;
  link_detail=(link_detail+((pressed&J_UP)?views-1u:1u))%views;
  link_view=255;draw();
 }
}
