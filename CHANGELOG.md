# Changelog

All notable changes to Filter+FX. Format-2
[elekloader](https://github.com/irpina/elekloader) mod for the Elektron
Digitakt **mk1, OS 1.53 and 1.54**.

## [1.0c] - 2026-10-18

### Added

- **RING (TYPE 12)**: sine ring modulator, FREQ = carrier, RESO = depth.
- **PHASER (TYPE 13)**: four-stage first-order allpass phaser, FREQ = rate,
  RESO = LFO depth.
- **FLANGER (TYPE 14)**: LFO-modulated fractional delay with feedback, FREQ =
  rate, RESO = depth/feedback.
- Creative graphics: ringed planet (RING), vortex (PHASER), waves (FLANGER);
  ring-modulated, chirped and rectified-sine pictures in the graph box.

### Performance

- VOWEL/BANK: 3042 instructions / ~3455 cycles static, 5011/5017 / ~6176/6187
  swept.
- FOLD 451–547, CRUSH 406, RING 666, PHASER 2583, FLANGER 1794 instructions.
- FLANGER allocates 512 samples per voice (16 KB).

## [1.0b] - 2026-10-18

### Added

- **FOLD (TYPE 10)**: triangle wavefolder, FREQ = drive 1–8×, RESO = bias.
- **CRUSH (TYPE 11)**: sample-rate reduction + 1–16 bit quantisation.
- Creative FLTR-page graphics: mouth (VOWEL), robot (BANK), folded wave (FOLD),
  Pac-Man (CRUSH); transfer curves for FOLD/CRUSH.

### Fixed

- The biquad kernel's coefficient scaling: `mac.l ...,<<` is not a left shift
  in fractional mode, so all biquad coefficients were effectively halved and the
  filters mostly passed a scaled dry signal. b0/b2/n2 are now Q31, n1 stays Q30
  and is applied twice.

### Performance

- VOWEL/BANK: 3034 instructions / ~3444 cycles static; 5003/5009 / ~6174/6185
  swept.
- FOLD: 485–581 / ~590–820. CRUSH: 405 / ~508.

## [1.0a] - 2026-10-18

Initial standalone analogue fork.

### Added

- **VOWEL (TYPE 8)**: a four-formant vocal-tract filter. FREQ sweeps the
  SynVOW vowel path i-e-a-o-u; RESO sets the band width.
- **BANK (TYPE 9)**: a four-resonator filterbank at 250/500/1000/2000 Hz.
  FREQ shifts the bank about an octave; RESO sets the Q.
- The FLTR page's FREQ/RES response curve and TYPE glyph for both models.
- Filter-envelope modulation and stock TYPE fall-through.
- OS 1.54 port.

### Performance

- Static knobs reuse the previous block's coefficients and run the 32-frame
  kernel directly.
- Moving knobs build one four-sub-block coefficient ramp per band.
- Measured per voice per 32-frame block (MCF54418):
  VOWEL 3027 instructions / ~3430 cycles static, 4996 / ~6150 swept;
  BANK 3027 / ~3430 static, 5002 / ~6161 swept.

### Internals

- Four independent RBJ band-pass biquads in transposed direct form II, one
  eMAC accumulator per band (`biquad_dsp.s`); Q30 coefficients, Q27 samples.
- `biquad_tables.h` is generated for the 8 Q rows and 128 FREQ steps.
- `analog_tables.h` is generated from SynVOW's formant tables (F1-F4).
- Forked from DigiFilter 1.1b; the OB-1, COMB/TRASH and BP/BP2 paths are not
  part of this mod.
