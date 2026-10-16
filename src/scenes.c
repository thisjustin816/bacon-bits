#pragma bank 6
#include "bb.h"
#include "scene_data.h"
static uint8_t prior_scene=255,prior_frame;
void ui_scene_reset(void) BANKED {prior_scene=255;}
void ui_scene_redraw(void) BANKED {prior_frame=255;}
void ui_scene(uint8_t scene,uint8_t frame) BANKED {
 const uint8_t *size=scene_sizes[scene],*map=scene_maps[scene][frame&3u],*old;
 uint8_t x,y;uint16_t n=0;
 if(prior_scene!=scene){set_bkg_data(UI_ART,size[0],scene_tiles[scene]);old=0;}
 else old=prior_frame==255?0:scene_maps[scene][prior_frame];
 for(y=0;y<size[4];++y)for(x=0;x<size[3];++x){if(!old || map[n]!=old[n])ui_cell(size[1]+x,size[2]+y,map[n]);++n;}
 prior_scene=scene;prior_frame=frame&3u;
}
