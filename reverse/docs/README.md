# BDA 逆向研究文档

本目录保存静态推断、候选 ABI、探针进度和未完成验证的开发笔记，不属于公开 SDK。
开发者应优先阅读 [`docs/`](../../docs/README.md) 和已验证示例
[`example/`](../../example/README.md)。

以下内容是原生 BDA C SDK 的研究参考，带 `_like` 或 `_LIKE` 的名称均可能调整。

触摸固定地址失败边界见 [`touch_press_fixed_va_failure.md`](touch_press_fixed_va_failure.md)；
真机已证明该地址不能作为公开 pressed-state API。

本目录面向 BBK 9588 原生 `*.bda` 应用开发。这里的接口不是 BB 虚拟机 API，
而是原机 BDA 直接调用的 MIPS native runtime table。

文档和注释默认用中文说明行为、证据和风险；常用开发词保留英文，开发者日常使用的英文不硬翻译。
例如 `SDK`、`API`、`header`、`toolchain`、`wrapper`、`helper`、`handle`、
`context`、`callback`、`message`、`object`、`window`、`control`、`offset`、
`entry`、`table`、`buffer`、`frame`、`surface`、`selector`、`getter`、
`smoke test`、`checksum` 都保留英文。命令行输出里的 `output=`、`size=`、
`checksum_ok=` 等字段也保持英文，方便脚本读取和 issue 里直接复制。

## Entry Function

应用需要定义一个 freestanding C 函数 `bda_main`：

```c
#include "bda_sdk.h"

__attribute__((section(".text.bda_main")))
int bda_main(void) {
    bda_msgbox("BDA SDK", "hello");
    return 0;
}
```

仓库自带的 `python -m bda_packer` 默认把稳定目录 `sdk\include` 加入 C include
搜索路径。只有受控逆向 probe 才显式传入 `-I reverse` 使用研究 header。

## 快速闭环

第一次使用先检查/安装本地 MIPS little-endian toolchain：

```powershell
.\scripts\setup_toolchain.ps1
```

从 C 源码直接构建 standalone BDA：

```powershell
python -m bda_packer example\basic\hello_world\hello_world_msgbox.c `
  --title HelloWorld `
  --category 9 `
  --icon-png path\to\icon.png `
  -o build\HelloWorld.bda
```

validate BDA header、entry offset、checksum 和四个 VX icon block：

```powershell
python -m bda_packer.validate build\HelloWorld.bda
```

修改 SDK、toolchain 或文档后，跑完整 smoke：

```powershell
.\scripts\verify_sdk.ps1 -SkipToolchainSetup
```

需要同时启动 emu 前端 smoke 时使用：

```powershell
.\scripts\verify_sdk.ps1 -SkipToolchainSetup -Emu
```

`verify_sdk.ps1` 会重新生成 API 覆盖表和 C200 API 表，运行 unit tests，编译
SDK C 示例并 validate `RectDemo.bda`。`-Emu` 只运行原版 NAND 的 frontend smoke，
不会制作 NAND 镜像。BDA 动态验证必须通过 frontend 文件 API 写入其持久 worker copy。
本地存在 `系统\数据\C200.bin` 时，C200 API 表生成失败会让 verify 失败。

注意：不要把 `Config.inf` 当成 BDA app 的有效注册机制。当前真机反馈显示它对
BDA 启动没有指导意义，也与内置 BDA 的扫描、category 分类、展示和菜单索引无关；
SDK 文档只把它作为历史 reverse 工具的分析对象，不再作为开发者安装 BDA 的推荐路径。

打包器只支持 standalone C，不接受既有 BDA，也没有 template、patch main 或
passthrough 模式。它会从输入 PNG 生成四个 VX menu icon；省略 `--icon-png` 时使用
内置诊断图标。`.bss` 会合并为最终 BDA 里的零填充数据。不要改回 ELF NOBITS
语义；C200 当前生成物没有可靠的 loader-side `.bss` 清零路径，未打包 `.bss` 会让
global 写到文件末尾之外，典型症状是 `GUI+0x084` 注册 frame 失败。

## Public Wrapper 快览

普通应用可以使用聚合 `sdk/include/bda_sdk.h`，也可以按需包含 `bda_memory.h`、
`bda_filesystem.h`、`bda_input.h`、`bda_time.h`、`bda_window.h`、`bda_graphics.h`、
`bda_dialogs.h`、`bda_controls.h` 和 `bda_audio.h`。游戏绘制新公开的核心接口是：

```c
bda_handle_t bda_gui_compatible_context_create(bda_handle_t source_context);
void bda_gui_compatible_context_free(bda_handle_t context);
int bda_gui_draw_vx(bda_handle_t context, s32 x, s32 y, const void *vx_resource);
int bda_gui_context_copy(
    bda_handle_t source, s32 sx, s32 sy, s32 width, s32 height,
    bda_handle_t destination, s32 dx, s32 dy, u32 color_key_rgb565
);
u32 bda_gui_tick_count_25ms(void);
u32 bda_gui_tick_elapsed_25ms(u32 start, u32 end);
u32 bda_gui_tick_elapsed_ms(u32 start, u32 end);
```

完整双缓冲、精灵、dirty rect 和生命周期教程见
`verified/game_rendering_api.md`。

下面的综合清单还包含 `reverse/bda_research_sdk.h` 中的逆向候选；带 `_like` 的名称不属于
公开 SDK，普通应用不要依赖：

