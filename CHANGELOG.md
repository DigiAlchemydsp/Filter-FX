# Changelog

All notable changes to Filter+FX. Format-2
[elekloader](https://github.com/irpina/elekloader) mods for the Elektron
**Digitakt mk1** and **Digitone mk1 / Keys**.

## [1.2] - 2026-10-22

### Added

- **Digitone mk1/Keys port** (`filter-fx-dn/`): VOWEL/BANK/FOLD/CRUSH/RING/
  PHASER/FLANGER as TYPE 4..10, per-voice FREQ/RESO, VOWEL/BANK AUX1/AUX2 on
  page-2 C/G (params 182/183), response/transfer graphs and TYPE icons.
- Release package now carries **one elemod per machine**:
  `filter-fx-1.2-dt.elemod` (Digitakt 1.54) and `filter-fx-dn-1.2.elemod`
  (Digitone 1.44).

### Changed

- Digitakt release build targets **OS 1.54** with core 4.0.
- Shared DSP for the Digitone lives in `fx_dsp.c` + `biquad_dsp.s`; the DT
  mod keeps its existing sources.

## [1.1a] - 2026-10-20

### Added

- **VOWEL second-page controls**: **SIZE** (F1-F4 up to +1 octave) and **F4**
  (3300 Hz band level, 1x-2x).
- **BANK second-page controls**: **SPRD** (spread the bank spacing up to +1
  octave on the top band) and **TILT** (dark to bright).
- Second-page descriptors and round dials, plus Base/Width low-byte mirroring
  for kit persistence.
- Other Filter+FX modes leave the second page stock.

### Fixed

- **FLANGER**: the delayed tap fed the feedback line but never the output, so
  RESO 0 was pure dry and higher settings were a resonant echo rather than a
  flange. The output is now the normal dry + delayed mix with feedback in the
  line.
- **FLANGER**: the delay centre (72 samples) was smaller than the LFO swing
  (+-2 x RESO), so RESO above 36 clamped the delay to one sample and the sweep
  collapsed. The centre is now 128 samples (2.7 ms), the swing +-RESO, and the
  minimum two samples.
- **PHASER**: four cascaded allpasses overshoot on transients (up to ~1.2x full
  scale at some frequencies), so the dry + wet sum wrapped/clipped the 32-bit
  sample. The output now saturates at +-2^27 like the biquad and comb kernels.
- **OS 1.54 UI**: the 1.54 elemod had been built from the shared work folder
  without the `OS154` defines, so it called the 1.53 FILLRECT/UI addresses and
  drew neither the response curves nor the TYPE glyphs. The port is now built
  from a clean work folder and its panels match 1.53 pixel for pixel.
- **Second-page dials**: the needle swept counter-clockwise and started at
  ~11:00. It now runs clockwise from 9:00 (value 0) through 12:00 to 7:00
  (value 127), a 300-degree sweep.

### Changed

- **FLANGER RAM**: the delay line is now 256 entries of 16-bit (4 KB) instead of
  512 entries of 32-bit (16 KB), keeping the same 2..255-sample sweep. The
  mod's `.bss` drops from 18360 to 6072 bytes; total RAM with core 2.1 drops
  from 51232 to 38952 bytes. The 16-bit line adds ~-90 dBFS quantisation noise.

### Performance

- VOWEL: 3074 instructions / ~3513 cycles static; 5082 / ~6371 swept.
- BANK: 3074 / ~3515 static; 5376 / ~7009 swept.
- PHASER: 2681 / ~3740 static and swept (was 2585 / ~3708 before the output
  saturation).
- FLANGER: 2019 / ~2371 static and swept (was 1796 / ~2178; the 16-bit line
  adds load/sign-extend and scale conversion).
- The other modes are unchanged.

### Verification

- `tests/digiemu_filter_fx_page2.py` PASS: C/G map to slots 0x2f/0x30, layout
  `{39,0,14,42,40,41,15,43}`, descriptors 14/15 are filter descriptors, and a
  stock TYPE restores the stock page.
- ColdFire aux test: SIZE/F4 and SPRD/TILT all change the DSP output.
- `tests/analog_smoke.py` also checks that PHASER stays inside full scale on a
  full-scale input and that FLANGER's first echo lands at its 128-sample centre.
- Build + lint pass for OS 1.53 and 1.54.

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
