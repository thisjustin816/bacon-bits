"""Independent LCD checks for the display diagnostic's default patterns."""
import numpy as np

def check_pattern(image, pattern, cgb):
 pixels=np.asarray(image.convert('RGB'))
 colors=np.unique(pixels.reshape(-1,3),axis=0)
 if pattern in (0,1,6):
  assert len(colors)==1,('Solid/flicker frame contains stray pixels',pattern,len(colors))
  if pattern==0:assert pixels.mean()>128,'Default solid should be white'
  if pattern==1:assert pixels.mean()<128,'One-pixel grid should be black'
 elif pattern==4:
  assert len(colors)==(32 if cgb else 4),('Ramp lost shades',cgb,len(colors))
  assert np.all(pixels==pixels[:,0:1]),'Ramp varies across a horizontal band'
  ordered=colors[np.argsort(colors.sum(axis=1))]
  for y in range(144):
   shade=(y//4)%32 if cgb else 3-(y//4)%4
   assert np.all(pixels[y]==ordered[shade]),('Ramp band/order changed',cgb,y)
 else:
  assert len(colors)==2,('Pattern lost one of its two colors',pattern,len(colors))
  dark=np.argmin(colors.sum(axis=1));ink=np.all(pixels==colors[dark],axis=2)
  y,x=np.indices(ink.shape)
  if pattern==2:expected=((x^y)&1).astype(bool)
  elif pattern==3:expected=(x&1).astype(bool)
  else:
   # Scroll has an arbitrary phase, but exactly one vertical line per 32 pixels.
   assert np.all(ink==ink[0]),'Scroll columns contain broken lines'
   assert all(ink[0,start:start+32].sum()==1 for start in range(0,129,32)), 'Scroll stripe width/spacing changed'
   return
  assert np.array_equal(ink,expected),('Incorrect raster pattern',pattern)