```c
int bda_msgbox(const char *title, const char *message);
int bda_msgbox_ex(void *parent, const char *title, const char *message, u32 flags);
int bda_confirm(const char *title, const char *message);
int bda_confirm_yes_all_no(const char *title, const char *message);
int bda_help_page(void *parent, const char *title, const char *body);
#define BDA_MSGBOX_TYPE_OK          0u
#define BDA_MSGBOX_TYPE_YES_NO      2u
#define BDA_MSGBOX_TYPE_YES_ALL_NO  6u
#define BDA_DIALOG_RESULT_YES       6
#define BDA_DIALOG_RESULT_NO        7
#define BDA_DIALOG_RESULT_ALL       10
#define BDA_GUI_HELP_PAGE_LIKE      0x5a8u
int bda_gui_help_page_like(void *parent, const char *document);
void *bda_alloc(bda_size_t size);
void bda_free(void *ptr);
void *bda_track_alloc_like(bda_size_t size);
void bda_track_free_like(void *ptr);
void bda_mem_track_begin_like(u32 free_on_finish);
int bda_mem_track_report_like(u32 summary_only);
void bda_mem_track_finish_like(void);
void *bda_mem_track_retain_like(void *ptr);
void bda_mem_track_release_like(void *ptr);
void *bda_calloc_like(bda_size_t count, bda_size_t size);
void *bda_realloc_like(void *ptr, bda_size_t new_size);
void *bda_memcpy(void *dst, const void *src, bda_size_t n);
void *bda_memset(void *dst, int value, bda_size_t n);
bda_size_t bda_strlen(const char *s);
```

从原机应用调用点和 C200 切片整理出的 wrapper：

