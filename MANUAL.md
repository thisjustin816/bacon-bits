# Controls and tests

A opens a browser card. Settings use Up/Down to select a field, Left/Right to
change it, and Select to change pages. A starts an activity; B stops it or
returns. Presets configure a test without starting it. Continue preserves
custom settings. A confirmation starts on No.

Platform, Link Cable, and Rumble use A+B+Start+Select to open a return dialog.
Continue is selected first; Test menu returns to the browser. Stop Link Cable
or Rumble before opening it. Buttons requires the chord to be held for at least
60 frames so each of its buttons can be tested separately.

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

## Link Cable

Five profiles cover sustained packets, scene waits, unequal CPU load, a shared
ball, and combined stress. Settings select host/peer, profile, pacing, wire
clock, and CPU speed. Fast wire clock and double CPU speed require CGB hardware.

Start begins the test. B stops it; Start then returns to settings. Left/Right
changes between traffic, shared-state, timing, and ball pages. A or Up/Down
changes the detail page. Select holds or resumes the displayed results while
the test continues.

The traffic instrument advances with accepted packets. Detailed pages retain
CRC, sequence, payload, overflow, underrun, timeout, barrier, state, and order
errors. Timing includes reply, gap, recovery, and deadline readings. The first
failure keeps its expected and received values. No peer is Wait, and a clean
run needs ten minutes before reporting Pass.

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
Rendering occurs outside the original motor-delay sections.

The frame range is 1-16; millisecond mode offers 1-99. Sweep steps cover 1-32
bits. Prespin, burst length, and gaps can be adjusted independently. The motor
is commanded off on return. Its physical response requires observation.

## Real Time Clock (MBC3)

Presets cover live observation, a held latch, temporary halt, and day rollover.
Live and latch tests leave clock registers unchanged. Select opens mode,
observation window, seed day/time, halt, and carry settings. The window is
1-120 seconds; seed fields cover the RTC's complete documented ranges.

A starts or stops observation. Halt and rollover tests require confirmation.
Halt checks whether the captured time stays fixed. Rollover starts from the
configured seed, initially day 511 at 23:59:58, and observes the day carry.
The display separates a tick observation from latch or halt changes.

Before a clock-changing test, the ROM saves a recovery record. Stopping or
returning restores the saved clock with elapsed software time added, unless
the original clock was halted. This has whole-second resolution. A power cut
leaves a recovery prompt on the next visit. Confirming it restores the saved
snapshot; elapsed time during that interruption is unknown. No retains the
record and returns without changing the clock.

Invalid RTC reads remain read-only. This test does not establish oscillator
accuracy or battery retention.

## Audio Range

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

Pulse spans 64-131,072 Hz and wave spans 32-65,536 Hz. Preset offers 34 steps,
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
chooses a button on the count and timing pages. Short presses and short release
gaps have separate counters; Up/Down changes their threshold from 1-8 frames.
A changes hold units between frames and milliseconds. Start opens the
clear-counts confirmation.

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
frame, inversion, and a 1-60-frame flicker interval. A opens the full LCD
pattern, Left/Right changes patterns, Select inverts, and B restores settings.

The ramp covers all 32 component levels within 128 vertical pixels.
Monochrome hardware shows its four shades. Test patterns use the complete LCD
so the interface does not obscure pixels being checked.

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

B stops and switches outputs off. Select opens first-failure details.
Start from stopped results returns to settings. Elapsed time follows VBlank
at either CPU speed.

## Cartridge LED

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

## Infrared

Presets cover receive-only observation, short bursts, a slow beacon, and dense
bursts. A starts or stops. Left/Right changes receive/transmit mode; Select
opens ON/OFF width, pulse count, and repetition interval. B disables the IR
port, restores CPU speed, and returns. DMG and GBA report no CGB IR port.

Receive mode polls throughout a frame and counts observed active edges.
Transmit mode counts the bursts it sends. Counts can miss activity while the
interface updates and are not protocol decoding or a peer acknowledgement.
A constant IR source can become ambient to the receiver, so transmit mode
uses bursts.

Bursts use the normal-speed CPU. The width controls step by 16 CPU cycles,
about 3.815 microseconds. ON ranges from 7.63-125.89 microseconds and OFF
from 11.44-129.70. The common preset is approximately 11.44 ON / 19.07 OFF,
with 32 pulses. Choose 1-64 pulses and 1-240 frames between bursts. Individual
widths are cycle-counted; repetition follows the UI polling loop. Receiver
sensitivity and physical transmission require hardware observation.

RTC and IR register behavior follows [Pan Docs](https://gbdev.io/pandocs/).
