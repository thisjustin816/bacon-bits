/* Included in the link engine's bank so serial state stays directly accessible. */
static uint8_t link_detail,link_view=255;
static void link_body(void) {
 uint8_t y;ui_cover();for(y=UI_TOP;y<=UI_BOTTOM;++y){fill_bkg_rect(0,y,20,1,0);if(running)service();}
 {char count[4]={(char)('1'+page),'/','4',0};ui_frame(UI_BOTTOM,"Link",count);}
}
static void link_begin(void) {link_view=255;link_detail=0;ui_scene(2,0);}
void draw(void) {
 char value[12];uint16_t ov,un;
 if(link_view!=page){link_body();link_view=page;ui_scene_redraw();}
 HIDE_SPRITES;
 if(page==0 && !link_detail){
  ui_scene(2,good?(uint8_t)good&3u:0);
  ui_count(6,9,good,8);
  ui_text(1,13,host?"Host":"Peer");ui_text(14,13,host?"Peer":"Host");
  ui_status(failed()?failures[first_code]:!good?"Waiting for peer":"Packets accepted");
 }else if(page==0){
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
  else {ui_field(0,"CPU",double_cpu?"Double":"Normal",0);if(running)service();ui_field(1,"Wire",fast?"Fast":"Normal",0);if(running)service();ui_field(2,"Rate",rate_mode==0?"Paced":rate_mode==1?"Burst":"Full",0);if(running)service();ui_value(3,"Dropouts",dropouts,0);}
 }else{
  if(profile){SHOW_SPRITES;ui_text(2,7,"Shared ball");}else ui_text(2,8,"No shared ball");
 }
 if(running)service();
 if(page || link_detail)ui_status(failed()?failures[first_code]:!profile && page==1?"Sustain profile":"Detailed view");
 {char *end=ui_decimal(value,elapsed_seconds/60u);uint8_t x;*end++=':';*end++='0'+(elapsed_seconds%60)/10;*end++='0'+elapsed_seconds%10;*end=0;x=19u-(uint8_t)(end-value);
  ui_cell(0,UI_DETAIL,0);ui_pad(1,UI_DETAIL,failed()?"Fail":!good?"Wait":elapsed_seconds>=PASS_SECONDS?"Pass":running?(frozen?"Held":"Running"):"Stopped",x-1u);ui_text(x,UI_DETAIL,value);ui_cell(19,UI_DETAIL,0);}
 if(running)service();
}
static void link_detail_change(uint8_t pressed) {
 if(pressed&(J_A|J_UP|J_DOWN)){
  link_detail=(link_detail+((pressed&J_UP)?3u:1u))&3u;
  if(page==2)link_detail&=1u;
  link_view=255;draw();
 }
}
