/* SPDX-License-Identifier: Apache-2.0 OR GPL-2.0-only */
#ifndef BDA_9688_RECORDING_H
#define BDA_9688_RECORDING_H

#include "bda_9688_platform.h"

/* Exact 9688 V2.32 firmware-owned recording. The SYS media manager owns
 * DMA, PCM buffers, encoding, and file creation. This is not a PCM read API.
 * Keep this translation unit and the recorder alive through finish(). Use
 * one recorder at a time and serialize calls in the foreground event loop.
 * Poll between GUI events; the SDK does not sleep or run an RTOS scheduler.
 */
enum bda_9688_recording_state {
    BDA_9688_REC_UNINITIALIZED = 0, BDA_9688_REC_READY = 1,
    BDA_9688_REC_OPEN = 2, BDA_9688_REC_QUEUED = 3,
    BDA_9688_REC_CAPTURING = 4, BDA_9688_REC_STOPPING = 5,
    BDA_9688_REC_COMPLETE = 6, BDA_9688_REC_CLOSED = 7
};

typedef struct bda_9688_recording_format {
    u32 sample_rate, channels, format_tag, bits_per_sample, block_align;
    u32 samples_per_block, fmt_chunk_bytes;
} bda_9688_recording_format_t;

typedef struct bda_9688_recording_status {
    u32 state, native_state, elapsed_ms, native_error;
} bda_9688_recording_status_t;

typedef struct bda_9688_recorder {
    u32 magic;
    bda_9688_context_t platform;
    u32 state, handle, descriptor[8], start_word;
    volatile u32 completed, native_error;
    bda_9688_recording_format_t format;
} bda_9688_recorder_t;

/* A nonzero initializer forces the registry into PROGBITS. Minimal BDA
 * launchers do not necessarily clear .bss. Its owner must never be replaced
 * while a native callback can still arrive. Header-local state deliberately
 * requires open/start/stop/poll/finish in the same translation unit.
 */
static struct {
    u32 magic;
    bda_9688_recorder_t *volatile owner;
    volatile u32 handle;
} bda_9688_recording_registry __attribute__((used)) = { 0x52454738u, 0, 0 };

#define BDA_9688_RECORDER_MAGIC 0x52454338u

/* Publish completion in JR's delay slot, with no C epilogue afterwards.
 * A higher-priority GUI task may finish/unload the BDA as soon as it observes
 * completed. The last store and return to ROM must therefore be the same
 * architectural branch completion. This is static BDA text, not generated
 * executable RAM, and requires no additional runtime cache synchronization.
 */
_Static_assert(__builtin_offsetof(bda_9688_recorder_t, handle) == 32, "recording ABI handle");
_Static_assert(__builtin_offsetof(bda_9688_recorder_t, completed) == 72, "recording ABI done");
_Static_assert(__builtin_offsetof(bda_9688_recorder_t, native_error) == 76, "recording ABI error");
extern void bda_9688_recording_completed(u32 handle, u32 error);
__asm__(
    ".pushsection .text.bda_9688_recording_completed,\"ax\",@progbits\n"
    ".set push\n.set noreorder\n"
    ".local bda_9688_recording_completed\n"
    ".type bda_9688_recording_completed,@function\n"
    "bda_9688_recording_completed:\n"
    "lui $t0,%hi(bda_9688_recording_registry)\n"
    "addiu $t0,$t0,%lo(bda_9688_recording_registry)\n"
    "lw $t1,0($t0)\nlui $t2,0x5245\nori $t2,$t2,0x4738\n"
    "bne $t1,$t2,1f\nnop\n"
    "lw $t1,8($t0)\nbne $a0,$t1,1f\nnop\n"
    "lw $t0,4($t0)\nbeq $t0,$zero,1f\nnop\n"
    "lw $t1,0($t0)\nlui $t2,0x5245\nori $t2,$t2,0x4338\n"
    "bne $t1,$t2,1f\nnop\n"
    "lw $t1,32($t0)\nbne $a0,$t1,1f\nnop\n"
    "sw $a1,76($t0)\naddiu $t1,$zero,1\n"
    "jr $ra\nsw $t1,72($t0)\n"
    "1: jr $ra\nnop\n"
    ".size bda_9688_recording_completed,.-bda_9688_recording_completed\n"
    ".set pop\n.popsection\n");

static inline int bda_9688_recording_owned(const bda_9688_recorder_t *recorder) {
    return recorder && recorder->magic == BDA_9688_RECORDER_MAGIC &&
        bda_9688_recording_registry.owner == recorder && recorder->handle &&
        bda_9688_recording_registry.handle == recorder->handle;
}

