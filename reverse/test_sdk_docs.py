from __future__ import annotations

import os
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SDK_HEADER = ROOT / "reverse" / "bda_research_sdk.h"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def public_sdk_text() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "sdk" / "include").rglob("*.h"))
    )


class SdkDocsTest(unittest.TestCase):
    def test_sdk_layout_is_split_from_reverse_workspace(self) -> None:
        self.assertTrue((ROOT / "reverse" / "bda_research_sdk.h").is_file())
        for header in [
            "bda_sdk.h",
            "bda_types.h",
            "bda_hardware.h",
            "bda_memory.h",
            "bda_filesystem.h",
            "bda_input.h",
            "bda_time.h",
            "bda_window.h",
            "bda_graphics.h",
            "bda_dialogs.h",
            "bda_controls.h",
            "bda_audio.h",
            "bda/detail/runtime.h",
        ]:
            self.assertTrue((ROOT / "sdk" / "include" / header).is_file(), header)
        self.assertTrue((ROOT / "docs" / "README.md").is_file())
        self.assertTrue((ROOT / "example" / "README.md").is_file())
        sdk_files = sorted(
            path.relative_to(ROOT / "sdk").as_posix()
            for path in (ROOT / "sdk").rglob("*")
            if path.is_file()
        )
        self.assertEqual(
            sdk_files,
            [
                "include/bda/detail/runtime.h",
                "include/bda_audio.h",
                "include/bda_controls.h",
                "include/bda_dialogs.h",
                "include/bda_filesystem.h",
                "include/bda_graphics.h",
                "include/bda_hardware.h",
                "include/bda_input.h",
                "include/bda_memory.h",
                "include/bda_sdk.h",
                "include/bda_time.h",
                "include/bda_types.h",
                "include/bda_window.h",
            ],
        )
        self.assertFalse((ROOT / "reverse" / "sdk").exists())

        public_docs = sorted(path.name for path in (ROOT / "docs").glob("*.md"))
        self.assertEqual(
            public_docs,
            [
                "README.md",
                "compatibility.md",
                "gam4980_sdk_optimization.md",
                "getting_started.md",
                "minesweeper_v1.md",
                "releasing.md",
                "sdk_api_layout.md",
            ],
        )
        verified_docs = sorted(path.name for path in (ROOT / "docs" / "verified").glob("*.md"))
        self.assertEqual(
            verified_docs,
            [
                "README.md",
                "audio_capture_api.md",
                "audio_pcm_api.md",
                "controls_api.md",
                "direct_framebuffer_api.md",
                "file_management_api.md",
                "file_selector_api.md",
                "fs_flush_api.md",
                "fs_write_api.md",
                "game_rendering_api.md",
                "graphics_primitives_api.md",
                "hardware_detection_api.md",
                "help_page_api.md",
                "high_resolution_timer_api.md",
                "input_polling_api.md",
                "msgbox_api.md",
                "picture_rendering_api.md",
                "public_api_policy.md",
                "raw_input_event_api.md",
                "runtime_services_api.md",
                "touch_position_api.md",
                "touch_window_lifecycle_api.md",
                "window_timer_api.md",
            ],
        )

        research_include_count = 0
        for source in (ROOT / "reverse" / "examples").glob("*.c"):
            text = source.read_text(encoding="utf-8")
            self.assertNotIn("../sdk/bda_sdk.h", text, source)
            if '#include "../bda_research_sdk.h"' in text:
                research_include_count += 1
        self.assertGreaterEqual(research_include_count, 10)

        catalog_tool = read("reverse/bda_api_catalog.py")
        system_tables = read("reverse/docs/system_api_tables.md")
        api_catalog = read("reverse/docs/api_catalog.md")
        generated_tables = system_tables + "\n" + api_catalog
        c200_table_tool = read("reverse/c200_api_tables.py")
        c200_disasm_tool = read("reverse/c200_api_disasm.py")
        sdk_readme = read("docs/sdk_api_layout.md")
        self.assertIn("# SDK API 目录", sdk_readme)
        self.assertIn("只保存动态验证后公开的 API", sdk_readme)
        for header in [
            "bda_sdk.h",
            "bda_hardware.h",
            "bda_memory.h",
            "bda_filesystem.h",
            "bda_input.h",
            "bda_time.h",
            "bda_window.h",
            "bda_graphics.h",
            "bda_dialogs.h",
            "bda_controls.h",
            "bda_audio.h",
        ]:
            self.assertIn(header, sdk_readme)
        self.assertIn("reverse/bda_research_sdk.h", sdk_readme)
        self.assertIn("example/README.md", sdk_readme)
        self.assertIn("[开发者文档](README.md)", sdk_readme)
        self.assertIn('#include "bda_sdk.h"', sdk_readme)
        self.assertIn('#include "bda_graphics.h"', sdk_readme)
        self.assertIn('#include "bda_input.h"', sdk_readme)
        self.assertIn('#include "bda_time.h"', sdk_readme)
        self.assertIn('#include "bda_window.h"', sdk_readme)
        self.assertIn('Path("reverse") / "bda_research_sdk.h"', catalog_tool)
        self.assertIn('Path("reverse") / "docs" / "api_catalog.md"', catalog_tool)
        self.assertIn('Path("reverse") / "bda_research_sdk.h"', c200_table_tool)
        self.assertIn('Path("reverse") / "docs" / "system_api_tables.md"', c200_table_tool)
        self.assertIn('Path("reverse") / "bda_research_sdk.h"', c200_disasm_tool)

    def test_front_door_docs_keep_common_computer_terms(self) -> None:
        combined = read("docs/sdk_api_layout.md") + "\n" + read("reverse/docs/README.md")
        for phrase in [
            "## Entry Function",
            "MIPS little-endian toolchain",
            "entry offset",
            "VX icon block",
            "运行 unit tests",
            "历史 misnames",
            "坐标/rect helper",
            "file read 示例",
            "开发者 docs entry",
            "emulator app 逆向",
            "verification_notes.md",
            "C200 API 表生成失败会让 verify 失败",
            "-SkipToolchainSetup -Emu",
        ]:
            self.assertIn(phrase, combined)
        for phrase in [
            "入口函数",
            "MIPS little-endian 工具链",
            "入口 offset",
            "VX 图标块",
            "运行单元测试",
            "历史误名",
            "坐标/矩形 helper",
            "文件读取示例",
            "开发者文档入口",
            "模拟器应用逆向",
        ]:
            self.assertNotIn(phrase, combined)

    def test_direct_framebuffer_api_is_guarded_and_documented(self) -> None:
        graphics = read("sdk/include/bda_graphics.h")
        runtime = read("sdk/include/bda/detail/runtime.h")
        verified = read("docs/verified/direct_framebuffer_api.md")
        example = read(
            "example/graphics/direct_framebuffer/direct_framebuffer_demo.c"
        )

        self.assertIn(
            "#define BDA_SDK_INTERNAL_GUI_SCREEN_BUFFER     0x6b0u",
            runtime,
        )
        self.assertIn(
            "#define BDA_SDK_INTERNAL_GUI_SCREEN_ORIENTATION      0x738u",
            runtime,
        )
        for name in [
            "bda_gui_framebuffer_t",
            "bda_gui_framebuffer_acquire",
            "bda_gui_framebuffer_present_rgb565",
            "BDA_GUI_FRAMEBUFFER_WIDTH",
            "BDA_GUI_FRAMEBUFFER_HEIGHT",
            "BDA_GUI_FRAMEBUFFER_STRIDE_BYTES",
            "BDA_GUI_FRAMEBUFFER_SIZE_BYTES",
        ]:
            self.assertIn(name, graphics)
            self.assertIn(name, verified + "\n" + example)
        for guard in [
            "physical == 0u",
            "(physical & 3u) != 0u",
            "physical > 0x20000000u - BDA_GUI_FRAMEBUFFER_SIZE_BYTES",
            "orientation != 0x130u",
            "orientation != 0x131u",
            "0xa0000000u | physical",
            '__asm__ volatile("sync"',
        ]:
            self.assertIn(guard, graphics)
        self.assertNotIn("0x01f82000u", graphics)
        self.assertIn("不固定 framebuffer 物理地址", verified)
        self.assertNotIn("bda_sdk_internal_", example)
        self.assertIn("5ebf5d14d0fbb7ee257001117a24ee57077672967bf22de17bc0ad263cc77462", verified)
        self.assertIn("单缓冲", verified)
        self.assertIn("必须回退", verified)

    def test_public_dialog_header_matches_verified_scope(self) -> None:
        header = read("sdk/include/bda_dialogs.h")
        base_header = read("sdk/include/bda_sdk.h")
        docs = read("docs/verified/msgbox_api.md")
        example = read(
            "example/system/three_button_dialog/three_button_dialog_demo.c"
        )

        self.assertIn('#include "bda_memory.h"', header)
        self.assertIn('#include "bda/detail/runtime.h"', header)
        self.assertNotIn("_like", header.lower())
        self.assertNotIn("static inline int bda_msgbox(", base_header)
        for name in [
            "bda_msgbox_ex",
            "bda_msgbox",
            "bda_confirm",
            "bda_confirm_yes_all_no",
            "BDA_MSGBOX_TYPE_OK",
            "BDA_MSGBOX_TYPE_YES_NO",
            "BDA_MSGBOX_TYPE_YES_ALL_NO",
            "BDA_DIALOG_RESULT_YES",
            "BDA_DIALOG_RESULT_ALL",
            "BDA_DIALOG_RESULT_NO",
        ]:
            self.assertIn(name, header)
            self.assertIn(name, docs)
        self.assertIn('#include "bda_dialogs.h"', example)
        self.assertIn("bda_confirm_yes_all_no", example)
        self.assertIn("msgbox_yes_all_no_verified.png", docs)
        log = read("docs/verified/assets/msgbox_yes_all_no_probe_log.txt")
        self.assertIn("LEFT=0x00000006", log)
        self.assertIn("MIDDLE=0x0000000A", log)
        self.assertIn("RIGHT=0x00000007", log)

    def test_public_controls_header_matches_verified_scope(self) -> None:
        header = read("sdk/include/bda_controls.h")
        docs = read("docs/verified/controls_api.md") + "\n" + read(
            "docs/tutorials/custom_controls.md"
        )

        self.assertIn('#include "bda_types.h"', header)
        self.assertIn('#include "bda/detail/runtime.h"', header)
        self.assertNotIn("_like", header.lower())
        self.assertNotIn('"treeview"', header)
        self.assertNotIn('"SLIDERCTRL"', header)
        self.assertIn("treeview", docs)
        self.assertIn("SLIDERCTRL", docs)

        functions = sorted(
            set(
                re.findall(
                    r"^static inline [^\n]+?\b(bda_[A-Za-z0-9_]+)\s*\(",
                    header,
                    re.M,
                )
            )
        )
        defines = sorted(
            set(re.findall(r"^#define\s+(BDA_[A-Z0-9_]+)\b", header, re.M))
        )
        self.assertGreaterEqual(len(functions), 20)
        self.assertGreaterEqual(len(defines), 30)
        self.assertEqual([name for name in functions if name not in docs], [])
        self.assertEqual(
            [
                name
                for name in defines
                if name != "BDA_CONTROLS_H"
                and not name.startswith("BDA_CONTROLS_INTERNAL_")
                and name not in docs
            ],
            [],
        )

        for example in [
            "example/gui/control_gallery/control_gallery_demo.c",
            "example/gui/custom_control/custom_control_demo.c",
            "example/gui/gif_player/gif_player_demo.c",
        ]:
            source = read(example)
            self.assertIn('#include "bda_controls.h"', source)
            self.assertNotIn("bda_sdk_internal_", source)

        skin_probe = read("reverse/examples/control_skin_binding_probe.c")
        for name in [
            "bda_medit_set_background_vx",
            "bda_medit_set_draw_object",
            "bda_listbox_set_background_vx",
            "bda_listbox_set_draw_object",
        ]:
            self.assertIn(name, header)
            self.assertIn(name, docs)
            self.assertIn(name, skin_probe)
        self.assertIn("controls_skin_binding_v2.png", docs)
        self.assertIn("RESULT=PASS", read(
            "docs/verified/assets/controls_skin_binding_v2_log.txt"
        ))

    def test_help_page_is_public_and_documented(self) -> None:
        header = read("sdk/include/bda_dialogs.h")
        base_header = read("sdk/include/bda_sdk.h")
        verified = read("docs/verified/help_page_api.md")
        verified_index = read("docs/verified/README.md")
        policy = read("docs/verified/public_api_policy.md")
        example = read("example/system/help_page/help_page_demo.c")
        scanner = read("reverse/bda_api_scan.py")
        log = read("docs/verified/assets/help_page_probe_log.txt")

        for name in [
            "BDA_HELP_PAGE_TITLE_MAX_BYTES",
            "BDA_HELP_PAGE_ERROR",
            "BDA_HELP_PAGE_COMPLETED",
            "bda_help_page",
        ]:
            self.assertIn(name, header)
            self.assertIn(name, verified)

        self.assertIn("BDA_DIALOGS_INTERNAL_GUI_HELP_PAGE", header)
        self.assertNotIn("bda_help_page", base_header)
        self.assertIn("GUI+0x5a8", verified)
        self.assertIn("不会自动给调用者窗口添加问号按钮", verified)
        self.assertIn("help_page_api.md", verified_index + policy)
        self.assertIn('#include "bda_dialogs.h"', example)
        self.assertIn("bda_help_page(0,", example)
        self.assertNotIn("bda_research_sdk.h", example)
        self.assertNotIn("_like", example)
        self.assertIn("0x5A8", scanner)
        self.assertIn("RETURNED FROM GUI+0x5A8", log)
        self.assertIn("RETURNED TO PARENT", log)
        self.assertTrue(
            (ROOT / "docs/verified/assets/help_page_verified.png").is_file()
        )
        self.assertTrue(
            (ROOT / "docs/verified/assets/help_page_return_verified.png").is_file()
        )

    def test_public_audio_header_matches_verified_scope(self) -> None:
        header = read("sdk/include/bda_audio.h")
        playback_docs = read("docs/verified/audio_pcm_api.md")
        capture_docs = read("docs/verified/audio_capture_api.md")
        docs = playback_docs + "\n" + capture_docs
        playback_example = read("example/system/audio_pcm/audio_pcm_demo.c")
        capture_example = read("example/system/audio_capture/audio_capture_demo.c")

        self.assertIn('#include "bda_types.h"', header)
        self.assertIn('#include "bda/detail/runtime.h"', header)
        self.assertNotIn("_like", header.lower())
        for name in [
            "bda_audio_open_pcm",
            "bda_audio_ready",
            "bda_audio_write",
            "bda_audio_set_attenuation",
            "bda_audio_get_attenuation",
            "bda_audio_stop",
        ]:
            self.assertIn(name, header)
            self.assertIn(name, playback_docs)
            self.assertIn(name, playback_example)
        for name in [
            "bda_audio_capture_profile",
            "bda_audio_capture_open",
            "bda_audio_capture_ready",
            "bda_audio_capture_read",
            "bda_audio_capture_stop",
        ]:
            self.assertIn(name, header)
            self.assertIn(name, capture_docs)
            self.assertIn(name, capture_example)
        self.assertIn("bda_audio_capture_is_supported", header)
        self.assertIn("bda_audio_capture_is_supported", capture_docs)
        self.assertIn("bda_audio_capture_firmware", header)
        self.assertIn("bda_audio_capture_firmware", capture_docs)
        for token in [
            "BDA_AUDIO_CAPTURE_UNSUPPORTED",
            "BDA_AUDIO_CAPTURE_INVALID_ARGUMENT",
            "BDA_AUDIO_CAPTURE_INVALID_STATE",
            "BDA_AUDIO_CAPTURE_IO_ERROR",
            "BDA_AUDIO_CAPTURE_BLOCK_BYTES",
            "dc41701442176ba81bf1b8041b2f9dac449e04f2adf6532993e7c55471de9bea",
        ]:
            self.assertIn(token, header)
            self.assertIn(token, capture_docs)
        for token in [
            "BDA_AUDIO_CAPTURE_FIRMWARE_9588_JZ4720",
            "BDA_AUDIO_CAPTURE_FIRMWARE_9588_JZ4730",
            "BDA_AUDIO_CAPTURE_FIRMWARE_9588_JZ4740",
            "BDA_AUDIO_CAPTURE_FIRMWARE_9688_JZ4730",
            "BDA_AUDIO_CAPTURE_FIRMWARE_9688_JZ4740",
            "BDA_AUDIO_CAPTURE_SUPPORT_STATIC_CANDIDATE",
            "BDA_AUDIO_CAPTURE_SUPPORT_HARDWARE_VERIFIED",
            "bda_audio_internal_capture_profile_detect",
            "capture_init_takes_format",
            "0x801967f0u",
            "0x80199d4cu",
            "0x80194900u",
            "0x801a169cu",
            "0x8019e400u",
        ]:
            self.assertIn(token, header)
        self.assertIn('#include "bda_hardware.h"', header)
        self.assertIn("static u32 detection_complete", header)
        self.assertIn("BDA_AUDIO_CAPTURE_SUPPORT_STATIC_CANDIDATE", capture_docs)
        self.assertIn("静态候选", capture_docs)
        self.assertIn("bytes != BDA_AUDIO_CAPTURE_BLOCK_BYTES", header)
        self.assertIn("不会调用任何录音私有地址", capture_docs)
        self.assertIn("首次 read 会启动 DMA", capture_docs)
        self.assertIn("实时波形", capture_docs)
        self.assertIn("calculate_waveform", capture_example)
        self.assertIn("present_waveform", capture_example)
        self.assertIn("bda_gui_event_pump_frame_once", capture_example)
        self.assertIn("START AUDIO CAPTURE WAVEFORM V1", capture_example)
        self.assertIn("AUDCAP.TXT", capture_example + capture_docs)
        waveform_result = read(
            "docs/verified/assets/audio_capture_waveform_hardware_result.txt"
        )
        self.assertIn(
            "D9F27ED3A7D84DE151316AAC84E6B34C36C8A728946769515C9D0102E3979FA0",
            capture_docs + waveform_result,
        )
        self.assertIn("live waveform version is operational", waveform_result)
        self.assertIn("Pressing ESC stops capture and returns normally", waveform_result)
        self.assertIn("full 128-block", waveform_result)
        self.assertLess(
            capture_example.index("bda_audio_capture_stop(&capture)"),
            capture_example.index("close_window(&message)"),
        )
        self.assertIn("RESULT=PASS", capture_docs)
        self.assertNotIn("0x80195b24", header)
        self.assertIn("SYS+0x0a0", playback_docs)
        self.assertIn("真机", docs)
        self.assertIn("BEFORE AIC RESET", playback_docs)
        self.assertTrue(
            (ROOT / "docs/verified/assets/audio_pcm_true_hardware_v3_log.txt").is_file()
        )
        self.assertTrue(
            (ROOT / "docs/verified/assets/audio_pcm_true_hardware_v4_result.txt").is_file()
        )
        self.assertIn("02a16107b11a3281067871c6fe3d4c289", playback_docs)
        self.assertNotIn("bda_sys_audio_reset_like", header)
        self.assertNotIn("bda_sys_audio_flush_like", header)
        self.assertIn('#include "bda_audio.h"', playback_example)
        self.assertIn('#include "bda_audio.h"', capture_example)
        self.assertNotIn("bda_sdk_internal_", playback_example + capture_example)

    def test_record_stream_probe_stays_firmware_private_and_guarded(self) -> None:
        public = public_sdk_text()
        research = read("reverse/bda_research_sdk.h")
        probe = read("reverse/examples/record_stream_hardware_probe.c")
        v2 = read("reverse/examples/record_stream_hardware_probe_v2.c")
        v3 = read("reverse/examples/record_stream_hardware_probe_v3.c")
        v4 = read("reverse/examples/record_stream_hardware_probe_v4.c")
        v5 = read("reverse/examples/record_stream_hardware_probe_v5.c")
        v6 = read("reverse/examples/record_stream_hardware_probe_v6.c")
        v7 = read("reverse/examples/record_stream_hardware_probe_v7.c")
        v8 = read("reverse/examples/record_stream_hardware_probe_v8.c")
        v9 = read("reverse/examples/record_stream_hardware_probe_v9.c")
        v10 = read("reverse/examples/record_stream_hardware_probe_v10.c")
        v11 = read("reverse/examples/record_stream_hardware_probe_v11.c")
        v12 = read("reverse/examples/record_stream_hardware_probe_v12.c")
        v13 = read("reverse/examples/record_stream_hardware_probe_v13.c")
        report = read("reverse/reports/recorder_bda_report.md")
        v1_hardware_log = read(
            "reverse/reports/assets/record_stream_v1_hardware_log.txt"
        )
        v2_hardware_log = read(
            "reverse/reports/assets/record_stream_v2_hardware_log.txt"
        )
        v3_hardware_log = read(
            "reverse/reports/assets/record_stream_v3_hardware_log.txt"
        )
        v4_hardware_log = read(
            "reverse/reports/assets/record_stream_v4_hardware_log.txt"
        )
        v5_hardware_log = read(
            "reverse/reports/assets/record_stream_v5_hardware_log.txt"
        )
        v6_hardware_log = read(
            "reverse/reports/assets/record_stream_v6_hardware_log.txt"
        )
        v7_hardware_log = read(
            "reverse/reports/assets/record_stream_v7_hardware_log.txt"
        )
        v8_hardware_log = read(
            "reverse/reports/assets/record_stream_v8_hardware_log.txt"
        )
        v9_hardware_log = read(
            "reverse/reports/assets/record_stream_v9_hardware_partial_log.txt"
        )
        v10_hardware_log = read(
            "reverse/reports/assets/record_stream_v10_hardware_log.txt"
        )
        v11_hardware_log = read(
            "reverse/reports/assets/record_stream_v11_hardware_log.txt"
        )
        v12_hardware_log = read(
            "reverse/reports/assets/record_stream_v12_hardware_log.txt"
        )

        self.assertNotIn("bda_c200_record_stream", public)
        self.assertIn("bda_audio_capture_open", public)
        self.assertIn("BDA_AUDIO_CAPTURE_UNSUPPORTED", public)
        self.assertIn("local-image probes only", research)
        self.assertIn("resolve_capture_open", probe)
        self.assertIn("ready_address - 0x800u", probe)
        self.assertIn("guess - 0x20u", probe)
        self.assertIn("STRUCTURAL RESOLUTION FAILED", probe)
        self.assertIn("OPEN RESOLVED TO PLAYBACK ENTRY", probe)
        self.assertIn("analyze_capture_layout", probe)
        self.assertIn("DIAGNOSTIC ONLY; NO AUDIO CALLS", probe)
        self.assertIn("#define RECORD_STREAM_PROBE_V2 1", v2)
        self.assertIn("#define RECORD_STREAM_PROBE_V3 1", v3)
        self.assertIn("#define RECORD_STREAM_PROBE_V4 1", v4)
        self.assertIn("#define RECORD_STREAM_PROBE_V5 1", v5)
        self.assertIn("#define RECORD_STREAM_PROBE_V6 1", v6)
        self.assertIn("#define RECORD_STREAM_PROBE_V7 1", v7)
        self.assertIn("#define RECORD_STREAM_PROBE_V8 1", v8)
        self.assertIn("#define RECORD_STREAM_PROBE_V9 1", v9)
        self.assertIn("#define RECORD_STREAM_PROBE_V10 1", v10)
        self.assertIn("#define RECORD_STREAM_PROBE_V11 1", v11)
        self.assertIn("#define RECORD_STREAM_PROBE_V12 1", v12)
        self.assertIn("#define RECORD_STREAM_PROBE_V13 1", v13)
        self.assertIn("READY SIG0=0x27BDFFE8", v1_hardware_log)
        self.assertIn("READ SIG0=0xAFBE0040", v1_hardware_log)
        self.assertIn("RESULT=UNSUPPORTED", v1_hardware_log)
        self.assertIn("OPEN RESOLVED=0x80199AD0", v2_hardware_log)
        self.assertIn("READ RESOLVED=0x80199290", v2_hardware_log)
        self.assertIn("READY TIMEOUT BLOCK=0x00000000", v2_hardware_log)
        self.assertIn("NEAREST BEFORE OLD GUESS=0x80199D4C", v3_hardware_log)
        self.assertIn("JR RA ADDRESS=0x80199F00", v3_hardware_log)
        self.assertIn("RESULT=MAP_ONLY", v3_hardware_log)
        self.assertIn("OPEN RESOLVED=0x80199D4C", v4_hardware_log)
        self.assertIn("READY TIMEOUT TICKS=0x000000C8", v4_hardware_log)
        self.assertIn("RESULT=FAIL", v4_hardware_log)
        self.assertIn("CALL ADDRESS=0x8018EDB4", v5_hardware_log)
        self.assertIn("CALL OWNER PROLOGUE=0x8018EE00", v5_hardware_log)
        self.assertIn(
            "CALL WORD ADDRESS=0x8018EE48 WORD=0x24040003",
            v5_hardware_log,
        )
        self.assertIn("CALL ADDRESS=0x8018D6D8", v5_hardware_log)
        self.assertIn("RESULT=MAP_ONLY", v5_hardware_log)
        self.assertIn("CONFIG WRAPPER RETURN=0x00000000", v6_hardware_log)
        self.assertIn("READY TIMEOUT TICKS=0x000000C8", v6_hardware_log)
        self.assertIn("RESULT=FAIL", v6_hardware_log)
        self.assertIn("TRUE HARDWARE SIGNATURE FAILED", v7_hardware_log)
        self.assertIn("RESULT=UNSUPPORTED", v7_hardware_log)
        self.assertIn("HARDWARE TARGET A=", probe)
        self.assertIn("STATE REF ADDRESS=", probe)
        self.assertIn("AUDIO TARGET JAL COUNT=0x00000008", v8_hardware_log)
        self.assertIn("RESULT=MAP_ONLY", v8_hardware_log)
        self.assertIn("STATE REF ADDRESS=0x80199400", v9_hardware_log)
        self.assertNotIn("END RECORD STREAM HARDWARE PROBE V9", v9_hardware_log)
        self.assertIn("STATE REF A=0x8019A674", v10_hardware_log)
        self.assertIn("COMPACT STATE REF COUNT=0x00000056", v10_hardware_log)
        self.assertIn("END RECORD STREAM HARDWARE PROBE V10", v10_hardware_log)
        self.assertIn(
            "CALLBACK PTR A=0x80199D74 W=0x24A5A5A0",
            v11_hardware_log,
        )
        self.assertIn("CALLBACK PTR MATCHES=0x00000002", v11_hardware_log)
        self.assertIn("END RECORD STREAM HARDWARE PROBE V11", v11_hardware_log)
        self.assertIn("BLOCK=0 GOT=4096", v12_hardware_log)
        self.assertIn("BLOCK=3 GOT=4096", v12_hardware_log)
        self.assertIn("CAPTURE-SPECIFIC STOP RETURNED", v12_hardware_log)
        self.assertIn("RESULT=PASS", v12_hardware_log)
        self.assertIn("COMPACT STATE REF COUNT=", probe)
        self.assertIn("CALLBACK PTR MATCHES=", probe)
        self.assertIn("READ PRIMES DMA", probe)
        self.assertIn("BEFORE BLOCKING READ BLOCK=", probe)
        self.assertIn("BEFORE CAPTURE-SPECIFIC STOP", probe)
        self.assertIn("RECORD CONTROL CALL GRAPH", probe)
        self.assertIn("MANAGER JALR ADDRESS=", probe)
        self.assertIn("record_stream_hardware_probe_v10.c", report)
        self.assertIn("record_stream_hardware_probe_v11.c", report)
        self.assertIn("record_stream_hardware_probe_v12.c", report)
        self.assertIn("record_stream_hardware_probe_v13.c", report)
        self.assertIn("read_target[0..1]", report)
        self.assertIn("没有启动录音硬件", report)
        self.assertIn("raw playback open", report)
        self.assertIn("RESULT=MAP_ONLY", report)
        self.assertIn("BEFORE CAPTURE OPEN NOARGS", probe)
        self.assertIn("CALLERS INIT CANDIDATE", probe)
        self.assertIn("CALLERS CAPTURE READ", probe)
        self.assertIn("resolve_capture_config_wrapper_v6", probe)
        self.assertIn("BEFORE CONFIG WRAPPER 16000", probe)
        self.assertIn("e168efa236c5ee9afe7816c9c3b78a5a68699f1e381bd165babb4ecfcb514649", report)
        self.assertIn("fd50ccd5aa87c2a9fa6e4d99e573614b611608787d5edf1397d021fd21b19357", report)
        self.assertIn("c12a6ed6aacb68a695857e855e8eee5e68cb77ff9b2cc624e065bb376907cc10", report)
        self.assertIn("f2106a653494ea15ff4cb5a3d0a3bad1407dda8c8e106b69bd10af856f4b5a97", report)
        self.assertIn("ce4a540788c5b3082364d531c5246e3270b28419dda74b8082de19cd9375a7b2", report)

    def test_front_door_build_examples_use_sdk_sources(self) -> None:
        combined = read("README.md") + "\n" + read("reverse/docs/README.md")
        self.assertIn(
            "python -m bda_packer example\\basic\\hello_world\\hello_world_msgbox.c",
            combined,
        )
        self.assertIn("--icon-png", combined)
        self.assertNotIn("reverse\\examples\\notpl_demo_msgbox.c", combined)
        self.assertNotIn("reverse/examples/notpl_demo_msgbox.c", combined)

    def test_gba_notes_do_not_treat_blit_as_framebuffer_allocator(self) -> None:
        notes = read("reverse/docs/gba_notes.md")
        self.assertIn("显示输出         暂未恢复", notes)
        self.assertIn("不能直接用 GUI+0x3f8/+0x400 当 framebuffer/present API", notes)
        self.assertIn("不负责分配 framebuffer", notes)
        self.assertIn("裸 no-template BDA 直接调用这组 wrapper 会逐块 flip 并死机", notes)
        self.assertIn("先复原 game shell lifecycle", notes)
        self.assertNotIn("通过 GUI+0x3f8 wrapper 分配 320x240 RGB565", notes)

    def test_sdk_doc_readme_indexes_all_markdown_docs(self) -> None:
        readme = read("reverse/docs/README.md")
        docs = sorted((ROOT / "reverse" / "docs").glob("*.md"))
        self.assertGreater(len(docs), 10)
        for doc in docs:
            if doc.name == "README.md":
                continue
            self.assertIn(doc.name, readme)

    def test_public_sdk_functions_are_mentioned_in_sdk_docs(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        docs = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "reverse" / "docs").glob("*.md")
        )
        pattern = re.compile(r"^(?:static inline\s+)?(?:[A-Za-z_][\w\s\*]+?)\s+(bda_[A-Za-z0-9_]+)\s*\(", re.M)
        functions = sorted({match.group(1) for match in pattern.finditer(header)})
        self.assertGreaterEqual(len(functions), 100)
        missing = [name for name in functions if name not in docs]
        self.assertEqual(missing, [])

    def test_public_sdk_defines_are_mentioned_in_sdk_docs(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        docs = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "reverse" / "docs").glob("*.md")
        )
        defines = sorted({match.group(1) for match in re.finditer(r"^#define\s+(BDA_[A-Z0-9_]+)\b", header, re.M)})
        self.assertGreaterEqual(len(defines), 100)
        ignored = {"BDA_RESEARCH_SDK_H"}
        missing = [name for name in defines if name not in ignored and name not in docs]
        self.assertEqual(missing, [])

    def test_public_sdk_types_are_mentioned_in_sdk_docs(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        docs = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "reverse" / "docs").glob("*.md")
        )
        names = set()
        for match in re.finditer(r"typedef\s+[^;{]+\s+(bda_[A-Za-z0-9_]+_t)\s*;", header):
            names.add(match.group(1))
        for match in re.finditer(r"typedef\s+struct\s+(bda_[A-Za-z0-9_]+)\s*\{", header):
            names.add(match.group(1))
        for match in re.finditer(r"}\s*(bda_[A-Za-z0-9_]+_t)\s*;", header):
            names.add(match.group(1))
        for match in re.finditer(r"typedef\s+int\s*\(\*\s*(bda_[A-Za-z0-9_]+_t)\s*\)", header):
            names.add(match.group(1))
        self.assertGreaterEqual(len(names), 20)
        missing = sorted(name for name in names if name not in docs)
        self.assertEqual(missing, [])

    def test_public_sdk_struct_fields_are_mentioned_in_sdk_docs(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        docs = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "reverse" / "docs").glob("*.md")
        )
        fields = []
        for struct_match in re.finditer(
            r"typedef\s+struct\s+bda_[A-Za-z0-9_]+\s*\{(?P<body>.*?)\}\s*bda_[A-Za-z0-9_]+_t\s*;",
            header,
            re.S,
        ):
            body = struct_match.group("body")
            for line in body.splitlines():
                line = line.split("/*", 1)[0].strip()
                if not line:
                    continue
                field_match = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(?:\[[^\]]+\])?\s*;", line)
                if field_match:
                    fields.append(field_match.group(1))
        self.assertGreaterEqual(len(fields), 80)
        missing = sorted({field for field in fields if field not in docs})
        self.assertEqual(missing, [])

    def test_verified_sdk_examples_are_indexed_in_docs(self) -> None:
        test_source = read("reverse/test_sdk_examples.py")
        readme = read("reverse/docs/README.md")
        sources = sorted(set(re.findall(r'"((?:example|reverse/examples)/[A-Za-z0-9_/]+\.c)"', test_source)))
        self.assertGreaterEqual(len(sources), 10)
        for source in sources:
            self.assertIn(source, readme)
        for phrase in [
            "Verify 覆盖的 SDK 示例",
            "standalone 示例",
            "开发者应从根目录",
            "未达到公开标准的 ABI/build smoke",
        ]:
            self.assertIn(phrase, readme)

    def test_all_public_sdk_examples_are_indexed(self) -> None:
        example_readme = read("example/README.md")
        doc_readme = read("reverse/docs/README.md")
        examples = sorted((ROOT / "example").rglob("*.c"))
        self.assertGreaterEqual(len(examples), 7)
        for example in examples:
            rel = example.relative_to(ROOT).as_posix()
            self.assertIn(example.name, example_readme)
            self.assertIn(rel, doc_readme)

    def test_public_examples_are_not_duplicated_in_reverse(self) -> None:
        examples = sorted((ROOT / "example").rglob("*.c"))
        self.assertGreaterEqual(len(examples), 7)
        for example in examples:
            mirror = ROOT / "reverse" / "examples" / example.name
            self.assertFalse(mirror.exists(), example.name)

    def test_docs_do_not_reference_removed_sdk_example_directory(self) -> None:
        docs = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "docs").rglob("*.md")
        ).replace("\\", "/")
        self.assertNotIn("sdk/api/examples", docs)
        for path in [
            "example/basic/hello_world/hello_world_msgbox.c",
            "example/filesystem/fs_write/fs_write_demo.c",
            "example/input/key_polling/key_msgbox_demo.c",
            "example/input/touch_crosshair/touch_crosshair_demo.c",
            "example/graphics/primitives/graphics_primitives_demo.c",
            "example/games/minesweeper/minesweeper_bda.c",
        ]:
            self.assertIn(path, docs)

    def test_reverse_readme_indexes_core_toolchain_scripts(self) -> None:
        readme = read("reverse/README.md")
        scripts = [
            "bda_header.py",
            "bda_compile_c.py",
            "bda_validate.py",
            "bda_deploy_bundle.py",
            "config_inf_add.py",
            "config_inf_probe.py",
            "bda_set_icon_png.py",
            "bda_copy_icons.py",
            "bda_extract_icons.py",
            "bda_inventory.py",
            "bda_table_globals.py",
            "bda_table_call_scan.py",
            "bda_api_catalog.py",
            "c200_api_tables.py",
            "c200_api_disasm.py",
            "c200_menu_scan.py",
            "dlx_inspect.py",
            "dlx_extract.py",
            "dlx_build.py",
        ]
        for script in scripts:
            self.assertIn(script, readme)
        for phrase in [
            "deploy bundle",
            "Config.inf",
            "menu icon",
            "DLX resource container",
            "C200 API 表种子",
            "首页硬编码",
            "table global",
            "调用点上下文",
        ]:
            self.assertIn(phrase, readme)

    def test_bda_packer_has_an_independent_package_boundary(self) -> None:
        for relative in [
            "bda_packer/__init__.py",
            "bda_packer/__main__.py",
            "bda_packer/build.py",
            "bda_packer/header.py",
            "bda_packer/validate.py",
            "bda_packer/vx_icon.py",
            "sdk/include/bda_sdk.h",
            "bda_packer/README.md",
        ]:
            self.assertTrue((ROOT / relative).is_file(), relative)

        docs = "\n".join(
            read(path)
            for path in [
                "README.md",
                "bda_packer/README.md",
                "reverse/README.md",
                "reverse/native_toolchain_notes.md",
                "docs/README.md",
                "reverse/docs/bda_header_notes.md",
                "reverse/docs/verification_notes.md",
            ]
        )
        self.assertIn("python -m bda_packer", docs)
        self.assertIn("python -m bda_packer.validate", docs)
        self.assertNotIn("python reverse\\bda_compile_c.py", docs)
        self.assertNotIn("python reverse\\bda_validate.py", docs)

    def test_bda_packer_category_mapping_is_documented(self) -> None:
        getting_started = read("docs/getting_started.md")
        packer_readme = read("bda_packer/README.md")
        header_notes = read("reverse/docs/bda_header_notes.md")
        documents = [getting_started, packer_readme, header_notes]
        expected = {
            1: "听说",
            2: "语法",
            3: "阅读",
            4: "娱乐天地",
            5: "考试",
            6: "背诵",
            7: "词典",
            8: "娱乐",
            9: "工具",
        }
        capacities = {1: 7, 2: 5, 3: 9, 4: 10, 5: 10, 6: 8, 7: 15, 8: 10, 9: 20}
        for document in documents:
            for value, label in expected.items():
                self.assertIn(f"`{value}` | {label} | `{capacities[value]}`", document)
            self.assertIn("没有发现对应", document)
            self.assertIn("总菜单项上限", document)

        self.assertIn("游戏", getting_started)
        self.assertIn("影音", getting_started)
        self.assertIn("第 11 个 BDA", getting_started)
        self.assertIn("其他分类上限来自 C200 固件", getting_started)
        self.assertIn("0x80366444..0x803664e4", header_notes)
        self.assertIn("54 个", header_notes)
        self.assertIn("0x80366834 + category * 10", header_notes)
        self.assertIn("current_count < capacity", header_notes)

    def test_verification_notes_document_current_verify_boundary(self) -> None:
        notes = read("reverse/docs/verification_notes.md")
        readme = read("reverse/docs/README.md")
        verify_script = read("scripts/verify_sdk.ps1")

        self.assertIn("verification_notes.md", readme)
        for phrase in [
            "standalone C 编译",
            "`.bss` 零填充",
            "原版 NAND",
            "persistent worker copy",
            "`/api/files/import`",
            "`/api/files/export`",
            "`/api/files/delete`",
            "不直接修改原版 NAND",
            "`docs/verified/`",
            "静态校验通过不等于系统 API 已验证",
        ]:
            self.assertIn(phrase, notes)

        self.assertIn('$systemBin = "系统\\数据\\C200.bin"', verify_script)
        self.assertIn("Test-Path $systemBin", verify_script)
        c200_step = verify_script.split('Invoke-Step "生成 C200 API 表"', 1)[1].split('Invoke-Step "运行单元测试', 1)[0]
        self.assertNotIn("try {", c200_step)
        self.assertNotIn("catch {", c200_step)
        for obsolete in ["TimePassthrough", "bda_build.py", "--template", "run_mine_as_time_web_smoke.py"]:
            self.assertNotIn(obsolete, verify_script + "\n" + notes)

    def test_minesweeper_example_documents_standalone_runtime_limits(self) -> None:
        source = read("example/games/minesweeper/minesweeper_bda.c")
        readme = read("reverse/docs/README.md")
        mines_notes = read("docs/minesweeper_v1.md")
        window_notes = read("reverse/docs/window_notes.md")
        self.assertIn("#define BOARD_WIDTH 9", source)
        self.assertIn("#define MINE_COUNT 10", source)
        self.assertIn("bda_gui_register_frame_desc", source)
        self.assertIn("bda_gui_current_draw", source)
        self.assertIn("bda_gui_end_draw", source)
        self.assertIn("bda_gui_compatible_context_create", source)
        self.assertIn("bda_gui_compatible_context_free", source)
        self.assertIn("bda_gui_draw_vx", source)
        self.assertIn("bda_gui_context_copy", source)
        self.assertIn("bda_gui_input_packet", source)
        self.assertIn("首击安全", mines_notes)
        self.assertIn("WON TICKS=", mines_notes)
        self.assertIn("--category 4", mines_notes)
        self.assertIn("--icon-png example\\games\\minesweeper\\minesweeper_icon.png", mines_notes)
        self.assertIn("娱乐天地", mines_notes)
        self.assertNotIn("-I reverse", mines_notes)
        self.assertNotIn("_like", source)
        self.assertNotIn("_LIKE", source)
        self.assertTrue(Path("example/games/minesweeper/minesweeper_icon.png").is_file())
        self.assertTrue(
            Path("docs/assets/minesweeper_v1_entertainment_menu.png").is_file()
        )
        self.assertIn("standalone 9x9 扫雷", readme)
        self.assertIn("彻底移除雷霆模板", window_notes)
        self.assertIn("模拟器稳定等级进入公开 include", readme)
        self.assertIn("verified/game_rendering_api.md", readme)
        self.assertNotIn("0x81c0fdb8", source.lower())
        examples_test = read("reverse/test_sdk_examples.py")
        self.assertIn('"Mines"', examples_test)
        self.assertIn("test_minesweeper_example_builds", examples_test)

    def test_game_rendering_api_is_public_and_documented(self) -> None:
        stable_header = public_sdk_text()
        verified = read("docs/verified/game_rendering_api.md")
        verified_index = read("docs/verified/README.md")
        include_readme = read("docs/verified/public_api_policy.md")
        sdk_readme = read("docs/sdk_api_layout.md")
        progress = read("reverse/docs/game_api_verification_progress.md")
        source = read("example/games/minesweeper/minesweeper_bda.c")

        required_offsets = [
            "BDA_SDK_INTERNAL_GUI_END_DRAW          0x30cu",
            "BDA_SDK_INTERNAL_GUI_COMPAT_CREATE     0x310u",
            "BDA_SDK_INTERNAL_GUI_COMPAT_FREE       0x314u",
            "BDA_SDK_INTERNAL_GUI_CONTEXT_COPY      0x418u",
            "BDA_SDK_INTERNAL_GUI_DRAW_VX           0x540u",
            "BDA_SDK_INTERNAL_GUI_TICK_COUNT_25MS   0x6d8u",
        ]
        required_api = [
            "bda_gui_end_draw",
            "bda_gui_compatible_context_create",
            "bda_gui_compatible_context_free",
            "bda_gui_draw_vx",
            "bda_gui_context_copy",
            "bda_gui_tick_count_25ms",
            "bda_gui_tick_elapsed_25ms",
            "bda_gui_tick_elapsed_ms",
            "bda_gui_rgb565_avoid_black_key",
            "BDA_GUI_COLOR_KEY_BLACK_RGB565",
            "BDA_GUI_COLOR_KEY_MAGENTA_RGB565",
            "BDA_GUI_OPAQUE_BLACK_RGB565",
        ]
        for text in required_offsets:
            self.assertIn(text, stable_header)
        for text in required_api:
            self.assertIn(text, stable_header)
            self.assertIn(text, verified)

        for legacy in [
            "bda_gui_compat_context_create_like",
            "bda_gui_surface_flush_like",
            "bda_gui_context_copy_like",
            "bda_gui_draw_vx_like",
            "bda_gui_tick_count_25ms_like",
        ]:
            self.assertNotIn(legacy, stable_header)
            self.assertNotIn(legacy, source)

        for phrase in [
            "模拟器稳定公开",
            "不扩张到其他机型或固件版本",
            "draw guard 内一次 copy",
            "24 + width * height * 2",
            "153624",
            "33x32",
            "0xfffffff0 -> 0x10",
            "frame stop",
            "RGB565 `0x0000` context-copy 行为为 C200knl 真机确认",
            "当前没有验证到固件通用的“禁用色键”值",
            "旧文字、旧图标或上一帧从黑色区域透出",
            "alpha blending",
        ]:
            self.assertIn(phrase, verified)

        self.assertNotIn(
            "#define BDA_GUI_COLOR_KEY_NONE",
            stable_header,
        )
        self.assertIn(
            "#define BDA_GUI_COLOR_KEY_BLACK_RGB565 0x0000u",
            stable_header,
        )
        self.assertIn(
            "#define BDA_GUI_OPAQUE_BLACK_RGB565 0x0001u",
            stable_header,
        )
        self.assertIn("BDA_GUI_COLOR_KEY_BLACK_RGB565", source)
        self.assertGreaterEqual(verified.count("```mermaid"), 2)
        self.assertNotIn("-I reverse", verified)
        self.assertIn("game_rendering_api.md", verified_index)
        self.assertIn("game_rendering_api.md", include_readme)
        self.assertIn("game_rendering_api.md", sdk_readme)
        self.assertIn("已按“模拟器稳定”等级进入", progress)

        for asset in [
            "game_rendering_double_buffer_a.png",
            "game_rendering_double_buffer_b.png",
            "game_rendering_color_key.png",
            "game_rendering_dirty_rect.png",
            "game_rendering_minesweeper.png",
        ]:
            self.assertIn(f"assets/{asset}", verified)
            self.assertTrue((ROOT / "docs/verified/assets" / asset).is_file())

    def test_gam4980_dependencies_are_public_and_documented(self) -> None:
        stable_header = public_sdk_text()
        runtime_doc = read("docs/verified/runtime_services_api.md")
        picture_doc = read("docs/verified/picture_rendering_api.md")
        runtime_example = read(
            "example/system/runtime_services/runtime_services_demo.c"
        )
        heap_probe = read("reverse/examples/max_heap_hardware_probe.c")
        heap_hardware_log = read(
            "docs/verified/assets/max_heap_v1_hardware_log.txt"
        )
        picture_example = read(
            "example/graphics/picture_render/picture_render_demo.c"
        )

        for offset in [
            "BDA_SDK_INTERNAL_MEM_ALLOC 0x008u",
            "BDA_SDK_INTERNAL_MEM_FREE  0x00cu",
            "BDA_SDK_INTERNAL_FS_SEEK       0x010u",
            "BDA_SDK_INTERNAL_FS_CHDIR      0x02cu",
            "BDA_SDK_INTERNAL_FS_MKDIR      0x030u",
            "BDA_SDK_INTERNAL_FS_FINDFIRST  0x03cu",
            "BDA_SDK_INTERNAL_FS_FINDNEXT   0x040u",
            "BDA_SDK_INTERNAL_FS_FINDCLOSE  0x044u",
            "BDA_SDK_INTERNAL_GUI_RENDER_PICTURE    0x410u",
        ]:
            self.assertIn(offset, stable_header)

        for name in [
            "bda_alloc",
            "bda_free",
            "bda_fs_seek_raw",
            "bda_fs_chdir",
            "bda_fs_mkdir",
            "bda_fs_find_data_t",
            "bda_fs_findfirst",
            "bda_fs_findnext",
            "bda_fs_findclose",
            "bda_gui_picture_t",
            "bda_gui_render_picture",
        ]:
            self.assertIn(name, stable_header)
            self.assertIn(name, runtime_doc + picture_doc)

        self.assertNotIn("_like", stable_header.lower())
        self.assertNotIn("bda_research_sdk.h", runtime_example + picture_example)
        self.assertNotIn("_like", runtime_example + picture_example)
        self.assertIn("6ac2fc57342a89fe", runtime_doc)
        self.assertIn("4bda88ee59db295d", picture_doc)
        self.assertIn("15360 = 160 * 96", picture_doc)
        for token in [
            "11337728",
            "11403264",
            "11599872",
            "10.8125 MiB",
            "11.0625 MiB",
            "耗尽返回值 | `NULL`",
            "8c2e2e3f160ba6c0a5c37db4a1dcadf5e3dde977c1e8df3da6dc416422a8deb0",
            "84863eb890bfda7601ed578864a971d9b97c985afc52dd43688126d83c80be1f",
        ]:
            self.assertIn(token, runtime_doc)
        self.assertIn("RECOVERY_RESERVE_BYTES KIB(256)", heap_probe)
        self.assertIn("FINE_STEP_BYTES        KIB(64)", heap_probe)
        self.assertIn("PROBE_CAP_BYTES        MIB(16)", heap_probe)
        self.assertIn("touch_and_verify_pages", heap_probe)
        self.assertIn("MAX SAFE SINGLE BYTES=11337728", heap_hardware_log)
        self.assertIn(
            "FIRST FAILED CANDIDATE BYTES=11403264", heap_hardware_log
        )
        self.assertIn("RECOVERY PAGE=PASS", heap_hardware_log)
        self.assertIn("RESULT=PASS", heap_hardware_log)
        self.assertNotIn("约 6.5 MiB", runtime_doc)
        self.assertIn("真机仍需复测", picture_doc)

        for asset in [
            "max_heap_v1_hardware_log.txt",
            "runtime_services_probe_pass.png",
            "runtime_services_probe_log.txt",
            "picture_render_phase0.png",
            "picture_render_phase1.png",
            "picture_render_phase2.png",
            "picture_render_probe_log.txt",
        ]:
            self.assertTrue((ROOT / "docs/verified/assets" / asset).is_file())

    def test_file_selector_is_public_and_documented(self) -> None:
        header = read("sdk/include/bda_dialogs.h")
        base_header = read("sdk/include/bda_sdk.h")
        verified = read("docs/verified/file_selector_api.md")
        verified_index = read("docs/verified/README.md")
        policy = read("docs/verified/public_api_policy.md")
        example = read("example/system/file_selector/file_selector_demo.c")

        for name in [
            "BDA_FILE_SELECTOR_PATH_SIZE",
            "BDA_FILE_SELECTOR_ERROR",
            "BDA_FILE_SELECTOR_CANCELLED",
            "BDA_FILE_SELECTOR_SELECTED",
            "bda_file_selector_t",
            "bda_gui_select_file",
        ]:
            self.assertIn(name, header)
            self.assertIn(name, verified)

        for offset in [
            "BDA_DIALOGS_INTERNAL_GUI_FILE_SELECTOR_OPEN 0x6a8u",
            "BDA_DIALOGS_INTERNAL_GUI_LIST_NTH           0x6b8u",
            "BDA_DIALOGS_INTERNAL_GUI_LIST_FREE          0x6bcu",
            "BDA_DIALOGS_INTERNAL_GUI_FILE_SELECTOR_RUN  0x6c8u",
        ]:
            self.assertIn(offset, header)

        self.assertNotIn("bda_gui_select_file", base_header)
        self.assertIn('#include "bda_dialogs.h"', example)
        self.assertIn('"A:\\\\gameboy\\\\"', header)
        self.assertIn('"gb;gbc"', header)
        self.assertIn("GUI+0x6bc(list_head)", verified)
        self.assertIn("A:\\gameboy\\SELECT.GB", verified)
        self.assertIn("file_selector_api.md", verified_index + policy)
        self.assertIn("bda_gui_select_file", example)
        self.assertNotIn("bda_research_sdk.h", example)
        self.assertNotIn("_like", example)
        self.assertTrue(
            (ROOT / "docs/verified/assets/file_selector_verified.png").is_file()
        )
        self.assertTrue(
            (ROOT / "docs/verified/assets/file_selector_result_verified.png").is_file()
        )

    def test_gui_lifecycle_boundary_is_documented_near_public_wrappers(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        tile_probe = read("reverse/examples/tile_blit_probe.c")
        combined = header + "\n" + readme + "\n" + tile_probe
        required = [
            "event poll helper",
            "BDA_GUI_MESSAGE_SIZE(0x1c) byte buffer",
            "不能让 bare bda_main() 变成稳定 event loop",
            "不应把它当成无需 frame handle 的通用 message pump",
            "不要手写一个短 struct 后直接 dispatch",
            "在 bare bda_main()、硬编码时间入口替换或 create callback 早期阶段直接 begin_draw",
            "可能白屏、逐块刷新、重启或死机",
            "不是 frame handle",
            "不要把 bda_gui_draw_object_create_like(15)+register_frame 当成最小绘图 demo",
            "## Wrapper 使用边界",
            "低风险 smoke",
            "需要真实 lifecycle",
            "破坏性或全局状态",
            "`register_frame` 只负责把 descriptor",
            "它不是“一次调用显示 UI”的 high-level API",
            "硬编码替换",
            "header/loader smoke",
            "8x6 个 16x16 RGB565 tile",
            "逐块 flip，并在全部 tile 渲染后死机",
            "surface/context",
            "不应作为第一个 smoke",
            "bda_gui_draw_guard_begin_like();",
            "#define GRID_W 8",
            "#define GRID_H 6",
            "for (row = 0; row < GRID_H; ++row)",
            "for (col = 0; col < GRID_W; ++col)",
            "(void)bda_gui_blit_alt_like(16 + col * 18, 28 + row * 18, TILE_H, TILE_W, g_tiles[index]);",
            "bda_gui_draw_guard_end_like();",
        ]
        for text in required:
            with self.subTest(text=text):
                self.assertIn(text, combined)
        self.assertLess(tile_probe.index("bda_gui_draw_guard_begin_like();"), tile_probe.index("bda_gui_blit_alt_like"))
        self.assertLess(tile_probe.rindex("bda_gui_blit_alt_like"), tile_probe.index("bda_gui_draw_guard_end_like();"))
        self.assertEqual(tile_probe.count("bda_gui_draw_guard_end_like();"), 1)
        self.assertNotIn("register_frame 当作安全绘图入口", combined)
        self.assertNotIn("整块网格一次出现", combined)

    def test_developer_docs_use_current_wrapper_names(self) -> None:
        paths = [
            "README.md",
            "reverse/README.md",
            "reverse/native_toolchain_notes.md",
            "docs/README.md",
            "reverse/docs/fs_notes.md",
        ]
        combined = "\n".join(read(path) for path in paths)
        self.assertIn("bda_fs_close_raw", combined)
        self.assertIn("bda_fs_seek_raw", combined)
        self.assertIn("bda_alloc", combined)
        self.assertIn("bda_free", combined)
        self.assertIn("bda_header.py", combined)
        self.assertIn("bda_fix_header_checksum.py", combined)
        self.assertNotIn("bda_fs_fclose_raw", combined)
        self.assertNotIn("bda_fs_fseek_raw", combined)
        self.assertNotIn("bda_mem_alloc", combined)
        self.assertNotIn("bda_mem_free", combined)
        self.assertFalse((ROOT / "reverse" / "bda_mix_header.py").exists())
        self.assertFalse((ROOT / "reverse" / "bda_build.py").exists())

    def test_fs_notes_keep_risky_candidates_unwrapped(self) -> None:
        notes = read("reverse/docs/fs_notes.md")
        bbvm_notes = read("reverse/docs/bbvm_notes.md")
        eros_report = read("reverse/reports/eros_bda_report.md")
        linkgame_report = read("reverse/reports/linkgame_bda_report.md")
        sango_report = read("reverse/reports/sango_bda_report.md")
        video_report = read("reverse/reports/video_bda_report.md")
        header = SDK_HEADER.read_text(encoding="utf-8")
        for phrase in [
            "## 暂不公开的辅助函数",
            "FS+0x058",
            "低层 storage/boot-sector 检查",
            "不要在 SDK 中包装为普通 storage",
            "现有只读 storage ready wrapper 是 `bda_fs_storage_ready_like()`",
            "FS+0x080",
            "path/open-object 内部检查",
            "不是普通存在性检查",
            "0x80178178(temp_obj)",
            "0x8086cce0",
            "FS+0x068",
            "file-object block read helper",
            "a3 是内部 file object/descriptor",
            "0x200 byte block",
            "普通开发继续使用 `fopen/fread/fclose` 路径",
        ]:
            self.assertIn(phrase, notes)
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        self.assertIn("FS +0x068: 不公开的 file-object block read helper", c200_notes)
        self.assertIn("system function VA：`0x8017a200`", c200_notes)
        self.assertIn("a0=buffer", c200_notes)
        self.assertIn("a1=offset", c200_notes)
        self.assertIn("a2=size", c200_notes)
        self.assertIn("a3=file_object", c200_notes)
        self.assertIn("descriptor `+0x4a`", c200_notes)
        self.assertIn("0x8017fbc0(index, block, 1, stack_buf)", c200_notes)
        self.assertIn("不是 path API", c200_notes)
        self.assertIn("bda_fs_read_bytes_raw()", c200_notes)
        self.assertNotIn("FS+0x068  0x8017a200  game framework 存档相关候选，签名未解决", notes)
        self.assertIn("FS+0x068  内部 file-object block read helper", bbvm_notes)
        self.assertIn("FS +0x068  内部 file-object block read helper，不公开 SDK wrapper", eros_report)
        self.assertIn("FS +0x068  内部 file-object block read helper，不公开 SDK wrapper", linkgame_report)
        self.assertIn("FS +0x068                                      内部 file-object block read helper，不公开 SDK wrapper", sango_report)
        self.assertIn("不是 public stat/access API", video_report)
        self.assertIn("不是普通\n   文件路径 API", video_report)
        self.assertIn("不是公共存档 API", linkgame_report)
        self.assertNotIn("FS +0x068  未命名辅助", eros_report + "\n" + linkgame_report)
        self.assertNotIn("FS +0x068/+0x06c                               stat/access 类辅助", sango_report)
        self.assertNotIn("它为 FS+0x068/+0x06c 接近 access/stat 类辅助提供额外证据", sango_report)
        self.assertNotIn("`FS+0x068` 的含义；它同时出现在两个视频构建和游戏框架笔记中", video_report)
        self.assertNotIn("FS+0x018/+0x01c/+0x020/+0x028/+0x068", eros_report)
        self.assertIn("不能替代普通 `fread` wrapper", bbvm_notes)
        self.assertIn("FS +0x080: 不公开的 path/open-object 内部检查", c200_notes)
        self.assertIn("system function VA：`0x8017a708`", c200_notes)
        self.assertIn("bda_fs_path_info_like(path, info)", c200_notes)
        self.assertIn("bda_fs_stat_like(path, flags)", c200_notes)
        self.assertIn("不要把 `FS+0x080` 命名为 `bda_fs_exists_like()`", c200_notes)
        for name in [
            "BDA_FS_BOOT_SECTOR",
            "BDA_FS_CURRENT_PATH",
            "BDA_FS_EXISTS_LIKE",
            "BDA_FS_IS_FILE_LIKE",
            "bda_fs_current_path",
            "bda_fs_boot",
            "bda_fs_exists_like",
            "bda_fs_is_file_like",
        ]:
            self.assertNotIn(name, header)

    def test_bda_header_notes_document_validator_constraints(self) -> None:
        notes = read("reverse/docs/bda_header_notes.md")
        required = [
            "# BDA Header 与固件加载规则",
            "菜单扫描函数 `0x8002c4c0`",
            "启动函数 `0x8002c5b0` / `0x8002c878`",
            "前 11 个 u32 与 `0x44525744` XOR 解码",
            "0x004b4242",
            "`0x5d245562`",
            "category 低 16 位必须小于 `10`",
            "标题 `\"资源管理\"` 被菜单明确过滤",
            "version 低 16 位必须至少为 `0x0102`",
            "直接 `jalr 0x81c00020`",
            "loader 不做 relocation",
            "把 `.bss` 合并成文件里的零填充 `.data`",
            "## 唯一构建入口",
            "打包器不接受任何已有 BDA",
            "静态通过只证明文件会通过已还原的 loader 条件",
            "category 4）总容量为 10",
            "第 11 个合法 BDA 文件",
            "属于菜单索引容量边界，不是 header 校验失败",
        ]
        for phrase in required:
            self.assertIn(phrase, notes)

    def test_fs064_block_read_support_is_documented_but_not_public_wrapper(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        fs_notes = read("reverse/docs/fs_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        report = read("reverse/reports/ninecourse_bda_report.md")
        self.assertIn("FS+0x064", fs_notes)
        self.assertIn("0x8017afb4", fs_notes)
        self.assertIn("低层 block read support helper", fs_notes)
        self.assertIn("未公开的 block read support helper", c200_notes)
        self.assertIn("signed 16-bit volume/index", fs_notes + "\n" + report)
        self.assertIn("0x80175dfc(index, a1)", c200_notes)
        self.assertIn("0x8017fbc0(a0, converted_a1, a2_or_default, a3)", c200_notes)
        self.assertIn("a2=1, a3=stack+0x10", c200_notes + "\n" + report)
        self.assertIn("0x218` byte stack buffer", c200_notes + "\n" + report)
        self.assertIn("暂不在 `bda_sdk.h` 暴露 wrapper", c200_notes)
        self.assertIn("不是 path API", c200_notes)
        self.assertIn("不是普通 file handle API", c200_notes)
        self.assertIn("不是存档 API", c200_notes)
        self.assertIn("不能暴露为公共 SDK helper", report)
        self.assertNotIn("FS+0x064 未解决辅助调用", report)
        self.assertNotIn("FS+0x064` 仍未解决", report)
        self.assertNotIn("BDA_FS_064", header)
        self.assertNotIn("bda_fs_064", header)

    def test_fs06c_stat_like_does_not_claim_output_struct(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        fs_notes = read("reverse/docs/fs_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        self.assertIn("bda_fs_stat_like(const char *path, u32 flags)", header)
        self.assertIn("bda_fs_stat_like(const char *path, u32 flags);", readme)
        self.assertIn("C200 wrapper 只保存", fs_notes)
        self.assertIn("使用 `a0/a1`", fs_notes)
        self.assertIn("没有保存或读取 `a2/a3`", c200_notes)
        self.assertIn("旧的第三个 output pointer 参数", c200_notes)
        self.assertNotIn("stat_data", header + readme + fs_notes)
        self.assertNotIn("optional_output", fs_notes)

    def test_sys050_stub_is_not_public_sdk_wrapper(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        media_notes = read("reverse/docs/media_notes.md")
        game_notes = read("reverse/docs/game_framework_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        self.assertIn("SYS+0x050", media_notes)
        self.assertIn("立即返回", media_notes)
        self.assertIn("stub", game_notes)
        self.assertIn("SYS +0x024 / +0x048 / +0x04c: 不公开 stub", c200_notes)
        self.assertIn("SYS+0x024 -> 0x80187df8", c200_notes)
        self.assertIn("SYS+0x048 -> 0x801895d4", c200_notes)
        self.assertIn("SYS+0x04c -> 0x801895dc", c200_notes)
        self.assertIn("不能把后续函数体算作该 offset 的 ABI", c200_notes)
        self.assertIn("SYS+0x024/+0x048/+0x04c", media_notes)
        thunder_report = read("reverse/reports/thunder_bda_report.md")
        self.assertIn("SDK 不公开这两个 offset", game_notes)
        self.assertNotIn("兼容/占位入口", game_notes)
        self.assertIn("不公开 no-op stub", thunder_report)
        self.assertNotIn("兼容/占位入口", thunder_report)
        self.assertNotIn("SYS+0x044 stores a byte", media_notes + game_notes)
        self.assertNotIn("repeatedly paired", media_notes + game_notes)
        self.assertNotIn("BDA_SYS_PACKAGE_SOUND_LOAD_LIKE", header)
        self.assertNotIn("bda_sys_package_sound_load_like", header)

    def test_sys004_resource_close_is_documented_as_internal_constant(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        api_offsets = read("reverse/docs/api_offsets.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = header + "\n" + c200_notes + "\n" + catalog_tool + "\n" + api_offsets
        self.assertIn("SYS +0x000 / +0x008 / +0x00c / +0x010", c200_notes)
        self.assertIn("SYS+0x000 -> 0x80184d30", c200_notes)
        self.assertIn("SYS+0x008 -> 0x80185628", c200_notes)
        self.assertIn("SYS+0x00c -> 0x80185814", c200_notes)
        self.assertIn("SYS+0x010 -> 0x801859f0", c200_notes)
        self.assertIn("最多 10 个", c200_notes)
        self.assertIn("system resource/session slot", c200_notes)
        self.assertIn("descriptor+0x00", c200_notes)
        self.assertIn("busy-wait `0xea60`", c200_notes)
        self.assertIn("SDK 不公开 type-5 session manager wrapper", c200_notes)
        self.assertIn("SYS +0x000  不公开", api_offsets)
        self.assertIn("#define BDA_SYS_CLOSE_LIKE       0x004u", header)
        self.assertIn("SYS +0x004: `BDA_SYS_CLOSE_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x80185414`", c200_notes)
        self.assertIn("a0=resource_id", c200_notes)
        self.assertIn("resource_id - 1", c200_notes)
        self.assertIn("1..10", combined)
        self.assertIn("close callback", combined)
        self.assertIn("不是 app exit", combined)
        self.assertIn("raw audio 专用 stop", c200_notes)
        self.assertIn("不提供 wrapper", c200_notes)
        self.assertNotIn("bda_sys_close_like", header + read("reverse/docs/README.md"))
        self.assertNotIn("BDA_SYS_RESOURCE_OPEN_LIKE", header)
        self.assertNotIn("bda_sys_resource_open_like", header)

    def test_raw_audio_reset_flush_are_void_wrappers(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        media_notes = read("reverse/docs/media_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        self.assertIn("#define BDA_SYS_AUDIO_RESET_LIKE 0x08cu", header)
        self.assertIn("#define BDA_SYS_AUDIO_FLUSH_LIKE 0x0a0u", header)
        self.assertIn("static inline void bda_sys_audio_reset_like(void)", header)
        self.assertIn("static inline void bda_sys_audio_flush_like(void)", header)
        self.assertNotIn("static inline int bda_sys_audio_reset_like", header)
        self.assertNotIn("static inline int bda_sys_audio_flush_like", header)
        self.assertIn("SYS+0x08c -> 0x8001dc04", c200_notes)
        self.assertIn("SYS+0x0a0 -> 0x801891e8", c200_notes)
        self.assertIn("没有稳定 return value 约定", c200_notes)
        self.assertIn("void bda_sys_audio_reset_like(void)", media_notes)
        self.assertIn("void bda_sys_audio_flush_like(void)", media_notes)
        self.assertIn("不假设 return value 有效", media_notes)

    def test_raw_audio_state_getter_is_read_only_pointer_probe(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        media_notes = read("reverse/docs/media_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        api_offsets = read("reverse/docs/api_offsets.md")
        readme = read("reverse/docs/README.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = "\n".join([header, media_notes, c200_notes, api_offsets, readme, catalog_tool])
        self.assertIn("#define BDA_SYS_AUDIO_STATE_LIKE 0x090u", header)
        self.assertIn("static inline void *bda_sys_audio_state_like(void)", header)
        self.assertIn("typedef void *(*state_fn)(void)", header)
        self.assertIn("SYS+0x090 -> 0x8001dad4", c200_notes + "\n" + media_notes)
        self.assertIn("0x80362830", combined)
        self.assertIn("不读取调用者参数", c200_notes)
        self.assertIn("不是 open/init", c200_notes)
        self.assertIn("不是 open API", combined)
        self.assertIn("不要写入", combined)
        self.assertIn("SYS+0x094 -> 0x8001dae0", c200_notes + "\n" + media_notes)
        self.assertIn("raw audio state 写入 helper", c200_notes + "\n" + media_notes)
        self.assertIn("state+0x210..+0x221", c200_notes + "\n" + media_notes)
        self.assertIn("0x804781b4", c200_notes + "\n" + media_notes)
        self.assertIn("SDK 不公开 `SYS+0x094` wrapper", c200_notes)
        self.assertIn("不要把它当成 high-level audio state setter", media_notes)
        self.assertIn("void *bda_sys_audio_state_like(void);", readme + "\n" + media_notes)
        self.assertNotIn("static inline int bda_sys_audio_state_like", header)
        self.assertNotIn("BDA_SYS_AUDIO_STATE_SET_LIKE", header)
        self.assertNotIn("bda_sys_audio_state_set_like", header)

    def test_package_sound_wrappers_match_c200_argument_counts(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        readme = read("reverse/docs/README.md")
        media_notes = read("reverse/docs/media_notes.md")
        game_notes = read("reverse/docs/game_framework_notes.md")
        combined = header + "\n" + c200_notes + "\n" + catalog_tool + "\n" + readme + "\n" + media_notes + "\n" + game_notes
        self.assertIn("bda_sys_audio_attenuation_set_like(s32 attenuation)", header)
        self.assertIn("bda_sys_audio_attenuation_get_like(void)", header)
        self.assertIn("bda_sys_package_sound_op58_like(const void *descriptor)", header)
        self.assertIn("bda_sys_package_sound_op5c_like(u32 slot, const void *descriptor, u32 a2, u32 flags)", header)
        self.assertIn("bda_sys_package_sound_op60_like(void)", header)
        self.assertIn("bda_sys_package_sound_op64_like(void)", header)
        self.assertIn("bda_sys_package_sound_op68_like(void)", header)
        self.assertNotIn("bda_sys_package_sound_op58_like(u32 a0, u32 a1)", header)
        self.assertNotIn("bda_sys_package_sound_op5c_like(u32 a0)", header)
        self.assertNotIn("bda_sys_package_sound_op60_like(u32", header)
        self.assertNotIn("bda_sys_package_sound_op64_like(u32", header)
        self.assertNotIn("bda_sys_package_sound_op68_like(u32", header)
        self.assertIn("SYS+0x040 -> 0x8018921c", c200_notes)
        self.assertIn("SYS+0x044 -> 0x80189248", c200_notes)
        self.assertIn("SYS+0x058 -> 0x8018ecb4", c200_notes)
        self.assertIn("大于等于 `99` 的值 clamp", c200_notes)
        self.assertIn("0x806c4790 = 1", c200_notes)
        self.assertIn("0x80474308 = pending attenuation", c200_notes)
        self.assertIn("调用 `0x80195fb4`", c200_notes)
        self.assertIn("只读取 `a0=descriptor`", c200_notes)
        self.assertIn("a0=slot", c200_notes)
        self.assertIn("a1=descriptor", c200_notes)
        self.assertIn("a3=flags", c200_notes)
        self.assertIn("slot >= 8", c200_notes)
        self.assertIn("0x804c4ba8 == 0", c200_notes)
        self.assertIn("0x804c4ba8 != 0", c200_notes)
        self.assertIn("bda_audio_set_attenuation", combined)
        self.assertIn("bda_audio_get_attenuation", combined)
        self.assertNotIn("op40(sound_id)", combined)
        self.assertNotIn("op44(void)", combined)
        self.assertIn("op58(descriptor)", combined)
        self.assertIn("slot,descriptor,a2,flags", combined)
        self.assertIn("op60(void)", combined)
        self.assertIn("op64(void)", combined)
        self.assertIn("op68(void)", combined)

    def test_raw_audio_open_ready_write_c200_abi_is_documented(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        media_notes = read("reverse/docs/media_notes.md")
        gameboy_notes = read("reverse/docs/gameboy_notes.md")
        catalog = read("reverse/docs/api_catalog.md")
        combined = header + "\n" + c200_notes + "\n" + media_notes + "\n" + gameboy_notes + "\n" + catalog
        self.assertIn("SYS +0x06c / +0x074 / +0x078", c200_notes)
        self.assertIn("SYS+0x06c -> 0x80194654", combined)
        self.assertIn("SYS+0x074 -> 0x80194da4", combined)
        self.assertIn("SYS+0x078 -> 0x80194320", combined)
        self.assertIn("static inline void bda_sys_audio_open_like(u32 device, u32 format, u32 channels)", header)
        self.assertIn("bda_call3(bda_sys_table(), BDA_SYS_AUDIO_OPEN_LIKE, device, format, channels)", header)
        self.assertIn("void bda_sys_audio_open_like(u32 device, u32 format, u32 channels);", read("reverse/docs/README.md"))
        self.assertIn("void bda_sys_audio_open_like(u32 device, u32 format, u32 channels);", media_notes)
        self.assertNotIn("bda_sys_audio_open_like(u32 device, u32 format, u32 channels, u32 buffer_hint)", header + media_notes + c200_notes + read("reverse/docs/README.md"))
        self.assertNotIn("buffer_hint", header + media_notes + c200_notes + read("reverse/docs/README.md"))
        self.assertNotIn("static inline int bda_sys_audio_open_like", header)
        self.assertIn("`0x8058+0x6e8 > 0`", c200_notes)
        self.assertIn("返回 0x8058+0x6e8 > 0", catalog + "\n" + gameboy_notes)
        self.assertIn("0/1` ready bool", media_notes)
        self.assertIn("`bytes <= 0` 时返回 `-1`", c200_notes)
        self.assertIn("C200 bytes<=0 返回 -1", header)
        self.assertIn("最大 `0x8000` byte chunk", media_notes)
        self.assertIn("最多 0x8000 byte chunk", header)
        self.assertIn("已消费 byte 数", combined)
        self.assertIn("不要和飞天音乐/数码录音的 high-level 媒体后端混用", c200_notes)
        self.assertIn("当前切片没有看到 `a3` 被读取", media_notes)
        self.assertIn("尾部固定 `v0=0`", c200_notes + media_notes)
        self.assertIn("不暴露 return value", c200_notes)

    def test_sys_delay_and_timer_parameters_match_c200_evidence(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        time_notes = read("reverse/docs/time_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        api_offsets = read("reverse/docs/api_offsets.md")
        self.assertIn("void bda_sys_delay_like(u32 delay_units)", header)
        self.assertNotIn("static inline int bda_sys_delay_like", header)
        self.assertIn("void bda_sys_timer_like(u32 preset_index)", header)
        self.assertNotIn("static inline int bda_sys_timer_like", header)
        self.assertIn("void bda_sys_delay_like(u32 delay_units)", readme)
        self.assertIn("void bda_sys_timer_like(u32 preset_index)", readme)
        self.assertIn("阻塞式 delay", c200_notes)
        self.assertIn("busy-wait delay", read("reverse/docs/api_catalog.md"))
        self.assertIn("无稳定 return value", read("reverse/docs/api_catalog.md"))
        self.assertIn("不要读取 return value", c200_notes + "\n" + time_notes)
        self.assertIn("不是调度式 sleep", time_notes)
        self.assertIn("按 `0..14`", c200_notes)
        self.assertIn("0x8018921c", c200_notes)
        self.assertIn("0x806c4790 = 1", c200_notes)
        self.assertIn("0x80474308", c200_notes)
        self.assertIn("preset_index", time_notes)
        self.assertIn("不是任意 tick 数", api_offsets)
        self.assertNotIn("ticks_or_us", header + readme + time_notes)
        self.assertNotIn("bda_sys_timer_like(u32 ticks)", header + readme + time_notes)

    def test_game_tick_api_keeps_raw_unit_and_validation_boundary(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        stable_header = public_sdk_text()
        time_notes = read("reverse/docs/time_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        api_offsets = read("reverse/docs/api_offsets.md")
        progress = read("reverse/docs/game_api_verification_progress.md")
        combined = "\n".join([header, time_notes, c200_notes, api_offsets, progress])

        self.assertIn("#define BDA_GUI_TICK_COUNT_25MS_LIKE   0x6d8u", header)
        self.assertIn("static inline u32 bda_gui_tick_count_25ms_like(void)", header)
        self.assertIn("bda_gui_tick_count_25ms(void)", stable_header)
        self.assertIn("bda_gui_tick_elapsed_25ms(u32 start, u32 end)", stable_header)
        self.assertIn("bda_gui_tick_elapsed_ms(u32 start, u32 end)", stable_header)
        self.assertIn("return end - start", header)
        self.assertIn("return end - start", stable_header)
        self.assertIn("* 25u", header)
        self.assertIn("* 25u", stable_header)
        self.assertIn("0x8012bdb0", c200_notes)
        self.assertIn("0x8012bb90", c200_notes)
        self.assertIn("(current - base) * 25", combined)
        self.assertIn("24.853 ms/tick", progress)
        self.assertIn("真机待测", time_notes)
        self.assertIn("进入 `sdk/include`", time_notes)

    def test_high_resolution_timer_public_api_matches_hardware_evidence(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        stable_header = public_sdk_text()
        verified = read("docs/verified/high_resolution_timer_api.md")
        hardware_log = read(
            "docs/verified/assets/high_resolution_timer_v4_hardware_log.txt"
        )
        time_notes = read("reverse/docs/time_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        progress = read("reverse/docs/game_api_verification_progress.md")

        self.assertIn("bda_cp0_count_raw_like(void)", header)
        self.assertIn("BDA_TCU_TIMER1_COUNTS_PER_SECOND_LIKE 750000u", header)
        self.assertIn("0xb0002058u", header)
        self.assertIn("bda_tcu_timer1_available_like(void)", header)
        self.assertNotIn("bda_time_counter_750khz_like", header)
        self.assertNotIn("bda_firmware_millisecond_count_raw_like", header)
        self.assertIn("BDA_GUI_MILLISECOND_TIMER_START_LIKE 0x714u", header)
        self.assertIn("BDA_GUI_MILLISECOND_TIMER_STOP_LIKE  0x718u", header)
        self.assertIn("BDA_GUI_MILLISECOND_COUNT_LIKE       0x71cu", header)
        self.assertIn("bda_gui_millisecond_timer_start_like(void)", header)
        self.assertIn("bda_gui_millisecond_timer_stop_like(void)", header)
        self.assertIn("bda_gui_millisecond_count_like(void)", header)
        self.assertIn("bda_gui_millisecond_elapsed_like(u32 start, u32 end)", header)
        self.assertNotIn("bda_time_counter_750khz", stable_header)
        self.assertNotIn("bda_cp0_count_raw", stable_header)
        for offset in [
            "BDA_SDK_INTERNAL_GUI_MILLISECOND_TIMER_START 0x714u",
            "BDA_SDK_INTERNAL_GUI_MILLISECOND_TIMER_STOP  0x718u",
            "BDA_SDK_INTERNAL_GUI_MILLISECOND_COUNT       0x71cu",
        ]:
            self.assertIn(offset, stable_header)
        for name in [
            "bda_gui_millisecond_timer_start(void)",
            "bda_gui_millisecond_timer_stop(void)",
            "bda_gui_millisecond_count(void)",
            "bda_gui_millisecond_elapsed(u32 start, u32 end)",
        ]:
            self.assertIn(name, stable_header)
            self.assertIn(name, verified)
        self.assertIn("0x8091ce34", time_notes + c200_notes + progress)
        self.assertIn("HighResolutionTimerProbeV2", time_notes + progress)
        self.assertIn("TDFR1=0x0000FFFF", time_notes + progress)
        self.assertIn("CP0 Count 恒为零", time_notes + c200_notes + progress)
        self.assertIn("HighResolutionTimerProbeV3", time_notes + c200_notes + progress)
        self.assertIn("HighResolutionTimerProbeV4", time_notes + c200_notes + progress)
        self.assertIn("0x8001dce0", time_notes + c200_notes + progress)
        self.assertIn("0x8001dec0", time_notes + c200_notes + progress)
        self.assertIn("0x8001dde0", time_notes + c200_notes + progress)
        self.assertIn("0x8001ddb0", time_notes + c200_notes + progress)
        for phrase in [
            "标称 1 ms",
            "每次 BDA 只启动一次",
            "不要连续调用\n两次 `start`",
            "不承诺计数与真实毫秒\n严格相等",
            "STOP CHECK TICKS=2 C0=1017 C1=1017",
            "SUBTICK=PASS",
            "RESULT=PASS",
        ]:
            self.assertIn(phrase, verified + "\n" + hardware_log)
        self.assertIn("WINDOW=1 TICKS=8 MS=194", hardware_log)
        self.assertIn("high_resolution_timer_api.md", read("docs/verified/README.md"))
        self.assertIn(
            "high_resolution_timer_api.md",
            read("docs/verified/public_api_policy.md"),
        )
        self.assertTrue(
            (ROOT / "example/system/high_resolution_timer/HighResolutionTimer.bda").is_file()
        )

    def test_stub_and_constant_query_apis_are_not_misleading(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        time_notes = read("reverse/docs/time_notes.md")
        gameboy_notes = read("reverse/docs/gameboy_notes.md")

        self.assertIn(
            "#define BDA_GUI_SCREEN_ORIENTATION_LIKE 0x738u", header
        )
        self.assertIn(
            "static inline int bda_gui_screen_orientation_like(void)", header
        )
        self.assertIn("int bda_gui_screen_orientation_like(void);", readme)
        self.assertIn("gui_screen_orientation_demo.c", readme)
        self.assertIn("`0x130`", readme)
        self.assertNotIn("BDA_GUI_SCREEN_MODE_QUERY_LIKE", header)
        self.assertNotIn("bda_gui_screen_mode_query_like", header)

        self.assertNotIn("BDA_SYS_ALARM_COMMIT_LIKE", header)
        self.assertNotIn("bda_sys_alarm_commit_like", header)
        self.assertNotIn("bda_sys_alarm_commit_like", readme)
        self.assertIn("#define BDA_SYS_ALARM_RECORD_SIZE 0x2b8u", header)
        self.assertIn("#define BDA_SYS_ALARM_CONFIRMED_SLOTS 3u", header)
        self.assertIn("#define BDA_SYS_ALARM_DB_FIRST_RECORD_OFFSET 0x578u", header)
        self.assertIn("#define BDA_SYS_ALARM_SLOT_TAG_OFFSET 0x00u", header)
        self.assertIn("#define BDA_SYS_ALARM_ENABLE_FLAG_OFFSET 0x10u", header)
        self.assertIn("#define BDA_SYS_ALARM_DUE_MISS_TAG 0xffffffffu", header)
        self.assertIn("typedef struct bda_sys_alarm_record_like", header)
        self.assertIn("u8 raw[BDA_SYS_ALARM_RECORD_SIZE]", header)
        self.assertIn("bda_sys_alarm_record_init_like(bda_sys_alarm_record_like_t *record)", header + readme + time_notes)
        self.assertIn("bda_sys_alarm_slot_confirmed_like(u32 slot)", header + readme + time_notes)
        self.assertIn("bda_sys_alarm_record_file_offset_like(u32 slot)", header + readme + time_notes)
        self.assertIn("bda_sys_alarm_record_slot_tag_like(const bda_sys_alarm_record_like_t *record)", header + readme + time_notes)
        self.assertIn("bda_sys_alarm_due_miss_like(const bda_sys_alarm_record_like_t *record)", header + readme + time_notes)
        self.assertIn("bda_sys_alarm_record_enable_flag_like(const bda_sys_alarm_record_like_t *record)", header + readme + time_notes)
        self.assertIn("#define BDA_SYS_ALARM_DUE_GET_LIKE", header)
        self.assertIn("bda_sys_alarm_due_get_like(bda_sys_alarm_record_like_t *out_alarm_data)", header)
        self.assertIn("int bda_sys_alarm_due_get_like(bda_sys_alarm_record_like_t *out_alarm_data);", readme)
        self.assertIn("bda_sys_alarm_set_like(bda_sys_alarm_record_like_t *alarm_data, u32 slot)", header)
        self.assertIn("bda_sys_alarm_get_like(bda_sys_alarm_record_like_t *alarm_data, u32 slot)", header)
        self.assertIn("BDA_SYS_ALARM_RECORD_SIZE", readme + time_notes + c200_notes)
        self.assertIn("bda_sys_alarm_record_like_t", readme + time_notes + c200_notes)
        self.assertIn("alarm.db", time_notes + c200_notes)
        self.assertIn("out+0x00 = -1", time_notes + c200_notes)
        self.assertIn("不能传 short buffer", readme + c200_notes)
        self.assertIn("static bda_sys_alarm_record_like_t g_due_alarm_data", read("reverse/examples/time_probe.c"))
        self.assertIn("bda_sys_alarm_due_get_like(&g_due_alarm_data)", read("reverse/examples/time_probe.c"))
        self.assertIn("0x578 + slot * 0x2b8", header + time_notes + c200_notes)
        self.assertIn("record+0x10", readme + time_notes + c200_notes)
        self.assertIn("slot tag", readme + time_notes + c200_notes)
        self.assertIn("完整结构体", readme + time_notes + c200_notes)
        self.assertIn("未见 slot bounds check", header + time_notes + c200_notes)
        self.assertIn("return value: 成功 1，失败 0", time_notes + c200_notes)
        self.assertNotIn("BDA_SYS_TIME_GET_LIKE", header + readme + time_notes + c200_notes)
        self.assertNotIn("bda_sys_time_get_like", header + readme + time_notes + c200_notes)
        self.assertNotIn("static unsigned char g_time_data[64]", read("reverse/examples/time_probe.c"))
        self.assertNotIn("bda_sys_alarm_due_get_like(void *out_alarm_data)", header + readme + time_notes)
        self.assertNotIn("bda_sys_alarm_set_like(void *alarm_data, u32 index)", header + readme + time_notes)
        self.assertNotIn("bda_sys_alarm_get_like(void *alarm_data, u32 index)", header + readme + time_notes)

        self.assertIn("GUI +0x738", c200_notes)
        self.assertIn("delay slot 是 `addiu v0, zero, 0x130`", c200_notes)
        self.assertIn("BDA_GUI_SCREEN_ORIENTATION_LIKE", c200_notes)
        self.assertIn("SYS +0x0a8  不公开 no-op stub", time_notes)
        self.assertIn("SDK 不再公开该 wrapper", time_notes)
        self.assertIn("GUI +0x738  screen orientation", gameboy_notes)

    def test_msgbox_api_has_dynamic_standalone_evidence(self) -> None:
        verified = read("docs/verified/msgbox_api.md")
        index = read("docs/verified/README.md")
        source = read("example/basic/hello_world/hello_world_msgbox.c")
        confirm_source = read(
            "example/system/confirm_dialog/confirm_dialog_probe.c"
        )
        three_button_source = read(
            "example/system/three_button_dialog/three_button_dialog_demo.c"
        )
        public_header = read("sdk/include/bda_dialogs.h")
        for phrase in [
            "GUI +0x2b8",
            "0x800c6544",
            "parent,message,title,flags",
            'bda_msgbox("HelloWorld", "HelloWorld")',
            "A91EF6F90A2CE32E7F4F1CEB31E4CDCAC3499F4A8B630DD03BA9DFA45E9E0B60",
            "新增第 11 个文件不会展示",
            "LEFT=0x00000006",
            "RIGHT=0x00000007",
            "running=true",
            "invalid=0",
            "退出键返回值",
            "原版 NAND SHA-256 保持",
        ]:
            self.assertIn(phrase, verified)
        self.assertIn("msgbox_api.md", index)
        self.assertIn('bda_msgbox("HelloWorld", "HelloWorld")', source)
        self.assertIn("bda_confirm(", confirm_source)
        self.assertIn("BDA_DIALOG_RESULT_YES", confirm_source)
        self.assertIn("bda_confirm_yes_all_no", three_button_source)
        self.assertIn("BDA_DIALOG_RESULT_ALL", three_button_source)
        self.assertIn("#define BDA_MSGBOX_TYPE_YES_NO      2u", public_header)
        self.assertIn("#define BDA_MSGBOX_TYPE_YES_ALL_NO  6u", public_header)
        self.assertIn("#define BDA_DIALOG_RESULT_YES 6", public_header)
        self.assertIn("#define BDA_DIALOG_RESULT_ALL 10", public_header)
        self.assertIn("#define BDA_DIALOG_RESULT_NO  7", public_header)
        self.assertIn("static inline int bda_confirm(", public_header)
        self.assertTrue((ROOT / "docs/verified/assets/msgbox_hello_world_verified.png").is_file())
        self.assertTrue(
            (ROOT / "docs/verified/assets/msgbox_confirm_yes_no_verified.png").is_file()
        )
        self.assertTrue(
            (ROOT / "docs/verified/assets/msgbox_confirm_result_verified.png").is_file()
        )

    def test_gameboy_extended_gui_helpers_match_c200_abi(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        gameboy_notes = read("reverse/docs/gameboy_notes.md")
        verified_input = read("docs/verified/input_polling_api.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        system_tables = read("reverse/docs/system_api_tables.md")
        api_catalog = read("reverse/docs/api_catalog.md")
        generated_tables = system_tables + "\n" + api_catalog
        self.assertIn("#define BDA_GUI_INPUT_PACKET_LIKE      0x5d4u", header)
        self.assertIn("#define BDA_GUI_INPUT_PACKET_SIZE 6u", header)
        self.assertIn("typedef struct bda_gui_input_packet_like", header)
        self.assertIn("u8 bytes[BDA_GUI_INPUT_PACKET_SIZE]", header)
        self.assertIn("int bda_gui_input_packet_like(bda_gui_input_packet_like_t *packet)", header)
        self.assertIn("#define BDA_KEY_ESCAPE 0x01u", header)
        self.assertIn("#define BDA_KEY_ENTER  0x1cu", header)
        self.assertIn("#define BDA_KEY_UP     0x67u", header)
        self.assertIn("#define BDA_KEY_LEFT   0x69u", header)
        self.assertIn("#define BDA_KEY_RIGHT  0x6au", header)
        self.assertIn("#define BDA_KEY_DOWN   0x6cu", header)
        self.assertIn("#define BDA_INPUT_PACKET_RIGHT_INDEX  0u", header)
        self.assertIn("#define BDA_INPUT_PACKET_LEFT_INDEX   1u", header)
        self.assertIn("#define BDA_INPUT_PACKET_DOWN_INDEX   2u", header)
        self.assertIn("#define BDA_INPUT_PACKET_UP_INDEX     3u", header)
        self.assertIn("#define BDA_INPUT_PACKET_ESCAPE_INDEX 4u", header)
        self.assertIn("#define BDA_INPUT_PACKET_ENTER_INDEX  5u", header)
        self.assertIn("bda_gui_input_packet_key_pressed_like", header)
        self.assertIn("bda_gui_key_pressed_like", header)
        self.assertIn("packet[0]  Right", verified_input)
        self.assertIn("packet[1]  Left", verified_input)
        self.assertIn("packet[2]  Down", verified_input)
        self.assertIn("packet[3]  Up", verified_input)
        self.assertIn("packet[4]  Esc", verified_input)
        self.assertIn("packet[5]  Enter", verified_input)
        self.assertIn("按 Right 显示 DOWN", verified_input)
        self.assertIn("int bda_gui_input_packet_like(bda_gui_input_packet_like_t *packet);", readme)
        self.assertIn("typedef struct bda_gui_event_fetch_like", header)
        self.assertIn("s32 code;", header)
        self.assertIn("s32 value;", header)
        self.assertIn("#define BDA_GUI_SCREEN_BUFFER_LIKE     0x6b0u", header)
        self.assertIn("void *bda_gui_screen_buffer_like(void)", header)
        self.assertIn("int bda_gui_state_query_like(void)", header)
        self.assertIn("int bda_gui_event_fetch_like(bda_gui_event_fetch_like_t *out_event)", header)
        self.assertIn("void *bda_gui_screen_buffer_like(void);", readme)
        self.assertIn("int bda_gui_state_query_like(void);", readme)
        self.assertIn("int bda_gui_event_fetch_like(bda_gui_event_fetch_like_t *out_event);", readme)
        self.assertNotIn("BDA_GUI_SCREEN_ALLOC_LIKE", header + readme + c200_notes)
        self.assertNotIn("bda_gui_screen_alloc_like", header + readme + c200_notes)
        self.assertNotIn("bda_gui_state_query_like(u32 a0)", header + readme + c200_notes)
        self.assertNotIn("bda_gui_event_fetch_like(u32 a0)", header + readme + c200_notes)
        self.assertNotIn("bda_gui_event_fetch_like(s32 *out_code, s32 *out_value)", header + readme + c200_notes)
        self.assertNotIn("bda_gui_input_packet_like(u8 *packet)", header + readme + c200_notes)
        self.assertNotIn("BDA_GUI_DRAW_PACKET_LIKE", header + readme + c200_notes)
        self.assertNotIn("bda_gui_draw_packet_like", header + readme + c200_notes)
        self.assertIn("GUI +0x5d4 / +0x6b0 / +0x6e0 / +0x72c / +0x750", c200_notes)
        self.assertIn("GUI+0x5d4 -> 0x8001b518", c200_notes)
        self.assertIn("GUI+0x6b0 -> 0x80010d94", c200_notes)
        self.assertIn("GUI+0x6e0 -> 0x8005b844", c200_notes)
        self.assertIn("GUI+0x72c -> 0x8005a2d4", c200_notes)
        self.assertIn("GUI+0x750 -> 0x8001de5c", c200_notes)
        self.assertIn("game/display 扩展 screen/input helper", c200_notes)
        self.assertIn("不是 4 参数分配函数", c200_notes + "\n" + catalog_tool)
        self.assertIn("不要直接写或自定义 present", catalog_tool + "\n" + generated_tables)
        self.assertIn("不是 SDK 分配的稳定 framebuffer", header + "\n" + c200_notes + "\n" + gameboy_notes)
        self.assertIn("普通 BDA 不要直接写入", header + "\n" + c200_notes + "\n" + gameboy_notes)
        self.assertIn("不要把它和 `GUI+0x3f8/+0x400` 拼成自定义 present 路径", header + "\n" + c200_notes + "\n" + gameboy_notes)
        self.assertIn("取得/使用内部 GUI screen buffer", gameboy_notes)
        self.assertNotIn("分配大型 GUI/screen buffer", gameboy_notes)
        self.assertIn("清 6 byte packet", c200_notes + "\n" + gameboy_notes)
        self.assertIn("BDA_GUI_INPUT_PACKET_SIZE", c200_notes)
        self.assertIn("record+4", c200_notes)
        self.assertIn("record+0", c200_notes)
        self.assertIn("两个 s32 output pointer", gameboy_notes)

    def test_window_timer_c200_layout_and_public_api_are_documented(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        stable_header = read("sdk/include/bda_time.h")
        umbrella = read("sdk/include/bda_sdk.h")
        verified = read("docs/verified/window_timer_api.md")
        probe = read("reverse/examples/window_timer_probe.c")
        precision_probe = read(
            "reverse/examples/window_timer_precision_probe.c"
        )
        emulator_log = read(
            "docs/verified/assets/window_timer_v4_emulator_log.txt"
        )
        precision_log = read(
            "docs/verified/assets/window_timer_precision_v6_emulator_log.txt"
        )
        hardware_log = read(
            "docs/verified/assets/window_timer_v4_hardware_log.txt"
        )
        notes = read("reverse/docs/c200_api_function_notes.md")
        window_notes = read("reverse/docs/window_notes.md")
        bbvm_notes = read("reverse/docs/bbvm_notes.md")
        ninecourse_report = read("reverse/reports/ninecourse_bda_report.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = "\n".join([header, notes, window_notes, bbvm_notes, ninecourse_report, catalog_tool])
        self.assertIn("bda_gui_destroy_like(bda_handle_t handle)", header)
        self.assertIn("GUI +0x1a8: `BDA_GUI_DESTROY_LIKE`", notes)
        self.assertIn("system function VA：`0x800cd41c`", notes)
        self.assertIn("subtype halfword 为 `0x12`", notes)
        self.assertIn("0x800dd380(handle, 0x64, 0, 0)", notes)
        self.assertIn("handle+0xd0", notes)
        self.assertIn("0x16a", notes)
        self.assertIn("MEM_FREE(handle)", notes)
        self.assertIn("成功释放返回 `1`", notes)
        self.assertIn("不是顶层 frame close", window_notes)
        self.assertIn("kind=1 subtype=0x12", catalog_tool)
        self.assertIn("GUI +0x1ac..+0x1bc", notes)
        self.assertIn("内部 `0x162`", notes)
        self.assertIn("内部 `0x163`", notes)
        self.assertIn("sp+0x10/+0x14/+0x18", notes)
        self.assertIn("sp+0x10/+0x14", notes)
        self.assertIn("0x800dd380", notes)
        self.assertIn("bda_gui_window_timer_start_like", header)
        self.assertIn("bda_gui_window_timer_stop_like", header)
        self.assertIn("bda_gui_window_timer_exists_like", header)
        self.assertIn("bda_gui_window_timer_set_period_like", header)
        self.assertIn("bda_gui_window_timer_clock_ms_like", header)
        self.assertIn("0x800de0a8", notes)
        self.assertIn("0x800de1c8", notes)
        self.assertIn("0x800de144", notes)
        self.assertIn("0x804a6b40", notes + "\n" + window_notes + "\n" + catalog_tool)
        self.assertIn("record+0", notes + "\n" + window_notes + "\n" + catalog_tool)
        self.assertIn("record+4", notes + "\n" + window_notes + "\n" + catalog_tool)
        self.assertIn("返回 `0`", notes)
        self.assertIn("message `0x144`", notes)
        self.assertIn("10 ms", notes)
        self.assertIn("16 byte", notes)
        self.assertIn("空指针解引用风险", notes + verified)
        self.assertNotIn("_like", stable_header.lower())
        self.assertNotIn("WINDOW_TIMER_SET_PERIOD", read("sdk/include/bda/detail/runtime.h"))
        self.assertIn('#include "bda_time.h"', umbrella)
        for name in [
            "bda_gui_window_timer_start",
            "bda_gui_window_timer_stop",
            "bda_gui_window_timer_exists",
            "bda_gui_window_timer_set_period",
            "bda_gui_window_timer_clock_ms",
        ]:
            self.assertIn(name, stable_header)
            self.assertIn(name, verified)
            self.assertIn(name, probe)
        for name in [
            "BDA_MSG_WINDOW_TIMER",
            "BDA_WINDOW_TIMER_MAX_ACTIVE",
            "BDA_WINDOW_TIMER_RESOLUTION_MS",
        ]:
            self.assertIn(name, stable_header)
            self.assertIn(name, verified)
        self.assertIn("period_ms == 0u", stable_header)
        self.assertIn("stop + start", verified)
        self.assertIn("START WINDOW TIMER PROBE V4", emulator_log)
        self.assertIn("CLOCK_DELTA=40", emulator_log)
        self.assertIn("CLOCK_DELTA=20", emulator_log)
        self.assertIn("SPARSE SET B=0x00000001", emulator_log)
        self.assertIn("FAILURES=0x00000000", emulator_log)
        self.assertIn("RESULT=PASS", emulator_log)
        self.assertIn("START WINDOW TIMER PROBE V4", hardware_log)
        self.assertIn("REGISTER=0x80A89528", hardware_log)
        self.assertEqual(hardware_log.count("CLOCK_DELTA=40"), 4)
        self.assertEqual(hardware_log.count("CLOCK_DELTA=20"), 4)
        self.assertIn("EXISTS AFTER STOP=0x00000000", hardware_log)
        self.assertIn("SPARSE SET B=0x00000001", hardware_log)
        self.assertIn("FAILURES=0x00000000", hardware_log)
        self.assertIn("RESULT=PASS", hardware_log)
        self.assertIn("CLOSE RETURNED", hardware_log)
        self.assertIn("BBK 9588 真机均验证", verified)
        self.assertIn("START WINDOW TIMER PRECISION PROBE V6", precision_log)
        for request, expected in [(5, 10), (10, 10), (15, 20), (25, 30)]:
            self.assertIn(
                f"REQUEST={request} EXPECT={expected} ", precision_log
            )
            self.assertIn(f"{request}u", precision_probe)
            self.assertIn(f"{expected}u", precision_probe)
        self.assertEqual(precision_log.count("SAMPLE P="), 48)
        self.assertIn("SCHED FAILURES=0x00000000", precision_log)
        self.assertIn("SCHED RESULT=PASS", precision_log)
        self.assertIn("DELIVERY RESULT=OUTSIDE TOLERANCE", precision_log)
        self.assertIn("RESULT=PASS", precision_log)
        self.assertIn("ceil(period_ms / 10) * 10 ms", verified)
        self.assertIn("V6 真机", verified)
        self.assertIn("bda_gui_object_userdata0_get_like(bda_handle_t handle)", header)
        self.assertIn("bda_gui_object_userdata0_set_like(bda_handle_t handle, u32 value)", header)
        self.assertIn("bda_gui_object_userdata1_get_like(bda_handle_t handle)", header)
        self.assertIn("bda_gui_object_userdata1_set_like(bda_handle_t handle, u32 value)", header)
        self.assertIn("bda_gui_object_payload_word_get_like(bda_handle_t handle)", header)
        self.assertIn("bda_gui_object_payload_word_set_like(bda_handle_t handle, u32 value)", header)
        self.assertIn("bda_gui_object_resource_ptr_get_like(bda_handle_t handle)", header)
        self.assertIn("bda_gui_object_callback_ptr_get_like(bda_handle_t handle)", header)
        self.assertIn("bda_gui_object_callback_ptr_set_like(bda_handle_t handle, void *value)", header)
        self.assertIn("bda_gui_object_flags_get_like(bda_handle_t handle)", header)
        self.assertIn("bda_gui_object_flags_or_like(bda_handle_t handle, u32 mask)", header)
        self.assertIn("bda_gui_object_flags_clear_like(bda_handle_t handle, u32 mask)", header)
        readme = read("reverse/docs/README.md")
        self.assertIn("u32 bda_gui_object_flags_get_like(bda_handle_t handle);", readme)
        self.assertIn("int bda_gui_object_flags_or_like(bda_handle_t handle, u32 mask);", readme)
        self.assertIn("int bda_gui_object_flags_clear_like(bda_handle_t handle, u32 mask);", readme)
        self.assertIn("GUI +0x07c/+0x080/+0x0b0 / +0x0b8..+0x0dc", notes)
        self.assertIn("GUI+0x07c -> 0x800ce4c8", notes)
        self.assertIn("GUI+0x080 -> 0x800ce4fc", notes)
        self.assertIn("GUI+0x0b0 -> 0x800ce4a0", notes)
        self.assertIn("GUI+0x0b8 -> 0x800ce558", notes)
        self.assertIn("GUI+0x0bc -> 0x800ce580", notes)
        self.assertIn("GUI+0x0c0 -> 0x800ce5b0", notes)
        self.assertIn("GUI+0x0c4 -> 0x800ce5d8", notes)
        self.assertIn("GUI+0x0c8 -> 0x800ce608", notes)
        self.assertIn("GUI+0x0cc -> 0x800ce644", notes)
        self.assertIn("GUI+0x0d0 -> 0x800ce7dc", notes)
        self.assertIn("GUI+0x0d4 -> 0x800ce804", notes)
        self.assertIn("GUI+0x0d8 -> 0x800ce780", notes)
        self.assertIn("GUI+0x0dc -> 0x800ce7a8", notes)
        self.assertIn("handle+0x80", notes + "\n" + catalog_tool)
        self.assertIn("handle+0x24", notes + "\n" + window_notes + "\n" + catalog_tool)
        self.assertIn("flags OR helper", notes + "\n" + catalog_tool)
        self.assertIn("flags clear/OR/get helper", window_notes)
        self.assertIn("flags &= ~mask", read("reverse/docs/api_offsets.md"))
        self.assertIn("成功返回 `1`", notes + "\n" + window_notes)
        self.assertIn("它不清除任何 bit", notes)
        self.assertIn("只清 mask 对应 bit", notes)
        self.assertIn("失败返回 `0`", notes + "\n" + window_notes)
        self.assertIn("不是 show/hide、enable/disable", notes)
        self.assertIn("不是通用 show/hide/enable/disable API", window_notes)
        self.assertIn("handle+0x84", notes + "\n" + catalog_tool)
        self.assertIn("handle+0xec", notes + "\n" + window_notes + "\n" + catalog_tool)
        self.assertIn("payload+0x1c", notes + "\n" + window_notes + "\n" + catalog_tool)
        self.assertIn("handle+0x8c", notes + "\n" + window_notes + "\n" + catalog_tool)
        self.assertIn("handle+0x88", notes + "\n" + window_notes + "\n" + catalog_tool)
        self.assertIn("不公开 wrapper", notes + "\n" + window_notes)
        self.assertIn("0x134", notes + "\n" + window_notes)
        self.assertIn("value != 0", notes)
        self.assertIn("wndproc/callback", notes + "\n" + window_notes)
        self.assertIn("subtype `0x12`", notes + "\n" + window_notes)
        self.assertIn("setter 返回旧值", window_notes)
        self.assertIn("不要把 `0` return 单独当成失败证明", notes)
        self.assertIn("window timer start", catalog_tool)
        self.assertIn("内部消息 0x162", catalog_tool)
        self.assertIn("window timer stop", catalog_tool)
        self.assertIn("内部消息 0x163", catalog_tool)
        self.assertIn("window timer start；frame,timer_id,period_ms", bbvm_notes)
        self.assertIn("window timer stop；frame,timer_id", bbvm_notes)
        self.assertIn("不是 lock/unlock 或 object refresh", bbvm_notes)
        self.assertIn("不是\nlock/unlock、begin/end frame 或对象 update notification", ninecourse_report)
        self.assertIn("WindowTimerProbe", bbvm_notes)
        self.assertNotIn("lock/begin update-like", bbvm_notes)
        self.assertNotIn("unlock/end update-like", bbvm_notes)
        self.assertNotIn("begin/end frame 或 lock/unlock", bbvm_notes)
        self.assertNotIn("BlitLockProbe", bbvm_notes)
        self.assertIn("window timer exists", catalog_tool)
        self.assertIn("userdata0 getter", catalog_tool)
        self.assertIn("userdata1 setter", catalog_tool)
        self.assertIn("payload word getter", catalog_tool)
        self.assertIn("resource pointer getter", catalog_tool)
        self.assertIn("callback pointer setter", catalog_tool)
        self.assertNotIn("bda_gui_destroy_like(bda_handle_t frame)", combined)

    def test_gui_origin_helpers_are_documented_as_parent_chain_coordinate_converters(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        window_notes = read("reverse/docs/window_notes.md")
        api_offsets = read("reverse/docs/api_offsets.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = "\n".join([header, readme, c200_notes, window_notes, api_offsets, catalog_tool])

        self.assertIn("#define BDA_GUI_ACCUMULATE_ORIGIN_LIKE 0x0f4u", header)
        self.assertIn("#define BDA_GUI_SUBTRACT_ORIGIN_LIKE   0x0f8u", header)
        self.assertIn("bda_gui_accumulate_origin_like(bda_handle_t handle, s32 *x, s32 *y)", header)
        self.assertIn("bda_gui_subtract_origin_like(bda_handle_t handle, s32 *x, s32 *y)", header)
        self.assertIn("void bda_gui_subtract_origin_like(bda_handle_t handle, s32 *x, s32 *y);", readme)
        self.assertIn("GUI +0x0f4 / +0x0f8", c200_notes)
        self.assertIn("GUI+0x0f4 -> 0x800ce26c", c200_notes)
        self.assertIn("GUI+0x0f8 -> 0x800cc664", c200_notes)
        self.assertIn("从 `*x` 减去对象 `+0x14`", c200_notes)
        self.assertIn("从 `*y` 减去对象 `+0x18`", c200_notes)
        self.assertIn("+0xd0", combined)
        self.assertIn("+0x14/+0x18", combined)
        self.assertIn("反向累计 object 父链 origin", catalog_tool)
        self.assertIn("GUI+0x0fc/+0x100", c200_notes)
        self.assertIn("+0x04/+0x08", c200_notes)
        self.assertIn("SDK 暂不公开", c200_notes)
        self.assertIn("BDA_GUI_SUBTRACT_ORIGIN_LIKE", api_offsets)

    def test_gui_rgb_and_color_setters_match_c200_context_abi(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        text_notes = read("reverse/docs/text_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = header + "\n" + text_notes + "\n" + c200_notes + "\n" + catalog_tool
        self.assertIn("bda_gui_rgb_like(bda_handle_t handle, u32 r, u32 g, u32 b)", header)
        self.assertIn("bda_gui_set_fill_color_like(bda_handle_t handle, u32 color)", header)
        self.assertIn("bda_gui_set_text_mode_like(bda_handle_t handle, u32 mode)", header)
        self.assertIn("bda_gui_set_text_color_like(bda_handle_t handle, u32 color)", header)
        self.assertIn("GUI+0x334 -> 0x800b2c7c", c200_notes)
        self.assertIn("GUI+0x338 -> 0x800b2c94", c200_notes)
        self.assertIn("GUI+0x33c -> 0x800b2cac", c200_notes)
        self.assertIn("GUI+0x378 -> 0x800bc2e0", c200_notes)
        self.assertIn("0x80825690", combined)
        self.assertIn("a1/a2/a3", c200_notes)
        self.assertIn("低 8 位", combined)
        self.assertIn("context+0x14", c200_notes)
        self.assertIn("context+0x18", c200_notes + "\n" + text_notes)
        self.assertIn("context+0x50", c200_notes)
        self.assertIn("返回旧值", combined)
        self.assertIn("mode 枚举仍未完全命名", c200_notes)
        self.assertIn("不是裸 RGB565", combined)
        self.assertIn("global+0x5c", c200_notes)
        self.assertIn("GUI+0x2fc(0x10)", c200_notes)
        self.assertIn("不要把这种返回值当 surface/context handle", c200_notes)

    def test_gui_put_pixel_documents_context_color_backend_path(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        paint_notes = read("reverse/docs/paint_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = header + "\n" + readme + "\n" + paint_notes + "\n" + c200_notes + "\n" + catalog_tool
        self.assertIn("bda_gui_put_pixel_like(bda_handle_t context, s32 x, s32 y, u32 color)", combined)
        self.assertNotIn("bda_gui_put_pixel_like(bda_handle_t surface, s32 x, s32 y, u16 rgb565)", combined)
        self.assertIn("GUI +0x368 / +0x36c: 单像素绘制", c200_notes)
        self.assertIn("GUI+0x368 -> 0x800b68c0", c200_notes)
        self.assertIn("a0=context", c200_notes)
        self.assertIn("a3=color", c200_notes)
        self.assertIn("0x80825690", c200_notes)
        self.assertIn("x-1/y-1/x+1/y+1", c200_notes)
        self.assertIn("0x800c056c(rect, rect, context+0xb0)", c200_notes)
        self.assertIn("0x800c0818", c200_notes)
        self.assertIn("+0xb0(surface, x, y, color)", c200_notes)
        self.assertIn("backend +0xb0", catalog_tool)
        verified = read("docs/verified/graphics_primitives_api.md")
        example = read("example/graphics/primitives/graphics_primitives_demo.c")
        self.assertIn("#define BDA_GUI_PUT_PIXEL_RGB_LIKE  0x36cu", header)
        self.assertIn("bda_gui_put_pixel_rgb_like", header + example + verified)
        self.assertIn("GUI+0x36c -> 0x800b6af8", c200_notes)
        self.assertIn("stack+0x10/+0x14", c200_notes + verified)
        self.assertIn("青色块", verified)
        self.assertIn("橙色块", verified)
        self.assertIn("矩形轮廓", verified)
        self.assertIn("assets/graphics_primitives_bda_verified.png", verified)
        self.assertTrue(
            (ROOT / "docs/verified/assets/graphics_primitives_bda_verified.png").is_file()
        )
        self.assertIn("不承诺可直接把该流程当双缓冲游戏循环", verified)

    def test_gui_polyline_and_clip_query_research_api(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        catalog_tool = read("reverse/bda_api_catalog.py")
        progress = read("reverse/docs/game_api_verification_progress.md")
        combined = header + "\n" + catalog_tool + "\n" + progress
        self.assertIn("#define BDA_GUI_POLYLINE_LIKE       0x384u", header)
        self.assertIn("bda_gui_polyline_like", header)
        self.assertIn("bda_gui_clip_bounds_like", header)
        self.assertIn("bda_gui_clip_contains_point_like", header)
        self.assertIn("bda_gui_clip_intersects_rect_like", header)
        self.assertIn("context,point_array,count", catalog_tool)
        self.assertIn("GamePolylineClipProbeV10", progress)

    def test_gui_ellipse_research_api(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        catalog_tool = read("reverse/bda_api_catalog.py")
        progress = read("reverse/docs/game_api_verification_progress.md")
        self.assertIn("#define BDA_GUI_ELLIPSE_LIKE        0x390u", header)
        self.assertIn("bda_gui_ellipse_like", header)
        self.assertIn("context,cx,cy,rx,ry,0,0,filled", catalog_tool)
        self.assertIn("GameEllipseProbeV11", progress)

    def test_gui_arc_round_rect_research_api(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        catalog_tool = read("reverse/bda_api_catalog.py")
        progress = read("reverse/docs/game_api_verification_progress.md")
        self.assertIn("#define BDA_GUI_ARC_LIKE            0x394u", header)
        self.assertIn("#define BDA_GUI_ROUND_RECT_LIKE     0x398u", header)
        self.assertIn("bda_gui_arc_like", header)
        self.assertIn("bda_gui_round_rect_like", header)
        self.assertIn("start_degrees,end_degrees,radius", catalog_tool)
        self.assertIn("center-based rounded rectangle", catalog_tool)
        self.assertIn("GameArcRoundRectProbeV12", progress)

    def test_gui_map_mode_research_api(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        catalog_tool = read("reverse/bda_api_catalog.py")
        progress = read("reverse/docs/game_api_verification_progress.md")
        for name in (
            "bda_gui_map_mode_get_like",
            "bda_gui_viewport_extent_get_like",
            "bda_gui_viewport_origin_get_like",
            "bda_gui_window_extent_get_like",
            "bda_gui_window_origin_get_like",
            "bda_gui_map_mode_set_like",
            "bda_gui_viewport_extent_set_like",
            "bda_gui_viewport_origin_set_like",
            "bda_gui_window_extent_set_like",
            "bda_gui_window_origin_set_like",
        ):
            self.assertIn(name, header)
        self.assertIn("context+0x70", catalog_tool)
        self.assertIn("context+0x7c/+0x80", catalog_tool)
        self.assertIn("GameMapModeProbeV13", progress)

    def test_gui_coordinate_transform_research_api(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        catalog_tool = read("reverse/bda_api_catalog.py")
        progress = read("reverse/docs/game_api_verification_progress.md")
        for name in (
            "bda_gui_device_to_logical_point_like",
            "bda_gui_logical_to_device_point_like",
            "bda_gui_map_device_to_logical_point_like",
            "bda_gui_map_logical_to_device_point_like",
        ):
            self.assertIn(name, header)
        self.assertIn("device-to-logical point 原地转换", catalog_tool)
        self.assertIn("map-only logical-to-device point", catalog_tool)
        self.assertIn("GameCoordinateTransformProbeV14", progress)

    def test_gui_clip_select_research_api(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        catalog_tool = read("reverse/bda_api_catalog.py")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        progress = read("reverse/docs/game_api_verification_progress.md")
        self.assertIn("#define BDA_GUI_CLIP_SELECT_RECT_LIKE 0x3e4u", header)
        self.assertIn("bda_gui_clip_select_rect_like", header)
        self.assertIn("context,rect_or_null", catalog_tool)
        self.assertIn("无自定义 region", c200_notes)
        self.assertIn("GameClipSelectProbeV15", progress)

    def test_gui_clip_exclude_research_api(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        catalog_tool = read("reverse/bda_api_catalog.py")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        progress = read("reverse/docs/game_api_verification_progress.md")
        self.assertIn("#define BDA_GUI_CLIP_EXCLUDE_RECT_LIKE 0x3d8u", header)
        self.assertIn("bda_gui_clip_exclude_rect_like", header)
        self.assertIn("最多四个剩余条带", catalog_tool)
        self.assertIn("0x800d2fe4(region,rect)", c200_notes)
        self.assertIn("GameClipExcludeProbeV16", progress)

    def test_gui_clip_union_research_api(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        catalog_tool = read("reverse/bda_api_catalog.py")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        progress = read("reverse/docs/game_api_verification_progress.md")
        self.assertIn("#define BDA_GUI_CLIP_UNION_RECT_LIKE 0x3dcu", header)
        self.assertIn("bda_gui_clip_union_rect_like", header)
        self.assertIn("cached bounds 不随追加扩展", catalog_tool)
        self.assertIn("0x800d3530(region, new_rect)", c200_notes)
        self.assertIn("GameClipUnionProbeV17", progress)

    def test_gui_clip_intersect_research_api(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        catalog_tool = read("reverse/bda_api_catalog.py")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        progress = read("reverse/docs/game_api_verification_progress.md")
        self.assertIn("#define BDA_GUI_CLIP_INTERSECT_RECT_LIKE 0x3e0u", header)
        self.assertIn("bda_gui_clip_intersect_rect_like", header)
        self.assertIn("重新计算 aggregate bounds", catalog_tool)
        self.assertIn("0x800d35f0(context+0x94, intersect_rect)", c200_notes)
        self.assertIn("GameClipIntersectProbeV18", progress)

    def test_game_double_buffer_sprite_probe_is_documented(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        catalog_tool = read("reverse/bda_api_catalog.py")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        game_notes = read("reverse/docs/game_framework_notes.md")
        progress = read("reverse/docs/game_api_verification_progress.md")
        self.assertIn("bda_gui_context_copy_like", header)
        self.assertIn("V19-V21 验证 compatible 合成", catalog_tool)
        self.assertIn("compatible context 可以作为 `+0x418` 的 destination", c200_notes)
        self.assertIn("GUI+0x418(sprite -> back)", game_notes)
        self.assertIn("GameDoubleBufferSpriteProbeV19", progress)
        self.assertIn("FRAMES=0x0001C788", progress)

    def test_game_color_key_sprite_probe_is_documented(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        catalog_tool = read("reverse/bda_api_catalog.py")
        generated_catalogs = (
            read("reverse/docs/api_catalog.md")
            + read("reverse/docs/system_api_tables.md")
        )
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        progress = read("reverse/docs/game_api_verification_progress.md")
        verified = read("docs/verified/touch_window_lifecycle_api.md")
        self.assertIn("BDA_GUI_COLOR_KEY_MAGENTA_RGB565_LIKE 0xf81fu", header)
        self.assertIn("BDA_GUI_COLOR_KEY_BLACK_RGB565_LIKE 0x0000u", header)
        self.assertIn("BDA_GUI_OPAQUE_BLACK_RGB565_LIKE 0x0001u", header)
        self.assertIn("color_key_rgb565", header)
        self.assertNotIn("color_key_rgb565_or_zero", header)
        self.assertNotIn(
            "`BDA_GUI_COLOR_KEY_BLACK_RGB565_LIKE`",
            generated_catalogs,
        )
        self.assertNotIn(
            "`BDA_GUI_OPAQUE_BLACK_RGB565_LIKE`",
            generated_catalogs,
        )
        self.assertIn("0xf81f 洋红透明键", catalog_tool)
        self.assertIn("雷霆战机 `0x81c10db8`", c200_notes)
        self.assertIn("GameColorKeySpriteProbeV20", progress)
        self.assertIn("COLOR KEY=0x0000F81F", progress)
        self.assertIn("该\n推断撤回", verified)

    def test_game_dirty_rect_sprite_probe_is_documented(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        catalog_tool = read("reverse/bda_api_catalog.py")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        game_notes = read("reverse/docs/game_framework_notes.md")
        progress = read("reverse/docs/game_api_verification_progress.md")
        readme = read("reverse/docs/README.md")
        self.assertIn("33-pixel-wide back-to-visible dirty present", header)
        self.assertIn("dirty rect 局部提交", catalog_tool)
        self.assertIn("GameDirtyRectSpriteProbeV21", progress)
        self.assertIn("DIRTY WIDTH=0x00000021", progress)
        self.assertIn("clean -> back", c200_notes)
        self.assertIn("最小外接 dirty rect", game_notes)
        self.assertIn("game_dirty_rect_sprite_probe.c", readme)

    def test_gui_blit_entries_document_c200_backend_callbacks(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        readme = read("reverse/docs/README.md")
        api_offsets = read("reverse/docs/api_offsets.md")
        game_notes = read("reverse/docs/game_framework_notes.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = "\n".join([header, c200_notes, readme, api_offsets, game_notes, catalog_tool])
        self.assertIn("GUI +0x3f8 / +0x3fc / +0x400", c200_notes)
        self.assertIn("GUI+0x3f8 -> 0x800c0ba8", c200_notes)
        self.assertIn("GUI+0x3fc -> 0x800c0bf0", c200_notes)
        self.assertIn("GUI+0x400 -> 0x800c0c90", c200_notes)
        self.assertIn("#define BDA_GUI_CAPTURE_REGION_ALLOC_LIKE 0x3fcu", header)
        self.assertIn("void *bda_gui_capture_region_alloc_like(s32 x, s32 y, s32 width, s32 height)", header)
        self.assertIn("void *bda_gui_capture_region_alloc_like(s32 x, s32 y, s32 width, s32 height);", readme)
        self.assertIn("x, y, height, width, buffer", combined)
        self.assertIn("x, y, width, height", combined)
        self.assertIn("width*height*bytes_per_pixel", header)
        self.assertIn("width * height * bytes_per_pixel", c200_notes)
        self.assertIn("返回的 buffer 必须用 bda_free() 释放", header)
        self.assertIn("返回 pointer 用完必须 `bda_free()`", c200_notes)
        self.assertIn("返回 buffer 需 bda_free()", api_offsets + "\n" + game_notes)
        self.assertIn("名片.bda", c200_notes)
        self.assertIn("stack+0x10", c200_notes)
        self.assertIn("+0x84", combined)
        self.assertIn("+0x80", combined)
        self.assertIn("+0x44", combined)
        self.assertIn("clip/prepare", combined)
        self.assertIn("height 在 width 前", combined)
        self.assertIn("low-level framebuffer/backend API", c200_notes)

    def test_touch_position_api_is_verified_on_hardware(self) -> None:
        public = public_sdk_text()
        verified = read("docs/verified/touch_position_api.md")
        failure = read("reverse/docs/touch_press_fixed_va_failure.md")
        probe = read("reverse/examples/gameboy_fast_touch_hardware_probe.c")
        combined = public + "\n" + verified + "\n" + probe

        self.assertIn("BDA_SDK_INTERNAL_GUI_TOUCH_POSITION    0x6c0u", public)
        self.assertIn("bda_gui_touch_position(u16 *x, u16 *y)", public)
        self.assertNotIn("bda_touch_pressed_9588", public)
        self.assertNotIn("0x80059f68u", public)
        self.assertIn("9,831,102", verified)
        self.assertIn("不返回触摸是否按下", verified)
        self.assertIn("BDA_MSG_TOUCH_COORDINATE", verified)
        self.assertIn("BDA_MSG_TOUCH_RELEASE", verified)
        self.assertIn("FastTouchV3", combined)
        self.assertIn("第一次调用", failure)
        self.assertIn("禁止在真机运行", failure)
        self.assertTrue(
            (ROOT / "reverse/docs/assets/touch_press_emulator_compat.png").is_file()
        )

    def test_raw_input_event_api_is_verified_on_hardware(self) -> None:
        public = public_sdk_text()
        verified = read("docs/verified/raw_input_event_api.md")
        progress = read("reverse/docs/game_api_verification_progress.md")
        gameboy = read("reverse/docs/gameboy_notes.md")
        indexes = (
            read("docs/README.md")
            + read("docs/sdk_api_layout.md")
            + read("docs/verified/README.md")
            + read("docs/verified/public_api_policy.md")
        )

        self.assertIn("BDA_SDK_INTERNAL_GUI_RAW_EVENT_FETCH", public)
        self.assertIn("bda_gui_raw_event_t", public)
        self.assertIn("bda_gui_raw_event_fetch", public)
        self.assertIn("BDA_INPUT_EVENT_TOUCH_DOWN 8u", public)
        self.assertIn("BDA_INPUT_EVENT_TOUCH_MOVE 12u", public)
        self.assertIn("BDA_INPUT_EVENT_TOUCH_UP   11u", public)
        self.assertNotIn("bda_gui_state_query", public)
        self.assertNotIn("BDA_SDK_INTERNAL_GUI_STATE_QUERY", public)

        for phrase in [
            "COUNTS C3=361 C8=15 C9=11 C10=7 C11=17 C12=109",
            "前 512 条详细事件中",
            "code=3",
            "不能一直读取到",
            "全局消费型输入流",
            "5945bdd2646cc9e4462b5a45413f970e4697e6d613b7da3a810c9d2e628f34a8",
        ]:
            self.assertIn(phrase, verified)

        self.assertIn("raw_input_event_api.md", indexes)
        self.assertIn("RET == CODE", progress)
        self.assertIn("bda_gui_raw_event_fetch()", gameboy)
        self.assertTrue(
            (ROOT / "docs/verified/assets/gameboy_raw_event_v1_hardware_log.txt").is_file()
        )

    def test_touch_window_lifecycle_is_verified_on_hardware(self) -> None:
        stable_header = public_sdk_text()
        candidate_header = SDK_HEADER.read_text(encoding="utf-8")
        verified = read("docs/verified/touch_window_lifecycle_api.md")
        verified_index = read("docs/verified/README.md")
        include_readme = read("docs/verified/public_api_policy.md")
        sdk_readme = read("docs/sdk_api_layout.md")
        doc_readme = read("reverse/docs/README.md")
        source = read("reverse/examples/touch_input_stage_probe.c")
        v12_source = read("reverse/examples/touch_input_stage_probe_v12.c")
        v13_source = read("reverse/examples/touch_input_stage_probe_v13.c")
        v14_source = read("reverse/examples/touch_input_stage_probe_v14.c")
        v15_source = read("reverse/examples/touch_input_stage_probe_v15.c")
        v16_source = read("reverse/examples/touch_input_stage_probe_v16.c")
        v17_source = read("reverse/examples/touch_input_stage_probe_v17.c")
        v18_source = read("reverse/examples/touch_input_stage_probe_v18.c")
        v19_source = read("reverse/examples/touch_input_stage_probe_v19.c")
        v20_source = read("reverse/examples/touch_input_stage_probe_v20.c")
        v21_source = read("reverse/examples/touch_input_stage_probe_v21.c")
        v22_source = read("reverse/examples/touch_input_stage_probe_v22.c")
        v23_source = read("reverse/examples/touch_input_stage_probe_v23.c")
        public_example = read("example/input/touch_crosshair/touch_crosshair_demo.c")

        self.assertIn("BDA_SDK_INTERNAL_GUI_CLOSE_FRAME       0x17cu", stable_header)
        self.assertIn("void bda_gui_close_frame(bda_handle_t handle)", stable_header)
        self.assertIn("GUI+0x17c has no stable return value", stable_header)
        self.assertIn("BDA_MSG_TOUCH_COORDINATE    0x0001u", stable_header)
        self.assertIn("BDA_MSG_TOUCH_RELEASE       0x0002u", stable_header)
        self.assertIn("BDA_SDK_INTERNAL_GUI_OBJECT_DRAW_BEGIN 0x0e4u", stable_header)
        self.assertIn("BDA_SDK_INTERNAL_GUI_OBJECT_DRAW_END   0x0e8u", stable_header)
        self.assertIn("bda_gui_object_draw_begin(bda_handle_t object)", stable_header)
        self.assertIn("bda_gui_object_draw_end(", stable_header)
        self.assertIn("void bda_gui_end_draw(bda_handle_t draw_context)", stable_header)
        self.assertIn("无稳定返回值", candidate_header)

        for phrase in [
            "BBK 9588 真机",
            "首个 standalone BDA",
            "BDA_MSG_TOUCH_COORDINATE = 1  触摸按下/坐标更新",
            "BDA_MSG_TOUCH_RELEASE    = 2  触摸抬起",
            "stop -> release -> event poll 结束/detach -> end draw -> close -> bda_main return",
            "void bda_gui_close_frame()",
            "`ab`",
            "6362f946fbd84c74937e75290c082df36be7356dc10a30aa9044e96680da9aa6",
            "WAITING MESSAGE 1/2` 会被绘制三次",
            "V12 尚未完成真机闭环",
            "V13 的文字仍逐字出现在屏幕上",
            "2052d02bcc11f2db8378190fa7cf93435dcee3a796b2b0e7f4c158f39fb73f7a",
            "V14/V15 离屏复制反例",
            "a0          source_context",
            "V15 把两个 context 对调后",
            "首帧 `WAITING MESSAGE` 已显示为黑色",
            "V17 尚未完成真机验证",
            "V18 真机结果",
            "V20 真机",
            "V21 真机日志",
            "V22 真机日志",
            "V23 已在同一 BBK 9588 真机验证通过",
            "9d872884482e8539487cdead9f293d70ba5038572a43a2562c63cc197cbb4aee",
        ]:
            self.assertIn(phrase, verified)

        self.assertIn("touch_window_lifecycle_api.md", verified_index)
        self.assertIn("touch_window_lifecycle_api.md", include_readme)
        self.assertIn("touch_window_lifecycle_api.md", sdk_readme)
        self.assertIn("touch_window_lifecycle_api.md", doc_readme)

        self.assertIn("bda_gui_close_frame(g_frame);", source)
        self.assertNotIn("probe_close_frame", source)
        self.assertNotIn("0x13cu", source)
        self.assertIn("#define TOUCH_STAGE_VERSION 12", v12_source)
        self.assertIn("#define TOUCH_STAGE_VERSION 13", v13_source)
        self.assertIn("#define TOUCH_STAGE_VERSION 14", v14_source)
        self.assertIn("#define TOUCH_STAGE_VERSION 15", v15_source)
        self.assertIn("#define TOUCH_STAGE_VERSION 16", v16_source)
        self.assertIn("#define TOUCH_STAGE_VERSION 17", v17_source)
        self.assertIn("#define TOUCH_STAGE_VERSION 18", v18_source)
        self.assertIn("#define TOUCH_STAGE_VERSION 19", v19_source)
        self.assertIn("#define TOUCH_STAGE_VERSION 20", v20_source)
        self.assertIn("#define TOUCH_STAGE_VERSION 21", v21_source)
        self.assertIn("#define TOUCH_STAGE_VERSION 22", v22_source)
        self.assertIn("#define TOUCH_STAGE_VERSION 23", v23_source)
        self.assertIn("TOUCH_STAGE_COALESCE_STARTUP_REDRAWS 1", source)
        self.assertIn("TOUCH_STAGE_USE_OBJECT_PAINT 1", source)
        self.assertIn("bda_gui_object_draw_begin(g_frame)", source)
        self.assertIn("bda_gui_object_draw_end(g_frame, object_draw)", source)
        self.assertIn("bda_sdk_internal_gui(), 0x310u", source)
        self.assertIn("bda_sdk_internal_gui(), 0x418u", source)
        self.assertIn("bda_sdk_internal_gui(), 0x314u", source)
        self.assertIn("TOUCH_STAGE_COPY_DESTINATION_FIRST 1", source)
        self.assertIn("TOUCH_STAGE_COMPAT_WHITE_SURFACE 1", source)
        self.assertIn("TOUCH_STAGE_SKIP_OLD_ERASE 1", source)
        self.assertIn("NO OLD ERASE", source)
        self.assertIn("TOUCH_STAGE_USE_DRAW_GUARD 0", source)
        self.assertIn("NO DRAW GUARD", source)
        self.assertIn("TOUCH_STAGE_DRAW_IN_WNDPROC 1", source)
        self.assertIn("TOUCH_STAGE_REQUEST_OBJECT_REDRAW 1", source)
        self.assertIn("TOUCH_STAGE_DIRECT_REDRAW_NOTIFY 1", source)
        self.assertIn("bda_sdk_internal_gui(), 0x0e0u", source)
        self.assertIn("bda_sdk_internal_gui(), 0x03cu", source)
        self.assertIn("REDRAW REQUEST=", source)
        self.assertIn("BEFORE REDRAW NOTIFY", source)
        self.assertIn("REDRAW NOTIFY=", source)
        self.assertIn("REDRAW CALLBACK", source)
        self.assertIn("TOUCH_STAGE_PRESENT_AFTER_OBJECT_PAINT 1", source)
        self.assertIn("BEFORE DYNAMIC PRESENT", source)
        self.assertIn("DYNAMIC PRESENT=", source)
        self.assertIn("TOUCH_STAGE_VECTOR_DYNAMIC_STATUS 1", source)
        self.assertIn("VECTOR DYNAMIC DRAW", source)
        self.assertIn("touch_stage_draw_bitmap_text", source)
        self.assertIn("draw_initial_scene", public_example)
        self.assertIn("draw_dynamic_scene", public_example)
        self.assertIn("draw_bitmap_text", public_example)
        self.assertIn("bda_gui_object_draw_begin(g_frame)", public_example)
        self.assertIn("bda_gui_draw_guard_begin();", public_example)
        self.assertNotIn("WAITING FOR TOUCH", public_example)
        self.assertIn("draw_scene();", source)
        self.assertIn("foreground = (u32)bda_gui_rgb(g_draw, 0, 0, 0);", source)
        self.assertIn("g_initial_redraw_suppressed", source)
        self.assertIn("g_need_draw = 0;", source)

        stop_at = public_example.index("bda_gui_frame_stop(g_frame)")
        release_at = public_example.index("bda_gui_frame_release(g_frame)")
        close_at = public_example.index("bda_gui_close_frame(g_frame)")
        self.assertLess(stop_at, release_at)
        self.assertLess(release_at, close_at)
        self.assertIn("pump_result = bda_gui_event_pump_frame_once", public_example)
        self.assertIn("queue_touch_event(message, lparam)", public_example)
        self.assertIn("message == BDA_MSG_TOUCH_COORDINATE", public_example)
        self.assertIn("message == BDA_MSG_TOUCH_RELEASE", public_example)
        self.assertIn("g_initial_redraw_suppressed", public_example)
        self.assertIn("g_need_draw = 0;", public_example)

    def test_gui_draw_object_create_is_single_index_table_lookup(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        stable_header = public_sdk_text()
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        game_notes = read("reverse/docs/game_framework_notes.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = header + "\n" + c200_notes + "\n" + game_notes + "\n" + catalog_tool
        self.assertIn("bda_gui_draw_object_create_like(u32 kind)", header)
        self.assertIn("bda_gui_draw_object_create(u32 kind)", stable_header)
        self.assertNotIn("bda_gui_frame_surface", header + stable_header)
        self.assertNotIn("bda_gui_draw_object_create_like(u32 a0, u32 a1, u32 a2, u32 a3)", header)
        self.assertIn("GUI +0x2fc: `BDA_GUI_DRAW_OBJECT_CREATE_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x800bd36c`", c200_notes)
        self.assertIn("只读取 `a0=kind/index`", c200_notes)
        self.assertIn("kind < 0x11", c200_notes)
        self.assertIn("0x80825640 + kind*4", c200_notes)
        self.assertIn("旧 4 参数 wrapper", c200_notes)
        self.assertIn("kind=15", c200_notes)
        self.assertIn("kind=0x10", c200_notes + "\n" + header + "\n" + game_notes)
        self.assertIn("GUI+0x334/+0x33c", c200_notes + "\n" + game_notes)
        self.assertIn("surface 或 context handle", c200_notes + "\n" + header)
        self.assertIn("frame/control lifecycle 已经建立", c200_notes)
        self.assertIn("不是 framebuffer allocator 或最小绘图入口", c200_notes)
        self.assertIn("不要把 `bda_gui_draw_object_create_like(15)+register_frame`", c200_notes)
        self.assertIn("不是 framebuffer allocator", game_notes)
        self.assertIn("不是 no-template BDA 的 framebuffer allocator", game_notes)
        self.assertIn("surface=0", game_notes)
        self.assertIn("bda_gui_draw_object_create_like(kind)", game_notes)
        self.assertIn("只读取 kind/index", catalog_tool)

    def test_gui_current_draw_requires_handle_and_documents_mode0(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        window_notes = read("reverse/docs/window_notes.md")
        api_offsets = read("reverse/docs/api_offsets.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        examples = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "reverse/examples").glob("*.c"))
        combined = header + "\n" + c200_notes + "\n" + window_notes + "\n" + api_offsets + "\n" + catalog_tool
        self.assertIn("bda_gui_current_draw_like(bda_handle_t handle)", header)
        self.assertNotIn("bda_gui_current_draw_like(void)", header)
        self.assertNotIn("bda_gui_current_draw_like()", examples)
        self.assertIn("GUI +0x304 / +0x308 / +0x30c", c200_notes)
        self.assertIn("GUI+0x304 -> 0x800bceec", c200_notes)
        self.assertIn("GUI+0x308 -> 0x800bce50", c200_notes)
        self.assertIn("a0=handle", c200_notes)
        self.assertIn("0x800bd678(context_slot, handle, 0)", c200_notes)
        self.assertIn("0x800bd678(context_slot, handle, 1)", c200_notes)
        self.assertIn("GUI+0x304(frame_handle)", window_notes)
        self.assertIn("#define BDA_MSG_DRAW_CONTEXT_ATTACH_LIKE 0x0060u", header)
        self.assertIn("#define BDA_MSG_DRAW_CONTEXT_DETACH_LIKE 0x0066u", header)
        self.assertIn("BDA_MSG_DRAW_CONTEXT_ATTACH_LIKE", read("reverse/docs/input_notes.md"))
        self.assertIn("BDA_MSG_DRAW_CONTEXT_DETACH_LIKE", read("reverse/docs/input_notes.md"))
        self.assertIn("wndproc message `0x60`", c200_notes + "\n" + header)
        self.assertIn("GUI+0x304(object)", c200_notes)
        self.assertIn("message `0x66`", c200_notes)
        self.assertIn("GUI+0x30c(context) -> GUI+0x088(object) -> GUI+0x04c(object)", c200_notes)
        self.assertIn("frame/control lifecycle 信号", read("reverse/docs/input_notes.md"))
        self.assertIn("BDA_MSG_DRAW_CONTEXT_ATTACH_LIKE", window_notes)
        self.assertIn("BDA_MSG_DRAW_CONTEXT_DETACH_LIKE", window_notes)
        self.assertIn("5 个普通 draw context", header + "\n" + c200_notes + "\n" + window_notes)
        self.assertIn("0x804a60c0", c200_notes)
        self.assertIn("0x804a64e4", c200_notes)
        self.assertIn("0x804a65b8", c200_notes)
        self.assertIn("满池后还会计算越界地址", window_notes)
        self.assertIn("mode=0", combined)
        self.assertIn("mode=1", combined)
        self.assertIn("旧的无参数", c200_notes)
        self.assertIn("不是无参数 getter", header + "\n" + window_notes)
        self.assertIn("不是查询全局\ndraw handle 的无状态 getter", api_offsets)
        self.assertIn("不会\n * 创建 frame/window 生命周期", header)
        self.assertNotIn("`GUI+0x304` 与 `GUI+0x308` 两条 draw handle 路径的适用场景差异", window_notes)
        self.assertIn("从 5 个普通 slot 取/初始化 context，并以 mode=0", catalog_tool)
        self.assertIn("从 5 个普通 slot 取/初始化 context，并以 mode=1", catalog_tool)
        bbvm_black_probe = read("reverse/examples/window_text_bbvm_black_probe.c")
        bbvm_hold_probe = read("reverse/examples/window_text_bbvm_black_hold_probe.c")
        bbvm_style_probe = read("reverse/examples/window_text_bbvm_style_probe.c")
        for source in [bbvm_black_probe, bbvm_hold_probe, bbvm_style_probe]:
            self.assertIn("BDA_MSG_DRAW_CONTEXT_ATTACH_LIKE", source)
            self.assertIn("BDA_MSG_DRAW_CONTEXT_DETACH_LIKE", source)

    def test_gui_end_and_surface_flush_are_void_cleanup_apis(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        api_offsets = read("reverse/docs/api_offsets.md")
        paint_notes = read("reverse/docs/paint_notes.md")
        paint_report = read("reverse/reports/paint_bda_report.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = header + "\n" + readme + "\n" + api_offsets + "\n" + paint_notes + "\n" + paint_report + "\n" + c200_notes + "\n" + catalog_tool
        self.assertIn("void bda_gui_end_draw_like(bda_handle_t draw_handle)", header)
        self.assertNotIn("int bda_gui_end_draw_like(bda_handle_t draw_handle)", combined)
        self.assertIn("void bda_gui_surface_flush_like(bda_handle_t context)", combined)
        self.assertNotIn("int bda_gui_surface_flush_like(bda_handle_t surface)", combined)
        self.assertIn("GUI+0x30c -> 0x800bd4b0", c200_notes)
        self.assertIn("没有稳定 return value", c200_notes)
        self.assertIn("context+0x94", c200_notes)
        self.assertIn("context+0xb0", c200_notes)
        self.assertIn("GUI+0x314 -> 0x800bd584", c200_notes)
        self.assertIn("draw backend `+0x34", c200_notes)
        self.assertIn("MEM_FREE(context)", c200_notes)
        self.assertIn("flush 会释放 context", readme)
        self.assertIn("flush-and-free", c200_notes)
        self.assertIn("surface/canvas flush-and-free", paint_notes + "\n" + paint_report)
        self.assertIn("context+0x94/+0xb0", paint_notes + "\n" + paint_report)
        self.assertIn("它不是单纯 invalidate", paint_report)
        self.assertNotIn("`GUI+0x314` 是 present/flush 还是 invalidate", paint_report)
        self.assertIn("无稳定 return value", catalog_tool)
        self.assertIn("释放 context", catalog_tool)

    def test_gui_object_draw_end_is_void_cleanup_api(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = header + "\n" + readme + "\n" + c200_notes + "\n" + catalog_tool
        self.assertIn("bda_gui_object_draw_begin_like(bda_handle_t handle)", header)
        self.assertIn("void bda_gui_object_draw_end_like(bda_handle_t handle, bda_handle_t draw_handle)", combined)
        self.assertNotIn("int bda_gui_object_draw_end_like(bda_handle_t handle, bda_handle_t draw_handle)", combined)
        self.assertIn("GUI +0x0e4 / +0x0e8", c200_notes)
        self.assertIn("GUI+0x0e4 -> 0x800ce928", c200_notes)
        self.assertIn("GUI+0x0e8 -> 0x800ce9f0", c200_notes)
        self.assertIn("a0=object", c200_notes)
        self.assertIn("a1=draw_context", c200_notes)
        self.assertIn("object-level wrapper", c200_notes)
        self.assertIn("0x800bce50(object)", c200_notes)
        self.assertIn("object+0x54+0x1c", c200_notes)
        self.assertIn("object+0x7c", header + "\n" + c200_notes + "\n" + read("reverse/docs/window_notes.md"))
        self.assertIn("0x800b3950()", c200_notes)
        self.assertIn("0x800bd4b0(draw_context)", c200_notes)
        self.assertIn("必须传回同一个 object", c200_notes + "\n" + read("reverse/docs/window_notes.md"))
        self.assertIn("不能把它当作无状态 present/flush", c200_notes + "\n" + read("reverse/docs/window_notes.md"))
        self.assertIn("不要把它当作\n * 独立的 framebuffer/present API", header)
        self.assertIn("没有稳定 return value", c200_notes)
        self.assertIn("`void` cleanup wrapper", c200_notes)
        self.assertIn("调用 GUI+0x308 取得 draw context 并递增 draw 计数", catalog_tool)
        self.assertIn("调用 GUI+0x30c(draw_context)，无稳定 return value", catalog_tool)

    def test_gui_object_op_is_single_object_refresh_message(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        window_notes = read("reverse/docs/window_notes.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        examples = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "reverse/examples").glob("*.c"))
        combined = header + "\n" + readme + "\n" + c200_notes + "\n" + window_notes + "\n" + catalog_tool
        self.assertIn("bda_gui_object_op_like(bda_handle_t object)", combined)
        self.assertNotIn("bda_gui_object_op_like(u32 object, u32 op, u32 arg)", combined)
        self.assertNotIn("bda_gui_object_op_like((u32)g_frame, 0, 0)", examples)
        self.assertIn("GUI +0x0e0: `BDA_GUI_OBJECT_OP_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x800ccf64`", c200_notes)
        self.assertIn("只保存并使用 `a0=object`", c200_notes)
        self.assertIn("没有读取 `a1/a2`", c200_notes)
        self.assertIn("0x800ccc58(object)", c200_notes)
        self.assertIn("0x800dced0(object, 0xb1, 0, 0)", c200_notes)
        self.assertIn("内部 `0xb1`", c200_notes)
        self.assertIn("GUI+0x0e0(frame)", window_notes)
        self.assertIn("只读取 object", catalog_tool)

    def test_gui_region_draw_uses_five_argument_c200_abi(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        game_notes = read("reverse/docs/game_framework_notes.md")
        paint_notes = read("reverse/docs/paint_notes.md")
        paint_report = read("reverse/reports/paint_bda_report.md")
        album_report = read("reverse/reports/album_bda_report.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = header + "\n" + c200_notes + "\n" + game_notes + "\n" + paint_notes + "\n" + paint_report + "\n" + album_report + "\n" + catalog_tool
        self.assertIn(
            "bda_gui_region_draw_like(bda_handle_t context, s32 x, s32 y, s32 width, s32 height)",
            header,
        )
        self.assertNotIn("bda_gui_region_draw_like(u32 a0, u32 a1, u32 a2, u32 a3)", header)
        self.assertIn("GUI +0x40c: `BDA_GUI_REGION_DRAW_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x800b2e30`", c200_notes)
        self.assertIn("stack+0x10", c200_notes)
        self.assertIn("caller stack+0x10", header)
        self.assertIn("sp+0x10 = height", paint_report)
        self.assertIn("height", combined)
        self.assertIn("x/y/x+width/y+height", c200_notes)
        self.assertIn("x/y/x+width/y+height", paint_notes)
        self.assertIn("0x800c04d8(rect)", c200_notes)
        self.assertIn("0x800c056c(rect, rect, context+0xb0)", c200_notes)
        self.assertIn("context+0xb0", paint_notes + "\n" + paint_report)
        self.assertIn("+0x7c", c200_notes)
        self.assertIn("旧 4 参数形状少传", c200_notes)
        self.assertIn("它不是独立 fill-rect API", paint_notes + "\n" + paint_report)
        self.assertIn("context,x,y,width,height 五参数", catalog_tool)
        self.assertIn("GUI +0x40c   11 次  region draw/copy helper", album_report)
        self.assertIn("GUI +0x40c  -> context,x,y,width,height region draw/copy", album_report)
        self.assertNotIn("`GUI+0x40c`、`GUI+0x418` 的完整 stack 参数语义仍需", paint_report)
        self.assertNotIn("GUI +0x40c   11 次  区域绘制辅助候选", album_report)
        self.assertNotIn("GUI+0x40c  -> 区域绘制候选", album_report)

    def test_gui_rect_prepare_is_documented_as_five_arg_rect_writer(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        readme = read("reverse/docs/README.md")
        api_offsets = read("reverse/docs/api_offsets.md")
        picture_notes = read("reverse/docs/picture_notes.md")
        schedule_report = read("reverse/reports/schedule_bda_report.md")
        ninecourse_report = read("reverse/reports/ninecourse_bda_report.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = "\n".join([header, c200_notes, readme, api_offsets, picture_notes, schedule_report, ninecourse_report, catalog_tool])
        self.assertIn("#define BDA_GUI_OBJECT_RECT_LIKE    0x0a4u", header)
        self.assertIn("int bda_gui_object_rect_like(bda_handle_t handle, bda_rect_like_t *rect)", header)
        self.assertIn("int bda_gui_object_rect_like(bda_handle_t handle, bda_rect_like_t *rect);", readme)
        self.assertIn("GUI +0x0a4: `BDA_GUI_OBJECT_RECT_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x800ce3c8`", c200_notes)
        self.assertIn("a0=handle", c200_notes)
        self.assertIn("a1=rect", c200_notes)
        self.assertIn("0x80825830..0x8082583c", c200_notes)
        self.assertIn("handle+0x1c - handle+0x14", c200_notes)
        self.assertIn("handle+0x20 - handle+0x18", c200_notes)
        self.assertIn("黄冈教辅.bda", c200_notes)
        self.assertIn("client rect 查询", combined)
        self.assertIn("不是屏幕绝对坐标", c200_notes)
        self.assertIn("不要把它当成当前 BDA window 已经创建成功的证据", c200_notes)
        self.assertIn("BDA_GUI_RECT_PREPARE_LIKE   0x430u", header)
        self.assertIn("GUI +0x430: `BDA_GUI_RECT_PREPARE_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x800c0410`", c200_notes)
        self.assertIn("a0=rect", c200_notes)
        self.assertIn("a1=x0", c200_notes)
        self.assertIn("a2=y0", c200_notes)
        self.assertIn("a3=x1", c200_notes)
        self.assertIn("stack+0x10", combined)
        self.assertIn("rect+0x00=x0", c200_notes)
        self.assertIn("rect+0x0c=y1", c200_notes)
        self.assertIn("不会检查空 pointer", c200_notes)
        self.assertIn("rect,x0,y0,x1,y1 五参数", combined)
        self.assertIn("static inline void bda_gui_rect_prepare_like", header)
        self.assertIn("写入 16 byte rect record", header)
        self.assertIn("bda_gui_rect_prepare_like(rect, x0, y0, x1, y1)", combined)
        self.assertIn("bda_call5", header + c200_notes + picture_notes)
        self.assertIn("至少 16 byte 可写内存", combined)
        self.assertIn("rect prepare / rect contains 调用对", schedule_report + "\n" + ninecourse_report + "\n" + picture_notes)
        self.assertIn("GUI+0x430                  rect prepare；写 x0/y0/x1/y1", schedule_report)
        self.assertIn("`GUI+0x430` 已可按 rect prepare 使用", schedule_report)
        self.assertNotIn("结构体签名仍需继续逆向", combined)
        self.assertNotIn("`GUI+0x430` 应继续作为矩形/paint 辅助候选跟踪", schedule_report)

    def test_gui_rect_contains_is_not_documented_as_resource_draw_api(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        picture_notes = read("reverse/docs/picture_notes.md")
        ebook_report = read("reverse/reports/ebook_bda_report.md")
        schedule_report = read("reverse/reports/schedule_bda_report.md")
        ninecourse_report = read("reverse/reports/ninecourse_bda_report.md")
        combined = "\n".join([header, c200_notes, picture_notes, ebook_report, schedule_report, ninecourse_report])
        self.assertIn("BDA_GUI_RECT_CONTAINS_LIKE", header)
        self.assertIn("bda_gui_rect_contains_like", header)
        self.assertIn("判断点是否落在 rect 内", header)
        self.assertIn("GUI +0x46c: `BDA_GUI_RECT_CONTAINS_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x800c0818`", c200_notes)
        self.assertIn("rect[0] <= x && x < rect[2] && rect[1] <= y && y < rect[3]", combined)
        self.assertIn("不是 image draw 或\nresource loader", picture_notes)
        self.assertIn("待测试点坐标", picture_notes)
        self.assertIn("GUI+0x46c                  rect contains；判断点是否在 rect 内", schedule_report)
        self.assertIn("`GUI+0x46c` 已可按 rect contains 使用", schedule_report)
        self.assertIn("点-in-rect 判断", ninecourse_report)
        self.assertNotIn("GUI+0x46c                  资源/图片辅助", schedule_report)
        self.assertNotIn("`GUI+0x46c` 仍属于资源/图片辅助类", schedule_report)
        self.assertNotIn("GUI +0x430/+0x46c  矩形/资源辅助族", schedule_report + "\n" + ninecourse_report)
        self.assertNotIn("GUI+0x430/+0x46c       矩形/资源辅助族", ninecourse_report)

    def test_gui_draw_text_extra_parameter_matches_c200_abi(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        text_notes = read("reverse/docs/text_notes.md")
        window_notes = read("reverse/docs/window_notes.md")
        notepad_report = read("reverse/reports/notepad_bda_report.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = "\n".join([
            header,
            text_notes,
            window_notes,
            notepad_report,
            c200_notes,
            catalog_tool,
        ])
        self.assertIn("bda_gui_draw_text_like(bda_handle_t handle, s32 x, s32 y, const char *text, s32 extra)", header)
        self.assertIn("GUI +0x4f0: `BDA_GUI_DRAW_TEXT_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x800c0d40`", c200_notes)
        self.assertIn("stack+0x10", combined)
        self.assertIn("extra == 0", combined)
        self.assertIn("直接返回 `0`", combined)
        self.assertIn("extra < 0", combined)
        self.assertIn("0x800068c4(text)", combined)
        self.assertIn("0x80119f68(context, context+0x54, text, extra)", c200_notes)
        self.assertIn("0x80119b50(context,x,y,text,extra)", c200_notes)
        self.assertIn("extra=-1", combined)
        self.assertIn("不要把", combined)
        self.assertIn("当作默认值", combined)
        self.assertTrue("`extra=0`" in combined or "`extra == 0`" in combined)
        self.assertIn("`handle=0`", c200_notes)
        self.assertIn("调用可能重启", c200_notes)
        self.assertIn("extra<0 时按 strlen", catalog_tool)
        self.assertIn("0x81c01878..0x81c019e8", notepad_report + text_notes)
        self.assertIn("GUI+0x0e4(frame)", notepad_report + text_notes)
        self.assertIn("GUI+0x0e8(frame, draw)", notepad_report + text_notes)
        self.assertIn("局部调用链中没有 `GUI+0x074", notepad_report)
        self.assertIn('create("medit", "", 0x08083001', notepad_report)
        self.assertIn("GUI+0x040(body_medit, 0x0134, 0, 0x81c197a0)", notepad_report)
        self.assertIn("GUI+0x040(body_medit, 0x0133, 0x19000, output_buffer)", notepad_report)
        self.assertIn("get_dlx_resource(12, text_skin)", notepad_report)
        self.assertIn("取得的是 `text_A.dlx` / `text_B.dlx` 报告中的 `#11`", notepad_report)
        self.assertIn("GUI+0x040(title_medit, 0xf0dd, g_edit_background, 0)", notepad_report)
        self.assertIn("`0xf0dd` 会进入 edit/medit 私有状态", window_notes)
        self.assertIn("它不是\n字体句柄", window_notes)
        self.assertIn("0xf1b4, background_vx", window_notes)
        self.assertIn("control message id，不是 GUI table offset", text_notes)
        self.assertIn("`0x0134` 不是\nGUI table 的 `GUI+0x134`", window_notes)

    def test_gui_draw_vx_uses_vx_header_dimensions_not_public_width_height(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        picture_notes = read("reverse/docs/picture_notes.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = "\n".join([header, readme, c200_notes, picture_notes, catalog_tool])
        self.assertIn("BDA_GUI_DRAW_VX_LIKE", header)
        self.assertIn("GUI +0x540: `BDA_GUI_DRAW_VX_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x800bb864`", c200_notes)
        self.assertIn("bda_gui_draw_vx_like(bda_handle_t handle, s32 x, s32 y, const void *vx_resource)", header)
        self.assertIn("int bda_gui_draw_vx_like(bda_handle_t handle, s32 x, s32 y, const void *vx_resource);", readme)
        self.assertNotIn("bda_gui_draw_vx_like(bda_handle_t handle, s32 x, s32 y, s32 width, s32 height", header + readme)
        self.assertIn("bda_call6", header + c200_notes)
        self.assertIn("第 6 个参数", combined)
        self.assertIn("VX header", combined)
        self.assertIn("+0x06/+0x0a", combined)
        self.assertIn("不是裸 pixel buffer", c200_notes)
        self.assertIn("不再公开旧的 `width,height` 参数", c200_notes)
        for source in (ROOT / "reverse" / "examples").glob("*.c"):
            text = source.read_text(encoding="utf-8")
            self.assertNotIn("bda_gui_draw_vx_like(g_draw, x, y, (s32)g_vx_width", text, source)
            self.assertNotIn("bda_gui_draw_vx_like(g_draw, 0, 40, (s32)g_vx_width", text, source)

    def test_picture_decode_c200_abi_is_documented(self) -> None:
        notes = read("reverse/docs/c200_api_function_notes.md")
        picture_notes = read("reverse/docs/picture_notes.md")
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = "\n".join([header, readme, notes, picture_notes, catalog_tool])
        self.assertIn("GUI +0x670 / +0x808", notes)
        self.assertIn("GUI+0x670 -> 0x800e1f74", notes)
        self.assertIn("GUI+0x808 -> 0x800e2d2c", notes)
        self.assertIn("`a2=path`", notes)
        self.assertIn("bda_gui_decode_bmp_like(void *owner, bda_picture_like_t *out, const char *path, void **out_source_buffer)", header)
        self.assertIn("int bda_gui_decode_bmp_like(void *owner, bda_picture_like_t *out, const char *path, void **out_source_buffer);", readme)
        self.assertNotIn("bda_gui_decode_bmp_like(void *owner, bda_picture_like_t *out, const char *path, void *work)", header + readme + picture_notes)
        self.assertIn("u32 width;", header)
        self.assertIn("u32 height;", header)
        self.assertIn("u32 stride_bytes;", header)
        self.assertIn("u8 bits_per_pixel11;", header)
        self.assertIn("void *source_pixels;", header)
        self.assertIn("width/height/stride_bytes", read("reverse/docs/api_offsets.md") + "\n" + picture_notes)
        self.assertIn("source_pixels", read("reverse/docs/api_offsets.md") + "\n" + picture_notes)
        self.assertIn("void **out_source_buffer", combined)
        self.assertIn("不要传 `NULL`", header + "\n" + notes + "\n" + picture_notes)
        self.assertIn("*out_source_buffer", notes + "\n" + picture_notes)
        self.assertIn("out+0x04 = width", notes + "\n" + picture_notes)
        self.assertIn("out+0x08 = height", notes + "\n" + picture_notes)
        self.assertIn("out+0x0c = width * 2", notes + "\n" + picture_notes)
        self.assertIn("out+0x14 = resource + 0x18", picture_notes)
        self.assertNotIn("dim_a", header + picture_notes)
        self.assertNotIn("dim_b", header + picture_notes)
        self.assertNotIn("owned_pixels", header + picture_notes)
        self.assertNotIn("reserved12", header + picture_notes)
        self.assertIn("signed 8-bit mode", notes)
        self.assertIn("mode==1", catalog_tool)
        self.assertIn("C200 target = 0x800e1f74", picture_notes)
        self.assertIn("C200 target = 0x800e2d2c", picture_notes)
        self.assertIn("不是完整 image control API", combined)

    def test_res_get_state_uses_sized_output_struct(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        api_offsets = read("reverse/docs/api_offsets.md")
        picture_notes = read("reverse/docs/picture_notes.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        self.assertIn("typedef struct bda_res_state_like", header)
        self.assertIn("u32 aux10_minus1", header)
        self.assertIn("static inline void bda_res_get_state_like(bda_res_state_like_t *out_state)", header)
        self.assertIn("void bda_res_get_state_like(bda_res_state_like_t *out_state);", readme)
        self.assertNotIn("static inline int bda_res_get_state_like", header)
        self.assertNotIn("bda_res_get_state_like(void *out_state)", header + readme)
        self.assertIn("RES +0x090: `BDA_RES_GET_STATE_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x80017580`", c200_notes)
        self.assertIn("0xb0003004", header + "\n" + c200_notes)
        self.assertIn("共 7 个 word", c200_notes)
        self.assertIn("`out_state+0x10` 减 1", c200_notes)
        self.assertIn("0x8000528c(saved_cp0_status)", c200_notes)
        self.assertIn("不要读取 return value", c200_notes + "\n" + picture_notes)
        self.assertIn("bda_res_state_like_t", picture_notes)
        self.assertIn("reverse/examples/res_state_demo.c", picture_notes)
        self.assertIn("不是推荐的第一个运行 smoke", picture_notes)
        self.assertIn("bda_res_get_state_like(&g_res_state);", read("reverse/examples/res_state_demo.c"))
        self.assertNotIn("int ret = bda_res_get_state_like", read("reverse/examples/res_state_demo.c"))
        self.assertIn("写 7 个 word", catalog_tool)
        self.assertIn("RES +0x000/+0x004/+0x008/+0x00c/+0x010/+0x040", c200_notes)
        self.assertIn("RES+0x004 -> 0x8013aaf0", c200_notes)
        self.assertIn("RES+0x040 -> 0x80142f50", c200_notes)
        self.assertIn("resource manager lifecycle", c200_notes)
        self.assertIn("不是普通 DLX loader", c200_notes)
        self.assertIn("失败时若全局静音/抑制 flag 未置位，会调用 `GUI+0x2b8` message box", c200_notes)
        self.assertIn("SDK 不公开这些 wrapper", c200_notes + "\n" + api_offsets)
        self.assertIn("RES +0x004  不公开", api_offsets)
        self.assertIn("RES +0x040  不公开", api_offsets)
        self.assertNotIn("BDA_RES_OPEN", header)
        self.assertNotIn("bda_res_open", header)
        self.assertNotIn("bda_load_dlx", header)
        self.assertIn("已删除的历史 misnames", readme)

    def test_gui074_requires_explicit_draw_guard_argument(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        window_notes = read("reverse/docs/window_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        game_notes = read("reverse/docs/game_framework_notes.md")
        thunder_report = read("reverse/reports/thunder_bda_report.md")
        tank_report = read("reverse/reports/tank_bda_report.md")
        combined = "\n".join([header, readme, window_notes, c200_notes, game_notes, thunder_report, tank_report])
        self.assertIn("bda_gui_pump_present_arg_like(u32 draw_guard_enabled)", header)
        self.assertIn("bda_gui_draw_guard_begin_like(void)", header)
        self.assertIn("bda_gui_draw_guard_end_like(void)", header)
        self.assertIn("bda_gui_pump_present_arg_like(u32 draw_guard_enabled);", readme)
        self.assertIn("C200 明确读取 `a0`", c200_notes)
        self.assertIn("删除无参数", window_notes)
        self.assertIn("present/update 边界", combined)
        self.assertIn("不要在每个 tile 后", combined)
        self.assertIn("逐块 present/flip", combined)
        self.assertIn("批量 blit 全部 dirty region", combined)
        self.assertIn("即使只在循环外统一 present", combined)
        self.assertIn("surface/context 生命周期", combined)
        self.assertIn("复原 game shell surface/context 创建、绑定和释放 lifecycle", game_notes)
        self.assertIn("RGB565/stride/dirty region 约定", game_notes)
        self.assertIn("不应再按“哪个负责 present、哪个负责清屏”的二选一理解", game_notes)
        self.assertIn("`GUI+0x3f8` 后接 `GUI+0x6e0`", combined)
        self.assertIn("GUI+0x3f8(0, 0, 0xf0, 0x140, buffer)", combined)
        self.assertIn("GUI+0x400(0, 0, 0xf0, 0x140, buffer)", combined)
        self.assertIn("MEM+0x00c(buffer)", combined)
        self.assertIn("temporary full-screen buffer path", game_notes)
        self.assertIn("object render 调用点也同构", game_notes)
        self.assertIn("GUI+0x414 -> 0x81c0d8e0 GUI+0x0e8 -> 0x81c0d8f4 GUI+0x074(0)", game_notes)
        self.assertIn("GUI+0x414 -> 0x81c00d60 GUI+0x0e8 -> 0x81c00d74 GUI+0x074(0)", game_notes)
        self.assertIn("GUI+0x414 render helper -> GUI+0x0e8 object draw end", header + "\n" + c200_notes)
        self.assertIn("message 0x60: save object=0x81c16c8c -> GUI+0x304(object) -> save context=0x81c16c94", game_notes)
        self.assertIn("message 0x60: save object=0x81c12854 -> GUI+0x304(object) -> save context=0x81c1285c", game_notes)
        self.assertIn("message 0x66: GUI+0x30c(context) -> GUI+0x088(object) -> GUI+0x04c(object)", game_notes)
        self.assertIn("0x81c0d32c  save callback a0 object to 0x81c16c8c", thunder_report)
        self.assertIn("0x81c007ac  save callback a0 object to 0x81c12854", tank_report)
        self.assertIn("GUI+0x35c(context=0x81c16c94", game_notes + "\n" + thunder_report)
        self.assertIn("GUI+0x35c(context=0x81c1285c", game_notes + "\n" + tank_report)
        self.assertIn("GUI+0x2fc(0x10) -> GUI+0x334/0x33c", game_notes)
        self.assertIn("不是创建 game surface", game_notes)
        self.assertIn("这不是创建 context", thunder_report)
        self.assertIn("object=0x81c16c8c", thunder_report)
        self.assertIn("object=0x81c12854", tank_report)
        self.assertIn("game/display state pump", combined)
        self.assertIn("不能直接作为自定义游戏绘图接口", thunder_report)
        self.assertIn("不能证明 bare BDA 可直接用", tank_report)
        self.assertNotIn("更稳的做法是使用小块 static buffer", thunder_report)
        self.assertNotIn("再用 `bda_gui_blit_alt_like` 贴到", thunder_report)
        self.assertIn("不是 tile-level flip API", c200_notes)
        self.assertIn("旧扫雷真机", window_notes + "\n" + thunder_report)
        self.assertIn("反馈", window_notes + "\n" + thunder_report)
        self.assertIn("每个方块逐个 flip", thunder_report)
        self.assertNotIn("bda_gui_pump_present_like(void)", header + readme)
        self.assertNotIn("bda_gui_pump_present_like();", read("reverse/docs/game_framework_notes.md"))
        self.assertNotIn("确认 +0x3f8/+0x400 哪个负责 present", game_notes)
        for source in (ROOT / "reverse" / "examples").glob("*.c"):
            text = source.read_text(encoding="utf-8")
            self.assertNotIn("bda_gui_pump_present_like(", text, source)

    def test_file_selector_adjacent_helpers_match_c200_abi(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        fs_notes = read("reverse/docs/fs_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        self.assertIn("#define BDA_GUI_LIST_NTH_LIKE", header)
        self.assertIn("#define BDA_GUI_LIST_FREE_LIKE", header)
        self.assertIn("bda_gui_file_selector_update_like(\n    bda_file_selector_like_t *selector", header)
        self.assertIn("bda_gui_list_nth_like(void *head, s32 index)", header)
        self.assertIn("bda_gui_list_free_like(void *head)", header)
        self.assertIn("bda_gui_file_selector_update_like(bda_file_selector_like_t *selector);", readme)
        self.assertIn("bda_gui_list_nth_like(void *head, s32 index);", readme)
        self.assertIn("bda_gui_list_free_like(void *head);", readme)
        self.assertIn("不是无参数 get-result", fs_notes)
        self.assertIn("a0=selector descriptor", fs_notes)
        self.assertIn("0x80040864", c200_notes)
        self.assertIn("不是无参数“获取文件选择结果”", c200_notes)
        self.assertIn("GUI+0x6bc -> 0x80042ebc", c200_notes)
        self.assertIn("0x8003e868", c200_notes + "\n" + fs_notes)
        self.assertIn("a0=head", c200_notes + "\n" + fs_notes)
        self.assertIn("不是无参数 selector close", fs_notes)
        self.assertNotIn("BDA_GUI_FILE_SELECTOR_GET_LIKE", header)
        self.assertNotIn("BDA_GUI_FILE_SELECTOR_CLOSE_LIKE", header)
        self.assertNotIn("bda_gui_file_selector_get_like", header + readme + fs_notes)
        self.assertNotIn("bda_gui_file_selector_close_like", header + readme + fs_notes)
        for source in (ROOT / "reverse" / "examples").glob("file_selector*.c"):
            text = source.read_text(encoding="utf-8")
            if "bda_gui_file_selector_update_like(" in text:
                self.assertIn("bda_gui_file_selector_update_like(&selector)", text, source)
            self.assertNotIn("bda_gui_file_selector_get_like", text, source)
            self.assertNotIn("bda_gui_file_selector_close_like", text, source)

    def test_file_selector_open_mode_session_is_documented(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        fs_notes = read("reverse/docs/fs_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        api_offsets = read("reverse/docs/api_offsets.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        selector_probe = read("reverse/examples/file_selector_probe.c")
        self.assertIn("bda_gui_file_selector_open_like(u32 mode)", header)
        self.assertIn("从 a0 读取 mode", header)
        self.assertIn("void *list_head;", header)
        self.assertIn("s32 status;", header)
        self.assertIn("s32 selected_index;", header)
        self.assertIn("s32 sentinel20;", header)
        self.assertIn("s32 sentinel24;", header)
        self.assertIn("u32 sentinel34;", header)
        self.assertIn("u32 sentinel38;", header)
        self.assertIn("u32 list_limit40;", header)
        self.assertIn("s32 sentinel48;", header)
        self.assertIn("u32 result64;", header)
        self.assertIn("selector->selected_index = -1;", header)
        self.assertIn("selector->list_limit40 = 0x1000;", header)
        self.assertIn("selector->result64 = 0;", header)
        self.assertIn("不是 descriptor pointer", fs_notes)
        self.assertIn("不是无害 padding", fs_notes + c200_notes)
        self.assertIn("list_limit40", api_offsets + c200_notes)
        self.assertIn("result64", api_offsets + c200_notes)
        self.assertIn("selector.selected_index = -1;", selector_probe)
        self.assertIn("a0=mode", api_offsets)
        self.assertIn("GUI +0x6a8: `BDA_GUI_FILE_SELECTOR_OPEN_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x80021334`", c200_notes)
        self.assertIn("0x8001f344", c200_notes)
        self.assertIn("0x80473fe4", c200_notes)
        self.assertIn("0x800bd36c(15)", c200_notes)
        self.assertIn("0x800cc1c8", c200_notes)
        self.assertIn("0x800dbfd0", c200_notes)
        self.assertIn("0x800de378", c200_notes)
        self.assertIn("0x800dd4b8", c200_notes)
        self.assertIn("0x800cdffc", c200_notes)
        self.assertIn("不要把 selector descriptor", c200_notes)
        self.assertIn("a0=mode", catalog_tool)
        self.assertNotIn("reserved1c", header + selector_probe + fs_notes + api_offsets)
        self.assertNotIn("reserved40", header + selector_probe + fs_notes + api_offsets)
        self.assertNotIn("reserved64", header + selector_probe + fs_notes + api_offsets)
        self.assertNotIn("bda_gui_file_selector_open_like(bda_file_selector_like_t", header)
        self.assertNotIn("bda_gui_file_selector_open_like(void *selector", header)

    def test_deprecated_dlx_loader_aliases_are_removed_from_public_sdk(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        removed = [
            "BDA_RES_LOAD_DLX",
            "bda_load_dlx_ex",
            "bda_load_dlx(",
            "bda_load_dlx_gui",
            "bda_load_dlx_fs",
            "bda_load_dlx_mem",
            "bda_load_dlx_res",
            "bda_file_selector_load_default_skin_like",
            "bda_gui_create_ex",
            "BDA_MSG_TOUCH_B_LIKE",
        ]
        for name in removed:
            self.assertNotIn(name, header)
        self.assertIn("bda_res_trace_like", header)
        self.assertIn("bda_gui_create_window_like", header)
        self.assertIn("BDA_MSG_REDRAW_INPUT_LIKE", header)
        self.assertIn("bda_file_selector_init_like", header)

    def test_gui_create_requires_real_parent_frame_lifecycle(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        api_offsets = read("reverse/docs/api_offsets.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        system_notes = read("reverse/docs/system_bin_notes.md")
        text_notes = read("reverse/docs/text_notes.md")
        window_notes = read("reverse/docs/window_notes.md")
        combined = "\n".join([header, api_offsets, c200_notes, system_notes, text_notes, window_notes])
        self.assertIn("bda_gui_create_window_like", header)
        self.assertIn("GUI +0x1a4: `BDA_GUI_CREATE`", c200_notes)
        self.assertIn("这个 wrapper 只固定 ABI", header)
        self.assertIn("真实 parent/frame lifecycle", header + "\n" + api_offsets + "\n" + system_notes)
        self.assertIn("不要在裸 bda_main() 中用 parent=0 创建\n * edit/listbox 当作 GUI bootstrap", header)
        self.assertIn("裸 `bda_main()` 中用 `parent=0` 直接创建 edit/listbox", system_notes)
        self.assertIn("不是通用 GUI bootstrap", system_notes)
        self.assertIn("不是 GUI bootstrap", api_offsets)
        self.assertIn("失败点更可能是缺少真实\nparent/frame lifecycle", text_notes)
        self.assertIn("不要把这些 probe 当成 SDK 推荐示例", text_notes)
        self.assertIn("不要在 bare `main()` 里随便用空 parent 创建 edit/listbox control", window_notes)
        self.assertNotIn("当前面向 custom app 的公开路线仍是通过 `GUI+0x1a4` 创建", system_notes)
        self.assertNotIn("参数布局仍不完整", text_notes)
        self.assertNotIn("bda_gui_create_ex", header)

    def test_fs_open_uses_string_mode_only(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        self.assertNotIn("bda_fs_open_raw", header)
        self.assertNotIn("bda_fs_open_raw", readme)
        self.assertIn("bda_fs_fopen_raw", header)
        self.assertIn('bda_fs_fopen_raw(const char *path, const char *mode)', readme)
        self.assertIn("原机代码常传 rb/wb 等 mode string", read("reverse/docs/api_catalog.md"))

    def test_fs_read_write_fread_order_and_zero_failure_are_documented(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        raw_demo = read("reverse/examples/fs_read_raw_demo.c")
        write_demo = read("example/filesystem/fs_write/fs_write_demo.c")
        fs_notes = read("reverse/docs/fs_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = header + "\n" + readme + "\n" + fs_notes + "\n" + c200_notes + "\n" + catalog_tool
        self.assertIn("bda_fs_fread_raw(void *buffer, bda_size_t size, bda_size_t count, int file)", header)
        self.assertIn("bda_fs_fwrite_raw(const void *buffer, bda_size_t size, bda_size_t count, int file)", header)
        self.assertIn("static inline int bda_fs_file_is_valid(int file)", header)
        self.assertIn("file != 0 && (u32)file != 0xffffffffu", header)
        self.assertIn("int bda_fs_file_is_valid(int file);", readme)
        self.assertIn("bda_fs_read_raw(file, buffer, size)", readme)
        self.assertIn("参数顺序不是", readme)
        self.assertIn("got = bda_fs_read_raw(file, buffer, sizeof(buffer) - 1);", raw_demo)
        self.assertNotIn("bda_fs_fread_raw(buffer", raw_demo)
        self.assertIn("破坏性 raw write", header)
        self.assertIn("只对明确以写模式打开的有效 fd 调用", header)
        self.assertIn("不要在只读 probe 中调用", header)
        self.assertIn("便捷 write wrapper", header)
        self.assertIn("FS +0x008 / +0x00c", c200_notes)
        self.assertIn("FS+0x008 -> 0x8017a978", c200_notes)
        self.assertIn("FS+0x00c -> 0x8017ab2c", c200_notes)
        self.assertIn("a0=buffer", combined)
        self.assertIn("a1=size", combined)
        self.assertIn("a2=count", combined)
        self.assertIn("a3=file", combined)
        self.assertIn("file+0x48", c200_notes)
        self.assertIn("失败路径都返回 `0`", c200_notes)
        self.assertIn("不是 -1", header + "\n" + fs_notes)
        self.assertIn("0x80170d94(buffer,size,count,file)", c200_notes)
        self.assertIn("0x80171154(buffer,size,count,file)", c200_notes)
        self.assertIn("bda_fs_file_is_valid(result->open_write)", write_demo)
        self.assertIn("write=19,tell=19,error=0,read=19,match=1", fs_notes + "\n" + c200_notes)
        self.assertIn("44f98eda68a182a6222469f93bc9f008747fd942d966549328dfe25792180f76", fs_notes)
        self.assertNotIn("result->open_write <= 0", write_demo)
        self.assertNotIn("bda_fs_fread_raw(int file, void *buffer", header)
        self.assertNotIn("bda_fs_fwrite_raw(int file, const void *buffer", header)

    def test_fs_seek_and_close_c200_abi_are_documented(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        fs_notes = read("reverse/docs/fs_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = header + "\n" + fs_notes + "\n" + c200_notes + "\n" + catalog_tool
        self.assertIn("static inline int bda_fs_close_raw(int fd)", header)
        self.assertIn("static inline int bda_fs_seek_raw(int file, s32 offset, int whence)", header)
        self.assertIn("FS +0x004: `BDA_FS_CLOSE`", c200_notes)
        self.assertIn("system function VA：`0x8017a928`", c200_notes)
        self.assertIn("0x80170c74(file)", c200_notes)
        self.assertIn("FS +0x010: `BDA_FS_SEEK`", c200_notes)
        self.assertIn("system function VA：`0x801712a0`", c200_notes)
        self.assertIn("a0=file", combined)
        self.assertIn("a1=offset", combined)
        self.assertIn("a2=whence", combined)
        self.assertIn("BDA_SEEK_SET(0)", fs_notes)
        self.assertIn("BDA_SEEK_CUR(1)", fs_notes)
        self.assertIn("BDA_SEEK_END(2)", fs_notes)
        self.assertIn("其他 `whence` 值会直接返回 `-1`", c200_notes)
        self.assertIn("成功路径返回更新后的 `file+0x44`", c200_notes)
        self.assertIn("file+0x20 + offset", c200_notes)
        self.assertNotIn("bda_fs_seek_raw(s32 offset, int whence, int file)", header)

    def test_fs_tell_index_and_zero_error_paths_are_documented(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        fs_notes = read("reverse/docs/fs_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        self.assertIn("bda_fs_tell_raw(int file)", header)
        self.assertIn("+0x48", header)
        self.assertIn("返回 0", header)
        self.assertIn("file+0x48", fs_notes)
        self.assertIn("内部错误码 `9`", fs_notes)
        self.assertIn("设置 `0x10`", fs_notes)
        self.assertIn("返回 `0` 既可能是文件开头", c200_notes)
        self.assertIn("0x804bf434", c200_notes)
        self.assertIn("0x804bf438", c200_notes)
        self.assertIn("file+0x44", catalog_tool)

    def test_fs_status_example_is_read_only_and_documented(self) -> None:
        source = read("reverse/examples/fs_status_demo.c")
        fs_notes = read("reverse/docs/fs_notes.md")
        sdk_readme = read("docs/sdk_api_layout.md")
        docs_readme = read("reverse/docs/README.md")
        combined_docs = fs_notes + "\n" + sdk_readme + "\n" + docs_readme

        self.assertIn("bda_fs_media_present_raw_like()", source)
        self.assertIn("bda_fs_storage_ready_like()", source)
        self.assertIn("bda_fs_getcwd_like(g_cwd, sizeof(g_cwd))", source)
        self.assertIn("bda_fs_path_info_like(CFG_PATH, &g_info)", source)
        self.assertIn("bda_fs_path_info_size_like(&g_info)", source)
        self.assertIn("bda_fs_stat_like(CFG_PATH, 0)", source)
        self.assertIn("bda_fs_stat_like(CFG_PATH_ALT, 0)", source)
        self.assertNotIn("bda_fs_remove_raw", source)
        self.assertNotIn("bda_fs_mkdir_like", source)
        self.assertNotIn("bda_fs_fwrite_raw", source)
        self.assertIn("fs_status_demo.c", combined_docs)
        self.assertIn("只读调用", fs_notes)
        self.assertIn("raw media bit", fs_notes)
        self.assertIn("不会创建、删除或写入文件", fs_notes)
        self.assertIn("返回 `-1`", fs_notes)
        self.assertIn("不应直接当作致命错误", fs_notes)

    def test_fs_getcwd_required_size_abi_is_documented(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        fs_notes = read("reverse/docs/fs_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        api_offsets = read("reverse/docs/api_offsets.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = "\n".join([header, readme, fs_notes, c200_notes, api_offsets, catalog_tool])
        self.assertIn("#define BDA_FS_GETCWD_LIKE", header)
        self.assertIn("static inline int bda_fs_getcwd_like(char *buffer, bda_size_t size)", header)
        self.assertIn("int bda_fs_getcwd_like(char *buffer, bda_size_t size);", readme)
        self.assertIn("FS +0x050: `BDA_FS_GETCWD_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x801700d0`", c200_notes)
        self.assertIn("a0=buffer", c200_notes)
        self.assertIn("a1=size", c200_notes)
        self.assertIn("required size", combined)
        self.assertIn("buffer == NULL", combined)
        self.assertIn("A:", combined)
        self.assertIn("只读 getter", c200_notes)
        self.assertIn("不会切换目录", combined)
        self.assertNotIn("FS+0x050  0x801700d0  current path getter-like；当前未见原机直接调用点", fs_notes)

    def test_fs_path_info_abi_is_documented_from_c200(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        fs_notes = read("reverse/docs/fs_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        api_offsets = read("reverse/docs/api_offsets.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = "\n".join([header, readme, fs_notes, c200_notes, api_offsets, catalog_tool])

        self.assertIn("#define BDA_FS_PATH_INFO_LIKE", header)
        self.assertIn("typedef struct bda_fs_path_info_like", header)
        self.assertIn("bda_fs_path_info_like_t", header)
        self.assertIn("static inline void bda_fs_path_info_init_like(bda_fs_path_info_like_t *info)", header)
        self.assertIn(
            "static inline int bda_fs_path_info_like(const char *path, bda_fs_path_info_like_t *info)",
            header,
        )
        self.assertIn("static inline int bda_fs_path_info_is_dir_like", header)
        self.assertIn("static inline u32 bda_fs_path_info_size_like", header)
        self.assertIn("int bda_fs_path_info_like(const char *path, bda_fs_path_info_like_t *info);", readme)
        self.assertIn("FS +0x054: `BDA_FS_PATH_INFO_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x8017a0d8`", c200_notes)
        self.assertIn("0x80179cb8(temp_path, info)", c200_notes)
        self.assertIn("0x18 byte", combined)
        self.assertIn("attr_like", combined)
        self.assertIn("size_like", combined)
        self.assertIn("time_like", combined)
        self.assertIn("0x4000", combined)
        self.assertIn("path info getter", combined)
        self.assertNotIn("FS+0x054  0x8017a0d8  path stat 内部 helper；当前未见原机直接调用点", fs_notes)

    def test_fs_remove_single_path_abi_is_documented_from_c200(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        fs_notes = read("reverse/docs/fs_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = header + "\n" + readme + "\n" + fs_notes + "\n" + c200_notes + "\n" + catalog_tool
        self.assertIn("static inline int bda_fs_remove_raw(const char *path)", header)
        self.assertIn("int bda_fs_remove_raw(const char *path);", readme)
        self.assertIn("FS +0x024: `BDA_FS_REMOVE`", c200_notes)
        self.assertIn("system function VA：`0x801717f4`", c200_notes)
        self.assertIn("只使用一个调用者参数", c200_notes)
        self.assertIn("0x20a byte 临时 path buffer", combined)
        self.assertIn("路径解析 helper `0x8016f904`", combined)
        self.assertIn("内部删除 helper `0x801714ec", c200_notes)
        self.assertIn("失败返回 -1", header)
        self.assertIn("破坏性删除", header)
        self.assertIn("不要传 directory path、空 pointer 或未终止字符串", header)
        self.assertIn("重新 `bda_fs_fopen_raw(path, \"wb\")`", combined)
        self.assertNotIn("bda_fs_remove_raw(void)", header + readme)
        self.assertNotIn("bda_fs_remove_raw(const char *path, u32", header + readme)

    def test_fs_storage_ready_is_no_arg_low_byte_query(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        fs_notes = read("reverse/docs/fs_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        self.assertIn("static inline int bda_fs_media_present_raw_like(void)", header)
        self.assertIn("int bda_fs_media_present_raw_like(void);", readme)
        self.assertIn("static inline int bda_fs_storage_ready_like(void)", header)
        self.assertIn("int bda_fs_storage_ready_like(void);", readme)
        self.assertIn("不读取 a0..a3", header + "\n" + c200_notes)
        self.assertIn("低 8 位", header + "\n" + fs_notes + "\n" + c200_notes + "\n" + catalog_tool)
        self.assertIn("0x8017952c", fs_notes + "\n" + c200_notes)
        self.assertIn("0xb0010300", header + "\n" + fs_notes + "\n" + c200_notes + "\n" + catalog_tool)
        self.assertIn("0x01000000", header + "\n" + fs_notes + "\n" + c200_notes)
        self.assertIn("raw media-present", fs_notes + "\n" + c200_notes + "\n" + catalog_tool)
        self.assertIn("0x801705ec", fs_notes + "\n" + c200_notes)
        self.assertIn("0x8000f8a0", fs_notes + "\n" + c200_notes)
        self.assertIn("FS +0x074", c200_notes)
        self.assertIn("bda_fs_flush_all", c200_notes)
        self.assertIn("不等于具体 directory enumeration 一定成功", c200_notes)
        self.assertNotIn("bda_fs_media_present_raw_like(const char", header + readme)
        self.assertNotIn("bda_fs_media_present_raw_like(u32", header + readme)
        self.assertNotIn("bda_fs_storage_ready_like(const char", header + readme)
        self.assertNotIn("bda_fs_storage_ready_like(u32", header + readme)

    def test_fs_flush_all_is_public_after_forced_power_cut_ab(self) -> None:
        public_header = read("sdk/include/bda_filesystem.h")
        runtime = read("sdk/include/bda/detail/runtime.h")
        verified = read("docs/verified/fs_flush_api.md")
        evidence = read(
            "docs/verified/assets/fs_flush_power_probe_result.txt"
        )
        example = read(
            "example/filesystem/fs_flush/fs_flush_power_demo.c"
        )
        c200_notes = read("reverse/docs/c200_api_function_notes.md")

        self.assertIn("BDA_SDK_INTERNAL_FS_FLUSH_ALL  0x074u", runtime)
        self.assertIn("static inline void bda_fs_flush_all(void)", public_header)
        self.assertIn("global operation", public_header)
        self.assertIn("does not close handles", public_header)
        self.assertIn("bda_fs_flush_all();", example)
        self.assertNotIn("bda_sdk_internal_api", example)
        self.assertIn("F74YES.DAT", example + "\n" + verified)
        self.assertIn("F74NO.DAT", example + "\n" + verified)
        self.assertIn("flushed read=4096, byte_match=1", evidence)
        self.assertIn("control read=0, byte_match=0", evidence)
        self.assertIn(
            "4bdb590eaadb6efc9fc001b29f09b2af9edf289898cd204289fcf5557d97cb87",
            verified + "\n" + evidence,
        )
        self.assertIn("void bda_fs_flush_all(void)", c200_notes)
        self.assertIn("真机物理断电仍未验证", verified + "\n" + c200_notes)

    def test_file_management_api_is_public_after_crud_probe(self) -> None:
        public_header = read("sdk/include/bda_filesystem.h")
        runtime = read("sdk/include/bda/detail/runtime.h")
        types = read("sdk/include/bda_types.h")
        verified = read("docs/verified/file_management_api.md")
        evidence = read(
            "docs/verified/assets/file_management_probe_log.txt"
        )
        example = read(
            "example/filesystem/file_management/file_management_demo.c"
        )

        for offset in [
            "BDA_SDK_INTERNAL_FS_REMOVE     0x024u",
            "BDA_SDK_INTERNAL_FS_RENAME     0x028u",
            "BDA_SDK_INTERNAL_FS_RMDIR      0x034u",
            "BDA_SDK_INTERNAL_FS_DISK_INFO  0x048u",
            "BDA_SDK_INTERNAL_FS_GETCWD     0x050u",
            "BDA_SDK_INTERNAL_FS_PATH_INFO  0x054u",
            "BDA_SDK_INTERNAL_FS_STORAGE_READY 0x07cu",
        ]:
            self.assertIn(offset, runtime)

        for name in [
            "BDA_FS_DRIVE_A",
            "BDA_FS_ATTR_DIRECTORY",
            "BDA_FS_DISK_INFO_SIZE",
            "BDA_FS_PATH_INFO_SIZE",
            "bda_fs_disk_info_t",
            "bda_fs_path_info_t",
            "bda_fs_remove",
            "bda_fs_rename",
            "bda_fs_rmdir",
            "bda_fs_disk_info",
            "bda_fs_disk_total_bytes",
            "bda_fs_disk_free_bytes",
            "bda_fs_getcwd",
            "bda_fs_path_info_init",
            "bda_fs_path_info",
            "bda_fs_path_info_is_dir",
            "bda_fs_storage_ready",
        ]:
            self.assertIn(name, public_header)
            self.assertIn(name, verified)

        self.assertIn("typedef unsigned long long u64;", types)
        self.assertNotIn("_like", public_header.lower())
        self.assertNotIn("bda_research_sdk.h", example)
        self.assertNotIn("_like", example)
        self.assertIn("rmdir_nonempty=-1", evidence)
        self.assertIn("old_after_rename=-1", evidence)
        self.assertIn("new_after_remove=-1", evidence)
        self.assertIn("dir_after_rmdir=-1", evidence)
        self.assertIn("RESULT=PASS", evidence)
        self.assertIn(
            "20633563cc75126965fd75daba1e1e9a0543d78eaaf3adcbdcaa72bff673e80c",
            verified,
        )
        self.assertTrue(
            (ROOT / "example/filesystem/file_management/FileManagement.bda").is_file()
        )

    def test_fs_chdir_mkdir_and_rmdir_are_documented_from_c200(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        fs_notes = read("reverse/docs/fs_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        api_offsets = read("reverse/docs/api_offsets.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = "\n".join([header, readme, fs_notes, c200_notes, api_offsets, catalog_tool])
        self.assertIn("static inline int bda_fs_chdir_like(const char *path)", header)
        self.assertIn("static inline int bda_fs_mkdir_like(const char *path)", header)
        self.assertIn("static inline int bda_fs_rmdir_like(const char *path)", header)
        self.assertIn("int bda_fs_chdir_like(const char *path);", readme)
        self.assertIn("int bda_fs_mkdir_like(const char *path);", readme)
        self.assertIn("int bda_fs_rmdir_like(const char *path);", readme)
        self.assertIn("FS +0x02c: `BDA_FS_CHDIR_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x8016fe18`", c200_notes)
        self.assertIn("FS +0x030: `BDA_FS_MKDIR_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x80171f8c`", c200_notes)
        self.assertIn("FS +0x034: `BDA_FS_RMDIR_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x80172520`", c200_notes)
        self.assertIn("目录属性位 `0x4000`", combined)
        self.assertIn("空字符串返回 `0`", combined)
        self.assertIn("不只是无副作用的存在性检查", c200_notes)
        self.assertIn("创建目录 helper `0x80171ec0", c200_notes)
        self.assertIn("directory removal helper `0x801720c8", combined)
        self.assertIn("删除空目录", combined)
        self.assertIn("破坏性目录删除 API", c200_notes)
        self.assertIn("英语百科.bda", c200_notes)
        self.assertIn("飞天影音.bda", c200_notes)
        self.assertIn("飞天音乐.bda", c200_notes)
        self.assertIn("改变当前目录状态", combined)
        self.assertIn("会修改 filesystem", header)
        self.assertNotIn("bda_fs_chdir_like(void)", header + readme)
        self.assertNotIn("bda_fs_mkdir_like(void)", header + readme)
        self.assertNotIn("bda_fs_rmdir_like(void)", header + readme)
        self.assertNotIn("FS+0x034  0x80172520  path 解析 + 内部 helper；当前未见原机直接调用点", fs_notes)

    def test_sdk_readme_documents_removed_dlx_aliases(self) -> None:
        readme = read("reverse/docs/README.md")
        self.assertIn("已删除的历史 misnames", readme)
        self.assertIn("bda_gui_create_ex / BDA_MSG_TOUCH_B_LIKE", readme)
        self.assertIn("使用 `bda_gui_create_window_like()` 创建 control", readme)
        self.assertIn("使用 `BDA_MSG_REDRAW_INPUT_LIKE`", readme)
        self.assertIn("bda_gui_surface_flush_like", readme)
        self.assertIn("bda_gui_set_fill_color_like", readme)
        self.assertIn("element_bda_notes.md", readme)
        self.assertIn("showcase_notes.md", readme)
        self.assertIn("reverse/examples/window_text_bbvm_black_probe.c", readme)
        self.assertIn("BBVM 风格 text draw lifecycle probe", readme)
        self.assertIn("frame/control lifecycle 回归 probe", readme)
        self.assertIn("不是 standalone SDK starter", readme)

    def test_sdk_readme_has_build_validate_deploy_verify_quickstart(self) -> None:
        readme = read("reverse/docs/README.md")
        required = [
            "## 快速闭环",
            ".\\scripts\\setup_toolchain.ps1",
            "python -m bda_packer example\\basic\\hello_world\\hello_world_msgbox.c",
            "--title HelloWorld",
            "--category 9",
            "--icon-png",
            "python -m bda_packer.validate build\\HelloWorld.bda",
            ".\\scripts\\verify_sdk.ps1 -SkipToolchainSetup",
            ".\\scripts\\verify_sdk.ps1 -SkipToolchainSetup -Emu",
            "emu 前端 smoke",
            "frontend 文件 API 写入其持久 worker copy",
            "不要把 `Config.inf` 当成 BDA app 的有效注册机制",
            "Public Wrapper 快览",
            "普通应用可以使用聚合 `sdk/include/bda_sdk.h`",
            "`bda_filesystem.h`、`bda_input.h`、`bda_time.h`",
            "`bda_window.h`、`bda_graphics.h`",
            "`bda_dialogs.h`、`bda_controls.h` 和 `bda_audio.h`",
            "从原机应用调用点和 C200 切片整理出的 wrapper",
            "用于 low-level probe 或复刻原机调用形状的 table call",
            "不要把未知 offset 当成稳定 API",
            "打包器只支持 standalone C",
            "不接受既有 BDA",
        ]
        for phrase in required:
            self.assertIn(phrase, readme)
        for phrase in [
            "python reverse\\bda_deploy_bundle.py `\n  --bda build\\HelloBDA.bda",
            "--config 系统\\数据\\Config.inf",
            "`bda_deploy_bundle.py --json`",
            "build\\deploy_RectDemo_verify",
            "build\\deploy_Mine_as_Time",
            "--template",
            "TimePassthrough",
        ]:
            self.assertNotIn(phrase, readme)

    def test_native_toolchain_notes_do_not_promote_config_inf_as_registration(self) -> None:
        notes = read("reverse/native_toolchain_notes.md")
        for phrase in [
            "# BBK 9588 Standalone BDA Toolchain",
            "BDA loader 从 header 指定的 file offset",
            "固定 VA `0x81c00020`",
            "builder 将 `.bss` 作为零字节写进 flat image",
            "唯一构建入口",
            "没有基于原机 BDA 的构建",
            "frontend persistent worker copy",
            "`/api/files/import`",
            "不要手工\n制作 NAND",
        ]:
            self.assertIn(phrase, notes)
        self.assertIn("入口覆盖或 passthrough 功能", notes)
        for obsolete in ["Config.inf", "TimePassthrough", "bda_build.py"]:
            self.assertNotIn(obsolete, notes)

    def test_public_header_comments_explain_risky_common_wrappers(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        required_notes = [
            "表内 offset 单位是 byte",
            "MIPS a0..a3",
            "第五/第六参数放在 caller stack",
            "low-level table call helper",
            "controlled probe",
            "开发者 API 使用 title,message 顺序",
            "parent,message,title,flags",
            "standalone app 可把它作为首个",
            "docs/verified/msgbox_api.md",
            "class_name 常见值包括",
            "height 在 width 前",
            "flush 会释放 context",
            "不要在 bare bda_main() 中用 handle=0 做 probe",
            "不是 DLX loader",
            "其他值返回 -1 并设置内部 error 9",
            "find_data 必须至少是 bda_fs_find_data_like_t 大小",
            "raw audio finish/stop。真机可安全停止并返回",
            "常用开发词保留英文",
            "album-backed picture decode descriptor",
            "C200-backed directory enumeration",
            "provisional message ID",
        ]
        combined = header + "\n" + read("reverse/docs/README.md")
        for note in required_notes:
            self.assertIn(note, combined)
        for old_phrase in [
            "消息框 wrapper",
            "C200 表入口",
            "表项无参数",
            "函数级反汇编",
            "返回类型",
            "返回值来自",
            "RGB565 像素数据",
            "文件选择器 descriptor",
            "目录枚举入口",
        ]:
            self.assertNotIn(old_phrase, header)
        self.assertNotIn("实验封装", combined)
        self.assertNotIn("实验性高层文件选择器", combined)
        self.assertNotIn("实验性 picture decode descriptor", header)
        self.assertNotIn("实验性 directory enumeration", header)

    def test_api_offset_naming_rules_do_not_overclaim_no_like_wrappers(self) -> None:
        api_offsets = read("reverse/docs/api_offsets.md")
        self.assertIn("没有 `_LIKE` 的少数 wrapper 表示当前风险较低", api_offsets)
        self.assertIn("不表示", api_offsets)
        self.assertIn("任意入口上下文", api_offsets)
        self.assertIn("任意 GUI lifecycle 都安全", api_offsets)
        self.assertIn("`bda_msgbox()`", api_offsets)
        self.assertIn("硬编码时间入口替换上下文仍可能崩溃", api_offsets)
        self.assertIn("不是自动稳定的 high-level API", api_offsets)

    def test_low_level_call_helpers_document_mips_o32_stack_args(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        api_offsets = read("reverse/docs/api_offsets.md")
        combined = "\n".join([header, readme, api_offsets])

        self.assertIn("MIPS a0..a3", header)
        self.assertIn("第五/第六参数放在 caller stack", header)
        self.assertIn("MIPS o32 只有 `a0..a3` 四个参数寄存器", readme + "\n" + api_offsets)
        self.assertIn("`bda_call5()` / `bda_call6()`", readme + "\n" + api_offsets)
        self.assertIn("读取 `stack+0x10`", readme + "\n" + api_offsets)
        self.assertNotIn("a0..a5", combined)

    def test_gui_object_bind_is_documented_as_context_slot_setter(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        paint_notes = read("reverse/docs/paint_notes.md")
        picture_notes = read("reverse/docs/picture_notes.md")
        game_notes = read("reverse/docs/game_framework_notes.md")
        paint_report = read("reverse/reports/paint_bda_report.md")
        album_report = read("reverse/reports/album_bda_report.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = "\n".join([header, readme, c200_notes, paint_notes, picture_notes, game_notes, paint_report, album_report, catalog_tool])
        self.assertIn("static inline int bda_gui_object_bind_like(u32 context, u32 value)", header)
        self.assertIn("int bda_gui_object_bind_like(u32 context, u32 value);", readme)
        self.assertIn("GUI +0x35c: `BDA_GUI_OBJECT_BIND_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x800b2d58`", c200_notes)
        self.assertIn("a0=context", c200_notes)
        self.assertIn("a1=value", c200_notes)
        self.assertIn("context+0x20", combined)
        self.assertIn("返回旧 `context+0x20`", paint_report)
        self.assertIn("GUI+0x35c(context, resource_or_image_slot_value)", paint_report)
        self.assertIn("返回旧值", catalog_tool)
        self.assertIn("不负责创建或释放 object", header)
        self.assertIn("不是 object 生命周期绑定", combined)
        self.assertIn("GUI +0x35c   11 次  draw context resource/image slot setter", album_report)
        self.assertIn("GUI +0x35c  -> 写 draw context +0x20 的 resource/image slot", album_report)
        self.assertNotIn("GUI +0x35c   11 次  对象/资源绑定辅助候选", album_report)
        self.assertNotIn("GUI+0x35c  -> 绑定对象/资源候选", album_report)
        self.assertNotIn("`GUI+0x35c`、`GUI+0x40c`、`GUI+0x418` 的准确签名仍需", paint_report)
        self.assertNotIn("bda_gui_object_bind_like(u32 object, u32 resource)", header + readme)

    def test_gui_default_proc_is_documented_as_wndproc_fallback(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        window_notes = read("reverse/docs/window_notes.md")
        input_notes = read("reverse/docs/input_notes.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = "\n".join([header, c200_notes, window_notes, input_notes, catalog_tool])
        self.assertIn("bda_gui_default_proc_like(bda_handle_t handle, u32 message, u32 wparam, u32 lparam)", header)
        self.assertIn("签名与 bda_wndproc_t 一致", combined)
        self.assertIn("a0=handle", c200_notes)
        self.assertIn("a1=message", c200_notes)
        self.assertIn("a2=wparam", c200_notes)
        self.assertIn("a3=lparam", c200_notes)
        self.assertIn("0x800d0688(wparam, lparam)", c200_notes)
        self.assertIn("0x800cfb08(handle, wparam)", c200_notes)
        self.assertIn("0x800d02b4(handle, wparam, flag)", c200_notes)
        self.assertIn("0xb0..0xb3", window_notes)
        self.assertIn("callback fallback", window_notes)
        self.assertIn("主动 send API", input_notes)
        self.assertIn("handle,message,wparam,lparam", catalog_tool)
        self.assertNotIn("bda_gui_default_proc_like(u32 message", header)

    def test_frame_descriptor_uses_named_fields_for_sample_layout(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        window_notes = read("reverse/docs/window_notes.md")
        api_offsets = read("reverse/docs/api_offsets.md")
        stage_probe = read("reverse/examples/showcase_stage_probe.c")
        combined = "\n".join([header, c200_notes, window_notes, api_offsets])
        self.assertIn("typedef struct bda_frame_desc_like", header)
        self.assertIn("u32 internal28;", header)
        self.assertIn("u32 internal44;", header)
        self.assertIn("u32 internal48;", header)
        self.assertIn("u32 helper_arg14;", header)
        self.assertIn("s32 x;", header)
        self.assertIn("s32 y;", header)
        self.assertIn("s32 height;", header)
        self.assertIn("s32 width;", header)
        self.assertIn("u32 surface;", header)
        self.assertIn("u32 aux30;", header)
        self.assertIn("descriptor->height = height;", header)
        self.assertIn("descriptor->width = width;", header)
        self.assertIn("descriptor->surface = (u32)surface;", header)
        self.assertIn("descriptor->style = 0;", header)
        self.assertIn("不是单步显示 API", header)
        self.assertIn("不是硬编码时间入口下的", header)
        self.assertIn("通用 GUI bootstrap", header)
        self.assertIn("必须按真实 frame lifecycle", header)
        self.assertIn("不能把 register_frame 当作无需 event loop 的安全绘图入口", header)
        self.assertIn("style=0,surface=0", window_notes + "\n" + api_offsets)
        self.assertIn("no-template BDA 开发先用 `surface=0`", c200_notes)
        self.assertIn("不是通用最小组合", window_notes + "\n" + api_offsets)
        self.assertIn("height=240,width=320", c200_notes)
        self.assertIn("internal28/internal44/internal48/helper_arg14/aux30", window_notes)
        self.assertIn("desc.height = SCREEN_H", stage_probe)
        self.assertIn("desc.width = SCREEN_W", stage_probe)
        self.assertIn("desc.surface = (u32)bda_gui_draw_object_create_like(15)", stage_probe)
        self.assertNotIn("rect_or_state1c", header + stage_probe + window_notes)
        self.assertNotIn("arg2c", header + stage_probe + combined)
        self.assertNotIn("arg04", header + window_notes + api_offsets)

    def test_element_event_loop_is_sample_specific_not_sdk_default(self) -> None:
        element_notes = read("reverse/docs/element_bda_notes.md")
        window_notes = read("reverse/docs/window_notes.md")
        header = SDK_HEADER.read_text(encoding="utf-8")
        self.assertIn("Element 原机 event loop 形态", element_notes)
        self.assertIn("Element 原机 event loop 使用 GUI+0x030(msg, 0)", element_notes)
        self.assertIn("这不是 no-template SDK 的通用规则", element_notes)
        self.assertIn("新 no-template BDA 应优先使用 `bda_gui_event_poll_like(&msg, frame)`", element_notes)
        self.assertIn("surface=GUI+0x2fc(15)` 和 `GUI+0x030(msg, 0)` 是 Element\n原机应用在已有系统上下文中的模式", element_notes)
        self.assertIn("bda_frame_desc_init_like(..., surface=0)", element_notes)
        self.assertIn("bda_gui_event_poll_like(&msg, frame)", element_notes)
        self.assertIn("全局/default frame slot poll", header)
        self.assertIn("新 BDA 不应把它当成无需 frame handle 的通用 message pump", header)
        self.assertIn("注册后的典型 event loop", window_notes)
        self.assertNotIn("event loop 必须使用 GUI+0x030(msg, 0)", element_notes)
        self.assertNotIn("frame = create_frame(proc, surface=GUI+0x2fc(15));\nwhile (GUI+0x030(msg, 0))", element_notes)

    def test_frame_lifecycle_helpers_are_documented_with_distinct_roles(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        window_notes = read("reverse/docs/window_notes.md")
        api_offsets = read("reverse/docs/api_offsets.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = "\n".join([header, c200_notes, window_notes, api_offsets, catalog_tool])
        self.assertIn("bda_gui_frame_stop_like(bda_handle_t handle)", header)
        self.assertIn("bda_gui_frame_activate_like(bda_handle_t handle, u32 mode)", header)
        self.assertIn("bda_gui_close_frame_like(bda_handle_t handle)", header)
        self.assertIn("bda_gui_frame_release_like(bda_handle_t handle)", header)
        self.assertIn("int bda_gui_active_frame_set_like(bda_handle_t handle)", header)
        self.assertIn("#define BDA_GUI_ACTIVE_FRAME_GET_LIKE  0x13cu", header)
        self.assertIn("bda_handle_t bda_gui_active_child_get_like(bda_handle_t context)", header)
        self.assertIn("int bda_gui_active_frame_set_like(bda_handle_t handle);", read("reverse/docs/README.md"))
        self.assertIn("bda_handle_t bda_gui_active_child_get_like(bda_handle_t context);", read("reverse/docs/README.md"))
        self.assertNotIn("bda_handle_t bda_gui_active_frame_set_like", header + read("reverse/docs/README.md"))
        self.assertIn("GUI +0x04c: `BDA_GUI_FRAME_RELEASE_LIKE`", c200_notes)
        self.assertIn("GUI +0x088 / +0x098 / +0x17c", c200_notes)
        self.assertIn("system function VA：`0x800dd31c`", c200_notes)
        self.assertIn("GUI+0x088 -> 0x800ce090", c200_notes)
        self.assertIn("GUI+0x098 -> 0x800cc4ec", c200_notes)
        self.assertIn("GUI+0x17c -> 0x800cdffc", c200_notes)
        self.assertIn("0x80825840", c200_notes)
        self.assertIn("0x80000000", c200_notes)
        self.assertIn("不是释放内存的 close 操作", c200_notes)
        self.assertIn("0x800dd180(handle)", c200_notes)
        self.assertIn("内部 `0x66` message", c200_notes)
        self.assertIn("成功路径返回 `1`", c200_notes)
        self.assertIn("mode == 0", c200_notes)
        self.assertIn("`0x10`", c200_notes)
        self.assertIn("`0x100`", c200_notes)
        self.assertIn("GUI +0x134: `BDA_GUI_ACTIVE_FRAME_SET_LIKE`", c200_notes)
        self.assertIn("manager+0xd8", c200_notes)
        self.assertIn("内部 `0x31` message", c200_notes)
        self.assertIn("内部 `0x30` message", c200_notes)
        self.assertIn("内部 message return value 或 `0`", c200_notes)
        self.assertIn("int bda_gui_active_frame_set_like(handle)", c200_notes)
        self.assertIn("GUI +0x13c: `BDA_GUI_ACTIVE_FRAME_GET_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x800cae04`", c200_notes)
        self.assertIn("读取 `a0=context`", c200_notes)
        self.assertIn("读取并返回 `container+0xd8`", c200_notes)
        self.assertIn("`名片.bda` 中该 offset 在 GUI table 下出现 67 次", c200_notes)
        self.assertIn("bda_gui_active_child_get_like(context)", c200_notes)
        self.assertIn("不创建 frame、不激活 frame", c200_notes)
        self.assertIn("0x804a6540", c200_notes)
        self.assertIn("active frame 全局槽", combined)
        self.assertIn("frame release/request-like", api_offsets)
        self.assertIn("active frame set-like", window_notes)
        self.assertIn("active child get-like", window_notes)
        self.assertIn("active child get-like", api_offsets)
        self.assertIn("返回 container+0xd8", catalog_tool)
        self.assertIn("不是 show flag", combined)
        self.assertIn("不要把它和普通", c200_notes)
        self.assertIn("不要把 return value 当作新 active handle", window_notes)
        self.assertIn("bare `bda_main()` 变成可绘制 GUI 上下文", window_notes)
        self.assertNotIn("bda_gui_frame_activate_like(bda_handle_t handle, int show)", header)

    def test_gui_event_loop_helpers_match_c200_message_buffer_abi(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        window_notes = read("reverse/docs/window_notes.md")
        api_offsets = read("reverse/docs/api_offsets.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = "\n".join([header, c200_notes, window_notes, api_offsets, catalog_tool])
        self.assertIn("#define BDA_GUI_MESSAGE_SIZE 0x1cu", header)
        self.assertIn("typedef struct bda_gui_message_like", header)
        self.assertIn("bda_handle_t handle;", header)
        self.assertIn("u32 message;", header)
        self.assertIn("u32 wparam;", header)
        self.assertIn("u32 lparam;", header)
        self.assertIn("bda_gui_event_poll_like(bda_gui_message_like_t *message, bda_handle_t handle)", header)
        self.assertIn("bda_gui_event_step_like(bda_gui_message_like_t *message)", header)
        self.assertIn("bda_gui_event_dispatch_like(bda_gui_message_like_t *message)", header)
        self.assertIn("int bda_gui_event_poll_global_like(bda_gui_message_like_t *message);", read("reverse/docs/README.md"))
        self.assertIn("bda_gui_event_pump_frame_once_like", header)
        self.assertIn("bda_gui_event_poll_like(message, frame)", header)
        self.assertIn("GUI +0x030 / +0x050 / +0x054", c200_notes)
        self.assertIn("GUI+0x030 -> 0x800dbfd0", c200_notes)
        self.assertIn("GUI+0x050 -> 0x800de378", c200_notes)
        self.assertIn("GUI+0x054 -> 0x800dd4b8", c200_notes)
        self.assertIn("清零 `0x1c` byte", c200_notes)
        self.assertIn("message_buffer+0x04", c200_notes)
        self.assertIn("`0x10` 或 `0x13`", c200_notes)
        self.assertIn("内部 `0x11` 或 `0x14`", c200_notes)
        self.assertIn("handle+0x88", c200_notes)
        self.assertIn("handle, message, wparam, lparam", c200_notes)
        self.assertIn("bda_gui_message_like_t", c200_notes + window_notes)
        self.assertIn("BDA_GUI_MESSAGE_SIZE", c200_notes + window_notes)
        self.assertIn("bda_gui_message_like_t msg;", window_notes)
        self.assertIn("不是无参数 pump", combined)
        self.assertIn("poll(&msg, frame) -> step(&msg) -> dispatch(&msg)", c200_notes)
        self.assertIn("message_buffer,frame_or_handle", catalog_tool)
        self.assertNotIn("bda_gui_event_poll_like(void *message", header + read("reverse/docs/README.md"))
        self.assertNotIn("新代码建议使用 7 个 word 的局部数组", c200_notes)
        self.assertNotIn("bda_gui_event_step_like(void)", header)
        self.assertNotIn("bda_gui_event_step_like();", read("reverse/docs/window_notes.md"))
        for source in (ROOT / "reverse" / "examples").glob("*.c"):
            text = source.read_text(encoding="utf-8")
            self.assertNotIn("bda_gui_event_step_like();", text, source)

    def test_gui_send_and_notify_are_documented_as_sync_vs_queued(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        window_notes = read("reverse/docs/window_notes.md")
        api_offsets = read("reverse/docs/api_offsets.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = "\n".join([header, c200_notes, window_notes, api_offsets, catalog_tool])
        self.assertIn("bda_gui_send(bda_handle_t handle, u32 message, u32 a, u32 b)", header)
        self.assertIn("bda_gui_notify_like(bda_handle_t handle, u32 message, u32 a, u32 b)", header)
        self.assertIn("GUI +0x03c / +0x040", c200_notes)
        self.assertIn("GUI+0x03c -> 0x800dced0", c200_notes)
        self.assertIn("GUI+0x040 -> 0x800dd380", c200_notes)
        self.assertIn("handle+0x88", combined)
        self.assertIn("同步 send", combined)
        self.assertIn("异步 notify/post", combined)
        self.assertIn("0x02000000", c200_notes)
        self.assertIn("0x40000000", c200_notes)
        self.assertIn("0x1c byte 一项", c200_notes)
        self.assertIn("队列满", c200_notes)
        self.assertIn("return value 直接来自", c200_notes)
        self.assertIn("不是 standard queue item", window_notes)
        self.assertIn("0xb1 只置 pending flag", api_offsets)
        self.assertNotIn("notify/post/send message 类调用", catalog_tool)

    def test_gui_render_helpers_are_documented_as_low_level_multi_arg_api(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        api_offsets = read("reverse/docs/api_offsets.md")
        paint_notes = read("reverse/docs/paint_notes.md")
        paint_report = read("reverse/reports/paint_bda_report.md")
        picture_notes = read("reverse/docs/picture_notes.md")
        game_notes = read("reverse/docs/game_framework_notes.md")
        media_notes = read("reverse/docs/media_notes.md")
        system_bin_notes = read("reverse/docs/system_bin_notes.md")
        eros_report = read("reverse/reports/eros_bda_report.md")
        linkgame_report = read("reverse/reports/linkgame_bda_report.md")
        album_report = read("reverse/reports/album_bda_report.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = "\n".join([header, c200_notes, api_offsets, paint_notes, paint_report, picture_notes, game_notes, media_notes, system_bin_notes, eros_report, linkgame_report, album_report, catalog_tool])
        self.assertIn("BDA_GUI_RENDER_COPY_LIKE    0x410u", header)
        self.assertIn("BDA_GUI_RENDER_HELPER_LIKE  0x414u", header)
        self.assertIn("BDA_GUI_RENDER_FINISH_LIKE  0x418u", header)
        self.assertIn("SDK 暂不", header)
        self.assertIn("GUI +0x410 / +0x414 / +0x418", c200_notes)
        self.assertIn("GUI+0x410 -> 0x800b3124", c200_notes)
        self.assertIn("GUI+0x414 -> 0x800b34c0", c200_notes)
        self.assertIn("GUI+0x418 -> 0x800b3d90", c200_notes)
        self.assertIn("stack+0x10=height", c200_notes)
        self.assertIn("stack+0x14=descriptor", c200_notes)
        self.assertIn("descriptor 的 `+0x04/+0x08/+0x14/+0x18`", c200_notes)
        self.assertIn("backend `+0x88` 还是 `+0x80`", c200_notes)
        self.assertIn("临时分配裁剪 buffer", header + "\n" + paint_notes + "\n" + picture_notes)
        self.assertIn("backend `+0x8c`", paint_notes + "\n" + picture_notes)
        self.assertIn("结束后释放该临时 buffer", paint_notes + "\n" + picture_notes)
        self.assertIn("descriptor+0x04/+0x08", picture_notes)
        self.assertIn("+0x18` 选择 backend 路径", picture_notes)
        self.assertIn("stack+0x10/+0x14/+0x18/+0x1c/+0x20/+0x24", c200_notes)
        self.assertIn("stack+0x1c", c200_notes)
        self.assertIn("stack+0x1c = descriptor", eros_report + "\n" + game_notes)
        self.assertIn("descriptor+0x04/+0x08` 读到", c200_notes)
        self.assertIn("descriptor+0x04/+0x08/+0x14/+0x18", eros_report + "\n" + linkgame_report + "\n" + game_notes)
        self.assertIn("local `sp+0x34/+0x38`", c200_notes)
        self.assertIn("stack+0x14/+0x18` 作为裁剪后", c200_notes)
        self.assertIn("width/height gate", eros_report + "\n" + linkgame_report + "\n" + game_notes)
        self.assertIn("0x80474030+0x1c", c200_notes)
        self.assertIn("临时\n  buffer size", c200_notes)
        self.assertIn("按行复制裁剪后的区域", eros_report + "\n" + linkgame_report + "\n" + game_notes)
        self.assertNotIn("`GUI+0x414` 的栈参数布局仍未解决", linkgame_report)
        self.assertNotIn("`GUI+0x414` 和 `GUI+0x418` 的栈参数布局仍需恢复", eros_report)
        self.assertIn("default context `0x80825690`", c200_notes)
        self.assertIn("类型 word `+0x04 == 0x82`", c200_notes)
        self.assertIn("descriptor", combined)
        self.assertIn("MEM_ALLOC", c200_notes)
        self.assertIn("`+0x80/+0x88/+0x8c`", c200_notes)
        self.assertIn("stack+0x14` 作为第二个 context", c200_notes)
        self.assertIn("stack+0x10` 参与第一矩形", c200_notes)
        self.assertIn("stack+0x18/+0x1c", c200_notes)
        self.assertIn("stack+0x20` 会原样转发给 backend `+0x94`", c200_notes)
        self.assertIn("sp+0x14 = context_b", paint_report)
        self.assertIn("sp+0x20 = backend_arg", paint_report)
        self.assertIn("归一化为两个\n  context", c200_notes)
        self.assertIn("backend `+0x94`", combined)
        self.assertIn("bda_gui_context_copy()", c200_notes)
        self.assertIn("不是简单 present/finish", picture_notes)
        self.assertIn("GUI +0x418  双 context/双矩形 render helper", system_bin_notes)
        self.assertIn("GUI +0x418   31 次  双 context/双矩形 render helper", album_report)
        self.assertIn("GUI +0x418  -> 双 context/双矩形 render helper", album_report)
        self.assertIn("不能把这些 helper 升格为\n可从裸 `bda_main()` 直接调用的 public image API", album_report)
        self.assertIn("`GUI+0x40c/+0x410/+0x414/+0x418` 已有 C200 级别参数边界", media_notes)
        self.assertIn("不等于可脱离 frame/control lifecycle 的 public\n图片 API", media_notes)
        self.assertNotIn("GUI +0x418  绘制/缩放/渲染辅助候选", system_bin_notes)
        self.assertNotIn("GUI +0x418   31 次  渲染结束/提交辅助候选", album_report)
        self.assertNotIn("GUI+0x418  -> 渲染结束/提交候选", album_report)
        self.assertIn("高层 source/destination 语义仍需", combined)
        self.assertNotIn("`GUI+0x418` 的完整 stack 参数语义仍需", paint_report)
        self.assertIn("六参数 render/copy helper", c200_notes)
        self.assertIn("context,x,y,width,height,descriptor", combined)
        self.assertIn("low-level render helper", catalog_tool)
        self.assertIn("双 context/双矩形", combined)

    def test_game_display_pump_is_documented_as_no_arg_state_pump(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        gameboy_notes = read("reverse/docs/gameboy_notes.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = "\n".join([header, c200_notes, gameboy_notes, catalog_tool])
        self.assertIn("BDA_GUI_GAME_DISPLAY_PUMP_LIKE", header)
        self.assertIn("static inline int bda_gui_game_display_pump_like(void)", header)
        self.assertNotIn("BDA_GUI_BLIT_STATE_LIKE", header)
        self.assertNotIn("bda_gui_blit_state_like", header)
        self.assertIn("GUI+0x6e0 -> 0x8005b844", c200_notes)
        self.assertIn("table entry 无参数", c200_notes)
        self.assertIn("0x80059f68", c200_notes)
        self.assertIn("0x8001e6c4", c200_notes)
        self.assertIn("0x8005a7e0", c200_notes)
        self.assertIn("0x1068", combined)
        self.assertIn("0x8047402c = 2", c200_notes)
        self.assertIn("带全局副作用的 game state pump", c200_notes)
        self.assertIn("GAMEBOY 没有调用", gameboy_notes)
        self.assertIn("GUI +0x6c0", gameboy_notes)
        self.assertIn("event code 8", gameboy_notes)
        self.assertIn("event code 11", gameboy_notes)
        self.assertIn("不是 10 ms Window Timer", gameboy_notes)
        self.assertIn("active-low pen GPIO", c200_notes)
        self.assertIn("雷霆战机.bda", c200_notes)
        self.assertIn("决战坦克.bda", c200_notes)
        self.assertIn("GUI+0x3f8", c200_notes)
        self.assertIn("GUI+0x400", c200_notes)
        self.assertIn("不是 framebuffer pointer", header)
        self.assertIn("不是 blit", c200_notes)
        self.assertIn("status getter", c200_notes)
        self.assertIn("触摸长按驱动的 game state pump", catalog_tool)

    def test_sys_raw_keycode_query_is_documented_as_raw_input(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        input_notes = read("reverse/docs/input_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        api_offsets = read("reverse/docs/api_offsets.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = "\n".join([header, readme, input_notes, c200_notes, api_offsets, catalog_tool])

        self.assertIn("#define BDA_SYS_KEYCODE_RAW_LIKE 0x088u", header)
        self.assertIn("static inline int bda_sys_keycode_raw_like(void)", header)
        self.assertIn("int bda_sys_keycode_raw_like(void);", readme)
        self.assertIn("SYS +0x088: `BDA_SYS_KEYCODE_RAW_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x8001b464`", c200_notes)
        self.assertIn("0xb0010100", combined)
        self.assertIn("0xb0010200", combined)
        self.assertIn("0xb0010300", combined)
        self.assertIn("raw code", combined)
        self.assertIn("0`、`4`、`5`、`6`、`7`、`9`、`10", combined)
        self.assertIn("不生成 GUI message", c200_notes)
        self.assertIn("不填充 packet", c200_notes)
        self.assertIn("不要在文档或示例中提前命名", c200_notes)
        self.assertIn("SYS +0x084: 不公开的 raw input/internal helper", c200_notes)
        self.assertIn("system function VA：`0x8001b6a8`", c200_notes)
        self.assertIn("0x8001b324()", c200_notes + "\n" + input_notes)
        self.assertIn("0x8001b0e4()", c200_notes + "\n" + input_notes)
        self.assertIn("SDK 不公开 wrapper", c200_notes + "\n" + input_notes)
        self.assertIn("不要把 `SYS+0x084` 命名为 input reset", c200_notes)
        self.assertIn("BDA_MSG_KEYDOWN_LIKE", input_notes)
        self.assertNotIn("bda_sys_keycode_raw_like(u32", header + readme)
        self.assertNotIn("BDA_SYS_INPUT_RESET_LIKE", header)
        self.assertNotIn("bda_sys_input_reset_like", header)

    def test_mem_alloc_free_c200_locking_and_ownership_are_documented(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        readme = read("reverse/docs/README.md")
        memory_notes = read("reverse/docs/memory_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = header + "\n" + readme + "\n" + memory_notes + "\n" + c200_notes + "\n" + catalog_tool
        self.assertIn("static inline void *bda_alloc(bda_size_t size)", header)
        self.assertIn("static inline void bda_free(void *ptr)", header)
        self.assertIn("static inline void *bda_track_alloc_like(bda_size_t size)", header)
        self.assertIn("static inline void bda_track_free_like(void *ptr)", header)
        self.assertIn("static inline void bda_mem_track_begin_like(u32 free_on_finish)", header)
        self.assertIn("static inline int bda_mem_track_report_like(u32 summary_only)", header)
        self.assertIn("static inline void bda_mem_track_finish_like(void)", header)
        self.assertIn("static inline void *bda_mem_track_retain_like(void *ptr)", header)
        self.assertIn("static inline void bda_mem_track_release_like(void *ptr)", header)
        self.assertNotIn("static inline int bda_free", header)
        self.assertIn("memory_notes.md", readme)
        self.assertIn("MEM +0x000: `BDA_MEM_TRACK_ALLOC_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x80058574`", c200_notes)
        self.assertIn("MEM +0x004: `BDA_MEM_TRACK_FREE_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x80058618`", c200_notes)
        self.assertIn("MEM +0x01c: `BDA_MEM_TRACK_BEGIN_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x80058554`", c200_notes)
        self.assertIn("MEM +0x020: `BDA_MEM_TRACK_REPORT_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x8005868c`", c200_notes)
        self.assertIn("MEM +0x024: `BDA_MEM_TRACK_FINISH_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x80058750`", c200_notes)
        self.assertIn("MEM +0x028: `BDA_MEM_TRACK_RETAIN_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x80058820`", c200_notes)
        self.assertIn("MEM +0x02c: `BDA_MEM_TRACK_RELEASE_LIKE`", c200_notes)
        self.assertIn("system function VA：`0x800588b8`", c200_notes)
        self.assertIn("MEM +0x008: `BDA_MEM_ALLOC`", c200_notes)
        self.assertIn("system function VA：`0x80007648`", c200_notes)
        self.assertIn("MEM +0x00c: `BDA_MEM_FREE`", c200_notes)
        self.assertIn("system function VA：`0x800067f4`", c200_notes)
        self.assertIn("a0=size", combined)
        self.assertIn("0x80007648(size)", combined)
        self.assertIn("0x80474020", combined)
        self.assertIn("0x80474018", combined)
        self.assertIn("0x8047401c", combined)
        self.assertIn("0x80823e40", combined)
        self.assertIn("active flag", combined)
        self.assertIn("free_on_finish", combined)
        self.assertIn("summary_only", combined)
        self.assertIn("不会释放 pointer", combined)
        self.assertIn("bda_mem_track_finish_like", combined)
        self.assertIn("bda_mem_track_retain_like", combined)
        self.assertIn("bda_mem_track_release_like", combined)
        self.assertIn("refcount-like", combined)
        self.assertIn("可能释放", combined)
        self.assertIn("0x800067f4(ptr)", combined)
        self.assertIn("0x80007440(size)", combined)
        self.assertIn("a0=ptr", combined)
        self.assertIn("0x80006620(ptr)", combined)
        self.assertIn("0x800067f4(ptr)", combined)
        self.assertIn("0x80473f00", c200_notes)
        self.assertIn("没有可用 return value", combined)
        self.assertIn("普通开发优先使用 `bda_alloc()`", combined)
        self.assertIn("不要和 libc `malloc/free` 混用", combined)
        self.assertIn("bda_free(NULL)", memory_notes)
        self.assertIn("固件堆内存分配", catalog_tool)
        self.assertIn("Firmware Heap Allocator", memory_notes)
        self.assertIn("firmware heap alloc wrapper", memory_notes)
        self.assertIn("C200 table entry 目标为 `0x80007648`", memory_notes)
        self.assertIn("pointer 必须用 `bda_free()` 释放", memory_notes)
        self.assertNotIn("固件堆分配入口", memory_notes)
        self.assertNotIn("C200 表入口", memory_notes)
        self.assertNotIn("栈指针", memory_notes)

    def test_mem_alloc_example_checks_failure_and_frees_owned_pointer(self) -> None:
        source = read("reverse/examples/mem_alloc_demo.c")
        memory_notes = read("reverse/docs/memory_notes.md")
        sdk_readme = read("docs/sdk_api_layout.md")
        docs_readme = read("reverse/docs/README.md")
        combined_docs = memory_notes + "\n" + sdk_readme + "\n" + docs_readme

        self.assertIn("mem_alloc_demo.c", combined_docs)
        self.assertIn("bda_alloc(64)", source)
        self.assertIn("if (buffer == 0)", source)
        self.assertIn("alloc failed", source)
        self.assertIn("bda_free(buffer)", source)
        self.assertNotIn("bda_free(0)", source)
        self.assertNotIn("bda_free(NULL)", source)
        self.assertIn("不会调用 `bda_free(NULL)`", memory_notes)

    def test_reverse_report_template_headings_are_chinese(self) -> None:
        forbidden = [
            "Analysis Report",
            "BDA report",
            "## Status",
            "## API Usage Summary",
            "## Header And Layout",
            "## Header and layout",
            "## External resources",
            "## API usage summary",
            "## File-system behavior",
            "## GUI/event behavior",
            "## Cross-checks",
            "## Open questions",
            "## Generated Index",
            "## Deep Reports Already Started",
            "Evidence:",
            "Cached runtime table globals:",
            "External resources:",
            "classified indirect runtime-table calls",
            "## External Resources",
            "## Text Rendering Cross-Checks",
            "## File-System Behavior",
            "## Window/Event Behavior",
            "## Unknowns",
            "## Next Static Tasks",
        ]
        for report in (ROOT / "reverse" / "reports").glob("*.md"):
            text = report.read_text(encoding="utf-8")
            for phrase in forbidden:
                self.assertNotIn(phrase, text, report)
        reports_readme = read("reverse/reports/README.md")
        self.assertIn("# BDA 逆向报告", reports_readme)
        self.assertIn("## 生成索引", reports_readme)

    def test_c200_menu_index_report_documents_deploy_menu_boundary(self) -> None:
        report = read("reverse/reports/c200_menu_index_notes.md")
        reports_readme = read("reverse/reports/README.md")
        required = [
            "C200 首页菜单索引线索",
            "`a:\\系统\\数据\\Config.inf`",
            "`A:\\应用\\程序\\*.bda`",
            "首页 carousel",
            "硬编码了一批",
            "`Config.inf` 与内置 BDA 的目录扫描、category 分类、排序、展示和菜单索引无关",
            "`A:\\应用\\程序\\我的相册.bda`",
            "`A:\\应用\\程序\\时间.bda`",
            "## 分类容量表",
            "`current_count < capacity`",
            "| `1` | 听说 | `7` | `0` | `0x8036683e` |",
            "| `4` | 娱乐天地 | `10` | `0` | `0x8036685c` |",
            "| `7` | 词典 | `15` | `7` | `0x8036687a` |",
            "| `9` | 工具 | `20` | `4` | `0x8036688e` |",
            "其他分类容量目前是 C200 静态证据",
        ]
        for phrase in required:
            self.assertIn(phrase, report)
        self.assertIn("c200_menu_index_notes.md", reports_readme)

    def test_bda_inventory_report_is_chinese(self) -> None:
        text = read("reverse/reports/bda_inventory.md")
        self.assertIn("# 原生 BDA 清点索引", text)
        self.assertIn("| BDA | 大小 | 标题 | 分类 | 入口 | BSS | 校验 | 高频 API Offset | DLX 引用 |", text)
        self.assertIn("逐应用报告应把本索引当作清单", text)
        forbidden = [
            "Native BDA Inventory",
            "Generated from the original app directory",
            "Hot API Offsets are raw",
            "Per-app reports should use this inventory",
        ]
        for phrase in forbidden:
            self.assertNotIn(phrase, text)

    def test_high_value_reverse_reports_are_chinese(self) -> None:
        expectations = {
            "reverse/reports/ebook_bda_report.md": [
                "# 电子图书.bda 逆向报告",
                "## 文字绘制证据",
                "## 资源和图片绘制证据",
                "## 未确认点",
            ],
            "reverse/reports/recorder_bda_report.md": [
                "# 数码录音.bda 逆向报告",
                "## 字符串和文件模型",
                "## 文件系统行为",
                "## 未确认点",
            ],
            "reverse/reports/eros_bda_report.md": [
                "# Eros方块.bda 逆向报告",
                "## 文件和存档行为",
                "## GUI 和游戏渲染",
                "## 未确认点",
            ],
            "reverse/reports/linkgame_bda_report.md": [
                "# 连连看.bda 逆向报告",
                "## 文件和存档行为",
                "## GUI 和游戏渲染",
                "## 未确认点",
            ],
            "reverse/reports/thunder_bda_report.md": [
                "# 雷霆战机.bda 逆向报告",
                "## 打包音效流程",
                "## 当前解释",
            ],
            "reverse/reports/tank_bda_report.md": [
                "# 决战坦克.bda 逆向报告",
                "## 打包音效流程",
                "## 当前解释",
            ],
            "reverse/reports/ninecourse_bda_report.md": [
                "# 九门课程.bda 逆向报告",
                "## GUI 对象模型",
                "## 对 SDK 的含义",
                "## 未确认点",
            ],
            "reverse/reports/schedule_bda_report.md": [
                "# 课程表.bda 逆向报告",
                "## 窗口和事件流程",
                "## 对 SDK 的含义",
                "## 未确认点",
            ],
            "reverse/reports/blackwhite_bda_report.md": [
                "# 黑白子.bda 逆向报告",
                "## 内嵌 VX 资源",
                "## 当前解释",
            ],
            "reverse/reports/jiugongge_bda_report.md": [
                "# 九宫格.bda 逆向报告",
                "## 外部文件",
                "## 当前解释",
            ],
            "reverse/reports/sango_bda_report.md": [
                "# 三国霸业.bda 逆向报告",
                "## 外部文件",
                "## 当前解释",
            ],
            "reverse/reports/settings_bda_report.md": [
                "# 系统设置.bda 逆向报告",
                "## 磁盘和存储信息",
                "## 文件系统行为",
                "## 未确认点",
            ],
            "reverse/reports/paint_bda_report.md": [
                "# 电子画板.bda 逆向报告",
                "## 像素和线段绘制",
                "## 区域绘制和刷新",
                "## 未确认点",
            ],
        }
        forbidden = [
            "Generated evidence",
            "Classified indirect calls",
            "Hot GUI offsets",
            "This is better evidence",
            "For now these should",
            "The app uses",
            "No external",
            "unknown helper",
            "SDK Implications",
            "Open Items",
        ]
        for path, required_phrases in expectations.items():
            text = read(path)
            for phrase in required_phrases:
                self.assertIn(phrase, text, path)
            for phrase in forbidden:
                self.assertNotIn(phrase, text, path)

    def test_rect_prepare_has_wrapper_after_c200_abi_confirmation(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        picture_notes = read("reverse/docs/picture_notes.md")
        self.assertIn("BDA_GUI_RECT_PREPARE_LIKE", header)
        self.assertIn("bda_gui_rect_prepare_like", header)
        self.assertIn("wrapper 通过 `bda_call5`", picture_notes)
        self.assertNotIn("SDK 目前只暴露", picture_notes)

    def test_examples_do_not_use_deprecated_dlx_loader_aliases(self) -> None:
        for source in (ROOT / "reverse" / "examples").glob("*.c"):
            text = source.read_text(encoding="utf-8")
            self.assertNotIn("bda_load_dlx_gui(", text, source)
            self.assertNotIn("bda_load_dlx_ex(", text, source)
            self.assertNotIn("bda_file_selector_load_default_skin_like(", text, source)
            self.assertNotIn("bda_gui_create_ex(", text, source)
            self.assertNotIn("BDA_MSG_TOUCH_B_LIKE", text, source)

    def test_fs_find_examples_use_sized_find_data_struct(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        self.assertIn("#define BDA_FS_FIND_DATA_SIZE 0x220u", header)
        self.assertIn("typedef struct bda_fs_find_data_like", header)
        self.assertIn("char name_or_path12[0x20a]", header)
        self.assertIn("typedef struct bda_fs_disk_info_like", header)
        self.assertIn("bda_fs_disk_free_bytes_like", header)
        self.assertIn("typedef unsigned long long u64;", header)
        self.assertIn("bda_fs_disk_free_bytes64_like", header)
        self.assertIn("drive 0/1", header)
        self.assertIn("bytes_per_sector 固定写入 0x200", header)
        for source in (ROOT / "reverse" / "examples").glob("fs_find*_probe.c"):
            text = source.read_text(encoding="utf-8")
            self.assertIn("bda_fs_find_data_like_t", text, source)
            self.assertNotIn("g_find_data[512]", text, source)
        list_probe = read("reverse/examples/fs_list_probe.c")
        self.assertIn("bda_fs_find_data_like_t", list_probe)
        self.assertNotIn("g_find_data[512]", list_probe)

    def test_fs_diskinfo_drive_and_output_layout_are_documented(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        fs_notes = read("reverse/docs/fs_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        combined = "\n".join([header, fs_notes, c200_notes, catalog_tool])
        self.assertIn("static inline int bda_fs_diskinfo_like(u32 drive, bda_fs_disk_info_like_t *info)", header)
        self.assertIn("drive & 0xff", header + "\n" + fs_notes)
        self.assertIn("确认 `0` 和 `1` 两类路径", fs_notes)
        self.assertIn("drive 不是 `0` 或 `1` 时返回 `-1`", c200_notes)
        self.assertIn("内部错误码 `9`", c200_notes)
        self.assertIn("内部错误码 `0x10`", c200_notes)
        self.assertIn("info+0x00", c200_notes)
        self.assertIn("info+0x04", c200_notes)
        self.assertIn("info+0x08", c200_notes)
        self.assertIn("info+0x0c = 0x200", c200_notes)
        self.assertIn("u64 bda_fs_disk_free_bytes64_like(const bda_fs_disk_info_like_t *info)", read("reverse/docs/README.md"))
        self.assertIn("u64 free_bytes = bda_fs_disk_free_bytes64_like(&info);", fs_notes)
        self.assertIn("32-bit return value", fs_notes)
        self.assertIn("64-bit helper", fs_notes)
        self.assertIn("32-bit 兼容计算", c200_notes)
        self.assertIn("free_clusters *", header)
        self.assertIn("sectors_per_cluster * bytes_per_sector", combined)
        self.assertIn("(u64)info->free_clusters", header)
        self.assertNotIn("u32 free_bytes = bda_fs_disk_free_bytes_like(&info);", fs_notes)
        self.assertIn("成功写 4 个 word", catalog_tool)

    def test_fs_findnext_and_findclose_cursor_paths_are_documented(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        fs_notes = read("reverse/docs/fs_notes.md")
        c200_notes = read("reverse/docs/c200_api_function_notes.md")
        catalog_tool = read("reverse/bda_api_catalog.py")
        self.assertIn("bda_fs_findfirst_like(const char *pattern, u32 attr, bda_fs_find_data_like_t *find_data)", header)
        self.assertIn("0x20a byte 临时 path buffer", header + "\n" + fs_notes)
        self.assertIn("pattern, attr, find_data", c200_notes)
        self.assertIn("0x8016f904(pattern, temp_path)", fs_notes)
        self.assertIn("0x8017e1a0(temp_path, find_data, attr)", fs_notes)
        self.assertIn("C200 function-level disasm", fs_notes)
        self.assertIn("table entry 会先申请 `0x20a` byte 临时 path buffer", fs_notes)
        self.assertIn("早期 probe 使用的 `unsigned char[512]` 偏小", fs_notes)
        self.assertIn("0x80474280 = 1", c200_notes + "\n" + fs_notes)
        self.assertIn("pattern,attr,find_data", catalog_tool)
        self.assertIn("bda_fs_findnext_like(bda_fs_find_data_like_t *find_data)", header)
        self.assertIn("bda_fs_findclose_like(bda_fs_find_data_like_t *find_data)", header)
        self.assertIn("find_data+0x10", header + "\n" + catalog_tool)
        self.assertIn("0x8017f6b0(find_data)", catalog_tool)
        self.assertIn("find_data+0x00 cursor", catalog_tool)
        self.assertIn("`0x8017f6b0(find_data)` 更新下一项", c200_notes)
        self.assertIn("0x8017f73c(find_data)", c200_notes)
        self.assertIn("内部错误码 `9`", c200_notes)
        self.assertIn("内部错误码 `0x10`", c200_notes)
        self.assertIn("原地更新 `data`", c200_notes)
        self.assertIn("可省略的 no-op", header)
        self.assertIn("`0x8017f6b0(find_data)` 原地更新下一项", fs_notes)
        self.assertIn("`0x8017f73c(find_data)` 清理 cursor", fs_notes)

    def test_primary_build_tool_help_is_chinese(self) -> None:
        scripts = [
            "reverse/bda_compile_c.py",
            "reverse/bda_fix_header_checksum.py",
            "reverse/bda_set_icon_png.py",
            "reverse/bda_copy_icons.py",
            "reverse/bda_extract_icons.py",
            "reverse/dlx_build.py",
            "reverse/dlx_extract.py",
            "reverse/dlx_inspect.py",
            "reverse/bda_api_catalog.py",
            "reverse/c200_api_tables.py",
            "reverse/c200_api_disasm.py",
            "reverse/c200_menu_scan.py",
            "reverse/bda_inventory.py",
            "reverse/bda_table_globals.py",
            "reverse/bda_table_call_scan.py",
            "reverse/bda_sdk_usage.py",
        ]
        for script in scripts:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            output = subprocess.check_output(
                [sys.executable, script, "--help"],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                env=env,
            )
            self.assertRegex(output, r"BDA|DLX|VX", script)
            self.assertNotIn("Compile freestanding", output, script)
            self.assertNotIn("Build a first-pass", output, script)
            self.assertNotIn("Existing native BDA", output, script)
            self.assertNotIn("package from scratch", output, script)
            self.assertNotIn("Generate BDA VX icon resources", output, script)
            self.assertNotIn("Copy the four VX icon resources", output, script)
            self.assertNotIn("Extract VX RGB565 icon resources", output, script)
            self.assertNotIn("Build a simple BBK DLX resource container", output, script)
            self.assertNotIn("Extract BBK DLX resources", output, script)
            self.assertNotIn("Inspect BBK DLX resource containers", output, script)
            self.assertNotIn("Generate a Chinese BDA API coverage catalog", output, script)
            self.assertNotIn("BDA to modify", output, script)
            self.assertNotIn("RGBA matte color", output, script)
            self.assertNotIn("PNG alpha matte color", output, script)

    def test_core_build_tool_help_uses_chinese_argparse_labels(self) -> None:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        expectations = {
            "reverse/bda_compile_c.py": [
                "包含 bda_main 的 freestanding C 源码",
                "菜单标题，GBK 编码后最多 16 字节",
                "菜单分类编号，通常使用 1..9",
                "1  听说（总菜单项上限 7）",
                "4  娱乐天地（游戏目录；总菜单项上限 10）",
                "8  娱乐（影音、多媒体目录；总菜单项上限 10）",
                "9  工具（总菜单项上限 20）",
                "0  固件范围检查允许",
                "固件内建项也会占用槽位",
                "category 4 的第 11 个 BDA 不展示已动态验证",
                "菜单图标 PNG",
                "输出 BDA 路径",
            ],
            "reverse/bda_validate.py": ["要校验的 BDA 文件", "输出 JSON，便于脚本集成"],
            "reverse/bda_fix_header_checksum.py": ["要修复 checksum 的 BDA 文件", "输出 BDA 路径"],
            "reverse/bda_deploy_bundle.py": [
                "输出 deploy bundle 目录",
                "原始 系统\\数据\\Config.inf 路径",
                "Config.inf 不作为 BDA app 注册或启动证据",
            ],
            "reverse/config_inf_add.py": ["输出 Config.inf 路径", "写入前列出现有 entries"],
            "reverse/bda_set_icon_png.py": ["要修改的 BDA", "输出 BDA 路径"],
            "reverse/dlx_build.py": ["输出 DLX 文件", "DLX 变体，默认 3"],
            "reverse/dlx_extract.py": ["要导出的 DLX 文件", "VX RGB565 像素字节序"],
            "reverse/dlx_inspect.py": ["要检查的 DLX 文件", "输出 JSON 报告"],
            "reverse/bda_extract_icons.py": ["要导出图标的 BDA", "输出目录"],
            "reverse/bda_copy_icons.py": ["提供 VX 图标资源的 BDA", "输出 BDA 路径"],
            "reverse/bda_api_catalog.py": ["原机 BDA inventory JSON", "输出 Markdown 文件"],
            "reverse/c200_api_tables.py": ["仓库根目录", "SDK header", "可选 JSON 输出路径"],
            "reverse/c200_api_disasm.py": ["SDK 宏名，例如 BDA_GUI_MSGBOX", "表内 offset，例如 0x2b8"],
            "reverse/c200_menu_scan.py": ["C200.bin 路径", "输出 Markdown 报告"],
            "reverse/bda_inventory.py": ["原机应用 BDA 目录", "输出 Markdown 索引"],
            "reverse/bda_table_globals.py": ["缓存 GUI/FS/SYS/MEM/RES runtime table pointer", "要扫描的原机 BDA 文件"],
            "reverse/bda_table_call_scan.py": ["按缓存 table global", "要扫描的原机 BDA 文件", "只输出指定 API 表内 offset"],
            "reverse/bda_sdk_usage.py": ["生成单个原机 BDA", "要分析的 BDA 文件", "输出 Markdown"],
        }
        scripts_without_positionals = {
            "reverse/bda_deploy_bundle.py",
            "reverse/dlx_build.py",
            "reverse/bda_api_catalog.py",
            "reverse/c200_api_tables.py",
            "reverse/c200_api_disasm.py",
            "reverse/c200_menu_scan.py",
            "reverse/bda_inventory.py",
            "reverse/bda_table_globals.py",
            "reverse/bda_table_call_scan.py",
        }
        for script, phrases in expectations.items():
            output = subprocess.check_output(
                [sys.executable, script, "--help"],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                env=env,
            )
            if script not in scripts_without_positionals:
                self.assertIn("位置参数", output, script)
            self.assertIn("选项", output, script)
            self.assertIn("显示帮助并退出", output, script)
            for phrase in phrases:
                self.assertIn(phrase, output, script)
            self.assertNotIn("positional arguments", output, script)
            self.assertNotIn("show this help message and exit", output, script)

    def test_thunder_source_api_mapping_is_documented(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        notes = read("reverse/docs/thunder_api_notes.md")
        inventory = read("reverse/docs/thunder_api_inventory.md")
        report = read("reverse/reports/thunder_bda_report.md")

        for name in [
            "bda_gui_display_pixel_bytes_like",
            "bda_gui_compat_context_create_like",
            "bda_gui_select_draw_object_like",
            "bda_gui_move_to_like",
            "bda_gui_line_to_like",
            "bda_gui_circle_like",
            "bda_gui_rectangle_like",
            "bda_gui_current_font_like",
            "bda_gui_font_cell_width_like",
            "bda_gui_font_cell_height_like",
            "bda_gui_invalidate_window_like",
        ]:
            self.assertIn(name, header)
            self.assertIn(name, notes)

        self.assertIn("间接调用总数：295", inventory)
        self.assertIn("唯一 table entry：78", inventory)
        self.assertNotIn("| 未命名 |", inventory)
        self.assertIn("| FS | +0x068 | 1 | 未公开 |", inventory)
        self.assertIn("| SYS | +0x050 | 1 | 未公开 |", inventory)
        self.assertIn("源码不是这份 BDA 的精确", notes)
        self.assertIn("配套源码的版本边界", report)

    def test_thunder_rectangle_wrapper_uses_o32_fifth_argument(self) -> None:
        header = SDK_HEADER.read_text(encoding="utf-8")
        start = header.index("static inline void bda_gui_rectangle_like")
        body = header[start : start + 500]
        self.assertIn("bda_call5", body)
        self.assertIn("BDA_GUI_RECTANGLE_LIKE", body)


if __name__ == "__main__":
    unittest.main()
