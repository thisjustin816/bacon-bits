# Controls and tests

A opens a browser card. The third card shows which release is running: Rumble
on MBC5 or Clock on MBC3. Settings use Up/Down to select a field, Left/Right to
change it, and Select to change pages. Changing a setting rewrites it in place;
a new screen appears once it is fully drawn. A starts an activity; B stops it or
returns. Presets configure a test without starting it. Continue preserves
custom settings. A confirmation starts on No.

Platform, Link, Rumble, Buttons and Flicker use A+B+Start+Select to open a
return dialog. Continue is selected first; Test menu returns to the browser.
Stop Link or Rumble before opening it. Buttons requires the chord to be held
for at least 60 frames so each of its buttons can be tested separately.

## Platform

The chip diagram shows the twelve captured probe results. Filled ports passed;
a crossed port failed. The summary reports hardware class and any matching
emulator signature. A or Select opens the evidence.

Left/Right chooses a probe. A switches between failed probes and all twelve.
Select switches to name evidence, and B returns to the diagram. Each probe
shows expected bytes, captured reads, and what it checks. KEY1 compares its
unused-bit mask. RP accepts three documented signatures. Monochrome hardware
reports that the CGB probes do not apply.

The classification follows Platform Detect v1.4's ordered rules. A named host
can pass all twelve probes, and an unknown signature can still fail probes.
These register signatures do not guarantee host identity.

## Link

Five profiles cover sustained packets, scene waits, unequal CPU load, a shared
ball, and combined stress. Settings select host/peer, profile, pacing, wire
clock, and CPU speed. Fast wire clock and double CPU speed require CGB hardware.

Start begins the test. B stops it; Start then returns to settings. Left/Right
changes between traffic, shared-state, timing, and ball pages. A or Up/Down
changes the detail page. Select holds or resumes the displayed results while
the test continues.

The traffic instrument advances with accepted packets. Detailed pages retain
CRC, sequence, payload, overflow, underrun, timeout, barrier, state, and order
errors. Sequence counts packets that went missing without being rejected, so a
packet that failed its CRC counts once, under CRC. Timing includes reply, gap,
recovery, and deadline readings, and its second page counts dropouts: runs of
16 or more $FF bytes after the first packet, which is what an end reads when
the other stops driving the wire. Only the host sees a dropout; the peer sees
a gap. The reply budget depends only on the rate, so a slower CPU or a heavier
profile can make most updates late with no fault on the wire. Compare late
updates only between runs with the same settings. The first failure keeps its
expected and received values. No peer is Wait, and a clean run needs ten
minutes before reporting Pass.

## Rumble (MBC5)

Start plays or stops. B changes between pattern, on sweep, off sweep, and
preset modes. In the pattern editor, Left/Right chooses a bit and A flips it.
Up/Down changes bit length; in preset mode it chooses among ten presets.
A imports a preset into the editable pattern.

Hold Select to see timing settings. Select+A switches frame/millisecond units;
Select+B changes prespin. Select+Up/Down changes burst length, and
Select+Right/Left changes the gap. A zero burst length runs continuously;
a zero gap produces one burst. The instrument previews the pattern and its
nominal period in milliseconds. An on/off sweep retains its Felt at reading.
In the pattern editor, a bar under the waveform marks the selected bit.
Rendering occurs outside the original motor-delay sections.

The frame range is 1-16; millisecond mode offers 1-99. Sweep steps cover 1-32
bits. Prespin, burst length, and gaps can be adjusted independently. The motor
is commanded off on return. Its physical response requires observation.

## Clock (MBC3)

Presets cover live observation, a held latch, temporary halt, and day rollover.
Live and latch tests leave clock registers unchanged. Select opens mode,
observation window, seed day/time, halt, and carry settings. The window is
1-120 seconds; seed fields cover the RTC's complete documented ranges.

A starts or stops observation. Halt and rollover tests require confirmation.
Halt checks whether the captured time stays fixed. Rollover starts from the
configured seed, initially day 511 at 23:59:58, and observes the day carry.
The display separates a tick observation from latch or halt changes. The last
settings page counts Changed readings: in Latch mode, reads that differed while
the latch was held; in Halt mode, reads that moved while the clock was halted.

Before a clock-changing test, the ROM saves a recovery record. Stopping or
returning restores the saved clock with elapsed software time added, unless
the original clock was halted. This has whole-second resolution. A power cut
leaves a recovery prompt on the next visit. Confirming it restores the saved
snapshot; elapsed time during that interruption is unknown. No retains the
record and returns without changing the clock.

Invalid RTC reads remain read-only. This test does not establish oscillator
accuracy or battery retention.

## Audio

The waveform preview shows the selected shape, not measured sound. Up/Down
moves the cursor among voice, frequency/clock, level, and stereo output.
Left/Right changes that setting. Select opens shape, fine/preset stepping,
on frames, and gap frames. A toggles playback. B silences the APU and returns.

