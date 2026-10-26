# Diagnostic development

Bacon Bit Bench is the home for reusable Game Boy and Game Boy Color diagnostic
cartridges, instruments, hardware stress tests and measurement improvements.

- Add new generic diagnostics and their test coverage here. Use this repository's
  issues for diagnostic bugs and feature requests.
- Platform Detect, Link Sustain and Rumble Pulse in their original repositories
  are historical predecessors. Use the bench instruments for current testing.
- Keep game patches and game-specific debugging in their game repositories.
  Keep public reports free of private game names and identifying details.
- Read `vendor/README.md` and the adaptation workflow in `tools/adapt.py` before
  changing imported engines. Preserve the source revision provenance.
- Update the instrument's tests and manual when behavior changes. Measure
  timing and performance against the prior build; diagnostic rendering and
  logging must preserve the workload being measured. Distinguish emulator
  evidence from physical hardware results.
