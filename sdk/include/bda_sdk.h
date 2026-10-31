#ifndef BDA_SDK_H
#define BDA_SDK_H

/*
 * Public kj409588/C200 SDK and explicitly gated 9688 V2.32 media bindings.
 *
 * Applications may include this umbrella header for every verified module,
 * or include individual bda_*.h headers to keep dependencies explicit.
 * Admission rule: only dynamically verified APIs belong in these modules.
 * Admission evidence and lifecycle notes live in docs/verified/.
 */

#include "bda_types.h"
#include "bda_hardware.h"
#include "bda_memory.h"
#include "bda_filesystem.h"
#include "bda_input.h"
#include "bda_time.h"
#include "bda_window.h"
#include "bda_graphics.h"
#include "bda_dialogs.h"
#include "bda_controls.h"
#include "bda_audio.h"
#include "bda_9688_media.h"

#endif
