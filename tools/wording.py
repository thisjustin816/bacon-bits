"""Case imported display strings without changing abbreviations or hex values."""
import re
ABBREVIATIONS={'APU','CPU','CGB','DMG','GBA','SGB','GB','RTC','SRAM','RAM','ROM','IR','LED','RGB','CRC','RX','TX','OAM','VBK','KEY0','KEY1','OPRI','PCM','RP','SB','IO','NE','NW','SE','SW','LR','MSB','LSB','LFSR'}
UNITS={'HZ':'Hz','KHZ':'kHz','MS':'ms','US':'us','FR':'fr','BIT':'bit','BITS':'bits','SEC':'sec'}
def display_case(value):
 if value in UNITS:return UNITS[value]
 if not re.search('[A-Z]{2}',value) or re.fullmatch('[0-9A-F /]+',value):return value
 if '_' in value or '\\' in value or '%' in value:return value
 def word(match):
  w=match[0]
  if w in ABBREVIATIONS or re.fullmatch('FF[0-9A-F]+',w):return w
  if w in UNITS:return UNITS[w]
  return w.lower()
 result=re.sub(r'\b[A-Z][A-Z0-9-]*\b',word,value)
 if result and result[0].isalpha():result=result[0].upper()+result[1:]
 return result.replace('Emu: likely','Emu likely').replace('Emu: no tells','Emu no tells')
def c_display_strings(source):
 return re.sub(r'"(?:[^"\\]|\\.)*"',lambda m:'"'+display_case(m[0][1:-1])+'"',source)
