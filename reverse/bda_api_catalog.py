from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path


DEFINE_RE = re.compile(r"^#define\s+(BDA_(GUI|FS|SYS|MEM|RES)_[A-Z0-9_]+)\s+(0x[0-9a-fA-F]+)u?\b")

CORE_API_DEFINE_NAMES = {
    "BDA_GUI_MSGBOX",
    "BDA_GUI_CREATE",
    "BDA_GUI_SEND",
    "BDA_FS_OPEN",
    "BDA_FS_CLOSE",
    "BDA_FS_READ",
    "BDA_FS_WRITE",
    "BDA_FS_SEEK",
    "BDA_FS_TELL",
    "BDA_FS_REMOVE",
    "BDA_FS_FLUSH_ALL",
    "BDA_MEM_ALLOC",
    "BDA_MEM_FREE",
}

# RGB565 pixel values live beside the GUI declarations in the research header,
# but they are data constants rather than GUI table offsets.  Keep them out of
# the generated API catalog even though the reverse-engineering names use the
# conventional _LIKE suffix.
NON_API_DEFINE_NAMES = {
    "BDA_GUI_COLOR_KEY_BLACK_RGB565_LIKE",
    "BDA_GUI_COLOR_KEY_MAGENTA_RGB565_LIKE",
    "BDA_GUI_OPAQUE_BLACK_RGB565_LIKE",
}

