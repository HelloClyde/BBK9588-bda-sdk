# Filesystem API 笔记

本文记录原生 BDA filesystem table 的当前结论。function-level C200 disasm 补充见
`c200_api_function_notes.md`。已经完成动态写入验证的开发者文档见
`verified/fs_write_api.md`。

## 基础文件读写

`FS+0x000..+0x020` 基本对应 stdio 风格 API：

```c
file = fopen(path, "rb");
fseek(file, 0, SEEK_SET);
fread(buffer, 1, size, file);
fwrite(buffer, 1, size, file);
pos_or_size = ftell(file);
eof = feof(file);
err = ferror(file);
clearerr(file);
fclose(file);
```

SDK 中对应 wrapper：

```c
int bda_fs_fopen_raw(const char *path, const char *mode);
int bda_fs_close_raw(int file);
int bda_fs_fread_raw(void *buffer, u32 size, u32 count, int file);
int bda_fs_fwrite_raw(const void *buffer, u32 size, u32 count, int file);
int bda_fs_seek_raw(int file, int offset, int whence);
int bda_fs_tell_raw(int file);
int bda_fs_eof_like(int file);
int bda_fs_error_like(int file);
int bda_fs_clear_error_like(int file);
```

重要修正：成功返回值是高地址 file-object pointer，按 signed `int` 显示时通常为负数，
不能使用 `fd <= 0`。失败哨兵为 `0` 或 `0xffffffff`，统一使用
`bda_fs_file_is_valid(fd)`；把失败哨兵继续传给 read/seek 可能导致真机重启。

`FS+0x008/0x00c` 的 C200 参数顺序与 stdio 一致，是
`buffer, size, count, file`。table entry 会从 `file+0x48` 读取 handle index；索引非法、
volume 越界或 filesystem backend 未就绪时返回 `0`，不是 `-1`。因此 read/write
调用前必须先确认 `bda_fs_fopen_raw()` 返回有效 fd，调用后按返回的元素/byte
数量判断实际完成量。

模拟器 worker NAND 写入闭环已经确认：`fs_write_demo.c` 分别使用 `A:` 路径和根相对路径
写入 `BDA-FS-WRITE-9588\r\n`，两路均返回 `write=19,tell=19,error=0,read=19,match=1`。
停止 QEMU 提交 worker 后，从 NAND 文件接口导出的两个文件均为 19 byte，SHA-256 都是
`44f98eda68a182a6222469f93bc9f008747fd942d966549328dfe25792180f76`。

`FS+0x010` 是 fseek-like 调用，参数顺序为 `file, offset, whence`。C200
只接受 `BDA_SEEK_SET(0)`、`BDA_SEEK_CUR(1)`、`BDA_SEEK_END(2)`；其他 whence
会返回 `-1`。三种模式分别把当前位置 `file+0x44` 设置为 `offset`、
`current+offset`、`file_size_like+offset`，其中 `file_size_like` 来自 handle
object `+0x20`。

`FS+0x014` 是 ftell-like 调用。C200 先读取 `file+0x48` 的 signed 16-bit
index 并检查 backend 范围；index 非法时返回 `0` 并设置内部错误码 `9`，backend
未就绪时返回 `0` 并设置 `0x10`。有效路径返回 `file+0x44`。因此 `tell()` 返回
`0` 不能单独证明失败；调用前必须确认 file handle 有效，取文件大小时按原机模式
先 `seek(file, 0, BDA_SEEK_END)` 再 `tell(file)`。

研究用最小编译示例见 `reverse\examples\fs_read_demo.c`。它读取
`A:\gba\gba.cfg`，流程是：

```c
int file = bda_fs_fopen_raw("A:\\gba\\gba.cfg", "rb");
if (!bda_fs_file_is_valid(file)) {
    /* 打开失败，不能继续 read/seek/close */
}
bda_fs_seek_raw(file, 0, BDA_SEEK_END);
int size = bda_fs_tell_raw(file);
bda_fs_seek_raw(file, 0, BDA_SEEK_SET);
int got = bda_fs_fread_raw(buffer, 1, sizeof(buffer), file);
bda_fs_close_raw(file);
```

示例使用 ASCII 路径来避免源码编码影响。若路径包含 `应用`、`系统` 等中文目录，
当前建议显式写 GBK byte string，例如已有 path matrix probe 中的
`"\xd3\xa6\xd3\xc3"` 表示 `应用`。

C200 function-level evidence：

