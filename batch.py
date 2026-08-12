import os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from language_codes import LANGUAGE_CODES

# SUPPLEMENT
# Import your custom supplement file
try:
    from code_supplement import ADDITIONAL_LANGUAGE_CODES
except ImportError:
    ADDITIONAL_LANGUAGE_CODES = []

# Merge both sources into a single set/list
ALL_CODES = set(LANGUAGE_CODES) | set(ADDITIONAL_LANGUAGE_CODES)

# SUPPLEMENT end


f = TTFont('fonts/OverpassMono-Bold.ttf')
upm = f['head'].unitsPerEm
cmap = f.getBestCmap()
gs = f.getGlyphSet()
hmtx = f['hmtx']

def glyph_path_and_advance(ch):
    gid = cmap[ord(ch)]
    pen = SVGPathPen(gs)
    gs[gid].draw(pen)
    return pen.getCommands(), hmtx[gid][0]

# Calibrated params (900-space), per code length.
# "3" is your original calibration for "nan". Others are placeholders —
# tune each by rendering a sample code at that length and eyeballing it.
PARAMS_BY_LEN = {
    2: dict(font_size=470.0, track=-10, cx=450, cy=484.5 + 110),
    3: dict(font_size=353.3, track=-10, cx=450, cy=484.5 + 70),
}
DEFAULT_PARAMS = dict(font_size=300.0, track=-20, cx=450, cy=484.5 + 70)

def get_params(code):
    return PARAMS_BY_LEN.get(len(code), DEFAULT_PARAMS)

BADGE_RING = '''<g transform="matrix(2,0,0,2,-61.4375,-67.125)">
 <path d="M 255.71875,33.5625 C 178.93962,33.5625 111.10867,72.086118 70.5,130.84375 L 114,155.96875 C 145.8111,112.11504 197.43839,83.5625 255.71875,83.5625 C 313.99911,83.562502 365.6264,112.11504 397.4375,155.96875 L 440.9375,130.84375 C 400.32883,72.086118 332.49788,33.5625 255.71875,33.5625 z " style="fill:#900;stroke:none"/>
 <path d="M 46.8125,174.9375 C 36.442946,200.79582 30.71875,229.01254 30.71875,258.5625 C 30.71875,374.31432 118.2675,469.74106 230.71875,482.1875 L 230.71875,431.75 C 145.95412,419.60155 80.71875,346.67019 80.71875,258.5625 C 80.718751,238.11672 84.234053,218.49436 90.6875,200.25 L 46.8125,174.9375 z " style="fill:#069;stroke:none"/>
 <path d="M 464.625,174.9375 L 420.75,200.25 C 427.20345,218.49436 430.71875,238.11672 430.71875,258.5625 C 430.71875,346.67018 365.48339,419.60155 280.71875,431.75 L 280.71875,482.1875 C 393.16999,469.74106 480.71874,374.31432 480.71875,258.5625 C 480.71875,229.01254 474.99455,200.79582 464.625,174.9375 z " style="fill:#069;stroke:none"/>
</g>'''

def build_text_paths(text, font_size, track, cx, cy_baseline):
    scale = font_size / upm
    x = 0
    paths = []
    for ch in text:
        d, adv = glyph_path_and_advance(ch)
        paths.append((x, d))
        x += adv * scale + track
    total_w = x - track
    return paths, total_w, scale

def render_code(code, out_dir):
    p = get_params(code)
    paths, total_w, scale = build_text_paths(code, p['font_size'], p['track'], p['cx'], p['cy'])
    start_x = p['cx'] - total_w / 2

    svg_paths = []
    for x_off, d in paths:
        svg_paths.append(
            f'<path transform="translate({start_x + x_off},{p["cy"]}) '
            f'scale({scale},{-scale})" d="{d}" style="fill:#396;stroke:none"/>'
        )

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="900" height="900" viewBox="0 0 900 900">
{BADGE_RING}
{''.join(svg_paths)}
</svg>
'''
    sub_dir = os.path.join(out_dir, str(len(code)))
    os.makedirs(sub_dir, exist_ok=True)
    out_path = os.path.join(sub_dir, f'WML_language_icon_{code}.svg')
    with open(out_path, 'w') as fo:
        fo.write(svg)
    return out_path

def tune_sample(codes, out_dir='tune'):
    """Render just a few codes to quickly eyeball params for a given length."""
    os.makedirs(out_dir, exist_ok=True)
    for code in codes:
        render_code(code, out_dir)
    print(f'rendered sample: {codes} -> {out_dir}/')

if __name__ == '__main__':
    # Quick way to tune one length before running the full batch:
    # tune_sample(['aa', 'zh', 'ja'])   # 2-letter samples
    # exit()

    out_dir = 'out'
    os.makedirs(out_dir, exist_ok=True)

    skipped = []
    for code in sorted(ALL_CODES):
        # skip codes containing chars not in the font (e.g. non-ascii)
        if not all(ord(ch) in cmap for ch in code):
            skipped.append(code)
            continue
        render_code(code, out_dir)

    print(f'generated {len(ALL_CODES) - len(skipped)} svgs into {out_dir}/')
    if skipped:
        print(f'skipped {len(skipped)} codes missing glyphs: {skipped}')