```c
int bda_gui_send(bda_handle_t handle, u32 message, u32 a, u32 b);
int bda_gui_notify_like(bda_handle_t handle, u32 message, u32 a, u32 b);
int bda_gui_destroy_like(bda_handle_t handle);
bda_handle_t bda_gui_create_window_like(
    const char *class_name,
    const char *caption,
    u32 style,
    u32 flags,
    u32 id,
    s32 x,
    s32 y,
    s32 width,
    s32 height,
    bda_handle_t parent,
    u32 extra
);
int bda_gui_blit_like(s32 x, s32 y, s32 height, s32 width, const void *buffer);
int bda_gui_blit_alt_like(s32 x, s32 y, s32 height, s32 width, const void *buffer);
int bda_gui_set_text_mode_like(bda_handle_t handle, u32 mode);
int bda_gui_rgb_like(bda_handle_t handle, u32 r, u32 g, u32 b);
int bda_gui_set_text_color_like(bda_handle_t handle, u32 color);
int bda_gui_put_pixel_like(bda_handle_t context, s32 x, s32 y, u32 color);
int bda_gui_draw_text_like(bda_handle_t handle, s32 x, s32 y, const char *text, s32 extra);
int bda_gui_draw_vx_like(bda_handle_t handle, s32 x, s32 y, const void *vx_resource);
int bda_gui_pump_present_arg_like(u32 draw_guard_enabled);
int bda_gui_draw_guard_begin_like(void);
int bda_gui_draw_guard_end_like(void);
bda_handle_t bda_gui_register_frame_desc_like(bda_frame_desc_like_t *descriptor);
int bda_gui_register_frame_like(void *descriptor);
int bda_gui_event_poll_global_like(bda_gui_message_like_t *message);
int bda_gui_event_pump_frame_once_like(bda_gui_message_like_t *message, bda_handle_t frame);
int bda_gui_event_poll_like(bda_gui_message_like_t *message, bda_handle_t handle);
int bda_gui_event_step_like(bda_gui_message_like_t *message);
int bda_gui_event_dispatch_like(bda_gui_message_like_t *message);
int bda_gui_object_rect_like(bda_handle_t handle, bda_rect_like_t *rect);
void bda_gui_rect_prepare_like(bda_rect_like_t *rect, s32 x0, s32 y0, s32 x1, s32 y1);
int bda_gui_rect_contains_like(const bda_rect_like_t *rect, s32 x, s32 y);
void bda_gui_accumulate_origin_like(bda_handle_t handle, s32 *x, s32 *y);
void bda_gui_subtract_origin_like(bda_handle_t handle, s32 *x, s32 *y);
u32 bda_gui_object_flags_get_like(bda_handle_t handle);
int bda_gui_object_flags_or_like(bda_handle_t handle, u32 mask);
int bda_gui_object_flags_clear_like(bda_handle_t handle, u32 mask);
u32 bda_gui_object_userdata0_get_like(bda_handle_t handle);
u32 bda_gui_object_userdata0_set_like(bda_handle_t handle, u32 value);
u32 bda_gui_object_userdata1_get_like(bda_handle_t handle);
u32 bda_gui_object_userdata1_set_like(bda_handle_t handle, u32 value);
u32 bda_gui_object_payload_word_get_like(bda_handle_t handle);
u32 bda_gui_object_payload_word_set_like(bda_handle_t handle, u32 value);
void *bda_gui_object_resource_ptr_get_like(bda_handle_t handle);
void *bda_gui_object_callback_ptr_get_like(bda_handle_t handle);
void *bda_gui_object_callback_ptr_set_like(bda_handle_t handle, void *value);
int bda_gui_object_op_like(bda_handle_t object);
bda_handle_t bda_gui_object_draw_begin_like(bda_handle_t handle);
void bda_gui_object_draw_end_like(bda_handle_t handle, bda_handle_t draw_handle);
int bda_gui_active_frame_set_like(bda_handle_t handle);
bda_handle_t bda_gui_active_child_get_like(bda_handle_t context);
int bda_gui_window_timer_start_like(bda_handle_t frame, u32 timer_id, u32 period_ms);
int bda_gui_window_timer_stop_like(bda_handle_t frame, u32 timer_id);
int bda_gui_window_timer_exists_like(bda_handle_t frame, u32 timer_id);
int bda_gui_window_timer_set_period_like(bda_handle_t frame, u32 timer_id, u32 period_ms);
u32 bda_gui_window_timer_clock_ms_like(void);
#define BDA_MSG_WINDOW_TIMER_LIKE 0x0144u
int bda_gui_object_bind_like(u32 context, u32 value);
void bda_gui_surface_flush_like(bda_handle_t context);
void *bda_gui_capture_region_alloc_like(s32 x, s32 y, s32 width, s32 height);
int bda_gui_set_fill_color_like(bda_handle_t handle, u32 color);
int bda_gui_input_packet_like(bda_gui_input_packet_like_t *packet);
void *bda_gui_screen_buffer_like(void);
void bda_gui_touch_position_like(u16 *x, u16 *y);
int bda_gui_state_query_like(void);
int bda_gui_screen_orientation_like(void);
int bda_touch_pressed_9588(void); /* 危险固定地址失败探针，禁止真机调用 */
int bda_gui_event_fetch_like(bda_gui_event_fetch_like_t *out_event);
int bda_gui_file_selector_update_like(bda_file_selector_like_t *selector);
void *bda_gui_list_nth_like(void *head, s32 index);
void bda_gui_list_free_like(void *head);
int bda_gui_decode_bmp_like(void *owner, bda_picture_like_t *out, const char *path, void **out_source_buffer);
int bda_gui_decode_jpeg_like(void *owner, bda_picture_like_t *out, const char *path, u32 mode);

int bda_res_entry_094_like(const char *text_or_path, void *arg);
int bda_res_trace_like(const char *format, void *arg);
void bda_res_get_state_like(bda_res_state_like_t *out_state);

int bda_fs_fopen_raw(const char *path, const char *mode);
int bda_fs_file_is_valid(int file);
int bda_fs_close_raw(int file);
int bda_fs_fread_raw(void *buffer, bda_size_t size, bda_size_t count, int file);
int bda_fs_read_raw(int file, void *buffer, bda_size_t size);
int bda_fs_fwrite_raw(const void *buffer, bda_size_t size, bda_size_t count, int file);
int bda_fs_write_raw(int file, const void *buffer, bda_size_t size);
int bda_fs_seek_raw(int file, s32 offset, int whence);
int bda_fs_tell_raw(int file);
int bda_fs_eof_like(int file);
int bda_fs_error_like(int file);
int bda_fs_clear_error_like(int file);
int bda_fs_remove_raw(const char *path);
int bda_fs_rename_like(const char *old_path, const char *new_path);
int bda_fs_chdir_like(const char *path);
int bda_fs_mkdir_like(const char *path);
int bda_fs_rmdir_like(const char *path);
void bda_fs_find_data_init_like(bda_fs_find_data_like_t *find_data);
int bda_fs_findfirst_like(const char *pattern, u32 attr, bda_fs_find_data_like_t *find_data);
int bda_fs_findnext_like(bda_fs_find_data_like_t *find_data);
int bda_fs_findclose_like(bda_fs_find_data_like_t *find_data);
int bda_fs_diskinfo_like(u32 drive, bda_fs_disk_info_like_t *info);
u32 bda_fs_disk_free_bytes_like(const bda_fs_disk_info_like_t *info);
u64 bda_fs_disk_free_bytes64_like(const bda_fs_disk_info_like_t *info);
int bda_fs_getcwd_like(char *buffer, bda_size_t size);
void bda_fs_path_info_init_like(bda_fs_path_info_like_t *info);
int bda_fs_path_info_like(const char *path, bda_fs_path_info_like_t *info);
int bda_fs_path_info_is_dir_like(const bda_fs_path_info_like_t *info);
u32 bda_fs_path_info_size_like(const bda_fs_path_info_like_t *info);
int bda_fs_stat_like(const char *path, u32 flags);
int bda_fs_media_present_raw_like(void);
int bda_fs_storage_ready_like(void);
void bda_fs_flush_all(void);

void *bda_sys_table(void);
int bda_sys_session_open_like(bda_sys_session_desc_like_t *descriptor);
int bda_sys_session_close_like(u32 session_id);
int bda_sys_session_init_word_like(u32 session_id, const u32 *word);
int bda_sys_session_stop_like(u32 session_id);
int bda_sys_session_status_like(u32 session_id, bda_sys_session_status_like_t *status);
u32 bda_c200_record_open_address_like(void);
u32 bda_c200_record_ready_address_like(void);
u32 bda_c200_record_read_address_like(void);
int bda_c200_record_stream_supported_like(void);
void bda_c200_record_stream_open_like(u32 sample_rate, u32 bits_per_sample, u32 channels);
int bda_c200_record_stream_ready_like(void);
int bda_c200_record_stream_read_like(void *buffer, bda_size_t bytes);
void bda_c200_record_stream_stop_like(void);
void bda_sys_audio_open_like(u32 device, u32 format, u32 channels);
int bda_sys_audio_ready_like(void);
int bda_sys_audio_write_like(const void *buffer, bda_size_t bytes);
int bda_sys_keycode_raw_like(void);
void bda_sys_audio_reset_like(void);
void *bda_sys_audio_state_like(void);
void bda_sys_audio_flush_like(void);
void bda_sys_audio_attenuation_set_like(s32 attenuation);
int bda_sys_audio_attenuation_get_like(void);
int bda_sys_package_sound_op58_like(const void *descriptor);
int bda_sys_package_sound_op5c_like(u32 slot, const void *descriptor, u32 a2, u32 flags);
int bda_sys_package_sound_op60_like(void);
int bda_sys_package_sound_op64_like(void);
int bda_sys_package_sound_op68_like(void);
void bda_sys_delay_like(u32 delay_units);
void bda_sys_timer_like(u32 preset_index);
int bda_sys_alarm_due_get_like(bda_sys_alarm_record_like_t *out_alarm_data);
int bda_sys_alarm_set_like(bda_sys_alarm_record_like_t *alarm_data, u32 slot);
int bda_sys_alarm_get_like(bda_sys_alarm_record_like_t *alarm_data, u32 slot);
void bda_sys_alarm_record_init_like(bda_sys_alarm_record_like_t *record);
int bda_sys_alarm_slot_confirmed_like(u32 slot);
u32 bda_sys_alarm_record_file_offset_like(u32 slot);
u32 bda_sys_alarm_record_slot_tag_like(const bda_sys_alarm_record_like_t *record);
int bda_sys_alarm_due_miss_like(const bda_sys_alarm_record_like_t *record);
u8 bda_sys_alarm_record_enable_flag_like(const bda_sys_alarm_record_like_t *record);
```