- `FS+0x000` 目标 `0x80170b68`，会申请 `0x20a` byte handle object，参数仍是
  `path, mode`。
- `FS+0x004` 目标 `0x8017a928`，保存 `a0=file` 后调用内部 close helper
  `0x80170c74`。
- `FS+0x008` 目标 `0x8017a978`，保存 `a0=buffer,a1=size,a2=count,a3=file`。
- `FS+0x00c` 目标 `0x8017ab2c`，保存 `a0=buffer,a1=size,a2=count,a3=file`。
- `FS+0x010` 目标 `0x801712a0`，保存 `a0=file,a1=offset,a2=whence`。
- `FS+0x014` 目标 `0x8017ac18`，检查 `file+0x48` index 和 backend pointer 后，
  有效路径返回 handle object `+0x44` 的当前位置/文件大小类 word。
- `FS+0x018` 目标 `0x8017ac84`，检查 `file+0x48` index 和 backend pointer 后，
  对比 `file+0x44` 当前位置与 `file+0x20` size-like word，返回 eof-like 状态。
- `FS+0x01c` 目标 `0x8017acfc`，检查 `file+0x48` index 和 backend pointer 后，
  读取 `file+0x4a` 的 `0x1000` flag，返回 ferror-like 状态。
- `FS+0x020` 目标 `0x8017ad70`，检查 `file+0x48` index 和 backend pointer 后，
  清掉 `file+0x4a` 的 `0x1000` flag，返回 clearerr-like 状态。

原机证据来自游戏、相册、电子书、录音等应用。相册会 `fseek(..., SEEK_END)`
后调用 `FS+0x014` 获取大小。
BB 虚拟机、Eros 方块、三国霸业、九宫格、决战坦克、连连看、雷霆战机、黑白子等
都有 `FS+0x018/+0x01c/+0x020` 的 file 状态 wrapper 调用点。

2026-09-22 的独立 `FMAPI` 探针又在 8013 完整 NAND 中完成了创建、写入、路径查询、
枚举、重命名、非空目录拒删、文件删除和空目录删除闭环。对应的稳定公开名称已进入
`sdk/include/bda_filesystem.h`：`bda_fs_remove()`、`bda_fs_rename()`、
`bda_fs_rmdir()`、`bda_fs_disk_info()`、`bda_fs_getcwd()`、
`bda_fs_path_info()` 和 `bda_fs_storage_ready()`。下文保留 `_like`/`raw` 名称用于描述
研究头和原始逆向过程；公开用法与动态边界见
`docs/verified/file_management_api.md`。

## 删除文件

`FS+0x024(path)` 是 remove/unlink 类调用。C200 table entry 目标为 `0x801717f4`，
只读取 `a0=path`，随后申请 `0x20a` byte 临时 path buffer，调用路径解析 helper
`0x8016f904`，再进入内部删除 helper。路径解析失败或 volume/index 越界会
返回 `-1` 并设置内部错误码 `9`；filesystem backend 未就绪时可设置 `0x10`。

SDK wrapper：

```c
int bda_fs_remove_raw(const char *path);
```

原机游戏和记事本会用它删除/重建存档或文档文件。新代码应先确认 path 是目标
文件，不要把 directory path 或未终止字符串传入该 wrapper；删除后若要重建文件，应重新
`bda_fs_fopen_raw(path, "wb")` 并检查 return value。

## 重命名/移动

`FS+0x028(old_path, new_path)` 是 rename/move-like 调用。C200 table entry 目标为
`0x80171d24`，会先用 `0x80174340` 判断两个 path 的 volume/backend 类别，再分别
申请 `0x20a` byte 临时 path buffer，通过 `0x8016f904` 解析 old/new path，最后调用
内部 rename helper `0x80171930(old_resolved, new_resolved)`。成功后调用
`0x801813a0(volume)` 做同步/刷新；失败通常返回 `-1` 并设置内部错误码。

SDK wrapper：

```c
int bda_fs_rename_like(const char *old_path, const char *new_path);
```

这是破坏性 API，会修改 filesystem。调用前应确认 old/new path 都是 GBK/ASCII
zero-terminated string，并且不要依赖它跨不确定 volume 移动文件。原机 BB 虚拟机、
Eros 方块、三国霸业、九宫格、决战坦克、连连看、雷霆战机、黑白子等游戏框架
都有直接 FS+0x028 调用点。

## 目录创建

多个应用使用以下模式：

