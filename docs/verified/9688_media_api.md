# 9688 V2.32 摄像头与原生 WAV 录音 API

公开头为 `sdk/include/bda_9688_platform.h`、`bda_9688_camera.h`、
`bda_9688_recording.h`。按需包含 `bda_9688_media.h`，或使用完整聚合头 `bda_sdk.h`。
这些接口绑定精确的 9688 C100 V2.32 ROM；9588、其他版本或签名不符会返回不支持，
不会调用私有设备函数。

**JZ4740 已于 2026-11-01 经真机 Debug EXEC 完成动态闭环；JZ4730 仅为静态候选。**
新增接口不改变 [实时 PCM 录音 API](audio_capture_api.md) 的成熟度：
`bda_audio_capture_*` 返回调用者可读取的 raw PCM block，本页 `bda_9688_recorder_*`
管理固件持有的 WAV 文件、异步录音任务和完成回调，是不同的生命周期。

## 精确 Profile 与成熟度

`bda_9688_media_profile()` 返回只读 profile，未知固件返回 `NULL`。
`bda_9688_probe(&context)` 将五张服务表与 ROM seed CRC 一起匹配；摄像头和录音
初始化随后分别核对自己的机器码守卫。应用可读取 `profile->device_model`、`chip`、
`support_level`、`name` 和 `raw_firmware_sha256`。

| 设备 / 固件 | 芯片 | 原始 payload SHA-256 | `support_level` |
|---|---|---|---|
| 9688 C100 V2.32 | JZ4740 | `7ec707b69a1f4fa7016856b2eba6900412d02d7daefc8b4d11654c63731abca0` | `BDA_9688_SUPPORT_HARDWARE_VERIFIED` |
| 9688 C100 V2.32 | JZ4730 | `b18ce485a6ca6a8ea9ef5e3963d5970188ff7a2aeb4a6d4e58fe43625f49e514` | `BDA_9688_SUPPORT_STATIC_CANDIDATE` |

hash 对应加载在 `0x80004000` 的 raw `C100.bin`。包装文件 `kj409688.bin`（4740）
和 `C100knl.bin`（4730）多出 64 字节头，去头后与对应 payload 一致。仓库不分发
原厂固件、原机应用或拍摄、录音内容。`STATIC_CANDIDATE` 表示地址和离线调用约定
已核对，不能解释为该型号真机已通过。

```c
#include "bda_9688_media.h"

const bda_9688_profile_t *profile = bda_9688_media_profile();
/* NULL: unsupported; profile->support_level tells the evidence level. */
```

## 摄像头

公开范围是 **320×240、YUYV（Y0 U Y1 V）、stride 640、153600 字节**的单帧 DMA。
预览由应用重复抓帧、转换和绘制组成；没有公开未验证的高分辨率模式或 native UI。

| 调用 | 作用与返回值 |
|---|---|
| `bda_9688_camera_init(&camera, &platform)` | 核对代码并初始化上下文，不开启传感器 |
| `bda_9688_camera_open_qvga(&camera)` | 检查独占、保存配置并开启 QVGA；0 成功 |
| `bda_9688_camera_start(&camera)` | 清除旧 done，再启动本帧；0 表示启动成功 |
| `bda_9688_camera_poll(&camera, &frame)` | `E_BUSY` 尚未完成；0 表示 DMA 已停止且稳定帧可读 |
| `bda_9688_camera_yuyv_to_rgb565(...)` | 独立缓冲区的 RGB565 转换；检查尺寸、容量、对齐和重叠 |
| `bda_9688_camera_close(&camera)` | 停止采集并释放原生设备，恢复自身 GPIO/时钟/IRQ 配置 |

上下文先显式清零，避免无 CRT 程序的大聚合初始化依赖 `memset`：

```c
bda_9688_context_t platform;
bda_9688_camera_t camera;
bda_9688_camera_frame_t frame;
bda_9688_camera_zero((volatile u32 *)&camera, sizeof(camera) / sizeof(u32));
int result = bda_9688_probe(&platform);
if (!result) result = bda_9688_camera_init(&camera, &platform);
if (!result) result = bda_9688_camera_open_qvga(&camera);
if (!result) result = bda_9688_camera_start(&camera);
/* Poll with a shared total budget, then always check close's return value. */
```

`frame.pixels` 是借用的 uncached DMA 视图，下一次 start 或 close 后失效；不得 free，
不得在 DMA 运行时读取。需要下载或长期保存时，在关闭前复制到自己的内存。
RGB565 目标需 76800 个 `u16`，与 YUYV 源完全独立。相机拒绝接管原生相机 UI、
已占用的设备、异常元数据或被改写的 IRQ；fault/busy 不能当作清理已经完成。

