"""Compiled 9688 recording ABI/state tests and real-ROM WAV writer execution.

Set BBK9688_FIRMWARE_JZ4730/JZ4740 to original raw or 64-byte wrapped ROMs.
No microphone, DMA, filesystem, or hardware is operated. The native writer
checks replace libc/OS boundaries with explicit in-memory models, while the
actual firmware record open, buffer writer, encoder, and close execute in MIPS.
"""
from __future__ import annotations
import hashlib,json,os,struct,subprocess,unittest
from pathlib import Path
from elftools.elf.elffile import ELFFile
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE
from unicorn.mips_const import *
from test_9688_platform import PlatformModel,LOAD_BASE,RUNTIME_BASE,ENTRY,n
from bda_compile_c import bundled_prefix,find_tool
ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/"build/9688-media/recording-tests"
HARNESS=r"""
#include "bda_9688_recording.h"
bda_9688_context_t platform;
bda_9688_recorder_t recorders[2];
bda_9688_recording_status_t statuses[2];
u32 config[10] = {1,1,1,1,0,1,0,1,0,0};
u32 seen[8], counters[5], native_state;
int test_init(u32 index) { int r=bda_9688_probe(&platform); return r?r:bda_9688_recorder_init(&recorders[index],&platform); }
int test_open(u32 index,const char *path) { return bda_9688_recorder_open(&recorders[index],path); }
int test_start(u32 index) { return bda_9688_recorder_start(&recorders[index]); }
int test_stop(u32 index) { return bda_9688_recorder_stop(&recorders[index]); }
int test_poll(u32 index) { return bda_9688_recorder_poll(&recorders[index],&statuses[index]); }
int test_finish(u32 index) { return bda_9688_recorder_finish(&recorders[index]); }
int test_emit(u32 handle,u32 error) { if(seen[4]) ((void(*)(u32,u32))seen[4])(handle,error);return 0; }
int test_field(u32 index,u32 field) {
 bda_9688_recorder_t *r=&recorders[index];
 switch(field){case 0:return r->state;case 1:return r->handle;case 2:return r->completed;
 case 3:return r->native_error;case 4:return r->format.format_tag;case 5:return r->format.bits_per_sample;
 case 6:return (u32)bda_9688_recording_registry.owner;case 7:return bda_9688_recording_registry.handle;
 case 8:return statuses[index].elapsed_ms;case 9:return statuses[index].state;default:return -1;}
}
int test_native_open(u32 *d) { counters[0]++; for(unsigned i=0;i<8;i++)seen[i]=d[i];d[3]=16000;native_state=1;return config[0]; }
int test_native_close(u32 h) { counters[1]++;seen[6]=h;return config[1]; }
int test_native_start(u32 h,u32 *w) { counters[2]++;seen[7]=*w;native_state=0;
 if(config[4]&1) { test_emit(h,config[8]); } return config[2]; }
int test_native_stop(u32 h) { counters[3]++;native_state=1;
 if(config[4]&2) { test_emit(h,config[8]); } return config[3]; }
int test_native_info(u32 h,u32 *info) { counters[4]++;
 for(unsigned i=0;i<8;i++)info[i]=0;
 info[0]=h?config[7]:config[6];info[1]=native_state;info[3]=128;
 if(h && (config[4]&4)) { test_emit(h,config[8]); } return config[5]; }
"""

class RecordingModel(PlatformModel):
 def call(self,name,*arguments):
  sentinel=0x81bf1000;self.u.reg_write(UC_MIPS_REG_SP,0x81b80000);self.u.reg_write(UC_MIPS_REG_RA,sentinel)
  for register,value in zip((UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3),arguments):self.u.reg_write(register,value&0xffffffff)
  self.u.emu_start(self.symbols[name],sentinel,count=100000000)
  if self.u.reg_read(UC_MIPS_REG_PC)!=sentinel:raise AssertionError("MIPS function did not return: "+name)
  v=self.u.reg_read(UC_MIPS_REG_V0);return v-0x100000000 if v>=0x80000000 else v
 def word(self,address):return struct.unpack("<I",self.get(address,4))[0]
 def setword(self,address,value):self.put(address,struct.pack("<I",value&0xffffffff))
 def configure(self,index,value):self.setword(self.symbols["config"]+4*index,value)
 def field(self,index,field):return self.call("test_field",index,field)
 def count(self,index):return self.word(self.symbols["counters"]+4*index)
 def activate(self):self.setword(self.symbols["native_state"],2)
 def install_api_model(self,table):
  for offset,name in ((0,"open"),(4,"close"),(0x14,"start"),(0x20,"stop"),(0x2c,"info")):
   self.setword(table+offset,self.symbols["test_native_"+name])
  self.put(0x81bf0000,b"A:/test.wav\0")

class RecordingTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  BUILD.mkdir(parents=True,exist_ok=True);prefix=os.environ.get("BDA_TOOLCHAIN_PREFIX") or bundled_prefix() or "mipsel-none-elf-"
  source,linker,elf,binary=[BUILD/name for name in ("harness.c","harness.ld","harness.elf","harness.bin")]
  source.write_text(HARNESS,encoding="ascii")
  linker.write_text("ENTRY(test_init)\nSECTIONS { . = 0x81c00020; .text : { *(.text*) } .rodata : { *(.rodata*) } .data : { *(.data*) } .bss (NOLOAD) : { *(.bss*) *(COMMON) } /DISCARD/ : { *(.MIPS.abiflags*) *(.reginfo*) *(.pdr*) *(.comment*) *(.note*) } }\n",encoding="ascii")
  cmd=[find_tool(prefix,"gcc"),"-EL","-march=mips32","-mabi=32","-msoft-float","-mno-abicalls","-G0","-fno-pic","-Os","-ffreestanding","-fno-builtin","-nostdlib","-Wall","-Wextra","-Werror","-Wl,--build-id=none",f"-Wl,-T,{linker}","-I",str(ROOT/"sdk/include"),str(source),"-o",str(elf)]
  subprocess.run(cmd,check=True,capture_output=True);subprocess.run([find_tool(prefix,"objcopy"),"-O","binary",str(elf),str(binary)],check=True,capture_output=True)
  with elf.open("rb") as stream:
   e=ELFFile(stream);cls.symbols={s.name:s["st_value"] for s in e.get_section_by_name(".symtab").iter_symbols() if s.name}
   cls.registry_section=e.get_section(next(s["st_shndx"] for s in e.get_section_by_name(".symtab").iter_symbols() if s.name=="bda_9688_recording_registry"))["sh_type"]
  cls.binary=binary.read_bytes()
 @classmethod
 def firmware(cls,chip):
  path=os.environ.get(f"BBK9688_FIRMWARE_JZ{chip}")
  if not path:raise unittest.SkipTest(f"set BBK9688_FIRMWARE_JZ{chip} to the local firmware")
  data=Path(path).read_bytes();profile=json.loads((ROOT/f"reverse/fixtures/9688-v232-jz{chip}.json").read_text(encoding="utf-8"));expected=profile["firmware"]["sha256"]
  raw=data if hashlib.sha256(data).hexdigest()==expected else data[64:]
  if hashlib.sha256(raw).hexdigest()!=expected:raise AssertionError("wrong firmware")
  return raw,profile
 def model(self,chip=4740,install=True):
  raw,p=self.firmware(chip);seed=n(p["macros"]["FW_BDA_SEED"])-LOAD_BASE;tables=struct.unpack_from("<8I",raw,seed)[1:6]
  m=RecordingModel(self.binary,self.symbols,raw,tables)
  # The caller's uninitialized storage may contain arbitrary bytes.
  m.put(self.symbols["recorders"],bytes([0xa5])*256)
  self.assertEqual(m.call("test_init",0),0)
  if install:m.install_api_model(tables[2])
  return m,tables[2]
 def start(self,m):
  self.assertEqual(m.call("test_open",0,0x81bf0000),0);self.assertEqual(m.call("test_start",0),0)
 def test_aggregate_header_links_when_recording_is_unused_os_and_o2(self):
  source,linker=BUILD/"aggregate-unused.c",BUILD/"aggregate-unused.ld"
  source.write_text('#include "bda_9688_media.h"\nint bda_main(void) { return 0; }\n',encoding="ascii")
  linker.write_text("ENTRY(bda_main)\nSECTIONS { . = 0x81c00020; .text : { *(.text*) } .rodata : { *(.rodata*) } .data : { *(.data*) } .bss (NOLOAD) : { *(.bss*) *(COMMON) } /DISCARD/ : { *(.MIPS.abiflags*) *(.reginfo*) *(.pdr*) *(.comment*) *(.note*) } }\n",encoding="ascii")
  gcc=find_tool(os.environ.get("BDA_TOOLCHAIN_PREFIX") or bundled_prefix() or "mipsel-none-elf-","gcc")
  for optimization in ("-Os","-O2"):
   with self.subTest(optimization=optimization):
    output=BUILD/("aggregate-unused-"+optimization[1:]+".elf")
    result=subprocess.run([gcc,"-EL","-march=mips32","-mabi=32","-msoft-float","-mno-abicalls","-G0","-fno-pic",optimization,"-ffreestanding","-fno-builtin","-nostdlib","-Wall","-Wextra","-Werror","-Wl,--build-id=none",f"-Wl,-T,{linker}","-I",str(ROOT/"sdk/include"),str(source),"-o",str(output)],capture_output=True)
    self.assertEqual(result.returncode,0,result.stderr.decode(errors="replace"))
    with output.open("rb") as stream:
     elf=ELFFile(stream)
     self.assertTrue(any(s.name=="bda_9688_recording_registry" for s in elf.get_section_by_name(".symtab").iter_symbols()))
 def test_registry_is_initialized_progbits_and_unknown_platform_rejected(self):
  self.assertEqual(self.registry_section,"SHT_PROGBITS")
  m=RecordingModel(self.binary,self.symbols)
  self.assertEqual(m.call("test_init",0),-1)
  self.assertEqual(m.call("test_open",0,0x81bf0000),-2)
 def test_real_rom_guards_and_codec_metadata_both_chips(self):
  for chip,codec,bits in ((4730,17,4),(4740,1,16)):
   with self.subTest(chip=chip):
    m,_=self.model(chip,False);self.assertEqual(m.field(0,4),codec);self.assertEqual(m.field(0,5),bits)
    address=0x80196530 if chip==4730 else 0x80192be0;m.put(address,bytes([m.get(address,1)[0]^1]))
    self.assertEqual(m.call("test_init",1),-1)
 def test_open_descriptor_exclusive_ownership_and_never_started_cleanup(self):
  m,_=self.model();self.assertEqual(m.call("test_open",0,0x81bf0000),0)
  d=struct.unpack("<8I",m.get(self.symbols["seen"],32));self.assertEqual(d[:4],(5,2,0x81bf0000,16000));self.assertNotEqual(d[4],0);self.assertEqual(d[5:],(0,0,0))
  self.assertEqual(m.call("test_init",0),-3);self.assertEqual(m.call("test_open",0,0x81bf0000),-5)
  self.assertEqual(m.call("test_finish",0),0);self.assertEqual(m.count(1),1);self.assertEqual(m.field(0,6),0)
  self.assertEqual(m.call("test_finish",0),-5);self.assertEqual(m.count(1),1)
 def test_busy_media_and_open_failure_never_claim_registry(self):
  m,_=self.model();m.configure(6,1);self.assertEqual(m.call("test_open",0,0x81bf0000),-3);self.assertEqual(m.count(0),0)
  m.configure(6,0);m.configure(0,0);self.assertEqual(m.call("test_open",0,0x81bf0000),-4);self.assertEqual(m.field(0,6),0);self.assertEqual(m.count(1),0)
 def test_pending_start_cannot_be_stopped_or_freed_before_completion(self):
  m,_=self.model();self.start(m);self.assertEqual(m.call("test_stop",0),-3);self.assertEqual(m.count(3),0);self.assertEqual(m.call("test_finish",0),-3)
  m.activate();self.assertEqual(m.call("test_poll",0),0);self.assertEqual(m.field(0,9),4);self.assertEqual(m.field(0,8),128)
  self.assertEqual(m.call("test_stop",0),0);self.assertEqual(m.call("test_finish",0),-3);self.assertEqual(m.count(1),0)
  self.assertEqual(m.call("test_stop",0),0);self.assertEqual(m.count(3),1)
  self.assertEqual(m.call("test_emit",1,7),0);self.assertEqual(m.call("test_poll",0),0);self.assertEqual(m.field(0,9),6);self.assertEqual(m.field(0,3),7)
  self.assertEqual(m.call("test_finish",0),0);self.assertEqual(m.count(1),1)
 def test_unknown_callback_handle_does_not_close_or_complete_owned_context(self):
  m,_=self.model();self.start(m);self.assertEqual(m.call("test_emit",2,9),0);self.assertEqual(m.field(0,2),0);self.assertEqual(m.count(1),0)
 def test_completion_during_start_query_or_stop_is_preserved(self):
  for event in (1,2,4):
   with self.subTest(event=event):
    m,_=self.model();m.configure(4,event);m.configure(8,10);self.start(m)
    if event==2:m.activate();self.assertEqual(m.call("test_stop",0),0)
    if event==4:self.assertEqual(m.call("test_poll",0),0)
    self.assertEqual(m.field(0,2),1);self.assertEqual(m.field(0,3),10);self.assertEqual(m.call("test_finish",0),0)
 def test_completion_is_published_in_return_delay_slot_without_c_epilogue(self):
  m,_=self.model();self.start(m)
  callback=m.word(self.symbols["seen"]+16)
  code=m.get(callback,128)
  self.assertIn(struct.pack("<2I",0x03e00008,0xad090048),code)
  # Emulate the actual callback return to its ROM continuation. At the first
  # externally observable PC after done, no instruction in this BDA remains.
  continuation=0x80190c30
  m.u.reg_write(UC_MIPS_REG_RA,continuation)
  m.u.reg_write(UC_MIPS_REG_A0,1);m.u.reg_write(UC_MIPS_REG_A1,12)
  m.u.emu_start(callback,continuation,count=1000)
  self.assertEqual(m.u.reg_read(UC_MIPS_REG_PC),continuation)
  self.assertEqual(m.field(0,2),1);self.assertEqual(m.field(0,3),12)
 def test_start_stop_and_close_failures_keep_ownership_safe(self):
  m,_=self.model();self.assertEqual(m.call("test_open",0,0x81bf0000),0);m.configure(2,0);self.assertEqual(m.call("test_start",0),-4);self.assertEqual(m.field(0,0),2)
  m.configure(2,1);self.assertEqual(m.call("test_start",0),0);m.activate();m.configure(3,0);self.assertEqual(m.call("test_stop",0),-4);self.assertEqual(m.field(0,0),4)
  self.assertEqual(m.call("test_emit",1,0),0);m.configure(1,0);self.assertEqual(m.call("test_finish",0),-4);self.assertEqual(m.field(0,1),0);self.assertEqual(m.field(0,6),0)
  self.assertEqual(m.call("test_finish",0),-5);self.assertEqual(m.count(1),1)
 def test_two_contexts_cannot_replace_the_callback_owner(self):
  m,table=self.model(install=False);self.assertEqual(m.call("test_init",1),0);m.install_api_model(table)
  self.assertEqual(m.call("test_open",0,0x81bf0000),0);self.assertEqual(m.call("test_open",1,0x81bf0000),-3);self.assertEqual(m.call("test_emit",1,0),0);self.assertEqual(m.field(0,2),1);self.assertEqual(m.field(1,2),0)
 def test_actual_native_start_stop_getinfo_abi_both_chips(self):
  for chip in (4730,4740):
   with self.subTest(chip=chip):
    raw,_=self.firmware(chip);m=NativeRecordModel(chip,raw)
    desc,path,parameters,out=0x80700000,0x80701000,0x80701800,0x80701900
    m.put(path,b"A:/state.wav\0");m.put(parameters,bytes(4))
    m.put(desc,struct.pack("<8I",5,2,path,8000,0x80710000,0,0,0))
    self.assertEqual(m.call("open",desc),0)
    if chip==4740:
     slot,active,info_table=0x808a34f0,0x804a9dd0,0x808a34e4
     start,stop,info,backend_info,silent,post=0x8018efd0,0x8018f124,0x8018f210,0x80193198,0x801914f8,0x80198f10
    else:
     slot,active,info_table=0x80a61ad0,0x804a9b14,0x80a61ac4
     start,stop,info,backend_info,silent,post=0x80192e58,0x80194bec,0x80192f74,0x80196b50,0x80194e98,0x8019cdf0
    m.put(slot,struct.pack("<15I",0,5,2,1,384,0,0,0,16000,0,0,0,0x80710000,0,0))
    m.put(active,struct.pack("<I",0xffffffff));m.put(info_table,struct.pack("<I",backend_info))
    for address,name in ((silent,"silent"),(post,"post")):
     m.put(address,struct.pack("<2I",0x03e00008,0));m.u.hook_add(UC_HOOK_CODE,m.stub,name,begin=address,end=address)
    m.a.update(record_start=start,record_stop=stop,record_info=info)
    self.assertEqual(m.call("record_start",1,parameters),1)
    self.assertEqual(m.word(slot+12),0)
    self.assertTrue(any(c[0]=="post" and c[1:3]==[0,128] for c in m.calls))
    # This is why the wrapper must not stop a pending start: no completion.
    self.assertEqual(m.call("record_stop",1),1);self.assertEqual(m.word(slot+12),1)
    m.put(slot+12,struct.pack("<I",2));m.put(active,bytes(4))
    self.assertEqual(m.call("record_stop",1),1);self.assertEqual(m.word(slot+12),1)
    m.put(slot+16,struct.pack("<I",384))
    self.assertEqual(m.call("record_info",1,out),1)
    self.assertEqual(m.word(out),1);self.assertEqual(m.word(out+4),1)
    self.assertEqual(m.word(out+12),384)
 def test_actual_native_wav_writer_4740(self):self.native_writer(4740)
 def test_actual_native_wav_writer_4730(self):self.native_writer(4730)
 def native_writer(self,chip):
  raw,_=self.firmware(chip);m=NativeRecordModel(chip,raw);report=m.run()
  self.assertEqual(report["format_tag"],17 if chip==4730 else 1);self.assertEqual(report["sample_rate"],16000);self.assertEqual(report["channels"],1)
  self.assertEqual(report["data_bytes"],8192 if chip==4730 else 32768);self.assertEqual(report["file_bytes"],report["data_bytes"]+60)

