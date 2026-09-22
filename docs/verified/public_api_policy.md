# `sdk/include` 准入规则

`sdk/include/bda_sdk.h` 是全部已验证模块的聚合入口；内存、文件、输入、时间、窗口、
绘图、对话框、控件和音频分别位于独立 `bda_*.h`。tick、counter、delay 和窗口定时器
统一位于 `bda_time.h`。`bda/detail/runtime.h` 只承载这些
wrapper 共用的动态函数表实现。这里不是逆向 API 候选目录，只能放入已经动态验证、ABI
稳定且结论确定的系统或固件绑定 API。

## 必须满足的条件

一个 API 进入 `sdk/include` 前，必须同时满足：

1. 使用独立测试 BDA 调用了目标 API，而不是只观察原机应用调用点。
2. 在当前目标固件的真机或模拟器中实际运行，并得到可重复的可观察结果；文档必须
   明确环境，不能把其中一种环境的结果自动扩张到另一种。
3. 参数顺序、参数宽度、返回值语义及必要的数据结构布局已经确定。
4. 在 `docs/verified/` 有独立说明，记录用法、注意点、固件绑定、测试步骤、
   动态证据和未覆盖边界。
5. 有可编译的最小示例，并保留构建或回归验证。

已经完成动态闭环的公开 API 可以增加“精确固件绑定”，但不得借此引入新的未验证
参数或生命周期。新增绑定必须同时具备设备/芯片识别、完整机器码门禁、固定镜像 hash、
离线调用约定复核和公开的成熟度字段；未完成对应真机闭环时必须标记为
`STATIC_CANDIDATE`，文档和兼容性矩阵不得写成真机通过。录音 API 的多固件 profile
采用这一规则：公开调用约定来自已验证基线，各固件绑定保留各自的验证等级。

可观察结果包括屏幕输出、导出的日志或数据文件、输入响应和绘图截图。仅有以下证据
不够进入本目录：

- 静态反汇编或固件表项定位。
- 其他 BDA 的调用点和参数推断。
- C 源码编译、链接或 BDA header 校验通过。
- 模拟器未崩溃、API 返回了一个数值，但结果语义未闭环。
- 尚未复现成功的 probe，或只在逆向笔记中标记为 `_LIKE` 的候选接口。

稳定公开 API、类型和常量的名称不得带 `_like` 或 `_LIKE` 后缀。该后缀只允许出现在
`reverse/bda_research_sdk.h` 和普通逆向笔记的候选名称中；候选接口动态闭环并进入公开头时，
必须同时确定稳定的公开名称。`sdk/include` 不提供带 `_like` 的兼容别名。

SDK 尚未对外发布，不为仓库内部出现过的旧误名保留兼容别名。同一个系统表项在公开头
中只保留一个开发者名称；内部示例和文档应同步迁移，避免把单个能力误导成两个 API。

## 当前公开范围

- 9588/9688 机型与 JZ4720/JZ4730/JZ4740 只读识别：
  `docs/verified/hardware_detection_api.md`
- Message Box、是/否和是/全部/否确认框：`docs/verified/msgbox_api.md`
- 系统帮助页：`docs/verified/help_page_api.md`
- 文件写入与读回：`docs/verified/fs_write_api.md`
- 全局 open-file flush 与强制断电 A/B：`docs/verified/fs_flush_api.md`
- 文件删除、重命名、空目录删除、路径信息、容量和存储状态：
  `docs/verified/file_management_api.md`
- 六个实体键轮询：`docs/verified/input_polling_api.md`
- 高速触摸逻辑坐标读取：`docs/verified/touch_position_api.md`
- GAMEBOY 式全局原始输入事件流：`docs/verified/raw_input_event_api.md`
- frame 绘制链和图形图元：`docs/verified/graphics_primitives_api.md`
- 真机触摸坐标与完整 frame 生命周期：`docs/verified/touch_window_lifecycle_api.md`
- 游戏 compatible context、VX、矩形复制、色键、dirty rect 和 25 ms tick：
  `docs/verified/game_rendering_api.md`
- 标称 1 ms counter 及 timer start/read/stop 生命周期：
  `docs/verified/high_resolution_timer_api.md`
- Frame 周期定时器、`0x144` 消息、存在查询和安全改周期：
  `docs/verified/window_timer_api.md`
- 基础 heap、seek、目录创建/切换和文件枚举：
  `docs/verified/runtime_services_api.md`
- 原生尺寸 raw RGB565 picture descriptor 提交：
  `docs/verified/picture_rendering_api.md`
- C200 240×320 RGB565 直接 framebuffer 获取、方向补偿、整帧提交和布局拒绝回退：
  `docs/verified/direct_framebuffer_api.md`
- 系统文件选择器：`docs/verified/file_selector_api.md`
- 内建控件、内存 GIF89a 播放、控件消息和自定义类：
  `docs/verified/controls_api.md`
- 22050 Hz/16-bit/mono raw PCM open、write、attenuation 与真机安全 stop：
  `docs/verified/audio_pcm_api.md`
- 9588/9688 多固件 profile 保护的 16000 Hz/16-bit/mono 实时 PCM 录音；
  9588/JZ4730 已真机验证，其余 profile 保持静态候选：
  `docs/verified/audio_capture_api.md`

未达到上述条件的 API 必须留在 `reverse/bda_research_sdk.h` 或 `reverse/docs/` 逆向材料中，
不得被打包器隐式提供。受控 probe 可以显式传 `-I reverse` 使用候选头，但这不会改变
候选 API 的验证状态。若后续证据推翻现有 ABI，应立即从公开头移除或降回候选区，
不能为了源码兼容继续声明为稳定 API。
