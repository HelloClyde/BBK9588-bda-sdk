/* SPDX-License-Identifier: Apache-2.0 OR GPL-2.0-only */
#ifndef BDA_9688_MEDIA_H
#define BDA_9688_MEDIA_H

/* Optional 9688 V2.32 extensions to the 9588 native BDA SDK.
 * Each subsystem binds a checked JZ4730/JZ4740 ROM before accessing devices.
 * JZ4740 capture/conversion and native WAV recording were hardware verified;
 * JZ4730 remains STATIC_CANDIDATE. Query bda_9688_media_profile() for maturity
 * and the exact raw firmware SHA256. See docs/verified/9688_media_api.md.
 * Include this header directly or through the public bda_sdk.h umbrella.
 */
#include "bda_9688_platform.h"
#include "bda_9688_camera.h"
#include "bda_9688_recording.h"

#endif
