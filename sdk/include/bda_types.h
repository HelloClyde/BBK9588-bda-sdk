#ifndef BDA_TYPES_H
#define BDA_TYPES_H

#define BDA_SDK_VERSION_MAJOR 0u
#define BDA_SDK_VERSION_MINOR 1u
#define BDA_SDK_VERSION_PATCH 0u
#define BDA_SDK_VERSION_PRERELEASE 1u
#define BDA_SDK_VERSION_STRING "0.1.0-alpha.1"

/* Common freestanding types shared by every public SDK module. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef unsigned long long u64;
typedef signed short s16;
typedef int s32;
typedef unsigned int bda_size_t;
typedef void *bda_handle_t;
typedef int (*bda_wndproc_t)(bda_handle_t, u32, u32, u32);

#endif
