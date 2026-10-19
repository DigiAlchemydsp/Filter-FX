/* Filter+FX: the FLTR page's FREQ/RES response curve for VOWEL/BANK.
 *
 * Subscribes to core's ev_draw; after the frame (stock curve included) has been
 * drawn, paints ours over the graph when the FLTR page is up and the active
 * track uses one of our TYPEs. No second page and no commandeered knobs: the
 * two models use only FREQ and RESO.
 */
#ifdef OS154
#define F_400c19a6 0x400c1bce
#define F_4197b6b4 0x4197c6b4
#define F_4199dc44 0x4199ec44
#else
#define F_400c19a6 0x400c19a6
#define F_4197b6b4 0x4197b6b4
#define F_4199dc44 0x4199dc44
#endif

typedef int int32;
typedef unsigned int uint32;

#include "filter_tables.h"
#include "analog_tables.h"
#include "mod_tables.h"

typedef void (*fillrect_t)(void *bmp, int x0, int y0, int x1, int y1, int colour);
#define FILLRECT ((fillrect_t)F_400c19a6)

#define VIEW_KINDS(view) (*(int32 **)((char *)(view) + 124))
#define VIEW_KINDS_END(view) (*(int32 **)((char *)(view) + 128))
#define VIEW_INDEX(view) (*(int32 *)((char *)(view) + 144))

#define CTRL_SENTINEL(ctrl) ((char *)(ctrl) + 0x14)
#define CTRL_HEAD(ctrl) (*(char **)((char *)(ctrl) + 0x1c))
#define NODE_VIEW(node) (*(void **)((char *)(node) + 8))
#define NODE_NEXT(node) (*(char **)(node))

#define UI_KIT (*(unsigned char *volatile *)F_4199dc44)
#define ACTIVE_TRACK (*(int *volatile *)F_4197b6b4)
#define FSLOT(kit, t, s) ((int)(*(unsigned short *)((kit) + 0x20 + (t) * 0xa2 + 0x14 + 2 * (s))))
#define FS_TYPE 0x19
#define FS_FREQ 0x1a
#define FS_RESO 0x1b

#define FLTR_KIND 6
#define FM_FIRST_TYPE 8
#define FM_FOLD 10
#define FM_CRUSH 11
#define FM_RING 12
#define FM_PHASER 13
#define FM_FLANGER 14
#define FM_LAST 14

#define GX0 20
#define GX1 71
#define GY0 7
#define GY1 23

#define TBX0 78
#define TBX1 92
#define TBY0 8
#define TBY1 22

static int32 curve[128];
static int curve_transfer;              /* FOLD/CRUSH draw a transfer curve, not a response */

static int clampi(int v, int lo, int hi)
{
    return v < lo ? lo : v > hi ? hi : v;
}

static int32 mulsh(int32 a, int32 b, int sh)
{
    uint32 ua = a < 0 ? -(uint32)a : (uint32)a, ub = b < 0 ? -(uint32)b : (uint32)b;
    uint32 al = ua & 0xffff, ah = ua >> 16, bl = ub & 0xffff, bh = ub >> 16;
    uint32 ll = al * bl, lh = al * bh, hl = ah * bl, hh = ah * bh;
    uint32 mid = (ll >> 16) + (lh & 0xffff) + (hl & 0xffff);
    uint32 lo = (ll & 0xffff) | (mid << 16);
    uint32 hi = hh + (lh >> 16) + (hl >> 16) + (mid >> 16);
    if ((a < 0) != (b < 0)) {
        lo = ~lo + 1;
        hi = ~hi + (lo == 0);
    }
    return (int32)((hi << (32 - sh)) | (lo >> sh));
}

static uint32 udivq16(uint32 x, uint32 y)     /* floor(x * 65536 / y) */
{
    uint32 rem = x, q = 0;
    int i;
    for (i = 0; i < 16; i++) {
        rem <<= 1;
        q <<= 1;
        if (rem >= y) {
            rem -= y;
            q |= 1;
        }
    }
    return q;
}

