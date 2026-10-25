"""Two consoles in one process, stepped in lockstep on a shared clock.

PyBoy runs one console. Its infrared port is a stub that reads $FF, and its
linked serial makes each side wait for the other, so neither can show a
timing fault between two machines. This module runs two consoles on a
pure-Python copy of the installed PyBoy, a few cycles at a time, the one
behind first. Times are in normal-speed cycles from when the pair was formed.

Pair(cable=True) joins them with Cable, a link cable that behaves as the
hardware's does: the clocking end shifts a bit on each edge and never waits,
and an edge that finds the other end unarmed is lost. Infrared(pair) faces
their infrared ports instead.

The copy, made under build/ and imported as pyboy_pair, is patched at load:
- the infrared port (RP, $FF56) goes to the machine's ir_read and ir_write;
- a KEY1 write changes only the switch bit, as on hardware (PyBoy's own write
  replaces the current-speed bit);
- each mb.tick() runs at most the machine's step_cycles;
- an instruction that starts at $3FFE or $3FFF is fetched from bank 0.
"""
from __future__ import annotations

import bisect
import importlib
import importlib.util
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'pyboy_pair'
CACHE = ROOT / 'build' / 'pair-pyboy'
COPY_VERSION = '1'
FRAME = 70224


def _copy_pyboy() -> Path:
    source = Path(importlib.util.find_spec('pyboy').origin).parent
    dest = CACHE / PACKAGE
    stamp = CACHE / 'source.txt'
    key = f'{source}\n{(source / "core" / "mb.py").stat().st_mtime_ns}\n{COPY_VERSION}\n'
    if stamp.exists() and stamp.read_text() == key and (dest / '__init__.py').exists():
        return CACHE
    shutil.rmtree(dest, ignore_errors=True)
    for f in source.rglob('*'):
        if not f.is_file() or f.suffix not in ('.py', '.bin', '.txt', '.json') or '__pycache__' in f.parts:
            continue
        target = dest / f.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        if f.suffix != '.py':
            shutil.copyfile(f, target)
            continue
        text = f.read_text(encoding='utf-8')
        text = re.sub(r'\bfrom pyboy(\.[\w.]*)? import', rf'from {PACKAGE}\1 import', text)
        text = re.sub(r'^(\s*)import pyboy\s*$', rf'\1import {PACKAGE} as pyboy', text, flags=re.M)
        target.write_text(text, encoding='utf-8')
    mb = dest / 'core' / 'mb.py'
    text = mb.read_text(encoding='utf-8')
    for old, new in (
            ('while not self.lcd.frame_done:', 'for _step in range(1):'),
            ('self.timer._cycles_to_interrupt,', f'getattr(self, "step_cycles", {FRAME}), self.timer._cycles_to_interrupt,'),
            ('                # IR Port\n                return 0xFF',
             '                return self.ir_read() if hasattr(self, "ir_read") else 0xFF'),
            ('                pass  # IR Port',
             '                if hasattr(self, "ir_write"): self.ir_write(value)'),
            ('            elif self.cgb and i == 0xFF4D:\n                self.key1 = value',
             '            elif self.cgb and i == 0xFF4D:\n                self.key1 = (self.key1 & 0x80) | (value & 0x01)')):
        if text.count(old) != 1:
            raise RuntimeError(f'unexpected PyBoy mb.py layout: {old!r}')
        text = text.replace(old, new)
    mb.write_text(text, encoding='utf-8')
    cpu = dest / 'core' / 'cpu.py'
    text = cpu.read_text(encoding='utf-8')
    broken = 'elif (not self.mb.bootrom_enabled) and self.PC + 2 < 0x8000:'
    fixed = 'elif (not self.mb.bootrom_enabled) and 0x4000 <= self.PC and self.PC + 2 < 0x8000:'
    if broken in text:
        text = text.replace(broken, fixed)
    elif fixed not in text:
        raise RuntimeError('unexpected PyBoy cpu.py layout')
    cpu.write_text(text, encoding='utf-8')
    stamp.write_text(key)
    return CACHE


def pyboy_module():
    CACHE.mkdir(parents=True, exist_ok=True)
    path = str(_copy_pyboy())
    if path not in sys.path:
        sys.path.insert(0, path)
    return importlib.import_module(PACKAGE)


