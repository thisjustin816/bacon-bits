"""Small libretro driver for scripted SameBoy checks, with direct memory maps."""
import ctypes as c
from pathlib import Path
from PIL import Image
class Variable(c.Structure):_fields_=[('key',c.c_char_p),('value',c.c_char_p)]
class Descriptor(c.Structure):
 _fields_=[('flags',c.c_uint64),('ptr',c.c_void_p),('offset',c.c_size_t),('start',c.c_size_t),('select',c.c_size_t),('disconnect',c.c_size_t),('length',c.c_size_t),('space',c.c_char_p)]
class MemoryMap(c.Structure):_fields_=[('descriptors',c.POINTER(Descriptor)),('count',c.c_uint)]
class Game(c.Structure):_fields_=[('path',c.c_char_p),('data',c.c_void_p),('size',c.c_size_t),('meta',c.c_char_p)]
ENV=c.CFUNCTYPE(c.c_bool,c.c_uint,c.c_void_p)
VIDEO=c.CFUNCTYPE(None,c.c_void_p,c.c_uint,c.c_uint,c.c_size_t)
AUDIO=c.CFUNCTYPE(None,c.c_int16,c.c_int16)
BATCH=c.CFUNCTYPE(c.c_size_t,c.POINTER(c.c_int16),c.c_size_t)
POLL=c.CFUNCTYPE(None)
INPUT=c.CFUNCTYPE(c.c_int16,c.c_uint,c.c_uint,c.c_uint,c.c_uint)
RUMBLE=c.CFUNCTYPE(c.c_bool,c.c_uint,c.c_uint,c.c_uint16)
class SameBoy:
 BUTTONS={'b':0,'select':2,'start':3,'up':4,'down':5,'left':6,'right':7,'a':8}
 def __init__(self,core,rom,model='Game Boy Color'):
  self.lib=c.CDLL(str(core));self.held=set();self.maps={};self.image=None;self.frame=0;self.transitions=[];self.samples=[];self.model=model.encode();self.directory=b'/tmp';self.pixel_format=1
  self.callbacks=[ENV(self.environment),VIDEO(self.video),AUDIO(lambda l,r:None),BATCH(self.audio),POLL(lambda:None),INPUT(self.input),RUMBLE(self.rumble)]
  for name,callback in zip(['environment','video_refresh','audio_sample','audio_sample_batch','input_poll','input_state'],self.callbacks):getattr(self.lib,'retro_set_'+name)(callback)
  self.lib.retro_load_game.argtypes=[c.POINTER(Game)];self.lib.retro_load_game.restype=c.c_bool
  self.lib.retro_get_memory_data.argtypes=[c.c_uint];self.lib.retro_get_memory_data.restype=c.c_void_p
  self.lib.retro_init();self.rom_data=c.create_string_buffer(Path(rom).read_bytes());self.path=str(rom).encode()
  assert self.lib.retro_load_game(c.byref(Game(self.path,c.cast(self.rom_data,c.c_void_p),len(self.rom_data)-1,None)))
 def environment(self,command,data):
  command &=0xffff
  if command==10:self.pixel_format=c.cast(data,c.POINTER(c.c_int))[0];return True
  if command in [9,31]:c.cast(data,c.POINTER(c.c_char_p))[0]=self.directory;return True
  if command==15:
   var=c.cast(data,c.POINTER(Variable)).contents
   values={b'sameboy_model':self.model,b'sameboy_color_correction_mode':b'disabled',b'sameboy_high_pass_filter_mode':b'off',b'sameboy_rumble':b'rumble-enabled games'}
   if var.key in values:var.value=values[var.key];return True
   return False
  if command==17:c.cast(data,c.POINTER(c.c_bool))[0]=False;return True
  if command==23:c.cast(data,c.POINTER(c.c_void_p))[0]=c.cast(self.callbacks[-1],c.c_void_p);return True
  if command==36:
   m=c.cast(data,c.POINTER(MemoryMap)).contents
   self.maps={int(d.start):(int(d.ptr or 0)+int(d.offset),int(d.length)) for d in m.descriptors[:m.count]};return True
  if command in [18,16,11,37,35,65,69]:return True
  return False
 def video(self,ptr,w,h,pitch):
  if ptr:
   assert self.pixel_format==1,self.pixel_format
   self.image=Image.frombytes('RGB',(w,h),c.string_at(ptr,pitch*h),'raw','BGRX',pitch).copy()
 def audio(self,ptr,count):
  if self.capture:self.samples.append(c.string_at(ptr,count*4))
  return count
 def input(self,port,device,index,button):return int(button in self.held) if port==0 else 0
 def rumble(self,port,effect,strength):
  on=bool(strength)
  if not self.transitions or self.transitions[-1][1]!=on:self.transitions.append((self.frame,on))
  return True
 capture=False
 def tick(self,n=1,check=None):
  for _ in range(n):
   self.lib.retro_run();self.frame+=1
   if check:check(self)
 def press(self,key,n=8):self.held={self.BUTTONS[key]};self.tick(n);self.held=set();self.tick(12)
 def chord(self):self.held={0,2,3,8};self.tick(8);self.held=set();self.tick(12)
 def read(self,address,size=1):
  for start,(pointer,length) in self.maps.items():
   if pointer and start<=address and address+size<=start+length:return c.string_at(pointer+address-start,size)
  raise KeyError(hex(address))
 def vram(self):return c.string_at(self.lib.retro_get_memory_data(3),0x4000)
 def close(self):self.lib.retro_unload_game();self.lib.retro_deinit()