static inline int bda_9688_recording_guards(const bda_9688_context_t *platform) {
    static const bda_9688_guard_t jz4730[] = {
        {0x8025d2a0u, 0x38u, 0x5e38db00u},
        {0x80191fe0u, 0x2ebcu, 0x91eafb38u},
        {0x80196530u, 0x684u, 0x488d0cd0u},
        {0x8019ac38u, 0x19cu, 0x825fbaf6u}
    };
    static const bda_9688_guard_t jz4740[] = {
        {0x8029bea0u, 0x38u, 0x98a08abau},
        {0x8018e120u, 0x33e0u, 0x63b8744cu},
        {0x80192be0u, 0x61cu, 0x9bffc83eu}
    };
    if (!platform || !platform->profile) return BDA_9688_E_ARGUMENT;
    if (platform->profile->chip == BDA_9688_CHIP_JZ4730)
        return bda_9688_check_guards(platform, jz4730, 4);
    if (platform->profile->chip == BDA_9688_CHIP_JZ4740)
        return bda_9688_check_guards(platform, jz4740, 3);
    return BDA_9688_E_UNSUPPORTED;
}

/* Initialize explicit caller storage; no zeroed BSS or preinitialized context
 * is required. Platform detection and ROM guards perform read-only checks.
 */
static inline int bda_9688_recorder_init(bda_9688_recorder_t *recorder,
                                      const bda_9688_context_t *platform) {
    if (!recorder || !platform) return BDA_9688_E_ARGUMENT;
    if (bda_9688_recording_registry.owner == recorder) return BDA_9688_E_BUSY;
    int result = bda_9688_recording_guards(platform);
    if (result) return result;
    volatile u32 *words = (volatile u32 *)recorder;
    for (unsigned i = 0; i < sizeof(*recorder) / sizeof(u32); ++i) words[i] = 0;
    recorder->magic = BDA_9688_RECORDER_MAGIC;
    recorder->platform.profile = platform->profile;
    for (unsigned i = 0; i < 5; ++i)
        ((volatile u32 *)recorder->platform.runtime_tables)[i] = platform->runtime_tables[i];
    recorder->state = BDA_9688_REC_READY;
    recorder->format.sample_rate = 16000;
    recorder->format.channels = 1;
    recorder->format.block_align = 256;
    if (platform->profile->chip == BDA_9688_CHIP_JZ4730) {
        recorder->format.format_tag = 0x11;
        recorder->format.bits_per_sample = 4;
        recorder->format.samples_per_block = 505;
        recorder->format.fmt_chunk_bytes = 20;
    } else {
        recorder->format.format_tag = 1;
        recorder->format.bits_per_sample = 16;
        recorder->format.fmt_chunk_bytes = 32;
    }
    return BDA_9688_OK;
}

/* The path is consumed synchronously by native fopen("wb"). Its directory
 * must already exist. Existing files are replaced, as in the stock recorder.
 * The returned file is the native WAV variant, including its header quirks.
 */
static inline int bda_9688_recorder_open(bda_9688_recorder_t *recorder, const char *path) {
    if (!recorder || !path || !*path) return BDA_9688_E_ARGUMENT;
    if (recorder->magic != BDA_9688_RECORDER_MAGIC ||
        (recorder->state != BDA_9688_REC_READY && recorder->state != BDA_9688_REC_CLOSED))
        return BDA_9688_E_STATE;
    if (bda_9688_recording_registry.owner) return BDA_9688_E_BUSY;
    u32 info[8];
    for (unsigned i = 0; i < 8; ++i) ((volatile u32 *)info)[i] = 0;
    void *table = (void *)recorder->platform.runtime_tables[2];
    if (bda_sdk_internal_call2(table, 0x2cu, 0, (u32)info) != 1) return BDA_9688_E_NATIVE;
    if (info[0]) return BDA_9688_E_BUSY; /* Own the media manager exclusively. */
    for (unsigned i = 0; i < 8; ++i) ((volatile u32 *)recorder->descriptor)[i] = 0;
    recorder->descriptor[0] = 5;
    recorder->descriptor[1] = 2;
    recorder->descriptor[2] = (u32)path;
    recorder->descriptor[3] = 16000;
    recorder->descriptor[4] = (u32)bda_9688_recording_completed;
    /* descriptor[5] is a second callback/reserved field, not userdata. */
    recorder->completed = 0;
    recorder->native_error = 0;
    recorder->start_word = 0;
    int handle = bda_sdk_internal_call1(table, 0, (u32)recorder->descriptor);
    if (handle < 1 || handle > 10) return BDA_9688_E_NATIVE;
    recorder->handle = (u32)handle;
    bda_9688_recording_registry.handle = (u32)handle;
    bda_9688_recording_registry.owner = recorder;
    recorder->state = BDA_9688_REC_OPEN;
    return BDA_9688_OK;
}