```text
FS+0x02c(path)
if return == -1:
    FS+0x030(path)
```

路径通常是系统目录或系统数据目录，因此当前把 `+0x02c` 命名为
`chdir_like`，`+0x030` 命名为 `mkdir_like`。C200 function-level slice 已经确认
`FS+0x02c` 会解析 path、检查 directory attr bit `0x4000`，成功后更新 current directory state；
`NULL` 路径返回 `-1`，空字符串返回 `0`。它不只是普通 `access()` 检查，
调用后可能改变后续 relative path 的解释。`FS+0x030` 会解析 path 并调用内部 mkdir
helper，失败时同样返回 `-1` 并设置内部错误码。

`FS+0x034(path)` 是 rmdir/remove-directory 类调用。C200 wrapper 只读取单参数
`path`，先用 `0x8016f904(path, temp_path)` 解析路径，再调用内部 directory removal
helper `0x801720c8(temp_path)`。内部 helper 会检查目标是 directory，并更新目录项、
cluster 链和 filesystem 状态；成功返回 `0`，失败通常返回 `-1` 并设置内部错误码。
这个调用会修改 filesystem，只应传空目录 path。不要传 file path、`NULL`、未终止
字符串或仍包含文件的目录。

## Directory Enumeration

directory enumeration 是三调用组合：

```text
FS+0x03c(path_or_pattern, attr_filter, find_data)
FS+0x040(find_data)
FS+0x044(find_data)
```

记事本、系统设置、相册、录音都会用这个组合。`C200.bin` 和 `4720knl.bin`
字符串中也能看到 `fs_findfirst`，与该组合吻合。

已见 filter 值：

```text
0x01  相册/录音扫描
0x06  记事本扫描
0x10  系统设置，可能是目录属性
0x27  系统设置，更宽的过滤
```

`find_data` struct 还未完整命名。应用传入调用者持有的 stack/global buffer，并在
`findnext` 之间读取其中字段。

C200 function-level disasm 已经确认几个重要边界：`findfirst` 参数是
`pattern, attr, find_data`；table entry 会先申请 `0x20a` byte 临时 path buffer，调用
`0x8016f904(pattern, temp_path)` 解析路径，然后在 backend 锁内调用
`0x8017e1a0(temp_path, find_data, attr)` 写回枚举状态。成功路径会写
`find_data+0x21c`，因此早期 probe 使用的 `unsigned char[512]` 偏小。SDK 现在
提供保守的 `bda_fs_find_data_like_t`，大小由 `BDA_FS_FIND_DATA_SIZE` 固定为
`0x220` byte，并只命名已确认
offset：

```c
bda_fs_find_data_like_t data;
bda_fs_find_data_init_like(&data);
if (bda_fs_findfirst_like("\\*.*", 0x27, &data) != -1) {
    /* data.name_or_path12 是原始 byte name/path 区，通常为 ASCII 或 GBK。 */
    bda_fs_findclose_like(&data);
}
```

SDK 示例 `reverse/examples/fs_find_demo.c` 采用同样的保守模式：先清零
`bda_fs_find_data_like_t`，只调用 `findfirst`，成功时调用 `findclose` 收尾，并把
return value 和结构前 16 byte 显示出来。它用于确认 wrapper/struct 形状，不承诺
具体 pattern 在所有 dump 或真机目录状态下都能枚举成功。

已确认字段包括 `cursor(+0x000)`、`size_or_aux04(+0x004)`、
`attr_or_flags08(+0x008)`、`time_like0c(+0x00c)`、`date_like0e(+0x00e)`、
`volume_index10(+0x010)`、`name_or_path12(+0x012..+0x21b)` 和
`aux21c(+0x21c)`。`findfirst` 的 path 解析失败会返回 `-1`
并设置内部错误码 `9`，backend 未就绪会返回 `-1` 并设置 `0x10`；临时 buffer
申请失败路径会写全局 `0x80474280 = 1` 并返回 `0`，当前仍按保守异常路径处理。
`findnext/findclose` 会先读取
`volume_index10` 并检查范围，index 非法时返回 `-1` 并设置内部错误码 `9`，
backend 未就绪时返回 `-1` 并设置 `0x10`。C200 的 `findnext` 有效路径会对
backend 加锁，调用 `0x8017f6b0(find_data)` 原地更新下一项，然后解锁；
`findclose` 还会释放 `cursor`，有效路径会对 backend 加锁，调用
`0x8017f73c(find_data)` 清理 cursor，然后解锁。

