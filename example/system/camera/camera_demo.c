/* SPDX-License-Identifier: Apache-2.0 OR GPL-2.0-only */
/* Capture 13 complete frames, convert the last, and close before the dialog.
 * This source is build-checked; the SDK lifecycle was exercised independently
 * through Debug EXEC on 9688 V2.32/JZ4740. It does not display/save a photo.
 */
#include "bda_sdk.h"

#define CAMERA_FRAME_COUNT 13u
#define CAMERA_TOTAL_POLL_BUDGET 200000u

__attribute__((section(".text.bda_main")))
int bda_main(void) {
    bda_9688_context_t platform;
    bda_9688_camera_t camera;
    bda_9688_camera_frame_t frame;
    u16 *rgb = 0;
    u32 remaining = CAMERA_TOTAL_POLL_BUDGET;
    int result = bda_9688_probe(&platform);
    int close_result;

    if (result) return result; /* No unknown GUI or private-device calls. */
    if (platform.profile->support_level != BDA_9688_SUPPORT_HARDWARE_VERIFIED)
        return bda_msgbox("9688 Camera", "Static candidate profile. Camera not opened.");
    bda_9688_camera_zero((volatile u32 *)&camera, sizeof(camera)/sizeof(u32));
    result = bda_9688_camera_init(&camera, &platform);
    if (result) return bda_msgbox("9688 Camera", "Camera ABI unavailable. Camera not opened.");
    rgb = (u16 *)bda_alloc(BDA_9688_CAMERA_BYTES);
    if (!rgb) return bda_msgbox("9688 Camera", "Not enough memory. Camera not opened.");
    result = bda_9688_camera_open_qvga(&camera);
    for (u32 index = 0; !result && index < CAMERA_FRAME_COUNT; ++index) {
        result = bda_9688_camera_start(&camera);
        if (result) break;
        for (;;) {
            if (!remaining) { result = BDA_9688_E_BUSY; break; }
            --remaining;
            result = bda_9688_camera_poll(&camera, &frame);
            if (result != BDA_9688_E_BUSY) break;
            /* Native calibrated busy delay, not an RTOS yield or milliseconds.
             * Camera completion comes from IRQ; recording must not use this.
             * The single shared poll budget bounds all 13 waits together. */
            bda_sys_delay(1000u);
        }
    }
    if (!result)
        result = bda_9688_camera_yuyv_to_rgb565(
            frame.pixels, frame.bytes, rgb, 320u*240u, 320u, 240u
        );
    close_result = bda_9688_camera_close(&camera);
    bda_free(rgb);
    if (close_result)
        return bda_msgbox("9688 Camera", "Camera close incomplete. Restart device before retrying.");
    if (result)
        return bda_msgbox("9688 Camera", "Capture/conversion failed or poll budget expired. Camera closed.");
    return bda_msgbox("9688 Camera", "13 frames captured; final frame converted to RGB565. Camera closed.");
}
