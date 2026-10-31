/* SPDX-License-Identifier: Apache-2.0 OR GPL-2.0-only */
#ifndef BDA_9688_CAMERA_H
#define BDA_9688_CAMERA_H
#include "bda_9688_platform.h"

/* Exact V2.32 private ROM binding, not a public BDA table ABI. QVGA only.
 * Zero-initialize the context; use one foreground task and no native camera
 * UI/other camera owner concurrently. See docs/verified/9688_media_api.md for evidence.
 */
#define BDA_9688_CAMERA_MAGIC 0x43413936u
#define BDA_9688_CAMERA_WIDTH 320u
#define BDA_9688_CAMERA_HEIGHT 240u
#define BDA_9688_CAMERA_BYTES (320u * 240u * 2u)
enum { BDA_9688_CAMERA_CLOSED, BDA_9688_CAMERA_OPEN,
       BDA_9688_CAMERA_CAPTURING, BDA_9688_CAMERA_FRAME,
       BDA_9688_CAMERA_FAULT };
enum { BDA_9688_CAMERA_YUYV = 1 };
typedef struct bda_9688_camera_frame {
    const u8 *pixels; /* Borrowed uncached DMA view; invalidated by start/close. */
    u32 width, height, stride, bytes, format;
} bda_9688_camera_frame_t;
typedef struct bda_9688_camera_rom {
    u32 init, close, start, ready, clear_ready, sensor_probe, sensor_init, sensor_write;
    u32 irq_handler, irq_number, irq_slot, irq_default;
    u32 opened, device, done, native_ui_state, clock_gate_mask;
    const bda_9688_guard_t *guards;
    u32 guard_count;
} bda_9688_camera_rom_t;
typedef struct bda_9688_camera {
    u32 magic, state;
    bda_9688_context_t platform;
    const bda_9688_camera_rom_t *rom;
    u32 device, buffer;
    u32 saved_clock, saved_irq_mask, saved_irq_handler, saved_irq_argument;
    u32 saved_config, saved_control, saved_dma;
    u32 saved_i2c_control, saved_i2c_divider;
    u32 saved_gpio[5];
} bda_9688_camera_t;

