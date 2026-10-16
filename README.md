# Bacon Bits

A Game Boy diagnostic cartridge with a sunrise browser and four tests:

- **Platform Detect:** hardware class, twelve emulator tells, and known
  emulator signatures from Platform Detect v1.4.
- **Link Sustain:** sustained packets, shared simulation, scene barriers,
  uneven CPU load, and retained errors from Link Sustain v1.2.
- **Rumble Pulse:** editable patterns, presets, frame and millisecond timing,
  start/stop sweeps, and prespin.
- **Audio Range:** manually stepped frequencies, levels, and stereo routing
  on both pulse channels, sine/square waves, and 15-bit/7-bit noise.

![Bacon Bits browser and audio screens](assets/review.png)

The icons and sunrise are original pixel drawings. The colors are blue sky,
yellow sun, cream, toast brown, and bacon red. Color reinforces shape and text;
the browser also works in monochrome.

## Controls

Browse tests with Left/Right and open one with A. Returning keeps the selected
test. Hold A+B+Start+Select together to open the return menu on Platform Detect,
in Link Sustain's settings or stopped results, or while Rumble Pulse is idle.
CONTINUE is selected first. Choose TEST MENU to return to the browser.

The original diagnostics retain their controls. Link Sustain stops with B and
returns to its settings with Start. It restores normal CPU speed on exit.
Fast link clock and double CPU speed require color hardware.
Rumble Pulse uses Start to play/stop, B to change mode, and Select combinations
for settings. Its motor is switched off before returning to the browser.

## Audio Range

Up/Down chooses VOICE, HZ/CLOCK, LEVEL, or OUTPUT. Left/Right changes the value;
holding a direction repeats. A starts or stops the tone, and B stops it and
returns to the browser. Playback starts silent. OUTPUT selects BOTH, LEFT,
or RIGHT.

Pulse frequencies span 64-131,072 Hz. Wave frequencies span 32-65,536 Hz,
with sine and square waveforms. Each has 34 steps, with more steps at the low
end. Pulse and noise have all 16 levels, including mute. Wave has mute,
quarter, half, and full level. Pulse duty is 50 percent; the hardware sweep
and volume envelopes are disabled.

Noise offers all 60 distinct running LFSR clocks, from 4.57 to 524,288 Hz,
in both 15-bit and 7-bit modes. CLOCK is the generator's shift rate. At the
lowest clock, the first change can take several seconds. Frequency values
come from the actual hardware divisors. Steps above hearing range are useful
for register comparisons; speaker response requires listening on hardware.

## Build

Requires GBDK-2020 4.5.0, Python 3, and Pillow:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install Pillow pyboy==2.8.1 numpy
make GBDK_HOME=/path/to/gbdk/ PYTHON=python
```

The build image is `build/bacon-bits.gbc`. `make release` also updates
`Bacon Bits (World).gbc`, the checked-in diagnostic. The cartridge is 128 KiB,
MBC5+RUMBLE, with no cartridge RAM or battery. Flash hardware needs a
compatible mapper and a motor for rumble.
The original diagnostic ROM is distributed with its source. Reference game
ROMs, saves, Python environments, and test artifacts are excluded from Git.

`vendor/README.md` records the source revisions. The build generates adapters
for banking and return hooks while keeping the upstream source copies intact.
The assembly diagnostic has a checked bank entry and a return address resolved
from the final link symbols. The browser uses 194 of 256 background tile slots,
two background palettes, and no sprites. Two icon buffers keep the old picture
visible while the next one loads. Each diagnostic replaces the browser tiles
when it opens.

## Verification

```sh
python tests/upstream.py
python tests/smoke.py
python tools/check_build.py
python tests/modal_regression.py
python tests/link_combined.py
python tests/rumble_combined.py
python tests/audio_ui.py
python tests/audio_backend.py
python tests/sameboy.py --core /path/to/sameboy_libretro.so
python tests/audio_sameboy.py --core /path/to/sameboy_libretro.so
```

The standalone suites rebuild all three imported diagnostics. Link Sustain's
original native and paired suites also run against the banked combined ROM.
The original rumble timing suite also runs on the combined ROM's assembly bank
through the timing interpreter's flat memory view.
The paired harness uses a synthetic byte transport; it does not establish
physical serial timing or cable behavior. Its instruction hook is relocated
from the current symbol file.

The browser and audio controls run on the unmodified compiled ROM in PyBoy
in color and monochrome modes. The audio backend harness redirects startup
to a WRAM call stub, then captures the compiled APU routines. It measures
64 Hz pulse and 32 Hz wave fundamentals and silence at level zero.

SameBoy checks color output, transitions, borrowed tile restoration, attributes,
and motor-control output. Its audio suite reads every frequency,
noise clock, and level setting at the APU registers and captures left/right
output separately. Emulator output does not establish speaker response,
physical motor strength, cartridge timing, or hardware reliability.

SameBoy 26a56bd can be built with `make libretro` in its source checkout.
It needs RGBDS and a `hexdump` utility. The shared core is written to
`build/bin/sameboy_libretro.so`. Test evidence is written under this repo's
`build/` directory.
