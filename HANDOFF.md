# Filter+FX handoff — 1.1a

Worktree: `C:\Users\benan\Music\ELEKTRON\digifilter-analogue`  
Branch: `filter-fx`  
Repo: <https://github.com/DigiAlchemydsp/Filter-FX> (`master`, clean-root commit `3daf5a5`)

**Published:** `v1.1a` (VOWEL/BANK second page, FLANGER/PHASER fixes, both
elemods and `releases/Filter-FX-1.1a.zip`).  
**Current tree:** **1.1a** — committed and pushed to `filterfx/master`.

## Modes

| TYPE | mode | page 1 | page 2 |
|---|---|---|---|
| 8 | VOWEL | FREQ = vowel path i-e-a-o-u; RESO = width | C = **SIZE**, G = **F4** |
| 9 | BANK | FREQ = bank shift; RESO = Q | C = **SPRD**, G = **TILT** |
| 10 | FOLD | FREQ = drive; RESO = bias | stock |
| 11 | CRUSH | FREQ = hold rate; RESO = bits | stock |
| 12 | RING | FREQ = carrier; RESO = depth | stock |
| 13 | PHASER | FREQ = LFO rate; RESO = depth | stock |
| 14 | FLANGER | FREQ = LFO rate; RESO = depth/feedback | stock |

## 1.1a changes

### VOWEL second page
- **SIZE**: adds up to +1 octave to all formants, 0 = neutral.
  `off = a1 * 12 * 256 / 127` added to the 8.8 formant index.
- **F4**: scales the 3300 Hz singer's-formant gain from 1× to 2×, 0 = 1×.
  `g4 = mulsh(VOWEL_GAIN[3], (127 + a2) * 258, 15) << 3`.

### BANK second page
- **SPRD**: increases the spacing of the bank, up to +1 octave on the top band.
  `off_b = (a1 * 12 * 256 / 127) * b / 3`.
- **TILT**: flat at 0, dark to bright above.
  `gain_b = mulsh(BANK_GAIN[b], (127 + tilt) * 258, 15) << 3`, with
  `tilt = a2 * (2b - 3) / 3`.

Both aux values participate in the coefficient cache (`prev_a1/prev_a2`), so
changing a second-page knob rebuilds the biquad target and ramps normally.

### FLANGER / PHASER fixes
- **FLANGER output**: the delayed tap only fed the feedback line, never the
  output, so RESO 0 was dry and high RESO was an echo, not a flange. The output
  is now `(dry + delayed) >> 1`; feedback stays in the line and saturates.
- **FLANGER delay range**: the centre was 72 samples while the LFO swung
  `+-2 x RESO`, so RESO > 36 clamped the delay to one sample. Centre is now 128
  samples (2.7 ms), swing `+-RESO`, minimum two samples.
- **PHASER output**: the four allpasses overshoot on transients (up to ~1.2x
  full scale at some frequencies), so dry + wet wrapped the 32-bit sample. The
  output saturates at `+-2^27`, the same limit the biquad/comb kernels use.
- **FLANGER RAM**: the line is 256 entries of 16-bit (4 KB) instead of 512
  entries of 32-bit (16 KB). The 2..255-sample sweep is unchanged; `.bss` falls
  from 18360 to 6072 B.
- **Second-page dials**: the needle now sweeps clockwise from 9:00 (0) through
  12:00 to 7:00 (127). Both ports draw identically.

### Second-page plumbing
- Spare slots: `FS_AUX1 0x2f`, `FS_AUX2 0x30`.
- Layout kind 7 for VOWEL/BANK: `{39,0,14,42,40,41,15,43}`; stock otherwise.
- Descriptors 14/15 commandeered with group 6, slot 0x2f/0x30, range 0x7f00,
  step 1. Labels: `SIZE`/`F4` for VOWEL, `SPRD`/`TILT` for BANK.
- `digifilter_tick` (ev_tick) runs `digifilter_page2_sync` and `aux_persist`.
- `aux_persist` mirrors the spare values into the low bytes of Base/Width
  (slots 0x21/0x22), so they survive kit save/load; only VOWEL/BANK tracks are
  touched.
- `digifilter_draw` now accepts FLTR kind 6 or 7; on kind 7 it paints the two
  round dials at (85,41) and (85,15).

## Verification

- `tests/digiemu_filter_fx_page2.py` — **PASS**:
  - encoders C/G move slots 0x2f/0x30
  - kind-7 layout/descriptors match
  - stock TYPE restores the stock page
- ColdFire aux test: SIZE/F4 and SPRD/TILT change the DSP output.
- `tests/analog_smoke.py` — all seven modes bounded/non-silent; PHASER stays
  inside full scale on a full-scale input; FLANGER echoes at its 128-sample
  centre delay.
- `tests/digiemu_filter_fx_shots.py` — all seven FLTR curves and TYPE glyphs
  render on both 1.53 and 1.54; the 1.54 panels are pixel-identical to 1.53.
- Second FLTR page captured at values 0/64/127 on 1.53 and 1.54: the dials run
  9:00 → 2:00 → 7:00 clockwise, and both ports are pixel-identical.
- Build + `elekloader.lint` pass for OS 1.53 and 1.54.