NOTES: dict[tuple[str, int], str] = {
    ("FS", 0x074): "全局 open-file flush；无参数，遍历脏 file object 写回数据和 metadata；8013 强制断电 A/B 验证 4096-byte flushed 文件完整、未 flush 对照为 0 byte。",
    ("GUI", 0x030): "event poll；C200 参数为 message_buffer,frame_or_handle，会填 0x1c byte message packet。",
    ("GUI", 0x03C): "异步 notify/post；C200 将 handle,message,a,b 写入 frame queue，0xb1 只置 pending flag。",
    ("GUI", 0x040): "同步 send；C200 直接调用 handle+0x88 wndproc，参数为 handle,message,wparam,lparam。",
    ("GUI", 0x04C): "frame release/request；C200 解析 handle/default slot 后设置 object 高位状态 flag。",
    ("GUI", 0x050): "event step；C200 读取 a0=message_buffer，只处理 message 0x10/0x13 派生通知。",
    ("GUI", 0x054): "event dispatch；C200 读取 message_buffer 并调用目标 handle 的 +0x88 wndproc。",
    ("GUI", 0x074): "绘图/present guard；C200 保存 a0，a0=0 时触发 present/update；缺少原机 surface/context 时 TileBlit 会逐块 flip 后死机。",
    ("GUI", 0x07C): "kind=1 object flags clear helper；C200 把 handle+0x24 与 ~mask 相与，成功返回 1。",
    ("GUI", 0x080): "kind=1 object flags OR helper；C200 把 mask OR 到 handle+0x24，成功返回 1。",
    ("GUI", 0x084): "注册 frame/window descriptor；C200 读取 0x34 byte descriptor 后创建内部 window object。",
    ("GUI", 0x088): "停止 frame/window；C200 只读取 handle，解析 frame 后发送内部 0x66/0xf1 message。",
    ("GUI", 0x08C): "default window procedure fallback；C200 参数为 handle,message,wparam,lparam。",
    ("GUI", 0x098): "激活/状态切换 frame；C200 参数为 handle,mode，mode 0/0x10/0x100 有特殊路径。",
    ("GUI", 0x0A4): "object/default client rect 查询；C200 使用 handle,rect，写 16 byte rect，成功返回 1。",
    ("GUI", 0x0B0): "kind=1 object flags getter；C200 读取 handle+0x24，失败返回 0。",
    ("GUI", 0x0E0): "object refresh/notify；C200 只读取 object 并发送内部 0xb1 message。",
    ("GUI", 0x0E4): "object draw begin wrapper；C200 检查 object kind，调用 GUI+0x308 取得 draw context 并递增 draw 计数。",
    ("GUI", 0x0E8): "object draw end wrapper；C200 递减 draw 计数并调用 GUI+0x30c(draw_context)，无稳定 return value。",
    ("GUI", 0x0B8): "kind=1 object userdata0 getter；C200 读取 handle+0x80，失败返回 0。",
    ("GUI", 0x0BC): "kind=1 object userdata0 setter；C200 写 handle+0x80，返回旧值，失败返回 0。",
    ("GUI", 0x0C0): "kind=1 object userdata1 getter；C200 读取 handle+0x84，失败返回 0。",
    ("GUI", 0x0C4): "kind=1 object userdata1 setter；C200 写 handle+0x84，返回旧值，失败返回 0。",
    ("GUI", 0x0C8): "subtype=0x12 object payload word getter；C200 读取 handle+0xec 指向 payload 的 +0x1c。",
    ("GUI", 0x0CC): "subtype=0x12 object payload word setter；C200 写 payload+0x1c，返回旧值，失败返回 0。",
    ("GUI", 0x0D0): "kind=1 object resource pointer getter；C200 读取 handle+0x8c，失败返回 0。",
    ("GUI", 0x0D8): "kind=1 object callback pointer getter；C200 读取 handle+0x88，失败返回 0。",
    ("GUI", 0x0DC): "kind=1 object callback pointer setter；C200 在 value 非 0 时写 handle+0x88，返回旧值。",
    ("GUI", 0x0F4): "累计 object 父链 origin，把 object 坐标累加到调用者传入的 x/y pointer。",
    ("GUI", 0x0F8): "反向累计 object 父链 origin；C200 从调用者 x/y pointer 中减去 object/parent 的 +0x14/+0x18。",
    ("GUI", 0x134): "设置/切换当前 active frame；C200 写内部 +0xd8，并向旧/新 frame 发 0x31/0x30。",
    ("GUI", 0x13C): "查询 context 所属 frame/container 的 active child；C200 读取 a0，解析 parent 后返回 container+0xd8。",
    ("GUI", 0x17C): "关闭并释放 frame/window；V11 真机确认应在 stop/release 和 event poll 结束后调用，且无稳定返回值。",
    ("GUI", 0x1A4): "创建 window/control，class 字符串常见 edit/listbox/medit 等。",
    ("GUI", 0x1A8): "destroy control/object；C200 要求 kind=1 subtype=0x12，先发内部 0x64 再摘链释放。",
    ("GUI", 0x1AC): "window timer start；注册 (frame,timer_id,period_ms)，内部消息 0x162，最多 16 个活动记录。",
    ("GUI", 0x1B0): "window timer stop；按 (frame,timer_id) 注销，内部消息 0x163。",
    ("GUI", 0x1B4): "window timer exists；扫描 0x804a6b40 timer 表并比较 frame/timer_id。",
    ("GUI", 0x1B8): "window timer period raw update；内部消息 0x164；稀疏表存在空指针风险，不公开直调。",
    ("GUI", 0x1BC): "window timer scheduler clock；无参数返回 millisecond-valued counter，10 ms 分辨率。",
    ("GUI", 0x2B8): "message box，hardware probe 已确认可用于简单 BDA demo。",
    ("GUI", 0x2FC): "draw/resource object table 查询；C200 只读取 kind/index，范围为 0..16。",
    ("GUI", 0x300): "display backend metric 查询；C200 使用 context,metric，metric 范围 0..6；Thunder 用 metric=6 作为 framebuffer 像素字节因子。",
    ("GUI", 0x304): "current draw context；C200 读取 handle，从 5 个普通 slot 取/初始化 context，并以 mode=0 调内部 helper；满池扫描存在越界缺陷。",
    ("GUI", 0x308): "begin draw context；C200 读取 handle，从 5 个普通 slot 取/初始化 context，并以 mode=1 调内部 helper；满池扫描存在越界缺陷。",
    ("GUI", 0x30C): "结束 draw 并归还 fixed context slot；无稳定 return value，必须与 +0x304/+0x308 配对。",
    ("GUI", 0x310): "compatible draw context create；C200 分配 0xd4 byte context 并复制 source context 的 drawable bounds/backend；V19 验证可同时创建两块。",
    ("GUI", 0x314): "surface/canvas flush 并释放 context；C200 调 backend +0x34 后释放 object；V19 验证两块 compatible surface 可分别释放。",
    ("GUI", 0x334): "设置 fill color；C200 写 context+0x14 并返回旧值。",
    ("GUI", 0x338): "设置文本模式/背景模式；C200 写 context+0x18 并返回旧值。",
    ("GUI", 0x33C): "设置文本颜色；C200 写 context+0x50 并返回旧值。",
    ("GUI", 0x358): "select draw object；C200 把 object 写入 context+0x30 并返回旧值，Thunder 会在绘制后恢复旧 object。",
    ("GUI", 0x35C): "draw context resource/image slot setter；C200 写 context+0x20 并返回旧值。",
    ("GUI", 0x368): "画点/put pixel；C200 使用 context,x,y,color 并经 backend +0xb0 提交。",
    ("GUI", 0x36C): "直接 RGB 画点；C200 使用 context,x,y,r,g,b，转换三个低 8-bit 分量后经 backend +0xb0 提交。",
    ("GUI", 0x378): "RGB 颜色构造或转换；C200 使用 a1/a2/a3 低 8 位和 draw/context callback。",
    ("GUI", 0x37C): "line-to primitive；C200 使用 context,x,y，从 context+0x34/+0x38 取旧点，裁剪后调用 line backend。",
    ("GUI", 0x380): "move-to primitive；C200 使用 context,x,y，写 context+0x34/+0x38。",
    ("GUI", 0x384): "polyline primitive；C200 使用 context,point_array,count，首点写入 current point，后续点逐个走 line-to。",
    ("GUI", 0x388): "circle primitive；C200 使用 context,center_x,center_y,radius，并按圆的 bounding rect clipping。",
    ("GUI", 0x38C): "rectangle primitive；C200 使用 context,left,top,right,bottom，第五参数从 stack+0x10 读取。",
    ("GUI", 0x390): "ellipse primitive；核心参数为 context,cx,cy,rx,ry,0,0,filled，末项选择 outline/fill backend。",
    ("GUI", 0x394): "circular arc primitive；参数为 context,cx,cy,start_degrees,end_degrees,radius。",
    ("GUI", 0x398): "center-based rounded rectangle；参数为 context,cx,cy,width,height,corner_rx,corner_ry,filled。",
    ("GUI", 0x3A0): "logical/device map mode getter；返回 context+0x70。",
    ("GUI", 0x3A4): "viewport extent getter；复制 context+0x7c/+0x80。",
    ("GUI", 0x3A8): "viewport origin getter；复制 context+0x74/+0x78。",
    ("GUI", 0x3AC): "window extent getter；复制 context+0x8c/+0x90。",
    ("GUI", 0x3B0): "window origin getter；复制 context+0x84/+0x88。",
    ("GUI", 0x3B4): "logical/device map mode setter；写 context+0x70。",
    ("GUI", 0x3B8): "viewport extent setter；写 context+0x7c/+0x80。",
    ("GUI", 0x3BC): "viewport origin setter；写 context+0x74/+0x78。",
    ("GUI", 0x3C0): "window extent setter；写 context+0x8c/+0x90。",
    ("GUI", 0x3C4): "window origin setter；写 context+0x84/+0x88。",
    ("GUI", 0x3C8): "device-to-logical point 原地转换；先减 context origin，再逆 viewport/window mapping。",
    ("GUI", 0x3CC): "logical-to-device point 原地转换；先做 viewport/window mapping，再加 context origin。",
    ("GUI", 0x3D0): "map-only device-to-logical point 原地转换；不处理 context origin。",
    ("GUI", 0x3D4): "map-only logical-to-device point 原地转换；不处理 context origin。",
    ("GUI", 0x3D8): "exclude clip rect；context,left,top,right,bottom，从当前 region 扣除矩形并拆成最多四个剩余条带。",
    ("GUI", 0x3DC): "union clip rect；context,left,top,right,bottom，去除旧节点重叠后追加新矩形；cached bounds 不随追加扩展。",
    ("GUI", 0x3E0): "intersect clip rect；context,const rect*，逐节点求交并清理空节点，然后重新计算 aggregate bounds。",
    ("GUI", 0x3E4): "矩形 clip select/reset；context,rect_or_null，NULL 清除自定义 region，绘图回退到 context bounds。",
    ("GUI", 0x3EC): "读取 custom clip-region bounds；reset 后返回零矩形哨兵，effective clip 仍回退到 context bounds。",
    ("GUI", 0x3F0): "current clip 点命中测试；C200 使用 context,point，并遍历 clip region 或 fallback bounds。",
    ("GUI", 0x3F4): "current clip 矩形相交测试；C200 使用 context,rect，并遍历 clip region 或 fallback bounds。",
    ("GUI", 0x3F8): "framebuffer/region blit；C200 使用 x,y,height,width,buffer 五参数，依赖原机 surface/context，SDK 仅作 unsafe probe。",
    ("GUI", 0x3FC): "screen/backend region capture alloc；C200 使用 x,y,width,height，分配 buffer 后经 backend +0x84 抓取区域。",
    ("GUI", 0x400): "带全局 clip/prepare 的 blit；C200 使用 x,y,height,width,buffer 五参数，TileBlit 真机会逐块 flip 后死机。",
    ("GUI", 0x40C): "region draw/copy；C200 使用 context,x,y,width,height 五参数。",
    ("GUI", 0x410): "low-level render/copy helper；C200 使用 context,x,y,width,height,descriptor 六参数。",
    ("GUI", 0x414): "low-level render helper；C200 读取 descriptor、多个 stack 参数并可分配临时 buffer。",
    ("GUI", 0x418): "双 context 矩形复制；V19-V21 验证 compatible 合成、0xf81f 洋红透明键和 dirty rect 局部提交；stack+0x14 为 destination，stack+0x20 为 RGB565 color_key；C200knl 真机确认 0 跳过黑色而非禁用色键。",
    ("GUI", 0x430): "rect writer；C200 使用 rect,x0,y0,x1,y1 五参数并写入四个 word。",
    ("GUI", 0x46C): "矩形命中测试，判断点是否落在 x0/y0/x1/y1 范围内。",
    ("GUI", 0x4A4): "current font pointer getter；C200 返回 context+0x54，context=0 时使用 default draw context。",
    ("GUI", 0x4D0): "font cell width-like metric；C200 返回 current font descriptor +0x38。",
    ("GUI", 0x4D4): "font cell height-like metric；C200 查询 primary/fallback font callback 并返回较大值。",
    ("GUI", 0x4F0): "draw GBK/ASCII text；C200 使用 handle,x,y,text,extra，extra<0 时按 strlen。",
    ("GUI", 0x540): "绘制完整 VX resource block；C200 从第 6 参数读取 resource，尺寸来自 VX header +0x06/+0x0a。",
    ("GUI", 0x5A8): "同步系统帮助页；参数为 parent 和 title\\r\\nbody，8013 已验证裸调用、注册 Frame parent、退出返回和公开 wrapper。",
    ("GUI", 0x5D4): "GAMEBOY/input 按键包 helper；C200 清 6 byte packet 后写入按键状态。",
    ("GUI", 0x670): "BMP/VX decode；C200 使用 owner,out,path,out_source_buffer，VX 快路径会写回 file buffer pointer。",
    ("GUI", 0x6A8): "file selector open/session；C200 只读取 a0=mode，内部构造 modal frame。",
    ("GUI", 0x6B0): "内部 screen/framebuffer pointer getter；无参数，不是 allocator；正式 API 通过该入口动态取址并校验 KSEG、范围、对齐和方向，不固定物理地址。裸候选返回值不要直接写或自定义 present。",
    ("GUI", 0x6C0): "raw-to-logical 最新触摸坐标 getter；a0/a1 为 u16 output pointer，结果裁剪到 240x320；FastTouchV3 已在真机高频动态验证，公开为 `bda_gui_touch_position()`。",
    ("GUI", 0x6B8): "链表第 N 项 helper；C200 使用 a0=head、a1=index，不是无参数 selector get。",
    ("GUI", 0x6BC): "linked list free helper；C200 将 a0=head 传给 0x8003e868，释放节点和节点 data，不是无参数 selector close。",
    ("GUI", 0x6C8): "file selector modal run；a0=descriptor，C200 entry 将它原样传给内部 helper。",
    ("GUI", 0x6D8): "25 ms raw tick counter；无参数返回 u32，C200 定时 IRQ 递增，BBVM 用无符号差值乘 25 转为毫秒。",
    ("GUI", 0x6E0): "触摸长按驱动的 game state pump；C200 无参数，先查 pen GPIO，阈值 0x1068 后写全局状态；有副作用。",
    ("GUI", 0x714): "1 ms timer start；C200 配置 TCU0 为 750 kHz/750 count 并注册 IRQ 0x17；必须与 +0x718 配对。",
    ("GUI", 0x718): "1 ms timer stop；C200 mask TCU0 并注销 IRQ 0x17；每个成功 start 在退出前调用一次。",
    ("GUI", 0x71C): "标称 1 ms raw counter；无参数返回 u32，只有 +0x714 start 后才持续递增；V4 在 8013 和真机通过，真机 200 ms 窗口实测 194..200 count。",
    ("GUI", 0x72C): "GAMEBOY 状态查询；C200 table entry 无参数并更新内部状态 word。",
    ("GUI", 0x738): "返回 screen orientation；C200 的 0x130 表示整帧复制需旋转 180 度，0x131 表示正向。",
    ("GUI", 0x750): "全局 raw input event 获取；C200 使用 a0/a1 两个 s32 output pointer；GbTouchEventV1 真机确认 8/12/11 为 touch down/move/up、9/10 为 key down/up，已公开为 `bda_gui_raw_event_fetch()`。code 3 语义未命名，调用方必须有界 drain。",
    ("GUI", 0x808): "JPEG decode；C200 使用 owner,out,path,mode，mode 截成 signed 8-bit，mode==1 先做路径/格式检查。",
    ("FS", 0x000): "fopen-style；原机代码常传 rb/wb 等 mode string。",
    ("FS", 0x004): "fclose-style；C200 单参数 file，return value 来自内部 close helper。",
    ("FS", 0x008): "fread-style；C200 参数顺序为 buffer,size,count,file，失败返回 0。",
    ("FS", 0x00C): "fwrite-style；C200 参数顺序为 buffer,size,count,file，失败返回 0。",
    ("FS", 0x010): "fseek-style；C200 参数为 file,offset,whence，无效 whence 返回 -1。",
    ("FS", 0x014): "ftell-style；C200 检查 file+0x48 index，有效路径返回 file+0x44。",
    ("FS", 0x018): "feof-like；C200 检查 file+0x44 当前位置和 file+0x20 size-like word。",
    ("FS", 0x01C): "ferror-like；C200 检查 file+0x4a 的 0x1000 error flag。",
    ("FS", 0x020): "clearerr-like；C200 清除 file+0x4a 的 0x1000 error flag。",
    ("FS", 0x024): "remove/unlink；C200 解析单参数 path 后删除文件。",
    ("FS", 0x028): "rename/move-like；C200 使用 old_path,new_path，分别解析后调用内部 rename helper。",
    ("FS", 0x02C): "chdir/current directory 切换；C200 检查目录属性位 0x4000。",
    ("FS", 0x030): "mkdir-style；C200 解析 path 后调用内部创建目录 helper。",
    ("FS", 0x034): "rmdir/remove-directory；C200 使用单参数 path，删除空目录。",
    ("FS", 0x03C): "findfirst/search-open；C200 参数为 pattern,attr,find_data，内部申请 0x20a 临时 path buffer。",
    ("FS", 0x040): "findnext-style；C200 读取 find_data+0x10 index，并调用 0x8017f6b0(find_data)。",
    ("FS", 0x044): "findclose-style；C200 读取 find_data+0x10 index，并释放 find_data+0x00 cursor。",
    ("FS", 0x048): "disk/storage 容量查询；C200 只取 drive 低 8 位，确认 0/1 路径，成功写 4 个 word。",
    ("FS", 0x050): "current directory getter；C200 使用 buffer,size，返回所需 byte 数，写入 A:/B: 前缀路径。",
    ("FS", 0x054): "path info getter；C200 使用 path,info，填充 0x18 byte attr/size/time-like 结构。",
    ("FS", 0x06C): "path/flags 存在性或属性检查；C200 只使用 a0/a1，不填充 stat 输出结构。",
    ("FS", 0x078): "raw media-present query；C200 无参数，底层读取 0xb0010300 的 media-present bit 后返回 0/1。",
    ("FS", 0x07C): "无参数存储介质就绪查询；C200 返回内部检测结果低 8 位。",
    ("MEM", 0x000): "tracked heap alloc；C200 单参数 size，debug tracking 开启时记录 pointer/size。",
    ("MEM", 0x004): "tracked heap free；C200 单参数 ptr，debug tracking 开启时清记录后释放。",
    ("MEM", 0x008): "固件堆内存分配/heap alloc；C200 单参数 size，锁保护后返回 pointer。",
    ("MEM", 0x00C): "固件堆内存释放；C200 单参数 ptr，锁保护后调用内部 free。",
    ("MEM", 0x010): "firmware heap calloc-like；C200 使用 count,size，按 count*align4(size) 分配并清零。",
    ("MEM", 0x014): "firmware heap realloc-like；C200 使用 ptr,new_size，支持 ptr=0 alloc 和 size=0 free。",
    ("MEM", 0x01C): "heap tracking begin；C200 使用 free_on_finish flag，开启 tracking 并清记录计数。",
    ("MEM", 0x020): "heap tracking report/count；C200 使用 summary_only flag，返回 tracked 记录计数。",
    ("MEM", 0x024): "heap tracking finish；C200 结束 tracking，free_on_finish 非 0 时可释放记录 pointer。",
    ("MEM", 0x028): "heap tracking retain；C200 查 tracked record table，命中时递增 refcount-like 字段并返回 pointer。",
    ("MEM", 0x02C): "heap tracking release；C200 查 tracked record table，递减 refcount-like 字段，归零时释放 pointer。",
    ("RES", 0x090): "资源/图片状态 snapshot；C200 从 0xb0003004 取状态源，向 out_state 写 7 个 word，无稳定 return value。",
    ("RES", 0x094): "trace/log；历史 DLX loader 名称已废弃。",
    ("SYS", 0x004): "内部 system resource close；C200 使用 resource_id 1..10 查资源表并调用 close callback，不是 app exit。",
    ("SYS", 0x040): "raw PCM attenuation setter；C200 clamp 到 0..98，写 pending value，下一次 audio write 量化并应用。",
    ("SYS", 0x044): "raw PCM attenuation getter；C200 无参数，返回当前 effective attenuation（0..96，步进 3）。",
    ("SYS", 0x058): "打包音效 init/start；C200 使用 a0=descriptor，成功置 0x804c4ba4 并返回 1。",
    ("SYS", 0x05C): "打包音效 descriptor 操作；C200 使用 slot,descriptor,a2,flags 四参数。",
    ("SYS", 0x060): "打包音效状态置位；C200 无参数，0x804c4ba8 从 0 置 1 时返回 1。",
    ("SYS", 0x064): "打包音效状态清除；C200 无参数，0x804c4ba8 从 1 清 0 时返回 1。",
    ("SYS", 0x068): "打包音效 release/stop；C200 无参数，关闭全局 handle 并清 0x804c4ba4。",
    ("SYS", 0x06C): "raw audio open/init；C200 使用 device,format,channels 三参数，format/channels 截成 signed 8-bit，尾部固定 v0=0。",
    ("SYS", 0x074): "raw audio ready query；C200 无参数，返回 0x8058+0x6e8 > 0。",
    ("SYS", 0x078): "raw audio write；C200 使用 buffer,bytes，bytes<=0 返回 -1，正常返回已消费 byte 数。",
    ("SYS", 0x088): "raw keycode query；C200 无参数，读取硬件输入寄存器并返回 raw code。",
    ("SYS", 0x080): "阻塞式 busy-wait delay；C200 按系统校准值把 a0 换算成循环次数，无稳定 return value。",
    ("SYS", 0x08C): "raw audio reset/init；C200 无参数，关闭全局 audio object 后进入初始化路径，无稳定 return value。",
    ("SYS", 0x090): "raw audio state pointer getter；C200 无参数，直接返回全局 state 0x80362830。",
    ("SYS", 0x09C): "timer/rate preset 选择；C200 把 a0 clamp 到 0..14 后查内部表，无稳定 return value。",
    ("SYS", 0x0A0): "raw audio finish/stop；C200 无参数，真机安全返回且停止声音；模拟器后端 timer 状态存在差异，无稳定 return value。",
    ("SYS", 0x0AC): "alarm set；C200 使用 alarm_data,slot，record size 0x2b8，未见 slot bounds check，return value 成功 1。",
    ("SYS", 0x0B0): "alarm get；C200 使用 alarm_data,slot，从 file offset 0x578+slot*0x2b8 复制 0x2b8 byte，return value 成功 1。",
    ("SYS", 0x0B8): "alarm due record get；C200 打开 alarm.db，扫描 0x2b8 byte record，并向 out buffer 复制整条 record。",
}