hardware probe 结论：

```text
FSList_cat09.bda:
  FS+0x07c() -> 0x00000001
  FS+0x03c("a:\\*.*", 0x27, find_data) -> 0xffffffff
  find_data remains all zero
```

这说明存储就绪查询可用，但 `findfirst` 路径/过滤组合还没完全跑通。系统字符串
更偏向 root-relative 模式，如 `\*.*`、`\*.bda`，后续应继续用 short-message probe 确认。

## System File Selector

GAMEBOY.BDA 通过 GUI table 使用 high-level file selector，不是直接 FS enumeration：

```text
GUI+0x6a8  open/session-like；a0=mode，不是 descriptor pointer
GUI+0x6b8  list nth helper-like，不是无参数 get-result
GUI+0x6bc  list free helper；a0=head，不是无参数 selector close
GUI+0x6c8  modal run-like；a0=selector descriptor
```

`GUI+0x6a8` 会调用 `0x8001f344` 准备内部 selector 状态，把 `mode` 写到全局
`0x80473fe4`，并按 mode 读取不同状态 byte。真正打开时它在 stack 上构造 modal
frame descriptor，通过 `0x800bd36c(15)`、`0x800cc1c8` 和一组 event loop helper
完成弹窗生命周期；调用者不应该把 descriptor pointer 传给 open。

selector descriptor 不只是 path/title/filter。硬件测试显示，short descriptor 会打开 selector
但 directory text 黑底黑字不可读；按 GAMEBOY 风格填完整字段后颜色正常。因此
`bda_file_selector_like_t` 里的 `sentinel*`、`list_limit40`、`result64` 和
`internal*` 字段实际参与 display/theme/state 初始化，不是无害 padding。
当前字段名为：`out_path`、`extensions`、`dir_state`、`title`、`list_head`、
`internal14`、`status`、`selected_index`、`sentinel20`、`sentinel24`、
`internal28`、`internal2c`、`internal30`、`sentinel34`、`sentinel38`、
`internal3c`、`list_limit40`、`internal44`、`sentinel48`、`internal4c`、
`internal50`、`internal54`、`internal58`、`internal5c`、`internal60`、
`result64`。这些名称只描述当前初始化/观测边界，不表示字段语义已经稳定。
当前 SDK 不再暴露无参数 selector get wrapper；C200 中 `GUI+0x6b8`
读取的是 `a0=head, a1=index`，更像链表第 N 项 helper。
同样，`GUI+0x6bc` 会把 `a0=head` 传给 `0x8003e868` 释放链表节点和节点 data，
不是无参数 selector close。

`GAMEBOY.BDA` 在 `0x81c0fc7c` 的 `jalr` delay slot 显式执行 `move a0,s2`，其中
`s2` 是 selector descriptor。C200 的 `GUI+0x6c8` entry 虽然自己不改写 `a0`，但会
把它原样传给 `0x80040848`；内部在 `0x80040864` 保存该指针，并从 descriptor
`+0x00/+0x04/+0x0c/+0x18/+0x30` 读取路径、后缀、标题、状态和 flags。

这个 color 修正与 `RES+0x094` 无关。后续 RES094
probe 显示该 table entry 更像 trace/log stub，不会可见地加载 skin。

## Disk/Storage 状态

`FS+0x048(drive, info)` 返回 disk/storage 容量信息。C200 只使用 `drive & 0xff`；
当前确认 `0` 和 `1` 两类路径，其他值返回 `-1` 并设置内部 error `9`。系统设置会反复计算：

```text
word(info+4) * word(info+8) * word(info+0x0c)
```

并与 `0x200000`、`0x10000` 等阈值比较，像 FAT cluster 大小/数量计算。
九门课程也会调用 `FS+0x048` 并做同样的容量式乘法。

C200 成功路径会写四个 word：

```c
typedef struct bda_fs_disk_info_like {
    u32 total_clusters;       /* +0x00 */
    u32 free_clusters;        /* +0x04 */
    u32 sectors_per_cluster;  /* +0x08 */
    u32 bytes_per_sector;     /* +0x0c, C200 写 0x200 */
} bda_fs_disk_info_like_t;
```

容量估算可使用：

```c
bda_fs_disk_info_like_t info;
if (bda_fs_diskinfo_like(0, &info) == 0) {
    u64 free_bytes = bda_fs_disk_free_bytes64_like(&info);
}
```