录音相关 raw session ABI 只在研究头中提供：

```text
BDA_SYS_SESSION_OPEN_LIKE
BDA_SYS_CLOSE_LIKE
BDA_SYS_SESSION_INIT_WORD_LIKE
BDA_SYS_SESSION_OP18_LIKE
BDA_SYS_SESSION_OP1C_LIKE
BDA_SYS_SESSION_STOP_LIKE
BDA_SYS_SESSION_STATUS_LIKE
BDA_SYS_SESSION_RECORD_TYPE_LIKE
BDA_SYS_SESSION_RECORD_FLAGS_LIKE
BDA_C200_RECORD_OPEN_FROM_AUDIO_OPEN_DELTA_LIKE
BDA_C200_RECORD_READY_FROM_AUDIO_READY_DELTA_LIKE
BDA_C200_RECORD_READ_BEFORE_AUDIO_WRITE_DELTA_LIKE
BDA_C200_RECORD_OPEN_SIGNATURE0_LIKE
BDA_C200_RECORD_OPEN_SIGNATURE1_LIKE
BDA_C200_RECORD_READY_SIGNATURE0_LIKE
BDA_C200_RECORD_READY_SIGNATURE1_LIKE
BDA_C200_RECORD_READ_SIGNATURE0_LIKE
BDA_C200_RECORD_READ_SIGNATURE1_LIKE
```

`bda_sys_session_desc_like` / `bda_sys_session_desc_like_t` 是 24-byte descriptor；
已确认字段为 `type`、`flags`、`path`、`parameter_0c`、`callback`、`user_data`。
`bda_sys_session_status_like` / `bda_sys_session_status_like_t` 保留 8 个未命名 word。
type-5 录音 session 的保守生命周期是 open、init word、可选 status query、
stop-like、close。close 负责写回最终 WAV header，不能省略。callback 事件码、
`parameter_0c` 的业务名称和 status word 单位仍未真机确认，因此这些类型和 wrapper
不属于公开 SDK。

`bda_c200_record_stream_*_like()` 是更低层的 firmware-private PCM capture 实验
wrapper。它们从 SYS raw playback function address 加减已交叉验证的 delta，且
在调用前检查 MIPS prologue。支持的原厂调用形状是 16000-Hz、16-bit、mono，
每次阻塞读取 0x1000 byte；普通应用不得在签名检查失败后调用，也不得把 read
直接放在 GUI wndproc 中。

`bda_sys_alarm_record_like_t` 是 `0x2b8` byte。`alarm_due_get` 会向调用者
buffer 复制整条 record，不能传 short buffer。C200 的 alarm get/set 只确认了
原机 slot 0/1/2，当前函数切片未见 slot bounds check。alarm helper 只覆盖
`record+0x00` slot tag、`record+0x10` enable flag、due miss tag 和
`0x578 + slot * 0x2b8` 持久化 offset 这些已确认字段；不要把 raw record 当成
完整结构体使用。

`bda_sys_audio_attenuation_set_like()` / `get_like()` 已由 `GameVolV1` 确认为 raw
PCM attenuation；公开稳定名称位于 `sdk/include/bda_audio.h`。`op58_like()` 到
`op68_like()` 才是按 offset 命名的 low-level package sound wrapper，只用于复刻
原机游戏调用形状；descriptor/slot layout 仍需 probe，不要当成 stable high-level
sound API。

已删除的历史 misnames：

```text
bda_load_dlx_ex / bda_load_dlx / bda_load_dlx_gui / bda_load_dlx_fs
bda_load_dlx_mem / bda_load_dlx_res / bda_file_selector_load_default_skin_like
bda_gui_create_ex / BDA_MSG_TOUCH_B_LIKE
```

这些旧名字分别来自误判的 `RES+0x094`、no-op 或不准确的早期 probe 命名。新代码
应使用 FS 读取 DLX/resource data，使用 `bda_gui_create_window_like()` 创建 control，
使用 `BDA_MSG_REDRAW_INPUT_LIKE` 表示 `0x00b1` 输入/重绘触发。file selector color
修正来自 `bda_file_selector_init_like()` 的完整结构体初始化。

`BDA_RES_TRACE_LIKE` 是 `BDA_RES_ENTRY_094_LIKE` 的 alias，用于强调该 entry
目前按 trace/printf-like 使用，不再按 DLX loader 命名。

用于 low-level probe 或复刻原机调用形状的 table call：

