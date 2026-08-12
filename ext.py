import os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

from language_codes_extended import EXTENDED_LANGUAGE_CODES

# --- line 1 font (unchanged, monospace) ---
f = TTFont('fonts/OverpassMono-Bold.ttf')
upm = f['head'].unitsPerEm
cmap = f.getBestCmap()
gs = f.getGlyphSet()
hmtx = f['hmtx']

# --- line 2 font (subtag) - a separate, non-monospace font ---
FONT2_PATH = 'fonts/Montserrat-Bold.ttf'
f2 = TTFont(FONT2_PATH)
upm2 = f2['head'].unitsPerEm
cmap2 = f2.getBestCmap()
gs2 = f2.getGlyphSet()
hmtx2 = f2['hmtx']

def _get_cap_height(font, glyphset, cmap_):
    """Cap height in font units - the line the tops of capital letters sit
    on. Prefer OS/2.sCapHeight (present in OS/2 table version >= 2);
    otherwise fall back to measuring 'H' directly."""
    os2 = font.get('OS/2')
    if os2 is not None and getattr(os2, 'version', 0) >= 2 and os2.sCapHeight:
        return os2.sCapHeight
    from fontTools.pens.boundsPen import BoundsPen
    bp = BoundsPen(glyphset)
    glyphset[cmap_[ord('H')]].draw(bp)
    return bp.bounds[3] if bp.bounds else int(font['head'].unitsPerEm * 0.7)

CAP_HEIGHT = _get_cap_height(f, gs, cmap)      # line 1 font's cap height (unused elsewhere now)
CAP_HEIGHT2 = _get_cap_height(f2, gs2, cmap2)  # line 2 font's cap height - this is what line-2 math needs

def glyph_path_and_advance(ch, cmap_, glyphset, hmtx_):
    gid = cmap_[ord(ch)]
    pen = SVGPathPen(glyphset)
    glyphset[gid].draw(pen)
    return pen.getCommands(), hmtx_[gid][0]

def build_text_paths(text, font_size, track, cmap_=cmap, glyphset=gs, hmtx_=hmtx, upm_=upm):
    """Returns (paths relative to x=0, total_w, scale). Not positioned yet.
    Pass cmap_/glyphset/hmtx_/upm_ to use a font other than the default
    (line 1) font - e.g. the line-2 font's cmap2/gs2/hmtx2/upm2."""
    scale = font_size / upm_
    x = 0
    paths = []
    for ch in text:
        d, adv = glyph_path_and_advance(ch, cmap_, glyphset, hmtx_)
        paths.append((x, d))
        x += adv * scale + track
    total_w = x - track
    return paths, total_w, scale

BADGE_RING = '''<g transform="matrix(2,0,0,2,-61.4375,-67.125)">
 <path d="M 255.71875,33.5625 C 178.93962,33.5625 111.10867,72.086118 70.5,130.84375 L 114,155.96875 C 145.8111,112.11504 197.43839,83.5625 255.71875,83.5625 C 313.99911,83.562502 365.6264,112.11504 397.4375,155.96875 L 440.9375,130.84375 C 400.32883,72.086118 332.49788,33.5625 255.71875,33.5625 z " style="fill:#900;stroke:none"/>
 <path d="M 46.8125,174.9375 C 36.442946,200.79582 30.71875,229.01254 30.71875,258.5625 C 30.71875,374.31432 118.2675,469.74106 230.71875,482.1875 L 230.71875,431.75 C 145.95412,419.60155 80.71875,346.67019 80.71875,258.5625 C 80.718751,238.11672 84.234053,218.49436 90.6875,200.25 L 46.8125,174.9375 z " style="fill:#069;stroke:none"/>
 <path d="M 464.625,174.9375 L 420.75,200.25 C 427.20345,218.49436 430.71875,238.11672 430.71875,258.5625 C 430.71875,346.67018 365.48339,419.60155 280.71875,431.75 L 280.71875,482.1875 C 393.16999,469.74106 480.71874,374.31432 480.71875,258.5625 C 480.71875,229.01254 474.99455,200.79582 464.625,174.9375 z " style="fill:#069;stroke:none"/>
</g>'''

CX = 450

# --- PLACEHOLDERS - none of this is calibrated yet, tune by eyeballing ---
# Line 1 (primary tag, e.g. "be"): reused from batch.py's single-line table,
# just with cy pulled up to make room for line 2 underneath.
LINE1_PARAMS_BY_LEN = {
    1: dict(font_size=290.0, track=-10, cy=455),
    2: dict(font_size=290.0, track=-10, cy=455),
    3: dict(font_size=290.0, track=-10, cy=455),
}

# Line 2 (subtag, e.g. "TARASK"): smaller, sits below line 1.
LINE2_FONT_SIZE = 190.0
LINE2_TRACK = 0

