;; Slowdown's timed code: the burn loop, the per-update loop and the VBlank
;; handler that counts and draws the readout. They stay in bank 0 so the
;; handler can run whichever bank the main loop has mapped, and so their
;; cycle counts do not include bank switches.

	.module slowdown_asm
	.globl _shadow_OAM, _sys_time, __vbl_done, _joypad

	;; Readout cells in the background map at 9800.
	FRAMES_AT = 0x994B	; row 10, column 11
	LAG_AT = 0x998B		; row 12, column 11
	WINDOW_AT = 0x99ED	; row 15, column 13
	RUN_AT = 0x9A27		; row 17, column 7
	LONGEST_AT = 0x9A30	; row 17, column 16

	;; Sprite 0 is the VBlank marker and sprite 1 the Update marker. Each
	;; moves one pixel along a 64-pixel track.
	MARKER_X = 80

	.area _DATA

;; Burn In's scratch test and a Slowdown run never happen at once, so they
;; share these 256 bytes. Slowdown keeps only its run state here.
_bb_shared::
;; Packed BCD, least significant byte first: VBlanks since the start, and
;; those that found the main loop still working.
_slow_frames::
	.ds 3
_slow_lag::
	.ds 3
;; Lag frames in the last complete block of 64 VBlanks (BCD), and the count
;; for the block in progress.
_slow_window::
	.ds 1
_slow_window_count::
	.ds 1
;; VBlanks into the current block, 0 to 63.
_slow_frame64::
	.ds 1
;; Consecutive lag frames now, and the longest run.
_slow_run::
	.ds 1
_slow_longest::
	.ds 1
;; 1 from the main loop's wake until it waits again.
_slow_busy::
	.ds 1
;; The second count: GBDK's frame counter at the last wake, and the lag
;; frames summed from the gaps between wakes (24-bit binary).
_slow_last::
	.ds 2
_slow_tick_lag::
	.ds 3
_slow_keys::
	.ds 1
_slow_update_x::
	.ds 1
;; The schedule: up to 60 burn lengths in loops, used in turn. An entry
;; repeats slow_reps[index & 1] times, so Pulse needs two entries and Ramp
;; one per step.
_slow_index::
	.ds 1
_slow_left::
	.ds 1
_slow_count::
	.ds 1
_slow_reps::
	.ds 2
_slow_sched::
	.ds 120
	.ds 256 - (. - _bb_shared)

	.area _HOME

;; Burns 28 cycles for each of the DE (1-65535) iterations, from the first
;; instruction to the ret.
_slow_burn::
	ld a,e
1$:
	dec de
	ld a,d
	or e
	jr nz,1$
	ret

;; Draws the readout as the previous VBlank left it, then counts this one.
;; Every path takes the same number of cycles, whatever the counts hold, so
;; the readout's cost is a fixed part of each update's overhead.
	.macro BCD_DIGITS
	ld a,(bc)
	swap a
	and d
	or e
	ld (hl+),a
	ld a,(bc)
	and d
	or e
	ld (hl+),a
	.endm
	.macro BCD_PAIR
	BCD_DIGITS
	dec bc
	.endm

_slow_vbl::
	;; D masks a digit and E holds the tile of '0'.
	ld de,#0x0F10
	;; Lag directly follows Frames, so one pointer walks down both.
	ld bc,#_slow_lag+2
	ld hl,#LAG_AT
	BCD_PAIR
	BCD_PAIR
	BCD_PAIR
	ld hl,#FRAMES_AT
	BCD_PAIR
	BCD_PAIR
	BCD_DIGITS
	ld bc,#_slow_window
	ld hl,#WINDOW_AT
	BCD_DIGITS
	ld a,(_slow_run)
	or e
	ld (RUN_AT),a
	ld a,(_slow_longest)
	or e
	ld (LONGEST_AT),a

	ld a,(_slow_busy)
	ld b,a
	ld c,#0
	ld hl,#_slow_frames
	ld a,(hl)
	add a,#1
	daa
	ld (hl+),a
	ld a,(hl)
	adc a,c
	daa
	ld (hl+),a
	ld a,(hl)
	adc a,c
	daa
	ld (hl+),a
	ld a,(hl)
	add a,b
	daa
	ld (hl+),a
	ld a,(hl)
	adc a,c
	daa
	ld (hl+),a
	ld a,(hl)
	adc a,c
	daa
	ld (hl),a

	;; Run counts while busy and clears on an idle VBlank.
	xor a
	sub b
	ld e,a
	ld a,(_slow_run)
	inc a
	and e
	ld (_slow_run),a
	ld d,a
	ld a,(_slow_longest)
	cp d
	jr nc,2$
	ld a,d
