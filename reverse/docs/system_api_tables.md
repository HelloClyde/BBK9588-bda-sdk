# C200 原生 BDA API 表

本表由 `reverse/c200_api_tables.py` 从本地 `C200.bin` 直接读取。
它把 SDK 中已命名的 table offset 映射到 C200 里的 function pointer 地址，供后续 disasm 和注释使用。
未命名 candidate 来自原机 BDA inventory 的高频 offset；candidate 只说明某个 table+offset 组合有 C200 function pointer，不等于 ABI 已确认。

- C200 加载基址：`0x80004000`
- 固件文件：`系统\数据\C200.bin`

## Runtime Table Seeds

C200 会把 `0x80281680` 处的 8 个 word 复制到 `0x81c00000`，原生 BDA 从这里取得 table pointer。

| Table | Runtime slot | C200 table VA | Notes |
| --- | ---: | ---: | --- |
| GUI | `0x81c00004` | `0x80280e60` | window/control/draw table |
| FS | `0x81c00008` | `0x80280dd0` | 文件系统表 |
| SYS | `0x81c0000c` | `0x80280c60` | 系统/设备表 |
| MEM | `0x81c00010` | `0x8028169c` | 内存表 |
| RES | `0x81c00014` | `0x80280d30` | 资源/DLX/trace 表 |

## SDK Named Entries

