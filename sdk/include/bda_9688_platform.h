/* SPDX-License-Identifier: Apache-2.0 OR GPL-2.0-only */
#ifndef BDA_9688_PLATFORM_H
#define BDA_9688_PLATFORM_H

#include "bda_types.h"
#include "bda/detail/runtime.h"
#include "bda_hardware.h"

/* These bindings identify the exact V2.32 recovery ROMs examined here.
 * They do not imply that a sensor, microphone or analog path has been tested.
 * No private ROM function is called by capability detection.
 */
/* Exact 9688 media bindings; maturity applies to this camera/WAV mechanism,
 * not bda_audio.h's separate realtime raw-PCM capture implementation. */
#define BDA_9688_SUPPORT_NONE              0u
#define BDA_9688_SUPPORT_STATIC_CANDIDATE  1u
#define BDA_9688_SUPPORT_HARDWARE_VERIFIED 2u
#define BDA_9688_INTERNAL_RUNTIME_BASE 0x81c00000u

enum bda_9688_error {
    BDA_9688_OK = 0,
    BDA_9688_E_UNSUPPORTED = -1,
    BDA_9688_E_ARGUMENT = -2,
    BDA_9688_E_BUSY = -3,
    BDA_9688_E_NATIVE = -4,
    BDA_9688_E_STATE = -5,
    BDA_9688_E_IO = -6,
    BDA_9688_E_RANGE = -7
};

enum bda_9688_chip {
    BDA_9688_CHIP_NONE = 0,
    BDA_9688_CHIP_JZ4730 = 4730,
    BDA_9688_CHIP_JZ4740 = 4740
};

typedef struct bda_9688_profile {
    enum bda_9688_chip chip;
    u32 rom_base, rom_end;
    u32 seed_address, seed_crc32;
    u32 runtime_tables[5];
    u32 device_model, support_level;
    const char *name;
    const char *raw_firmware_sha256;
} bda_9688_profile_t;

typedef struct bda_9688_context {
    const bda_9688_profile_t *profile;
    u32 runtime_tables[5];
} bda_9688_context_t;

typedef struct bda_9688_guard {
    u32 address, length, crc32;
} bda_9688_guard_t;

/* CRC-32/ISO-HDLC, compatible with Python zlib.crc32. */
static inline u32 bda_9688_crc32(const volatile void *data, u32 length) {
    const volatile u8 *bytes = (const volatile u8 *)data;
    u32 crc = ~0u;
    while (length--) {
        crc ^= *bytes++;
        for (unsigned bit = 0; bit < 8; ++bit)
            crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
    }
    return ~crc;
}

static inline const bda_9688_profile_t *bda_9688_profile_for_chip(enum bda_9688_chip chip) {
    static const bda_9688_profile_t profiles[2] = {
        { BDA_9688_CHIP_JZ4730, 0x80004000u, 0x804a9628u,
          0x8025dcc0u, 0x91bfc490u,
          {0x8025d4a0u, 0x8025d410u, 0x8025d2a0u, 0x8025dcdcu, 0x8025d370u},
          BDA_DEVICE_MODEL_9688, BDA_9688_SUPPORT_STATIC_CANDIDATE,
          "9688 V2.32 JZ4730 media",
          "b18ce485a6ca6a8ea9ef5e3963d5970188ff7a2aeb4a6d4e58fe43625f49e514" },
        { BDA_9688_CHIP_JZ4740, 0x80004000u, 0x804a99b8u,
          0x8029c8c0u, 0xb560da9au,
          {0x8029c0a0u, 0x8029c010u, 0x8029bea0u, 0x8029c8dcu, 0x8029bf70u},
          BDA_DEVICE_MODEL_9688, BDA_9688_SUPPORT_HARDWARE_VERIFIED,
          "9688 V2.32 JZ4740 media",
          "7ec707b69a1f4fa7016856b2eba6900412d02d7daefc8b4d11654c63731abca0" }
    };
    if (chip == BDA_9688_CHIP_JZ4730) return &profiles[0];
    if (chip == BDA_9688_CHIP_JZ4740) return &profiles[1];
    return (const bda_9688_profile_t *)0;
}

