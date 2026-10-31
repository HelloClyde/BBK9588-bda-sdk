"""Compile the header to real MIPS and exercise optional original V2.32 ROMs.

The native CIM init/config/start/IRQ/close code executes unchanged. Allocator,
interrupt registration, cache maintenance and the SCCB sensor boundary are
explicit models. This is an ABI/lifecycle test, not a sensor or DMA simulation.
Set BBK9688_FIRMWARE_JZ4730/JZ4740 to local raw/64-byte wrapped firmware.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

from elftools.elf.elffile import ELFFile
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn.mips_const import (
    UC_MIPS_REG_A0, UC_MIPS_REG_A1, UC_MIPS_REG_A2, UC_MIPS_REG_A3,
    UC_MIPS_REG_CP0_STATUS, UC_MIPS_REG_PC, UC_MIPS_REG_RA,
    UC_MIPS_REG_SP, UC_MIPS_REG_V0,
)
from bda_compile_c import bundled_prefix, find_tool
from test_9688_platform import PlatformModel, LOAD_BASE, RUNTIME_BASE, ENTRY, ROOT, n

HARNESS = r"""
#include "bda_9688_camera.h"
bda_9688_context_t context;
bda_9688_camera_t camera;
bda_9688_camera_frame_t frame;
int test_probe(void) { return bda_9688_probe(&context); }
int test_init(void) { return bda_9688_camera_init(&camera, &context); }
int test_open(void) { return bda_9688_camera_open_qvga(&camera); }
int test_start(void) { return bda_9688_camera_start(&camera); }
int test_poll(void) { return bda_9688_camera_poll(&camera, &frame); }
int test_close(void) { return bda_9688_camera_close(&camera); }
int test_state(void) { return (int)camera.state; }
int test_convert(const u8 *a,u32 size,u16 *b,u32 capacity,u32 w,u32 h) {
 return bda_9688_camera_yuyv_to_rgb565(a,size,b,capacity,w,h);
}
int test_null(void) { return bda_9688_camera_init(0, &context); }
"""

CONTRACT = {
    4730: dict(init=0x80225C68, close=0x8022569C, start=0x8022572C,
               irq=0x80225E44, number=18, slot=0x804A9EF4, default=0x80004D74,
               opened=0x808ADF44, device=0x808ADF48, done=0x808ADF40, ui=0x804B5B34,
               alloc=0x80006EB8, free=0x80006074, cache=0x80004150,
               log=0x8000518C, register=0x80004A34, unregister=0x80004B64,
               sensor_probe=0x80226E70, sensor_init=0x80226E54, sensor_write=0x80226DF8,
               gate=0x800000, i2c_gate=0x100),
    4740: dict(init=0x80222CF8, close=0x802226DC, start=0x8022276C,
               irq=0x80222ED4, number=17, slot=0x804AA22C, default=0x800052E4,
               opened=0x806FA424, device=0x806FA428, done=0x806FA420, ui=0x804B8844,
               alloc=0x80007688, free=0x80006844, cache=0x80004264,
               log=0x800098E4, register=0x800050A8, unregister=0x800051C4,
               sensor_probe=0x80222430, sensor_init=0x80222414, sensor_write=0x802223B8,
               gate=0x200, i2c_gate=8),
}
BYTES, DEVICE, BUFFER = 153600, 0x80900000, 0x80A00000


class CameraModel(PlatformModel):
    def __init__(self, binary, symbols, raw=None, tables=None, chip=4740):
        super().__init__(binary, symbols, raw, tables)
        self.chip, self.f = chip, CONTRACT[chip]
        self.u.mem_map(0x10000000, 0x20000)
        self.u.mem_map(0x13060000, 0x1000)
        self.u.mem_map(0x10042000, 0x1000)
        self.calls, self.allocations, self.freed, self.sensor_writes = [], [], [], []
        self.fail_allocation, self.sensor_present = 0, True
        self.hardware_writes = []
        self.write32(self.f['slot'], self.f['default'])
        self.write32(self.f['slot'] + 4, 0x12345678)
        # Model a booted board, including unrelated bits to preserve on close.
        self.initial = {0xB0000020: 0xA500AAAA | self.f['gate'] | self.f['i2c_gate'],
                        0xB0001004: 0xF0F0F0F0 | (1 << self.f['number']),
                        0xB3060000: 0x12345678, 0xB3060004: 0x40,
                        0xB3060020: 0x123400, 0xB0042004:0x40,0xB004200C:0x1234}
        if chip == 4730:
            self.initial.update({0xB0010020: 0x12345678, 0xB0010004: 0xB2345678,
                                 0xB0010014: 0xC2345678, 0xB0010000: 0xD2345678})
        else:
            self.initial.update({address: 0x5A5A5A5A for address in
                                 (0xB0010340, 0xB0010350, 0xB0010360, 0xB0010310, 0xB0010330)})
        for address, value in self.initial.items(): self.write32(address, value)
        self.boundaries = {self.f[key]: key for key in
                           ('alloc', 'free', 'cache', 'log', 'register', 'unregister',
                            'sensor_probe', 'sensor_init', 'sensor_write')}
        # Observe only explicit modeled OS/SCCB call boundaries. A global code
        # hook would invoke Python for every instruction in the independent
        # product-signature scan without adding any model assertions.
        for address in self.boundaries:
            self.u.hook_add(UC_HOOK_CODE, self.native_boundary, begin=address, end=address)
        # Model only these MMIO regions. This does not fix Unicorn's separate
        # MIPS JAL/delay-slot store hook limitation (debug runtime regression).
        self.u.hook_add(UC_HOOK_MEM_WRITE, self.mmio_write, begin=0xB0000000, end=0xB001FFFF)
        self.u.hook_add(UC_HOOK_MEM_WRITE, self.mmio_write, begin=0xB3060000, end=0xB3060FFF)
        self.u.hook_add(UC_HOOK_MEM_READ, self.cim_read, begin=0xB3060000, end=0xB3060FFF)
        self.u.hook_add(UC_HOOK_MEM_READ, self.i2c_read, begin=0xB0042000, end=0xB0042FFF)
        self.u.hook_add(UC_HOOK_MEM_WRITE, self.mmio_write, begin=0xB0042000, end=0xB0042FFF)

    def read32(self, address): return struct.unpack('<I', self.get(address, 4))[0]
    def write32(self, address, value): self.put(address, struct.pack('<I', value & 0xFFFFFFFF))

    def cim_read(self, uc, access, address, size, value, unused):
        if self.read32(0xB0000020) & self.f['gate']:
            raise AssertionError('CIM register read before its clock is enabled')

    def i2c_read(self, uc, access, address, size, value, unused):
        if self.read32(0xB0000020) & self.f['i2c_gate']:
            raise AssertionError('I2C register read before its clock is enabled')

    def mmio_write(self, uc, access, address, size, value, unused):
        address = (address & 0x1FFFFFFF) | 0xA0000000
        if address == 0xB0001008:
            self.write32(0xB0001004, self.read32(0xB0001004) | value)
        elif address == 0xB000100C:
            self.write32(0xB0001004, self.read32(0xB0001004) & ~value)
        elif self.chip == 4740 and 0xB0010300 <= address < 0xB0010380:
            if address & 0xF in (4, 8):
                base = address & ~0xF
                current = self.read32(base)
                self.write32(base, current | value if address & 0xF == 4 else current & ~value)
        if (0xB0000000 <= address < 0xB0020000 or 0xB3060000 <= address < 0xB3061000 or
                0xB0042000 <= address < 0xB0043000):
            self.hardware_writes.append((address, size, value))

    def native_boundary(self, uc, address, size, unused):
        key = self.boundaries.get(address)
        if key is None: return
        args = [uc.reg_read(register) for register in
                (UC_MIPS_REG_A0, UC_MIPS_REG_A1, UC_MIPS_REG_A2, UC_MIPS_REG_A3)]
        self.calls.append((key, args))
        result = 0
        if key == 'alloc':
            self.allocations.append(args[0])
            if self.fail_allocation != len(self.allocations):
                result = DEVICE if len(self.allocations) % 2 else BUFFER
        elif key == 'free':
            if self.read32(0xB3060004) & 5:
                raise AssertionError('native freed memory while CIM DMA/capture active')
            self.freed.append(args[0])
        elif key == 'register':
            if args[0] != self.f['number']: raise AssertionError('wrong CIM IRQ')
            self.write32(self.f['slot'], args[1]); self.write32(self.f['slot']+4, args[2])
            self.write32(0xB0001004, self.read32(0xB0001004) & ~(1 << args[0]))
        elif key == 'unregister':
            if args[0] != self.f['number']: raise AssertionError('wrong CIM IRQ')
            self.write32(self.f['slot'], self.f['default']); self.write32(self.f['slot']+4, 0)
            self.write32(0xB0001004, self.read32(0xB0001004) | (1 << args[0]))
        elif key == 'sensor_probe': result = int(self.sensor_present)
        elif key == 'sensor_init':
            descriptor = struct.unpack('<10I', self.get(args[0], 40))
            if descriptor != (2,320,240,0,0,0,0,0,0,0):
                raise AssertionError('unexpected sensor descriptor')
        elif key == 'sensor_write': self.sensor_writes.append(tuple(args[:2]))
        if key.startswith('sensor_'):
            # Each modeled SCCB boundary applies the real enable/disable helper's
            # side effect; this checks restoration without pretending to model a sensor.
            self.put(0xB004200C,struct.pack('<H',6))
            self.put(0xB0042004,bytes([self.read32(0xB0042004)&0xFE]))
        uc.reg_write(UC_MIPS_REG_V0, result)
        uc.reg_write(UC_MIPS_REG_PC, uc.reg_read(UC_MIPS_REG_RA))

    def call(self, name, *arguments):
        sentinel, stack = 0x81BF1000, 0x81B80000
        self.u.reg_write(UC_MIPS_REG_SP, stack)
        self.u.reg_write(UC_MIPS_REG_RA, sentinel)
        for register, value in zip((UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3), arguments):
            self.u.reg_write(register, value & 0xFFFFFFFF)
        for index, value in enumerate(arguments[4:]): self.write32(stack+16+index*4, value)
        self.u.emu_start(self.symbols.get(name, name), sentinel, count=100_000_000)
        if self.u.reg_read(UC_MIPS_REG_PC) != sentinel: raise AssertionError('MIPS function did not return')
        value = self.u.reg_read(UC_MIPS_REG_V0)
        return value - 0x100000000 if value >= 0x80000000 else value


class CameraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        prefix = os.environ.get('BDA_TOOLCHAIN_PREFIX') or bundled_prefix() or 'mipsel-none-elf-'
        cls.gcc, cls.objcopy = find_tool(prefix,'gcc'), find_tool(prefix,'objcopy')
        cls.temporary = tempfile.TemporaryDirectory(); folder=Path(cls.temporary.name)
        source,linker,elf,raw=(folder/name for name in ('camera.c','camera.ld','camera.elf','camera.bin'))
        source.write_text(HARNESS,encoding='ascii')
        linker.write_text('ENTRY(test_probe)\nSECTIONS { . = 0x81c00020; .text : { *(.text*) } '
            '.rodata : { *(.rodata*) } .data : { *(.data*) } .bss (NOLOAD) : { *(.bss*) *(COMMON) } '
            '/DISCARD/ : { *(.MIPS.abiflags*) *(.reginfo*) *(.pdr*) *(.comment*) *(.note*) } }\n',encoding='ascii')
        result=subprocess.run([cls.gcc,'-EL','-march=mips32','-mabi=32','-msoft-float','-mno-abicalls','-G0',
            '-fno-pic','-Os','-ffreestanding','-fno-builtin','-nostdlib','-Wall','-Wextra','-Werror',
            '-Wl,--build-id=none',f'-Wl,-T,{linker}','-I',str(ROOT/'sdk/include'),str(source),'-o',str(elf)],capture_output=True,text=True)
        if result.returncode: raise RuntimeError(result.stdout+result.stderr)
        subprocess.run([cls.objcopy,'-O','binary',str(elf),str(raw)],check=True,capture_output=True)
        with elf.open('rb') as stream:
            cls.symbols={s.name:s['st_value'] for s in ELFFile(stream).get_section_by_name('.symtab').iter_symbols() if s.name}
        cls.binary=raw.read_bytes()
        cls.profiles={chip:json.loads((ROOT/f'reverse/fixtures/9688-v232-jz{chip}.json').read_text(encoding='utf8')) for chip in CONTRACT}

    @classmethod
    def tearDownClass(cls): cls.temporary.cleanup()

    def model(self, chip=None):
        if chip is None: return CameraModel(self.binary,self.symbols)
        path=os.environ.get(f'BBK9688_FIRMWARE_JZ{chip}')
        if not path:self.skipTest(f'set BBK9688_FIRMWARE_JZ{chip} to local firmware')
        raw=Path(path).read_bytes(); profile=self.profiles[chip]; expected=profile['firmware']['sha256']
        if hashlib.sha256(raw).hexdigest()!=expected: raw=raw[64:]
        self.assertEqual(hashlib.sha256(raw).hexdigest(),expected)
        seed=n(profile['macros']['FW_BDA_SEED'])-LOAD_BASE
        tables=struct.unpack_from('<8I',raw,seed)[1:6]
        model=CameraModel(self.binary,self.symbols,raw,tables,chip)
        self.assertEqual(model.call('test_probe'),0)
        self.assertEqual(model.call('test_init'),0)
        return model

    def assert_restored(self,m):
        for address,value in m.initial.items():self.assertEqual(m.read32(address),value,hex(address))
        self.assertEqual(m.read32(m.f['slot']),m.f['default'])
        self.assertEqual(m.read32(m.f['slot']+4),0x12345678)
        self.assertEqual(m.read32(m.f['opened']),0)
        self.assertEqual(m.read32(m.f['device']),0)
        self.assertEqual(m.call('test_state'),0)

    def test_unsupported_has_no_native_or_mmio_effects(self):
        m=self.model();self.assertEqual(m.call('test_probe'),-1)
        self.assertEqual(m.call('test_init'),-1);self.assertEqual(m.call('test_null'),-2)
        self.assertFalse(m.calls);self.assertFalse(m.hardware_writes)

    def test_real_rom_guard_tamper_refuses_open_before_native(self):
        for chip in CONTRACT:
            with self.subTest(chip=chip):
                m=self.model(chip);address=m.f['start']+3
                m.put(address,bytes([m.get(address,1)[0]^1]))
                self.assertEqual(m.call('test_open'),-1)
                self.assertFalse(m.calls);self.assertFalse(m.hardware_writes)

    def test_native_success_capture_irq_stable_frame_and_close(self):
        for chip in CONTRACT:
            with self.subTest(chip=chip):
                m=self.model(chip);self.assertEqual(m.call('test_open'),0)
                self.assertEqual(m.allocations,[32,BYTES+1024])
                descriptor=struct.unpack('<4I',m.get(DEVICE+16,16))
                self.assertEqual(descriptor,((DEVICE+16)&0x1FFFFFFF,BUFFER&0x1FFFFFFF,0x52052018,0x50000000|BYTES//4))
                self.assertEqual(m.call('test_init'),-3)
                m.write32(m.f['done'],1)
                self.assertEqual(m.call('test_start'),0)
                self.assertEqual(m.read32(m.f['done']),0)
                self.assertEqual(m.read32(0xB3060020),(DEVICE+16)&0x1FFFFFFF)
                self.assertEqual(sum(key=='cache' for key,args in m.calls),2)
                self.assertEqual(m.read32(0xB3060004)&5,5)
                self.assertEqual(m.call('test_start'),-5)
                self.assertEqual(m.call('test_poll'),-3)
                self.assertEqual(m.get(self.symbols['frame'],24),bytes(24))
                m.write32(m.f['done'],1) # stale flag alone cannot expose active DMA
                self.assertEqual(m.call('test_poll'),-3)
                m.write32(0xB3060008,0x10)
                m.call(m.f['irq'],0)
                self.assertEqual(m.read32(0xB3060004)&5,0)
                self.assertEqual(m.call('test_poll'),0)
                self.assertEqual(struct.unpack('<6I',m.get(self.symbols['frame'],24)),
                    ((BUFFER&0x1FFFFFFF)|0xA0000000,320,240,640,BYTES,1))
                self.assertEqual(m.call('test_start'),0) # new capture invalidates old frame
                self.assertEqual(m.call('test_close'),0) # cancellation quiesces before freeing
                self.assertEqual(m.freed,[BUFFER,DEVICE]);self.assertEqual(m.sensor_writes,[(9,0x11)])
                self.assert_restored(m);self.assertEqual(m.call('test_close'),0)
                self.assertEqual(m.call('test_poll'),-5)
                self.assertEqual(m.call('test_open'),0);self.assertEqual(m.call('test_close'),0)

    def test_allocator_failures_cleanup_and_restore(self):
        for chip in CONTRACT:
            for allocation in (1,2):
                with self.subTest(chip=chip,allocation=allocation):
                    m=self.model(chip);m.fail_allocation=allocation
                    self.assertEqual(m.call('test_open'),-4)
                    self.assertEqual(m.freed,[] if allocation==1 else [DEVICE])
                    self.assertFalse(any(k.startswith('sensor') for k,a in m.calls))
                    self.assert_restored(m)

    def test_missing_sensor_frees_everything_and_restores(self):
        for chip in CONTRACT:
            with self.subTest(chip=chip):
                m=self.model(chip);m.sensor_present=False
                self.assertEqual(m.call('test_open'),-6)
                self.assertEqual(m.freed,[BUFFER,DEVICE]);self.assert_restored(m)

    def test_busy_preflight_never_touches_existing_owner(self):
        for chip in CONTRACT:
            for key,value in (('opened',1),('device',DEVICE),('ui',1),('slot',0x80009900)):
                with self.subTest(chip=chip,key=key):
                    m=self.model(chip);m.write32(m.f[key],value)
                    self.assertEqual(m.call('test_open'),-3)
                    self.assertFalse(m.calls);self.assertFalse(m.hardware_writes)

    def test_ownership_loss_refuses_start_close_and_free(self):
        for chip in CONTRACT:
            with self.subTest(chip=chip):
                m=self.model(chip);self.assertEqual(m.call('test_open'),0)
                m.write32(m.f['device'],DEVICE+32)
                before=len(m.hardware_writes)
                self.assertEqual(m.call('test_start'),-3);self.assertEqual(m.call('test_close'),-3)
                self.assertEqual(len(m.hardware_writes),before);self.assertFalse(m.freed)

    def test_active_controller_refuses_open_and_restores_gate(self):
        for chip in CONTRACT:
            with self.subTest(chip=chip):
                m=self.model(chip);m.write32(0xB3060004,0x45)
                self.assertEqual(m.call('test_open'),-3)
                self.assertEqual(m.read32(0xB0000020),m.initial[0xB0000020])
                self.assertEqual(m.read32(0xB3060004),0x45)
                self.assertFalse(m.calls)

    def test_active_i2c_refuses_open_and_restores_both_gates(self):
        for chip in CONTRACT:
            with self.subTest(chip=chip):
                m=self.model(chip);m.write32(0xB0042004,0x41)
                self.assertEqual(m.call('test_open'),-3)
                self.assertEqual(m.read32(0xB0000020),m.initial[0xB0000020])
                self.assertEqual(m.read32(0xB0042004),0x41)
                self.assertFalse(m.calls)

    def test_unrelated_gpio_and_clock_changes_are_preserved(self):
        for chip in CONTRACT:
            with self.subTest(chip=chip):
                m=self.model(chip);self.assertEqual(m.call('test_open'),0)
                register=0xB0010004 if chip==4730 else 0xB0010360
                m.write32(register,m.read32(register)^1)
                m.write32(0xB0000020,m.read32(0xB0000020)^1)
                m.initial[register]^=1;m.initial[0xB0000020]^=1
                self.assertEqual(m.call('test_close'),0);self.assert_restored(m)

    def test_modified_device_refuses_dma_or_free_of_unknown_buffer(self):
        for chip in CONTRACT:
            for offset in (0,4,0x10,0x14,0x18,0x1C):
                with self.subTest(chip=chip,offset=offset):
                    m=self.model(chip);self.assertEqual(m.call('test_open'),0)
                    m.write32(DEVICE+offset,m.read32(DEVICE+offset)^4)
                    before=len(m.hardware_writes)
                    self.assertEqual(m.call('test_start'),-3);self.assertEqual(m.call('test_close'),-3)
                    self.assertEqual(len(m.hardware_writes),before);self.assertFalse(m.freed)

    def test_runtime_gate_or_i2c_ownership_loss_refuses_mmio_and_free(self):
        for chip in CONTRACT:
            for reason in ('gate','i2c_gate','i2c_busy'):
                with self.subTest(chip=chip,reason=reason):
                    m=self.model(chip);self.assertEqual(m.call('test_open'),0)
                    self.assertEqual(m.call('test_start'),0)
                    if reason=='i2c_busy':m.write32(0xB0042004,m.read32(0xB0042004)|1)
                    else:m.write32(0xB0000020,m.read32(0xB0000020)|m.f[reason])
                    before=len(m.hardware_writes)
                    self.assertEqual(m.call('test_poll'),-3);self.assertEqual(m.call('test_close'),-3)
                    self.assertEqual(len(m.hardware_writes),before);self.assertFalse(m.freed)

    def test_converter_matches_native_coefficients_and_bounds(self):
        m=self.model();source,dest=0x81BD0000,0x81BE0000
        data=bytes((0,128,255,128,100,20,180,240))
        m.put(source,data)
        self.assertEqual(m.call('test_convert',source,len(data),dest,4,4,1),0)
        expected=[]
        for offset in range(0,len(data),4):
            u,v=data[offset+1]-128,data[offset+3]-128
            for y in (data[offset],data[offset+2]):
                clamp=lambda x:max(0,min(255,x>>10))
                r,g,b=clamp(y*1024+1435*v),clamp(y*1024-352*u-731*v),clamp(y*1024+1815*u+128)
                expected.append((r>>3)<<11|(g>>2)<<5|(b>>3))
        self.assertEqual(struct.unpack('<4H',m.get(dest,8)),tuple(expected))
        self.assertEqual(expected[:2],[0,65535])
        for args,error in (((source,7,dest,4,4,1),-7),((source,8,dest,3,4,1),-7),
                           ((source,8,dest,4,3,1),-2),((source,8,source,4,4,1),-2),
                           ((source,8,dest+1,4,4,1),-2),((source,8,dest,4,2,0xFFFFFFFF),-7),
                           ((0,8,dest,4,4,1),-2)):
            with self.subTest(args=args):self.assertEqual(m.call('test_convert',*args),error)


if __name__=='__main__':unittest.main()
