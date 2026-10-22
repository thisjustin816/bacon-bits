#pragma bank 7
#include "bb.h"
#include "focus_data.h"
static uint8_t prior_item;
void ui_focus(uint8_t item,uint8_t fresh) BANKED {
 const uint8_t *map,*tiles;uint8_t y,i,tile[16],left=(item&1u)?10:0,top=(item&2u)?10:4,variant=selected_test>=8?(item<2u?item+4u:item):((selected_test/4u)==1u && !(item&1u))?6u+(item>>1):item;
 if(!fresh && item==prior_item)return;
 if(!fresh){
  ui_scene_border(prior_item);
  if(_cpu==CGB_TYPE){VBK_REG=1;fill_bkg_rect((prior_item&1u)?11:1,(prior_item&2u)?11:5,8,5,0);VBK_REG=0;}
 }
 tiles=focus_tiles[variant];
 bb_tiles_dirty|=UI_TILES_BORROWED;
 if(_cpu==CGB_TYPE){set_bkg_data(UI_FOCUS,8,tiles);set_bkg_data(UI_FOCUS_EXTRA,4,tiles+128);}
 else for(y=0;y<12;++y){
  for(i=0;i<16;i+=2){tile[i+1]=tiles[y*16u+i+1];tile[i]=tiles[y*16u+i]&tile[i+1];}
  set_bkg_data(y<8?UI_FOCUS+y:UI_FOCUS_EXTRA+y-8,1,tile);
 }
 vsync();
 map=focus_maps[variant];
 set_bkg_tiles(left,top,10,1,map);set_bkg_tiles(left,top+6,10,1,map+20);
 for(y=1;y<6;++y){set_bkg_tile_xy(left,top+y,map[8+y*2]);set_bkg_tile_xy(left+9,top+y,map[9+y*2]);}
 if(_cpu==CGB_TYPE){VBK_REG=1;fill_bkg_rect(left+1,top+1,8,5,3);VBK_REG=0;}
 prior_item=item;
}