Bench (`tests/analog_bench.py`, instructions / cycles per voice per block):

| mode | static | swept | vs stock |
|---|---|---|---|
| VOWEL | 3074 / ~3513 | 5082 / ~6371 | +28 % / +112 % |
| BANK | 3074 / ~3515 | 5376 / ~7009 | +28 % / +124 % |
| FOLD | 452–548 | same | −77…−81 % |
| CRUSH | 408 | same | −83 % |
| RING | 668 | same | −72 % |
| PHASER | 2681 | same | +12 % |
| FLANGER | 2019 | same | −16 % |
| stock | ~2400 | — | 1.00× |

Footprint (1.1a): `.run` **31492 B**, `.bss` **6072 B**; RAM **38948 /
131072** (1.53), **38980 / 262144** (1.54); 3 sites, 127 relocations,
`imports nothing`.

## 1.1a test artifacts

Local, gitignored `out/`:

| file | sha256 (first 16) |
|---|---|
| `out/filter-fx-1.1a.elemod` | `620b8a1a192aa798` |
| `out/filter-fx-1.1a-os1.54.elemod` | `6318b6d39cf8ba9c` |
| `out/filter-fx-1.1a-1.53-test.syx` | `51d83bbfb82443c0` |
| `out/filter-fx-1.1a-os1.54-test.syx` | `5f0f461b81ba0688` |

Release package: `releases/Filter-FX-1.1a.zip` (`c96a1f1e5c3897dd`), with the two
elemods under `releases/elemods/`. The 1.53 test firmware folder in digiemu is
`dt1-2.0t-90bdc6a2`; that folder is derived from the patched syx and is not
committed.

## Build / test

```powershell
$env:PATH = "C:\SysGCC\m68k-elf\bin;" + $env:PATH
$env:ELEKLOADER_CROSS = "m68k-elf-"
$env:PYTHONPATH = "C:\Users\benan\Music\ELEKTRON\elekloader"
$stock = "C:\Users\benan\Music\ELEKTRON\digiemu-main\portable\firmware\dt1-1.53-9bdd44bb\Digitakt_OS1.53.syx"
$core  = "C:\Users\benan\Music\ELEKTRON\elekloader\mods\core\out\core-2.1.elemod"

python -m elekloader.sdk.build . --stock $stock
python -m elekloader.lint out/filter-fx-1.1a.elemod --stock $stock --with $core
python -m elekloader.patch --stock $stock --mod $core --mod out/filter-fx-1.1a.elemod `
    --out out/filter-fx-1.1a-1.53-test.syx --version 2.0t
```

Bench/smoke:

```powershell
$env:PYTHONPATH = "C:\Users\benan\Music\ELEKTRON\digiemu-main"
python tests/analog_bench.py
python tests/analog_smoke.py
python tests/digiemu_filter_fx_page2.py --digiemu <digiemu> --fw dt1-2.0t-90bdc6a2
```

OS 1.54 uses the 1.54 stock and the 1.54-capable elekloader/core 4.0.

**Build one port at a time.** The SDK reuses `out/filter-fx.work`, and its
objects are not keyed by the port's `defsym`/`cflags`. Building 1.53 and 1.54
without deleting that folder leaves the second elemod with the first port's
`#ifdef OS154` addresses (the 1.54 UI then calls 1.53's FILLRECT and displays
neither the curves nor the glyphs). `Remove-Item -Recurse out/filter-fx.work`
between the two builds, then lint each elemod against its own stock and core.

## Files touched in 1.1a

- `filter.c` — FS_AUX1/2, `PARAM_SLOT`, aux-aware `build_target`/`run_mode`,
  cache keys, `aux_persist`, `digifilter_tick`; FLANGER dry+delay output, delay
  range and 16-bit 256-entry line; PHASER output saturation.
- `filter_ui.c` — second-page descriptors/layout/dials, page 6/7 view handling.
- `mod.json` — version 1.1a, ev_tick subscription, description.
- `tests/analog_smoke.py` — full-scale PHASER and FLANGER delay regressions.
- `tests/digiemu_filter_fx_page2.py` — new page-2 regression test.
- `README.md`, `CHANGELOG.md`, this handoff.

## Trade-offs / limitations

- SIZE and SPRD are upward-only (0 = neutral, max = +1 octave). This keeps the
  spare-slot default (0) sounding like 1.0c.
- F4 is level-only (1×–2×), not a frequency control.
- TILT is a simple per-band gain tilt, not a shelf filter.
- The second page is only customized while VOWEL/BANK is the active type.
- Page-2 values persist through the Base/Width low-byte mirror; the high bytes
  remain the stock Base/Width values.

## Open items

1. Optional: capture page-2 screenshots for VOWEL/BANK and add them to the
   README.
2. Hardware listening test of the second-page controls and the FLANGER/PHASER
   fixes.

## Licensing

GPL-2.0-or-later. `COPYING` has the full GPL-2.0 text; `THIRD_PARTY.md` covers
DigiFilter, SynVOW (author's own work, used with permission), ER-301, Freescale
DSPLIB, Elektron and build tools. The Digitakt screenshots are Elektron UI and
are not GPL-licensed. No Elektron firmware is included in the repository.