### 曝光预热与等待

JZ4740 初次打开后的首帧近灰。原厂拍摄路径有 13 次采集计数；真机在同次 open 中
严格等待 13 个新 DMA 帧、丢弃前 12 帧后取得了实际场景。每次 start 都必须清除旧
完成标志，调用方应设置覆盖全部帧的总等待预算。固定帧数不保证任意光照下曝光准确。

[最小摄像头示例](../../example/system/camera/camera_demo.c) 取得 13 帧、转换最后一帧，
关闭相机并释放转换缓冲后才显示消息框。它使用一个全局轮询次数预算，配合原生
校准 busy delay；该次数不是毫秒，也不是 RTOS 延时。CIM 完成来自 IRQ，示例不依赖
低优先级媒体任务；不能把此 busy-poll 等待方式照搬到异步录音。

## 固件持有的 WAV 录音

```text
init -> open(new_path) -> start -> QUEUED -> CAPTURING
                                      |
                                      v
                            stop accepted -> STOPPING
                                      |
                               completion callback
                                      |
                                      v
                                COMPLETE -> finish
```

| 调用 | 作用与注意点 |
|---|---|
| `bda_9688_recorder_init(&recorder, &platform)` | 核对媒体/后端机器码并初始化 |
| `bda_9688_recorder_open(&recorder, path)` | 父目录须存在；原生 `wb` 会截断同名文件 |
| `bda_9688_recorder_start(&recorder)` | 成功只代表已排队，不代表已开始采集 |
| `bda_9688_recorder_poll(&recorder, &status)` | 返回 SDK 状态、native_state、采集中毫秒计数和原生错误 |
| `bda_9688_recorder_stop(&recorder)` | 尚在 queued 时 BUSY；成功只是停止请求已接受 |
| `bda_9688_recorder_finish(&recorder)` | 等完成回调后同步写最终 WAV 头、flush、close 并释放后端 |

所有操作在同一任务和翻译单元串行执行，一次只用一个 recorder。recorder、回调代码
及所在 BDA 必须保留到 finish 完成；不能启动后直接从 `bda_main()` 返回或换掉模块。
回调只发布完成/错误，不在中断或回调里 close。已接受 stop 不等于 callback 已结束，
`native_state==1` 也不能代替完成标志。从未 start 的 open 文件可直接 finish。

正常应用将 poll 放到 GUI 事件循环，在 queued/capturing/stopping 期间继续分发事件，
让出任务给原生媒体 worker。Debug 真机测试使用单一串口会话和同一 RAM 镜像，每轮
短调用返回或协作 yield；Debug 任务优先级 6，媒体 worker 为 7，不能高优先级忙等。
`status.elapsed_ms` 仅在 native_state 2 的采集中有明确含义，按 4 KiB 块以 128 ms 增加；
完成后可能回零，最终时长应以文件实际 data 字节数计算。

[录音示例](../../example/system/recording/recording_demo.c) 的入口只检测 profile/格式，
**不打开麦克风、不创建文件**。同文件的 begin、request_stop、poll_and_finish helper
展示应用如何接入自己的 GUI Start/Stop/idle 事件；没有隐藏的阻塞录音循环。

### WAV 与文件 API

| 字段 | JZ4740 V2.32 | JZ4730 V2.32 |
|---|---|---|
| 采样 | 16000 Hz、mono | 16000 Hz、mono |
| 原生编码 | PCM tag 1，16 bit | IMA ADPCM tag 0x11，4 bit |
| fmt chunk | 32 字节 | 20 字节及 fact chunk |
| block align | 256（原厂非常规值） | 256，505 samples/block |
| 证据 | 真机 WAV 完整读回 | ROM/MIPS 模型 |

SDK 保留原厂头部，不改成跨型号的统一 PCM 读取接口。JZ4740 原生 PCM WAV 的
block_align=256 不是通常的 mono PCM16 值 2，不保证全部播放器接受。可在电脑端另存
标准头播放副本，但应保留原文件，并校验 PCM 内容逐字节不变。native close 不可靠
传播所有存储错误，因此 finish 成功不能代替文件重开、读回及长度检查。

JZ4740 实测 `FS+0x10` seek **成功返回新的文件偏移，失败为 -1**，不是标准 C fseek
的零成功值。seek-to-end 通常返回正的文件长度；seek-to-offset 可核对返回值等于目标
offset。FILE 指针用 `int` 存储时可能为负，只有零表示 open 失败。读取应使用真实
四参数 `(buffer, size, count, file)` ABI；本页未修改既有 raw filesystem wrapper。

