# Diagnostic sources

- `platform-detect/main.c`: Platform Detect v1.4 from
  `thisjustin816/gameboy-homebrew-patches`, commit
  `8451dd8954de4f20a8ff6d402f17e71da81293e6`.
- `link-sustain/`: Link Sustain v1.2 from the same commit.
- `rumble-pulse/`: Rumble Pulse from `thisjustin816/pokepinball-rumble-patch`,
  commit `d5d144f742ca5f6146a3f5196ef31590b95c14b9`.

The source files are kept unchanged. `tools/adapt.py` generates banked entry
points and the return-to-menu hooks in `build/adapted/`. Rumble's assembly is
resolved at address $4000 and keeps its original polled playback routines.
The launcher reuses Rumble Pulse's diagnostic font. Its icons and sunrise
are original drawings in `tools/art.py`.

The supplied reference cartridges contribute no art or code.