class Cable:
    """The wire between two serial ports. Each edge from the clocking end
    shifts a bit into each end armed at that moment, judged by the time it
    armed, not by whether it has armed by the time the step reaches the
    edge. fault() flips a received bit or drops an edge at one end, and
    connected=False unplugs it: the clocking end reads 1 bits and the other
    gets no edges."""

    def __init__(self) -> None:
        self.ends = []
        self.edges = 0
        self.bytes = [0, 0]
        self.missed = [0, 0]
        self.connected = True
        self.faults = {}
        self.injected = []
        # How long before a byte's first edge the receiving end armed.
        self.slack = []

    def fault(self, kind: str, edge: int, receiver: int) -> None:
        """Flip the bit end receiver takes at absolute edge, or drop that edge."""
        if kind not in ('flip', 'drop') or receiver not in (0, 1) or edge <= self.edges:
            raise ValueError((kind, edge, receiver))
        self.faults[edge] = (kind, receiver)

    def advance(self, now: float) -> None:
        while True:
            senders = [e for e in self.ends if e.transfer_enabled and e.internal_clock and e.edge <= now]
            if not senders:
                return
            sender = min(senders, key=lambda e: e.edge)
            at = sender.edge
            armed = [bool(e.transfer_enabled) and e.armed_at <= at for e in self.ends]
            bits = [(e.SB >> 7) & 1 if on else 1 for e, on in zip(self.ends, armed)]
            if sender.bits == 0:
                self.slack += [at - e.armed_at for e, on in zip(self.ends, armed) if e is not sender and on and e.bits == 0]
            self.edges += 1
            fault = self.faults.pop(self.edges, None)
            if fault:
                self.injected.append((self.edges, at, *fault))
            for i, (end, on) in enumerate(zip(self.ends, armed)):
                if end is not sender and not self.connected:
                    continue
                if fault == ('drop', i):
                    continue
                if not on:
                    self.missed[i] += 1
                    continue
                bit = bits[1 - i] if self.connected else 1
                if fault == ('flip', i):
                    bit ^= 1
                end.SB = ((end.SB << 1) & 0xFF) | bit
                end.bits += 1
                if end.bits == 8:
                    end.transfer_enabled = 0
                    end.SC &= 0x7F
                    end.mb.cpu.set_interruptflag(8)
                    self.bytes[i] += 1
            if sender.transfer_enabled:
                sender.edge = at + sender.period


def _end_class(serial, utils):
    class End(serial.Serial):
        """One console's serial port, timed on the pair's clock."""

        def __init__(self, cgb):
            super().__init__(cgb)
            self.edge = utils.MAX_CYCLES
            self.bits = 0
            self.armed_at = utils.MAX_CYCLES
            self.mb = None
            self.base = 0.0

        def now(self):
            return mb_clock(self.mb) - self.base

        def set_SB(self, value):
            self.SB = value

        def set_SC(self, value):
            self.SC = value | 0x7C
            self.transfer_enabled = value & 0x80
            self.internal_clock = value & 1
            self.bits = 0
            now = self.now()
            self.armed_at = now if self.transfer_enabled else utils.MAX_CYCLES
            # 8192 Hz, or 262144 Hz with CGB fast clock; double speed doubles either.
            self.period = (16 if value & 2 else 512) / (2 if self.mb.double_speed else 1)
            self.edge = now + self.period if self.transfer_enabled and self.internal_clock else utils.MAX_CYCLES
            self._cycles_to_interrupt = utils.MAX_CYCLES

        def tick(self, cycles):
            self.last_cycles = cycles
            return False
    return End


def mb_clock(mb) -> float:
    """A console's time in normal-speed cycles. The CPU's cycle count runs
    twice as fast at double speed, so the time accumulates step by step at
    the speed in force, and a speed switch mid-run leaves no jump."""
    cycles = mb.cpu.cycles
    last = getattr(mb, 'pair_clock', None)
    if last is None:
        time = cycles / (2 if mb.double_speed else 1)
    else:
        time = last[1] + max(cycles - last[0], 0) / (2 if mb.double_speed else 1)
    mb.pair_clock = (cycles, time)
    return time


def clock(pb) -> float:
    return mb_clock(pb.mb)


def run_frames(pb, frames: int) -> None:
    """Run one console on its own for whole frames."""
    for _ in range(frames):
        while not pb.mb.lcd.frame_done:
            pb.mb.tick()
        pb.mb.lcd.frame_done = False
        pb.frame_count += 1
        pb._handle_events(pb.events)
        pb._post_handle_events()


def press(pb, button: str, held: int = 8, after: int = 24) -> None:
    pb.button_press(button)
    run_frames(pb, held)
    pb.button_release(button)
    run_frames(pb, after)


