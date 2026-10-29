GBDK_HOME ?= /opt/gbdk/
PYTHON ?= python3
VARIANT ?= mbc5
BUILD_DIR ?= build
export BB_BUILD_DIR = $(BUILD_DIR)
CC = $(GBDK_HOME)/bin/lcc
FLAGS = -I$(BUILD_DIR) -Isrc -Ivendor/link-sustain -Wm-yc -Wm-yo8 -Wm-ynBACONBENCH -Wl-m -Wl-j -Wi-e
ifeq ($(VARIANT),mbc3)
FLAGS += -DBB_MBC3 -Wm-yt0x10 -Wm-ya4
else
FLAGS += -Wm-yt0x1e -Wm-ya4 -Wm-yp0x149=0x05
endif
ifneq ($(AUTORUN),)
FLAGS += -DBB_AUTORUN=$(AUTORUN)
endif
SOURCES = $(BUILD_DIR)/adapted/rumble.c src/main.c src/common.c src/scenes.c src/rumble_ui.c src/manifest.c src/hardware_art.c src/rtc.c src/led.c src/ir.c src/printer.c src/audio.c src/tones.c src/buttons.c src/focus.c src/display.c src/flicker.c src/sram.c src/burn.c src/platform_details.c $(BUILD_DIR)/adapted/platform.c $(BUILD_DIR)/adapted/link.c $(BUILD_DIR)/adapted/protocol.c $(BUILD_DIR)/adapted/stress.c
all:
	mkdir -p $(BUILD_DIR)
	$(PYTHON) tools/art.py
	$(PYTHON) tools/scenes.py
	$(PYTHON) tools/logo.py
	$(PYTHON) tools/flicker_art.py
	$(PYTHON) tools/controls_art.py
	$(PYTHON) tools/hardware_art.py
	$(PYTHON) tools/tones.py
	$(PYTHON) tools/adapt.py
	$(PYTHON) tools/compile.py --cc $(CC) --output $(BUILD_DIR) -- $(FLAGS) $(SOURCES)
	$(PYTHON) tools/adapt.py
	$(PYTHON) tools/compile.py --cc $(CC) --output $(BUILD_DIR) -- $(FLAGS) $(SOURCES)
	$(PYTHON) tools/manifest.py
	$(PYTHON) tools/compile.py --cc $(CC) --output $(BUILD_DIR) -- $(FLAGS) $(SOURCES)
	$(PYTHON) tools/check_build.py

mbc3:
	$(MAKE) VARIANT=mbc3 BUILD_DIR=build/mbc3 all

releases: all mbc3
	$(PYTHON) tools/releases.py

release: releases

clean:
	rm -rf build
.PHONY: all release releases mbc3 clean