2$:
	ld (_slow_longest),a

	ld hl,#_slow_frame64
	ld a,(hl)
	inc a
	and #63
	ld (hl),a
	ld d,a
	add a,#MARKER_X
	ld (_shadow_OAM+1),a
	ld hl,#_slow_window_count
	ld a,(hl)
	add a,b
	daa
	ld e,a
	ld a,d
	or a
	jr nz,3$
	;; A block ends: show its count and start the next from zero.
	ld a,e
	ld (_slow_window),a
	ld e,c
	jr 4$
3$:
	;; Same cost as the path above.
	ld a,(_slow_window)
	ld (_slow_window),a
4$:
	ld (hl),e
	ret

;; One update: wait for VBlank, count the frames since the last wake, read
;; the pad, then burn this update's share. Returns 0 to go on, 1 for B, 2
;; for the return chord and 3 when Frames is about to pass 999,999.
_slow_update::
	xor a
	ld (__vbl_done),a
	ld (_slow_busy),a
	halt
	nop
5$:
	ld a,(__vbl_done)
	or a
	jr nz,6$
	halt
	nop
	jr 5$
6$:
	ld a,#1
	ld (_slow_busy),a

	ld hl,#_sys_time
	ld a,(hl+)
	ld d,(hl)
	ld e,a
	ld hl,#_slow_last
	ld a,e
	sub (hl)
	ld c,a
	ld (hl),e
	inc hl
	ld a,d
	sbc a,(hl)
	ld b,a
	ld (hl),d
	dec bc
	ld hl,#_slow_tick_lag
	ld a,(hl)
	add a,c
	ld (hl+),a
	ld a,(hl)
	adc a,b
	ld (hl+),a
	ld a,(hl)
	adc a,#0
	ld (hl),a

	call _joypad
	ld b,a
	ld hl,#_slow_keys
	ld a,(hl)
	cpl
	and b
	ld c,a
	ld (hl),b
	ld a,b
	and #0xF0
	cp #0xF0
	jr z,12$
	ld a,c
	and #0x20
	jr nz,11$
	;; 99 99 9x is the last block of ten before the six digits roll over.
	ld a,(_slow_frames+2)
	ld b,a
	ld a,(_slow_frames+1)
	and b
	ld b,a
	ld a,(_slow_frames)
	or #0x09
	and b
	cp #0x99
	jr z,13$

	ld a,(_slow_index)
	ld c,a
	ld b,#0
	ld hl,#_slow_sched
	add hl,bc
	add hl,bc
	ld e,(hl)
	inc hl
	ld d,(hl)
	ld hl,#_slow_left
	dec (hl)
	jr nz,8$
	;; The entry is used up: take the next, back to the first after the last.
	inc c
	ld a,(_slow_count)
	sub c
	add a,#0xFF
	sbc a,a
	and c
	ld (_slow_index),a
	and #1
	ld c,a
	ld hl,#_slow_reps
	add hl,bc
	ld a,(hl)
	ld (_slow_left),a
	jr 9$
8$:
	;; Same cost as the path above.
	ld a,#7
10$:
	dec a
	jr nz,10$
	nop
9$:
	call _slow_burn

	ld hl,#_slow_update_x
	ld a,(hl)
	inc a
	and #63
	ld (hl),a
	add a,#MARKER_X
	ld (_shadow_OAM+5),a
	xor a
	ret
11$:
	ld a,#1
	ret
12$:
	ld a,#2
	ret
13$:
	ld a,#3
	ret
