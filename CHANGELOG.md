# Changelog

All notable SDK and packer changes are recorded here. The project follows
[Semantic Versioning](https://semver.org/) once a public release is tagged.

## Unreleased

- Prepare the repository for an initial open-source SDK release.
- Add installable `bda-pack`, `bda-validate`, and `bda-icon` commands.
- Package verified public headers with the Python wheel.
- Add CI, compatibility documentation, and a focused developer quick start.
- Dual-license original project material under Apache-2.0 OR GPL-2.0-only and document
  third-party data boundaries in `NOTICE` and `DATA_NOTICE.md`.
- Split the public SDK into focused memory, filesystem, input, time, window,
  graphics, dialogs, controls, and audio headers while retaining `bda_sdk.h`
  as the complete umbrella include.
- Keep repository automation in `scripts/` and downloaded compiler state in
  the ignored `.toolchain/` directory.
- Document the complete firmware menu mapping for `bda-pack --category`.
- Document each category's firmware menu capacity and distinguish the
  dynamically verified category 4 boundary from other static limits.
- Publish the true-hardware-verified nominal 1 ms timer lifecycle API, while
  documenting its observed 194-200 count range over nominal 200 ms windows.
- Correct the C200knl context-copy color-key contract: argument `0` skips
  RGB565 black rather than disabling transparency. Replace the misleading
  `BDA_GUI_COLOR_KEY_NONE` name with an explicit black key and provide an
  opaque-near-black replacement constant/helper.
- Add the guarded C200 240x320 RGB565 direct-framebuffer API, including
  GUI-provided dynamic addressing, orientation compensation, uncached
  full-frame copies, firmware fallback requirements, an independently
  verified example, and emulator/true-device evidence.
- Publish the true-hardware-verified read-only BBK 9588/9688 and
  JZ4720/JZ4730/JZ4740 identification API, example BDA, and verification
  boundaries.
- Move the exact 9588/9688 JZ4720/JZ4730/JZ4740 capture profiles into the
  public audio API, including cached hardware/signature gating, profile
  maturity reporting, format-aware initialization, and nonblocking
  `bda_audio_capture_ready()` polling.
- Publish the no-argument global filesystem flush API after an 8013 forced
  power-cut A/B test preserved the flushed 4096-byte file while the unflushed
  control remained 0 bytes.
- Publish file removal, rename, empty-directory removal, current-directory,
  path metadata, disk-capacity, and storage-ready APIs after an 8013 CRUD and
  cleanup verification loop.

## 0.1.0-alpha.1

- Build standalone MIPS little-endian BDA applications from freestanding C.
- Validate BDA headers, entry points, checksums, and VX icon regions.
- Publish dynamically verified filesystem, GUI, input, controls, dialogs,
  graphics, and raw PCM APIs.
- Include source and prebuilt binaries for verified examples.