static const bda_9688_guard_t bda_9688_camera_guards_4730[] = {
    {0x80027314u, 0x28u, 0x043f8806u}, /* sensor_i2c_enable */
    {0x80225c68u, 0x138u, 0xb22fbf68u}, /* cim_init */
    {0x8022569cu, 0x90u, 0xc97faa86u}, /* cim_close */
    {0x80225da0u, 0xa4u, 0xc050b977u}, /* cim_release */
    {0x8022572cu, 0xa0u, 0x9023afaau}, /* cim_start */
    {0x802257ccu, 0x1cu, 0x481f3903u}, /* cim_ready */
    {0x80226e70u, 0xe8u, 0xa5cda1aeu}, /* sensor_probe */
    {0x80226e54u, 0x1cu, 0xc5fddcf8u}, /* sensor_init_wrapper */
    {0x80226f58u, 0x190u, 0xcde1c0f1u}, /* sensor_init */
    {0x80226df8u, 0x5cu, 0xe4383df1u}, /* sensor_write */
    {0x80225e44u, 0x64u, 0xecb8af11u}, /* cim_irq */
    {0x802257e8u, 0x240u, 0x10e6c1b7u}, /* cim_qvga_config */
    {0x80225a28u, 0x240u, 0x6a0807f8u}, /* cim_other_config */
    {0x804a46e0u, 0xcu, 0x7f25fe1du}, /* sensor_lengths */
    {0x804a4b4cu, 0xcu, 0xac45431au}, /* sensor_table_pointers */
    {0x804a4a3cu, 0x110u, 0xadfa05fdu}, /* sensor_mode0_registers */
    {0x804a4704u, 0x108u, 0x97c912b7u}, /* sensor_mode2_registers */
};
static const bda_9688_guard_t bda_9688_camera_guards_4740[] = {
    {0x800179bcu, 0x28u, 0x043f8806u}, /* sensor_i2c_enable */
    {0x80222cf8u, 0x138u, 0x3be13908u}, /* cim_init */
    {0x802226dcu, 0x90u, 0x8346920au}, /* cim_close */
    {0x80222e30u, 0xa4u, 0xebaf927eu}, /* cim_release */
    {0x8022276cu, 0xa0u, 0xc1574aabu}, /* cim_start */
    {0x8022280cu, 0x1cu, 0xc236b94u}, /* cim_ready */
    {0x80222430u, 0xe8u, 0xf520fba5u}, /* sensor_probe */
    {0x80222414u, 0x1cu, 0x293c0a0au}, /* sensor_init_wrapper */
    {0x80222518u, 0x190u, 0x59595052u}, /* sensor_init */
    {0x802223b8u, 0x5cu, 0xd775f1efu}, /* sensor_write */
    {0x80222ed4u, 0x64u, 0xd1a1f204u}, /* cim_irq */
    {0x80222828u, 0x268u, 0x674e42e1u}, /* cim_qvga_config */
    {0x80222a90u, 0x268u, 0xcd689b31u}, /* cim_other_config */
    {0x804a4a20u, 0xcu, 0xd52c3696u}, /* sensor_lengths */
    {0x804a4e90u, 0xcu, 0x67568992u}, /* sensor_table_pointers */
    {0x804a4d80u, 0x110u, 0xc52ea93eu}, /* sensor_mode0_registers */
    {0x804a4a44u, 0x10cu, 0x19c99d81u}, /* sensor_mode2_registers */
};
static inline const bda_9688_camera_rom_t *bda_9688_camera_rom(enum bda_9688_chip chip) {
    static const bda_9688_camera_rom_t bindings[2] = {
        {0x80225c68u, 0x8022569cu, 0x8022572cu, 0x802257ccu, 0x802257d8u, 0x80226e70u, 0x80226e54u, 0x80226df8u, 0x80225e44u, 0x12u, 0x804a9ef4u, 0x80004d74u, 0x808adf44u, 0x808adf48u, 0x808adf40u, 0x804b5b34u, 0x800000u, bda_9688_camera_guards_4730, 17u},
        {0x80222cf8u, 0x802226dcu, 0x8022276cu, 0x8022280cu, 0x80222818u, 0x80222430u, 0x80222414u, 0x802223b8u, 0x80222ed4u, 0x11u, 0x804aa22cu, 0x800052e4u, 0x806fa424u, 0x806fa428u, 0x806fa420u, 0x804b8844u, 0x200u, bda_9688_camera_guards_4740, 17u},
    };
    if (chip == BDA_9688_CHIP_JZ4730) return &bindings[0];
    if (chip == BDA_9688_CHIP_JZ4740) return &bindings[1];
    return (const bda_9688_camera_rom_t *)0;
}
static inline u32 bda_9688_camera_read(u32 address) { return *(volatile u32 *)address; }
static inline void bda_9688_camera_write(u32 address, u32 value) { *(volatile u32 *)address = value; }
static inline u32 bda_9688_camera_gate_mask(const bda_9688_camera_t *c) {
    return c->rom->clock_gate_mask | (c->platform.profile->chip==BDA_9688_CHIP_JZ4730?0x100u:8u);
}
static inline void bda_9688_camera_zero(volatile u32 *words, u32 count) {
    while (count--) *words++ = 0; /* Freestanding -Os must not synthesize memset. */
}
static inline u32 bda_9688_camera_lock(void) {
    u32 old, masked;
    __asm__ volatile("mfc0 %0,$12\n\tnop" : "=r"(old) :: "memory"); masked = old & ~1u;
    __asm__ volatile("mtc0 %0,$12\n\tnop\n\tnop\n\tnop" :: "r"(masked) : "memory");
    return old;
}
static inline void bda_9688_camera_unlock(u32 old) {
    __asm__ volatile("mtc0 %0,$12\n\tnop\n\tnop\n\tnop" :: "r"(old) : "memory");
}
static inline void bda_9688_camera_masked(u32 address, u32 mask, u32 value) {
    bda_9688_camera_write(address, (bda_9688_camera_read(address) & ~mask) | (value & mask));
}
static inline int bda_9688_camera_ram(u32 address, u32 bytes) {
    return !(address & 3u) && address >= 0x804aa000u && address < BDA_9688_INTERNAL_RUNTIME_BASE &&
        bytes <= BDA_9688_INTERNAL_RUNTIME_BASE - address;
}
static inline int bda_9688_camera_device_valid(const bda_9688_camera_t *c) {
    if(!bda_9688_camera_ram(c->device,32u) ||
       !bda_9688_camera_ram(c->buffer,BDA_9688_CAMERA_BYTES+1024u) ||
       (c->device<c->buffer+BDA_9688_CAMERA_BYTES+1024u && c->buffer<c->device+32u)) return 0;
    return bda_9688_camera_read(c->device)==c->buffer &&
        bda_9688_camera_read(c->device+4u)==BDA_9688_CAMERA_BYTES &&
        bda_9688_camera_read(c->device+0x10u)==((c->device+0x10u)&0x1fffffffu) &&
        bda_9688_camera_read(c->device+0x14u)==(c->buffer&0x1fffffffu) &&
        bda_9688_camera_read(c->device+0x18u)==0x52052018u &&
        bda_9688_camera_read(c->device+0x1cu)==(0x50000000u|BDA_9688_CAMERA_BYTES/4u);
}
static inline int bda_9688_camera_valid(const bda_9688_camera_t *camera) {
    if (!camera || camera->magic != BDA_9688_CAMERA_MAGIC || !camera->platform.profile)
        return BDA_9688_E_STATE;
    const bda_9688_camera_rom_t *expected = bda_9688_camera_rom(camera->platform.profile->chip);
    return expected && camera->rom && camera->rom->init == expected->init &&
        camera->rom->close == expected->close && camera->rom->device == expected->device &&
        camera->rom->irq_slot == expected->irq_slot ? BDA_9688_OK : BDA_9688_E_STATE;
}
static inline int bda_9688_camera_init(bda_9688_camera_t *camera,
                                        const bda_9688_context_t *platform) {
    if (!camera || !platform) return BDA_9688_E_ARGUMENT;
    if (camera->magic == BDA_9688_CAMERA_MAGIC && camera->state != BDA_9688_CAMERA_CLOSED)
        return BDA_9688_E_BUSY;
    const bda_9688_camera_rom_t *rom = platform->profile
        ? bda_9688_camera_rom(platform->profile->chip) : (const bda_9688_camera_rom_t *)0;
    if (!rom) return BDA_9688_E_UNSUPPORTED;
    int result = bda_9688_check_guards(platform, rom->guards, rom->guard_count);
    if (result) return result;
    bda_9688_camera_zero((volatile u32 *)camera, sizeof(*camera)/sizeof(u32));
    camera->magic = BDA_9688_CAMERA_MAGIC; camera->platform.profile = platform->profile;
    for (unsigned i=0;i<5;i++) camera->platform.runtime_tables[i]=platform->runtime_tables[i];
    camera->rom = rom;
    return BDA_9688_OK;
}
static inline void bda_9688_camera_board_save(bda_9688_camera_t *c) {
    c->saved_irq_mask = bda_9688_camera_read(0xb0001004u);
    c->saved_irq_handler = bda_9688_camera_read(c->rom->irq_slot);
    c->saved_irq_argument = bda_9688_camera_read(c->rom->irq_slot + 4u);
    c->saved_config = bda_9688_camera_read(0xb3060000u);
    c->saved_control = bda_9688_camera_read(0xb3060004u);
    c->saved_dma = bda_9688_camera_read(0xb3060020u);
    c->saved_i2c_control = *(volatile u8 *)0xb0042004u;
    c->saved_i2c_divider = *(volatile u16 *)0xb004200cu;
    if (c->platform.profile->chip == BDA_9688_CHIP_JZ4730) {
        static const u32 addresses[4] = {0xb0010020u,0xb0010004u,0xb0010014u,0xb0010000u};
        for (unsigned i=0;i<4;i++) c->saved_gpio[i]=bda_9688_camera_read(addresses[i]);
    } else {
        static const u32 addresses[5] = {0xb0010340u,0xb0010350u,0xb0010360u,0xb0010310u,0xb0010330u};
        for (unsigned i=0;i<5;i++) c->saved_gpio[i]=bda_9688_camera_read(addresses[i]);
    }
}
static inline void bda_9688_camera_board_on(bda_9688_camera_t *c) {
    if (c->platform.profile->chip == BDA_9688_CHIP_JZ4730) {
        bda_9688_camera_masked(0xb0010020u,0x04000000u,0);
        bda_9688_camera_masked(0xb0010004u,0x04000000u,0x04000000u);
        bda_9688_camera_masked(0xb0010014u,0x00300000u,0);
        bda_9688_camera_masked(0xb0010000u,0x04000000u,0);
    } else {
        bda_9688_camera_write(0xb0010348u,0x00200000u);
        bda_9688_camera_write(0xb0010358u,0x00200000u);
        bda_9688_camera_write(0xb0010364u,0x00200000u);
        bda_9688_camera_write(0xb0010318u,0x00200000u);
        bda_9688_camera_write(0xb0010344u,0x0183c0ffu);
        bda_9688_camera_write(0xb0010358u,0x0003c0ffu);
        bda_9688_camera_write(0xb0010334u,0x0183c0ffu);
        bda_9688_camera_write(0xb0010354u,0x01800000u);
    }
    bda_9688_camera_masked(0xb0000020u,bda_9688_camera_gate_mask(c),0);
}
static inline void bda_9688_camera_quiesce(bda_9688_camera_t *c) {
    bda_9688_camera_write(0xb0001008u,1u<<c->rom->irq_number);
    bda_9688_camera_write(0xb3060004u,bda_9688_camera_read(0xb3060004u)&~5u);
    bda_9688_camera_write(0xb3060008u,0);
    __asm__ volatile("sync" ::: "memory");
    (void)bda_9688_camera_read(0xb3060004u);
}
static inline void bda_9688_camera_board_restore(bda_9688_camera_t *c) {
    bda_9688_camera_write(0xb3060020u,c->saved_dma);
    bda_9688_camera_write(0xb3060000u,c->saved_config);
    bda_9688_camera_write(0xb3060004u,c->saved_control);
    bda_9688_camera_write(c->rom->irq_slot,c->saved_irq_handler);
    bda_9688_camera_write(c->rom->irq_slot+4u,c->saved_irq_argument);
    if (c->platform.profile->chip == BDA_9688_CHIP_JZ4730) {
        static const u32 addresses[4]={0xb0010020u,0xb0010004u,0xb0010014u,0xb0010000u};
        static const u32 masks[4]={0x04000000u,0x04000000u,0x00300000u,0x04000000u};
        for(unsigned i=0;i<4;i++) bda_9688_camera_masked(addresses[i],masks[i],c->saved_gpio[i]);
    } else {
        static const u32 bases[5]={0xb0010340u,0xb0010350u,0xb0010360u,0xb0010310u,0xb0010330u};
        static const u32 masks[5]={0x01a3c0ffu,0x01a3c0ffu,0x00200000u,0x00200000u,0x0183c0ffu};
        for(unsigned i=0;i<5;i++) {
            bda_9688_camera_write(bases[i]+4u,c->saved_gpio[i]&masks[i]);
            bda_9688_camera_write(bases[i]+8u,(~c->saved_gpio[i])&masks[i]);
        }
    }
    *(volatile u16 *)0xb004200cu=(u16)c->saved_i2c_divider;
    *(volatile u8 *)0xb0042004u=(u8)c->saved_i2c_control;
    bda_9688_camera_masked(0xb0000020u,bda_9688_camera_gate_mask(c),c->saved_clock);
    bda_9688_camera_write((c->saved_irq_mask&(1u<<c->rom->irq_number))?0xb0001008u:0xb000100cu,
                          1u<<c->rom->irq_number);
}
static inline int bda_9688_camera_owned(const bda_9688_camera_t *c) {
    return bda_9688_camera_read(c->rom->opened)==1u &&
        bda_9688_camera_read(c->rom->device)==c->device &&
        bda_9688_camera_device_valid(c) &&
        bda_9688_camera_read(c->rom->irq_slot)==c->rom->irq_handler &&
        !bda_9688_camera_read(c->rom->irq_slot+4u) &&
        !(bda_9688_camera_read(0xb0000020u)&bda_9688_camera_gate_mask(c)) &&
        !(*(volatile u8 *)0xb0042004u&1u);
}
static inline int bda_9688_camera_close(bda_9688_camera_t *c) {
    int result=bda_9688_camera_valid(c); if(result)return result;
    if(c->state==BDA_9688_CAMERA_CLOSED)return BDA_9688_OK;
    if(c->state==BDA_9688_CAMERA_FAULT || !bda_9688_camera_owned(c))return BDA_9688_E_BUSY;
    result=bda_9688_check_guards(&c->platform,c->rom->guards,c->rom->guard_count);
    if(result)return result;
    u32 saved=bda_9688_camera_lock();
    if(!bda_9688_camera_owned(c)){bda_9688_camera_unlock(saved);return BDA_9688_E_BUSY;}
    bda_9688_camera_quiesce(c);bda_9688_camera_unlock(saved);
    ((void (*)(u32,u32))c->rom->sensor_write)(9u,0x11u);
    ((void (*)(void))c->rom->close)();
    saved=bda_9688_camera_lock();
    bda_9688_camera_write(c->rom->device,0);bda_9688_camera_write(c->rom->done,0);
    bda_9688_camera_board_restore(c);bda_9688_camera_unlock(saved);
    c->device=c->buffer=0;c->state=BDA_9688_CAMERA_CLOSED;
    return BDA_9688_OK;
}
static inline int bda_9688_camera_open_qvga(bda_9688_camera_t *c) {
    int result=bda_9688_camera_valid(c);if(result)return result;
    if(c->state!=BDA_9688_CAMERA_CLOSED)return BDA_9688_E_BUSY;
    result=bda_9688_check_guards(&c->platform,c->rom->guards,c->rom->guard_count);if(result)return result;
    u32 saved=bda_9688_camera_lock();
    if(bda_9688_camera_read(c->rom->opened) || bda_9688_camera_read(c->rom->device) ||
       bda_9688_camera_read(c->rom->native_ui_state) ||
       bda_9688_camera_read(c->rom->irq_slot)!=c->rom->irq_default) {
        bda_9688_camera_unlock(saved);return BDA_9688_E_BUSY;
    }
    /* The CIM register bus is not assumed accessible with its clock gated. */
    c->saved_clock=bda_9688_camera_read(0xb0000020u);
    bda_9688_camera_masked(0xb0000020u,bda_9688_camera_gate_mask(c),0);
    if((bda_9688_camera_read(0xb3060004u)&5u) || (*(volatile u8 *)0xb0042004u&1u)) {
        bda_9688_camera_masked(0xb0000020u,bda_9688_camera_gate_mask(c),c->saved_clock);
        bda_9688_camera_unlock(saved);return BDA_9688_E_BUSY;
    }
    bda_9688_camera_board_save(c);
    bda_9688_camera_write(c->rom->opened,2u); /* Reserve before native allocation; no IRQ lock around malloc/I2C. */
    bda_9688_camera_board_on(c);bda_9688_camera_unlock(saved);
    u32 descriptor[10];
    bda_9688_camera_zero(descriptor,10u);descriptor[0]=2u;descriptor[1]=320u;descriptor[2]=240u;
    result=((int (*)(const u32 *))c->rom->init)(descriptor);
    if(result) {
        saved=bda_9688_camera_lock();bda_9688_camera_quiesce(c);
        bda_9688_camera_write(c->rom->opened,0);bda_9688_camera_write(c->rom->device,0);
        bda_9688_camera_write(c->rom->done,0);bda_9688_camera_board_restore(c);bda_9688_camera_unlock(saved);
        return BDA_9688_E_NATIVE; /* Native init already releases its partial allocation. */
    }
    c->device=bda_9688_camera_read(c->rom->device);
    if(!bda_9688_camera_ram(c->device,32u)) {c->state=BDA_9688_CAMERA_FAULT;return BDA_9688_E_NATIVE;}
    c->buffer=bda_9688_camera_read(c->device);
    if(!bda_9688_camera_device_valid(c) ||
       bda_9688_camera_read(c->rom->irq_slot)!=c->rom->irq_handler ||
       bda_9688_camera_read(c->rom->irq_slot+4u)) {
        c->state=BDA_9688_CAMERA_FAULT;return BDA_9688_E_NATIVE;
    }
    bda_9688_camera_write(c->rom->opened,1u);c->state=BDA_9688_CAMERA_OPEN;
    if(!((int (*)(void))c->rom->sensor_probe)()) {
        (void)bda_9688_camera_close(c);return BDA_9688_E_IO;
    }
    ((void (*)(const u32 *))c->rom->sensor_init)(descriptor);
    bda_9688_camera_write(c->rom->done,0);
    return BDA_9688_OK;
}
static inline int bda_9688_camera_start(bda_9688_camera_t *c) {
    int result=bda_9688_camera_valid(c);if(result)return result;
    if(c->state!=BDA_9688_CAMERA_OPEN && c->state!=BDA_9688_CAMERA_FRAME)return BDA_9688_E_STATE;
    if(!bda_9688_camera_owned(c))return BDA_9688_E_BUSY;
    ((void (*)(void))c->rom->clear_ready)();
    u32 buffer=((u32 (*)(void))c->rom->start)();
    if(buffer!=c->buffer){c->state=BDA_9688_CAMERA_FAULT;return BDA_9688_E_NATIVE;}
    c->state=BDA_9688_CAMERA_CAPTURING;return BDA_9688_OK;
}
static inline int bda_9688_camera_poll(bda_9688_camera_t *c,bda_9688_camera_frame_t *frame) {
    if(!frame)return BDA_9688_E_ARGUMENT;
    bda_9688_camera_zero((volatile u32 *)frame,sizeof(*frame)/sizeof(u32));
    int result=bda_9688_camera_valid(c);if(result)return result;
    if(c->state!=BDA_9688_CAMERA_CAPTURING && c->state!=BDA_9688_CAMERA_FRAME)return BDA_9688_E_STATE;
    if(!bda_9688_camera_owned(c))return BDA_9688_E_BUSY;
    if(!((u32 (*)(void))c->rom->ready)() || (bda_9688_camera_read(0xb3060004u)&5u))
        return BDA_9688_E_BUSY;
    __asm__ volatile("sync" ::: "memory");
    frame->pixels=(const u8 *)((c->buffer&0x1fffffffu)|0xa0000000u);
    frame->width=320;frame->height=240;frame->stride=640;frame->bytes=BDA_9688_CAMERA_BYTES;
    frame->format=BDA_9688_CAMERA_YUYV;c->state=BDA_9688_CAMERA_FRAME;return BDA_9688_OK;
}
static inline u32 bda_9688_camera_component(s32 value) {
    value >>= 10;return value<0?0u:value>255?255u:(u32)value;
}
/* Full-range YUYV conversion derived from native 80223704/80223868 paths.
 * Size/overflow checked; destination must be separate from the source.
 */
