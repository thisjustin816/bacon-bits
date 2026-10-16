# Bacon Bits Test Cartridge

A Game Boy and Game Boy Color diagnostic cartridge with animated instruments,
breakfast colors, and detailed results behind each test. The artwork and font
are original. The interface also works in monochrome.

![Cartridge screens](assets/review.png)

| Release | Cartridge hardware | Test in the third slot |
| --- | --- | --- |
| [MBC5 Rumble](<Bacon Bits Test Cartridge (MBC5 Rumble).gbc>) | MBC5, rumble, up to 64 KiB RAM | Rumble |
| [MBC3 RTC](<Bacon Bits Test Cartridge (MBC3 RTC).gbc>) | MBC3, timer, 32 KiB RAM | Real Time Clock |

Both releases contain Platform, Link Cable, Audio Range, Buttons, Display,
SRAM, Burn In, and Infrared. The MBC5 release also drives the insideGadgets
RGB LED cartridge. Its LED page is disabled in the MBC3 release because the
same writes control the RTC latch on that mapper.

Left/Right browses tests, Up/Down moves between card rows, and A opens one.
Settings use Up/Down to select a field and Left/Right to change it. Presets
open with outputs stopped; later visits select Continue. Destructive actions
start on No. [The manual](MANUAL.md) covers controls, presets, and limits.

The tests retain readings for comparison: the bytes behind an emulator
signature, separate D-pad corner holds, all audio divisors and wave shapes,
first memory failures, and a saved SRAM configuration. Link Cable checks
sustained traffic and shared state under different loads. Burn In combines
repeatable loads while keeping the first failure.

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
cleanup. Paired link tests use synthetic byte transport. These checks do not
establish physical cable timing, speaker response, motor strength, infrared
range, LED brightness, battery retention, or RTC oscillator accuracy.

SameBoy 26a56bd builds with `make libretro`, RGBDS, and `hexdump`.
`vendor/README.md` records the imported source revisions. The vendored files
remain unchanged. Build checks enforce ROM-bank bounds, a fixed serial
interrupt handler, current assembly bridges, and the per-bank CRC manifest.
The busiest browser page uses 245 resident background tiles and no sprites.
The shared font has 96 glyphs; instruments start at tile 112 and the brand uses
240-255. The launcher borrows unused punctuation patterns to center odd-length
labels by half a tile, then restores them before entering a test. Buttons marks
pressed inputs with a separate shape. The return dialog uses the shared font
and frames.
