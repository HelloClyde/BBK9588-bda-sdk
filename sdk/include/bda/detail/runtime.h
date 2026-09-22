#ifndef BDA_DETAIL_RUNTIME_H
#define BDA_DETAIL_RUNTIME_H

#include "../../bda_types.h"

/* Internal dynamic system-table locations for the kj409588/C200 firmware. */
#define BDA_SDK_INTERNAL_GUI_TABLE_ADDR 0x81c00004u
#define BDA_SDK_INTERNAL_FS_TABLE_ADDR  0x81c00008u
#define BDA_SDK_INTERNAL_SYS_TABLE_ADDR 0x81c0000cu
#define BDA_SDK_INTERNAL_MEM_TABLE_ADDR 0x81c00010u

#define BDA_SDK_INTERNAL_GUI_MSGBOX            0x2b8u
#define BDA_SDK_INTERNAL_GUI_EVENT_POLL        0x030u
#define BDA_SDK_INTERNAL_GUI_FRAME_RELEASE     0x04cu
#define BDA_SDK_INTERNAL_GUI_EVENT_STEP        0x050u
#define BDA_SDK_INTERNAL_GUI_EVENT_DISPATCH    0x054u
#define BDA_SDK_INTERNAL_GUI_DRAW_GUARD        0x074u
#define BDA_SDK_INTERNAL_GUI_REGISTER_FRAME    0x084u
#define BDA_SDK_INTERNAL_GUI_FRAME_STOP        0x088u
#define BDA_SDK_INTERNAL_GUI_DEFAULT_PROC      0x08cu
#define BDA_SDK_INTERNAL_GUI_FRAME_ACTIVATE    0x098u
#define BDA_SDK_INTERNAL_GUI_OBJECT_DRAW_BEGIN 0x0e4u
#define BDA_SDK_INTERNAL_GUI_OBJECT_DRAW_END   0x0e8u
#define BDA_SDK_INTERNAL_GUI_CLOSE_FRAME       0x17cu
#define BDA_SDK_INTERNAL_GUI_WINDOW_TIMER_START 0x1acu
#define BDA_SDK_INTERNAL_GUI_WINDOW_TIMER_STOP  0x1b0u
#define BDA_SDK_INTERNAL_GUI_WINDOW_TIMER_EXISTS 0x1b4u
#define BDA_SDK_INTERNAL_GUI_WINDOW_TIMER_CLOCK 0x1bcu
#define BDA_SDK_INTERNAL_GUI_DRAW_OBJECT       0x2fcu
#define BDA_SDK_INTERNAL_GUI_CURRENT_DRAW      0x304u
#define BDA_SDK_INTERNAL_GUI_END_DRAW          0x30cu
#define BDA_SDK_INTERNAL_GUI_COMPAT_CREATE     0x310u
#define BDA_SDK_INTERNAL_GUI_COMPAT_FREE       0x314u
#define BDA_SDK_INTERNAL_GUI_SET_TEXT_MODE     0x338u
#define BDA_SDK_INTERNAL_GUI_SET_TEXT_COLOR    0x33cu
#define BDA_SDK_INTERNAL_GUI_SELECT_DRAW       0x358u
#define BDA_SDK_INTERNAL_GUI_PUT_PIXEL         0x368u
#define BDA_SDK_INTERNAL_GUI_PUT_PIXEL_RGB     0x36cu
#define BDA_SDK_INTERNAL_GUI_RGB               0x378u
#define BDA_SDK_INTERNAL_GUI_LINE_TO           0x37cu
#define BDA_SDK_INTERNAL_GUI_MOVE_TO           0x380u
#define BDA_SDK_INTERNAL_GUI_CIRCLE            0x388u
#define BDA_SDK_INTERNAL_GUI_RECTANGLE         0x38cu
#define BDA_SDK_INTERNAL_GUI_RENDER_PICTURE    0x410u
#define BDA_SDK_INTERNAL_GUI_CONTEXT_COPY      0x418u
#define BDA_SDK_INTERNAL_GUI_DRAW_TEXT         0x4f0u
#define BDA_SDK_INTERNAL_GUI_DRAW_VX           0x540u
#define BDA_SDK_INTERNAL_GUI_INPUT_PACKET      0x5d4u
#define BDA_SDK_INTERNAL_GUI_SCREEN_BUFFER     0x6b0u
#define BDA_SDK_INTERNAL_GUI_TOUCH_POSITION    0x6c0u
#define BDA_SDK_INTERNAL_GUI_TICK_COUNT_25MS   0x6d8u
#define BDA_SDK_INTERNAL_GUI_MILLISECOND_TIMER_START 0x714u
#define BDA_SDK_INTERNAL_GUI_MILLISECOND_TIMER_STOP  0x718u
#define BDA_SDK_INTERNAL_GUI_MILLISECOND_COUNT       0x71cu
#define BDA_SDK_INTERNAL_GUI_SCREEN_ORIENTATION      0x738u
#define BDA_SDK_INTERNAL_GUI_RAW_EVENT_FETCH         0x750u