```c
BDA_RUNTIME_BASE;
BDA_GUI_TABLE_ADDR;
BDA_FS_TABLE_ADDR;
BDA_SYS_TABLE_ADDR;
BDA_MEM_TABLE_ADDR;
BDA_RES_TABLE_ADDR;

int bda_call0(void *table, u32 offset);
int bda_call1(void *table, u32 offset, u32 a0);
int bda_call2(void *table, u32 offset, u32 a0, u32 a1);
int bda_call3(void *table, u32 offset, u32 a0, u32 a1, u32 a2);
int bda_call4(void *table, u32 offset, u32 a0, u32 a1, u32 a2, u32 a3);
int bda_call5(void *table, u32 offset, u32 a0, u32 a1, u32 a2, u32 a3, u32 a4);
int bda_call6(void *table, u32 offset, u32 a0, u32 a1, u32 a2, u32 a3, u32 a4, u32 a5);
```

新代码应优先使用已命名 wrapper。直接调用 `bda_call*()` 前，至少要确认 table、
offset、参数个数、stack 参数和 return value；不要把未知 offset 当成稳定 API。
MIPS o32 只有 `a0..a3` 四个参数寄存器；`bda_call5()` / `bda_call6()` 的第 5/6
参数会按 C ABI 放到 caller stack，用来满足 C200 中读取 `stack+0x10` 等参数的入口。
`BDA_RUNTIME_BASE` 和 `BDA_*_TABLE_ADDR` 是 runtime table pointer slot 地址，
不是 function offset；普通应用通常不需要直接使用。

## Wrapper 使用边界

当前 SDK wrapper 分三类看待：

```text
低风险 smoke:
  bda_gui_screen_orientation_like()
  bda_gui_rect_prepare_like()
  bda_gui_rect_contains_like()
  bda_alloc()/bda_free()
  只读 FS helper，例如 open/read/seek/tell/close/read_raw

需要真实 lifecycle:
  bda_gui_register_frame_like()
  bda_gui_event_poll_like()/bda_gui_event_dispatch_like()
  bda_gui_begin_draw_like()/bda_gui_end_draw_like()
  bda_gui_draw_object_create_like()
  text/image/control draw 相关 wrapper

破坏性或全局状态:
  bda_fs_write_raw()/bda_fs_fwrite_raw()
  bda_fs_remove_raw()/bda_fs_mkdir_like()/bda_fs_rmdir_like()
  alarm/audio/storage 状态修改类 probe
```

“需要真实 lifecycle” 的意思是：调用者已经有原机认可的 frame/window/control
handle、wndproc、message loop 和 close 路径。`register_frame` 只负责把 descriptor
交给 C200，它不是“一次调用显示 UI”的 high-level API；
`bda_gui_draw_object_create_like(15)` 也只是查询 low-level object/surface，不能单独证明
绘图上下文已经准备好。硬编码替换
`应用\程序\时间.bda` 的入口尤其不能当作普通 GUI app bootstrap：这个路径只适合
header/loader smoke，不适合直接验证 frame/window/draw API。

坐标/rect helper 示例：

```powershell
python -m bda_packer reverse\examples\gui_rect_contains_demo.c `
  --title RectDemo `
  --category 9 `
  -I reverse `
  -o build\RectDemo.bda

python -m bda_packer.validate build\RectDemo.bda
```

`bda_gui_rect_prepare_like()` 和 `bda_gui_rect_contains_like()` 不需要真实 window
handle，适合做 SDK smoke test。
`bda_gui_accumulate_origin_like()` 和 object draw/update 相关 wrapper 需要原机
window/control handle，应放在真实 frame/control 生命周期中使用。
`bda_gui_surface_flush_like()` 和 `bda_gui_set_fill_color_like()` 来自画板/BBVM
路径，也需要真实 draw context；flush 会释放 context，不要继续复用同一个 handle，
也不要在 bare `bda_main()` 中传 `0` 做 probe。
framebuffer/tile 游戏不能直接套用 `bda_gui_blit_like()` / `bda_gui_blit_alt_like()`
做独立绘图。旧扫雷把 present 放在 tile 循环里会逐块 flip；`TileBlit` 后续真机
结果又确认，即使只在循环外统一 `draw_guard_end_like()`，仍会逐块 flip 并在全部 tile
渲染后死机。当前结论是 `GUI+0x074/+0x400` 依赖原机游戏的 surface/context 生命周期，
SDK 暂不把它作为可玩 tile 游戏绘图接口。
`bda_gui_screen_orientation_like()` 是很适合 standalone 的 smoke：C200 当前直接返回
`0x130`，研究示例 `reverse\examples\gui_screen_orientation_demo.c` 会用 message box 显示结果。

```powershell
python -m bda_packer reverse\examples\gui_screen_orientation_demo.c `
  --title OrientDemo `
  --category 9 `
  -I reverse `
  -o build\OrientDemo.bda
```

file read 示例：

```powershell
python -m bda_packer reverse\examples\fs_read_demo.c `
  --title FsRead `
  --category 9 `
  -I reverse `
  -o build\FsRead.bda

python -m bda_packer.validate build\FsRead.bda
```

`fs_read_demo.c` 会尝试读取 `A:\gba\gba.cfg` 或 `a:\gba\gba.cfg`，演示
`bda_fs_file_is_valid(fd)` 句柄判断、`seek/tell` 获取大小、`fread` 读取和 `close` 收尾。
`reverse/examples/fs_read_raw_demo.c` 则只演示便捷 wrapper
`bda_fs_read_raw(file, buffer, size)`；注意它的参数顺序不是
`fread(buffer, size, count, file)`。
示例故意使用 ASCII 路径；访问 `A:\应用\...` 这类中文路径时，应像现有
path matrix probe 一样使用 GBK byte string，不要依赖编译器源文件编码。