Presets are low end, pulse pair, stereo check, and burst check. Low end uses
a 32 Hz sine at full wave level. Pulse pair starts at 440 Hz and 50 percent
duty; either pulse voice can be selected. Stereo starts on the left output.
Burst check uses a triangle with 30-frame on and gap intervals.

Both pulse voices offer 12.5/25/50/75 percent duty. Wave offers sine, square,
triangle, ascending saw, descending saw, and 25 percent pulse. Noise offers
15-bit and 7-bit LFSR modes. Sweep and volume envelopes are disabled.

Pulse spans 64-131,072 Hz and wave spans 32-65,536 Hz. The front page shows
the frequency to 0.1 Hz below 1 kHz, in whole hertz up to 99,999 Hz, and in kHz
above that. Preset offers 34 steps,
with more near the low end. Fine changes the 11-bit register through all 2,048
settings. Pulse and noise have levels 0-15; wave has mute, quarter, half, and
full. Output selects both stereo outputs, left, or right.

Noise has all 60 distinct running clocks, from 4.57 to 524,288 Hz. The clock
is the LFSR shift rate. Its lowest setting can take seconds to change output.
Settings above hearing range remain available for comparisons.

Playback can hold continuously or run for 1-120 frames, with gaps of 0-120
frames. A nonzero gap repeats;
zero gap ends after one burst. Changing a sound setting restarts its burst.
Gates follow the polling loop, with the configured intervals as minimums.
Listening on hardware is needed to judge low-frequency audibility.

## Buttons

Presets cover live buttons, short events, hold timing, and diagonals. Select
changes between live, press-count, timing, and diagonal views. Left/Right
chooses a button on the count and timing pages. Taps (short presses) and gaps
(short releases) have separate counters; Up/Down changes their threshold from
1-8 frames. A changes hold units between frames and milliseconds. Start opens
the clear-counts confirmation.

Select, A and Start act when the button is released, and only when no other
button was held with it. Holding combinations, or the return chord, leaves the
page, units and counters as they were.

The D-pad diagram marks the current corner. Each of the four corners has an
entry count and longest hold. A changes between counts, hold frames, and hold
milliseconds. Opposite-direction reports have a separate counter. Large corner
readings display 99K+ while the underlying counters remain intact. Other
counters use K/M/G units when a full number would cross the right margin.

Presets preserve counters. Control inputs are sampled too. This software test
cannot measure electrical contact bounce or events shorter than its polling
interval. A diagonal report describes the button states the ROM received.

## Display

Presets cover pixel, color, motion, and flicker checks. Settings offer six
colors, widths of 1/2/4/8/16 pixels, either axis, scrolling at 1-8 pixels per
frame, inversion, and a 1-60-frame flicker interval. Each flicker phase lasts
exactly the set number of frames. A opens the full LCD
pattern, Left/Right changes patterns, Select inverts, and B restores settings.

The ramp covers all 32 component levels within 128 vertical pixels.
Monochrome hardware shows its four shades. Test patterns use the complete LCD
so the interface does not obscure pixels being checked.

## Flicker

Flicker compares temporal effects with a static dither reference. Its original
patterns cover four techniques:

- Layers alternates two background planes behind a solid moving probe.
- Shadows keeps the scene and probe solid while alternating a small shadow.
- Fine detail swaps checker phases at cell widths from 1 to 8 pixels.
- Color mix swaps two large fields, with gray, gold/sky, or red/blue endpoints.

These demonstrate techniques used in games such as ZAS and Shantae. They do
not reproduce either game's artwork or rendering engine. The overview is a
fixed illustration of alternating layers and spatial dithering; A opens the
selected pattern over the full display.

Each preset opens stopped. Select cycles through the overview, cadence,
motion, and color pages. Phase A and B each last 1-60 LCD frames. Lead chooses
the first phase. Duty is A's share of the cycle; the displayed cycle rate uses
the Game Boy's approximately 59.7275 Hz LCD refresh. A 1/1 cycle is about
29.86 Hz. Unequal lengths help compare visible flicker at different duties.

Motion can advance every frame or once per complete B-to-A cycle, at 0-8
pixels per step, horizontally, vertically, or diagonally. The probe wraps
within the test area. Fine detail hides it so the checker remains unobstructed.
Choose Compare Split to retain a fixed dither patch and both endpoints along
the bottom edge, or Off to use the full height. The reference never scrolls.
It remains 50/50 spatial dithering even when the temporal duty is unequal.

On color hardware each endpoint has 32 brightness settings. Monochrome uses
four shades and the Gray pair. Color mix defaults to gold and sky on color
hardware, or white and black in monochrome. Equal endpoints intentionally
remove the difference between phases.

In full view, A pauses or resumes, Right advances exactly one frame while
paused, and B stops and restores settings. Settings persist through Continue.
The return chord stops the test before opening the usual Continue/Test menu
dialog; Continue returns to stopped settings.