# The ring is a true circle: transforming BADGE_RING's own coordinates shows
# its outer edge passes through (450,0) and is ~450 units from (450,450)
# everywhere else too. So center=(450,450), radius=450, confirmed from the
# path data itself (not eyeballed).
CIRCLE_CENTER_Y = 450
CIRCLE_RADIUS = 350
# Padding pulled in from the true edge to clear the ring's stroke/border.
# PLACEHOLDER - tune by eyeballing against the rendered ring.
TEXT_INSET = 30

# Line 2 no longer moves vertically. It stays anchored at LINE2_CY (a fixed
# baseline position); when it needs to shrink, it shrinks about its own
# cap-height line instead of its baseline, so the tops of the letters stay
# put and only the baseline creeps upward as the glyphs get shorter - see
# cy_for_font_scale below.
LINE2_CY = 680  # PLACEHOLDER - baseline position at full size, tune by eyeballing


def available_width_at(cy, inset=TEXT_INSET):
    """Chord width of the (inset) circle at height cy. 0 if cy is outside the circle."""
    r = CIRCLE_RADIUS - inset
    dy = cy - CIRCLE_CENTER_Y
    if abs(dy) >= r:
        return 0.0
    return 2 * (r * r - dy * dy) ** 0.5
 
def cy_for_font_scale(font_scale):
    """Baseline y when the font is shrunk to font_scale (relative to
    LINE2_FONT_SIZE) while holding the cap-height line fixed at whatever it
    is at LINE2_CY/LINE2_FONT_SIZE. Shrinking moves the baseline upward
    (smaller y) since the glyphs get shorter but the top stays put."""
    nominal_scale = LINE2_FONT_SIZE / upm2
    shrunk_scale = nominal_scale * font_scale
    return LINE2_CY - CAP_HEIGHT2 * (nominal_scale - shrunk_scale)
 
def solve_font_scale(total_w2_base, sx, inset=TEXT_INSET):
    """Exact font_scale such that sx * total_w2_base * font_scale just fits
    the circle's chord width at cy_for_font_scale(font_scale) - i.e. accounts
    for the fact that shrinking also raises the (cap-height-anchored)
    baseline toward the circle's center, which itself grants extra width.
 
    Substituting cy2(scale) = cap_top_y + k*scale (both affine in scale)
    into the chord equation sx*scale*total_w2_base = 2*sqrt(r^2-(cy2-cy0)^2)
    and squaring both sides leaves scale only up to power 2, so this has a
    closed-form (quadratic) solution - confirmed against a numeric bisection
    to make sure no sign/domain error sneaks in from the squaring step.
 
    Returns None if no valid scale in (0, 1] solves it (shouldn't normally
    happen given how this is called, but the caller should treat None as
    "give up", the same as font_scale < FONT_SCALE_MIN).
    """
    nominal_scale = LINE2_FONT_SIZE / upm2
    cap_top_y = LINE2_CY - CAP_HEIGHT2 * nominal_scale  # fixed anchor point
    k = CAP_HEIGHT2 * nominal_scale
    r = CIRCLE_RADIUS - inset
    C = sx * total_w2_base
    D0 = cap_top_y - CIRCLE_CENTER_Y
 
    a = C * C + 4 * k * k
    b = 8 * D0 * k
    c = 4 * D0 * D0 - 4 * r * r
    disc = b * b - 4 * a * c
    if disc < 0:
        return None
    sqrt_disc = disc ** 0.5
    for scale in ((-b + sqrt_disc) / (2 * a), (-b - sqrt_disc) / (2 * a)):
        if 0 < scale <= 1:
            return scale
    return None

# Squeeze/shrink policy for line 2:
#   1. At LINE2_CY, squeeze horizontally first.
#   2. If that would need to go past SX_THRESHOLD_1, stop squeezing there
#      and instead shrink the font size (+ tracking, proportionally) on the
#      spot - anchored to the cap-height line, not the baseline, so the
#      shrink happens from the top down rather than growing a gap above it.
#   3. If the required shrink would go past FONT_SCALE_MIN, give up (skip).
SX_THRESHOLD_1 = 0.8    # PLACEHOLDER - soft squeeze limit before shrinking kicks in, tune by eyeballing
FONT_SCALE_MIN = 0.25    # PLACEHOLDER - floor as a fraction of LINE2_FONT_SIZE; beyond this we skip

# Escape valve for codes that don't fit even after squeeze -> shrink.
# Fill in by hand after eyeballing, same idea as batch.py's PARAMS_BY_LEN.
MANUAL_OVERRIDE = {
    # 'some-reallylongsubtag': dict(font_size=100.0, track=-15, sx=0.55),
}
# --------------------------------------------------------------------------