`fs_write_demo.c` 会在 `A:\应用\数据\游戏` 下写入固定 19 byte payload，随后
`tell`、关闭、重开、读回并逐字节比较。模拟器 worker NAND 已验证 `A:` 路径和根相对路径
都得到 `write=19,tell=19,error=0,read=19,match=1`。

filesystem raw wrapper 保持保守命名，直到 struct layout 和 return value 细节在真机上确认。
当前 directory enumeration 应优先使用 `findfirst/findnext/findclose` 这一组；`find_data`
必须按 `bda_fs_find_data_like_t` 大小分配并先清零，不要使用 512 byte 临时 buffer。
`reverse/examples/fs_find_demo.c` 是最小 findfirst/findclose 示例，只显示 return value
和结构开头字节，不把某个 pattern 的成功视为跨固件保证。

## Verify 覆盖的 SDK 示例

`reverse.test_sdk_examples` 会编译并 validate standalone 示例。开发者应从根目录
`example/` 中已经动态验证的程序开始，完整入口见
[`example/README.md`](../../example/README.md)：

```text
example/basic/hello_world/hello_world_msgbox.c        最小 verified message box
example/filesystem/fs_write/fs_write_demo.c              已验证的写入、关闭、重开和读回闭环
example/filesystem/fs_flush/fs_flush_power_demo.c       已验证的全局 flush 强制断电 A/B 对照
example/filesystem/file_management/file_management_demo.c  已验证的文件增删改查、属性与容量闭环
example/input/key_polling/key_msgbox_demo.c            已验证的六键 packet 轮询
example/input/touch_crosshair/touch_crosshair_demo.c       真机 V23 两阶段绘制的无闪烁触摸定位测试
example/graphics/primitives/graphics_primitives_demo.c   已验证的 frame 图元和彩色像素绘制
example/graphics/picture_render/picture_render_demo.c    已验证的原生尺寸 raw RGB565 动态提交
example/graphics/direct_framebuffer/direct_framebuffer_demo.c 已验证的 C200 240x320 RGB565 整帧直接提交
example/games/minesweeper/minesweeper_bda.c            娱乐天地分类的 9x9 可玩扫雷
example/system/runtime_services/runtime_services_demo.c  已验证的 heap、seek、目录和枚举闭环
example/system/high_resolution_timer/high_resolution_timer_demo.c  已验证的标称 1 ms timer 生命周期
example/system/hardware_detection/hardware_detection_demo.c  真机验证的 9588/9688 与 JZ47xx 只读识别
example/system/file_selector/file_selector_demo.c       已验证的系统模态文件选择器
example/system/confirm_dialog/confirm_dialog_probe.c     已验证的是/否确认框及返回值
example/system/three_button_dialog/three_button_dialog_demo.c  已验证的是/全部/否确认框及返回值
example/system/help_page/help_page_demo.c             已验证的系统同步帮助页和返回链
example/system/audio_pcm/audio_pcm_demo.c                已验证的 raw PCM open/write/attenuation/stop 闭环
example/system/audio_capture/audio_capture_demo.c        C200knl profile 保护的实时 PCM 录音与波形示例
example/gui/control_gallery/control_gallery_demo.c      已验证的内建控件和消息 helper
example/gui/custom_control/custom_control_demo.c         已验证的自定义类、局部绘制和注销
example/gui/gif_player/gif_player_demo.c                 已验证的内存 GIF89a 自动播放和销毁
```

未达到公开标准的 ABI/build smoke 和动态研究 probe 统一放在 `reverse/examples/`，其中
包括：

