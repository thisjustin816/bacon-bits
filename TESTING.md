# Cartridge verification

Build both mapper variants, then run the complete suite:

```sh
make releases
python tests/run.py --core /path/to/sameboy_libretro.so
```

Export `GBDK_HOME` for the subprocess builds. Use the Python environment with
PyBoy 2.8.1, Pillow and NumPy installed. `--jobs` sets concurrency. Each suite
has a timeout and a separate `build/verify-*.log`; `build/verification.json`
records exit statuses, the SHA-256 of both ROMs, and any suites not run.
Without `--core` the SameBoy suites are listed as not run, and the run is not
a full verification. Both mapper builds receive the header, bank, symbol,
tile-budget, CRC and screen-text width checks.

The runner records each suite's pass in `build/verification-progress.json` as it
finishes. A run cut short, as by a restart of the machine, can continue with
`--resume`, which skips the suites that passed under the same ROMs, test and tool
sources, and SameBoy core and runs the rest. Any change to those starts a new
record, and a failed suite always runs again. `build/verification.json` lists the
suites it resumed rather than ran. Without `--resume` every suite runs.

The Verify workflow runs the whole suite on pull requests that change more than
Markdown or `LICENSE`, and from the Actions page, not on pushes to `main`. It
builds both ROMs and the SameBoy core once, then runs the suites in parallel
jobs: the fast ones in four slices (`--shard K/4`) and each slow suite alone.
`--list` prints the suites a run would start. The Verification job merges the
shards' `verification.json` files and fails unless every suite ran once and
passed, all on one pair of ROM hashes. Each shard's logs are kept as an artifact
for 14 days. These are PyBoy and SameBoy results, not hardware.

Verify does not block a merge, so read its result on every pull request that
runs it before merging. A pull request that changes only Markdown files or
`LICENSE` skips it and merges without a run. Any other change, including one
under `assets/`, runs the whole suite.

SameBoy 26a56bd builds with `make libretro`, RGBDS and `hexdump`. Build it
with `make -j1`: the parallel build can race on a helper program.

## What the checks establish

| Diagnostic | Automated evidence | Remaining hardware check |
| --- | --- | --- |
| Platform | Probe observations, evidence pages, register signatures, summary restoration, upstream classifier suite; the mode-3 write probe fails in PyBoy, which lets the writes through, and passes in SameBoy, which drops them | Classification on a real console; signatures identify observed behavior, not emulator authenticity |
| Link cable | Original features and paired stress suites on standalone and banked ROMs; an interrupt during a graphics-bank switch must queue its byte; two benches on a free-running cable at both CPU speeds on each end, with a flipped bit, a dropped edge and a 40-frame unplug | Two consoles and a cable for electrical timing, connectors and sustained operation |
| Rumble | Compiled assembly timing, output transitions in SameBoy, retained settings and output cleanup | Motor response, strength and cartridge compatibility |
| Audio | Compiled APU calls and ordinary UI inputs; frequencies, clocks, waveform bytes, levels, stereo samples, mute, bursts and input responsiveness | Speaker/headphone response and audible artifacts |
| Buttons | Counts, short presses, hold durations, diagonals, opposing inputs, confirmations, live D-pad graphics, retained counters, on-screen hints, the loop's poll rate, and staged or simultaneous return chords on every page | Contacts, physical bounce and combinations the emulator filters |
| Display | All seven default patterns checked as pixels, including checker parity, stripe spacing, scroll columns and ramp bands; preparation preserves font tiles on every sampled frame; flicker phases of 1, 2 and 30 frames measured frame by frame; controls during the full view | Panel faults, response time, color accuracy and motion appearance |
| SRAM | All patterns, confirmation defaults, bank limits, power cycling, injected data errors, copied bank tags and damaged records | Cartridge retention, banking and electrical reliability |
| Burn in | Complete ROM checksums, an altered ROM, retained first-error details, duration, CPU switching and cleanup; scratch and SRAM paths run in the cartridge; motor pulse width and spacing at every load from SameBoy's rumble output; RTC watch and redraw cadence at every load | Sustained hardware stability under load |
| Clock (MBC3) | Live tick, held latch, halt, rollover, confirmation, journal recovery and restoration in PyBoy; halt/restore in SameBoy; displayed change counters | Battery-backed accuracy and long-term retention |
| Cartridge LED (MBC5) | Actual compiled 24-bit command order, idle output, primary-color commands and OFF cleanup | Compatible cartridge protocol and visible light output |
| Infrared | Compiled edge-cycle counts, burst count, presets, receiver controls, mode-switch text and cleanup; two benches in one harness, one sending each transmit preset and the other counting every pulse at three frame offsets | Optical transmission and reception between real devices: receiver response, range and ambient light |
| Flicker | Every-frame phase cadence, duty, movement, pause/step, reference stability, OAM DMA and cleanup in both emulators | Panel blending and perceived flicker |

`smoke`, `variants` and `graphical_ui` cover entry routes and safe initial
states. Their broad checks supplement the diagnostic-specific suites.
`modal_regression`, `sameboy` and `rumble_return` cover dialog restoration,
consumed input and shared-memory cleanup. `modal_regression` also presses
Start a frame ahead of the rest of the chord in Link setup; the dialog must
open and Link must not start. `preset_bounce` picks Flicker's and
Infrared's presets with an A press that reads released for one frame, as a
bouncing button can; neither instrument may start from the held button. `lettering`, `menu_alignment`,
`menu_art`, `ui_spacing` and `ui_transitions` cover glyphs, layout, animation,
focus changes and counter formatting.