/* Clear the context on every attempt. All five imported service tables must
 * match before the known ROM seed is read. A 9588 or unknown firmware returns
 * E_UNSUPPORTED without calling or probing any private device function.
 */
static inline int bda_9688_probe(bda_9688_context_t *context) {
    if (!context) return BDA_9688_E_ARGUMENT;
    context->profile = (const bda_9688_profile_t *)0;
    for (unsigned i = 0; i < 5; ++i) context->runtime_tables[i] = 0;
    u32 tables[5];
    for (unsigned i = 0; i < 5; ++i)
        tables[i] = *(const volatile u32 *)(BDA_9688_INTERNAL_RUNTIME_BASE + 4u + 4u * i);
    for (unsigned candidate = 0; candidate < 2; ++candidate) {
        const bda_9688_profile_t *profile = bda_9688_profile_for_chip(
            candidate ? BDA_9688_CHIP_JZ4740 : BDA_9688_CHIP_JZ4730);
        unsigned matched = 0;
        for (unsigned i = 0; i < 5; ++i)
            matched += tables[i] == profile->runtime_tables[i];
        if (matched != 5) continue;
        /* Public read-only model/chip identification is an independent gate.
         * Exact tables and ROM guards never imply an unidentified device. */
        bda_hardware_info_t hardware;
        bda_detect_hardware(&hardware);
        if (hardware.device_model != profile->device_model ||
            hardware.chip_model != (u32)profile->chip)
            return BDA_9688_E_UNSUPPORTED;
        if (bda_9688_crc32((const volatile void *)profile->seed_address, 32u) != profile->seed_crc32)
            return BDA_9688_E_UNSUPPORTED;
        for (unsigned i = 0; i < 5; ++i) context->runtime_tables[i] = tables[i];
        context->profile = profile;
        return BDA_9688_OK;
    }
    return BDA_9688_E_UNSUPPORTED;
}

/* Return the checked platform binding and its public maturity/hash fields.
 * This read-only query does not open the camera or microphone. */
static inline const bda_9688_profile_t *bda_9688_media_profile(void) {
    bda_9688_context_t context;
    return bda_9688_probe(&context) == BDA_9688_OK
        ? context.profile : (const bda_9688_profile_t *)0;
}

/* Private camera/recording bindings provide their own code guards. The seed
 * guard identifies the ROM; each binding must additionally check its routines
 * before its first call. Empty guard lists are rejected, not treated as proof.
 * Contexts can cross translation units: compare profile values, not the address
 * of a header-local static profile object.
 */
static inline int bda_9688_check_guards(const bda_9688_context_t *context,
                                         const bda_9688_guard_t *guards, u32 count) {
    if (!context || !guards || !count) return BDA_9688_E_ARGUMENT;
    if (!context->profile) return BDA_9688_E_STATE;
    const bda_9688_profile_t *profile = bda_9688_profile_for_chip(context->profile->chip);
    if (!profile) return BDA_9688_E_UNSUPPORTED;
    if (context->profile->rom_base != profile->rom_base || context->profile->rom_end != profile->rom_end ||
        context->profile->seed_address != profile->seed_address || context->profile->seed_crc32 != profile->seed_crc32 ||
        context->profile->device_model != profile->device_model ||
        context->profile->support_level != profile->support_level)
        return BDA_9688_E_STATE;
    for (unsigned i = 0; i < 5; ++i)
        if (context->runtime_tables[i] != profile->runtime_tables[i] ||
            context->profile->runtime_tables[i] != profile->runtime_tables[i]) return BDA_9688_E_STATE;
    for (u32 i = 0; i < count; ++i) {
        const bda_9688_guard_t *guard = &guards[i];
        if (!guard->length || guard->address < profile->rom_base || guard->address >= profile->rom_end ||
            guard->length > profile->rom_end - guard->address) return BDA_9688_E_RANGE;
        if (bda_9688_crc32((const volatile void *)guard->address, guard->length) != guard->crc32)
            return BDA_9688_E_UNSUPPORTED;
    }
    return BDA_9688_OK;
}

#endif
