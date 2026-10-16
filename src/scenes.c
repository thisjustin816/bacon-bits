#pragma bank 6
#include "bb.h"
#include "scene_data.h"
static uint8_t prior_scene=255,prior_frame;
static uint8_t updates[32][3];
void ui_scene_reset(void) BANKED {prior_scene=255;}
void ui_scene_redraw(void) BANKED {prior_frame=255;}
void ui_scene(uint8_t scene,uint8_t frame) BANKED {
 const uint8_t *size=scene_sizes[scene],*map=scene_maps[scene][frame&3u],*old;
 uint8_t x,y,count=0,i;uint16_t n=0;
 if(prior_scene!=scene){set_bkg_data(UI_ART,size[0],scene_tiles[scene]);old=0;}
 else old=prior_frame==255?0:scene_maps[scene][prior_frame];
 for(y=0;y<size[4];++y)for(x=0;x<size[3];++x){
  if(!old)ui_cell(size[1]+x,size[2]+y,map[n]);
  else if(map[n]!=old[n]){updates[count][0]=size[1]+x;updates[count][1]=size[2]+y;updates[count++][2]=map[n];}
  ++n;
 }
 /* Compare poses before VBlank, leaving its short window for the writes. */
 if(count){vsync();for(i=0;i<count;++i)set_bkg_tile_xy(updates[i][0],updates[i][1],updates[i][2]);}
 prior_scene=scene;prior_frame=frame&3u;
}

/* Restore only the old focus perimeter; centered labels stay resident. */
void ui_scene_border(uint8_t item) BANKED {
 const uint8_t *map=scene_maps[prior_scene][prior_frame];
 uint8_t y,left=(item&1u)?10:0,top=(item&2u)?10:4;
 map+=(uint16_t)(top-4)*20u+left;
 vsync();
 set_bkg_tiles(left,top,10,1,map);set_bkg_tiles(left,top+6,10,1,map+120);
 for(y=1;y<6;++y){set_bkg_tile_xy(left,top+y,map[y*20u]);set_bkg_tile_xy(left+9,top+y,map[y*20u+9]);}
}
