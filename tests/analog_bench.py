#!/usr/bin/env python3
"""Count the analogue mod's per-voice instructions (and cycles) per 32-frame block.

Builds filter.c + biquad_dsp.s + tests/df_bench.c with the SDK flags, links at
0x10000 and runs digifilter_filt() in Unicorn for VOWEL and BANK.

    python <Filter+FX>/tests/analog_bench.py
"""
import os
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace

from unicorn import UC_ARCH_M68K, UC_HOOK_CODE, UC_MODE_BIG_ENDIAN, Uc
from unicorn.m68k_const import UC_CPU_M68K_CFV4E, UC_M68K_REG_A7
try:
    from emu import cftiming
except ImportError:
    cftiming = None

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
    n = [0]
    uc.hook_add(UC_HOOK_CODE, lambda u, a, s, d: n.__setitem__(0, n[0] + 1))
    clock = None
    if cftiming is not None:
        clock = cftiming.CycleClock(SimpleNamespace(uc=uc, raise_vector=lambda *a, **k: None))

    def block(type_, fi, qi, step=False):
        uc.mem_write(sym['df_params'], bytes([type_]) + b'\x00' * 0xff)
        uc.mem_write(sym['df_params'] + 2, struct.pack('>H', fi << 8))
        uc.mem_write(sym['df_params'] + 6, struct.pack('>H', 0x4000))
        uc.mem_write(0x80001502 + 0x36, struct.pack('>H', qi << 8))
        buf = b''.join(struct.pack('>i', (1 << 22) if (i // 2) % 2 else -(1 << 22))
                       for i in range(64))
        for warm in range(2):
            if step and warm == 1:
                uc.mem_write(sym['df_params'] + 2, struct.pack('>H', ((fi + 8) & 0x7f) << 8))
            uc.mem_write(sym['df_buf'], buf)
            uc.mem_write(STACK - 4, RET.to_bytes(4, 'big'))
            uc.reg_write(UC_M68K_REG_A7, STACK - 4)
            n[0] = 0
            if clock is not None and warm == 1:
                clock.cycles = clock.instructions = 0
                clock.stall_cycles = clock.flow_cycles = 0
            uc.emu_start(sym['df_filt_run'], RET, count=2000000)
        return n[0], (clock.cycles if clock is not None else 0)

    print('%-6s %-6s %-4s %s' % ('TYPE', 'mode', 'RESO', 'insn (cycles) static / swept'))
    for type_, name in ((8, 'VOWEL'), (9, 'BANK'), (10, 'FOLD'), (11, 'CRUSH'), (12, 'RING'), (13, 'PHASER'), (14, 'FLANGER')):
        for qi in (0, 64, 127):
            si, sc = block(type_, 64, qi)
            wi, wc = block(type_, 64, qi, step=True)
            print('%-6d %-6s %-4d %d (%d) / %d (%d)' % (type_, name, qi, si, sc, wi, wc))


if __name__ == '__main__':
    sys.exit(main())