`bda_fs_disk_free_bytes_like()` 保留 32-bit return value，适合复刻原机阈值判断；
新代码需要实际剩余 byte 数时优先用 64-bit helper：
`bda_fs_disk_free_bytes64_like()`。

## Current directory getter

`FS+0x050(buffer, size)` 是 current directory getter。C200 table entry 目标为
`0x801700d0`，会读取当前 volume index 和内部 current path 字符串，按
`A:`/`B:` 前缀生成路径，return value 是需要的 byte 数（包含 NUL）。

```c
char cwd[260];
int need = bda_fs_getcwd_like(cwd, sizeof(cwd));
```

`buffer == NULL` 或 `size` 小于所需长度时，C200 仍返回 required size；调用者应把
返回值当作“需要的 buffer 长度”处理。该 helper 只读，不会切换目录；切换仍使用
`bda_fs_chdir_like(path)`。

## Path info getter

`FS+0x054(path, info)` 是 path info getter。C200 table entry 目标为 `0x8017a0d8`，
会先申请 `0x20a` byte 临时 path buffer 并解析路径，然后调用内部 helper
`0x80179cb8(temp_path, info)` 填充 `bda_fs_path_info_like_t`。失败通常返回 `-1`。

当前确认输出结构至少写到 `+0x14`，SDK 固定为 0x18 byte：

```c
typedef struct bda_fs_path_info_like {
    s16 volume_index0;  /* +0x00 */
    u16 attr_like;      /* +0x02, bit 0x4000 表示 directory-like */
    s16 volume_index4;  /* +0x04 */
    u16 reserved6;      /* +0x06 */
    u32 size_like;      /* +0x08, 普通文件 size-like；目录路径为 0 */
    u32 time_like0c;    /* +0x0c */
    u32 time_like10;    /* +0x10 */
    u32 time_like14;    /* +0x14 */
} bda_fs_path_info_like_t;
```

示例：

```c
bda_fs_path_info_like_t info;
bda_fs_path_info_init_like(&info);
if (bda_fs_path_info_like("A:\\gba\\gba.cfg", &info) == 0) {
    u32 size = bda_fs_path_info_size_like(&info);
}
```

`time_like*` 字段来自 C200 内部转换，目前不命名为标准 FAT 时间。需要判断目录时使用
`bda_fs_path_info_is_dir_like(&info)`，不要直接依赖未知 bit。

`FS+0x07c()` 是无参数 storage-ready query。C200 table entry 目标为 `0x801705ec`，
函数不读取调用者参数，只调用内部检测 helper `0x8000f8a0`，并把 return value 收窄为
低 8 位。系统设置、媒体、录音、学习类应用会在启用文件相关流程前调用它。

`FS+0x078()` 是更 low-level 的 raw media-present query。C200 table entry 目标为
`0x8017952c`，函数不读取调用者参数，只调用内部 helper `0x8017060c` 并把结果
转换成 `0/1`。`0x8017060c` 会先调用 `0x800103c0()`，后者读取 `0xb0010300`
并检查 `0x01000000` bit；进入该路径前还会检查 `0xb0010300` 的 `0x00800000`
相关状态。SDK 暴露为 `bda_fs_media_present_raw_like()`，用于区分 raw media bit
和较高层的 `bda_fs_storage_ready_like()`；它不证明具体 `fopen/findfirst` 一定成功。

SDK 示例 `reverse/examples/fs_status_demo.c` 只读调用
`bda_fs_media_present_raw_like()`、`bda_fs_storage_ready_like()` 和
`bda_fs_stat_like(path, flags)`，用于确认 media bit、storage ready 与
path/access wrapper 形状。它不会创建、删除或写入文件；`stat` 返回 `-1`
只表示该 path/flags 组合失败或不存在，不应直接当作致命错误。

## stat/access 类调用

`FS+0x06c(path, flags)` 检查 path 存在或属性，失败返回 `-1`。C200 wrapper 只保存
并使用 `a0/a1`；没有读取 `a2`，因此它不会向调用者填充 `stat` 输出结构。
样本包括词典数据文件和系统数据目录下的游戏数据目录。

当前它更接近 `access()` 或带属性条件的存在性检查。内部 helper 对 flags `2`
和 `6` 有额外分支，会继续检查打开后的对象属性；其他 flags 主要按 standard path
打开结果返回。flags 的完整枚举仍需结合更多调用点命名。

## 全局 open-file flush

