# BDA API 覆盖表

本表由 `reverse/bda_api_catalog.py` 生成，合并了 `reverse/reports/bda_inventory.json` 的原机 BDA call inventory 和 `reverse/bda_research_sdk.h` 里的 SDK 命名。

注意：inventory 里的 offset 统计是未分类的 indirect call offset，不能单独证明属于 GUI/FS/SYS/MEM/RES 哪张 table；table name 来自 SDK 已命名项和人工逆向笔记。
因此表中的统计列表示“同 offset 在原机 BDA 中出现的总体热度”，不是该 table entry 已经独占确认的调用次数。

| Table | Offset | SDK name | Raw calls same offset | App count | Confidence | Notes |
| --- | ---: | --- | ---: | ---: | --- | --- |
| FS | +0x000 | `BDA_FS_OPEN` | 1858 | 54 | 较高 | fopen-style；原机代码常传 rb/wb 等 mode string。 |
| FS | +0x004 | `BDA_FS_CLOSE` | 1178 | 54 | 较高 | fclose-style；C200 单参数 file，return value 来自内部 close helper。 |
| FS | +0x008 | `BDA_FS_READ` | 2658 | 54 | 较高 | fread-style；C200 参数顺序为 buffer,size,count,file，失败返回 0。 |
| FS | +0x00c | `BDA_FS_WRITE` | 2412 | 54 | 较高 | fwrite-style；C200 参数顺序为 buffer,size,count,file，失败返回 0。 |
| FS | +0x010 | `BDA_FS_SEEK` | 2043 | 54 | 中 | fseek-style；C200 参数为 file,offset,whence，无效 whence 返回 -1。 |
| FS | +0x014 | `BDA_FS_TELL` | 156 | 34 | 中 | ftell-style；C200 检查 file+0x48 index，有效路径返回 file+0x44。 |
| FS | +0x018 | `BDA_FS_EOF_LIKE` | 108 | 23 | 中 | feof-like；C200 检查 file+0x44 当前位置和 file+0x20 size-like word。 |
| FS | +0x01c | `BDA_FS_ERROR_LIKE` | 95 | 16 | 中 | ferror-like；C200 检查 file+0x4a 的 0x1000 error flag。 |
| FS | +0x020 | `BDA_FS_CLEAR_ERROR_LIKE` | 217 | 23 | 中 | clearerr-like；C200 清除 file+0x4a 的 0x1000 error flag。 |
| FS | +0x024 | `BDA_FS_REMOVE` | 281 | 26 | 中 | remove/unlink；C200 解析单参数 path 后删除文件。 |
| FS | +0x028 | `BDA_FS_RENAME_LIKE` | 108 | 20 | 中 | rename/move-like；C200 使用 old_path,new_path，分别解析后调用内部 rename helper。 |
| FS | +0x02c | `BDA_FS_CHDIR_LIKE` | 126 | 30 | 中 | chdir/current directory 切换；C200 检查目录属性位 0x4000。 |
| FS | +0x030 | `BDA_FS_MKDIR_LIKE` | 784 | 54 | 中 | mkdir-style；C200 解析 path 后调用内部创建目录 helper。 |
| FS | +0x034 | `BDA_FS_RMDIR_LIKE` | 10 | 3 | 中 | rmdir/remove-directory；C200 使用单参数 path，删除空目录。 |
| FS | +0x03c | `BDA_FS_FINDFIRST_LIKE` | 1530 | 54 | 中 | findfirst/search-open；C200 参数为 pattern,attr,find_data，内部申请 0x20a 临时 path buffer。 |
| FS | +0x040 | `BDA_FS_FINDNEXT_LIKE` | 5702 | 52 | 中 | findnext-style；C200 读取 find_data+0x10 index，并调用 0x8017f6b0(find_data)。 |
| FS | +0x044 | `BDA_FS_FINDCLOSE_LIKE` | 305 | 27 | 中 | findclose-style；C200 读取 find_data+0x10 index，并释放 find_data+0x00 cursor。 |
| FS | +0x048 | `BDA_FS_DISKINFO_LIKE` | 268 | 38 | 中 | disk/storage 容量查询；C200 只取 drive 低 8 位，确认 0/1 路径，成功写 4 个 word。 |
| FS | +0x050 | `BDA_FS_GETCWD_LIKE` | 557 | 53 | 中 | current directory getter；C200 使用 buffer,size，返回所需 byte 数，写入 A:/B: 前缀路径。 |
| FS | +0x054 | `BDA_FS_PATH_INFO_LIKE` | 554 | 53 | 中 | path info getter；C200 使用 path,info，填充 0x18 byte attr/size/time-like 结构。 |
| FS | +0x06c | `BDA_FS_STAT_LIKE` | 97 | 10 | 中 | path/flags 存在性或属性检查；C200 只使用 a0/a1，不填充 stat 输出结构。 |
| FS | +0x074 | `BDA_FS_FLUSH_ALL` | 2462 | 51 | 中 | 全局 open-file flush；无参数，遍历脏 file object 写回数据和 metadata；8013 强制断电 A/B 验证 4096-byte flushed 文件完整、未 flush 对照为 0 byte。 |
| FS | +0x078 | `BDA_FS_MEDIA_PRESENT_RAW_LIKE` | 11 | 7 | 中 | raw media-present query；C200 无参数，底层读取 0xb0010300 的 media-present bit 后返回 0/1。 |
| FS | +0x07c | `BDA_FS_STORAGE_READY_LIKE` | 105 | 20 | 中 | 无参数存储介质就绪查询；C200 返回内部检测结果低 8 位。 |
| GUI | +0x030 | `BDA_GUI_EVENT_POLL_LIKE` | 784 | 54 | 中 | event poll；C200 参数为 message_buffer,frame_or_handle，会填 0x1c byte message packet。 |
| GUI | +0x03c | `BDA_GUI_NOTIFY_LIKE` | 1530 | 54 | 中 | 异步 notify/post；C200 将 handle,message,a,b 写入 frame queue，0xb1 只置 pending flag。 |
| GUI | +0x040 | `BDA_GUI_SEND` | 5702 | 52 | 中 | 同步 send；C200 直接调用 handle+0x88 wndproc，参数为 handle,message,wparam,lparam。 |
| GUI | +0x04c | `BDA_GUI_FRAME_RELEASE_LIKE` | 328 | 53 | 中 | frame release/request；C200 解析 handle/default slot 后设置 object 高位状态 flag。 |
| GUI | +0x050 | `BDA_GUI_EVENT_STEP_LIKE` | 557 | 53 | 中 | event step；C200 读取 a0=message_buffer，只处理 message 0x10/0x13 派生通知。 |
| GUI | +0x054 | `BDA_GUI_EVENT_DISPATCH_LIKE` | 554 | 53 | 中 | event dispatch；C200 读取 message_buffer 并调用目标 handle 的 +0x88 wndproc。 |
| GUI | +0x074 | `BDA_GUI_PUMP_PRESENT_LIKE` | 2462 | 51 | 中 | 绘图/present guard；C200 保存 a0，a0=0 时触发 present/update；缺少原机 surface/context 时 TileBlit 会逐块 flip 后死机。 |
| GUI | +0x07c | `BDA_GUI_OBJECT_FLAGS_CLEAR_LIKE` | 105 | 20 | 中 | kind=1 object flags clear helper；C200 把 handle+0x24 与 ~mask 相与，成功返回 1。 |
| GUI | +0x080 | `BDA_GUI_OBJECT_FLAGS_OR_LIKE` | 415 | 32 | 中 | kind=1 object flags OR helper；C200 把 mask OR 到 handle+0x24，成功返回 1。 |
| GUI | +0x084 | `BDA_GUI_REGISTER_FRAME_LIKE` | 533 | 53 | 中 | 注册 frame/window descriptor；C200 读取 0x34 byte descriptor 后创建内部 window object。 |
| GUI | +0x088 | `BDA_GUI_FRAME_STOP_LIKE` | 344 | 53 | 中 | 停止 frame/window；C200 只读取 handle，解析 frame 后发送内部 0x66/0xf1 message。 |
| GUI | +0x08c | `BDA_GUI_DEFAULT_PROC_LIKE` | 399 | 54 | 中 | default window procedure fallback；C200 参数为 handle,message,wparam,lparam。 |
| GUI | +0x098 | `BDA_GUI_FRAME_ACTIVATE_LIKE` | 93 | 22 | 中 | 激活/状态切换 frame；C200 参数为 handle,mode，mode 0/0x10/0x100 有特殊路径。 |
| GUI | +0x0a4 | `BDA_GUI_OBJECT_RECT_LIKE` | 30 | 10 | 中 | object/default client rect 查询；C200 使用 handle,rect，写 16 byte rect，成功返回 1。 |
| GUI | +0x0b0 | `BDA_GUI_OBJECT_FLAGS_GET_LIKE` | 7 | 2 | 中 | kind=1 object flags getter；C200 读取 handle+0x24，失败返回 0。 |
| GUI | +0x0b8 | `BDA_GUI_OBJECT_USERDATA0_GET_LIKE` | 350 | 27 | 中 | kind=1 object userdata0 getter；C200 读取 handle+0x80，失败返回 0。 |
| GUI | +0x0bc | `BDA_GUI_OBJECT_USERDATA0_SET_LIKE` | 34 | 7 | 中 | kind=1 object userdata0 setter；C200 写 handle+0x80，返回旧值，失败返回 0。 |
| GUI | +0x0c0 | `BDA_GUI_OBJECT_USERDATA1_GET_LIKE` | 16 | 1 | 中 | kind=1 object userdata1 getter；C200 读取 handle+0x84，失败返回 0。 |
| GUI | +0x0c4 | `BDA_GUI_OBJECT_USERDATA1_SET_LIKE` | 2 | 1 | 中 | kind=1 object userdata1 setter；C200 写 handle+0x84，返回旧值，失败返回 0。 |
| GUI | +0x0c8 | `BDA_GUI_OBJECT_PAYLOAD_WORD_GET_LIKE` | 28 | 3 | 中 | subtype=0x12 object payload word getter；C200 读取 handle+0xec 指向 payload 的 +0x1c。 |
| GUI | +0x0cc | `BDA_GUI_OBJECT_PAYLOAD_WORD_SET_LIKE` | 4 | 2 | 中 | subtype=0x12 object payload word setter；C200 写 payload+0x1c，返回旧值，失败返回 0。 |
| GUI | +0x0d0 | `BDA_GUI_OBJECT_RESOURCE_PTR_GET_LIKE` | 0 | 0 | 中 | kind=1 object resource pointer getter；C200 读取 handle+0x8c，失败返回 0。 |
| GUI | +0x0d8 | `BDA_GUI_OBJECT_CALLBACK_PTR_GET_LIKE` | 5 | 3 | 中 | kind=1 object callback pointer getter；C200 读取 handle+0x88，失败返回 0。 |
| GUI | +0x0dc | `BDA_GUI_OBJECT_CALLBACK_PTR_SET_LIKE` | 1 | 1 | 中 | kind=1 object callback pointer setter；C200 在 value 非 0 时写 handle+0x88，返回旧值。 |
| GUI | +0x0e0 | `BDA_GUI_OBJECT_OP_LIKE` | 985 | 49 | 中 | object refresh/notify；C200 只读取 object 并发送内部 0xb1 message。 |
| GUI | +0x0e4 | `BDA_GUI_OBJECT_DRAW_BEGIN_LIKE` | 512 | 51 | 中 | object draw begin wrapper；C200 检查 object kind，调用 GUI+0x308 取得 draw context 并递增 draw 计数。 |
| GUI | +0x0e8 | `BDA_GUI_OBJECT_DRAW_END_LIKE` | 483 | 51 | 中 | object draw end wrapper；C200 递减 draw 计数并调用 GUI+0x30c(draw_context)，无稳定 return value。 |
| GUI | +0x0f4 | `BDA_GUI_ACCUMULATE_ORIGIN_LIKE` | 244 | 17 | 中 | 累计 object 父链 origin，把 object 坐标累加到调用者传入的 x/y pointer。 |
| GUI | +0x0f8 | `BDA_GUI_SUBTRACT_ORIGIN_LIKE` | 6 | 2 | 中 | 反向累计 object 父链 origin；C200 从调用者 x/y pointer 中减去 object/parent 的 +0x14/+0x18。 |
| GUI | +0x134 | `BDA_GUI_ACTIVE_FRAME_SET_LIKE` | 353 | 49 | 中 | 设置/切换当前 active frame；C200 写内部 +0xd8，并向旧/新 frame 发 0x31/0x30。 |
| GUI | +0x13c | `BDA_GUI_ACTIVE_FRAME_GET_LIKE` | 81 | 4 | 中 | 查询 context 所属 frame/container 的 active child；C200 读取 a0，解析 parent 后返回 container+0xd8。 |
| GUI | +0x17c | `BDA_GUI_CLOSE_FRAME_LIKE` | 483 | 53 | 中 | 关闭并释放 frame/window；V11 真机确认应在 stop/release 和 event poll 结束后调用，且无稳定返回值。 |
| GUI | +0x1a4 | `BDA_GUI_CREATE` | 133 | 34 | 中 | 创建 window/control，class 字符串常见 edit/listbox/medit 等。 |
| GUI | +0x1a8 | `BDA_GUI_DESTROY_LIKE` | 474 | 47 | 中 | destroy control/object；C200 要求 kind=1 subtype=0x12，先发内部 0x64 再摘链释放。 |
| GUI | +0x1ac | `BDA_GUI_WINDOW_TIMER_START_LIKE` | 193 | 27 | 中 | window timer start；注册 (frame,timer_id,period_ms)，内部消息 0x162，最多 16 个活动记录。 |
| GUI | +0x1b0 | `BDA_GUI_WINDOW_TIMER_STOP_LIKE` | 344 | 28 | 中 | window timer stop；按 (frame,timer_id) 注销，内部消息 0x163。 |
| GUI | +0x1b4 | `BDA_GUI_WINDOW_TIMER_EXISTS_LIKE` | 86 | 5 | 中 | window timer exists；扫描 0x804a6b40 timer 表并比较 frame/timer_id。 |
| GUI | +0x1b8 | `BDA_GUI_WINDOW_TIMER_SET_PERIOD_LIKE` | 0 | 0 | 中 | window timer period raw update；内部消息 0x164；稀疏表存在空指针风险，不公开直调。 |
| GUI | +0x1bc | `BDA_GUI_WINDOW_TIMER_CLOCK_MS_LIKE` | 0 | 0 | 中 | window timer scheduler clock；无参数返回 millisecond-valued counter，10 ms 分辨率。 |
| GUI | +0x2b8 | `BDA_GUI_MSGBOX` | 382 | 44 | 较高 | message box，hardware probe 已确认可用于简单 BDA demo。 |
| GUI | +0x2fc | `BDA_GUI_DRAW_OBJECT_CREATE_LIKE` | 780 | 46 | 中 | draw/resource object table 查询；C200 只读取 kind/index，范围为 0..16。 |
| GUI | +0x300 | `BDA_GUI_DISPLAY_METRIC_LIKE` | 14 | 9 | 中 | display backend metric 查询；C200 使用 context,metric，metric 范围 0..6；Thunder 用 metric=6 作为 framebuffer 像素字节因子。 |
| GUI | +0x304 | `BDA_GUI_CURRENT_DRAW_LIKE` | 13 | 10 | 中 | current draw context；C200 读取 handle，从 5 个普通 slot 取/初始化 context，并以 mode=0 调内部 helper；满池扫描存在越界缺陷。 |
| GUI | +0x308 | `BDA_GUI_BEGIN_DRAW_LIKE` | 1174 | 37 | 中 | begin draw context；C200 读取 handle，从 5 个普通 slot 取/初始化 context，并以 mode=1 调内部 helper；满池扫描存在越界缺陷。 |
| GUI | +0x30c | `BDA_GUI_END_DRAW_LIKE` | 1063 | 45 | 中 | 结束 draw 并归还 fixed context slot；无稳定 return value，必须与 +0x304/+0x308 配对。 |
| GUI | +0x310 | `BDA_GUI_COMPAT_CONTEXT_CREATE_LIKE` | 37 | 13 | 中 | compatible draw context create；C200 分配 0xd4 byte context 并复制 source context 的 drawable bounds/backend；V19 验证可同时创建两块。 |
| GUI | +0x314 | `BDA_GUI_SURFACE_FLUSH_LIKE` | 57 | 13 | 中 | surface/canvas flush 并释放 context；C200 调 backend +0x34 后释放 object；V19 验证两块 compatible surface 可分别释放。 |
| GUI | +0x334 | `BDA_GUI_SET_FILL_COLOR_LIKE` | 57 | 14 | 中 | 设置 fill color；C200 写 context+0x14 并返回旧值。 |
| GUI | +0x338 | `BDA_GUI_SET_TEXT_MODE_LIKE` | 486 | 45 | 中 | 设置文本模式/背景模式；C200 写 context+0x18 并返回旧值。 |
| GUI | +0x33c | `BDA_GUI_SET_TEXT_COLOR_LIKE` | 580 | 44 | 中 | 设置文本颜色；C200 写 context+0x50 并返回旧值。 |
| GUI | +0x358 | `BDA_GUI_SELECT_DRAW_OBJECT_LIKE` | 76 | 22 | 中 | select draw object；C200 把 object 写入 context+0x30 并返回旧值，Thunder 会在绘制后恢复旧 object。 |
| GUI | +0x35c | `BDA_GUI_OBJECT_BIND_LIKE` | 201 | 25 | 中 | draw context resource/image slot setter；C200 写 context+0x20 并返回旧值。 |
| GUI | +0x368 | `BDA_GUI_PUT_PIXEL_LIKE` | 249 | 16 | 中 | 画点/put pixel；C200 使用 context,x,y,color 并经 backend +0xb0 提交。 |
| GUI | +0x36c | `BDA_GUI_PUT_PIXEL_RGB_LIKE` | 40 | 2 | 中 | 直接 RGB 画点；C200 使用 context,x,y,r,g,b，转换三个低 8-bit 分量后经 backend +0xb0 提交。 |
| GUI | +0x378 | `BDA_GUI_RGB_LIKE` | 535 | 43 | 中 | RGB 颜色构造或转换；C200 使用 a1/a2/a3 低 8 位和 draw/context callback。 |
| GUI | +0x37c | `BDA_GUI_LINE_TO_LIKE` | 60 | 18 | 中 | line-to primitive；C200 使用 context,x,y，从 context+0x34/+0x38 取旧点，裁剪后调用 line backend。 |
| GUI | +0x380 | `BDA_GUI_MOVE_TO_LIKE` | 60 | 18 | 中 | move-to primitive；C200 使用 context,x,y，写 context+0x34/+0x38。 |
| GUI | +0x384 | `BDA_GUI_POLYLINE_LIKE` | 0 | 0 | 中 | polyline primitive；C200 使用 context,point_array,count，首点写入 current point，后续点逐个走 line-to。 |
| GUI | +0x388 | `BDA_GUI_CIRCLE_LIKE` | 8 | 8 | 中 | circle primitive；C200 使用 context,center_x,center_y,radius，并按圆的 bounding rect clipping。 |
| GUI | +0x38c | `BDA_GUI_RECTANGLE_LIKE` | 22 | 12 | 中 | rectangle primitive；C200 使用 context,left,top,right,bottom，第五参数从 stack+0x10 读取。 |
| GUI | +0x390 | `BDA_GUI_ELLIPSE_LIKE` | 1 | 1 | 中 | ellipse primitive；核心参数为 context,cx,cy,rx,ry,0,0,filled，末项选择 outline/fill backend。 |
| GUI | +0x394 | `BDA_GUI_ARC_LIKE` | 0 | 0 | 中 | circular arc primitive；参数为 context,cx,cy,start_degrees,end_degrees,radius。 |
| GUI | +0x398 | `BDA_GUI_ROUND_RECT_LIKE` | 0 | 0 | 中 | center-based rounded rectangle；参数为 context,cx,cy,width,height,corner_rx,corner_ry,filled。 |
| GUI | +0x3a0 | `BDA_GUI_MAP_MODE_GET_LIKE` | 20 | 2 | 中 | logical/device map mode getter；返回 context+0x70。 |
| GUI | +0x3a4 | `BDA_GUI_VIEWPORT_EXTENT_GET_LIKE` | 0 | 0 | 中 | viewport extent getter；复制 context+0x7c/+0x80。 |
| GUI | +0x3a8 | `BDA_GUI_VIEWPORT_ORIGIN_GET_LIKE` | 0 | 0 | 中 | viewport origin getter；复制 context+0x74/+0x78。 |
| GUI | +0x3ac | `BDA_GUI_WINDOW_EXTENT_GET_LIKE` | 0 | 0 | 中 | window extent getter；复制 context+0x8c/+0x90。 |
| GUI | +0x3b0 | `BDA_GUI_WINDOW_ORIGIN_GET_LIKE` | 0 | 0 | 中 | window origin getter；复制 context+0x84/+0x88。 |
| GUI | +0x3b4 | `BDA_GUI_MAP_MODE_SET_LIKE` | 0 | 0 | 中 | logical/device map mode setter；写 context+0x70。 |
| GUI | +0x3b8 | `BDA_GUI_VIEWPORT_EXTENT_SET_LIKE` | 0 | 0 | 中 | viewport extent setter；写 context+0x7c/+0x80。 |
| GUI | +0x3bc | `BDA_GUI_VIEWPORT_ORIGIN_SET_LIKE` | 0 | 0 | 中 | viewport origin setter；写 context+0x74/+0x78。 |
| GUI | +0x3c0 | `BDA_GUI_WINDOW_EXTENT_SET_LIKE` | 0 | 0 | 中 | window extent setter；写 context+0x8c/+0x90。 |
| GUI | +0x3c4 | `BDA_GUI_WINDOW_ORIGIN_SET_LIKE` | 0 | 0 | 中 | window origin setter；写 context+0x84/+0x88。 |
| GUI | +0x3c8 | `BDA_GUI_DEVICE_TO_LOGICAL_POINT_LIKE` | 0 | 0 | 中 | device-to-logical point 原地转换；先减 context origin，再逆 viewport/window mapping。 |
| GUI | +0x3cc | `BDA_GUI_LOGICAL_TO_DEVICE_POINT_LIKE` | 0 | 0 | 中 | logical-to-device point 原地转换；先做 viewport/window mapping，再加 context origin。 |
| GUI | +0x3d0 | `BDA_GUI_MAP_DEVICE_TO_LOGICAL_POINT_LIKE` | 0 | 0 | 中 | map-only device-to-logical point 原地转换；不处理 context origin。 |
| GUI | +0x3d4 | `BDA_GUI_MAP_LOGICAL_TO_DEVICE_POINT_LIKE` | 0 | 0 | 中 | map-only logical-to-device point 原地转换；不处理 context origin。 |
| GUI | +0x3d8 | `BDA_GUI_CLIP_EXCLUDE_RECT_LIKE` | 0 | 0 | 中 | exclude clip rect；context,left,top,right,bottom，从当前 region 扣除矩形并拆成最多四个剩余条带。 |
| GUI | +0x3dc | `BDA_GUI_CLIP_UNION_RECT_LIKE` | 0 | 0 | 中 | union clip rect；context,left,top,right,bottom，去除旧节点重叠后追加新矩形；cached bounds 不随追加扩展。 |
| GUI | +0x3e0 | `BDA_GUI_CLIP_INTERSECT_RECT_LIKE` | 0 | 0 | 中 | intersect clip rect；context,const rect*，逐节点求交并清理空节点，然后重新计算 aggregate bounds。 |
| GUI | +0x3e4 | `BDA_GUI_CLIP_SELECT_RECT_LIKE` | 0 | 0 | 中 | 矩形 clip select/reset；context,rect_or_null，NULL 清除自定义 region，绘图回退到 context bounds。 |
| GUI | +0x3ec | `BDA_GUI_CLIP_BOUNDS_LIKE` | 20 | 2 | 中 | 读取 custom clip-region bounds；reset 后返回零矩形哨兵，effective clip 仍回退到 context bounds。 |
| GUI | +0x3f0 | `BDA_GUI_CLIP_CONTAINS_POINT_LIKE` | 0 | 0 | 中 | current clip 点命中测试；C200 使用 context,point，并遍历 clip region 或 fallback bounds。 |
| GUI | +0x3f4 | `BDA_GUI_CLIP_INTERSECTS_RECT_LIKE` | 0 | 0 | 中 | current clip 矩形相交测试；C200 使用 context,rect，并遍历 clip region 或 fallback bounds。 |
| GUI | +0x3f8 | `BDA_GUI_BLIT_LIKE` | 256 | 27 | 中 | framebuffer/region blit；C200 使用 x,y,height,width,buffer 五参数，依赖原机 surface/context，SDK 仅作 unsafe probe。 |
| GUI | +0x3fc | `BDA_GUI_CAPTURE_REGION_ALLOC_LIKE` | 27 | 11 | 中 | screen/backend region capture alloc；C200 使用 x,y,width,height，分配 buffer 后经 backend +0x84 抓取区域。 |
| GUI | +0x400 | `BDA_GUI_BLIT_ALT_LIKE` | 210 | 33 | 中 | 带全局 clip/prepare 的 blit；C200 使用 x,y,height,width,buffer 五参数，TileBlit 真机会逐块 flip 后死机。 |
| GUI | +0x40c | `BDA_GUI_REGION_DRAW_LIKE` | 174 | 28 | 中 | region draw/copy；C200 使用 context,x,y,width,height 五参数。 |
| GUI | +0x410 | `BDA_GUI_RENDER_COPY_LIKE` | 38 | 7 | 中 | low-level render/copy helper；C200 使用 context,x,y,width,height,descriptor 六参数。 |
| GUI | +0x414 | `BDA_GUI_RENDER_HELPER_LIKE` | 69 | 9 | 中 | low-level render helper；C200 读取 descriptor、多个 stack 参数并可分配临时 buffer。 |
| GUI | +0x418 | `BDA_GUI_RENDER_FINISH_LIKE` | 117 | 13 | 中 | 双 context 矩形复制；V19-V21 验证 compatible 合成、0xf81f 洋红透明键和 dirty rect 局部提交；stack+0x14 为 destination，stack+0x20 为 RGB565 color_key；C200knl 真机确认 0 跳过黑色而非禁用色键。 |
| GUI | +0x430 | `BDA_GUI_RECT_PREPARE_LIKE` | 69 | 6 | 中 | rect writer；C200 使用 rect,x0,y0,x1,y1 五参数并写入四个 word。 |
| GUI | +0x46c | `BDA_GUI_RECT_CONTAINS_LIKE` | 505 | 33 | 中 | 矩形命中测试，判断点是否落在 x0/y0/x1/y1 范围内。 |
| GUI | +0x4a4 | `BDA_GUI_CURRENT_FONT_LIKE` | 29 | 10 | 中 | current font pointer getter；C200 返回 context+0x54，context=0 时使用 default draw context。 |
| GUI | +0x4d0 | `BDA_GUI_FONT_CELL_WIDTH_LIKE` | 8 | 8 | 中 | font cell width-like metric；C200 返回 current font descriptor +0x38。 |
| GUI | +0x4d4 | `BDA_GUI_FONT_CELL_HEIGHT_LIKE` | 8 | 8 | 中 | font cell height-like metric；C200 查询 primary/fallback font callback 并返回较大值。 |
| GUI | +0x4f0 | `BDA_GUI_DRAW_TEXT_LIKE` | 1087 | 46 | 中 | draw GBK/ASCII text；C200 使用 handle,x,y,text,extra，extra<0 时按 strlen。 |
| GUI | +0x50c | `BDA_GUI_PICTURE_SOURCE_FREE_LIKE` | 26 | 4 | 中 | 已有 SDK name，但还缺少更细的 ABI/lifecycle 证据。 |
| GUI | +0x540 | `BDA_GUI_DRAW_VX_LIKE` | 1208 | 40 | 中 | 绘制完整 VX resource block；C200 从第 6 参数读取 resource，尺寸来自 VX header +0x06/+0x0a。 |
| GUI | +0x5a8 | `BDA_GUI_HELP_PAGE_LIKE` | 198 | 42 | 中 | 同步系统帮助页；参数为 parent 和 title\r\nbody，8013 已验证裸调用、注册 Frame parent、退出返回和公开 wrapper。 |
| GUI | +0x5d4 | `BDA_GUI_INPUT_PACKET_LIKE` | 9 | 9 | 中 | GAMEBOY/input 按键包 helper；C200 清 6 byte packet 后写入按键状态。 |
| GUI | +0x670 | `BDA_GUI_DECODE_BMP_LIKE` | 7 | 4 | 中 | BMP/VX decode；C200 使用 owner,out,path,out_source_buffer，VX 快路径会写回 file buffer pointer。 |
| GUI | +0x6a8 | `BDA_GUI_FILE_SELECTOR_OPEN_LIKE` | 30 | 29 | 中 | file selector open/session；C200 只读取 a0=mode，内部构造 modal frame。 |
| GUI | +0x6b0 | `BDA_GUI_SCREEN_BUFFER_LIKE` | 19 | 2 | 中 | 内部 screen/framebuffer pointer getter；无参数，不是 allocator；正式 API 通过该入口动态取址并校验 KSEG、范围、对齐和方向，不固定物理地址。裸候选返回值不要直接写或自定义 present。 |
| GUI | +0x6b8 | `BDA_GUI_LIST_NTH_LIKE` | 23 | 18 | 中 | 链表第 N 项 helper；C200 使用 a0=head、a1=index，不是无参数 selector get。 |
| GUI | +0x6bc | `BDA_GUI_LIST_FREE_LIKE` | 37 | 18 | 中 | linked list free helper；C200 将 a0=head 传给 0x8003e868，释放节点和节点 data，不是无参数 selector close。 |
| GUI | +0x6c0 | `BDA_GUI_TOUCH_POSITION_LIKE` | 4 | 3 | 高 | raw-to-logical 最新触摸坐标 getter；a0/a1 为 u16 output pointer，结果裁剪到 240x320；FastTouchV3 已在真机高频动态验证，公开为 `bda_gui_touch_position()`。 |
| GUI | +0x6c8 | `BDA_GUI_FILE_SELECTOR_UPDATE_LIKE` | 17 | 13 | 中 | file selector modal run；a0=descriptor，C200 entry 将它原样传给内部 helper。 |
| GUI | +0x6d8 | `BDA_GUI_TICK_COUNT_25MS_LIKE` | 4 | 1 | 中 | 25 ms raw tick counter；无参数返回 u32，C200 定时 IRQ 递增，BBVM 用无符号差值乘 25 转为毫秒。 |
| GUI | +0x6e0 | `BDA_GUI_GAME_DISPLAY_PUMP_LIKE` | 51 | 19 | 中 | 触摸长按驱动的 game state pump；C200 无参数，先查 pen GPIO，阈值 0x1068 后写全局状态；有副作用。 |
| GUI | +0x714 | `BDA_GUI_MILLISECOND_TIMER_START_LIKE` | 0 | 0 | 中 | 1 ms timer start；C200 配置 TCU0 为 750 kHz/750 count 并注册 IRQ 0x17；必须与 +0x718 配对。 |
| GUI | +0x718 | `BDA_GUI_MILLISECOND_TIMER_STOP_LIKE` | 0 | 0 | 中 | 1 ms timer stop；C200 mask TCU0 并注销 IRQ 0x17；每个成功 start 在退出前调用一次。 |
| GUI | +0x71c | `BDA_GUI_MILLISECOND_COUNT_LIKE` | 0 | 0 | 中 | 标称 1 ms raw counter；无参数返回 u32，只有 +0x714 start 后才持续递增；V4 在 8013 和真机通过，真机 200 ms 窗口实测 194..200 count。 |
| GUI | +0x72c | `BDA_GUI_STATE_QUERY_LIKE` | 9 | 6 | 中 | GAMEBOY 状态查询；C200 table entry 无参数并更新内部状态 word。 |
| GUI | +0x738 | `BDA_GUI_SCREEN_ORIENTATION_LIKE` | 12 | 6 | 中 | 返回 screen orientation；C200 的 0x130 表示整帧复制需旋转 180 度，0x131 表示正向。 |
| GUI | +0x750 | `BDA_GUI_EVENT_FETCH_LIKE` | 2 | 2 | 高 | 全局 raw input event 获取；C200 使用 a0/a1 两个 s32 output pointer；GbTouchEventV1 真机确认 8/12/11 为 touch down/move/up、9/10 为 key down/up，已公开为 `bda_gui_raw_event_fetch()`。code 3 语义未命名，调用方必须有界 drain。 |
| GUI | +0x808 | `BDA_GUI_DECODE_JPEG_LIKE` | 0 | 0 | 中 | JPEG decode；C200 使用 owner,out,path,mode，mode 截成 signed 8-bit，mode==1 先做路径/格式检查。 |
| MEM | +0x000 | `BDA_MEM_TRACK_ALLOC_LIKE` | 1858 | 54 | 中 | tracked heap alloc；C200 单参数 size，debug tracking 开启时记录 pointer/size。 |
| MEM | +0x004 | `BDA_MEM_TRACK_FREE_LIKE` | 1178 | 54 | 中 | tracked heap free；C200 单参数 ptr，debug tracking 开启时清记录后释放。 |
| MEM | +0x008 | `BDA_MEM_ALLOC` | 2658 | 54 | 较高 | 固件堆内存分配/heap alloc；C200 单参数 size，锁保护后返回 pointer。 |
| MEM | +0x00c | `BDA_MEM_FREE` | 2412 | 54 | 较高 | 固件堆内存释放；C200 单参数 ptr，锁保护后调用内部 free。 |
| MEM | +0x010 | `BDA_MEM_CALLOC_LIKE` | 2043 | 54 | 中 | firmware heap calloc-like；C200 使用 count,size，按 count*align4(size) 分配并清零。 |
| MEM | +0x014 | `BDA_MEM_REALLOC_LIKE` | 156 | 34 | 中 | firmware heap realloc-like；C200 使用 ptr,new_size，支持 ptr=0 alloc 和 size=0 free。 |
| MEM | +0x01c | `BDA_MEM_TRACK_BEGIN_LIKE` | 95 | 16 | 中 | heap tracking begin；C200 使用 free_on_finish flag，开启 tracking 并清记录计数。 |
| MEM | +0x020 | `BDA_MEM_TRACK_REPORT_LIKE` | 217 | 23 | 中 | heap tracking report/count；C200 使用 summary_only flag，返回 tracked 记录计数。 |
| MEM | +0x024 | `BDA_MEM_TRACK_FINISH_LIKE` | 281 | 26 | 中 | heap tracking finish；C200 结束 tracking，free_on_finish 非 0 时可释放记录 pointer。 |
| MEM | +0x028 | `BDA_MEM_TRACK_RETAIN_LIKE` | 108 | 20 | 中 | heap tracking retain；C200 查 tracked record table，命中时递增 refcount-like 字段并返回 pointer。 |
| MEM | +0x02c | `BDA_MEM_TRACK_RELEASE_LIKE` | 126 | 30 | 中 | heap tracking release；C200 查 tracked record table，递减 refcount-like 字段，归零时释放 pointer。 |
| RES | +0x090 | `BDA_RES_GET_STATE_LIKE` | 143 | 42 | 中 | 资源/图片状态 snapshot；C200 从 0xb0003004 取状态源，向 out_state 写 7 个 word，无稳定 return value。 |
| RES | +0x094 | `BDA_RES_ENTRY_094_LIKE` | 1987 | 54 | 中 | trace/log；历史 DLX loader 名称已废弃。 |
| SYS | +0x000 | `BDA_SYS_SESSION_OPEN_LIKE` | 1858 | 54 | 中 | 已有 SDK name，但还缺少更细的 ABI/lifecycle 证据。 |
| SYS | +0x004 | `BDA_SYS_CLOSE_LIKE` | 1178 | 54 | 中 | 内部 system resource close；C200 使用 resource_id 1..10 查资源表并调用 close callback，不是 app exit。 |
| SYS | +0x014 | `BDA_SYS_SESSION_INIT_WORD_LIKE` | 156 | 34 | 中 | 已有 SDK name，但还缺少更细的 ABI/lifecycle 证据。 |
| SYS | +0x018 | `BDA_SYS_SESSION_OP18_LIKE` | 108 | 23 | 中 | 已有 SDK name，但还缺少更细的 ABI/lifecycle 证据。 |
| SYS | +0x01c | `BDA_SYS_SESSION_OP1C_LIKE` | 95 | 16 | 中 | 已有 SDK name，但还缺少更细的 ABI/lifecycle 证据。 |
| SYS | +0x020 | `BDA_SYS_SESSION_STOP_LIKE` | 217 | 23 | 中 | 已有 SDK name，但还缺少更细的 ABI/lifecycle 证据。 |
| SYS | +0x02c | `BDA_SYS_SESSION_STATUS_LIKE` | 126 | 30 | 中 | 已有 SDK name，但还缺少更细的 ABI/lifecycle 证据。 |
| SYS | +0x040 | `BDA_SYS_AUDIO_ATTENUATION_SET_LIKE` | 5702 | 52 | 中 | raw PCM attenuation setter；C200 clamp 到 0..98，写 pending value，下一次 audio write 量化并应用。 |
| SYS | +0x044 | `BDA_SYS_AUDIO_ATTENUATION_GET_LIKE` | 305 | 27 | 中 | raw PCM attenuation getter；C200 无参数，返回当前 effective attenuation（0..96，步进 3）。 |
| SYS | +0x058 | `BDA_SYS_PACKAGE_SOUND_OP58_LIKE` | 16 | 3 | 中 | 打包音效 init/start；C200 使用 a0=descriptor，成功置 0x804c4ba4 并返回 1。 |
| SYS | +0x05c | `BDA_SYS_PACKAGE_SOUND_OP5C_LIKE` | 28 | 10 | 中 | 打包音效 descriptor 操作；C200 使用 slot,descriptor,a2,flags 四参数。 |
| SYS | +0x060 | `BDA_SYS_PACKAGE_SOUND_OP60_LIKE` | 20 | 9 | 中 | 打包音效状态置位；C200 无参数，0x804c4ba8 从 0 置 1 时返回 1。 |
| SYS | +0x064 | `BDA_SYS_PACKAGE_SOUND_OP64_LIKE` | 34 | 13 | 中 | 打包音效状态清除；C200 无参数，0x804c4ba8 从 1 清 0 时返回 1。 |
| SYS | +0x068 | `BDA_SYS_PACKAGE_SOUND_OP68_LIKE` | 51 | 17 | 中 | 打包音效 release/stop；C200 无参数，关闭全局 handle 并清 0x804c4ba4。 |
| SYS | +0x06c | `BDA_SYS_AUDIO_OPEN_LIKE` | 97 | 10 | 中 | raw audio open/init；C200 使用 device,format,channels 三参数，format/channels 截成 signed 8-bit，尾部固定 v0=0。 |
| SYS | +0x074 | `BDA_SYS_AUDIO_READY_LIKE` | 2462 | 51 | 中 | raw audio ready query；C200 无参数，返回 0x8058+0x6e8 > 0。 |
| SYS | +0x078 | `BDA_SYS_AUDIO_WRITE_LIKE` | 11 | 7 | 中 | raw audio write；C200 使用 buffer,bytes，bytes<=0 返回 -1，正常返回已消费 byte 数。 |
| SYS | +0x080 | `BDA_SYS_DELAY_LIKE` | 415 | 32 | 中 | 阻塞式 busy-wait delay；C200 按系统校准值把 a0 换算成循环次数，无稳定 return value。 |
| SYS | +0x088 | `BDA_SYS_KEYCODE_RAW_LIKE` | 344 | 53 | 中 | raw keycode query；C200 无参数，读取硬件输入寄存器并返回 raw code。 |
| SYS | +0x08c | `BDA_SYS_AUDIO_RESET_LIKE` | 399 | 54 | 中 | raw audio reset/init；C200 无参数，关闭全局 audio object 后进入初始化路径，无稳定 return value。 |
| SYS | +0x090 | `BDA_SYS_AUDIO_STATE_LIKE` | 143 | 42 | 中 | raw audio state pointer getter；C200 无参数，直接返回全局 state 0x80362830。 |
| SYS | +0x09c | `BDA_SYS_TIMER_LIKE` | 115 | 17 | 中 | timer/rate preset 选择；C200 把 a0 clamp 到 0..14 后查内部表，无稳定 return value。 |
| SYS | +0x0a0 | `BDA_SYS_AUDIO_FLUSH_LIKE` | 8 | 4 | 中 | raw audio finish/stop；C200 无参数，真机安全返回且停止声音；模拟器后端 timer 状态存在差异，无稳定 return value。 |
| SYS | +0x0ac | `BDA_SYS_ALARM_SET_LIKE` | 70 | 9 | 中 | alarm set；C200 使用 alarm_data,slot，record size 0x2b8，未见 slot bounds check，return value 成功 1。 |
| SYS | +0x0b0 | `BDA_SYS_ALARM_GET_LIKE` | 7 | 2 | 中 | alarm get；C200 使用 alarm_data,slot，从 file offset 0x578+slot*0x2b8 复制 0x2b8 byte，return value 成功 1。 |
| SYS | +0x0b8 | `BDA_SYS_ALARM_DUE_GET_LIKE` | 350 | 27 | 中 | alarm due record get；C200 打开 alarm.db，扫描 0x2b8 byte record，并向 out buffer 复制整条 record。 |

## 未命名高频 Offset

这些 offset 在原机 BDA 中出现，但还没有稳定映射到具体 table 和 SDK name。后续应使用 `bda_table_call_scan.py --context` 在原始样本上按全局 table pointer 分类。

当前 inventory 前 40 个高频 offset 都已有 SDK name；剩余长尾 offset 仍需按应用继续分类。

## 后续验证建议

- 有本地原机 BDA 样本时，先运行 `python reverse\bda_inventory.py --root 应用\程序` 更新 inventory。
- 对单个应用按表分类：`python reverse\bda_table_call_scan.py 应用\程序\计算器.bda --context`。
- 有 `C200.bin` 时，运行 `python reverse\system_bin_probe.py --root .` 和系统 API 交叉引用脚本，把 table entry function 与系统实现地址对应起来。