static const unsigned short LOG2Q8[256] = {
    0, 3, 6, 8, 11, 14, 16, 19, 22, 24, 27, 29, 32, 34, 37, 39,
    42, 45, 47, 50, 52, 54, 57, 59, 62, 64, 67, 69, 71, 74, 76, 78,
    81, 83, 85, 88, 90, 92, 94, 97, 99, 101, 103, 105, 108, 110, 112, 114,
    116, 119, 121, 123, 125, 127, 129, 131, 133, 135, 138, 140, 142, 144, 146, 148,
    150, 152, 154, 156, 158, 160, 162, 164, 166, 168, 169, 171, 173, 175, 177, 179,
    181, 183, 185, 186, 188, 190, 192, 194, 196, 197, 199, 201, 203, 205, 206, 208,
    210, 212, 213, 215, 217, 219, 220, 222, 224, 225, 227, 229, 231, 232, 234, 236,
    237, 239, 241, 242, 244, 246, 247, 249, 250, 252, 254, 255, 257, 259, 260, 262,
    263, 265, 267, 268, 270, 271, 273, 274, 276, 277, 279, 281, 282, 284, 285, 287,
    288, 290, 291, 293, 294, 296, 297, 299, 300, 302, 303, 305, 306, 308, 309, 311,
    312, 314, 315, 316, 318, 319, 321, 322, 324, 325, 326, 328, 329, 331, 332, 333,
    335, 336, 338, 339, 340, 342, 343, 345, 346, 347, 349, 350, 351, 353, 354, 355,
    357, 358, 359, 361, 362, 363, 365, 366, 367, 369, 370, 371, 373, 374, 375, 377,
    378, 379, 380, 382, 383, 384, 386, 387, 388, 389, 391, 392, 393, 394, 396, 397,
    398, 399, 401, 402, 403, 404, 406, 407, 408, 409, 411, 412, 413, 414, 415, 417,
    418, 419, 420, 421, 423, 424, 425, 426, 427, 429, 430, 431, 432, 433, 434, 436,
};

static int log2q8(uint32 v)
{
    int p = 31;
    uint32 m;
    while (!(v >> p))
        p--;
    m = p >= 8 ? v >> (p - 8) : v << (8 - p);
    return p * 256 + LOG2Q8[m & 255];
}

/* One SVF band's magnitude at frequency step x, in half-dB, for centre fi and
 * K27 row ek (same formula as DigiFilter's BP curve). */
static int bp_db2(int fi, int qi, int x)
{
    int32 g = G27[fi];
    int32 k = K27[qi] >> 11;
    int32 G = G27[x], t, num, den, n, d;
    if (G <= g)
        t = udivq16(G, (uint32)g);
    else
        t = udivq16((uint32)g, G);
    num = mulsh(k, t, 16);
    den = (1 << 16) - mulsh(t, t, 16);
    if (den < 0)
        den = -den;
    n = mulsh(num, num, 16);
    d = mulsh(den, den, 16) + n;
    if (d <= 0)
        return 0;
    /* half-dB, 0 at the band centre: the Q16 ratio has a 16-bit (160
     * half-dB) offset that must come off before combining bands. */
    return (int)((log2q8((uint32)(num * num)) - log2q8((uint32)d)) * 10 / 256) - 160;
}

#define CH (GY1 - GY0 - 4)

/* FOLD: the triangle transfer curve, drive from FREQ and bias from RESO. */
static void build_fold_curve(int fi, int qi)
{
    const int32 F = 1 << 27;
    int drive = 1 + fi * 7 / 127;
    int32 bias = (int32)(qi - 64) << 21;
    int x;
    for (x = 0; x < 128; x++) {
        int32 in = (int32)(x - 64) << 21;
        int32 v = in * drive + bias;
        uint32 u = (uint32)v & (4u * F - 1);
        if (u > 2u * F)
            u = 4u * F - u;
        curve[x] = ((int32)u >> 22) * CH / 128;
    }
}

/* CRUSH: the quantisation staircase, bit depth from RESO. */
static void build_crush_curve(int qi)
{
    int bits = 16 - qi * 15 / 127;
    int shift = 30 - bits;
    int x;
    for (x = 0; x < 128; x++) {
        int32 in = (int32)(x - 64) << 24;
        int32 q = (in >> shift) << shift;
        curve[x] = ((q >> 24) + 64) * CH / 128;
    }
}

/* RING: the carrier * modulator waveform. PHASER: a chirped sine (the swirl).
 * FLANGER: a rectified sine (the jet/comb). These are pictures, not responses. */
static void build_mod_curve(int mode, int fi, int qi)
{
    int x, depth = qi * 258;
    for (x = 0; x < 128; x++) {
        int v;
        if (mode == FM_RING) {
            int c = SINE_Q15[(x * 4) & 255];
            int m = SINE_Q15[(x * (2 + fi / 16)) & 255];
            int r = mulsh(c, m, 15);
            v = c + mulsh(r - c, depth, 15);
            curve[x] = (v + 32768) * CH / 65536;
        } else if (mode == FM_PHASER) {
            v = SINE_Q15[((x * x) / 3 + fi * 2) & 255];
            curve[x] = CH / 2 + (v * (CH / 2)) / 32768;
        } else {
            int s = SINE_Q15[(x * 4 + fi * 2) & 255];
            if (s < 0)
                s = -s;
            curve[x] = s * CH / 32768;
        }
    }
}

