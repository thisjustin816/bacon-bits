# Bacon Bits Test Cartridge

A Game Boy and Game Boy Color diagnostic cartridge with animated instruments,
breakfast colors, and detailed results behind each test. The artwork and font
are original. The interface also works in monochrome.

![Cartridge screens](assets/review.png)

[Menu and live button views](assets/controls.png) | [Flicker phases](assets/flicker.png)

| Release | Cartridge hardware | Test in the third slot |
| --- | --- | --- |
| [MBC5 Rumble](<Bacon Bits Test Cartridge (MBC5 Rumble).gbc>) | MBC5, rumble, up to 64 KiB RAM | Rumble |
| [MBC3 RTC](<Bacon Bits Test Cartridge (MBC3 RTC).gbc>) | MBC3, timer, 32 KiB RAM | Real Time Clock |

Both releases contain Platform, Link Cable, Audio Range, Buttons, Display,
SRAM, Burn In, Infrared, and Flicker. The MBC5 release also drives the
insideGadgets RGB LED cartridge. Its LED page is disabled in the MBC3 release because the
same writes control the RTC latch on that mapper.

Left/Right browses tests, Up/Down moves between card rows, and A opens one.
The selected card has a thicker border and a gold fill on color hardware.
Settings use Up/Down to select a field and Left/Right to change it. Presets
open with outputs stopped; later visits select Continue. Destructive actions
start on No. [The manual](MANUAL.md) covers controls, presets, and limits.

The tests retain readings for comparison: the bytes behind an emulator
signature, separate D-pad corner holds, all audio divisors and wave shapes,
first memory failures, and a saved SRAM configuration. Link Cable checks
sustained traffic and shared state under different loads. Burn In combines
repeatable loads while keeping the first failure. Flicker compares alternating
layers, shadows, detail, and color fields with a static dither reference. Its
phase lengths, duty, motion clock, and single-frame step are adjustable.

## Build

Requires GBDK-2020 4.5.0 and Python 3:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install Pillow pyboy==2.8.1 numpy
make releases GBDK_HOME=/path/to/gbdk/ PYTHON=python
```

`make` builds MBC5 into `build/`. `make mbc3` builds MBC3 into `build/mbc3/`.
`make releases` checks both builds and updates the two release ROMs.
Both are 128 KiB. Generated adapters, object caches, and CRC tables are
separate for each build. [SHA256SUMS](SHA256SUMS) identifies the release files.
These original diagnostic ROMs are distributed with their source. Reference
cartridges, saves, virtual environments, and test artifacts are excluded.

## Publishing releases

Push a `vX.Y.Z` tag to run [Publish release](.github/workflows/release.yml).
The workflow builds both variants with GBDK 4.5.0, checks their headers and
bank layout, and runs the routing, mapper, and display-font regressions.
It publishes versioned ROMs and `SHA256SUMS` as GitHub release assets.
Asset names use dots between words so GitHub keeps the checksum filenames.
The workflow downloads the published assets and checks their hashes again.
Run the full verification suite and hardware checks before tagging a release.

The workflow can also run from the Actions page with an existing tag, such as
`v1.0.0`, to attach assets to that release. It builds the tagged source and
keeps existing release notes. Re-running replaces assets with the same names.
GitHub's built-in token supplies release access; no repository secret is needed.

## Verification

```sh
GBDK_HOME=/path/to/gbdk/ python tests/run.py --core /path/to/sameboy_libretro.so
```

The runner rebuilds the three vendored diagnostics and runs their full suites.
It also runs the combined Link Cable feature and paired suites, the original
rumble timing suite against the combined bank, and the cartridge's PyBoy and
SameBoy checks. Logs and ROM hashes are saved under `build/`.

PyBoy checks color and monochrome routes, presets, probe evidence, D-pad
counters, audio settings and captures, display patterns, SRAM faults and saved
files, burn-in, RGB command bits, and RTC restoration and recovery.
A serial interrupt injected while the UI maps another bank checks the fixed
interrupt handler. The infrared check executes the compiled burst instructions
to measure their cycle spacing.

SameBoy checks palettes, maps and attributes, dialogs, wave RAM, stereo audio
captures, rumble-control output, IR control, RTC halt and restore, and CPU-speed
cleanup. Frame-by-frame replays check launcher labels during focus and page
changes, all menu animation poses, and return from Buttons. PyBoy checks all
16 direction combinations; SameBoy checks the nine ordinary states because
it filters opposing directions before they reach the cartridge. Both emulators
measure Flicker phase lengths, stationary reference patches, motion, pause,
and single-frame steps on both mapper builds and display modes. Raw frames
cannot establish physical screen persistence or frontend blending. Paired link
tests use synthetic byte transport. These checks do not
establish physical cable timing, speaker response, motor strength, infrared
range, LED brightness, battery retention, or RTC oscillator accuracy.

SameBoy 26a56bd builds with `make libretro`, RGBDS, and `hexdump`.
`vendor/README.md` records the imported source revisions. The vendored files
remain unchanged. Build checks enforce ROM-bank bounds, a fixed serial
interrupt handler, current assembly bridges, and the per-bank CRC manifest.
The busiest browser page uses 253 resident background tiles and no sprites.
The shared font has 96 glyphs; instruments start at tile 112 and the brand uses
240-255. The focus border uses 232-239 and four unused punctuation slots;
the live D-pad uses 37 instrument patterns. Odd-length labels use other
punctuation slots for a half-tile shift. Focus moves leave those label patterns
in place. Screen changes clear outgoing map references before restoring the
font. Button feedback includes a separate shape. The return dialog uses the
shared font and frames.

The [verification coverage guide](TESTING.md) maps each diagnostic to its
automated checks and remaining hardware checks. The runner checks header
continuity during transitions, preserves UI glyphs while display patterns load,
and checks the restored header after full-screen tests.