| Table | Offset | SDK name | entry VA | function VA | in C200 | first insn | Notes |
| --- | ---: | --- | ---: | ---: | --- | --- | --- |
| FS | +0x000 | `BDA_FS_OPEN` | `0x80280dd0` | `0x80170b68` | 是 | `addiu $sp, $sp, -0x28` | fopen-style；原机代码常传 rb/wb 等 mode string。 |
| FS | +0x004 | `BDA_FS_CLOSE` | `0x80280dd4` | `0x8017a928` | 是 | `addiu $sp, $sp, -0x20` | fclose-style；C200 单参数 file，return value 来自内部 close helper。 |
| FS | +0x008 | `BDA_FS_READ` | `0x80280dd8` | `0x8017a978` | 是 | `addiu $sp, $sp, -0x30` | fread-style；C200 参数顺序为 buffer,size,count,file，失败返回 0。 |
| FS | +0x00c | `BDA_FS_WRITE` | `0x80280ddc` | `0x8017ab2c` | 是 | `addiu $sp, $sp, -0x30` | fwrite-style；C200 参数顺序为 buffer,size,count,file，失败返回 0。 |
| FS | +0x010 | `BDA_FS_SEEK` | `0x80280de0` | `0x801712a0` | 是 | `addiu $sp, $sp, -0x30` | fseek-style；C200 参数为 file,offset,whence，无效 whence 返回 -1。 |
| FS | +0x014 | `BDA_FS_TELL` | `0x80280de4` | `0x8017ac18` | 是 | `lh $v1, 0x48($a0)` | ftell-style；C200 检查 file+0x48 index，有效路径返回 file+0x44。 |
| FS | +0x018 | `BDA_FS_EOF_LIKE` | `0x80280de8` | `0x8017ac84` | 是 | `lh $v1, 0x48($a0)` | feof-like；C200 检查 file+0x44 当前位置和 file+0x20 size-like word。 |
| FS | +0x01c | `BDA_FS_ERROR_LIKE` | `0x80280dec` | `0x8017acfc` | 是 | `lh $v1, 0x48($a0)` | ferror-like；C200 检查 file+0x4a 的 0x1000 error flag。 |
| FS | +0x020 | `BDA_FS_CLEAR_ERROR_LIKE` | `0x80280df0` | `0x8017ad70` | 是 | `lh $v1, 0x48($a0)` | clearerr-like；C200 清除 file+0x4a 的 0x1000 error flag。 |
| FS | +0x024 | `BDA_FS_REMOVE` | `0x80280df4` | `0x801717f4` | 是 | `addiu $sp, $sp, -0x28` | remove/unlink；C200 解析单参数 path 后删除文件。 |
| FS | +0x028 | `BDA_FS_RENAME_LIKE` | `0x80280df8` | `0x80171d24` | 是 | `addiu $sp, $sp, -0x30` | rename/move-like；C200 使用 old_path,new_path，分别解析后调用内部 rename helper。 |
| FS | +0x02c | `BDA_FS_CHDIR_LIKE` | `0x80280dfc` | `0x8016fe18` | 是 | `addiu $sp, $sp, -0x40` | chdir/current directory 切换；C200 检查目录属性位 0x4000。 |
| FS | +0x030 | `BDA_FS_MKDIR_LIKE` | `0x80280e00` | `0x80171f8c` | 是 | `addiu $sp, $sp, -0x28` | mkdir-style；C200 解析 path 后调用内部创建目录 helper。 |
| FS | +0x034 | `BDA_FS_RMDIR_LIKE` | `0x80280e04` | `0x80172520` | 是 | `addiu $sp, $sp, -0x28` | rmdir/remove-directory；C200 使用单参数 path，删除空目录。 |
| FS | +0x03c | `BDA_FS_FINDFIRST_LIKE` | `0x80280e0c` | `0x80172630` | 是 | `addiu $sp, $sp, -0x30` | findfirst/search-open；C200 参数为 pattern,attr,find_data，内部申请 0x20a 临时 path buffer。 |
| FS | +0x040 | `BDA_FS_FINDNEXT_LIKE` | `0x80280e10` | `0x8017add4` | 是 | `addiu $sp, $sp, -0x28` | findnext-style；C200 读取 find_data+0x10 index，并调用 0x8017f6b0(find_data)。 |
| FS | +0x044 | `BDA_FS_FINDCLOSE_LIKE` | `0x80280e14` | `0x8017ae90` | 是 | `addiu $sp, $sp, -0x28` | findclose-style；C200 读取 find_data+0x10 index，并释放 find_data+0x00 cursor。 |
| FS | +0x048 | `BDA_FS_DISKINFO_LIKE` | `0x80280e18` | `0x80172754` | 是 | `addiu $sp, $sp, -0x38` | disk/storage 容量查询；C200 只取 drive 低 8 位，确认 0/1 路径，成功写 4 个 word。 |
| FS | +0x050 | `BDA_FS_GETCWD_LIKE` | `0x80280e20` | `0x801700d0` | 是 | `lui $v0, 0x8047` | current directory getter；C200 使用 buffer,size，返回所需 byte 数，写入 A:/B: 前缀路径。 |
| FS | +0x054 | `BDA_FS_PATH_INFO_LIKE` | `0x80280e24` | `0x8017a0d8` | 是 | `addiu $sp, $sp, -0x20` | path info getter；C200 使用 path,info，填充 0x18 byte attr/size/time-like 结构。 |
| FS | +0x06c | `BDA_FS_STAT_LIKE` | `0x80280e3c` | `0x8017a5ec` | 是 | `addiu $sp, $sp, -0x28` | path/flags 存在性或属性检查；C200 只使用 a0/a1，不填充 stat 输出结构。 |
| FS | +0x074 | `BDA_FS_FLUSH_ALL` | `0x80280e44` | `0x8017b0d0` | 是 | `lui $v0, 0x804c` | 全局 open-file flush；无参数，遍历脏 file object 写回数据和 metadata；8013 强制断电 A/B 验证 4096-byte flushed 文件完整、未 flush 对照为 0 byte。 |
| FS | +0x078 | `BDA_FS_MEDIA_PRESENT_RAW_LIKE` | `0x80280e48` | `0x8017952c` | 是 | `addiu $sp, $sp, -0x18` | raw media-present query；C200 无参数，底层读取 0xb0010300 的 media-present bit 后返回 0/1。 |
| FS | +0x07c | `BDA_FS_STORAGE_READY_LIKE` | `0x80280e4c` | `0x801705ec` | 是 | `addiu $sp, $sp, -0x18` | 无参数存储介质就绪查询；C200 返回内部检测结果低 8 位。 |
| GUI | +0x030 | `BDA_GUI_EVENT_POLL_LIKE` | `0x80280e90` | `0x800dbfd0` | 是 | `addiu $sp, $sp, -0x28` | event poll；C200 参数为 message_buffer,frame_or_handle，会填 0x1c byte message packet。 |
| GUI | +0x03c | `BDA_GUI_NOTIFY_LIKE` | `0x80280e9c` | `0x800dced0` | 是 | `lui $t1, 0x8082` | 异步 notify/post；C200 将 handle,message,a,b 写入 frame queue，0xb1 只置 pending flag。 |
| GUI | +0x040 | `BDA_GUI_SEND` | `0x80280ea0` | `0x800dd380` | 是 | `addiu $sp, $sp, -0x18` | 同步 send；C200 直接调用 handle+0x88 wndproc，参数为 handle,message,wparam,lparam。 |
| GUI | +0x04c | `BDA_GUI_FRAME_RELEASE_LIKE` | `0x80280eac` | `0x800dd31c` | 是 | `lui $a1, 0x8082` | frame release/request；C200 解析 handle/default slot 后设置 object 高位状态 flag。 |
| GUI | +0x050 | `BDA_GUI_EVENT_STEP_LIKE` | `0x80280eb0` | `0x800de378` | 是 | `addiu $sp, $sp, -0x20` | event step；C200 读取 a0=message_buffer，只处理 message 0x10/0x13 派生通知。 |
| GUI | +0x054 | `BDA_GUI_EVENT_DISPATCH_LIKE` | `0x80280eb4` | `0x800dd4b8` | 是 | `addiu $sp, $sp, -0x18` | event dispatch；C200 读取 message_buffer 并调用目标 handle 的 +0x88 wndproc。 |
| GUI | +0x074 | `BDA_GUI_PUMP_PRESENT_LIKE` | `0x80280ed4` | `0x800d48a8` | 是 | `addiu $sp, $sp, -0x18` | 绘图/present guard；C200 保存 a0，a0=0 时触发 present/update；缺少原机 surface/context 时 TileBlit 会逐块 flip 后死机。 |
| GUI | +0x07c | `BDA_GUI_OBJECT_FLAGS_CLEAR_LIKE` | `0x80280edc` | `0x800ce4c8` | 是 | `beqz $a0, 0x800ce4e0` | kind=1 object flags clear helper；C200 把 handle+0x24 与 ~mask 相与，成功返回 1。 |
| GUI | +0x080 | `BDA_GUI_OBJECT_FLAGS_OR_LIKE` | `0x80280ee0` | `0x800ce4fc` | 是 | `beqz $a0, 0x800ce514` | kind=1 object flags OR helper；C200 把 mask OR 到 handle+0x24，成功返回 1。 |
| GUI | +0x084 | `BDA_GUI_REGISTER_FRAME_LIKE` | `0x80280ee4` | `0x800cc1c8` | 是 | `addiu $sp, $sp, -0x50` | 注册 frame/window descriptor；C200 读取 0x34 byte descriptor 后创建内部 window object。 |
| GUI | +0x088 | `BDA_GUI_FRAME_STOP_LIKE` | `0x80280ee8` | `0x800ce090` | 是 | `addiu $sp, $sp, -0x20` | 停止 frame/window；C200 只读取 handle，解析 frame 后发送内部 0x66/0xf1 message。 |
| GUI | +0x08c | `BDA_GUI_DEFAULT_PROC_LIKE` | `0x80280eec` | `0x800ca8c0` | 是 | `addiu $v0, $a1, -1` | default window procedure fallback；C200 参数为 handle,message,wparam,lparam。 |
| GUI | +0x098 | `BDA_GUI_FRAME_ACTIVATE_LIKE` | `0x80280ef8` | `0x800cc4ec` | 是 | `addiu $sp, $sp, -0x20` | 激活/状态切换 frame；C200 参数为 handle,mode，mode 0/0x10/0x100 有特殊路径。 |
| GUI | +0x0a4 | `BDA_GUI_OBJECT_RECT_LIKE` | `0x80280f04` | `0x800ce3c8` | 是 | `bnez $a0, 0x800ce408` | object/default client rect 查询；C200 使用 handle,rect，写 16 byte rect，成功返回 1。 |
| GUI | +0x0b0 | `BDA_GUI_OBJECT_FLAGS_GET_LIKE` | `0x80280f10` | `0x800ce4a0` | 是 | `beqz $a0, 0x800ce4b8` | kind=1 object flags getter；C200 读取 handle+0x24，失败返回 0。 |
| GUI | +0x0b8 | `BDA_GUI_OBJECT_USERDATA0_GET_LIKE` | `0x80280f18` | `0x800ce558` | 是 | `beqz $a0, 0x800ce570` | kind=1 object userdata0 getter；C200 读取 handle+0x80，失败返回 0。 |
| GUI | +0x0bc | `BDA_GUI_OBJECT_USERDATA0_SET_LIKE` | `0x80280f1c` | `0x800ce580` | 是 | `beqz $a0, 0x800ce598` | kind=1 object userdata0 setter；C200 写 handle+0x80，返回旧值，失败返回 0。 |
| GUI | +0x0c0 | `BDA_GUI_OBJECT_USERDATA1_GET_LIKE` | `0x80280f20` | `0x800ce5b0` | 是 | `beqz $a0, 0x800ce5c8` | kind=1 object userdata1 getter；C200 读取 handle+0x84，失败返回 0。 |
| GUI | +0x0c4 | `BDA_GUI_OBJECT_USERDATA1_SET_LIKE` | `0x80280f24` | `0x800ce5d8` | 是 | `beqz $a0, 0x800ce5f0` | kind=1 object userdata1 setter；C200 写 handle+0x84，返回旧值，失败返回 0。 |
| GUI | +0x0c8 | `BDA_GUI_OBJECT_PAYLOAD_WORD_GET_LIKE` | `0x80280f28` | `0x800ce608` | 是 | `beqz $a0, 0x800ce620` | subtype=0x12 object payload word getter；C200 读取 handle+0xec 指向 payload 的 +0x1c。 |
| GUI | +0x0cc | `BDA_GUI_OBJECT_PAYLOAD_WORD_SET_LIKE` | `0x80280f2c` | `0x800ce644` | 是 | `move $a2, $zero` | subtype=0x12 object payload word setter；C200 写 payload+0x1c，返回旧值，失败返回 0。 |
| GUI | +0x0d0 | `BDA_GUI_OBJECT_RESOURCE_PTR_GET_LIKE` | `0x80280f30` | `0x800ce7dc` | 是 | `beqz $a0, 0x800ce7f4` | kind=1 object resource pointer getter；C200 读取 handle+0x8c，失败返回 0。 |
| GUI | +0x0d8 | `BDA_GUI_OBJECT_CALLBACK_PTR_GET_LIKE` | `0x80280f38` | `0x800ce780` | 是 | `beqz $a0, 0x800ce798` | kind=1 object callback pointer getter；C200 读取 handle+0x88，失败返回 0。 |
| GUI | +0x0dc | `BDA_GUI_OBJECT_CALLBACK_PTR_SET_LIKE` | `0x80280f3c` | `0x800ce7a8` | 是 | `beqz $a0, 0x800ce7c0` | kind=1 object callback pointer setter；C200 在 value 非 0 时写 handle+0x88，返回旧值。 |
| GUI | +0x0e0 | `BDA_GUI_OBJECT_OP_LIKE` | `0x80280f40` | `0x800ccf64` | 是 | `addiu $sp, $sp, -0x20` | object refresh/notify；C200 只读取 object 并发送内部 0xb1 message。 |
| GUI | +0x0e4 | `BDA_GUI_OBJECT_DRAW_BEGIN_LIKE` | `0x80280f44` | `0x800ce928` | 是 | `addiu $sp, $sp, -0x28` | object draw begin wrapper；C200 检查 object kind，调用 GUI+0x308 取得 draw context 并递增 draw 计数。 |
| GUI | +0x0e8 | `BDA_GUI_OBJECT_DRAW_END_LIKE` | `0x80280f48` | `0x800ce9f0` | 是 | `addiu $sp, $sp, -0x28` | object draw end wrapper；C200 递减 draw 计数并调用 GUI+0x30c(draw_context)，无稳定 return value。 |
| GUI | +0x0f4 | `BDA_GUI_ACCUMULATE_ORIGIN_LIKE` | `0x80280f54` | `0x800ce26c` | 是 | `beqz $a0, 0x800ce280` | 累计 object 父链 origin，把 object 坐标累加到调用者传入的 x/y pointer。 |
| GUI | +0x0f8 | `BDA_GUI_SUBTRACT_ORIGIN_LIKE` | `0x80280f58` | `0x800cc664` | 是 | `beqz $a0, 0x800cc678` | 反向累计 object 父链 origin；C200 从调用者 x/y pointer 中减去 object/parent 的 +0x14/+0x18。 |
| GUI | +0x134 | `BDA_GUI_ACTIVE_FRAME_SET_LIKE` | `0x80280f94` | `0x800cad3c` | 是 | `addiu $sp, $sp, -0x20` | 设置/切换当前 active frame；C200 写内部 +0xd8，并向旧/新 frame 发 0x31/0x30。 |
| GUI | +0x13c | `BDA_GUI_ACTIVE_FRAME_GET_LIKE` | `0x80280f9c` | `0x800cae04` | 是 | `addiu $sp, $sp, -0x18` | 查询 context 所属 frame/container 的 active child；C200 读取 a0，解析 parent 后返回 container+0xd8。 |
| GUI | +0x17c | `BDA_GUI_CLOSE_FRAME_LIKE` | `0x80280fdc` | `0x800cdffc` | 是 | `addiu $sp, $sp, -0x18` | 关闭并释放 frame/window；V11 真机确认应在 stop/release 和 event poll 结束后调用，且无稳定返回值。 |
| GUI | +0x1a4 | `BDA_GUI_CREATE` | `0x80281004` | `0x800ccfac` | 是 | `addiu $sp, $sp, -0x70` | 创建 window/control，class 字符串常见 edit/listbox/medit 等。 |
| GUI | +0x1a8 | `BDA_GUI_DESTROY_LIKE` | `0x80281008` | `0x800cd41c` | 是 | `addiu $sp, $sp, -0x30` | destroy control/object；C200 要求 kind=1 subtype=0x12，先发内部 0x64 再摘链释放。 |
| GUI | +0x1ac | `BDA_GUI_WINDOW_TIMER_START_LIKE` | `0x8028100c` | `0x800de150` | 是 | `addiu $sp, $sp, -0x28` | window timer start；注册 (frame,timer_id,period_ms)，内部消息 0x162，最多 16 个活动记录。 |
| GUI | +0x1b0 | `BDA_GUI_WINDOW_TIMER_STOP_LIKE` | `0x80281010` | `0x800de190` | 是 | `addiu $sp, $sp, -0x28` | window timer stop；按 (frame,timer_id) 注销，内部消息 0x163。 |
| GUI | +0x1b4 | `BDA_GUI_WINDOW_TIMER_EXISTS_LIKE` | `0x80281014` | `0x800de0a8` | 是 | `move $t0, $zero` | window timer exists；扫描 0x804a6b40 timer 表并比较 frame/timer_id。 |
| GUI | +0x1b8 | `BDA_GUI_WINDOW_TIMER_SET_PERIOD_LIKE` | `0x80281018` | `0x800de1c8` | 是 | `addiu $sp, $sp, -0x28` | window timer period raw update；内部消息 0x164；稀疏表存在空指针风险，不公开直调。 |
| GUI | +0x1bc | `BDA_GUI_WINDOW_TIMER_CLOCK_MS_LIKE` | `0x8028101c` | `0x800de144` | 是 | `lui $v0, 0x8047` | window timer scheduler clock；无参数返回 millisecond-valued counter，10 ms 分辨率。 |
| GUI | +0x2b8 | `BDA_GUI_MSGBOX` | `0x80281118` | `0x800c6544` | 是 | `addiu $sp, $sp, -0x28` | message box，hardware probe 已确认可用于简单 BDA demo。 |
| GUI | +0x2fc | `BDA_GUI_DRAW_OBJECT_CREATE_LIKE` | `0x8028115c` | `0x800bd36c` | 是 | `sll $v1, $a0, 2` | draw/resource object table 查询；C200 只读取 kind/index，范围为 0..16。 |
| GUI | +0x300 | `BDA_GUI_DISPLAY_METRIC_LIKE` | `0x80281160` | `0x800bc8fc` | 是 | `addiu $sp, $sp, -0x18` | display backend metric 查询；C200 使用 context,metric，metric 范围 0..6；Thunder 用 metric=6 作为 framebuffer 像素字节因子。 |
| GUI | +0x304 | `BDA_GUI_CURRENT_DRAW_LIKE` | `0x80281164` | `0x800bceec` | 是 | `addiu $sp, $sp, -0x18` | current draw context；C200 读取 handle，从 5 个普通 slot 取/初始化 context，并以 mode=0 调内部 helper；满池扫描存在越界缺陷。 |
| GUI | +0x308 | `BDA_GUI_BEGIN_DRAW_LIKE` | `0x80281168` | `0x800bce50` | 是 | `addiu $sp, $sp, -0x18` | begin draw context；C200 读取 handle，从 5 个普通 slot 取/初始化 context，并以 mode=1 调内部 helper；满池扫描存在越界缺陷。 |
| GUI | +0x30c | `BDA_GUI_END_DRAW_LIKE` | `0x8028116c` | `0x800bd4b0` | 是 | `addiu $sp, $sp, -0x20` | 结束 draw 并归还 fixed context slot；无稳定 return value，必须与 +0x304/+0x308 配对。 |
| GUI | +0x310 | `BDA_GUI_COMPAT_CONTEXT_CREATE_LIKE` | `0x80281170` | `0x800bd100` | 是 | `addiu $sp, $sp, -0x30` | compatible draw context create；C200 分配 0xd4 byte context 并复制 source context 的 drawable bounds/backend；V19 验证可同时创建两块。 |
| GUI | +0x314 | `BDA_GUI_SURFACE_FLUSH_LIKE` | `0x80281174` | `0x800bd584` | 是 | `addiu $sp, $sp, -0x18` | surface/canvas flush 并释放 context；C200 调 backend +0x34 后释放 object；V19 验证两块 compatible surface 可分别释放。 |
| GUI | +0x334 | `BDA_GUI_SET_FILL_COLOR_LIKE` | `0x80281194` | `0x800b2c7c` | 是 | `lui $v1, 0x8082` | 设置 fill color；C200 写 context+0x14 并返回旧值。 |
| GUI | +0x338 | `BDA_GUI_SET_TEXT_MODE_LIKE` | `0x80281198` | `0x800b2c94` | 是 | `lui $v1, 0x8082` | 设置文本模式/背景模式；C200 写 context+0x18 并返回旧值。 |
| GUI | +0x33c | `BDA_GUI_SET_TEXT_COLOR_LIKE` | `0x8028119c` | `0x800b2cac` | 是 | `lui $v1, 0x8082` | 设置文本颜色；C200 写 context+0x50 并返回旧值。 |
| GUI | +0x358 | `BDA_GUI_SELECT_DRAW_OBJECT_LIKE` | `0x802811b8` | `0x800b2d40` | 是 | `lui $v1, 0x8082` | select draw object；C200 把 object 写入 context+0x30 并返回旧值，Thunder 会在绘制后恢复旧 object。 |
| GUI | +0x35c | `BDA_GUI_OBJECT_BIND_LIKE` | `0x802811bc` | `0x800b2d58` | 是 | `lui $v1, 0x8082` | draw context resource/image slot setter；C200 写 context+0x20 并返回旧值。 |
| GUI | +0x368 | `BDA_GUI_PUT_PIXEL_LIKE` | `0x802811c8` | `0x800b68c0` | 是 | `addiu $sp, $sp, -0x48` | 画点/put pixel；C200 使用 context,x,y,color 并经 backend +0xb0 提交。 |
| GUI | +0x36c | `BDA_GUI_PUT_PIXEL_RGB_LIKE` | `0x802811cc` | `0x800b6af8` | 是 | `addiu $sp, $sp, -0x50` | 直接 RGB 画点；C200 使用 context,x,y,r,g,b，转换三个低 8-bit 分量后经 backend +0xb0 提交。 |
| GUI | +0x378 | `BDA_GUI_RGB_LIKE` | `0x802811d8` | `0x800bc2e0` | 是 | `lui $v1, 0x8047` | RGB 颜色构造或转换；C200 使用 a1/a2/a3 低 8 位和 draw/context callback。 |
| GUI | +0x37c | `BDA_GUI_LINE_TO_LIKE` | `0x802811dc` | `0x800b715c` | 是 | `addiu $sp, $sp, -0x50` | line-to primitive；C200 使用 context,x,y，从 context+0x34/+0x38 取旧点，裁剪后调用 line backend。 |
| GUI | +0x380 | `BDA_GUI_MOVE_TO_LIKE` | `0x802811e0` | `0x800bc328` | 是 | `lui $v0, 0x8082` | move-to primitive；C200 使用 context,x,y，写 context+0x34/+0x38。 |
| GUI | +0x384 | `BDA_GUI_POLYLINE_LIKE` | `0x802811e4` | `0x800bc340` | 是 | `addiu $sp, $sp, -0x20` | polyline primitive；C200 使用 context,point_array,count，首点写入 current point，后续点逐个走 line-to。 |
| GUI | +0x388 | `BDA_GUI_CIRCLE_LIKE` | `0x802811e8` | `0x800b7494` | 是 | `addiu $sp, $sp, -0x48` | circle primitive；C200 使用 context,center_x,center_y,radius，并按圆的 bounding rect clipping。 |
| GUI | +0x38c | `BDA_GUI_RECTANGLE_LIKE` | `0x802811ec` | `0x800b76d8` | 是 | `addiu $sp, $sp, -0x50` | rectangle primitive；C200 使用 context,left,top,right,bottom，第五参数从 stack+0x10 读取。 |
| GUI | +0x390 | `BDA_GUI_ELLIPSE_LIKE` | `0x802811f0` | `0x800b7fa0` | 是 | `lui $v0, 0x8082` | ellipse primitive；核心参数为 context,cx,cy,rx,ry,0,0,filled，末项选择 outline/fill backend。 |
| GUI | +0x394 | `BDA_GUI_ARC_LIKE` | `0x802811f4` | `0x800ba660` | 是 | `addiu $sp, $sp, -0x58` | circular arc primitive；参数为 context,cx,cy,start_degrees,end_degrees,radius。 |
| GUI | +0x398 | `BDA_GUI_ROUND_RECT_LIKE` | `0x802811f8` | `0x800ba8dc` | 是 | `addiu $sp, $sp, -0xb8` | center-based rounded rectangle；参数为 context,cx,cy,width,height,corner_rx,corner_ry,filled。 |
| GUI | +0x3a0 | `BDA_GUI_MAP_MODE_GET_LIKE` | `0x80281200` | `0x800bfa40` | 是 | `lui $v1, 0x8082` | logical/device map mode getter；返回 context+0x70。 |
| GUI | +0x3a4 | `BDA_GUI_VIEWPORT_EXTENT_GET_LIKE` | `0x80281204` | `0x800bfa54` | 是 | `lui $v1, 0x8082` | viewport extent getter；复制 context+0x7c/+0x80。 |
| GUI | +0x3a8 | `BDA_GUI_VIEWPORT_ORIGIN_GET_LIKE` | `0x80281208` | `0x800bfa74` | 是 | `lui $v1, 0x8082` | viewport origin getter；复制 context+0x74/+0x78。 |
| GUI | +0x3ac | `BDA_GUI_WINDOW_EXTENT_GET_LIKE` | `0x8028120c` | `0x800bfa94` | 是 | `lui $v1, 0x8082` | window extent getter；复制 context+0x8c/+0x90。 |
| GUI | +0x3b0 | `BDA_GUI_WINDOW_ORIGIN_GET_LIKE` | `0x80281210` | `0x800bfab4` | 是 | `lui $v1, 0x8082` | window origin getter；复制 context+0x84/+0x88。 |
| GUI | +0x3b4 | `BDA_GUI_MAP_MODE_SET_LIKE` | `0x80281214` | `0x800bfad4` | 是 | `beqz $a0, 0x800bfae0` | logical/device map mode setter；写 context+0x70。 |
| GUI | +0x3b8 | `BDA_GUI_VIEWPORT_EXTENT_SET_LIKE` | `0x80281218` | `0x800bfae8` | 是 | `beqz $a0, 0x800bfb00` | viewport extent setter；写 context+0x7c/+0x80。 |
| GUI | +0x3bc | `BDA_GUI_VIEWPORT_ORIGIN_SET_LIKE` | `0x8028121c` | `0x800bfb08` | 是 | `beqz $a0, 0x800bfb20` | viewport origin setter；写 context+0x74/+0x78。 |
| GUI | +0x3c0 | `BDA_GUI_WINDOW_EXTENT_SET_LIKE` | `0x80281220` | `0x800bfb28` | 是 | `beqz $a0, 0x800bfb40` | window extent setter；写 context+0x8c/+0x90。 |
| GUI | +0x3c4 | `BDA_GUI_WINDOW_ORIGIN_SET_LIKE` | `0x80281224` | `0x800bfb48` | 是 | `beqz $a0, 0x800bfb60` | window origin setter；写 context+0x84/+0x88。 |
| GUI | +0x3c8 | `BDA_GUI_DEVICE_TO_LOGICAL_POINT_LIKE` | `0x80281228` | `0x800b6640` | 是 | `beqz $a0, 0x800b66e0` | device-to-logical point 原地转换；先减 context origin，再逆 viewport/window mapping。 |
| GUI | +0x3cc | `BDA_GUI_LOGICAL_TO_DEVICE_POINT_LIKE` | `0x8028122c` | `0x800b66e8` | 是 | `move $a3, $a0` | logical-to-device point 原地转换；先做 viewport/window mapping，再加 context origin。 |
| GUI | +0x3d0 | `BDA_GUI_MAP_DEVICE_TO_LOGICAL_POINT_LIKE` | `0x80281230` | `0x800b6834` | 是 | `lui $t1, 0x8082` | map-only device-to-logical point 原地转换；不处理 context origin。 |
| GUI | +0x3d4 | `BDA_GUI_MAP_LOGICAL_TO_DEVICE_POINT_LIKE` | `0x80281234` | `0x800b67b0` | 是 | `lui $t1, 0x8082` | map-only logical-to-device point 原地转换；不处理 context origin。 |
| GUI | +0x3d8 | `BDA_GUI_CLIP_EXCLUDE_RECT_LIKE` | `0x80281238` | `0x800b5e54` | 是 | `addiu $sp, $sp, -0x48` | exclude clip rect；context,left,top,right,bottom，从当前 region 扣除矩形并拆成最多四个剩余条带。 |
| GUI | +0x3dc | `BDA_GUI_CLIP_UNION_RECT_LIKE` | `0x8028123c` | `0x800b6040` | 是 | `addiu $sp, $sp, -0x40` | union clip rect；context,left,top,right,bottom，去除旧节点重叠后追加新矩形；cached bounds 不随追加扩展。 |
| GUI | +0x3e0 | `BDA_GUI_CLIP_INTERSECT_RECT_LIKE` | `0x80281240` | `0x800b6260` | 是 | `addiu $sp, $sp, -0x30` | intersect clip rect；context,const rect*，逐节点求交并清理空节点，然后重新计算 aggregate bounds。 |
| GUI | +0x3e4 | `BDA_GUI_CLIP_SELECT_RECT_LIKE` | `0x80281244` | `0x800b5c00` | 是 | `addiu $sp, $sp, -0x30` | 矩形 clip select/reset；context,rect_or_null，NULL 清除自定义 region，绘图回退到 context bounds。 |
| GUI | +0x3ec | `BDA_GUI_CLIP_BOUNDS_LIKE` | `0x8028124c` | `0x800b64f0` | 是 | `lui $a2, 0x8082` | 读取 custom clip-region bounds；reset 后返回零矩形哨兵，effective clip 仍回退到 context bounds。 |
| GUI | +0x3f0 | `BDA_GUI_CLIP_CONTAINS_POINT_LIKE` | `0x80281250` | `0x800b6520` | 是 | `addiu $sp, $sp, -0x20` | current clip 点命中测试；C200 使用 context,point，并遍历 clip region 或 fallback bounds。 |
| GUI | +0x3f4 | `BDA_GUI_CLIP_INTERSECTS_RECT_LIKE` | `0x80281254` | `0x800b65ac` | 是 | `addiu $sp, $sp, -0x28` | current clip 矩形相交测试；C200 使用 context,rect，并遍历 clip region 或 fallback bounds。 |
| GUI | +0x3f8 | `BDA_GUI_BLIT_LIKE` | `0x80281258` | `0x800c0ba8` | 是 | `addiu $sp, $sp, -0x20` | framebuffer/region blit；C200 使用 x,y,height,width,buffer 五参数，依赖原机 surface/context，SDK 仅作 unsafe probe。 |
| GUI | +0x3fc | `BDA_GUI_CAPTURE_REGION_ALLOC_LIKE` | `0x8028125c` | `0x800c0bf0` | 是 | `addiu $sp, $sp, -0x30` | screen/backend region capture alloc；C200 使用 x,y,width,height，分配 buffer 后经 backend +0x84 抓取区域。 |
| GUI | +0x400 | `BDA_GUI_BLIT_ALT_LIKE` | `0x80281260` | `0x800c0c90` | 是 | `lui $v1, 0x8047` | 带全局 clip/prepare 的 blit；C200 使用 x,y,height,width,buffer 五参数，TileBlit 真机会逐块 flip 后死机。 |
| GUI | +0x40c | `BDA_GUI_REGION_DRAW_LIKE` | `0x8028126c` | `0x800b2e30` | 是 | `addiu $sp, $sp, -0x50` | region draw/copy；C200 使用 context,x,y,width,height 五参数。 |
| GUI | +0x410 | `BDA_GUI_RENDER_COPY_LIKE` | `0x80281270` | `0x800b3124` | 是 | `addiu $sp, $sp, -0x58` | low-level render/copy helper；C200 使用 context,x,y,width,height,descriptor 六参数。 |
| GUI | +0x414 | `BDA_GUI_RENDER_HELPER_LIKE` | `0x80281274` | `0x800b34c0` | 是 | `lui $v1, 0x8047` | low-level render helper；C200 读取 descriptor、多个 stack 参数并可分配临时 buffer。 |
| GUI | +0x418 | `BDA_GUI_RENDER_FINISH_LIKE` | `0x80281278` | `0x800b3d90` | 是 | `addiu $sp, $sp, -0x60` | 双 context 矩形复制；V19-V21 验证 compatible 合成、0xf81f 洋红透明键和 dirty rect 局部提交；stack+0x14 为 destination，stack+0x20 为 RGB565 color_key；C200knl 真机确认 0 跳过黑色而非禁用色键。 |
| GUI | +0x430 | `BDA_GUI_RECT_PREPARE_LIKE` | `0x80281290` | `0x800c0410` | 是 | `lw $v0, 0x10($sp)` | rect writer；C200 使用 rect,x0,y0,x1,y1 五参数并写入四个 word。 |
| GUI | +0x46c | `BDA_GUI_RECT_CONTAINS_LIKE` | `0x802812cc` | `0x800c0818` | 是 | `lw $v0, ($a0)` | 矩形命中测试，判断点是否落在 x0/y0/x1/y1 范围内。 |
| GUI | +0x4a4 | `BDA_GUI_CURRENT_FONT_LIKE` | `0x80281304` | `0x800bf744` | 是 | `lui $v1, 0x8082` | current font pointer getter；C200 返回 context+0x54，context=0 时使用 default draw context。 |
| GUI | +0x4d0 | `BDA_GUI_FONT_CELL_WIDTH_LIKE` | `0x80281330` | `0x800c1c68` | 是 | `lui $v0, 0x8082` | font cell width-like metric；C200 返回 current font descriptor +0x38。 |
| GUI | +0x4d4 | `BDA_GUI_FONT_CELL_HEIGHT_LIKE` | `0x80281334` | `0x800c1c80` | 是 | `addiu $sp, $sp, -0x20` | font cell height-like metric；C200 查询 primary/fallback font callback 并返回较大值。 |
| GUI | +0x4f0 | `BDA_GUI_DRAW_TEXT_LIKE` | `0x80281350` | `0x800c0d40` | 是 | `addiu $sp, $sp, -0x50` | draw GBK/ASCII text；C200 使用 handle,x,y,text,extra，extra<0 时按 strlen。 |
| GUI | +0x50c | `BDA_GUI_PICTURE_SOURCE_FREE_LIKE` | `0x8028136c` | `0x800c008c` | 是 | `addiu $sp, $sp, -0x18` | 已有 SDK name，仍需 function-level disasm 确认 ABI。 |
| GUI | +0x540 | `BDA_GUI_DRAW_VX_LIKE` | `0x802813a0` | `0x800bb864` | 是 | `addiu $sp, $sp, -0x50` | 绘制完整 VX resource block；C200 从第 6 参数读取 resource，尺寸来自 VX header +0x06/+0x0a。 |
| GUI | +0x5a8 | `BDA_GUI_HELP_PAGE_LIKE` | `0x80281408` | `0x800db8d8` | 是 | `addiu $sp, $sp, -0x80` | 同步系统帮助页；参数为 parent 和 title\r\nbody，8013 已验证裸调用、注册 Frame parent、退出返回和公开 wrapper。 |
| GUI | +0x5d4 | `BDA_GUI_INPUT_PACKET_LIKE` | `0x80281434` | `0x8001b518` | 是 | `addiu $sp, $sp, -0x18` | GAMEBOY/input 按键包 helper；C200 清 6 byte packet 后写入按键状态。 |
| GUI | +0x670 | `BDA_GUI_DECODE_BMP_LIKE` | `0x802814d0` | `0x800e1f74` | 是 | `addiu $sp, $sp, -0x38` | BMP/VX decode；C200 使用 owner,out,path,out_source_buffer，VX 快路径会写回 file buffer pointer。 |
| GUI | +0x6a8 | `BDA_GUI_FILE_SELECTOR_OPEN_LIKE` | `0x80281508` | `0x80021334` | 是 | `addiu $sp, $sp, -0x5e0` | file selector open/session；C200 只读取 a0=mode，内部构造 modal frame。 |
| GUI | +0x6b0 | `BDA_GUI_SCREEN_BUFFER_LIKE` | `0x80281510` | `0x80010d94` | 是 | `lui $v0, 0x8034` | 内部 screen/framebuffer pointer getter；无参数，不是 allocator；正式 API 通过该入口动态取址并校验 KSEG、范围、对齐和方向，不固定物理地址。裸候选返回值不要直接写或自定义 present。 |
| GUI | +0x6b8 | `BDA_GUI_LIST_NTH_LIKE` | `0x80281518` | `0x80042ed8` | 是 | `blez $a1, 0x80042f00` | 链表第 N 项 helper；C200 使用 a0=head、a1=index，不是无参数 selector get。 |
| GUI | +0x6bc | `BDA_GUI_LIST_FREE_LIKE` | `0x8028151c` | `0x80042ebc` | 是 | `addiu $sp, $sp, -0x18` | linked list free helper；C200 将 a0=head 传给 0x8003e868，释放节点和节点 data，不是无参数 selector close。 |
| GUI | +0x6c0 | `BDA_GUI_TOUCH_POSITION_LIKE` | `0x80281520` | `0x8001a3a0` | 是 | `addiu $sp, $sp, -0x58` | raw-to-logical 最新触摸坐标 getter；a0/a1 为 u16 output pointer，结果裁剪到 240x320；FastTouchV3 已在真机高频动态验证，公开为 `bda_gui_touch_position()`。 |
| GUI | +0x6c8 | `BDA_GUI_FILE_SELECTOR_UPDATE_LIKE` | `0x80281528` | `0x80042fec` | 是 | `addiu $sp, $sp, -0x18` | file selector modal run；a0=descriptor，C200 entry 将它原样传给内部 helper。 |
| GUI | +0x6d8 | `BDA_GUI_TICK_COUNT_25MS_LIKE` | `0x80281538` | `0x8012bdb0` | 是 | `lui $v0, 0x8047` | 25 ms raw tick counter；无参数返回 u32，C200 定时 IRQ 递增，BBVM 用无符号差值乘 25 转为毫秒。 |
| GUI | +0x6e0 | `BDA_GUI_GAME_DISPLAY_PUMP_LIKE` | `0x80281540` | `0x8005b844` | 是 | `addiu $sp, $sp, -0x20` | 触摸长按驱动的 game state pump；C200 无参数，先查 pen GPIO，阈值 0x1068 后写全局状态；有副作用。 |
| GUI | +0x714 | `BDA_GUI_MILLISECOND_TIMER_START_LIKE` | `0x80281574` | `0x8001dce0` | 是 | `addiu $sp, $sp, -0x18` | 1 ms timer start；C200 配置 TCU0 为 750 kHz/750 count 并注册 IRQ 0x17；必须与 +0x718 配对。 |
| GUI | +0x718 | `BDA_GUI_MILLISECOND_TIMER_STOP_LIKE` | `0x80281578` | `0x8001ddb0` | 是 | `addiu $sp, $sp, -0x18` | 1 ms timer stop；C200 mask TCU0 并注销 IRQ 0x17；每个成功 start 在退出前调用一次。 |
| GUI | +0x71c | `BDA_GUI_MILLISECOND_COUNT_LIKE` | `0x8028157c` | `0x8001dde0` | 是 | `lui $v0, 0x8047` | 标称 1 ms raw counter；无参数返回 u32，只有 +0x714 start 后才持续递增；V4 在 8013 和真机通过，真机 200 ms 窗口实测 194..200 count。 |
| GUI | +0x72c | `BDA_GUI_STATE_QUERY_LIKE` | `0x8028158c` | `0x8005a2d4` | 是 | `lui $v0, 0x804a` | GAMEBOY 状态查询；C200 table entry 无参数并更新内部状态 word。 |
| GUI | +0x738 | `BDA_GUI_SCREEN_ORIENTATION_LIKE` | `0x80281598` | `0x80024708` | 是 | `jr $ra` | 返回 screen orientation；C200 的 0x130 表示整帧复制需旋转 180 度，0x131 表示正向。 |
| GUI | +0x750 | `BDA_GUI_EVENT_FETCH_LIKE` | `0x802815b0` | `0x8001de5c` | 是 | `addiu $sp, $sp, -0x28` | 全局 raw input event 获取；C200 使用 a0/a1 两个 s32 output pointer；GbTouchEventV1 真机确认 8/12/11 为 touch down/move/up、9/10 为 key down/up，已公开为 `bda_gui_raw_event_fetch()`。code 3 语义未命名，调用方必须有界 drain。 |
| GUI | +0x808 | `BDA_GUI_DECODE_JPEG_LIKE` | `0x80281668` | `0x800e2d2c` | 是 | `addiu $sp, $sp, -0x38` | JPEG decode；C200 使用 owner,out,path,mode，mode 截成 signed 8-bit，mode==1 先做路径/格式检查。 |
| MEM | +0x000 | `BDA_MEM_TRACK_ALLOC_LIKE` | `0x8028169c` | `0x80058574` | 是 | `addiu $sp, $sp, -0x18` | tracked heap alloc；C200 单参数 size，debug tracking 开启时记录 pointer/size。 |
| MEM | +0x004 | `BDA_MEM_TRACK_FREE_LIKE` | `0x802816a0` | `0x80058618` | 是 | `lui $v0, 0x8047` | tracked heap free；C200 单参数 ptr，debug tracking 开启时清记录后释放。 |
| MEM | +0x008 | `BDA_MEM_ALLOC` | `0x802816a4` | `0x80007648` | 是 | `addiu $sp, $sp, -0x20` | 固件堆内存分配/heap alloc；C200 单参数 size，锁保护后返回 pointer。 |
| MEM | +0x00c | `BDA_MEM_FREE` | `0x802816a8` | `0x800067f4` | 是 | `addiu $sp, $sp, -0x20` | 固件堆内存释放；C200 单参数 ptr，锁保护后调用内部 free。 |
| MEM | +0x010 | `BDA_MEM_CALLOC_LIKE` | `0x802816ac` | `0x800065bc` | 是 | `addiu $sp, $sp, -0x28` | firmware heap calloc-like；C200 使用 count,size，按 count*align4(size) 分配并清零。 |
| MEM | +0x014 | `BDA_MEM_REALLOC_LIKE` | `0x802816b0` | `0x800077b0` | 是 | `addiu $sp, $sp, -0x20` | firmware heap realloc-like；C200 使用 ptr,new_size，支持 ptr=0 alloc 和 size=0 free。 |
| MEM | +0x01c | `BDA_MEM_TRACK_BEGIN_LIKE` | `0x802816b8` | `0x80058554` | 是 | `addiu $v0, $zero, 1` | heap tracking begin；C200 使用 free_on_finish flag，开启 tracking 并清记录计数。 |
| MEM | +0x020 | `BDA_MEM_TRACK_REPORT_LIKE` | `0x802816bc` | `0x8005868c` | 是 | `addiu $sp, $sp, -0x20` | heap tracking report/count；C200 使用 summary_only flag，返回 tracked 记录计数。 |
| MEM | +0x024 | `BDA_MEM_TRACK_FINISH_LIKE` | `0x802816c0` | `0x80058750` | 是 | `lui $a3, 0x8047` | heap tracking finish；C200 结束 tracking，free_on_finish 非 0 时可释放记录 pointer。 |
| MEM | +0x028 | `BDA_MEM_TRACK_RETAIN_LIKE` | `0x802816c4` | `0x80058820` | 是 | `addiu $sp, $sp, -0x18` | heap tracking retain；C200 查 tracked record table，命中时递增 refcount-like 字段并返回 pointer。 |
| MEM | +0x02c | `BDA_MEM_TRACK_RELEASE_LIKE` | `0x802816c8` | `0x800588b8` | 是 | `addiu $sp, $sp, -0x18` | heap tracking release；C200 查 tracked record table，递减 refcount-like 字段，归零时释放 pointer。 |
| RES | +0x090 | `BDA_RES_GET_STATE_LIKE` | `0x80280dc0` | `0x80017580` | 是 | `addiu $sp, $sp, -0x50` | 资源/图片状态 snapshot；C200 从 0xb0003004 取状态源，向 out_state 写 7 个 word，无稳定 return value。 |
| RES | +0x094 | `BDA_RES_ENTRY_094_LIKE` | `0x80280dc4` | `0x800098c0` | 是 | `sw $a1, 4($sp)` | trace/log；历史 DLX loader 名称已废弃。 |
| SYS | +0x000 | `BDA_SYS_SESSION_OPEN_LIKE` | `0x80280c60` | `0x80184d30` | 是 | `addiu $sp, $sp, -0x148` | 已有 SDK name，仍需 function-level disasm 确认 ABI。 |
| SYS | +0x004 | `BDA_SYS_CLOSE_LIKE` | `0x80280c64` | `0x80185414` | 是 | `addiu $sp, $sp, -0x240` | 内部 system resource close；C200 使用 resource_id 1..10 查资源表并调用 close callback，不是 app exit。 |
| SYS | +0x014 | `BDA_SYS_SESSION_INIT_WORD_LIKE` | `0x80280c74` | `0x80185be0` | 是 | `addiu $sp, $sp, -0x20` | 已有 SDK name，仍需 function-level disasm 确认 ABI。 |
| SYS | +0x018 | `BDA_SYS_SESSION_OP18_LIKE` | `0x80280c78` | `0x80187c5c` | 是 | `addiu $a0, $a0, -1` | 已有 SDK name，仍需 function-level disasm 确认 ABI。 |
| SYS | +0x01c | `BDA_SYS_SESSION_OP1C_LIKE` | `0x80280c7c` | `0x80187d10` | 是 | `addiu $a0, $a0, -1` | 已有 SDK name，仍需 function-level disasm 确认 ABI。 |
| SYS | +0x020 | `BDA_SYS_SESSION_STOP_LIKE` | `0x80280c80` | `0x80185d34` | 是 | `addiu $sp, $sp, -0x20` | 已有 SDK name，仍需 function-level disasm 确认 ABI。 |
| SYS | +0x02c | `BDA_SYS_SESSION_STATUS_LIKE` | `0x80280c8c` | `0x80185e20` | 是 | `addiu $sp, $sp, -0x68` | 已有 SDK name，仍需 function-level disasm 确认 ABI。 |
| SYS | +0x040 | `BDA_SYS_AUDIO_ATTENUATION_SET_LIKE` | `0x80280ca0` | `0x8018921c` | 是 | `slti $v0, $a0, 0` | raw PCM attenuation setter；C200 clamp 到 0..98，写 pending value，下一次 audio write 量化并应用。 |
| SYS | +0x044 | `BDA_SYS_AUDIO_ATTENUATION_GET_LIKE` | `0x80280ca4` | `0x80189248` | 是 | `addiu $sp, $sp, -0x18` | raw PCM attenuation getter；C200 无参数，返回当前 effective attenuation（0..96，步进 3）。 |
| SYS | +0x058 | `BDA_SYS_PACKAGE_SOUND_OP58_LIKE` | `0x80280cb8` | `0x8018ecb4` | 是 | `lui $v0, 0x804c` | 打包音效 init/start；C200 使用 a0=descriptor，成功置 0x804c4ba4 并返回 1。 |
| SYS | +0x05c | `BDA_SYS_PACKAGE_SOUND_OP5C_LIKE` | `0x80280cbc` | `0x8018e958` | 是 | `addiu $sp, $sp, -0x28` | 打包音效 descriptor 操作；C200 使用 slot,descriptor,a2,flags 四参数。 |
| SYS | +0x060 | `BDA_SYS_PACKAGE_SOUND_OP60_LIKE` | `0x80280cc0` | `0x8018ee98` | 是 | `lui $v0, 0x804c` | 打包音效状态置位；C200 无参数，0x804c4ba8 从 0 置 1 时返回 1。 |
| SYS | +0x064 | `BDA_SYS_PACKAGE_SOUND_OP64_LIKE` | `0x80280cc4` | `0x8018eed0` | 是 | `lui $v0, 0x804c` | 打包音效状态清除；C200 无参数，0x804c4ba8 从 1 清 0 时返回 1。 |
| SYS | +0x068 | `BDA_SYS_PACKAGE_SOUND_OP68_LIKE` | `0x80280cc8` | `0x8018ee18` | 是 | `lui $v0, 0x804c` | 打包音效 release/stop；C200 无参数，关闭全局 handle 并清 0x804c4ba4。 |
| SYS | +0x06c | `BDA_SYS_AUDIO_OPEN_LIKE` | `0x80280ccc` | `0x80194654` | 是 | `addiu $sp, $sp, -0x30` | raw audio open/init；C200 使用 device,format,channels 三参数，format/channels 截成 signed 8-bit，尾部固定 v0=0。 |
| SYS | +0x074 | `BDA_SYS_AUDIO_READY_LIKE` | `0x80280cd4` | `0x80194da4` | 是 | `addiu $sp, $sp, -0x18` | raw audio ready query；C200 无参数，返回 0x8058+0x6e8 > 0。 |
| SYS | +0x078 | `BDA_SYS_AUDIO_WRITE_LIKE` | `0x80280cd8` | `0x80194320` | 是 | `addiu $sp, $sp, -0x48` | raw audio write；C200 使用 buffer,bytes，bytes<=0 返回 -1，正常返回已消费 byte 数。 |
| SYS | +0x080 | `BDA_SYS_DELAY_LIKE` | `0x80280ce0` | `0x800043a0` | 是 | `lui $v1, 0x8047` | 阻塞式 busy-wait delay；C200 按系统校准值把 a0 换算成循环次数，无稳定 return value。 |
| SYS | +0x088 | `BDA_SYS_KEYCODE_RAW_LIKE` | `0x80280ce8` | `0x8001b464` | 是 | `addiu $sp, $sp, -0x18` | raw keycode query；C200 无参数，读取硬件输入寄存器并返回 raw code。 |
| SYS | +0x08c | `BDA_SYS_AUDIO_RESET_LIKE` | `0x80280cec` | `0x8001dc04` | 是 | `addiu $sp, $sp, -0x18` | raw audio reset/init；C200 无参数，关闭全局 audio object 后进入初始化路径，无稳定 return value。 |
| SYS | +0x090 | `BDA_SYS_AUDIO_STATE_LIKE` | `0x80280cf0` | `0x8001dad4` | 是 | `lui $v0, 0x8036` | raw audio state pointer getter；C200 无参数，直接返回全局 state 0x80362830。 |
| SYS | +0x09c | `BDA_SYS_TIMER_LIKE` | `0x80280cfc` | `0x80022dd0` | 是 | `slti $a1, $a0, 0xf` | timer/rate preset 选择；C200 把 a0 clamp 到 0..14 后查内部表，无稳定 return value。 |
| SYS | +0x0a0 | `BDA_SYS_AUDIO_FLUSH_LIKE` | `0x80280d00` | `0x801891e8` | 是 | `addiu $sp, $sp, -0x18` | raw audio finish/stop；C200 无参数，真机安全返回且停止声音；模拟器后端 timer 状态存在差异，无稳定 return value。 |
| SYS | +0x0ac | `BDA_SYS_ALARM_SET_LIKE` | `0x80280d0c` | `0x80016294` | 是 | `addiu $sp, $sp, -0x1080` | alarm set；C200 使用 alarm_data,slot，record size 0x2b8，未见 slot bounds check，return value 成功 1。 |
| SYS | +0x0b0 | `BDA_SYS_ALARM_GET_LIKE` | `0x80280d10` | `0x800163d8` | 是 | `addiu $sp, $sp, -0xdc0` | alarm get；C200 使用 alarm_data,slot，从 file offset 0x578+slot*0x2b8 复制 0x2b8 byte，return value 成功 1。 |
| SYS | +0x0b8 | `BDA_SYS_ALARM_DUE_GET_LIKE` | `0x80280d18` | `0x80015014` | 是 | `addiu $sp, $sp, -0x2990` | alarm due record get；C200 打开 alarm.db，扫描 0x2b8 byte record，并向 out buffer 复制整条 record。 |