Both phase maps are prepared before timed playback. During playback, the
background map switches in VBlank and the probe uses at most six sprites.
The emulator suites measure consecutive raw frames, phase durations, static
references, movement, pause/step, and cleanup in both display modes and both
mapper builds. These checks cannot establish physical panel response,
persistence, or a frontend's frame-blending appearance. Those comparisons
require viewing the output with the relevant display or blending setting.

## SRAM

Presets cover a power cycle, a 32 KiB bank check, walking bits, and retention
intervals. Verify starts read-only. Write and Cycle require confirmation and
erase the selected test banks. Choose 1/2/4 banks in either release or 8 in
MBC5, eight patterns, a seed, 1/10/100/continuous passes, and a 0-30-second pause.
The 32 KiB bank preset suits the insideGadgets RGB cartridge; its actual FRAM
capacity is four banks. The MBC5 release can also test eight-bank cartridges.

Write writes once and verifies; Cycle writes and verifies each pass. Patterns
are zero, ones, 55, AA, walking one/zero, address, and seeded data. Sixteen bytes
per bank contain distinct tags to expose aliasing. Results retain the first
failing bank, decimal offset, expected byte, and read byte.

Bank 0's final 32 bytes are reserved. Sixteen hold the last completed pattern
configuration; the other sixteen hold RTC recovery. A power-cycle Verify uses
the checked pattern record. Missing or invalid records report Unknown.
Eight banks cover 65,504 pattern bytes; four cover 32,736. Stopping verification
does not report Pass. Emulator saved-file persistence does not establish
physical battery retention.

## Burn In

Presets cover a quick check, long soak, output load, and read-only SRAM watch.
Choose 1/5/10/30/60 minutes or continuous operation, three loads, normal/double
CPU speed, and stop/continue on failure. The instrument shows elapsed time,
completed cycles, error count, and the ROM bank being checked.

Burn In compares CRC-16 checksums across all eight ROM banks and writes/reads
256 bytes of scratch RAM. The CRC table and cartridge global checksum are
excluded from those CRCs. The scratch check does not test all work RAM.
Audio and rumble pulses, or a read-only RTC watch in MBC3, are optional and
start off. SRAM verification is read-only and reports a missing test record.
The first failure remains available while later cycles continue. A ROM CRC
failure identifies a complete bank. SRAM and scratch faults include a byte
offset. An invalid RTC read records the register, its limit, and its value.

Rumble f sets how many frames the motor runs at the start of each second,
from 0 to 6. The pulse is timed from VBlank, so it keeps its length at every
load. The MBC3 RTC watch reads the clock every 64 frames.

B stops and switches outputs off. Select opens first-failure details, or a
summary of cycles and seconds when nothing failed.
Start from stopped results returns to settings. Elapsed time follows VBlank
at either CPU speed.

## Cart LED (MBC5)

The MBC5 release supports the [insideGadgets MBC5 RGB cartridge](https://shop.insidegadgets.com/product/gameboy-2mb-32kb-fram-flash-cart-ultra-low-power/).
Presets cover primary colors, white levels, a color cycle, and pulses.
A starts or stops output, Select opens settings, and B sends off and returns.
Each RGB component has 256 settings; the interval is 1-255 software frames.
Manual color changes replace the automatic sequence.

The stopped page shows configured RGB values. During output, the lamp and
values preview the last command. Command sent means a write occurred. There is
no LED readback, so
appearance, brightness, and hardware support require observation.
The MBC3 release disables this page's output because its RTC uses the same
address range.

## Infrared (CGB)

Presets cover receive-only observation, short bursts, a slow beacon, and dense
bursts. A starts or stops. Left/Right changes receive/transmit mode; Select
opens ON/OFF width, pulse count, and repetition interval. B disables the IR
port, restores CPU speed, and returns. DMG and GBA report no CGB IR port.

Receive mode reads the port every 40 to 56 CPU cycles with interrupts held
off and counts each time light arrives. It counts every pulse when ON and OFF
are each at least 2 steps; at ON 1 it misses some. It stops reading once a
frame, for about 0.7 ms of VBlank work, and for up to two frames while the
screen shows a new count. A burst that arrives then loses the pulses sent
during it. Transmit mode counts the bursts it sends. Counts are not protocol
decoding or a peer acknowledgement.
A constant IR source can become ambient to the receiver, so transmit mode
uses bursts.

Bursts use the normal-speed CPU. The width controls step by 16 CPU cycles,
about 3.815 microseconds. ON ranges from 7.63-125.89 microseconds and OFF
from 11.44-129.70. The common preset is approximately 11.44 ON / 19.07 OFF,
with 32 pulses. Choose 1-64 pulses and 1-240 frames between bursts. Individual
widths are cycle-counted; repetition follows the UI polling loop. Receiver
sensitivity and physical transmission require hardware observation.

RTC and IR register behavior follows [Pan Docs](https://gbdev.io/pandocs/).
