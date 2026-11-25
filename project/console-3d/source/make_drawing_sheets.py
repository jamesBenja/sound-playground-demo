"""Dimensioned drawing sheets made from the orthographic renders.

The clean renders (console_*.png) carry no text. These separate sheets add
dimension lines whose positions are computed from the CAD parameters and the
orthographic camera data (renders_meta.json), so they stay true to the model.
Writes ../drawing_plan_dimensioned.png, ../drawing_front_dimensioned.png,
       ../drawing_side_section_dimensioned.png
"""
import json, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
meta = json.loads((OUT / "renders_meta.json").read_text())
man = json.loads((HERE / "parts" / "parts.json").read_text())
P = man["parameters"]
BB = {p["name"]: p["bbox_mm"] for p in man["parts"]}
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
try:
    F = ImageFont.truetype(FONT, 26); FS = ImageFont.truetype(FONT, 21); FT = ImageFont.truetype(FONT, 34)
except OSError:
    F = FS = FT = ImageFont.load_default()
INK, DIM, SUB = (32, 37, 40), (40, 92, 120), (95, 104, 108)
MARGIN_T, MARGIN_B, MARGIN_S = 120, 120, 60


class Sheet:
    def __init__(self, view, mapping):
        m = meta[view]
        self.img = Image.open(OUT / m["file"]).convert("RGB")
        self.rw, self.rh = self.img.size
        self.s = self.rw / m["ortho"] / 1000.0  # px per mm
        self.map = mapping
        self.W, self.H = self.rw + 2 * MARGIN_S, self.rh + MARGIN_T + MARGIN_B
        self.c = Image.new("RGB", (self.W, self.H), (250, 250, 248))
        self.c.paste(self.img, (MARGIN_S, MARGIN_T))
        self.d = ImageDraw.Draw(self.c)

    def p(self, a, b):  # model mm -> sheet px
        u, v = self.map(a, b)
        return MARGIN_S + self.rw / 2 + u * self.s, MARGIN_T + self.rh / 2 - v * self.s

    def text(self, xy, t, font=F, fill=DIM, anchor="mm", bg=True):
        if bg:
            box = self.d.textbbox(xy, t, font=font, anchor=anchor)
            self.d.rectangle((box[0] - 6, box[1] - 3, box[2] + 6, box[3] + 3), fill=(250, 250, 248))
        self.d.text(xy, t, font=font, fill=fill, anchor=anchor)

    def dim_h(self, a0, a1, b, off_px, label=None, ext_from=None):
        x0, y = self.p(a0, b); x1, _ = self.p(a1, b); yy = y + off_px
        if ext_from is not None:
            for x in (x0, x1):
                self.d.line((x, self.p(a0, ext_from)[1], x, yy + (6 if off_px > 0 else -6)), fill=DIM, width=1)
        self.d.line((x0, yy, x1, yy), fill=DIM, width=2)
        for x in (x0, x1):
            self.d.line((x - 7, yy + 7, x + 7, yy - 7), fill=DIM, width=2)
        self.text(((x0 + x1) / 2, yy), label or f"{abs(a1 - a0):.0f}")

    def dim_v(self, b0, b1, a, off_px, label=None, ext_from=None):
        x, y0 = self.p(a, b0); _, y1 = self.p(a, b1); xx = x + off_px
        if ext_from is not None:
            for y in (y0, y1):
                self.d.line((self.p(ext_from, b0)[0], y, xx + (6 if off_px > 0 else -6), y), fill=DIM, width=1)
        self.d.line((xx, y0, xx, y1), fill=DIM, width=2)
        for y in (y0, y1):
            self.d.line((xx - 7, y + 7, xx + 7, y - 7), fill=DIM, width=2)
        self.text((xx, (y0 + y1) / 2), label or f"{abs(b1 - b0):.0f}")

    def title(self, t, sub):
        self.text((MARGIN_S, 48), t, font=FT, fill=INK, anchor="lm", bg=False)
        self.text((MARGIN_S, 88), sub, font=FS, fill=SUB, anchor="lm", bg=False)
        self.d.line((MARGIN_S, self.H - 70, self.W - MARGIN_S, self.H - 70), fill=(200, 204, 203), width=1)
        self.text((MARGIN_S, self.H - 38), "SOUND PLAYGROUND console, CAD study v2 · dimensions in mm · design study, not for construction",
                  font=FS, fill=SUB, anchor="lm", bg=False)

    def save(self, name):
        self.c.save(OUT / name); print("wrote", name)


W, D, TOP = P["width"], P["depth"], P["deck_top"]
FY = -D / 2
scr, hood = BB["display_enclosure_32in"], BB["display_sun_hood"]
glass = BB["display_glass"]

