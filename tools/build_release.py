#!/usr/bin/env python3
"""Build Filter+FX 1.2 for Digitakt 1.54 and Digitone 1.44.

Builds one elemod per machine, lints each against its core, patch-checks the
stock image, stages the elemods under releases/elemods/ and writes the release
zip. The Digitakt mod is the root manifest; the Digitone port is filter-fx-dn/.

    python tools/build_release.py \
        --elekloader <elekloader checkout> \
        --stock-dt <Digitakt_OS1.54.syx> \
        --stock-dn <Digitone_OS1.44.syx>
"""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = '1.2'
SYX_VERSION = '1.2a'
DT_MOD_DIR = '.'
DN_MOD_DIR = 'filter-fx-dn'
DT_BUILD = f'filter-fx-{VERSION}-os1.54.elemod'
DN_BUILD = f'filter-fx-dn-{VERSION}.elemod'
DT_STAGE = f'filter-fx-{VERSION}-dt.elemod'
DN_STAGE = f'filter-fx-dn-{VERSION}.elemod'
DT_CORE = 'core-4.0-os1.54.elemod'
DN_CORE = 'core-dn1-4.0-os1.44.elemod'

ROOT_FILES = [
    'README.md', 'LICENSE', 'COPYING', 'THIRD_PARTY.md', 'CHANGELOG.md',
    'mod.json', 'filter.c', 'filter_ui.c', 'filter_glue.s', 'biquad_dsp.s',
    'biquad_tables.h', 'analog_tables.h', 'mod_tables.h', 'filter_tables.h',
    'fx_dsp.c', 'fx_dsp.h', 'HANDOFF.md',
]


def arg_or_env(parser, args, name, env, help_text):
    value = getattr(args, name) or os.environ.get(env)
    if not value:
        parser.error(f'--{name.replace("_", "-")} is required (or set ${env})')
    return Path(value).expanduser().resolve()


def find_core(elekloader, name, explicit):
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.is_file():
            raise SystemExit(f'core not found: {path}')
        return path
    candidates = [
        elekloader / 'mods' / 'core' / 'out' / name,
        elekloader / 'mods' / 'core-dn1' / 'out' / name,
        elekloader / name,
        elekloader.parent / name,
        elekloader.parent.parent / name,
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise SystemExit(f'core not found: {name}\n'
                     f'looked in: {", ".join(str(p) for p in candidates)}\n'
                     f'pass --core-dt/--core-dn explicitly')


def run(cmd, env):
    print('+', ' '.join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], cwd=ROOT, env=env, check=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def build_one(args, env, mod, stock, core, elemod, syx, stage_name):
    run([sys.executable, '-m', 'elekloader.sdk.build', mod,
         '--stock', stock, '--out', args.out], env)
    if not elemod.is_file():
        raise SystemExit(f'expected build output not found: {elemod}')
    run([sys.executable, '-m', 'elekloader.lint', elemod,
         '--stock', stock, '--with', core], env)
    run([sys.executable, '-m', 'elekloader.patch', '--stock', stock,
         '--mod', core, '--mod', elemod, '--out', syx,
         '--version', SYX_VERSION, '--check'], env)
    if not args.no_syx:
        run([sys.executable, '-m', 'elekloader.patch', '--stock', stock,
             '--mod', core, '--mod', elemod, '--out', syx,
             '--version', SYX_VERSION], env)
    dest_dir = ROOT / 'releases' / 'elemods'
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / stage_name
    shutil.copy2(elemod, dest)
    return dest


def make_zip(elemods):
    dest = ROOT / 'releases' / f'Filter+FX-{VERSION}.zip'
    with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as z:
        for name in ROOT_FILES:
            path = ROOT / name
            if path.is_file():
                z.write(path, path.relative_to(ROOT).as_posix())
        for name in ('filter-fx-dn', 'docs', 'tests', 'tools'):
            path = ROOT / name
            if path.is_dir():
                for item in sorted(path.rglob('*')):
                    if item.is_file() and '__pycache__' not in item.parts:
                        z.write(item, item.relative_to(ROOT).as_posix())
        for elemod in elemods:
            z.write(elemod, f'elemods/{elemod.name}')
    return dest


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--elekloader', help='elekloader checkout; or $ELEKLOADER_ROOT')
    parser.add_argument('--stock-dt', help='Digitakt_OS1.54.syx; or $DT_STOCK')
    parser.add_argument('--stock-dn', help='Digitone_OS1.44.syx; or $DN_STOCK')
    parser.add_argument('--core-dt', help=f'{DT_CORE} (default: next to the checkout)')
    parser.add_argument('--core-dn', help=f'{DN_CORE} (default: next to the checkout)')
    parser.add_argument('--toolchain-bin', help='directory with m68k-elf-gcc')
    parser.add_argument('--out', default=str(ROOT / 'out'))
    parser.add_argument('--no-syx', action='store_true')
    parser.add_argument('--no-zip', action='store_true')
    args = parser.parse_args()

    elekloader = arg_or_env(parser, args, 'elekloader', 'ELEKLOADER_ROOT', 'elekloader checkout')
    stock_dt = arg_or_env(parser, args, 'stock_dt', 'DT_STOCK', 'Digitakt 1.54 stock')
    stock_dn = arg_or_env(parser, args, 'stock_dn', 'DN_STOCK', 'Digitone 1.44 stock')
    args.out = Path(args.out).expanduser().resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    core_dt = find_core(elekloader, DT_CORE, args.core_dt)
    core_dn = find_core(elekloader, DN_CORE, args.core_dn)

    env = os.environ.copy()
    pythonpath = str(elekloader)
    if env.get('PYTHONPATH'):
        pythonpath += os.pathsep + env['PYTHONPATH']
    env['PYTHONPATH'] = pythonpath
    env.setdefault('ELEKLOADER_CROSS', 'm68k-elf-')
    if args.toolchain_bin:
        env['PATH'] = str(Path(args.toolchain_bin).expanduser().resolve()) + os.pathsep + env['PATH']

    print(f'stock DT: {stock_dt}')
    print(f'core  DT: {core_dt}')
    print(f'stock DN: {stock_dn}')
    print(f'core  DN: {core_dn}')

    dt = build_one(args, env, DT_MOD_DIR, stock_dt, core_dt,
                   args.out / DT_BUILD, args.out / 'filter-fx-1.2-dt.syx', DT_STAGE)
    dn = build_one(args, env, DN_MOD_DIR, stock_dn, core_dn,
                   args.out / DN_BUILD, args.out / 'filter-fx-dn-1.2.syx', DN_STAGE)
    for path in (dt, dn):
        print(f'staged {path.relative_to(ROOT)}  sha256 {sha256(path)}')
    if not args.no_zip:
        path = make_zip([dt, dn])
        print(f'wrote {path.relative_to(ROOT)}  sha256 {sha256(path)}')
    print('OK: one elemod per machine, latest OS only')


if __name__ == '__main__':
    sys.exit(main())