def parse_sdk_defines(path: Path) -> dict[tuple[str, int], list[str]]:
    out: dict[tuple[str, int], list[str]] = collections.defaultdict(list)
    for line in path.read_text(encoding="utf-8").splitlines():
        match = DEFINE_RE.match(line.strip())
        if not match:
            continue
        name, table, value = match.groups()
        if name in NON_API_DEFINE_NAMES:
            continue
        if not (name.endswith("_LIKE") or name in CORE_API_DEFINE_NAMES):
            continue
        offset = int(value, 16)
        if offset >= 0x1000:
            continue
        out[(table, offset)].append(name)
    return dict(out)


def inventory_totals(path: Path) -> tuple[collections.Counter[int], dict[int, set[str]]]:
    items = json.loads(path.read_text(encoding="utf-8"))
    counts: collections.Counter[int] = collections.Counter()
    apps_by_offset: dict[int, set[str]] = collections.defaultdict(set)
    for item in items:
        app_name = str(item.get("name", ""))
        for raw, count in item.get("api_offset_counts", {}).items():
            offset = int(raw.replace("+", ""), 16)
            counts[offset] += int(count)
            apps_by_offset[offset].add(app_name)
    return counts, apps_by_offset


def confidence(table: str, offset: int, total_calls: int, app_count: int, has_name: bool) -> str:
    if (table, offset) in {("GUI", 0x6C0), ("GUI", 0x750)}:
        return "高"
    if (table, offset) in {("GUI", 0x2B8), ("MEM", 0x008), ("MEM", 0x00C), ("FS", 0x000), ("FS", 0x004), ("FS", 0x008), ("FS", 0x00C)}:
        return "较高"
    if has_name and ((table, offset) in NOTES or total_calls >= 20 or app_count >= 3):
        return "中"
    if has_name:
        return "低"
    return "待归类"