class Pair:
    """Two consoles on one clock. Run each to where the test wants it with
    run_frames and press, then call start(): from then on step() runs the
    console that is behind for step_cycles, and presses land by frame."""

    def __init__(self, roms, *, cgb=True, cable=False) -> None:
        pyboy = pyboy_module()
        serial = importlib.import_module(f'{PACKAGE}.core.serial')
        utils = importlib.import_module(f'{PACKAGE}.utils')
        original = serial.Serial
        if cable:
            serial.Serial = _end_class(serial, utils)
        self.machines = []
        try:
            for rom in roms:
                pb = pyboy.PyBoy(str(rom), window='null', sound_emulated=False, cgb=cgb)
                pb.set_emulation_speed(0)
                pb.mb.lcd.disable_renderer = True
                pb.mb.serial.mb = pb.mb
                self.machines.append(pb)
        finally:
            serial.Serial = original
        self.cable = None
        self.never = utils.MAX_CYCLES
        if cable:
            self.cable = Cable()
            self.cable.ends = [pb.mb.serial for pb in self.machines]
        self.base = [0.0, 0.0]
        self.queues = [[], []]

    def start(self, *, step_cycles: int, offset: int = 0) -> None:
        """Pair the consoles where they stand. offset runs the second one
        that many cycles further first, which moves its frames against the
        first's."""
        second = self.machines[1]
        target = clock(second) + offset
        while clock(second) < target:
            second.mb.tick()
            if second.mb.lcd.frame_done:
                self._frame(1)
        for pb in self.machines:
            pb.mb.step_cycles = step_cycles
        self.base = [clock(pb) for pb in self.machines]
        if self.cable:
            for pb, base in zip(self.machines, self.base):
                end = pb.mb.serial
                # Times already set on the console's own clock move to the pair's.
                for name in ('edge', 'armed_at'):
                    if getattr(end, name) < self.never:
                        setattr(end, name, getattr(end, name) + end.base - base)
                end.base = base

    def now(self, index: int) -> float:
        return clock(self.machines[index]) - self.base[index]

    def _frame(self, index: int) -> None:
        pb = self.machines[index]
        pb.mb.lcd.frame_done = False
        pb.frame_count += 1
        queue = self.queues[index]
        while queue and queue[0][0] <= pb.frame_count:
            _, action, button = queue.pop(0)
            (pb.button_press if action == 'press' else pb.button_release)(button)
        pb._handle_events(pb.events)
        pb._post_handle_events()

    def press(self, index: int, button: str, held: int = 8) -> None:
        frame = self.machines[index].frame_count
        self.queues[index] += [(frame + 1, 'press', button), (frame + 1 + held, 'release', button)]

    def step(self) -> None:
        index = 0 if self.now(0) <= self.now(1) else 1
        if self.cable:
            self.cable.advance(self.now(index))
        pb = self.machines[index]
        pb.mb.tick()
        if pb.mb.lcd.frame_done:
            self._frame(index)

    def run_until(self, predicate, limit: float) -> None:
        """Step until predicate() holds, failing after limit cycles."""
        end = min(self.now(0), self.now(1)) + limit
        while not predicate():
            if min(self.now(0), self.now(1)) > end:
                raise AssertionError('pair ran out of time')
            self.step()

    def close(self) -> None:
        for pb in self.machines:
            pb.stop(save=False)


class Infrared:
    """Two infrared ports facing each other, as two Game Boy Colors held end
    to end. A port reads light (bit 1 low) while reading is enabled (bits 6
    and 7) and the other console's LED (bit 0) is on at that moment. Each LED
    change is kept with its time on the pair's clock, so a read finds the
    other LED as it was then, even when the reader is a step ahead. A real
    receiver's response time, range and ambient light are not modeled."""

    def __init__(self, pair: Pair) -> None:
        self.pair = pair
        self.written = [0, 0]
        self.changes = [[], []]
        self.lit = [[], []]
        for index, pb in enumerate(pair.machines):
            pb.mb.ir_write = lambda value, index=index: self._write(index, value)
            pb.mb.ir_read = lambda index=index: self._read(index)

    def _write(self, index: int, value: int) -> None:
        self.written[index] = value & 0xC1
        led = bool(value & 1)
        if (self.lit[index][-1] if self.lit[index] else False) != led:
            self.changes[index].append(self.pair.now(index))
            self.lit[index].append(led)

    def led(self, index: int, at: float) -> bool:
        k = bisect.bisect_right(self.changes[index], at) - 1
        return self.lit[index][k] if k >= 0 else False

    def pulses(self, index: int, since: float = float('-inf')) -> int:
        """LED turn-ons by console index after time since."""
        return sum(1 for t, on in zip(self.changes[index], self.lit[index]) if on and t > since)

    def _read(self, index: int) -> int:
        value = self.written[index] | 0x3E
        if self.written[index] & 0xC0 == 0xC0 and self.led(1 - index, self.pair.now(index)):
            value &= ~0x02
        return value