`screen_text` walks the settings pages and checks that no label touches its
value, along with the Buttons timing status, the Link timer, Infrared after a mode
switch, the Audio frequency unit and the Clock counters. `tools/check_build.py`
enforces the same eight-column limit on every settings label and value in the
source. `display_timing`, `buttons_chord`, `buttons_poll`, `burn_cadence` and
`burn_rumble` cover flicker phase lengths, the Buttons return chord, hints and
clear confirmation, how often the Buttons loop reads the pad, and Burn In timing.
`sram_burn` covers browser Up/Down order, SRAM cycle passes, a stopped write,
and Burn In's SRAM watch passing and then catching a flipped bit.

`stack_depth` fills the WRAM between static data and the stack with `$A5`,
opens and runs every instrument in each build and model, and requires the
lowest changed byte to stay above the static RAM limit in
`tools/check_build.py`. It writes the measured depths to
`build/stack-depth.json`.

`screen_tour` walks every screen of both builds in SameBoy, in color and
monochrome, and judges each frame as shown. It rejects a font slot showing
anything but its glyph, a cell that blinks off and back within four frames, a
change that takes more than three frames to land, and a blank body longer than
18 frames. `--frames` keeps every other frame for review.

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

`ir_pair` runs two benches in `tests/two_consoles.py`, a pure-Python copy of
PyBoy that steps two consoles a few cycles at a time on one clock, with their
infrared ports facing each other. PyBoy's own infrared port reads as idle.
The receiver must count every pulse the sender's LED makes, read the port
at least every 56 cycles, and stop for no more than 3,000 cycles a frame
outside its redraw after a burst. The ON 1 width is not covered: its pulse
is shorter than the gap between reads.

`link_pair` runs two benches in Link on the same harness with a cable that
behaves as the hardware's does: the host's clock never waits, and an edge that
finds the peer unarmed is lost. Clean runs at each pairing of CPU speeds, with
the peer's frames half a frame apart and under all stress, must lose no edge
and count no error. A bit flipped in a packet's payload must count as one CRC
error and no SEQ error, a dropped edge must recover without a two-second gap, and a 40-frame
unplug must count one host dropout and packets missing at the peer.

`link_stress` runs the same cable with the rate settings at both CPU speeds.
Paced, Burst, Full and Full on the fast wire must stay clean and move the
same bytes per run as the build before Custom pacing: Paced and Burst within
1%, Full within 3%, since it moves about 1.5% fewer, the cost of the 32-bit
interval clock. The loop's work, not the wire, limits Full, so the fast wire
moves no more bytes; the host must clock the wire at 16 cycles a bit on it
and 512 otherwise, halved at double speed. Each case must also find the Burst,
Idle and masked-lines steps it set held on each end. Custom bursts of 8 bytes
with 488 us between them must stay clean and move at least 1.2 times the
Burst preset's bytes. With 8 lines masked each frame on both ends, Burst must
stay clean. The loop's own work spaces bytes about 6 ms apart even with no
idle, so Custom All with no idle fails only once the peer masks 64 lines
(7.3 ms) and loses edges. 64 masked lines on the host must stay clean and
move fewer bytes than Full.

`link_snapshot` starts the peer 150 frames before the host. That wait must
not count as a failure, a gap or a recovery, and the first packet must clear
it. A bit then flipped in a payload byte must leave the peer a snapshot of the
rejected packet, sync bytes first and CRC bytes as the CRC view reports them,
with the settings in use and the serial registers. The snapshot must not
change through recovery, page and view changes, or a stop. Its cost, timed on
one console stepped an instruction at a time, is about 2000 cycles once a
test and must stay under 2500.

`link_long` runs two benches under All stress with their frame counters
starting just short of the 65536-frame wrap, so ordinary intervals cross
it and must not read as gaps. It then unplugs the cable and moves each
counter forward 100000 frames in steps, as 28 minutes of silence would, more
than 65536 of them after no sync has latched. The gap, the recovery and the
host's reply wait must each count all 100000 frames, and the first failure
must survive the recovery. A build that kept these intervals in 16 bits, or
one that sampled its 32-bit clock only while packets flowed, reads about
34500, the part past the wrap.

`upstream` rebuilds and runs every vendored standalone suite. `link_combined`
uses a separate autorun build and synthetic paired byte transport.
`rumble_combined` runs the compiled motor/delay/input bytes in the timing
interpreter, substituting its supported standalone renderer at draw calls.
Neither proves physical serial timing or motor performance.

PyBoy reads the sound registers as zero unless it emulates sound, so every
suite that checks the APU is off afterwards runs with sound emulated.
`audio_backend` redirects startup to a call stub; `audio_ui`, `audio_shapes`
and `audio_sameboy` additionally exercise ordinary cartridge inputs.
`audio_dacs` reads all four DAC enables on every frame through bursts, voice
changes, frequency steps, level 0 and stop/start, since a DAC switched off and
on pops on hardware and PyBoy does not reproduce the pop.
`audio_responsiveness` taps Right for one frame at twelve animation phases and
requires each tap to step the frequency. It also requires the scrolling graph's
map copy to finish before line 48, where the graph starts. Frequency
measurements find the strongest spectral peak above 10 Hz before comparing it
with the requested frequency; they do not restrict the search to that frequency.
`cart`, `libretro`, `audio_navigation` and `display_assertions` are helpers,
not standalone test suites. `capture_review` and `capture_flicker` generate review
media and do not establish a pass by themselves. They record each image's ROM
hashes, the commit it was built from and the emulator in `assets/media.json`.

When adding a regression, retain the prior ROM and matching symbols. Reproduce
the failure there first, then run the same inputs against the fixed build.
Fault cases should reject corrupted output as well as accept the normal result.
The suite does not substitute emulator output for physical-device evidence.
