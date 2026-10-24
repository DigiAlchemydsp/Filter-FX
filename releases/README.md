# releases

Prebuilt **Filter+FX 1.2** for the **Digitakt mk1 (OS 1.54)** and **Digitone
mk1 / Keys (OS 1.44)**. One elemod per machine.

| file | |
|---|---|
| `elemods/filter-fx-1.2-dt.elemod` | the Digitakt mod, **OS 1.54** |
| `elemods/filter-fx-dn-1.2.elemod` | the Digitone mod, **OS 1.44** |
| `Filter+FX-1.2.zip` | both elemods + sources + docs + README + screenshots + licences |
| older zips/elemods | previous releases, kept for reference |

Each elemod needs its matching core and stock OS:

| machine | elemod | core | stock |
|---|---|---|---|
| Digitakt mk1 | `filter-fx-1.2-dt.elemod` | `core-4.0-os1.54.elemod` | `Digitakt_OS1.54.syx` |
| Digitone mk1/Keys | `filter-fx-dn-1.2.elemod` | `core-dn1-4.0-os1.44.elemod` | `Digitone_OS1.44.syx` |

Install:

```sh
python -m elekloader.patch --stock Digitakt_OS1.54.syx \
    --mod core-4.0-os1.54.elemod \
    --mod releases/elemods/filter-fx-1.2-dt.elemod \
    --out Digitakt_OS1.54-filter-fx.syx --version 1.2a
```

Then flash the `.syx` with Elektron Transfer. Repeat with the Digitone files.

New in 1.2: the Digitone mk1/Keys port (`filter-fx-dn/`), bringing the seven
Filter+FX modes to TYPE 4..10 with VOWEL/BANK AUX1/AUX2 on page 2, plus the
Digitakt 1.54 rebuild. Both packages contain one elemod per machine.

No Elektron firmware is included. Filter+FX is GPL-2.0-or-later; see `LICENSE`,
`COPYING` and `THIRD_PARTY.md`.
