# SDK API 目录

`sdk/include/` 只保存动态验证后公开的 API。普通应用可以包含完整聚合头：

```c
#include "bda_sdk.h"
```

也可以按能力显式包含模块，避免一个对话框或音频程序得到全部 SDK 声明：

| 头文件 | 能力 |
|---|---|
| `bda_types.h` | SDK 版本、freestanding 基础类型和 handle |
| `bda_hardware.h` | 9588/9688 机型、JZ47xx 芯片和原始签名地址识别 |
| `bda_memory.h` | `memset`、`memcpy`、堆分配与释放 |
| `bda_filesystem.h` | 文件读写、flush、seek、增删改查、路径信息、容量与枚举 |
| `bda_input.h` | 六键轮询、原始输入事件和高速触摸坐标读取 |
| `bda_time.h` | 25 ms tick、标称 1 ms counter、Frame 周期定时器和 busy-wait delay |
| `bda_window.h` | Frame、消息、事件泵和窗口生命周期 |
| `bda_graphics.h` | draw context、图元、文字、VX、picture、context copy 和 C200 framebuffer |
| `bda_dialogs.h` | Message Box、确认框、帮助页和文件选择器 |
| `bda_controls.h` | 内建控件、GIF 和自定义控件类 |
| `bda_audio.h` | raw PCM 播放，以及 9588/9688 精确固件 profile 保护的实时录音 |
| `bda_sdk.h` | 聚合上述全部公共模块 |

例如，一个带窗口、按键和绘图的游戏可以只包含：

```c
#include "bda_graphics.h"
#include "bda_input.h"
#include "bda_time.h"
#include "bda_window.h"
```

模块头只包含自身实现所需的依赖，不会自动包含 `bda_sdk.h`。底层动态函数表和调用
helper 位于 `bda/detail/runtime.h`，它是公开 wrapper 的实现细节，应用不应直接包含。

未验证候选 API 单独保存在 `reverse/bda_research_sdk.h`。只有
`reverse/examples/` 中的受控研究 probe 才显式传入 `-I reverse`；普通应用不得依赖
候选 header。

- [已验证示例](../example/README.md)
- [开发者文档](README.md)
- [公开 API 准入规则](verified/public_api_policy.md)
- [机型与芯片识别](verified/hardware_detection_api.md)
- [触摸与窗口生命周期](verified/touch_window_lifecycle_api.md)
- [高速触摸坐标读取](verified/touch_position_api.md)
- [GAMEBOY 式原始输入事件](verified/raw_input_event_api.md)
- [C200 直接 framebuffer](verified/direct_framebuffer_api.md)
- [游戏绘图与计时](verified/game_rendering_api.md)
- [高分辨率计时](verified/high_resolution_timer_api.md)
- [窗口消息定时器](verified/window_timer_api.md)
- [堆、seek 与目录服务](verified/runtime_services_api.md)
- [全局文件 flush](verified/fs_flush_api.md)
- [文件管理、路径信息与容量](verified/file_management_api.md)
- [内建控件](verified/controls_api.md)
- [Raw PCM 音频](verified/audio_pcm_api.md)
- [实时 PCM 录音](verified/audio_capture_api.md)
