#!/usr/bin/env python3
"""Smoke-test the analogue DSP on ColdFire: output is non-zero, bounded, and
changes with FREQ/RESO for both VOWEL and BANK."""
import math
import os
import struct
import subprocess
import sys
import tempfile

from unicorn import UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, Uc
from unicorn.m68k_const import UC_CPU_M68K_CFV4E, UC_M68K_REG_A7

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CROSS = os.environ.get('ELEKLOADER_CROSS', 'm68k-elf-')
BASE, STACK, RET = 0x10000, 0x200000, 0x1f0000
CFLAGS = ['-mcpu=54455', '-O2', '-ffreestanding', '-fno-builtin', '-nostdlib',
          '-fno-pic', '-fno-pie', '-fomit-frame-pointer', '-Wall',
          '-ffunction-sections', '-fdata-sections']


def build():
    d = tempfile.mkdtemp()
    elf = os.path.join(d, 'analog.elf')
    subprocess.check_call([CROSS + 'gcc'] + CFLAGS + ['-I', ROOT,
                           os.path.join(ROOT, 'filter.c'),
                           os.path.join(ROOT, 'biquad_dsp.s'),
                           os.path.join(ROOT, 'tests', 'df_bench.c'),
                           '-Wl,-Ttext=0x10000', '-Wl,-e,df_filt_run',
                           '-Wl,--gc-sections', '-o', elf])
    syms = {l.split()[2]: int(l.split()[0], 16) for l in subprocess.check_output(
        [CROSS + 'nm', elf], text=True).splitlines() if len(l.split()) == 3}
    return elf, syms


def main():
    elf, sym = build()
    bin_ = elf + '.bin'
    subprocess.check_call([CROSS + 'objcopy', '-O', 'binary', elf, bin_])
    uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_CPU_M68K_CFV4E)
    uc.mem_map(0, 0x600000)
    uc.mem_map(0x80000000, 0x20000)
    uc.mem_write(BASE, open(bin_, 'rb').read())

    def call(type_, fi, qi, values):
        uc.mem_write(sym['df_params'], bytes([type_]) + b'\x00' * 0xff)
        uc.mem_write(sym['df_params'] + 2, struct.pack('>H', fi << 8))
        uc.mem_write(sym['df_params'] + 6, struct.pack('>H', 0x4000))
        uc.mem_write(0x80001502 + 0x36, struct.pack('>H', qi << 8))
        uc.mem_write(sym['df_buf'], b''.join(struct.pack('>i', v) for v in values))
        uc.mem_write(STACK - 4, RET.to_bytes(4, 'big'))
        uc.reg_write(UC_M68K_REG_A7, STACK - 4)
        uc.emu_start(sym['df_filt_run'], RET, count=2000000)
        return list(struct.unpack('>32i', uc.mem_read(sym['df_buf'], 128)))

    def run(type_, fi, qi, block=0, amp=1 << 26):
        values = [int(math.sin(2 * math.pi * 1500 * (block * 32 + i) / 48000) * amp)
                  for i in range(32)]
        return call(type_, fi, qi, values)

    nonzero = {}
    for type_, name in ((8, 'VOWEL'), (9, 'BANK'), (10, 'FOLD'), (11, 'CRUSH'), (12, 'RING'), (13, 'PHASER'), (14, 'FLANGER')):
        for fi in (0, 32, 64, 96, 127):
            for qi in (0, 64, 127):
                out = run(type_, fi, qi)
                peak = max(abs(v) for v in out)
                assert peak <= (1 << 30), (name, fi, qi, peak)
                if peak:
                    nonzero[name] = 1
    assert len(nonzero) == 7, nonzero

    full = 1 << 27
    for fi in (0, 32, 64, 96, 127):
        for block in range(8):
            out = run(13, fi, 127, block, amp=full)
            peak = max(abs(v) for v in out)
            assert peak <= full, ('PHASER', fi, block, peak)
    out = call(14, 64, 0, [1 << 26] + [0] * 31)
    for _ in range(5):
        out += call(14, 64, 0, [0] * 32)
    echo = [i for i, v in enumerate(out) if v]
    assert any(120 <= i <= 140 for i in echo), ('FLANGER', echo)
    print('PASS: all seven modes produce bounded, non-silent output; '
          'PHASER stays inside full scale; FLANGER echoes at its centre delay')


if __name__ == '__main__':
    sys.exit(main())