def render_extended_code(code, out_dir):
    if '-' not in code:
        raise ValueError(f'"{code}" has no subtag - this is not an extended code')
    primary, subtag = code.split('-', 1)
    subtag = subtag#.upper()
 
    l1p = LINE1_PARAMS_BY_LEN.get(len(primary))
    if l1p is None:
        print(f'skip (no line-1 params for primary len {len(primary)}): {code}')
        return None
 
    if any(ord(ch) not in cmap2 for ch in subtag):
        print(f'skip (subtag has glyph missing from font): {code}')
        return None
 
    # --- line 1 ---
    paths1, total_w1, scale1 = build_text_paths(primary, l1p['font_size'], l1p['track'])
    start_x1 = CX - total_w1 / 2
    svg_line1 = ''.join(
        f'<path transform="translate({start_x1 + x_off},{l1p["cy"]}) '
        f'scale({scale1},{-scale1})" d="{d}" style="fill:#396;stroke:none"/>'
        for x_off, d in paths1
    )
 
    # --- line 2: squeeze first, then shrink (anchored at cap-height) if
    # squeezing alone isn't enough - no vertical movement of the baseline
    # except what the cap-height anchoring itself produces ---
    if code in MANUAL_OVERRIDE:
        ov = MANUAL_OVERRIDE[code]
        font_size2, track2, sx = ov['font_size'], ov['track'], ov['sx']
        paths2, total_w2, scale2 = build_text_paths(
            subtag, font_size2, track2, cmap2, gs2, hmtx2, upm2)
        cy2 = LINE2_CY
    else:
        font_size2, track2 = LINE2_FONT_SIZE, LINE2_TRACK
        paths2, total_w2, scale2 = build_text_paths(
            subtag, font_size2, track2, cmap2, gs2, hmtx2, upm2)
 
        available_at_cy = available_width_at(LINE2_CY)
        sx_at_full = available_at_cy / total_w2 if total_w2 else 1.0
 
        if sx_at_full >= 1.0:
            # Fits at full size with no squeeze at all.
            cy2, sx = LINE2_CY, 1.0
        elif sx_at_full >= SX_THRESHOLD_1:
            # Stage 1: squeezing is enough, and doesn't need to go past the
            # soft threshold.
            cy2, sx = LINE2_CY, sx_at_full
        else:
            # Squeezing to SX_THRESHOLD_1 alone isn't enough - hold the
            # squeeze there and shrink the font instead, solved exactly
            # (accounts for the baseline rising as the font shrinks, which
            # itself grants extra width - ignoring that undershoots and can
            # skip codes that would actually fit).
            sx = SX_THRESHOLD_1
            font_scale = solve_font_scale(total_w2, sx)
 
            if font_scale is None or font_scale < FONT_SCALE_MIN:
                fs_str = f'{font_scale:.2f}' if font_scale is not None else 'n/a'
                print(f'skip (subtag too long even at sx={sx:.2f}, font_scale={fs_str}, add a MANUAL_OVERRIDE entry): {code}')
                return None
 
            font_size2 = LINE2_FONT_SIZE * font_scale
            track2 = LINE2_TRACK * font_scale
            paths2, total_w2, scale2 = build_text_paths(
                subtag, font_size2, track2, cmap2, gs2, hmtx2, upm2)
            # Cap-height-anchored: as the font shrinks, the baseline creeps
            # up so the tops of the letters stay where they'd be at full size.
            cy2 = cy_for_font_scale(font_scale)
 
    start_x2 = CX - total_w2 / 2
    inner2 = ''.join(
        f'<path transform="translate({start_x2 + x_off},{cy2}) '
        f'scale({scale2},{-scale2})" d="{d}" style="fill:#396;stroke:none"/>'
        for x_off, d in paths2
    )
    # Squeeze horizontally about CX only - height is untouched.
    svg_line2 = f'<g transform="translate({CX},0) scale({sx},1) translate({-CX},0)">{inner2}</g>'
 
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="900" height="900" viewBox="0 0 900 900">
{BADGE_RING}
{svg_line1}
{svg_line2}
</svg>
'''
    #sub_dir = os.path.join(out_dir, f'{len(primary)}-subtag')
    #os.makedirs(sub_dir, exist_ok=True)
    #out_path = os.path.join(sub_dir, f'WCL_language_icon_{code}.svg')
    out_path = os.path.join(out_dir, f'WCL_language_icon_{code}.svg')
    with open(out_path, 'w') as fo:
        fo.write(svg)
    return out_path

def tune_sample(codes, out_dir='tune_extended'):
    os.makedirs(out_dir, exist_ok=True)
    for code in codes:
        render_extended_code(code, out_dir)
    print(f'rendered sample: {codes} -> {out_dir}/')

if __name__ == '__main__':
    # tune_sample(['be-tarask', 'zh-Hans-CN'])
    # exit()

    out_dir = 'out_extended'
    os.makedirs(out_dir, exist_ok=True)

    done, skipped = 0, []
    for code in sorted(EXTENDED_LANGUAGE_CODES):
        result = render_extended_code(code, out_dir)
        if result is None:
            skipped.append(code)
        else:
            done += 1

    print(f'generated {done} svgs into {out_dir}/')
    if skipped:
        print(f'skipped {len(skipped)} codes: {skipped}')