/* VOWEL: formant bells; BANK: four shifted bells; FOLD/CRUSH: transfer curves. */
static void build_curve(int mode, int fi, int qi)
{
    static const int vdb2[4] = { 0, -4, -9, -20 };
    curve_transfer = 0;
    if (mode >= FM_RING) {
        curve_transfer = 1;
        build_mod_curve(mode, fi, qi);
        return;
    }
    if (mode == FM_FOLD) {
        curve_transfer = 1;
        build_fold_curve(fi, qi);
        return;
    }
    if (mode == FM_CRUSH) {
        curve_transfer = 1;
        build_crush_curve(qi);
        return;
    }
    int ek = 8 + qi * 7 / 127;
    int banks = (mode == FM_FIRST_TYPE) ? VOWEL_N : BANK_N;
    int pos[4], db[4], b, x, pass;
    if (mode == FM_FIRST_TYPE) {
        for (b = 0; b < VOWEL_N; b++) {
            pos[b] = VOWEL_FI8[b][fi] >> 8;
            db[b] = vdb2[b];
        }
    } else {
        int shift = (fi - 64) * 12 / 64;
        for (b = 0; b < BANK_N; b++) {
            pos[b] = clampi((BANK_BASE_FI8[b] >> 8) + shift, 0, 127);
            db[b] = 0;
        }
    }
    for (x = 0; x < 128; x++) {
        int best = -0x7fff;
        for (b = 0; b < banks; b++) {
            int d = bp_db2(pos[b], ek, x) + db[b];
            if (d > best)
                best = d;
        }
        if (best > 0)
            best = 0;
        curve[x] = CH * 50 / (50 - best);
    }
    for (pass = 0; pass < 3; pass++) {
        int32 prev = curve[0];
        for (x = 1; x < 127; x++) {
            int32 cur = curve[x];
            curve[x] = (prev + 2 * cur + curve[x + 1]) / 4;
            prev = cur;
        }
    }
}

static int curve_y(int s, int v)
{
    int w;
    if (curve_transfer)
        return GY0 + 2 + v;
    w = (s < 8) ? s : (s > 119) ? (127 - s) : 8;
    return GY0 + 2 + v * w / 8;
}

static void type_glyph(void *bmp, int mode)
{
    int x, cx = (TBX0 + TBX1) / 2, top = TBY0 + 1, bot = TBY1 - 1, h = bot - top;
    FILLRECT(bmp, TBX0, TBY0, TBX1, TBY1, 0);
    if (mode == FM_FIRST_TYPE) {                 /* a mouth */
        int y0 = top + 3, y1 = bot - 2;
        FILLRECT(bmp, cx - 5, y0, cx + 5, y0, 1);
        FILLRECT(bmp, cx - 6, y0 + 1, cx + 6, y0 + 1, 1);
        FILLRECT(bmp, cx - 5, y1, cx + 5, y1, 1);
        FILLRECT(bmp, cx - 4, y1 + 1, cx + 4, y1 + 1, 1);
        FILLRECT(bmp, cx - 4, y0 + 2, cx + 4, y1 - 1, 0);
        for (x = cx - 3; x <= cx + 3; x += 2)
            FILLRECT(bmp, x, y0 + 2, x, y0 + 3, 1);
    } else if (mode == FM_FIRST_TYPE + 1) {      /* a robot */
        FILLRECT(bmp, cx, top, cx, top + 1, 1);
        FILLRECT(bmp, cx - 1, top + 2, cx + 1, top + 2, 1);
        FILLRECT(bmp, cx - 5, top + 3, cx + 5, top + 3, 1);
        FILLRECT(bmp, cx - 6, top + 4, cx - 6, bot - 1, 1);
        FILLRECT(bmp, cx + 6, top + 4, cx + 6, bot - 1, 1);
        FILLRECT(bmp, cx - 5, bot, cx + 5, bot, 1);
        FILLRECT(bmp, cx - 4, top + 5, cx - 3, top + 6, 1);
        FILLRECT(bmp, cx + 3, top + 5, cx + 4, top + 6, 1);
        for (x = cx - 4; x <= cx + 4; x += 2)
            FILLRECT(bmp, x, bot - 2, x, bot - 1, 1);
    } else if (mode == FM_FOLD) {                /* a folded wave */
        for (x = TBX0 + 1; x < TBX1; x++) {
            int t = (x - TBX0 - 1) % 8, v = t < 4 ? t : 8 - t;
            int y = top + v * h / 4;
            FILLRECT(bmp, x, y, x, y + 1, 1);
        }
    } else if (mode == FM_RING) {                /* a ringed planet */
        static const unsigned char half[7] = { 1, 2, 3, 3, 3, 2, 1 };
        int cy = (top + bot) / 2, dy;
        for (dy = -3; dy <= 3; dy++)
            FILLRECT(bmp, cx - half[dy + 3], cy + dy, cx + half[dy + 3], cy + dy, 1);
        for (dy = -1; dy <= 1; dy += 2) {
            FILLRECT(bmp, cx - 6, cy + dy, cx - 3, cy + dy, 1);
            FILLRECT(bmp, cx + 3, cy + dy, cx + 6, cy + dy, 1);
        }
    } else if (mode == FM_PHASER) {              /* an open square spiral */
        static const signed char sx[10] = { 0, 2, 2, -2, -2, 4, 4, -4, -4, 6 };
        static const signed char sy[10] = { 0, 0, 2, 2, -2, -2, 4, 4, -4, -4 };
        int i, py = (top + bot) / 2;
        for (i = 1; i < 10; i++) {
            int x0 = cx + sx[i - 1], y0 = py + sy[i - 1];
            int x1 = cx + sx[i], y1 = py + sy[i];
            if (x0 == x1) {
                int lo = y0 < y1 ? y0 : y1, hi = y0 < y1 ? y1 : y0, y;
                for (y = lo; y <= hi; y++)
                    if (y >= top && y <= bot)
                        FILLRECT(bmp, x0, y, x0, y, 1);
            } else {
                int lo = x0 < x1 ? x0 : x1, hi = x0 < x1 ? x1 : x0, xx;
                for (xx = lo; xx <= hi; xx++)
                    if (xx >= TBX0 + 1 && xx <= TBX1 - 1)
                        FILLRECT(bmp, xx, y0, xx, y0, 1);
            }
        }
    } else if (mode == FM_FLANGER) {             /* three waves / jet */
        int row;
        for (row = 0; row < 3; row++)
            for (x = TBX0 + 1; x < TBX1; x++) {
                int s = SINE_Q15[(x * 9 + row * 80) & 255];
                int y = top + 3 + row * 3 + (s * 3) / 32768;
                FILLRECT(bmp, x, y, x, y + 1, 1);
            }
    } else {                                     /* Pac-Man */
        static const unsigned char half[11] = { 2, 4, 5, 5, 6, 6, 6, 5, 5, 4, 2 };
        int cy = (top + bot) / 2, dy;
        for (dy = -5; dy <= 5; dy++)
            FILLRECT(bmp, cx - half[dy + 5], cy + dy, cx + half[dy + 5], cy + dy, 1);
        for (dy = -1; dy <= 1; dy++)
            FILLRECT(bmp, cx, cy + dy, cx + 6, cy + dy, 0);
        FILLRECT(bmp, cx - 2, cy - 3, cx - 1, cy - 3, 0);   /* eye */
    }
}

