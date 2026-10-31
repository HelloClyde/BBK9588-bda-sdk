/* SPDX-License-Identifier: Apache-2.0 OR GPL-2.0-only */
/* The entry is deliberately read-only: no microphone or output file.
 * Helpers show the complete asynchronous SDK lifecycle for a GUI event loop.
 * Keep this source/context loaded until finish completes; never busy-wait.
 */
#include "bda_sdk.h"

static bda_9688_context_t platform;
static bda_9688_recorder_t recorder;

int recording_demo_begin(const char *new_output_path) {
    int result = bda_9688_probe(&platform);
    if (result) return result;
    result = bda_9688_recorder_init(&recorder, &platform);
    if (result) return result;
    /* Native wb truncates an existing path. The caller supplies a fresh path
     * in an existing directory after obtaining the user's recording action. */
    result = bda_9688_recorder_open(&recorder, new_output_path);
    if (result) return result;
    result = bda_9688_recorder_start(&recorder);
    if (result && (recorder.state == BDA_9688_REC_OPEN || recorder.completed)) {
        int close_result = bda_9688_recorder_finish(&recorder);
        if (close_result) return close_result;
    }
    return result;
}

int recording_demo_request_stop(void) {
    /* BUSY while queued: retry on a later GUI event, not in a spin loop. */
    return bda_9688_recorder_stop(&recorder);
}

int recording_demo_poll_and_finish(bda_9688_recording_status_t *status) {
    int result = bda_9688_recorder_poll(&recorder, status);
    if (result) return result;
    if (status->state != BDA_9688_REC_COMPLETE) return BDA_9688_E_BUSY;
    return bda_9688_recorder_finish(&recorder);
}

__attribute__((section(".text.bda_main")))
int bda_main(void) {
    int result = bda_9688_probe(&platform);
    if (result) return result;
    result = bda_9688_recorder_init(&recorder, &platform);
    if (result) return bda_msgbox("9688 Recording", "Recording ABI unavailable. Read-only check.");
    if (platform.profile->support_level != BDA_9688_SUPPORT_HARDWARE_VERIFIED)
        return bda_msgbox("9688 Recording", "JZ4730 V2.32: static candidate; IMA ADPCM WAV. No recording started.");
    return bda_msgbox("9688 Recording", "JZ4740 V2.32: verified mono 16000 Hz PCM WAV. Read-only check; no recording started.");
}
