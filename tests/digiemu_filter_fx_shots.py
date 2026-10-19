#!/usr/bin/env python3
"""Capture the FLTR page and TYPE-box icon for every Filter+FX mode.

Boots the patched firmware in digiemu, opens the FLTR page, forces each TYPE,
requests a redraw, and saves a 4x panel PNG plus a cropped TYPE-box icon.

    python tests/digiemu_filter_fx_shots.py --digiemu <checkout> --fw <folder>
"""
import argparse
import os
import struct
import sys
import types

from PIL import Image

ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
ap.add_argument("--digiemu", required=True)
ap.add_argument("--fw", required=True)
ap.add_argument("--steps", type=int, default=560)
ap.add_argument("--out", default=None)
a = ap.parse_args()

FW = os.path.join(a.digiemu, "portable", "firmware", a.fw)
OUT = a.out or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "docs", "img", "filter-fx")
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, a.digiemu)
syxname = [f for f in os.listdir(FW) if f.endswith(".syx")][0]
os.environ.update({
    "DT2_SYX": os.path.join(FW, syxname), "DT2_SECTIONS": FW + "/sections",
    "DT2_SNAPSHOTS": FW + "/snapshots", "DT2_PLUSDRIVE": FW + "/plusdrive.img",
    "DT2_MAIN_IMG": FW + "/sections/section_3_MAIN_OS.bin",
    "DT2_DEVICES": FW + "/devices" if os.path.isdir(FW + "/devices") else os.path.join(a.digiemu, "devices"),
    "DIGIKIT_PIT3_PROBE": "1"})
os.chdir(FW)
_tk = types.ModuleType("tkinter")
_tk.Frame = type("Frame", (), {})
_tk.Tk = type("Tk", (), {})
sys.modules["tkinter"] = _tk
for _n in ("ttk", "messagebox", "filedialog", "font"):
    sys.modules["tkinter." + _n] = types.ModuleType("tkinter." + _n)
from unicorn import UC_HOOK_CODE  # noqa: E402
from unicorn.m68k_const import UC_M68K_REG_A7  # noqa: E402
import emu.gui as G  # noqa: E402

SNAP = [os.path.join(dp, f) for dp, _, fs in os.walk(FW + "/snapshots") for f in fs if f == "gui.snap"][0]
UI_KIT = 0x4199DC44
ACTIVE = 0x4197B6B4
SITE = 0x4000A7D6             # core's ev_draw site: sp = ctrl, sp+4 = bmp
TYPES = ((8, "vowel"), (9, "bank"), (10, "fold"), (11, "crush"),
         (12, "ring"), (13, "phaser"), (14, "flanger"))


def rd(u, addr, n):
    try:
        return bytes(u.mem_read(addr, n))
    except Exception:
        return b""


def u32(u, addr):
    b = rd(u, addr, 4)
    return struct.unpack(">I", b)[0] if b else 0


def kit_word_addr(u, slot):
    kit = u32(u, UI_KIT)
    t = u32(u, ACTIVE)
    if not kit or t > 7:
        return 0
    return kit + 0x20 + t * 0xA2 + 0x14 + 2 * slot


def force(u, ty):
    a0 = kit_word_addr(u, 0x19)
    if not a0:
        return -1
    u.mem_write(a0, struct.pack(">H", ty << 8))          # TYPE
    u.mem_write(a0 + 2, struct.pack(">H", 64 << 8))       # FREQ 64
    u.mem_write(a0 + 4, struct.pack(">H", 64 << 8))       # RESO 64
    return struct.unpack(">H", rd(u, a0, 2))[0] >> 8


state = {"n": 0, "ctrl": 0, "shots": {}}
spin0 = G.spin
PLAN = {120: ("press", 21), 170: ("release", 21)}
STEP = 24
BASE = 240
FORCES = {BASE + i * STEP: t for i, (t, _) in enumerate(TYPES)}
CAPS = {BASE + i * STEP + 10: t for i, (t, _) in enumerate(TYPES)}


def ctrl_hook(u, address, size, user):
    if not state["ctrl"]:
        state["ctrl"] = u32(u, u.reg_read(UC_M68K_REG_A7))


def spin(m, pc, *args, **kw):
    uc = m.uc
    if state["n"] == 1:
        uc.hook_add(UC_HOOK_CODE, ctrl_hook, begin=SITE, end=SITE)
        uc.ctl_flush_tb()
    act = PLAN.get(state["n"])
    if act:
        E.inbox.append((act[0], act[1], 0))
    if state["ctrl"]:
        uc.mem_write(state["ctrl"] + 0x20, b"\x01")
    ty = FORCES.get(state["n"])
    if ty is not None:
        print("force TYPE %d" % force(uc, ty))
    r = spin0(m, pc, *args, **kw)
    cap = CAPS.get(state["n"])
    if cap is not None and getattr(E, "fb", None):
        state["shots"][cap] = bytes(E.fb)
    state["n"] += 1
    if state["n"] >= a.steps:
        E.stop_flag.set()
    return r


G.spin = spin
E = G.Emulator(SNAP, syx=os.environ["DT2_SYX"], realtime=False, audio=True)
E.run()
print("error:", E.error, "steps:", state["n"], "shots:", sorted(state["shots"]))


def panel_image(fb):
    img = Image.new("L", (128, 64))
    img.putdata([255 if fb[y * 128 + x] else 0
                 for y in range(64) for x in range(128)])
    return img


for ty, name in TYPES:
    fb = state["shots"].get(ty)
    if fb is None:
        print("FAIL: no shot for TYPE %d" % ty)
        continue
    panel = panel_image(fb)
    panel.resize((512, 256), Image.NEAREST).save(os.path.join(OUT, name + "-panel.png"))
    # TYPE box: x 78..92, firmware rows 8..22 -> top-origin rows 39..57
    icon = panel.crop((79, 41, 92, 54))
    icon.resize((13 * 14, 13 * 14), Image.NEAREST).save(os.path.join(OUT, name + "-icon.png"))
    print("saved %s-panel.png and %s-icon.png" % (name, name))
