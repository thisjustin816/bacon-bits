GBDK_HOME ?= /opt/gbdk/
PYTHON ?= python3
CC = $(GBDK_HOME)/bin/lcc
FLAGS = -Isrc -Ivendor/link-sustain -Wm-yc -Wm-yt0x1e -Wm-ya4 -Wm-yp0x149=0x05 -Wm-yo8 -Wm-ynBACONBITS -Wl-m -Wl-j
ifneq ($(AUTORUN),)
FLAGS += -DBB_AUTORUN=$(AUTORUN)
endif
SOURCES = src/main.c src/common.c src/manifest.c src/icons.c src/audio.c src/tones.c src/buttons.c src/display.c src/sram.c src/burn.c src/platform_details.c build/adapted/platform.c build/adapted/link.c build/adapted/protocol.c build/adapted/stress.c build/adapted/rumble.c
all:
	mkdir -p build
	$(PYTHON) tools/art.py
	$(PYTHON) tools/tones.py
	$(PYTHON) tools/adapt.py
	$(CC) $(FLAGS) -o build/bacon-bits.gbc $(SOURCES)
	$(PYTHON) tools/adapt.py
	$(CC) $(FLAGS) -o build/bacon-bits.gbc $(SOURCES)
	$(PYTHON) tools/manifest.py
	$(CC) $(FLAGS) -o build/bacon-bits.gbc $(SOURCES)
	$(PYTHON) tools/check_build.py

release: all
	$(PYTHON) tools/check_build.py
	cp build/bacon-bits.gbc "Bacon Bits (World).gbc"

clean:
	rm -rf build
.PHONY: all release clean
