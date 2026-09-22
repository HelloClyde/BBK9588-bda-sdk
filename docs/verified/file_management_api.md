# 文件管理 API

文件管理器所需的删除、重命名、删除空目录、当前目录、路径属性、磁盘容量和存储就绪
查询已经在 `kj409588/C200` 完整 NAND 模拟器中形成动态闭环，并进入公开
`bda_filesystem.h`。原有的打开、读写、seek、全局 flush、创建/切换目录和枚举接口继续
保留；两组 API 合起来覆盖基础文件管理流程。

验证环境是 8013 硬件级模拟器，不自动代表 C200 真机结论。

## 公开接口

```c
#define BDA_FS_DRIVE_A 0u
#define BDA_FS_ATTR_DIRECTORY 0x4000u
#define BDA_FS_DISK_INFO_SIZE 0x10u
#define BDA_FS_PATH_INFO_SIZE 0x18u

int bda_fs_remove(const char *path);
int bda_fs_rename(const char *old_path, const char *new_path);
int bda_fs_rmdir(const char *path);

int bda_fs_disk_info(u32 drive, bda_fs_disk_info_t *info);
u64 bda_fs_disk_total_bytes(const bda_fs_disk_info_t *info);
u64 bda_fs_disk_free_bytes(const bda_fs_disk_info_t *info);

int bda_fs_getcwd(char *buffer, bda_size_t size);
void bda_fs_path_info_init(bda_fs_path_info_t *info);
int bda_fs_path_info(const char *path, bda_fs_path_info_t *info);
int bda_fs_path_info_is_dir(const bda_fs_path_info_t *info);
int bda_fs_storage_ready(void);
```

固件函数表项如下：

| 能力 | FS 表偏移 | 本次动态结果 |
|---|---:|---|
| 删除文件 | `+0x024` | `NEW.TXT` 删除返回 `0`，随后路径查询返回 `-1` |
| 文件重命名 | `+0x028` | `OLD.TXT -> NEW.TXT` 返回 `0`，旧路径消失且新文件保持 18 byte |
| 删除空目录 | `+0x034` | 非空时返回 `-1`，删掉文件后返回 `0` |
| 磁盘信息 | `+0x048` | drive `0` 返回 `0`，sector size 为 512 byte |
| 当前目录 | `+0x050` | 返回含结尾 NUL 的所需 byte 数；测试路径返回 `18` |
| 路径信息 | `+0x054` | 文件大小为 18，目录属性位 `0x4000` 生效 |
| 存储就绪 | `+0x07c` | 正常 NAND 返回 `1` |

## 数据结构

```c
typedef struct bda_fs_disk_info {
    u32 total_clusters;
    u32 free_clusters;
    u32 sectors_per_cluster;
    u32 bytes_per_sector;
} bda_fs_disk_info_t; /* 0x10 byte */

typedef struct bda_fs_path_info {
    s16 volume_index;
    u16 attributes;
    s16 volume_index_copy;
    u16 reserved;
    u32 size;
    u32 time_raw_0;
    u32 time_raw_1;
    u32 time_raw_2;
} bda_fs_path_info_t; /* 0x18 byte */
```

`time_raw_0..2` 是固件原生值，目前没有把它们误命名为标准 FAT 日期时间。文件管理器
可以可靠使用 `attributes` 的 `BDA_FS_ATTR_DIRECTORY` 位和普通文件的 `size`；展示时间
前应先完成独立解码验证。

容量换算 helper 使用 64-bit 乘法，避免 cluster 乘积在 32-bit 中先溢出：

```c
bda_fs_disk_info_t disk;

if (bda_fs_disk_info(BDA_FS_DRIVE_A, &disk) == 0) {
    u64 total = bda_fs_disk_total_bytes(&disk);
    u64 free = bda_fs_disk_free_bytes(&disk);
    /* format total/free for display */
}
```

## 查询和修改路径

路径仍是固件使用的 ASCII/GBK byte string。不要把 UTF-8 中文路径直接传入这些接口。

```c
bda_fs_path_info_t info;

bda_fs_path_info_init(&info);
if (bda_fs_path_info(path, &info) == 0) {
    if (bda_fs_path_info_is_dir(&info)) {
        /* directory */
    } else {
        /* regular file; info.size is valid */
    }
}
```

删除和重命名属于破坏性操作，界面应先确认目标类型和用户意图，并检查每一步返回值：

```c
if (bda_fs_rename(old_path, new_path) == -1) {
    /* rename failed; keep the original item visible */
}

if (bda_fs_remove(file_path) == -1) {
    /* missing path, directory path, or backend failure */
}

if (bda_fs_rmdir(directory_path) == -1) {
    /* the directory may be non-empty */
}
```

`bda_fs_rmdir()` 只用于空目录。递归删除不是单个固件 API：应用必须先枚举子项，分别
删除文件和空子目录，确认成功后再删除父目录。复制文件和跨 volume 移动同样应由应用
用 read/write/flush/close 组合实现；当前只验证了 A 盘同 volume 的普通文件重命名。

`bda_fs_getcwd()` 在测试中返回了包含结尾 NUL 的所需 byte 数。公开示例使用 260-byte
buffer 并检查返回值；小 buffer 和 `NULL` 查询模式尚未动态覆盖，不应依赖未验证的截断
行为。`bda_fs_storage_ready()` 只是轻量状态，返回非零也不能替代后续每个 API 的错误
检查。

## 模拟器动态闭环

研究探针先直接调用候选 wrapper；通过后，同一个流程改为只包含公开头文件并再次运行。
正式示例是：

- `example/filesystem/file_management/file_management_demo.c`
- `example/filesystem/file_management/FileManagement.bda`

公开示例 BDA SHA-256：

```text
20633563cc75126965fd75daba1e1e9a0543d78eaaf3adcbdcaa72bff673e80c
```

测试从全新专用 NAND 启动，只修改：

```text
A:\应用\数据\游戏\FMAPI\
A:\应用\数据\游戏\FMAPI.TXT
```

闭环顺序是：查询存储和容量、读取当前目录、创建目录、查询目录属性、切入目录、创建并
枚举 `OLD.TXT`、查询大小、重命名为 `NEW.TXT`、验证旧路径消失、验证非空目录拒绝
删除、删除文件、删除空目录，再验证目录消失。最终目录列表只留下 324-byte 结果日志，
没有残留 `FMAPI` 目录。

完整结果见 [file_management_probe_log.txt](assets/file_management_probe_log.txt)，结尾为：

```text
rename=0
old_after_rename=-1
new_info=0
new_size=18
rmdir_nonempty=-1
remove=0
new_after_remove=-1
rmdir_empty=0
dir_after_rmdir=-1
failures=0
RESULT=PASS
```

## 当前边界

- 这些新增接口只完成 C200 完整 NAND 模拟器验证，真机仍需复测。
- 只验证 `BDA_FS_DRIVE_A`；没有公开第二个 drive 常量。
- 只验证同 volume 普通文件重命名，没有验证目录重命名、覆盖已有目标或跨 volume 移动。
- `bda_fs_rmdir()` 只验证非空失败和空目录成功；递归删除必须由应用实现。
- 只命名路径属性的 directory bit；其余属性 bit 和三个时间字段仍保持原始形式。
- 没有验证超长路径、长 GBK 文件名、同时修改同一目录或掉电中的 rename/remove 原子性。
- `FS+0x06c` 的候选 flags 查询和 `FS+0x078` 的 raw media bit 没有文件管理器必需的新增
  语义，因此仍留在研究区，没有为了凑接口数量进入公开 SDK。