#define BDA_SDK_INTERNAL_FS_OPEN       0x000u
#define BDA_SDK_INTERNAL_FS_CLOSE      0x004u
#define BDA_SDK_INTERNAL_FS_READ       0x008u
#define BDA_SDK_INTERNAL_FS_WRITE      0x00cu
#define BDA_SDK_INTERNAL_FS_SEEK       0x010u
#define BDA_SDK_INTERNAL_FS_TELL       0x014u
#define BDA_SDK_INTERNAL_FS_ERROR      0x01cu
#define BDA_SDK_INTERNAL_FS_REMOVE     0x024u
#define BDA_SDK_INTERNAL_FS_RENAME     0x028u
#define BDA_SDK_INTERNAL_FS_CHDIR      0x02cu
#define BDA_SDK_INTERNAL_FS_MKDIR      0x030u
#define BDA_SDK_INTERNAL_FS_RMDIR      0x034u
#define BDA_SDK_INTERNAL_FS_FINDFIRST  0x03cu
#define BDA_SDK_INTERNAL_FS_FINDNEXT   0x040u
#define BDA_SDK_INTERNAL_FS_FINDCLOSE  0x044u
#define BDA_SDK_INTERNAL_FS_DISK_INFO  0x048u
#define BDA_SDK_INTERNAL_FS_GETCWD     0x050u
#define BDA_SDK_INTERNAL_FS_PATH_INFO  0x054u
#define BDA_SDK_INTERNAL_FS_FLUSH_ALL  0x074u
#define BDA_SDK_INTERNAL_FS_STORAGE_READY 0x07cu

#define BDA_SDK_INTERNAL_MEM_ALLOC 0x008u
#define BDA_SDK_INTERNAL_MEM_FREE  0x00cu

#define BDA_SDK_INTERNAL_SYS_DELAY 0x080u

static inline void *bda_sdk_internal_table(u32 address) {
    return *(void **)address;
}

static inline void *bda_sdk_internal_api(void *table, u32 offset) {
    return *(void **)((u8 *)table + offset);
}

static inline void *bda_sdk_internal_gui(void) {
    return bda_sdk_internal_table(BDA_SDK_INTERNAL_GUI_TABLE_ADDR);
}

static inline void *bda_sdk_internal_fs(void) {
    return bda_sdk_internal_table(BDA_SDK_INTERNAL_FS_TABLE_ADDR);
}

static inline void *bda_sdk_internal_sys(void) {
    return bda_sdk_internal_table(BDA_SDK_INTERNAL_SYS_TABLE_ADDR);
}

static inline void *bda_sdk_internal_mem(void) {
    return bda_sdk_internal_table(BDA_SDK_INTERNAL_MEM_TABLE_ADDR);
}

static inline int bda_sdk_internal_call0(void *table, u32 offset) {
    typedef int (*fn_t)(void);
    return ((fn_t)bda_sdk_internal_api(table, offset))();
}

static inline int bda_sdk_internal_call1(void *table, u32 offset, u32 a0) {
    typedef int (*fn_t)(u32);
    return ((fn_t)bda_sdk_internal_api(table, offset))(a0);
}

static inline int bda_sdk_internal_call2(void *table, u32 offset, u32 a0, u32 a1) {
    typedef int (*fn_t)(u32, u32);
    return ((fn_t)bda_sdk_internal_api(table, offset))(a0, a1);
}

static inline int bda_sdk_internal_call3(
    void *table, u32 offset, u32 a0, u32 a1, u32 a2
) {
    typedef int (*fn_t)(u32, u32, u32);
    return ((fn_t)bda_sdk_internal_api(table, offset))(a0, a1, a2);
}

static inline int bda_sdk_internal_call4(
    void *table, u32 offset, u32 a0, u32 a1, u32 a2, u32 a3
) {
    typedef int (*fn_t)(u32, u32, u32, u32);
    return ((fn_t)bda_sdk_internal_api(table, offset))(a0, a1, a2, a3);
}

static inline int bda_sdk_internal_call5(
    void *table, u32 offset, u32 a0, u32 a1, u32 a2, u32 a3, u32 a4
) {
    typedef int (*fn_t)(u32, u32, u32, u32, u32);
    return ((fn_t)bda_sdk_internal_api(table, offset))(a0, a1, a2, a3, a4);
}

static inline int bda_sdk_internal_call6(
    void *table,
    u32 offset,
    u32 a0,
    u32 a1,
    u32 a2,
    u32 a3,
    u32 a4,
    u32 a5
) {
    typedef int (*fn_t)(u32, u32, u32, u32, u32, u32);
    return ((fn_t)bda_sdk_internal_api(table, offset))(a0, a1, a2, a3, a4, a5);
}

#endif