## 错误和清理

错误名称均带 `BDA_9688_` 前缀：

| 名称 | 值 | 含义 |
|---|---:|---|
| `OK` | 0 | 当前步骤完成 |
| `E_UNSUPPORTED` | -1 | profile 或精确代码守卫不匹配 |
| `E_ARGUMENT` | -2 | 参数无效 |
| `E_BUSY` | -3 | 被占用或异步步骤尚未完成 |
| `E_NATIVE` | -4 | 原生接口失败或返回不符 |
| `E_STATE` | -5 | 上下文或生命周期无效 |
| `E_IO` | -6 | 设备/数据检查失败 |
| `E_RANGE` | -7 | 地址、长度或容量越界 |

相机总是检查 close；录音总是等待 callback 再 finish。所有权丢失或异常返回时不能
盲目释放不属于调用者的资源，也不能把失败当作可以卸载代码的证明。录音已消费的
handle 不得因 close 返回异常而重试，避免误关之后复用该 handle 的媒体对象。

## 2026-11-01 真机证据

目标是 9688 V2.32/JZ4740，运行 Debug BDA SHA-256
`fe9d5b7ef5aebd6142c4ddb79e0bc721362e49bb1ad3cd8d5349a42a12346765`，
驻留 image_id `49d6b0c7`。独立 EXEC 模块直接调用这些 SDK 函数，先完成 camera
关闭/副本释放，再替换为 recorder 模块；不依靠原厂相机或录音界面代做操作。公开头迁入新目录后，又用包含新型号/芯片门禁的
独立只读模块在同一真机复核：probe=0、device=9688、chip=4740、support=2，
camera_init=0、recorder_init=0；该次门禁复核没有再次打开传感器或麦克风。
公开的[真机结果摘要](assets/9688_media_hardware_result.json)记录复核与采集证据，
不包含原图、音频或原厂固件。

- 相机 open、sensor probe、start、poll、close 均返回 0；13 个完整帧后取得
  320×240 YUYV。SDK 转换的全部 153600 字节 RGB565 与电脑端独立整数公式一致。
  第 13 帧 Y 范围 64..155，包含暗环境的实际物体，未评估色彩准确度。
- YUYV SHA-256：`e38103a8514c6b57bf70e3504f4c5a103501dff6c8c77c4bcdde15c71673e1dd`；
  RGB565 SHA-256：`6dd1d9ca1e3f4564db7db3559bc44ea8eaea06bbb01e2f02c955d4df66aeadf5`。
- 录音 queued→capturing，计数 3072 ms；stop 后 callback error=0，再 finish。
  重开并完整读回 98364 字节 WAV：RIFF size=98356，fmt=32，data=98304，即
  49152 个 mono PCM16 采样、**3.072 秒**。非零采样 41128，520 个不同值，
  采样范围 -178..2228；有变化的真实音频输入，没有验证可辨识语句。
- 原厂 WAV SHA-256：`586fe0397b5c0f0b873b2349a8e30601448d5c83b6c0347e18296a419d3af294`。
- camera IRQ/全局恢复、图像副本释放、recorder callback 完成及文件关闭后，两项
  测试的空闲堆均回到 **11566556 字节**；USB fault、last_error、bad_frames 均为 0，
  EXEC 状态回到空闲，Debug 保持运行。

新公开示例经过编译 smoke 和 BDA 静态校验，未将“新示例 BDA 已独立真机运行”作为
结论；上述动态闭环来自保留上下文的独立 EXEC 模块。私图、音频、设备文件、完整
原厂固件和实验 USB 调试器不随本 SDK 发布，以上尺寸、hash 和观察结果供核对。

未覆盖 JZ4730 真机、摄像头与录音同时使用、长时间采集、异常拔线清理、存储故障
注入及电气特性测量。现有 `bda_audio_capture_*` raw PCM 的 9688 profile 仍为
`STATIC_CANDIDATE`，不能因高层 WAV 路径通过而升级。

## 构建

```powershell
bda-pack example\system\camera\camera_demo.c --title Camera9688 --category 9 `
  -o build\Camera9688.bda
bda-validate build\Camera9688.bda

bda-pack example\system\recording\recording_demo.c --title Record9688 --category 9 `
  -o build\Recording9688.bda
bda-validate build\Recording9688.bda
```

两例只包含公开头，不要求 `-I reverse`。型号或固件不支持时入口直接返回，不通过
未知 GUI 显示消息；在支持 profile 上，摄像头示例会访问传感器，录音示例入口只读。
