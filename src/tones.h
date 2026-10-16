#ifndef TONES_H
#define TONES_H
#include <gb/gb.h>
extern uint8_t tone_voice,tone_index,tone_level,tone_output,tone_playing;
extern uint8_t tone_shape[4],tone_fine,tone_on,tone_gap,tone_gate;
extern uint16_t tone_register;
extern uint8_t tone_noise_clock;
extern uint32_t tone_hundredths;
void tone_apply(void);
void tone_stop(void);
uint8_t tone_count(void);
void tone_measure(void);
uint8_t tone_sample(uint8_t sample);
void burn_audio(uint8_t voice) BANKED;
#endif