## 使用建议

- `function VA` 可用 `C200_LOAD_BASE=0x80004000` 转换成 file offset：`file_off = va - 0x80004000`。
- `C200 内=否` 的项可能是 null pointer、外部 RAM table，或当前 offset 并非该表稳定成员，不能直接当作已确认 API。
- function-level ABI 仍要结合原机 BDA call site、寄存器/stack 参数和真机/emu probe 确认。

## Unnamed Hot Offset C200 Candidates

下表读取 inventory 高频 offset，并在尚未命名的 runtime table entry 中查同 offset 的 function pointer。
因为 inventory 的 offset 统计未区分 table，本表只用于 disasm 导航；同一 offset 在某张 table 已命名，不代表其他 table 的同 offset 也已确认。

| Offset | Raw calls same offset | App count | Candidate table | entry VA | function VA | first insn | Candidate status |
| ---: | ---: | ---: | --- | ---: | ---: | --- | --- |
| +0x040 | 5702 | 52 | RES | `0x80280d70` | `0x80142f50` | `lui $v0, 0x804b` | 已分析为内置 resource/cache 打开路径，失败时可能弹 message box，不公开 wrapper。 |
| +0x008 | 2658 | 54 | GUI | `0x80280e68` | `0x800dbd90` | `addiu $sp, $sp, -0x18` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x008 | 2658 | 54 | SYS | `0x80280c68` | `0x80185628` | `addiu $sp, $sp, -0x28` | 已分析为 10-slot system resource scheduler/tick helper，不公开 wrapper。 |
| +0x008 | 2658 | 54 | RES | `0x80280d38` | `0x8013bb40` | `lui $v0, 0x804b` | 已分析为 resource manager cleanup，会释放全局 buffer/file handle，不公开 wrapper。 |
| +0x00c | 2412 | 54 | GUI | `0x80280e6c` | `0x800dbe90` | `addiu $sp, $sp, -0x18` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x00c | 2412 | 54 | SYS | `0x80280c6c` | `0x80185814` | `addiu $sp, $sp, -0x70` | 已分析为 system resource scheduler helper，含 busy-wait，不公开 wrapper。 |
| +0x00c | 2412 | 54 | RES | `0x80280d3c` | `0x8013bc10` | `addiu $sp, $sp, -0x18` | 已分析为 resource descriptor/global state 写入 helper，不公开 wrapper。 |
| +0x010 | 2043 | 54 | GUI | `0x80280e70` | `0x800de690` | `addiu $sp, $sp, -0x40` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x010 | 2043 | 54 | SYS | `0x80280c70` | `0x801859f0` | `addiu $sp, $sp, -0x60` | 已分析为 system resource slot state 写入 helper，不公开 wrapper。 |
| +0x010 | 2043 | 54 | RES | `0x80280d40` | `0x8013e018` | `lui $v0, 0x804b` | 已分析为 resource manager close/cleanup helper，不公开 wrapper。 |
| +0x094 | 1987 | 54 | GUI | `0x80280ef4` | `0x800ce150` | `addiu $sp, $sp, -0x20` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x094 | 1987 | 54 | FS | `0x80280e64` | `0x800d4950` | `lui $t0, 0x8082` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x094 | 1987 | 54 | SYS | `0x80280cf4` | `0x8001dae0` | `addiu $sp, $sp, -0x20` | 已分析为 raw audio state 写入 helper，不是 high-level setter/restore。 |
| +0x000 | 1858 | 54 | GUI | `0x80280e60` | `0x800d3800` | `addiu $sp, $sp, -0x80` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x000 | 1858 | 54 | RES | `0x80280d30` | `0x8013dfe4` | `lui $at, 0x8047` | 已分析为 resource manager 全局 reset，普通 BDA 不应公开调用。 |
| +0x03c | 1530 | 54 | SYS | `0x80280c9c` | `0x80189264` | `sll $a0, $a0, 0x10` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x03c | 1530 | 54 | RES | `0x80280d6c` | `0x80143224` | `addiu $sp, $sp, -0x38` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x540 | 1208 | 40 | FS | `0x80281310` | `0x80128240` | `jr $ra` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x540 | 1208 | 40 | SYS | `0x802811a0` | `0x800b2cc4` | `lui $v1, 0x8082` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x540 | 1208 | 40 | RES | `0x80281270` | `0x800b3124` | `addiu $sp, $sp, -0x58` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x004 | 1178 | 54 | GUI | `0x80280e64` | `0x800d4950` | `lui $t0, 0x8082` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x004 | 1178 | 54 | RES | `0x80280d34` | `0x8013aaf0` | `addiu $sp, $sp, -0x30` | 已分析为 resource manager 文件/cache 路径，不是 DLX loader，不公开 wrapper。 |
| +0x308 | 1174 | 37 | FS | `0x802810d8` | `0x800c6054` | `addiu $sp, $sp, -0x18` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x308 | 1174 | 37 | SYS | `0x80280f68` | `0x800cdaac` | `lh $v1, ($a0)` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x308 | 1174 | 37 | RES | `0x80281038` | `0x800c4ed8` | `addiu $sp, $sp, -0x30` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x4f0 | 1087 | 46 | FS | `0x802812c0` | `0x800c0758` | `lw $v1, ($a0)` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x4f0 | 1087 | 46 | SYS | `0x80281150` | `0x800d3530` | `addiu $sp, $sp, -0x28` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x4f0 | 1087 | 46 | RES | `0x80281220` | `0x800bfb28` | `beqz $a0, 0x800bfb40` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x30c | 1063 | 45 | FS | `0x802810dc` | `0x800c5880` | `addiu $sp, $sp, -0x48` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x30c | 1063 | 45 | SYS | `0x80280f6c` | `0x800cda88` | `beqz $a0, 0x800cdaa0` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x30c | 1063 | 45 | RES | `0x8028103c` | `0x800c50c0` | `addiu $sp, $sp, -0x18` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x0e0 | 985 | 49 | FS | `0x80280eb0` | `0x800de378` | `addiu $sp, $sp, -0x20` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x0e0 | 985 | 49 | SYS | `0x80280d40` | `0x8013e018` | `lui $v0, 0x804b` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x0e0 | 985 | 49 | RES | `0x80280e10` | `0x8017add4` | `addiu $sp, $sp, -0x28` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x030 | 784 | 54 | SYS | `0x80280c90` | `0x80187eb4` | `addiu $a0, $a0, -1` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x030 | 784 | 54 | RES | `0x80280d60` | `0x80146824` | `addiu $sp, $sp, -0x458` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x2fc | 780 | 46 | FS | `0x802810cc` | `0x800c608c` | `addiu $sp, $sp, -0x20` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x2fc | 780 | 46 | SYS | `0x80280f5c` | `0x800ce354` | `beqz $a0, 0x800ce368` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x2fc | 780 | 46 | RES | `0x8028102c` | `0x800cec50` | `addiu $sp, $sp, -0x18` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x33c | 580 | 44 | FS | `0x8028110c` | `0x800c643c` | `addiu $sp, $sp, -0x20` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x33c | 580 | 44 | SYS | `0x80280f9c` | `0x800cae04` | `addiu $sp, $sp, -0x18` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x33c | 580 | 44 | RES | `0x8028106c` | `0x800c681c` | `addiu $sp, $sp, -0x30` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x050 | 557 | 53 | SYS | `0x80280cb0` | `0x8018ef04` | `jr $ra` | 已确认 ret1/stub，不是 loader 或 runtime init API，不公开 wrapper。 |
| +0x050 | 557 | 53 | RES | `0x80280d80` | `0x80161af0` | `addiu $sp, $sp, -0x98` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x054 | 554 | 53 | SYS | `0x80280cb4` | `0x8018ef0c` | `jr $ra` | 已确认 ret1/stub，不是 loader 或 runtime init API，不公开 wrapper。 |
| +0x054 | 554 | 53 | RES | `0x80280d84` | `0x80149748` | `addiu $sp, $sp, -0x80` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x378 | 535 | 43 | FS | `0x80281148` | `0x800d33b8` | `lw $v0, 0x10($a0)` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x378 | 535 | 43 | SYS | `0x80280fd8` | `0x800cdf5c` | `addiu $v0, $zero, 1` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x378 | 535 | 43 | RES | `0x802810a8` | `0x800c7af4` | `lh $v1, ($a0)` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x084 | 533 | 53 | SYS | `0x80280ce4` | `0x8001b6a8` | `addiu $sp, $sp, -0x18` | 已分析为内部 helper，只调用固定子过程，不是 input reset/init/poll。 |
| +0x0e4 | 512 | 51 | FS | `0x80280eb4` | `0x800dd4b8` | `addiu $sp, $sp, -0x18` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x0e4 | 512 | 51 | SYS | `0x80280d44` | `0x8013bd58` | `lui $a1, 0x8047` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x0e4 | 512 | 51 | RES | `0x80280e14` | `0x8017ae90` | `addiu $sp, $sp, -0x28` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x46c | 505 | 33 | FS | `0x8028123c` | `0x800b6040` | `addiu $sp, $sp, -0x40` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x46c | 505 | 33 | SYS | `0x802810cc` | `0x800c608c` | `addiu $sp, $sp, -0x20` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x46c | 505 | 33 | RES | `0x8028119c` | `0x800b2cac` | `lui $v1, 0x8082` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x338 | 486 | 45 | FS | `0x80281108` | `0x800c63ec` | `addiu $sp, $sp, -0x18` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x338 | 486 | 45 | SYS | `0x80280f98` | `0x800cd8d4` | `addiu $sp, $sp, -0x18` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x338 | 486 | 45 | RES | `0x80281068` | `0x800c65c0` | `addiu $sp, $sp, -0x48` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x0e8 | 483 | 51 | FS | `0x80280eb8` | `0x800dcc08` | `lui $t1, 0x8082` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x0e8 | 483 | 51 | SYS | `0x80280d48` | `0x8013c278` | `addiu $sp, $sp, -0x20` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x0e8 | 483 | 51 | RES | `0x80280e18` | `0x80172754` | `addiu $sp, $sp, -0x38` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x17c | 483 | 53 | FS | `0x80280f4c` | `0x800cd620` | `addiu $sp, $sp, -0x28` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x17c | 483 | 53 | SYS | `0x80280ddc` | `0x8017ab2c` | `addiu $sp, $sp, -0x30` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x17c | 483 | 53 | RES | `0x80280eac` | `0x800dd31c` | `lui $a1, 0x8082` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x1a8 | 474 | 47 | FS | `0x80280f78` | `0x800ce738` | `beqz $a0, 0x800ce750` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x1a8 | 474 | 47 | SYS | `0x80280e08` | `0x80172908` | `addiu $sp, $sp, -0x258` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x1a8 | 474 | 47 | RES | `0x80280ed8` | `0x800d48f4` | `lui $v0, 0x8047` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x080 | 415 | 32 | FS | `0x80280e50` | `0x8017a708` | `addiu $sp, $sp, -0x38` | 已定位但不公开：FS 内部状态/helper，普通 BDA 不应直接调用。 |
| +0x08c | 399 | 54 | RES | `0x80280dbc` | `0x8001680c` | `addiu $sp, $sp, -0x2e8` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x2b8 | 382 | 44 | FS | `0x80281088` | `0x800c7df0` | `addiu $sp, $sp, -0x20` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x2b8 | 382 | 44 | SYS | `0x80280f18` | `0x800ce558` | `beqz $a0, 0x800ce570` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x2b8 | 382 | 44 | RES | `0x80280fe8` | `0x800d49d0` | `sll $v1, $a0, 2` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x134 | 353 | 49 | FS | `0x80280f04` | `0x800ce3c8` | `bnez $a0, 0x800ce408` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x134 | 353 | 49 | SYS | `0x80280d94` | `0x801489a0` | `addiu $sp, $sp, -0x28` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x134 | 353 | 49 | RES | `0x80280e64` | `0x800d4950` | `lui $t0, 0x8082` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x0b8 | 350 | 27 | FS | `0x80280e88` | `0x800a81b0` | `addiu $sp, $sp, -0x40` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x0b8 | 350 | 27 | RES | `0x80280de8` | `0x8017ac84` | `lh $v1, 0x48($a0)` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x1b0 | 344 | 28 | FS | `0x80280f80` | `0x800cdb28` | `addiu $sp, $sp, -0x18` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x1b0 | 344 | 28 | SYS | `0x80280e10` | `0x8017add4` | `addiu $sp, $sp, -0x28` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x1b0 | 344 | 28 | RES | `0x80280ee0` | `0x800ce4fc` | `beqz $a0, 0x800ce514` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x04c | 328 | 53 | FS | `0x80280e1c` | `0x80170078` | `addiu $sp, $sp, -0x18` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x04c | 328 | 53 | SYS | `0x80280cac` | `0x801895dc` | `jr $ra` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x04c | 328 | 53 | RES | `0x80280d7c` | `0x8015c800` | `addiu $sp, $sp, -0x18` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x044 | 305 | 27 | GUI | `0x80280ea4` | `0x800dd3c0` | `addiu $sp, $sp, -0x28` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x044 | 305 | 27 | RES | `0x80280d74` | `0x80148248` | `lui $v0, 0x804b` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x024 | 281 | 26 | GUI | `0x80280e84` | `0x800dece4` | `addiu $sp, $sp, -0x30` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x024 | 281 | 26 | SYS | `0x80280c84` | `0x80187df8` | `jr $ra` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x024 | 281 | 26 | RES | `0x80280d54` | `0x80148a74` | `andi $a0, $a0, 0xff` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x048 | 268 | 38 | GUI | `0x80280ea8` | `0x800dd2dc` | `addiu $sp, $sp, -0x38` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x048 | 268 | 38 | SYS | `0x80280ca8` | `0x801895d4` | `jr $ra` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x048 | 268 | 38 | RES | `0x80280d78` | `0x8015c7b8` | `addiu $sp, $sp, -0x30` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x3f8 | 256 | 27 | FS | `0x802811c8` | `0x800b68c0` | `addiu $sp, $sp, -0x48` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x3f8 | 256 | 27 | SYS | `0x80281058` | `0x800c53f8` | `lw $v0, 0x7c($a0)` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x3f8 | 256 | 27 | RES | `0x80281128` | `0x800d2ce0` | `addiu $sp, $sp, -0x18` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x368 | 249 | 16 | FS | `0x80281138` | `0x800d3418` | `addiu $sp, $sp, -0x28` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x368 | 249 | 16 | SYS | `0x80280fc8` | `0x800cb088` | `addiu $sp, $sp, -0x38` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
| +0x368 | 249 | 16 | RES | `0x80281098` | `0x800c6de4` | `addiu $sp, $sp, -0x58` | 未分类 candidate：只能作为 disasm 导航，不能当作 SDK API。 |
