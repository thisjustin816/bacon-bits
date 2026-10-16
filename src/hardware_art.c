#pragma bank 1
#include "bb.h"
#include "hardware_data.h"
static uint16_t revision=65535;
static uint8_t scene_before=255,frame_before;
static uint8_t updates[32][3];
void ui_hardware(uint8_t scene,uint8_t frame) BANKED {
 const uint8_t *map=hardware_maps[scene][frame&3u],*old=0;uint8_t x,y,n=0,count=0,i;
 if(scene_before!=scene || revision!=ui_revision){set_bkg_data(UI_ART,hardware_sizes[scene],hardware_tiles[scene]);}
 else old=hardware_maps[scene][frame_before];
 for(y=6;y<14;++y)for(x=1;x<19;++x){
  if(!old)ui_cell(x,y,map[n]);
  else if(map[n]!=old[n]){updates[count][0]=x;updates[count][1]=y;updates[count++][2]=map[n];}
  ++n;
 }
 if(count){vsync();for(i=0;i<count;++i)set_bkg_tile_xy(updates[i][0],updates[i][1],updates[i][2]);}
 scene_before=scene;frame_before=frame&3u;revision=ui_revision;
}