```text
reverse/examples/hello_msgbox.c              兼容的 message box build smoke
reverse/examples/gui_rect_contains_demo.c    rect helper / RectDemo
reverse/examples/gui_screen_orientation_demo.c  standalone 方向查询 smoke
reverse/examples/input_state_demo.c          input packet/event/state 查询
reverse/examples/mem_alloc_demo.c            firmware heap alloc/free
reverse/examples/fs_read_demo.c              file open/read/seek/tell/close
reverse/examples/fs_read_raw_demo.c          read_raw 参数顺序 smoke
reverse/examples/fs_find_demo.c              directory enumeration struct
reverse/examples/fs_diskinfo_demo.c          disk/storage 容量查询
reverse/examples/fs_status_demo.c            storage ready + path stat/access
reverse/examples/res_state_demo.c            RES state snapshot struct
reverse/examples/control_skin_binding_probe.c  已验证的 medit/listbox VX 皮肤绑定和释放闭环
reverse/examples/tile_blit_probe.c           危险的 tile blit ABI/build probe
reverse/examples/time_probe.c                delay/timer/alarm 只读 probe
reverse/examples/game_api_probe.c            MEM/display metric/delay 模拟器动态 probe
reverse/examples/game_audio_probe.c          raw PCM open/ready/write/cleanup 模拟器动态 probe
reverse/examples/game_audio_cleanup_probe.c  raw PCM AIC stop/reopen 模拟器历史 probe
reverse/examples/audio_pcm_hw_stop_probe.c   真机固定 AIC 地址死锁反例 V3
reverse/examples/audio_pcm_hw_finish_probe.c 真机 SYS+0x0a0 安全停止闭环 V4
reverse/examples/game_audio_volume_probe.c   raw PCM attenuation set/get 与幅度动态 probe
reverse/examples/game_graphics_probe.c       window primitives/font/VX sprite 模拟器动态 probe
reverse/examples/game_image_probe.c          VX/BMP decode、descriptor、render 和 cleanup 动态 probe
reverse/examples/game_image_render_probe.c   V5 decoded BMP `GUI+0x410` render 动态 probe
reverse/examples/game_image_compat_probe.c   V6 compatible context + `GUI+0x418` copy 动态 probe
reverse/examples/game_jpeg_probe.c           V7 JPEG mode 0/1 decode、render 和 cleanup 动态 probe
reverse/examples/game_compat_animation_probe.c  V8 repeated compatible draw/copy 动画 probe
reverse/examples/game_tick_probe.c           V9 25 ms raw tick 和回绕算术动态 probe
reverse/examples/high_resolution_timer_probe.c GUI 标称 1 ms timer 生命周期 probe；V4 真机通过，保留 V2/V3 反例
reverse/examples/game_polyline_clip_probe.c  V10 polyline 和只读 clip 查询动态 probe
reverse/examples/game_ellipse_probe.c        V11 ellipse outline/fill 和 draw object 对照 probe
reverse/examples/game_arc_round_rect_probe.c V12 arc 角度和 rounded rectangle outline/fill probe
reverse/examples/game_map_mode_probe.c       V13 viewport/window 逻辑坐标映射与恢复 probe
reverse/examples/game_coordinate_transform_probe.c V14 point logical/device 双向转换 probe
reverse/examples/game_clip_select_probe.c    V15 clip rect select/query/reset probe
reverse/examples/game_clip_exclude_probe.c   V16 clip rect difference/hole probe
reverse/examples/game_clip_union_probe.c     V17 two-island clip region union probe
reverse/examples/game_clip_intersect_probe.c V18 two-island clip region intersect probe
reverse/examples/game_double_buffer_sprite_probe.c V19 two-surface sprite composition probe
reverse/examples/game_color_key_sprite_probe.c V20 RGB565 magenta color-key sprite probe
reverse/examples/game_dirty_rect_sprite_probe.c V21 three-surface dirty-rectangle sprite probe
reverse/examples/gam4980_runtime_api_probe.c  gam4980 heap、seek 和目录正式化准入 probe
reverse/examples/gam4980_picture_api_probe.c  gam4980 raw RGB565 picture 正式化准入 probe
reverse/examples/gameboy_fast_touch_hardware_probe.c  FastTouchV3 真机高速坐标 getter 验证
reverse/examples/gameboy_event_touch_hardware_probe.c GAMEBOY +0x750/+0x6c0 真机事件关联通过；+0x72c 保留研究
reverse/examples/touch_press_fixed_va_probe.c  旧兼容模拟器固定地址失败归档，禁止真机运行
reverse/examples/record_stream_hardware_probe.c  firmware-private 实时 PCM 采集 V1 精确签名探针
reverse/examples/record_stream_hardware_probe_v2.c  V2 结构解析反例；现已拒绝误命中的 playback open
reverse/examples/record_stream_hardware_probe_v3.c  真机旧 open guess 所在函数的只读边界探针
reverse/examples/record_stream_hardware_probe_v4.c  init 候选安全返回但 ready 超时的反例
reverse/examples/record_stream_hardware_probe_v5.c  真机 init/config/ready/read 只读调用图探针
reverse/examples/record_stream_hardware_probe_v6.c  init + 误判为采样率的 gain wrapper 反例
reverse/examples/record_stream_hardware_probe_v7.c  真机 control/worker 全调用图只读探针
reverse/examples/record_stream_hardware_probe_v8.c  修正 read 入口保护的全调用图只读探针
reverse/examples/record_stream_hardware_probe_v9.c  ready 状态写入者与启动候选深度只读探针
reverse/examples/record_stream_hardware_probe_v10.c  状态引用紧凑只读探针
reverse/examples/record_stream_hardware_probe_v11.c  worker 等待原语与采集回调引用只读探针
reverse/examples/record_stream_hardware_probe_v12.c  首次 blocking read 启动 DMA 的真机采集探针
reverse/examples/record_stream_hardware_probe_v13.c  1024-byte 低延迟读取与双周期重启探针
reverse/examples/touch_input_stage_probe_v12.c  最小文本与触摸 lifecycle 回归
reverse/examples/touch_input_stage_probe_v13.c  object draw scope 真机回归
reverse/examples/touch_input_stage_probe_v14.c  compatible context 方向实验
reverse/examples/touch_input_stage_probe_v15.c  compatible context 反向对照
reverse/examples/touch_input_stage_probe_v16.c  白底黑字临时 context 实验
reverse/examples/touch_input_stage_probe_v17.c  跳过旧状态擦除实验
reverse/examples/touch_input_stage_probe_v18.c  记事本短标签无 +0x074 对照
reverse/examples/touch_input_stage_probe_v19.c  wndproc 内 object draw 动态提交实验
reverse/examples/touch_input_stage_probe_v20.c  +0x0e0 请求 0xb1 重绘实验
reverse/examples/touch_input_stage_probe_v21.c  直接 +0x03c(frame,0xb1) 重绘实验
reverse/examples/touch_input_stage_probe_v22.c  object draw 后单独 +0x074(0) 提交
reverse/examples/touch_input_stage_probe_v23.c  真机无闪烁的完整 guard 十字与 5x7 坐标字
reverse/examples/window_text_bbvm_black_probe.c  BBVM 风格 text draw lifecycle probe
reverse/examples/showcase_stage_probe.c      Element 风格 display 回归链路
reverse/examples/file_selector_probe.c       file selector open/update smoke
reverse/examples/file_selector_admission_probe.c  file selector 公开准入闭环
reverse/examples/help_page_probe.c          parent=0 的系统帮助页准入闭环
reverse/examples/help_page_parent_probe.c   注册 Frame parent 的帮助页恢复闭环
```