`FS+0x074`（C200 `0x8017b0d0`）是无参数全局 flush。它检查文件系统初始化状态，
取得全局锁并遍历最多 100 个 open-file slot，对带 dirty flag 的 file object 执行
writeback。公开 SDK 名称为：

```c
void bda_fs_flush_all(void);
```

8013 强制断电 A/B 已确认：flush 前写入且保持打开的 `F74YES.DAT` 重启后为 4096 byte
并逐字节匹配；flush 后才写入且同样未 close 的 `F74NO.DAT` 重启后为 0 byte。这个
入口不关闭任何 handle，也不是 `fflush(file)`；普通程序仍应正常 close。原始 return
value 混合内部状态，公开 wrapper 不暴露。完整记录见
`docs/verified/fs_flush_api.md`。

## 暂不公开的辅助函数

FS 表还有一些 C200 table entry 已能定位到 function VA，但当前不公开 SDK wrapper：

```text
FS+0x038  0x80172908  枚举/计数类目录 helper；当前未见原机直接调用点
FS+0x04c  0x80170078  FS/internal state init 或 reset；会写全局错误状态
FS+0x058  0x80179998  低层 storage/boot-sector 检查；触碰全局存储状态，风险高
FS+0x064  0x8017afb4  低层 block read support helper；volume/index 和 block 参数依赖内部状态
FS+0x068  0x8017a200  file-object block read helper；a3 是内部 file object/descriptor
FS+0x080  0x8017a708  path/open-object 内部检查；会扫描打开文件表，不是普通 exists/stat
FS+0x094  0x800d4950  落到 GUI-like function 区域，不能按 FS API 暴露
```

其中 `FS+0x058` 明显不是普通 file handle API：它会调用底层读块 helper，
检查 `0xe9/0xeb` boot-sector-like signature 和 `0x55aa` 尾标记，并写
`0x80474278/0x80474248` 等全局状态。不要在 SDK 中包装为普通 storage
query；现有只读 storage ready wrapper 是 `bda_fs_storage_ready_like()`。

`FS+0x068` 不是 standard file handle 操作。C200 entry 把 `a3` 当内部
file object/descriptor 读取 `+0x48/+0x4a/+0x20/+0x3c`，按 0x200 byte block
调用内部读块 helper，再把数据复制到 `a0` 指向的 buffer。雷霆战机和决战坦克的
调用点都是 `a0=buffer+index*stride, a1=index*stride, a2=stride, a3=file_object`，
调用前还把 `stack+0x14` 清零。这个入口依赖已经打开并初始化的内部 object，
不公开为 SDK wrapper；普通开发继续使用 `fopen/fread/fclose` 路径。

九门课程两次调用 `FS+0x064`，传入 `0x218` byte stack buffer 并检查返回数据
byte；这是非游戏来源的第二份证据。C200 中 `FS+0x064` table entry 有效，目标
函数为 `0x8017afb4`。entry 会把 `a0` 当作 signed 16-bit volume/index 检查，
用 `0x80175dfc(index, a1)` 转换 block/cluster 参数，再调用
`0x8017fbc0(a0, converted_a1, a2_or_default, a3)`；`a2 == 0` 时会从
`0x80474254` 读取默认 byte/size。它是低层 block read support helper，但
volume/index、锁和默认参数都依赖 firmware 内部状态，不应暴露公共 SDK wrapper。

Eros 方块和连连看展示了紧凑的存档模式：创建目录，打开共享
`\SysPet.yzj` 数据和应用自己的 `.dat` 文件，然后读写固定 `0x44` byte record。
两者都在该 helper 区域调用 `FS+0x068` 一次；现在 C200 已确认该入口读取内部
file object/descriptor，因此不应作为公共存档 API 暴露。

`FS+0x080` 不是普通存在性检查。C200 entry 会调用 `0x80174340` 解析当前
volume/path 状态，分配 0x58 byte 临时对象，再调用 `0x80173504(temp_obj, path, stack,
0)` 填充对象。随后它拒绝 directory-like 对象，并调用 `0x80178178(temp_obj)` 扫描
`0x8086cce0` 一带的打开 file object table，比对 `+0x48` index 和 `+0x18`
对象字段。成功路径返回 `1`，未命中返回 `0`，解析/内存失败返回 `-1` 并写内部错误码。
它更像“path 是否对应已打开/占用对象”的内部检查，不应在 SDK 中包装成
`exists`、`is_file` 或 `stat`。