static int read_track(int *type, int *fi, int *qi)
{
    unsigned char *kit = UI_KIT;
    int t = ACTIVE_TRACK;
    int ty;
    if (!kit || t < 0 || t > 7)
        return 0;
    ty = FSLOT(kit, t, FS_TYPE) >> 8;
    if (ty < FM_FIRST_TYPE || ty > FM_LAST)
        return 0;
    *type = ty;
    *fi = clampi((unsigned)FSLOT(kit, t, FS_FREQ) >> 8, 0, 127);
    *qi = clampi((unsigned)FSLOT(kit, t, FS_RESO) >> 8, 0, 127);
    return 1;
}

static int view_kind(void *view)
{
    int32 *v = VIEW_KINDS(view), *e = VIEW_KINDS_END(view);
    int i = VIEW_INDEX(view);
    if (!v || i < 0 || i >= e - v)
        return -1;
    return v[i];
}

static void *page_view(void *ctrl)
{
    char *node, *sent;
    if (!ctrl)
        return 0;
    sent = CTRL_SENTINEL(ctrl);
    for (node = CTRL_HEAD(ctrl); node && node != sent; node = NODE_NEXT(node)) {
        void *view = NODE_VIEW(node);
        if (view && view_kind(view) == FLTR_KIND)
            return view;
    }
    return 0;
}

void digifilter_draw(void *bmp, void *ctrl)
{
    int mode, fi, qi, x, prev = -1;
    if (!bmp || !page_view(ctrl))
        return;
    if (!read_track(&mode, &fi, &qi))
        return;
    FILLRECT(bmp, GX0 + 1, GY0 + 1, GX1 - 1, GY1 - 1, 0);
    build_curve(mode, fi, qi);
    for (x = GX0 + 1; x < GX1; x++) {
        int s = (x - GX0 - 1) * 127 / (GX1 - GX0 - 2);
        int y = curve_y(s, curve[s]);
        if (prev < 0)
            prev = y;
        FILLRECT(bmp, x, prev < y ? prev : y, x, prev < y ? y : prev, 1);
        prev = y;
    }
    type_glyph(bmp, mode);
}
