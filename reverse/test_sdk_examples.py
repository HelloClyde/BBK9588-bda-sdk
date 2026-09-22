from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bda_compile_c import bundled_prefix, find_tool
from bda_validate import validate_bda


class SdkExamplesTest(unittest.TestCase):
    PREBUILT_EXAMPLES = [
        ("example/basic/hello_world/HelloWorld.bda", "HelloWorld", 9),
        ("example/filesystem/fs_write/FsWrite.bda", "FsWrite", 9),
        ("example/filesystem/fs_flush/FsFlush.bda", "FsFlush", 9),
        ("example/filesystem/file_management/FileManagement.bda", "FileManage", 9),
        ("example/input/key_polling/KeyInput.bda", "KeyInput", 9),
        ("example/input/touch_crosshair/TouchCrosshair.bda", "TouchXY", 9),
        ("example/graphics/primitives/GraphicsPrimitives.bda", "Graphics", 9),
        ("example/graphics/picture_render/PictureRender.bda", "PictureRaw", 9),
        ("example/graphics/direct_framebuffer/DirectFramebuffer.bda", "DirectFB", 9),
        ("example/games/minesweeper/MinesweeperV1.bda", "MinesV1", 4),
        ("example/system/runtime_services/RuntimeServices.bda", "RuntimeSvc", 9),
        ("example/system/high_resolution_timer/HighResolutionTimer.bda", "HighResTimer", 9),
        ("example/system/hardware_detection/HardwareDetect.bda", "HardwareDetect", 9),
        ("example/system/file_selector/FileSelector.bda", "FileSelect", 9),
        ("example/system/confirm_dialog/ConfirmDialog.bda", "Confirm", 9),
        ("example/system/three_button_dialog/ThreeButtonDialog.bda", "ThreeDialog", 9),
        ("example/system/help_page/HelpPage.bda", "HelpPage", 9),
        ("example/system/audio_pcm/AudioPcm.bda", "AudioPCM", 9),
        ("example/system/audio_capture/AudioCapture.bda", "AudioCapture", 9),
        ("example/gui/control_gallery/ControlGallery.bda", "Controls", 9),
        ("example/gui/custom_control/CustomControl.bda", "CustomCtrl", 9),
        ("example/gui/gif_player/GifPlayer.bda", "GifPlayer", 9),
    ]

    @classmethod
    def setUpClass(cls) -> None:
        prefix = bundled_prefix() or "mipsel-none-elf-"
        try:
            find_tool(prefix, "gcc")
            find_tool(prefix, "objcopy")
        except SystemExit as exc:
            raise unittest.SkipTest(str(exc))
        cls.prefix = prefix
        cls.out_dir = Path("build") / "test_sdk_examples"
        cls.out_dir.mkdir(parents=True, exist_ok=True)

    def build_and_validate(
        self,
        source: str,
        title: str,
        include_dirs: tuple[str, ...] = (),
        category: int = 9,
        icon_png: str | None = None,
    ) -> dict[str, object]:
        output = self.out_dir / f"{title}.bda"
        command = [
            sys.executable,
            "reverse/bda_compile_c.py",
            source,
            "--prefix",
            self.prefix,
            "--title",
            title,
            "--category",
            str(category),
        ]
        for include_dir in include_dirs:
            command.extend(["-I", include_dir])
        if icon_png is not None:
            command.extend(["--icon-png", icon_png])
        command.extend(["-o", str(output)])
        output_text = subprocess.check_output(command)
        report = validate_bda(output)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["title"], title)
        self.assertEqual(report["category"], category)
        self.assertEqual(report["entry_offset"], 0x95F8)
        return report

    def test_hello_msgbox_example_builds(self) -> None:
        self.build_and_validate("reverse/examples/hello_msgbox.c", "HelloC")

    def test_checked_in_verified_bdas_validate(self) -> None:
        for path, title, category in self.PREBUILT_EXAMPLES:
            report = validate_bda(Path(path))
            self.assertTrue(report["ok"], path)
            self.assertEqual(report["title"], title, path)
            self.assertEqual(report["category"], category, path)

    def test_verified_example_leaf_directories_pair_source_and_bda(self) -> None:
        expected_bdas = {Path(path) for path, _, _ in self.PREBUILT_EXAMPLES}
        actual_bdas = set(Path("example").rglob("*.bda"))
        self.assertEqual(actual_bdas, expected_bdas)

        for bda_path in expected_bdas:
            sources = list(bda_path.parent.glob("*.c"))
            binaries = list(bda_path.parent.glob("*.bda"))
            self.assertEqual(len(sources), 1, bda_path.parent)
            self.assertEqual(binaries, [bda_path], bda_path.parent)

    def test_gui_rect_contains_example_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/gui_rect_contains_demo.c", "RectDemo", ("reverse",)
        )

    def test_gui_screen_orientation_example_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/gui_screen_orientation_demo.c",
            "OrientDemo",
            ("reverse",),
        )

    def test_input_state_example_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/input_state_demo.c", "Input", ("reverse",)
        )

    def test_mem_alloc_example_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/mem_alloc_demo.c", "MemDemo", ("reverse",)
        )

    def test_fs_read_example_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/fs_read_demo.c", "FsRead", ("reverse",)
        )

    def test_fs_read_raw_example_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/fs_read_raw_demo.c", "FsRaw", ("reverse",)
        )

    def test_fs_write_example_builds(self) -> None:
        self.build_and_validate("example/filesystem/fs_write/fs_write_demo.c", "FsWrite")

    def test_fs_flush_example_builds(self) -> None:
        self.build_and_validate(
            "example/filesystem/fs_flush/fs_flush_power_demo.c", "FsFlush"
        )

    def test_file_management_example_builds(self) -> None:
        self.build_and_validate(
            "example/filesystem/file_management/file_management_demo.c",
            "FileManage",
        )

    def test_key_msgbox_example_builds(self) -> None:
        self.build_and_validate("example/input/key_polling/key_msgbox_demo.c", "KeyInput")

    def test_touch_crosshair_example_builds(self) -> None:
        self.build_and_validate(
            "example/input/touch_crosshair/touch_crosshair_demo.c", "TouchXY"
        )

    def test_fast_touch_hardware_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/gameboy_fast_touch_hardware_probe.c",
            "FastTouchV3",
            ("reverse",),
        )

    def test_gameboy_event_touch_hardware_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/gameboy_event_touch_hardware_probe.c",
            "GbTouchEvtV1",
            ("reverse",),
        )

    def test_touch_stage_v12_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/touch_input_stage_probe_v12.c", "TouchV12"
        )

    def test_touch_stage_v13_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/touch_input_stage_probe_v13.c", "TouchV13"
        )

    def test_touch_stage_v14_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/touch_input_stage_probe_v14.c", "TouchV14"
        )

    def test_touch_stage_v15_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/touch_input_stage_probe_v15.c", "TouchV15"
        )

    def test_touch_stage_v16_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/touch_input_stage_probe_v16.c", "TouchV16"
        )

    def test_touch_stage_v17_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/touch_input_stage_probe_v17.c", "TouchV17"
        )

    def test_touch_stage_v18_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/touch_input_stage_probe_v18.c", "TouchV18"
        )

    def test_touch_stage_v19_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/touch_input_stage_probe_v19.c", "TouchV19"
        )

    def test_touch_stage_v20_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/touch_input_stage_probe_v20.c", "TouchV20"
        )

    def test_touch_stage_v21_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/touch_input_stage_probe_v21.c", "TouchV21"
        )

    def test_touch_stage_v22_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/touch_input_stage_probe_v22.c", "TouchV22"
        )

    def test_touch_stage_v23_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/touch_input_stage_probe_v23.c", "TouchV23"
        )

    def test_graphics_primitives_example_builds(self) -> None:
        self.build_and_validate("example/graphics/primitives/graphics_primitives_demo.c", "Graphics")

    def test_picture_render_example_builds(self) -> None:
        self.build_and_validate(
            "example/graphics/picture_render/picture_render_demo.c", "PictureRaw"
        )

    def test_direct_framebuffer_example_builds(self) -> None:
        self.build_and_validate(
            "example/graphics/direct_framebuffer/direct_framebuffer_demo.c",
            "DirectFB",
        )

    def test_control_gallery_example_builds(self) -> None:
        self.build_and_validate(
            "example/gui/control_gallery/control_gallery_demo.c", "Controls"
        )

    def test_control_skin_binding_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/control_skin_binding_probe.c", "SkinBind"
        )

    def test_custom_control_example_builds(self) -> None:
        self.build_and_validate(
            "example/gui/custom_control/custom_control_demo.c", "CustomCtrl"
        )

    def test_gif_player_example_builds(self) -> None:
        self.build_and_validate(
            "example/gui/gif_player/gif_player_demo.c", "GifPlayer"
        )

    def test_runtime_services_example_builds(self) -> None:
        self.build_and_validate(
            "example/system/runtime_services/runtime_services_demo.c", "RuntimeSvc"
        )

    def test_high_resolution_timer_example_builds(self) -> None:
        self.build_and_validate(
            "example/system/high_resolution_timer/high_resolution_timer_demo.c",
            "HighResTimer",
        )

    def test_hardware_detection_example_builds(self) -> None:
        self.build_and_validate(
            "example/system/hardware_detection/hardware_detection_demo.c",
            "HardwareDetect",
        )

    def test_audio_pcm_example_builds(self) -> None:
        self.build_and_validate(
            "example/system/audio_pcm/audio_pcm_demo.c", "AudioPCM"
        )

    def test_audio_capture_example_builds(self) -> None:
        self.build_and_validate(
            "example/system/audio_capture/audio_capture_demo.c", "AudioCapture"
        )

    def test_record_stream_hardware_probe_v1_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/record_stream_hardware_probe.c",
            "RecPcmV1",
            ("reverse",),
        )

    def test_record_stream_hardware_probe_v2_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/record_stream_hardware_probe_v2.c",
            "RecPcmV2",
            ("reverse",),
        )

    def test_record_stream_hardware_probe_v3_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/record_stream_hardware_probe_v3.c",
            "RecPcmV3",
            ("reverse",),
        )

    def test_record_stream_hardware_probe_v4_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/record_stream_hardware_probe_v4.c",
            "RecPcmV4",
            ("reverse",),
        )

    def test_record_stream_hardware_probe_v5_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/record_stream_hardware_probe_v5.c",
            "RecPcmV5",
            ("reverse",),
        )

    def test_record_stream_hardware_probe_v6_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/record_stream_hardware_probe_v6.c",
            "RecPcmV6",
            ("reverse",),
        )

    def test_record_stream_hardware_probe_v7_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/record_stream_hardware_probe_v7.c",
            "RecPcmV7",
            ("reverse",),
        )

    def test_record_stream_hardware_probe_v8_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/record_stream_hardware_probe_v8.c",
            "RecPcmV8",
            ("reverse",),
        )

    def test_record_stream_hardware_probe_v9_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/record_stream_hardware_probe_v9.c",
            "RecPcmV9",
            ("reverse",),
        )

    def test_record_stream_hardware_probe_v10_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/record_stream_hardware_probe_v10.c",
            "RecPcmV10",
            ("reverse",),
        )

    def test_record_stream_hardware_probe_v11_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/record_stream_hardware_probe_v11.c",
            "RecPcmV11",
            ("reverse",),
        )

    def test_record_stream_hardware_probe_v12_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/record_stream_hardware_probe_v12.c",
            "RecPcmV12",
            ("reverse",),
        )

    def test_record_stream_hardware_probe_v13_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/record_stream_hardware_probe_v13.c",
            "RecPcmV13",
            ("reverse",),
        )

    def test_gam4980_runtime_admission_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/gam4980_runtime_api_probe.c", "G498RunV1"
        )

    def test_gam4980_picture_admission_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/gam4980_picture_api_probe.c", "G498PicV1"
        )

    def test_fs_find_example_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/fs_find_demo.c", "FsFind", ("reverse",)
        )

    def test_fs_diskinfo_example_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/fs_diskinfo_demo.c", "FsDisk", ("reverse",)
        )

    def test_fs_status_example_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/fs_status_demo.c", "FsStat", ("reverse",)
        )

    def test_res_state_example_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/res_state_demo.c", "ResState", ("reverse",)
        )

    def test_tile_blit_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/tile_blit_probe.c", "TileBlit", ("reverse",)
        )

    def test_time_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/time_probe.c", "TimeProbe", ("reverse",)
        )

    def test_game_api_probe_builds(self) -> None:
        self.build_and_validate("reverse/examples/game_api_probe.c", "GameApiV1")

    def test_game_audio_probe_builds(self) -> None:
        self.build_and_validate("reverse/examples/game_audio_probe.c", "GameAudioV2")

    def test_game_audio_cleanup_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/game_audio_cleanup_probe.c", "GameAudioV5"
        )

    def test_game_audio_volume_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/game_audio_volume_probe.c", "GameVolV1"
        )

    def test_game_graphics_probe_builds(self) -> None:
        self.build_and_validate("reverse/examples/game_graphics_probe.c", "GameGfxV3")

    def test_game_image_probe_builds(self) -> None:
        self.build_and_validate("reverse/examples/game_image_probe.c", "GameImgV4")

    def test_game_image_render_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/game_image_render_probe.c", "GameImgV5"
        )

    def test_game_image_compat_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/game_image_compat_probe.c", "GameImgV6"
        )

    def test_game_jpeg_probe_builds(self) -> None:
        self.build_and_validate("reverse/examples/game_jpeg_probe.c", "GameJpgV7")

    def test_game_compat_animation_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/game_compat_animation_probe.c", "GameAnimV8"
        )

    def test_game_tick_probe_builds(self) -> None:
        self.build_and_validate("reverse/examples/game_tick_probe.c", "GameTickV9")

    def test_high_resolution_timer_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/high_resolution_timer_probe.c", "HiResTimerV4"
        )

    def test_game_polyline_clip_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/game_polyline_clip_probe.c", "GameGfxV10"
        )

    def test_game_ellipse_probe_builds(self) -> None:
        self.build_and_validate("reverse/examples/game_ellipse_probe.c", "GameGfxV11")

    def test_game_arc_round_rect_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/game_arc_round_rect_probe.c", "GameGfxV12"
        )

    def test_game_map_mode_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/game_map_mode_probe.c", "GameGfxV13"
        )

    def test_game_coordinate_transform_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/game_coordinate_transform_probe.c", "GameGfxV14"
        )

    def test_game_clip_select_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/game_clip_select_probe.c", "GameGfxV15"
        )

    def test_game_clip_exclude_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/game_clip_exclude_probe.c", "GameGfxV16"
        )

    def test_game_clip_union_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/game_clip_union_probe.c", "GameGfxV17"
        )

    def test_game_clip_intersect_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/game_clip_intersect_probe.c", "GameGfxV18"
        )

    def test_game_double_buffer_sprite_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/game_double_buffer_sprite_probe.c", "GameGfxV19"
        )

    def test_game_color_key_sprite_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/game_color_key_sprite_probe.c", "GameGfxV20"
        )

    def test_game_dirty_rect_sprite_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/game_dirty_rect_sprite_probe.c", "GameGfxV21"
        )

    def test_showcase_stage_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/showcase_stage_probe.c", "StageProbe", ("reverse",)
        )

    def test_file_selector_probe_builds(self) -> None:
        self.build_and_validate(
            "reverse/examples/file_selector_probe.c", "FileSel", ("reverse",)
        )

    def test_confirm_dialog_example_builds(self) -> None:
        self.build_and_validate(
            "example/system/confirm_dialog/confirm_dialog_probe.c", "Confirm"
        )

    def test_three_button_dialog_example_builds(self) -> None:
        self.build_and_validate(
            "example/system/three_button_dialog/three_button_dialog_demo.c",
            "ThreeDialog",
        )

    def test_public_file_selector_example_builds(self) -> None:
        self.build_and_validate(
            "example/system/file_selector/file_selector_demo.c", "FileSelect"
        )

    def test_help_page_example_builds(self) -> None:
        self.build_and_validate(
            "example/system/help_page/help_page_demo.c", "HelpPage"
        )

    def test_minesweeper_example_builds(self) -> None:
        self.build_and_validate(
            "example/games/minesweeper/minesweeper_bda.c",
            "Mines",
            category=4,
            icon_png="example/games/minesweeper/minesweeper_icon.png",
        )
        source = Path("example/games/minesweeper/minesweeper_bda.c").read_text(
            encoding="utf-8"
        )
        self.assertIn("#define BOARD_WIDTH 9", source)
        self.assertIn("bda_gui_compatible_context_create", source)
        self.assertIn("bda_gui_compatible_context_free", source)
        self.assertIn("bda_gui_end_draw", source)
        self.assertIn("DRAW ACQUIRES=", source)
        self.assertIn("DRAW RELEASES=", source)
        self.assertIn("g_draw_acquires != g_draw_releases", source)
        self.assertIn("DRAW CONTEXT LEAK", source)
        self.assertIn("bda_gui_context_copy", source)
        self.assertIn("bda_gui_tick_count_25ms", source)
        self.assertIn("BDA_MSG_TOUCH_RELEASE", source)
        self.assertNotIn("_like", source)
        self.assertNotIn("_LIKE", source)
        self.assertNotIn("0x81c0fdb8", source.lower())
        self.assertNotIn("draw_object_create_like(15)", source)

    def test_public_window_examples_release_fixed_draw_slots(self) -> None:
        sources = [
            "example/games/minesweeper/minesweeper_bda.c",
            "example/graphics/primitives/graphics_primitives_demo.c",
            "example/graphics/picture_render/picture_render_demo.c",
            "example/input/touch_crosshair/touch_crosshair_demo.c",
        ]
        for path in sources:
            source = Path(path).read_text(encoding="utf-8")
            self.assertIn("acquire_draw_context", source, path)
            self.assertIn("release_draw_context", source, path)
            self.assertIn("bda_gui_end_draw(draw);", source, path)
            self.assertIn("BDA_MSG_DRAW_CONTEXT_DETACH", source, path)

    def test_no_template_build_includes_bss_zero_fill(self) -> None:
        source = self.out_dir / "bss_probe.c"
        output = self.out_dir / "BssProbe.bda"
        source.write_text(
            """
#include "bda_sdk.h"

static u8 g_scratch[1024];

__attribute__((section(".text.bda_main")))
int bda_main(void) {
    g_scratch[1023] = 7;
    return g_scratch[0];
}
""".lstrip(),
            encoding="ascii",
        )

        output_text = subprocess.check_output(
            [
                sys.executable,
                "reverse/bda_compile_c.py",
                str(source),
                "--prefix",
                self.prefix,
                "--title",
                "BssProbe",
                "--category",
                "9",
                "-o",
                str(output),
            ],
            text=True,
            encoding="utf-8",
        )
        self.assertIn("runtime_file_base=0x81bf6a28", output_text)

        report = validate_bda(output)
        self.assertTrue(report["ok"], report)
        self.assertGreaterEqual(output.stat().st_size, 0x95F8 + 1024)

    def test_call5_wrapper_places_fifth_argument_on_stack(self) -> None:
        source = self.out_dir / "call5_probe.c"
        output = self.out_dir / "Call5Probe.bda"
        source.write_text(
            """
#include "bda_research_sdk.h"

static u16 g_buf[4];

__attribute__((section(".text.bda_main")))
int bda_main(void) {
    return bda_gui_blit_like(1, 2, 3, 4, g_buf);
}
""".lstrip(),
            encoding="ascii",
        )

        subprocess.check_call(
            [
                sys.executable,
                "reverse/bda_compile_c.py",
                str(source),
                "--prefix",
                self.prefix,
                "--title",
                "Call5",
                "--category",
                "9",
                "-I",
                "reverse",
                "-o",
                str(output),
            ]
        )
        disasm = subprocess.check_output(
            [
                sys.executable,
                "reverse/bda_disasm_preview.py",
                str(output),
                "--offset",
                "0x95f8",
                "--base",
                "0x81bf6a28",
                "--count",
                "40",
            ],
            text=True,
            encoding="utf-8",
        )

        self.assertRegex(disasm, r"sw\s+\$[a-z0-9]+,\s+0x10\(\$sp\)")
        self.assertIn("lw       $v0, 0x3f8", disasm)
        self.assertIn("addiu    $a3, $zero, 4", disasm)
        self.assertIn("addiu    $a2, $zero, 3", disasm)
        self.assertIn("addiu    $a1, $zero, 2", disasm)
        self.assertIn("addiu    $a0, $zero, 1", disasm)


if __name__ == "__main__":
    unittest.main()