def write_markdown(
    out: Path,
    sdk_defs: dict[tuple[str, int], list[str]],
    totals: collections.Counter[int],
    apps_by_offset: dict[int, set[str]],
) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# BDA API 覆盖表")
    lines.append("")
    lines.append("本表由 `reverse/bda_api_catalog.py` 生成，合并了 `reverse/reports/bda_inventory.json` 的原机 BDA call inventory 和 `reverse/bda_research_sdk.h` 里的 SDK 命名。")
    lines.append("")
    lines.append("注意：inventory 里的 offset 统计是未分类的 indirect call offset，不能单独证明属于 GUI/FS/SYS/MEM/RES 哪张 table；table name 来自 SDK 已命名项和人工逆向笔记。")
    lines.append("因此表中的统计列表示“同 offset 在原机 BDA 中出现的总体热度”，不是该 table entry 已经独占确认的调用次数。")
    lines.append("")
    lines.append("| Table | Offset | SDK name | Raw calls same offset | App count | Confidence | Notes |")
    lines.append("| --- | ---: | --- | ---: | ---: | --- | --- |")
    rows = sorted(sdk_defs.items(), key=lambda item: (item[0][0], item[0][1]))
    for (table, offset), names in rows:
        total_calls = totals.get(offset, 0)
        app_count = len(apps_by_offset.get(offset, set()))
        note = NOTES.get((table, offset), "已有 SDK name，但还缺少更细的 ABI/lifecycle 证据。")
        conf = confidence(table, offset, total_calls, app_count, True)
        lines.append(
            f"| {table} | +0x{offset:03x} | `{', '.join(names)}` | {total_calls} | {app_count} | {conf} | {note} |"
        )
    lines.append("")
    lines.append("## 未命名高频 Offset")
    lines.append("")
    lines.append("这些 offset 在原机 BDA 中出现，但还没有稳定映射到具体 table 和 SDK name。后续应使用 `bda_table_call_scan.py --context` 在原始样本上按全局 table pointer 分类。")
    lines.append("")
    unnamed_lines: list[str] = []
    named_offsets = {offset for _table, offset in sdk_defs}
    for offset, total_calls in totals.most_common(40):
        if offset in named_offsets:
            continue
        unnamed_lines.append(f"| +0x{offset:03x} | {total_calls} | {len(apps_by_offset[offset])} |")
    if unnamed_lines:
        lines.append("| Offset | Raw call count | App count |")
        lines.append("| ---: | ---: | ---: |")
        lines.extend(unnamed_lines)
    else:
        lines.append("当前 inventory 前 40 个高频 offset 都已有 SDK name；剩余长尾 offset 仍需按应用继续分类。")
    lines.append("")
    lines.append("## 后续验证建议")
    lines.append("")
    lines.append("- 有本地原机 BDA 样本时，先运行 `python reverse\\bda_inventory.py --root 应用\\程序` 更新 inventory。")
    lines.append("- 对单个应用按表分类：`python reverse\\bda_table_call_scan.py 应用\\程序\\计算器.bda --context`。")
    lines.append("- 有 `C200.bin` 时，运行 `python reverse\\system_bin_probe.py --root .` 和系统 API 交叉引用脚本，把 table entry function 与系统实现地址对应起来。")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="从原机 BDA 清点和 SDK 宏生成中文 API 覆盖表。",
        add_help=False,
    )
    ap._optionals.title = "选项"
    ap.add_argument("-h", "--help", action="help", help="显示帮助并退出")
    ap.add_argument("--inventory", type=Path, default=Path("reverse") / "reports" / "bda_inventory.json", help="原机 BDA inventory JSON")
    ap.add_argument("--sdk", type=Path, default=Path("reverse") / "bda_research_sdk.h", help="SDK header")
    ap.add_argument("-o", "--output", type=Path, default=Path("reverse") / "docs" / "api_catalog.md", help="输出 Markdown 文件")
    ns = ap.parse_args()

    sdk_defs = parse_sdk_defines(ns.sdk)
    totals, apps_by_offset = inventory_totals(ns.inventory)
    write_markdown(ns.output, sdk_defs, totals, apps_by_offset)
    print(f"sdk_named_offsets={len(sdk_defs)}")
    print(f"inventory_offsets={len(totals)}")
    print(f"output={ns.output}")


if __name__ == "__main__":
    main()
