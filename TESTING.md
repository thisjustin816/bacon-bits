# Cartridge verification

Build both mapper variants, then run the complete suite:

```sh
make releases
python tests/run.py --core /path/to/sameboy_libretro.so
```

Export `GBDK_HOME` for the subprocess builds. Use the Python environment with
PyBoy 2.8.1, Pillow and NumPy installed. `--jobs` sets concurrency. Each suite
has a timeout and a separate `build/verify-*.log`; `build/verification.json`
records exit statuses and the SHA-256 of both ROMs. Both mapper builds receive
the header, bank, symbol, tile-budget and CRC checks.

## What the checks establish

| Diagnostic | Automated evidence | Remaining hardware check |
| --- | --- | --- |
| Platform | Probe observations, evidence pages, register signatures, summary restoration, upstream classifier suite | Classification on a real console; signatures identify observed behavior, not emulator authenticity |
| Link cable | Original features and paired stress suites on standalone and banked ROMs; an interrupt during a graphics-bank switch must queue its byte | Two consoles and a cable for wire timing, disconnects and sustained operation |
| Rumble | Compiled assembly timing, output transitions in SameBoy, retained settings and output cleanup | Motor response, strength and cartridge compatibility |
| Audio | Compiled APU calls and ordinary UI inputs; frequencies, clocks, waveform bytes, levels, stereo samples, mute, bursts and input responsiveness | Speaker/headphone response and audible artifacts |
| Buttons | Counts, short presses, hold durations, diagonals, opposing inputs, confirmations, live D-pad graphics and retained counters | Contacts, physical bounce and combinations the emulator filters |
| Display | All seven default patterns checked as pixels, including checker parity, stripe spacing, scroll columns and ramp bands; preparation preserves font tiles on every sampled frame | Panel faults, response time, color accuracy and motion appearance |
| SRAM | All patterns, confirmation defaults, bank limits, power cycling, injected data errors, copied bank tags and damaged records | Cartridge retention, banking and electrical reliability |
| Burn in | Complete ROM checksums, an altered ROM, retained first-error details, duration, CPU switching and cleanup; scratch and SRAM paths run in the cartridge | Sustained hardware stability under load |
| Clock (MBC3) | Live tick, held latch, halt, rollover, confirmation, journal recovery and restoration in PyBoy; halt/restore in SameBoy | Battery-backed accuracy and long-term retention |
| Cartridge LED (MBC5) | Actual compiled 24-bit command order, idle output, primary-color commands and OFF cleanup | Compatible cartridge protocol and visible light output |
| Infrared | Compiled edge-cycle counts, burst count, presets, receiver controls and cleanup | Optical transmission/reception between real devices |
| Flicker | Every-frame phase cadence, duty, movement, pause/step, reference stability, OAM DMA and cleanup in both emulators | Panel blending and perceived flicker |

`smoke`, `variants` and `graphical_ui` cover entry routes and safe initial
states. Their broad checks supplement the diagnostic-specific suites.
`modal_regression`, `sameboy` and `rumble_return` cover dialog restoration,
consumed input and shared-memory cleanup. `lettering`, `menu_alignment`,
`menu_art`, `ui_spacing` and `ui_transitions` cover glyphs, layout, animation,
focus changes and counter formatting.

`raster_transitions` compares the displayed header on every frame during
navigation, diagnostic entry, settings-page changes and return, in CGB/DMG
and both mapper variants. It retains inputs, ROM identities and review frames.
`display_font` checks resident glyph bytes on every sampled preparation frame
and the restored header map after each full-screen pattern.
These checks detect a temporarily erased heading and display patterns replacing
live letters; settled screenshots alone miss those failures.

The display assertions compare actual framebuffer pixels with independent
geometric expectations. A color-count check alone cannot distinguish a
checkerboard from stripes. Audio navigation is bounded and reports a missed
input instead of waiting indefinitely.

## Harnesses and evidence

`upstream` rebuilds and runs every vendored standalone suite. `link_combined`
uses a separate autorun build and synthetic paired byte transport.
`rumble_combined` runs the compiled motor/delay/input bytes in the timing
interpreter, substituting its supported standalone renderer at draw calls.
Neither proves physical serial timing or motor performance.

`audio_backend` redirects startup to a call stub; `audio_ui`, `audio_shapes`
and `audio_sameboy` additionally exercise ordinary cartridge inputs. Frequency
measurements find the strongest spectral peak above 10 Hz before comparing it
with the requested frequency; they do not restrict the search to that frequency.
`libretro`, `audio_navigation` and `display_assertions` are helpers, not
standalone test suites. `capture_review` and `capture_flicker` generate review
media and do not establish a pass by themselves.

When adding a regression, retain the prior ROM and matching symbols. Reproduce
the failure there first, then run the same inputs against the fixed build.
Fault cases should reject corrupted output as well as accept the normal result.
The suite does not substitute emulator output for physical-device evidence.
