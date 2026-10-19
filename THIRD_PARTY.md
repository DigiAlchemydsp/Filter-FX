# Third-party notices

Filter+FX is a derivative of **DigiFilter** and is distributed under
**GPL-2.0-or-later**. The main licence text is in `LICENSE`.

## DigiFilter

The SVF/biquad kernels, the elekloader glue, the filter tables and the
reverse-engineering notes are inherited from
[DigiFilter](https://github.com/DigiAlchemydsp/DigiFilter), copyright the
DigiFilter authors, GPL-2.0-or-later. Filter+FX keeps the same licence.

## SynVOW formant model

The VOWEL mode's F1–F4 reference values, vowel path and log-domain blending are
adapted from **SynVOW** (`FormantEngine.cpp` / `FormantEngine.h`,
`Syn-K7-VOW-SOURCE-main`), which credits the
[ER-301 MouthTowel](https://github.com/nickb808-dev/er301-MouthTowel) as the
origin of the formant model. Only numeric formant data and the model idea are
used here; the SynVOW source itself is not included.

SynVOW is the author's own work and is reused here with permission under the
project's GPL-2.0-or-later licence. Its formant table in turn credits the
ER-301 MouthTowel; only the numeric formant data and model idea are used here.

## Freescale DSPLIB

The ColdFire eMAC patterns (four accumulators, `mac.l`, the `<<` caveat) were
learned from Freescale's *Digital Signal Processing Libraries Using the ColdFire
eMAC and MAC* manual. No DSPLIB source or binary is included.

## Elektron / Digitakt

No Elektron firmware is included. The `.syx` files are generated locally by
`elekloader` by patching a user-supplied stock image; they are not part of the
repository.

The screenshots under `docs/img/filter-fx/` show the Digitakt's FLTR page for
documentation. The Digitakt UI artwork, fonts and the Elektron/Digitakt names
are the property of Elektron Music Machines MAV AB and are **not** covered by
this project's GPL licence.

## Build/test dependencies

`elekloader`, `digiemu`, Unicorn and Pillow are used as external tools and are
not vendored. Their own licences apply to those tools.