# ---- plan ----
if "top" in meta:
    s = Sheet("top", lambda x, y: (x, y))
    s.dim_h(-W / 2, W / 2, D / 2, -60, f"{W:.0f}", ext_from=D / 2)
    s.dim_v(-D / 2, D / 2, -W / 2, -55, f"{D:.0f}", ext_from=-W / 2)
    xs = P["station_x"]
    for a, b in zip(xs, xs[1:]):
        s.dim_h(a, b, FY, 55, f"{b - a:.0f}", ext_from=FY)
    px = xs[0] + P["pad_dx"]
    s.dim_v(FY, P["plate_cy"], px - 120, 0, f"{P['plate_cy'] - FY:.0f}")
    s.text(s.p(px, P["plate_cy"] - 125), f"pad Ø{P['pad_d']}", font=FS)
    s.text(s.p(xs[0] + P["knob_dx"], P["plate_cy"] - 125), f"encoder knob Ø{P['knob_d']}", font=FS)
    s.dim_h(scr[0], scr[3], scr[1], 45, f"display {scr[3] - scr[0]:.0f} wide")
    s.dim_v(FY, scr[1], 0, 0, f"{scr[1] - FY:.0f} front edge to display")
    for nm, x in zip(P["station_names"], xs):
        s.text(s.p(x, FY - 130), nm, font=F, fill=INK)
    s.title("PLAN", "Four pad + rotary stations on the front band; display, mast and speakers behind them (top orthographic render)")
    s.save("drawing_plan_dimensioned.png")

# ---- front elevation ----
if "front" in meta:
    cz = meta["front"]["target"][2] * 1000
    s = Sheet("front", lambda x, z: (x, z - cz))
    s.dim_h(-W / 2, W / 2, 0, 50, f"{W:.0f}")
    s.dim_v(0, TOP, -W / 2, -60, f"{TOP:.0f} playing surface", ext_from=-W / 2)
    s.dim_v(0, TOP - P["deck_thk"], -P["leg_x"][0], 55, f"{TOP - P['deck_thk']:.0f} under deck")
    s.dim_v(TOP, glass[2], 0, -470, f"{glass[2] - TOP:.0f}")
    s.dim_v(0, max(hood[5], BB['left_directional_speaker'][5]), W / 2, 60, f"{max(hood[5], BB['left_directional_speaker'][5]):.0f} overall", ext_from=W / 2)
    s.dim_v(TOP, P["spk_cz"], P["spk_x"] + 230, 0, f"speaker centre {P['spk_cz']:.0f}")
    s.dim_h(-P["leg_x"][0], P["leg_x"][0], 380, 0, f"{2 * P['leg_x'][0]:.0f} clear between legs")
    s.title("FRONT ELEVATION", "Player side. Display bottom edge and speaker heights relative to the 850 mm playing surface")
    s.save("drawing_front_dimensioned.png")

# ---- side section ----
if "side" in meta:
    ty, tz = meta["side"]["target"][1] * 1000, meta["side"]["target"][2] * 1000
    s = Sheet("side", lambda y, z: (y - ty, z - tz))
    s.dim_h(-D / 2, D / 2, 0, 110, f"{D:.0f} deck depth")
    s.dim_h(-D / 2, P["spine_y"][0], 0, 40, f"{P['spine_y'][0] - FY:.0f} knee/toe depth")
    s.dim_v(0, TOP - P["deck_thk"], P["spine_y"][0] - 60, 0, f"{TOP - P['deck_thk']:.0f} clear")
    s.dim_v(0, TOP, D / 2, 70, f"{TOP:.0f}", ext_from=D / 2)
    s.dim_v(TOP, P["spk_cz"], D / 2, 190, f"{P['spk_cz'] - TOP:.0f} to speaker centre")
    # 15° vertical coverage cone of the speaker towards the player zone (illustrative)
    sy, sz = P["spk_cy"] - P["spk_size"][1] / 2, P["spk_cz"]
    for ang in (-P["spk_pitch"] - 15, -P["spk_pitch"] + 15):
        L = 1150
        y1, z1 = sy - L * math.cos(math.radians(ang)), sz + L * math.sin(math.radians(ang))
        s.d.line((*s.p(sy, sz), *s.p(y1, z1)), fill=(70, 110, 135), width=2)
    s.text(s.p(sy - 900, sz + 210), f"speaker axis {-P['spk_pitch']:+.0f}° (level), ±15° shown (concept, not measured)" if P["spk_pitch"] == 0 else f"speaker axis {-P['spk_pitch']:+.0f}°, ±15° shown (concept, not measured)", font=FS, fill=SUB)
    s.text(s.p(-D / 2 + 20, TOP + 640), f"display tilted back {P['screen_tilt']}°", font=FS, fill=SUB, anchor="lm")
    s.title("SIDE SECTION (end leg removed)", "Knee and toe space under the deck with a wheelchair user at a station; display tilt and speaker aim")
    s.save("drawing_side_section_dimensioned.png")