static inline int bda_9688_recorder_start(bda_9688_recorder_t *recorder) {
    if (!bda_9688_recording_owned(recorder)) return BDA_9688_E_STATE;
    if (recorder->state != BDA_9688_REC_OPEN) return BDA_9688_E_STATE;
    recorder->state = BDA_9688_REC_QUEUED;
    int result = bda_sdk_internal_call2((void *)recorder->platform.runtime_tables[2], 0x14u,
                           recorder->handle, (u32)&recorder->start_word);
    if (result == 1) return BDA_9688_OK;
    if (!recorder->completed) recorder->state = BDA_9688_REC_OPEN;
    return BDA_9688_E_NATIVE;
}

static inline int bda_9688_recorder_poll(bda_9688_recorder_t *recorder,
                                      bda_9688_recording_status_t *status) {
    if (!status) return BDA_9688_E_ARGUMENT;
    if (!bda_9688_recording_owned(recorder)) return BDA_9688_E_STATE;
    u32 info[8];
    for (unsigned i = 0; i < 8; ++i) ((volatile u32 *)info)[i] = 0;
    if (recorder->completed) recorder->state = BDA_9688_REC_COMPLETE;
    int result = bda_sdk_internal_call2((void *)recorder->platform.runtime_tables[2], 0x2cu,
                           recorder->handle, (u32)info);
    if (result != 1 || !info[0]) return BDA_9688_E_NATIVE;
    /* Completion can arrive during the native query. */
    if (recorder->completed) recorder->state = BDA_9688_REC_COMPLETE;
    else if (recorder->state == BDA_9688_REC_QUEUED && info[1] == 2)
        recorder->state = BDA_9688_REC_CAPTURING;
    status->state = recorder->state;
    status->native_state = info[1];
    status->elapsed_ms = info[3];
    status->native_error = recorder->native_error;
    return BDA_9688_OK;
}

/* A queued start must first become capturing. Stopping state 0 would cancel
 * the queued job without a completion callback; return BUSY for a later retry.
 * Native return 1 acknowledges a request; only completion permits finish().
 */
static inline int bda_9688_recorder_stop(bda_9688_recorder_t *recorder) {
    if (!bda_9688_recording_owned(recorder)) return BDA_9688_E_STATE;
    if (recorder->completed || recorder->state == BDA_9688_REC_STOPPING)
        return BDA_9688_OK;
    if (recorder->state != BDA_9688_REC_QUEUED && recorder->state != BDA_9688_REC_CAPTURING)
        return BDA_9688_E_STATE;
    bda_9688_recording_status_t status;
    int result = bda_9688_recorder_poll(recorder, &status);
    if (result || recorder->completed) return result;
    if (status.native_state != 2) return BDA_9688_E_BUSY;
    recorder->state = BDA_9688_REC_STOPPING;
    result = bda_sdk_internal_call1((void *)recorder->platform.runtime_tables[2], 0x20u, recorder->handle);
    if (result == 1) return BDA_9688_OK;
    if (!recorder->completed) recorder->state = BDA_9688_REC_CAPTURING;
    return BDA_9688_E_NATIVE;
}

/* An opened, never-started file can be closed immediately. After start, keep
 * polling until completion. close synchronously writes the final WAV header,
 * flushes native buffers, closes FILE*, and frees the backend. The firmware
 * does not reliably propagate fwrite/fclose failures, so OK is not durability
 * proof. On any close return, forget the consumed native handle; never retry
 * close against a handle which another application could already have reused.
 */
static inline int bda_9688_recorder_finish(bda_9688_recorder_t *recorder) {
    if (!bda_9688_recording_owned(recorder)) return BDA_9688_E_STATE;
    if (!recorder->completed && recorder->state != BDA_9688_REC_OPEN)
        return BDA_9688_E_BUSY;
    int result = bda_sdk_internal_call1((void *)recorder->platform.runtime_tables[2], 4u, recorder->handle);
    bda_9688_recording_registry.owner = 0;
    bda_9688_recording_registry.handle = 0;
    recorder->handle = 0;
    recorder->state = BDA_9688_REC_CLOSED;
    return result == 1 ? BDA_9688_OK : BDA_9688_E_NATIVE;
}

#endif
