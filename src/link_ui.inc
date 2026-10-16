/* Included in the link engine's bank so serial state stays directly accessible. */
static uint8_t link_detail,link_view=255;
static void link_body(void) {
 uint8_t y;for(y=4;y<16;++y){fill_bkg_rect(0,y,20,1,0);if(running)service();}
 ui_text(1,4,"Link cable");ui_box(5,14);ui_number(16,4,page+1);ui_text(17,4,"/4");
}
static void link_begin(void) {link_view=255;link_detail=0;ui_scene(2,0);}
void draw(void) {
 char value[12];uint16_t ov,un;
 if(link_view!=page){link_body();link_view=page;ui_scene_redraw();}
 HIDE_SPRITES;
 if(page==0 && !link_detail){
  ui_scene(2,good?(uint8_t)good&3u:0);
  fill_bkg_rect(6,9,8,1,0);ui_number(6,9,good);
  ui_text(1,13,host?"Host":"Peer");ui_text(14,13,host?"Peer":"Host");
  ui_status(failed()?failures[first_code]:!good?"Waiting for peer":"Packets accepted");
 }else if(page==0){
  if(link_detail==1){ui_value(0,"Good",good,0);if(running)service();ui_value(1,"CRC",crc_errors,0);if(running)service();ui_value(2,"Sequence",seq_errors,0);if(running)service();ui_value(3,"Payload",data_errors,0);}
  else if(link_detail==2){CRITICAL{ov=overflow;un=underrun;}ui_value(0,"Gaps",timeouts,0);if(running)service();ui_value(1,"RX full",ov,0);if(running)service();ui_value(2,"TX empty",un,0);if(running)service();ui_value(3,"First pkt",first_seq,0);}
  else {ui_value(0,"First sec",first_sec,0);if(running)service();ui_value(1,"Want CRC",first_expected_crc,0);if(running)service();ui_value(2,"Read CRC",first_received_crc,0);if(running)service();ui_value(3,"Want seq",first_wanted_seq,0);}
 }else if(page==1){
  if(!link_detail){ui_value(0,"Updates",updates,0);if(running)service();ui_value(1,"Scenes",barriers,0);if(running)service();ui_value(2,"State err",state_errors,0);if(running)service();ui_value(3,"Late",deadlines,0);}
  else if(link_detail==1){ui_value(0,"Barriers",barrier_errors,0);if(running)service();ui_value(1,"Order err",epoch_errors,0);if(running)service();ui_value(2,"Old acks",stale_replies,0);if(running)service();ui_value(3,"Step",simulation.epoch,0);}
  else if(link_detail==2){ui_value(0,"Want hash",first_wanted_hash,0);if(running)service();ui_value(1,"Read hash",first_got_hash,0);if(running)service();ui_value(2,"Want step",first_wanted_epoch,0);if(running)service();ui_value(3,"Read step",first_got_epoch,0);}
  else {ui_value(0,"Want cmd",first_kind,0);if(running)service();ui_value(1,"Read cmd",first_got_kind,0);if(running)service();ui_value(2,"Test err",first_test_mismatch,0);if(running)service();ui_field(3,"Scene",scene_pending?"Loading":waiting?"Wait ack":"Ready",0);}
 }else if(page==2){
  if(!link_detail){ui_value(0,"Reply fr",max_reply,0);if(running)service();ui_value(1,"Gap fr",max_gap,0);if(running)service();ui_value(2,"Recov fr",max_recovery,0);if(running)service();ui_value(3,"Budget",reply_budget(),0);}
  else {ui_field(0,"CPU",double_cpu?"Double":"Normal",0);if(running)service();ui_field(1,"Wire",fast?"Fast":"Normal",0);if(running)service();ui_field(2,"Rate",rate_mode==0?"Paced":rate_mode==1?"Burst":"Full",0);if(running)service();ui_value(3,"Late",deadlines,0);}
 }else{
  if(profile){SHOW_SPRITES;ui_text(2,6,"Shared ball");}else ui_text(2,8,"No shared ball");
  fill_bkg_rect(1,15,18,1,0);ui_text(1,15,"Step");ui_number(7,15,simulation.epoch);
 }
 if(running)service();
 if(page || link_detail)ui_status(failed()?failures[first_code]:!profile && page==1?"Sustain profile":"Detailed readings");
 fill_bkg_rect(0,17,20,1,0);
 ui_text(1,17,failed()?"Fail":!good?"Wait":elapsed_seconds>=PASS_SECONDS?"Pass":running?(frozen?"Held":"Running"):"Stopped");
 ui_decimal(value,elapsed_seconds/60u);ui_text(12,17,value);ui_text(15,17,":");ui_cell(16,17,'0'-32+(elapsed_seconds%60)/10);ui_cell(17,17,'0'-32+elapsed_seconds%10);
 if(running)service();
}
static void link_detail_change(uint8_t pressed) {
 if(pressed&(J_A|J_UP|J_DOWN)){
  link_detail=(link_detail+((pressed&J_UP)?3u:1u))&3u;
  if(page==2)link_detail&=1u;
  link_view=255;draw();
 }
}