static inline int bda_9688_camera_yuyv_to_rgb565(const u8 *source,u32 source_bytes,
        u16 *destination,u32 destination_pixels,u32 width,u32 height) {
    if(!source || !destination || !width || !height || (width&1u))return BDA_9688_E_ARGUMENT;
    if(width>0x7fffffffu/height)return BDA_9688_E_RANGE;
    u32 pixels=width*height;
    if(pixels>0x7fffffffu || source_bytes<pixels*2u || destination_pixels<pixels)return BDA_9688_E_RANGE;
    u32 a=(u32)source,b=(u32)destination,bytes=pixels*2u;
    if((b&1u) || a>0xffffffffu-bytes || b>0xffffffffu-bytes || (a<b+bytes && b<a+bytes))return BDA_9688_E_ARGUMENT;
    for(u32 i=0;i<pixels;i+=2u) {
        s32 u=(s32)source[2*i+1]-128,v=(s32)source[2*i+3]-128;
        for(unsigned k=0;k<2;k++) {
            s32 y=(s32)source[2*i+2*k]*1024;
            u32 r=bda_9688_camera_component(y+1435*v);
            u32 g=bda_9688_camera_component(y-352*u-731*v);
            u32 blue=bda_9688_camera_component(y+1815*u+128);
            destination[i+k]=(u16)(((r>>3)<<11)|((g>>2)<<5)|(blue>>3));
        }
    }
    return BDA_9688_OK;
}
#endif
