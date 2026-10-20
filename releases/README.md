# releases

Prebuilt **Filter+FX 1.1a** for the **Digitakt mk1, OS 1.53 and OS 1.54**.

| file | |
|---|---|
| `elemods/filter-fx-1.1a.elemod` | the mod, **OS 1.53** |
| `elemods/filter-fx-1.1a-os1.54.elemod` | the mod, **OS 1.54** |
| `Filter-FX-1.1a.zip` | both elemods + sources + docs + README + screenshots + licences |

Each elemod needs `core` from
[elekloader](https://github.com/irpina/elekloader) and the matching stock OS
(`Digitakt_OS1.53.syx` or `Digitakt_OS1.54.syx`). OS 1.53 uses core 2.1; OS 1.54
uses core 4.0.

```sh
python -m elekloader.patch --stock Digitakt_OS1.53.syx \
    --mod core-2.1.elemod --mod releases/elemods/filter-fx-1.1a.elemod \
    --out Digitakt_OS1.53-filter-fx.syx --version 2.0t
```

Then flash the `.syx` with Elektron Transfer. No Elektron firmware is included.
Filter+FX is GPL-2.0-or-later; see `LICENSE`, `COPYING` and `THIRD_PARTY.md`.