`minesweeper_bda.c` 已重写为不依赖原机模板或绝对地址的 standalone 9x9 扫雷。
它在 8013 完成首击安全、插旗、重开、失败、获胜、触摸后实体键退出和 back surface
释放闭环；构建、操作和证据见 `minesweeper_v1.md`。compatible surface、25 ms tick
和 VX 绘制链已按模拟器稳定等级进入公开 include，开发教程见
`verified/game_rendering_api.md`；真机状态仍明确标记为待复测。

`game_api_probe.c`、`game_audio_probe.c`、`game_audio_cleanup_probe.c` 和
`game_audio_volume_probe.c` 保留为研究证据，不属于公开稳定示例。raw PCM 的
22050 Hz/16-bit/mono open/write、attenuation set/get，以及绑定当前 C200 的 AIC
stop/reopen 已按模拟器稳定等级进入 `sdk/include/bda_audio.h`；结果、失败
边界和后续真机任务记录在 `game_api_verification_progress.md` 和
`docs/verified/audio_pcm_api.md`。

首个在 BBK 9588 真机上完成“创建窗口、触摸绘图、实体键退出、销毁 frame、返回主菜单”
闭环的 standalone BDA 是 `TouchStageV11.bda`。其 API 清单和强制生命周期顺序见
`docs/verified/touch_window_lifecycle_api.md`。顶层窗口退出必须按
`stop -> release -> event poll 结束 -> close -> bda_main return` 执行。

`reverse/examples` 里其他文件多数是专题 probe 或真机回归实验，使用前先看对应
`docs/*_notes.md` 和 `reverse/reports/*.md` 的风险说明。
`window_text_bbvm_black_probe.c` 和相邻 BBVM text probe 证明
`BDA_MSG_DRAW_CONTEXT_ATTACH_LIKE` (`0x60`) 中取得 draw context、`0x66` 中清理的
路径可以显示文本；它们仍依赖 `style=0x08000000`、
`bda_gui_draw_object_create_like(15)` 和完整 event loop，属于 frame/control lifecycle 回归 probe，
不是 standalone SDK starter。
`tile_blit_probe.c` 是已经失败归档的 framebuffer hardware probe：它在一次
draw guard 内批量 blit 8x6 个 16x16 RGB565 tile，再统一 present。真机反馈显示
这仍会逐块 flip，并在全部 tile 渲染后死机。它证明 `GUI+0x074/+0x400` 不能脱离
原机游戏 surface/context 直接作为游戏 SDK 示例；它不代表 frame/window lifecycle
已经完整，也不应作为第一个 smoke。

输入和事件辅助：

```c
typedef int (*bda_wndproc_t)(bda_handle_t hwnd, u32 message, u32 wparam, u32 lparam);
typedef struct bda_gui_message_like bda_gui_message_like_t;
BDA_LOWORD(x);
BDA_HIWORD(x);
BDA_MAKEWORD(lo, hi);
bda_gui_input_packet_key_pressed_like(packet, keycode);
bda_gui_key_pressed_like(keycode);
BDA_KEY_UP; BDA_KEY_DOWN; BDA_KEY_LEFT; BDA_KEY_RIGHT;
BDA_KEY_ENTER; BDA_KEY_ESCAPE;
BDA_INPUT_PACKET_UP_INDEX; BDA_INPUT_PACKET_DOWN_INDEX;
BDA_INPUT_PACKET_LEFT_INDEX; BDA_INPUT_PACKET_RIGHT_INDEX;
BDA_INPUT_PACKET_ENTER_INDEX; BDA_INPUT_PACKET_ESCAPE_INDEX;
```

开发者 docs entry：`bda_header_notes.md` 记录当前原生 BDA header 构造规则；
`api_catalog.md` 是从原机 BDA 清点和 SDK header 生成的 API 覆盖表；
`api_offsets.md` 是手写 offset/API 速查索引；
`system_api_tables.md` 是从 `C200.bin` 读取出的 API 表函数地址；
`system_bin_notes.md` 记录 `C200.bin`、runtime table 和硬件线索；
`c200_api_function_notes.md` 记录若干关键 API 的 function-level disasm 结论；
`fs_notes.md` 记录 directory enumeration 和 disk state；`memory_notes.md` 记录 firmware heap alloc；
`window_notes.md` 记录 window/control 创建；
`text_notes.md` 记录 text draw；`time_notes.md` 记录 clock/alarm 线索；
`input_notes.md` 记录 touch/key；`media_notes.md` 记录 audio/video/image 线索；
`picture_notes.md` 记录 BMP/JPEG decode 和 picture struct；
`paint_notes.md` 记录 canvas/pixel draw；`dlx_notes.md` 记录 DLX resource container；
`bbvm_notes.md` 记录 BB 虚拟机包装线索；`gameboy_notes.md` 记录 emulator app 逆向；
`gba_notes.md` 记录 GBA.BDA 原生 probe；`game_framework_notes.md` 记录原机游戏的
display/audio 模式；`element_bda_notes.md` 记录元素周期表的标准 window/DLX/VX resource
lifecycle；`thunder_api_notes.md` 记录雷霆战机源码名称到 runtime SDK API 的映射和用法，
`thunder_api_inventory.md` 是该 BDA 的 75-entry 完整调用清单；`showcase_notes.md` 记录
Element 风格显示实验的真机回归链路。

`usb_debug_notes.md` 记录第一版 USB 大容量存储命令/日志调试桥；
`game_api_verification_progress.md` 记录游戏候选系统 API 的分级动态验证进度；
`verification_notes.md` 记录当前 SDK/toolchain 的 verify 覆盖和风险边界。
