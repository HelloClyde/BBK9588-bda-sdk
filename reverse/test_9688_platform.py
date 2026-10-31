"""Execute the compiled 9688 platform probe against optional original ROMs.

Set BBK9688_FIRMWARE_JZ4730/JZ4740 to raw or 64-byte wrapped local firmware.
BBK9588_FIRMWARE may point at a local C200.bin for the explicit unsupported
case. Firmware is not bundled; this checks read-only ABI identity, not sensors.
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
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_LITTLE_ENDIAN, UC_MODE_MIPS32
from unicorn.mips_const import (
    UC_MIPS_REG_A0, UC_MIPS_REG_A1, UC_MIPS_REG_A2, UC_MIPS_REG_A3,
    UC_MIPS_REG_CP0_STATUS, UC_MIPS_REG_PC, UC_MIPS_REG_RA, UC_MIPS_REG_SP, UC_MIPS_REG_V0,
)

from bda_compile_c import bundled_prefix, find_tool

ROOT = Path(__file__).resolve().parents[1]
LOAD_BASE, RUNTIME_BASE, ENTRY = 0x80004000, 0x81C00000, 0x81C00020
FIRMWARE_PATHS = {soc: os.environ.get("BBK9688_FIRMWARE_" + soc) for soc in ("JZ4730", "JZ4740")}
PROFILE_PATHS = {soc: ROOT / f"reverse/fixtures/9688-v232-{soc.lower()}.json" for soc in FIRMWARE_PATHS}

HARNESS = r"""
#include "bda_9688_platform.h"
bda_9688_context_t test_context;
int test_probe(void) { return bda_9688_probe(&test_context); }
int test_probe_null(void) { return bda_9688_probe((bda_9688_context_t *)0); }
int test_chip(void) { return test_context.profile ? (int)test_context.profile->chip : 0; }
int test_device_model(void) { return test_context.profile ? (int)test_context.profile->device_model : 0; }
int test_support_level(void) { return test_context.profile ? (int)test_context.profile->support_level : 0; }
int test_media_profile_chip(void) {
    const bda_9688_profile_t *profile = bda_9688_media_profile();
    return profile ? (int)profile->chip : 0;
}
u32 test_crc(const void *data, u32 length) { return bda_9688_crc32(data, length); }
int test_guard(u32 address, u32 length, u32 checksum) {
    bda_9688_guard_t guard = {address, length, checksum};
    return bda_9688_check_guards(&test_context, &guard, 1);
}
int test_guard_empty(void) {
    bda_9688_guard_t guard = {0, 0, 0};
    return bda_9688_check_guards(&test_context, &guard, 0);
}
"""


def n(value):
    return int(value, 0) if isinstance(value, str) else int(value)


class PlatformModel:
    def __init__(self, binary, symbols, raw=None, tables=None):
        self.symbols = symbols
        self.u = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 | UC_MODE_LITTLE_ENDIAN)
        self.u.mem_map(0, 0x2000000)
        # Only the JZ4740 Boot ROM identification marker is modeled. The OS
        # image and its product signature below remain the original firmware.
        self.u.mem_map(0x1FC00000, 0x1000)
        if tables and tables[0] == 0x8029C0A0:
            self.put(0xBFC00100, bytes(v for ch in b"JZ4740" for v in (ch, 0)))
        self.u.reg_write(UC_MIPS_REG_CP0_STATUS, 0x10000000)
        if raw is not None:
            self.put(LOAD_BASE, raw)
        self.put(ENTRY, binary)
        if tables is not None:
            self.put(RUNTIME_BASE + 4, struct.pack("<5I", *tables))

    def put(self, address, data):
        self.u.mem_write(address & 0x1FFFFFFF, bytes(data))

    def get(self, address, length):
        return bytes(self.u.mem_read(address & 0x1FFFFFFF, length))

    def call(self, name, *arguments):
        sentinel = 0x81BF1000
        self.u.reg_write(UC_MIPS_REG_SP, 0x81B80000)
        self.u.reg_write(UC_MIPS_REG_RA, sentinel)
        for register, value in zip((UC_MIPS_REG_A0, UC_MIPS_REG_A1, UC_MIPS_REG_A2, UC_MIPS_REG_A3), arguments):
            self.u.reg_write(register, value & 0xFFFFFFFF)
        self.u.emu_start(self.symbols[name], sentinel, count=100_000_000)
        if self.u.reg_read(UC_MIPS_REG_PC) != sentinel:
            raise AssertionError("compiled probe did not return")
        value = self.u.reg_read(UC_MIPS_REG_V0)
        return value - 0x100000000 if value >= 0x80000000 else value


class PlatformTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        prefix = os.environ.get("BDA_TOOLCHAIN_PREFIX") or bundled_prefix() or "mipsel-none-elf-"
        cls.gcc, cls.objcopy = find_tool(prefix, "gcc"), find_tool(prefix, "objcopy")
        cls.temporary = tempfile.TemporaryDirectory()
        cls.folder = Path(cls.temporary.name)
        source, linker, elf, raw = (cls.folder / name for name in ("probe.c", "probe.ld", "probe.elf", "probe.bin"))
        source.write_text(HARNESS, encoding="ascii")
        linker.write_text("ENTRY(test_probe)\nSECTIONS { . = 0x81c00020; .text : { *(.text*) } "
                          ".rodata : { *(.rodata*) } .data : { *(.data*) } .bss (NOLOAD) : { *(.bss*) *(COMMON) } "
                          "/DISCARD/ : { *(.MIPS.abiflags*) *(.reginfo*) *(.pdr*) *(.comment*) *(.note*) } }\n",
                          encoding="ascii")
        subprocess.run([cls.gcc, "-EL", "-march=mips32", "-mabi=32", "-msoft-float", "-mno-abicalls", "-G0",
                        "-fno-pic", "-O2", "-ffreestanding", "-fno-builtin", "-nostdlib", "-Wall", "-Wextra", "-Werror",
                        "-Wl,--build-id=none", f"-Wl,-T,{linker}", "-I", str(ROOT / "sdk/include"), str(source), "-o", str(elf)],
                       check=True, capture_output=True)
        subprocess.run([cls.objcopy, "-O", "binary", str(elf), str(raw)], check=True, capture_output=True)
        with elf.open("rb") as stream:
            cls.symbols = {symbol.name: symbol["st_value"] for symbol in
                           ELFFile(stream).get_section_by_name(".symtab").iter_symbols() if symbol.name}
        cls.binary = raw.read_bytes()
        cls.profiles = {soc: json.loads(path.read_text(encoding="utf-8")) for soc, path in PROFILE_PATHS.items()}

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def firmware(self, soc):
        if not FIRMWARE_PATHS[soc]:
            self.skipTest("set BBK9688_FIRMWARE_" + soc + " to the local firmware")
        supplied = Path(FIRMWARE_PATHS[soc]).read_bytes()
        expected = self.profiles[soc]["firmware"]["sha256"]
        raw = supplied if hashlib.sha256(supplied).hexdigest() == expected else supplied[64:]
        self.assertEqual(hashlib.sha256(raw).hexdigest(), expected)
        return raw

    def model(self, soc=None):
        if soc is None:
            return PlatformModel(self.binary, self.symbols)
        profile = self.profiles[soc]
        raw = self.firmware(soc)
        seed = n(profile["macros"]["FW_BDA_SEED"]) - LOAD_BASE
        tables = struct.unpack_from("<8I", raw, seed)[1:6]
        return PlatformModel(self.binary, self.symbols, raw, tables)

    def assert_cleared(self, model):
        self.assertEqual(model.get(self.symbols["test_context"], 24), bytes(24))

    def test_crc_vector_and_null_argument(self):
        model = self.model()
        model.put(0x81BF0000, b"123456789")
        self.assertEqual(model.call("test_crc", 0x81BF0000, 9) & 0xFFFFFFFF, 0xCBF43926)
        self.assertEqual(model.call("test_probe_null"), -2)
        self.assertEqual(model.call("test_guard_empty"), -2)

    def test_unknown_and_9588_table_seeds_return_unsupported(self):
        model = self.model()
        for tables in ((0, 0, 0, 0, 0),
                       (0x80280E60, 0x80280DD0, 0x80280C60, 0x8028169C, 0x80280D30)):
            with self.subTest(tables=tables):
                model.put(RUNTIME_BASE + 4, struct.pack("<5I", *tables))
                self.assertEqual(model.call("test_probe"), -1)
                self.assertEqual(model.call("test_chip"), 0)
                self.assert_cleared(model)

    def test_real_9588_rom_is_explicitly_unsupported(self):
        path = Path(os.environ.get("BBK9588_FIRMWARE", str(ROOT / "系统/数据/C200.bin")))
        if not path.is_file():
            self.skipTest("set BBK9588_FIRMWARE to a local raw C200.bin")
        raw = path.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         "02a16107b11a3281067871c6fe3d4c289c910d8dfa9924573dd87f00351d6525")
        tables = struct.unpack_from("<8I", raw, 0x80281680 - LOAD_BASE)[1:6]
        model = PlatformModel(self.binary, self.symbols, raw, tables)
        self.assertEqual(model.call("test_probe"), -1)
        self.assert_cleared(model)

    def test_real_4730_probe_and_private_guard(self):
        self.check_real_probe("JZ4730")

    def test_real_4740_probe_and_private_guard(self):
        self.check_real_probe("JZ4740")

    def check_real_probe(self, soc):
        model = self.model(soc)
        self.assertEqual(model.call("test_probe"), 0)
        self.assertEqual(model.call("test_chip"), int(soc[2:]))
        region = self.profiles[soc]["guards"][0]
        address, length, checksum = (n(region[key]) for key in ("address", "length", "crc32"))
        self.assertEqual(model.call("test_guard", address, length, checksum), 0)
        original = model.get(address + 3, 1)
        model.put(address + 3, bytes([original[0] ^ 1]))
        self.assertEqual(model.call("test_guard", address, length, checksum), -1)
        self.assertEqual(model.call("test_guard", 0xB3040000, 4, 0), -7)
        self.assertEqual(model.call("test_guard", address, 0, 0), -7)

    def test_each_imported_table_is_required_and_failed_probe_clears_context(self):
        for soc in self.profiles:
            for index in range(5):
                with self.subTest(soc=soc, index=index):
                    model = self.model(soc)
                    self.assertEqual(model.call("test_probe"), 0)
                    address = RUNTIME_BASE + 4 + index * 4
                    original = struct.unpack("<I", model.get(address, 4))[0]
                    model.put(address, struct.pack("<I", original ^ 4))
                    self.assertEqual(model.call("test_probe"), -1)
                    self.assert_cleared(model)

    def test_single_changed_rom_seed_byte_is_rejected(self):
        for soc in self.profiles:
            with self.subTest(soc=soc):
                model = self.model(soc)
                seed = n(self.profiles[soc]["macros"]["FW_BDA_SEED"])
                original = model.get(seed + 31, 1)
                model.put(seed + 31, bytes([original[0] ^ 1]))
                self.assertEqual(model.call("test_probe"), -1)
                self.assert_cleared(model)

    def test_public_profile_maturity_and_independent_hardware_gate(self):
        for soc, maturity in (("JZ4730", 1), ("JZ4740", 2)):
            with self.subTest(soc=soc):
                model = self.model(soc)
                self.assertEqual(model.call("test_probe"), 0)
                self.assertEqual(model.call("test_device_model"), 9688)
                self.assertEqual(model.call("test_support_level"), maturity)
                self.assertEqual(model.call("test_media_profile_chip"), int(soc[2:]))
                # A matching ROM/table binding must not bypass a contradictory
                # independent hardware result. Flip only the Boot ROM marker.
                marker = bytes(v for ch in b"JZ4740" for v in (ch, 0))
                model.put(0xBFC00100, bytes(len(marker)) if soc == "JZ4740" else marker)
                self.assertEqual(model.call("test_probe"), -1)
                self.assert_cleared(model)
                self.assertEqual(model.call("test_media_profile_chip"), 0)

    def test_matching_tables_with_missing_product_signature_are_rejected(self):
        for soc in self.profiles:
            with self.subTest(soc=soc):
                model = self.model(soc)
                raw = self.firmware(soc)
                signature = raw.find(b"9688 OS")
                self.assertGreaterEqual(signature, 0)
                model.put(LOAD_BASE + signature, b"UNKNOWN")
                self.assertEqual(model.call("test_probe"), -1)
                self.assert_cleared(model)

    def test_forged_other_chip_seeds_do_not_match_rom(self):
        for soc in self.profiles:
            with self.subTest(soc=soc):
                model = self.model(soc)
                other = "JZ4730" if soc == "JZ4740" else "JZ4740"
                macros = self.profiles[other]["macros"]
                names = ("FW_GUI_TABLE", "FW_FS_TABLE", "FW_SYS_TABLE", "FW_MEM_TABLE", "FW_RES_TABLE")
                model.put(RUNTIME_BASE + 4, struct.pack("<5I", *(n(macros[name]) for name in names)))
                self.assertEqual(model.call("test_probe"), -1)
                self.assert_cleared(model)


if __name__ == "__main__":
    unittest.main()