class NativeRecordModel:
 def __init__(self,chip,raw):
  self.chip=chip;self.raw=raw;self.u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);self.u.mem_map(0,0x2000000);self.put(0x80004000,self.raw);self.u.reg_write(UC_MIPS_REG_CP0_STATUS,0x10000000);self.calls=[];self.file=bytearray();self.position=0;self.blocks=[]
  if chip==4740:
   self.a=dict(open=0x80192be0,close=0x80192e8c,write=0x80193068,slots=0x804fa690,alloc=0x80007688,memset=0x80006c20,memcpy=0x80006c48,debug=0x800098e4,space=0x80192b4c,count=0x80192b9c,fopen=0x80179da8,fwrite=0x80183d64,fseek=0x8017a4e0,ftell=0x80183e50,fclose=0x80183b60,free=0x80006844,flush=0x80183c9c)
  else:
   self.a=dict(open=0x80196530,close=0x801967dc,write=0x80196978,slots=0x804f21f0,alloc=0x80006eb8,memset=0x80006450,memcpy=0x80006478,debug=0x8000518c,space=0x8019649c,count=0x801964ec,fopen=0x80179638,fwrite=0x80183504,fseek=0x80179d70,ftell=0x801835f0,fclose=0x80183300,free=0x80006074,flush=0x8018343c)
  for name in ("alloc","memset","memcpy","debug","space","count","fopen","fwrite","fseek","ftell","fclose","free","flush"):
   address=self.a[name];self.put(address,struct.pack("<2I",0x03e00008,0));self.u.hook_add(UC_HOOK_CODE,self.stub,name,begin=address,end=address)
 def put(self,a,d):self.u.mem_write(a&0x1fffffff,bytes(d))
 def get(self,a,n):return bytes(self.u.mem_read(a&0x1fffffff,n))
 def word(self,a):return struct.unpack("<I",self.get(a,4))[0]
 def cstr(self,a):return self.get(a,256).split(bytes(1),1)[0].decode("gbk",errors="replace")
 def stub(self,u,address,size,name):
  a,b,c,d=[u.reg_read(x) for x in (UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3)];v=0
  if name!="debug":self.calls.append([name,a,b,c,d])
  if name=="alloc":v=0x80600000;self.put(v,bytes(a))
  elif name=="memset":self.put(a,bytes([b&255])*c);v=a
  elif name=="memcpy":self.put(a,self.get(b,c));v=a
  elif name=="space":v=1
  elif name=="count":v=0x1000000
  elif name=="fopen":self.path=self.cstr(a);self.mode=self.cstr(b);v=0x12340000
  elif name=="fwrite":
   data=self.get(a,b*c);self.blocks.append(data.hex());end=self.position+len(data)
   if len(self.file)<end:self.file.extend(bytes(end-len(self.file)))
   self.file[self.position:end]=data;self.position=end;v=c
  elif name=="fseek":self.position=b;v=0
  elif name=="ftell":v=self.position
  elif name=="fclose":v=0
  u.reg_write(UC_MIPS_REG_V0,v)
 def call(self,name,*args):
  stack,ret=0x81d00000,0x81d01000;self.u.reg_write(UC_MIPS_REG_SP,stack);self.u.reg_write(UC_MIPS_REG_RA,ret)
  for reg,a in zip((UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3),args):self.u.reg_write(reg,a)
  self.u.emu_start(self.a[name],ret,count=10000000)
  if self.u.reg_read(UC_MIPS_REG_PC)!=ret:raise RuntimeError(hex(self.u.reg_read(UC_MIPS_REG_PC)))
  return self.u.reg_read(UC_MIPS_REG_V0)
 def run(self):
  desc,path,pcm=0x80700000,0x80701000,0x80702000;self.put(path,b"A:/test.wav\0");self.put(desc,struct.pack("<8I",5,2,path,8000,0x80710000,0,0,0));self.put(pcm,struct.pack("<2048h",*range(-1024,1024)))
  handle=self.call("open",desc);native=self.word(self.a["slots"]+4*handle);assert handle==0 and native==0x80600000;assert self.word(desc+12)==16000
  for _ in range(8):assert self.call("write",handle,pcm,4096)>=4096
  before_close=len(self.file);result=self.call("close",handle);assert result==1;assert self.word(self.a["slots"]+4*handle)==0
  header=bytes(self.file[:60]);assert header[:4]==b"RIFF" and header[8:12]==b"WAVE" and header[52:56]==b"data"
  report=dict(chip=self.chip,raw_sha256=hashlib.sha256(self.raw).hexdigest(),path=self.path,mode=self.mode,actual_rate=self.word(desc+12),open_native_index=handle,close_return=result,bytes_before_close=before_close,file_bytes=len(self.file),header=header.hex(),fmt_size=struct.unpack_from("<I",header,16)[0],format_tag=struct.unpack_from("<H",header,20)[0],channels=struct.unpack_from("<H",header,22)[0],sample_rate=struct.unpack_from("<I",header,24)[0],byte_rate=struct.unpack_from("<I",header,28)[0],block_align=struct.unpack_from("<H",header,32)[0],bits=struct.unpack_from("<H",header,34)[0],data_bytes=struct.unpack_from("<I",header,56)[0],write_sizes=[len(bytes.fromhex(x)) for x in self.blocks],calls=self.calls)
  BUILD.mkdir(parents=True,exist_ok=True);(BUILD/f"native-wav-{self.chip}.json").write_text(json.dumps(report,indent=2));return report


if __name__=="__main__":unittest.main()
